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
            mForumRequest = client.factory.create('ForumRequest')
            mForumRequest.userName = self.config['auth']['user']
            mForumRequest.password = self.config['auth']['password']
            mForumRequest.forumsRowVersion = self.forumsRowVersion
            result = client.service.GetForumList(mForumRequest)
            groups = dict()
            #print result
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
                GO.bot.joinChannel(forum['sname'], '%s :: %s ( http://rsdn.ru/forum/%s/ )'%(forum['gname'], forum['name'], forum['sname']))

    def syncForumsData(self):
        if len(self.forums) == 0: return
        (ok, client) = self._client()
        if ok:
            GO.bot.sendLog("RSDN. Запуск проверки новых сообщений на форумах")
            mChangeRequest = client.factory.create('ChangeRequest')
            mChangeRequest.userName = self.config['auth']['user']
            mChangeRequest.password = self.config['auth']['password']
            mChangeRequest.ratingRowVersion   = GO.storage.getRsdnRowVersion('ratingRowVersion')
            mChangeRequest.messageRowVersion  = GO.storage.getRsdnRowVersion('messageRowVersion')
            mChangeRequest.moderateRowVersion = GO.storage.getRsdnRowVersion('moderateRowVersion')
            mChangeRequest.maxOutput = int(self.config['limits']['max_sync_output'])
            for fid in self.forums.keys():
                forum = self.forums[fid]
                mRequestForumInfo = client.factory.create('RequestForumInfo')
                mRequestForumInfo.forumId = forum['fid']
                mRequestForumInfo.isFirstRequest = mChangeRequest.messageRowVersion == ''
                mChangeRequest.subscribedForums.RequestForumInfo.append(mRequestForumInfo)
            result = client.service.GetNewData(mChangeRequest)
            #print result
            GO.storage.setRsdnRowVersion('ratingRowVersion'  , result['lastRatingRowVersion']  )
            GO.storage.setRsdnRowVersion('messageRowVersion' , result['lastForumRowVersion']   )
            GO.storage.setRsdnRowVersion('moderateRowVersion', result['lastModerateRowVersion'])
            if len(result['newMessages']) > 0:
                for message in result['newMessages'][0]:
                    text = '`%s` ( %s ). Автор: %s ( %s )'%(
                                                               GO.utf8(message['subject']), 
                                                               self.getMessageUrlById(message['messageId']), 
                                                               GO.utf8(message['userNick']),
                                                               self.getMemberUrlById(message['userId'])
                                                             )
                    GO.bot.sendRsdnNotification('В форуме `%s` ( %s ) новое сообщение: %s'%(
                                                                                          GO.utf8(self.forums[message['forumId']]['name']),
                                                                                          GO.utf8(self.getForumUrlById(message['forumId'])),
                                                                                          text
                                                                                         ))
                    if message['parentId'] == 0:
                        GO.bot.sendChannelText('#'+GO.utf8(self.forums[message['forumId']]['sname']), 'Новый топик %s'%text)

    def getTopic(self, mid):
        (ok, client) = self._client()
        if ok:
            GO.bot.sendLog("RSDN. Запуск получения топика")
            mTopicRequest = client.factory.create('TopicRequest')
            mTopicRequest.userName = self.config['auth']['user']
            mTopicRequest.password = self.config['auth']['password']
            mTopicRequest.messageIds.int.append(mid)
            result = client.service.GetTopicByMessage(mTopicRequest)
            if len(result['Messages']):
                msgcount = 0
                message = dict()
                message['members'] = dict()
                message['exists'] = True
                for m in result['Messages'][0]:
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

