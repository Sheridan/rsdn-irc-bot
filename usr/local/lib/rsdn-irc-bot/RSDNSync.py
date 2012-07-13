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
        self.timerAdditionalSync = Timer.CTimer(int(self.config['timers']['sync_additional']), self.additionalSync)
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

    def additionalSync(self):
        mids = []
        f = open('/home/rsdn/mid', 'r')
        mid = int(f.read()) + 1
        f.close()
        while GO.storage.isMessageInDb(mid):
            mid += 1
        f = open('/home/rsdn/mid', 'w')
        f.write('%d'%mid)
        f.close()
        x = 0
        while x < 256:
            mids.append(mid)
            mid += 1
            while GO.storage.isMessageInDb(mid):
                mid += 32
            x += 1
        self.getTopics(mids)

    def getNewData(self):
        if len(self.forums) == 0: return
        (ok, client) = self._client()
        if ok:
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
            x = 1
            while not done:
                GO.bot.sendLog("RSDN. Синхронизация. Итерация %d"%x)
                x += 1
                request.ratingRowVersion   = GO.storage.getRsdnRowVersion('ratingRowVersion')
                request.messageRowVersion  = GO.storage.getRsdnRowVersion('messageRowVersion')
                request.moderateRowVersion = GO.storage.getRsdnRowVersion('moderateRowVersion')
                #print request
                if len(self.missedMessages):
                    for mid in self.missedMessages:
                        if not GO.storage.isMessageInDb(mid):
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
            GO.bot.sendLog("RSDN. Синхронизация пользователей")
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
                if message[s] not in self.missedMessages and not GO.storage.isMessageInDb(message[s]):
                    self.missedMessages.append(message[s])
            if message['userId'] not in self.missedMembers and not GO.storage.isUserInDb(message['userId']):
                self.missedMembers.append(message['userId'])

    def syncForumsData(self):
        GO.bot.sendLog("RSDN. Запуск синхронизации")
        newData = self.getNewData()
        if newData != None:
            msgcount = { True: 0, False: 0 }
            mdrcount = { True: 0, False: 0 }
            ratcount = { True: 0, False: 0 }
            for newDataBit in newData:
                #print newDataBit
                for message in newDataBit['newMessages'][0]:
                    msgcount[GO.storage.updateRsdnMessages(message)] += 1
                    fid = message['forumId']
                    if fid:
                        fchannel = '#%s'%GO.utf8(self.forums[fid]['sname'])
                        text = '`%s`. Автор: %s'%(
                                                   GO.utf8(message['subject']), 
                                                   GO.utf8(message['userNick']),
                                                 )
                        urls = ' | '.join([
                                          fchannel,
                                          GO.utf8(self.getForumUrlById(fid)),
                                          self.getMessageUrlById(message['messageId']), 
                                          self.getMemberUrlById(message['userId'])
                                        ])
                        GO.bot.sendRsdnNotification('В форуме `%s` новое сообщение: %s'%(
                                                                                          GO.utf8(self.forums[fid]['name']),
                                                                                          text
                                                                                         ))
                        GO.bot.sendRsdnNotification(urls)
                        if message['parentId'] == 0:
                            GO.bot.sendChannelNotification(fchannel, 'Новый топик %s'%text)
                            GO.bot.sendChannelNotification(fchannel, urls)
                
                if len(newDataBit['newRating']):
                    for rating in newDataBit['newRating'][0]:
                        ratcount[GO.storage.updateRating(rating)] += 1
                if len(newDataBit['newModerate']):
                    for moderate in newDataBit['newModerate'][0]:
                        mdrcount[GO.storage.updateModerate(moderate)] += 1
            
            GO.bot.sendLog("RSDN. Обработка новых сообщений закончена, принято %d, из них новых: %d, обновлено: %d"%(msgcount[True]+msgcount[False], msgcount[False], msgcount[True]))
            GO.bot.sendLog("RSDN. Обработка новых оценок закончена, принято %d, из них новых: %d, обновлено: %d"%(ratcount[True]+ratcount[False], ratcount[False], ratcount[True]))
            GO.bot.sendLog("RSDN. Обработка новых отметок модерирования закончена, принято %d, из них новых: %d, обновлено: %d"%(mdrcount[True]+mdrcount[False], mdrcount[False], mdrcount[True]))
        newUsers = self.getNewUsers()
        if newUsers != None:
            usrcount = { True: 0, False: 0 }
            for newUsersBit in newUsers:
                for user in newUsersBit['users'][0]:
                    usrcount[GO.storage.updateRsdnUsers(user)] += 1
                    GO.bot.sendRsdnNotification('Новый пользователь `%s`, `%s`, `%s`: %s'%(
                                                                                GO.utf8(user['userName']),
                                                                                GO.utf8(user['userNick']),
                                                                                GO.utf8(user['realName']),
                                                                                self.getMemberUrlById(user['userId'])
                                                                              ))
            GO.bot.sendLog("RSDN. Обработка новых пользователей закончена, принято %d, из них новых: %d, обновлено: %d"%(usrcount[True]+usrcount[False], usrcount[False], usrcount[True]))
        if len(self.missedMembers):
            users = self.loadUsersByIds(self.missedMembers)
            self.missedMembers = []
            if users:
                usrcount = { True: 0, False: 0 }
                for user in users['users'][0]:
                    usrcount[GO.storage.updateRsdnUsers(user)] += 1
                GO.bot.sendLog("RSDN. Обработка новых пользователей закончена, принято %d, из них новых: %d, обновлено: %d"%(usrcount[True]+usrcount[False], usrcount[False], usrcount[True]))
        GO.bot.sendLog("RSDN. Синхронизация закончена")

    def getUser(self, uid):
        data = self.loadUsersByIds([uid])
        if data != None and list(data['users']):
            user = data['users'][0][0]
            GO.storage.updateRsdnUsers(user)
            return user
        return None

    def getTopic(self, mid):
        return self.getTopics([mid])[0]

    def getTopics(self, mids):
        (ok, client) = self._client()
        if ok:
            results = []
            GO.bot.sendLog("RSDN. Запуск получения %d топиков"%len(mids))
            request = client.factory.create('TopicRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            for mid in mids:
                request.messageIds.int.append(mid)
            answer = client.service.GetTopicByMessage(request)
            if len(answer['Messages']):
                self.mineMissedInMessages(answer['Messages'][0])
                msgcount = { True: 0, False: 0 }
                mdrcount = { True: 0, False: 0 }
                ratcount = { True: 0, False: 0 }
                message = dict()
                message['members'] = dict()
                message['exists'] = True
                for m in answer['Messages'][0]:
                    msgcount[GO.storage.updateRsdnMessages(m)] += 1
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
                message['count'] = msgcount[True]+msgcount[False]
                if len(answer['Rating']):
                    for rating in answer['Rating'][0]:
                        ratcount[GO.storage.updateRating(rating)] += 1
                if len(answer['Moderate']):
                    for moderate in answer['Moderate'][0]:
                        mdrcount[GO.storage.updateModerate(moderate)] += 1
                GO.bot.sendLog("RSDN. Обработка получения новых топиков закончена, принято %d сообщений, из них новых: %d, обновлено: %d"%(msgcount[True]+msgcount[False], msgcount[False], msgcount[True]))
                GO.bot.sendLog("RSDN. Обработка новых оценок закончена, принято %d, из них новых: %d, обновлено: %d"%(ratcount[True]+ratcount[False], ratcount[False], ratcount[True]))
                GO.bot.sendLog("RSDN. Обработка новых отметок модерирования закончена, принято %d, из них новых: %d, обновлено: %d"%(mdrcount[True]+mdrcount[False], mdrcount[False], mdrcount[True]))
                results.append(message)
            else:
                results.append({'exists': False})
        else:
            results.append({'exists': False})
        return results

    def getForumId(self, short_name):
        for fid in self.forums.keys():
            if self.forums[fid]['sname'] == short_name:
                return fid
        return None

    def stop(self):
        self.terminate = True

    def run(self):
        self.timerForumListSync.start()
        self.timerDataSync.start()
        self.timerAdditionalSync.start()
        while not self.terminate:
            time.sleep(1)
        self.timerAdditionalSync.stop()
        self.timerDataSync.stop()
        self.timerForumListSync.stop()

