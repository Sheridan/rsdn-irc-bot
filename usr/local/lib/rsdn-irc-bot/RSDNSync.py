#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, socket, string, os, re, time
from threading import Thread, Lock
from suds.client import Client
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO, Timer
from Configurable import CConfigurable

class CRSDNSync(Thread, CConfigurable):
    def __init__(self):
        Thread.__init__(self)
        CConfigurable.__init__(self, '/etc/rsdn-irc-bot/rsdn.conf')
        self.terminate = False
        self.timerForumListSync = Timer.CTimer(int(self.config['timers']['sync_forum_list']), self.syncForumsList)
        self.timerDataSync = Timer.CTimer(int(self.config['timers']['sync_data']), self.syncForumsData)
        self.forumsRowVersion = 0
        self.forums = dict()
        self.missedMessages = []
        self.missedMembers = []

    def _client(self):
        client = Client("http://www.rsdn.ru/ws/janusAT.asmx?WSDL")
        try:
            client.service.Check()
        except URLError(err):
           print err
           return [0, err]
        return [1, client]

    def getMessageUrlById(self, mid):
        return 'http://www.rsdn.ru/forum/message/%d.aspx : mid %d'%(mid,mid)

    def getMemberUrlById(self, uid):
        return 'http://www.rsdn.ru/Users/%d.aspx : uid %d'%(uid,uid)
        
    def getForumUrlById(self, fid):
        return 'http://rsdn.ru/forum/%s/ : fid %d'%(self.forums[fid]['sname'],fid)

    def syncForumsList(self):
        (ok, client) = self._client()
        if ok:
            GO.bot.sendLog("RSDN. Запуск получения списка форумов")
            request = client.factory.create('ForumRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            request.forumsRowVersion = self.forumsRowVersion
            result = client.service.GetForumList(request)
            groups = dict()
            for fgroup in result['groupList'][0]:
                groups[fgroup['forumGroupId']] = fgroup['forumGroupName']
            for forum in result['forumList'][0]:
                self.forums[forum['forumId']] = {
                                      'sname': forum['shortForumName'],
                                      'gname': groups[forum['forumGroupId']],
                                      'name' : forum['forumName'], 
                                      'gid'  : forum['forumGroupId'],
                                      'fid'  : forum['forumId']
                                    }
            for fid in self.forums.keys():
                forum = self.forums[fid]
                GO.bot.joinChannel(forum['sname'], '%s :: %s ( %s )'%(forum['gname'], forum['name'], self.getForumUrlById(fid)))

    def getNewData(self):
        if len(self.forums) == 0: return
        (ok, client) = self._client()
        if ok:
            GO.bot.sendLog("RSDN. Запуск проверки новых сообщений на форумах")
            request = client.factory.create('ChangeRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            request.maxOutput = int(self.config['limits']['max_sync_output'])
            for fid in self.forums.keys():
                forum = self.forums[fid]
                mRequestForumInfo = client.factory.create('RequestForumInfo')
                mRequestForumInfo.forumId = forum['fid']
                mRequestForumInfo.isFirstRequest = request.messageRowVersion == ''
                request.subscribedForums.RequestForumInfo.append(mRequestForumInfo)
            done = False
            result = []
            while not done:
                request.ratingRowVersion   = GO.storage.getRsdnRowVersion('ratingRowVersion')
                request.messageRowVersion  = GO.storage.getRsdnRowVersion('messageRowVersion')
                request.moderateRowVersion = GO.storage.getRsdnRowVersion('moderateRowVersion')
                #print request
                if len(self.missedMessages):
                    for mid in self.missedMessages:
                        request.breakMsgIds.int.append(mid)
                    self.missedMessages = []
                answer = client.service.GetNewData(request)
                #print answer
                done = answer['lastForumRowVersion'] == GO.storage.getRsdnRowVersion('messageRowVersion')
                if not done:
                    GO.storage.setRsdnRowVersion('ratingRowVersion'  , answer['lastRatingRowVersion']  )
                    GO.storage.setRsdnRowVersion('messageRowVersion' , answer['lastForumRowVersion']   )
                    GO.storage.setRsdnRowVersion('moderateRowVersion', answer['lastModerateRowVersion'])
                    result.append(answer)
                    self.mineMissedInMessages(answer['newMessages'][0])
            return result
        return None

    def getNewUsers(self):
        if len(self.forums) == 0: return
        (ok, client) = self._client()
        if ok:
            GO.bot.sendLog("RSDN. Запуск проверки новых пользователей")
            request = client.factory.create('UserRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            request.maxOutput = int(self.config['limits']['max_sync_output'])
            done = False
            result = []
            while not done:
                request.lastRowVersion = GO.storage.getRsdnRowVersion('usersRowVersion')
                #print request
                answer = client.service.GetNewUsers(request)
                #print answer
                done = answer['lastRowVersion'] == GO.storage.getRsdnRowVersion('usersRowVersion')
                GO.storage.setRsdnRowVersion('usersRowVersion', answer['lastRowVersion'])
                if not done:
                    result.append(answer)

            return result
        return None

    def loadUsersByIds(self, ids):
        if len(self.forums) == 0: return
        (ok, client) = self._client()
        if ok:
            GO.bot.sendLog("RSDN. Запуск загрузки пользователей по id")
            request = client.factory.create('UserByIdsRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            for uid in ids:
                request.userIds.int.append(uid)
            answer = client.service.GetUserByIds(request)
            return answer
        return None

    def mineMissedInMessages(self, messages):
        for message in messages:
            for s in ['parentId', 'topicId']:
                if not GO.storage.isMessageInDb(message[s]) and message[s] not in self.missedMessages:
                    self.missedMessages.append(message[s])
            if not GO.storage.isUserInDb(message['userId']) and message['userId'] not in self.missedMembers:
                self.missedMembers.append(message['userId'])

    def syncForumsData(self):
        newData = self.getNewData()
        if newData != None:
            for newDataBit in newData:
                for message in newDataBit['newMessages'][0]:
                    GO.storage.updateRsdnMessages(message)
                    text = '`%s`. Автор: %s'%(
                                               GO.utf8(message['subject']), 
                                               GO.utf8(message['userNick']),
                                             )
                    urls = ' | '.join([
                                      '#'+GO.utf8(self.forums[message['forumId']]['sname']),
                                      GO.utf8(self.getForumUrlById(message['forumId'])),
                                      self.getMessageUrlById(message['messageId']), 
                                      self.getMemberUrlById(message['userId'])
                                    ])
                    GO.bot.sendRsdnNotification('В форуме `%s` новое сообщение: %s'%(
                                                                                      GO.utf8(self.forums[message['forumId']]['name']),
                                                                                      text
                                                                                     ))
                    GO.bot.sendRsdnNotification(urls)
                    if message['parentId'] == 0:
                        channel = '#'+GO.utf8(self.forums[message['forumId']]['sname'])
                        GO.bot.sendChannelText(channel, 'Новый топик %s'%text)
                        GO.bot.sendChannelText(channel, urls)
        newUsers = self.getNewUsers()
        if newUsers != None:
            for newUsersBit in newUsers:
                for user in newUsersBit['users'][0]:
                    GO.storage.updateRsdnUsers(user)
                    GO.bot.sendRsdnNotification('Новый пользователь `%s`, `%s`, `%s`: %s'%(
                                                                                GO.utf8(user['userName']),
                                                                                GO.utf8(user['userNick']),
                                                                                GO.utf8(user['realName']),
                                                                                self.getMemberUrlById(user['userId'])
                                                                              ))
        if len(self.missedMembers):
            users = self.loadUsersByIds(self.missedMembers)
            self.missedMembers = []
            if users:
                for user in users['users'][0]:
                    GO.storage.updateRsdnUsers(user)

    def getTopic(self, mid):
        (ok, client) = self._client()
        if ok:
            GO.bot.sendLog("RSDN. Запуск получения топика")
            request = client.factory.create('TopicRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            request.messageIds.int.append(mid)
            result = client.service.GetTopicByMessage(request)
            if len(result['Messages']):
                self.mineMissedInMessages(result['Messages'][0])
                msgcount = 0
                message = dict()
                message['members'] = dict()
                message['exists'] = True
                for m in result['Messages'][0]:
                    GO.storage.updateRsdnMessages(m)
                    msgcount += 1
                    nick = GO.utf8(m['userNick'])
                    message['members'][nick] = 1 if nick not in message['members'] else message['members'][nick] + 1
                    if m['messageId'] == mid:
                        message['self'] = {
                                            'subject': GO.utf8(m['subject']), 
                                            'user'   : nick,
                                            'message': GO.utf8(m['message']), 
                                            'date'   : m['messageDate'],
                                            'mid'    : m['messageId'], 
                                            'closed' : m['closed']
                                          }
                    if m['parentId'] == 0:
                        message['top'] = {
                                            'subject': GO.utf8(m['subject']), 
                                            'user'   : nick,
                                            'date'   : m['messageDate'],
                                            'mid'    : m['messageId'], 
                                            'closed' : m['closed']
                                          }
                message['count'] = msgcount
                return message
            else:
                return {'exists': False}
        return {'exists': False}

    def stop(self):
        self.terminate = True

    def run(self):
        self.timerForumListSync.start()
        self.timerDataSync.start()
        while not self.terminate:
            time.sleep(1)
        self.timerDataSync.stop()
        self.timerForumListSync.stop()

