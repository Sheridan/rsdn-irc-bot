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
        self.max_broken_per_sync_iteration = int(self.config['limits']['max_broken_messages_per_iteration'])

    def _client(self):
        client = Client('http://www.rsdn.ru/ws/janusAT.asmx?WSDL')
        try:
            client.service.Check()
        except URLError(err):
           print err
           return [0, err]
        return [1, client]

    def getMessageUrlById(self, mid):
        return u'http://www.rsdn.ru/forum/message/%d.aspx : mid %d'%(mid,mid)

    def getMemberUrlById(self, uid):
        return u'http://www.rsdn.ru/Users/%d.aspx : uid %d'%(uid,uid)
        
    def getForumUrlById(self, fid):
        return u'http://rsdn.ru/forum/%s/ : fid %d'%(self.forums[fid]['sname'],fid)

    def syncForumsList(self):
        (ok, client) = self._client()
        if ok:
            GO.bot.sendLog(u'RSDN. Список форумов. Запуск.')
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
                GO.bot.store_channel_topic(u'#%s'%forum['sname'], u'%s :: %s ( %s )'%(forum['gname'], forum['name'], self.getForumUrlById(fid)))
                GO.bot.join_forum_channel(forum['sname'])
            GO.bot.sendLog(u'RSDN. Список форумов. Закончено.')

    def additionalSync(self):
        GO.bot.sendLog(u'RSDN. Дополнительная синхронизация. Запуск.')
        mids = []
        f = open('/home/rsdn/mid', 'r')
        mid = int(f.read()) - 1
        f.close()
        if mid > 1:
            startmid = mid
            GO.bot.sendLog(u'RSDN. Дополнительная синхронизация. Начинаем сканировать с %d'%mid)
            x = 0
            while x < 1000:
                mids.append(mid)
                while mid > 1 and mid in mids or GO.storage.isMessageInDb(mid):
                    mid -= 1
                x += 1
            f = open('/home/rsdn/mid', 'w')
            f.write('%d'%mid)
            f.close()
            x = 0
            GO.bot.sendLog(u'RSDN. Дополнительная синхронизация. Сканирование остановлено на %d. Просмотрено: %d'%(mid, startmid-mid))
            self.getTopics(mids)
        GO.bot.sendLog(u'RSDN. Дополнительная синхронизация. Закончено.')

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
            request.ratingRowVersion   = GO.storage.getRsdnRowVersion('ratingRowVersion')
            request.messageRowVersion  = GO.storage.getRsdnRowVersion('messageRowVersion')
            request.moderateRowVersion = GO.storage.getRsdnRowVersion('moderateRowVersion')
            for mid in self.missedMessages[:self.max_broken_per_sync_iteration]:
                if not GO.storage.isMessageInDb(mid):
                    request.breakMsgIds.int.append(mid)
            self.missedMessages = self.missedMessages[self.max_broken_per_sync_iteration:]
            answer = client.service.GetNewData(request)
            #print answer
            GO.storage.setRsdnRowVersion('ratingRowVersion'  , answer['lastRatingRowVersion']  )
            GO.storage.setRsdnRowVersion('messageRowVersion' , answer['lastForumRowVersion']   )
            GO.storage.setRsdnRowVersion('moderateRowVersion', answer['lastModerateRowVersion'])
            return answer
        return None

    def getNewUsers(self):
        if len(self.forums) == 0: return
        (ok, client) = self._client()
        if ok:
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

    def mineMissedInMessages(self, objects):
        for obj in objects:
            for s in ['parentId', 'topicId', 'messageId']:
                try:
                    if obj[s] not in self.missedMessages and not GO.storage.isMessageInDb(obj[s]):
                        self.missedMessages.append(obj[s])
                except: pass
            try:
                if obj['userId'] not in self.missedMembers and not GO.storage.isUserInDb(obj['userId']):
                    self.missedMembers.append(obj['userId'])
            except: pass

    def syncForumsData(self):
        self.additionalSync()
        GO.bot.sendLog(u'RSDN. Синхронизация. Запуск.')
        msgcount = { True: 0, False: 0 }
        mdrcount = { True: 0, False: 0 }
        ratcount = { True: 0, False: 0 }
        sync_iteration = 0
        while True:
            msgcnt = 0
            ratcnt = 0
            mdrcnt = 0
            sync_iteration += 1
            GO.bot.sendLog(u'RSDN. Синхронизация. Итерация: %d.'%sync_iteration)
            GO.bot.sendLog(u'RSDN. Синхронизация. Будет загружено отсутствующих сообщений: %d'%(self.max_broken_per_sync_iteration if len(self.missedMessages) > self.max_broken_per_sync_iteration else len(self.missedMessages)))
            newData = self.getNewData()
            GO.bot.sendLog(u'RSDN. Синхронизация. Сообщения загружены. В итерацию не попало %d отсутствующих сообщений'%len(self.missedMessages))
            if newData == None:
                break
            if len(newData['newMessages']):
                GO.bot.sendLog(u'RSDN. Синхронизация. Обработка сообщений.')
                for message in newData['newMessages'][0]:
                    msgcount[GO.storage.updateRsdnMessages(message)] += 1
                    fid = message['forumId']
                    if fid:
                        forum_name = self.forums[fid]['sname']
                        text = u'`%s`. Автор: %s'%(
                                                   message['subject'], 
                                                   message['userNick'],
                                                 )
                        urls = u' | '.join([
                                          forum_name,
                                          self.getForumUrlById(fid),
                                          self.getMessageUrlById(message['messageId']), 
                                          self.getMemberUrlById(message['userId'])
                                        ])
                        GO.bot.sendRsdnNotification(u'В форуме `%s` новое сообщение: %s'%(
                                                                                          self.forums[fid]['name'],
                                                                                          text
                                                                                         ))
                        GO.bot.sendRsdnNotification(urls)
                        if message['parentId'] == 0:
                            GO.bot.send_channel_notification(forum_name, u'Новый топик %s'%text)
                            GO.bot.send_channel_notification(forum_name, urls)
                self.mineMissedInMessages(newData['newMessages'][0])

            if len(newData['newRating']):
                GO.bot.sendLog(u'RSDN. Синхронизация. Обработка рейтинга.')
                for rating in newData['newRating'][0]:
                    ratcount[GO.storage.updateRating(rating)] += 1
                    target_msg = GO.storage.getMessage(rating['messageId'])
                    from_user = GO.storage.getUser(rating['userId'])
                    rate = rating['rate']
                    r = ''
                    if   rate  >  0: r = u'%d'%(rating['userRating']*rate)
                    elif rate ==  0: r = u'-1'
                    elif rate == -2: r = u':)'
                    elif rate == -4: r = u'+1'
                    GO.bot.sendRsdnNotification(u'Оценка %s сообщению `%s` от пользователя %s'%(
                                                                                                  r, 
                                                                                                  GO.unicod(target_msg[4]) if target_msg else u'--нет-в-бд--', 
                                                                                                  GO.unicod(from_user[1])  if target_msg else u'--нет-в-бд--'
                                                                                                ))
                    GO.bot.sendRsdnNotification(u' | '.join([
                                          self.getMessageUrlById(rating['messageId']), 
                                          self.getMemberUrlById(rating['userId'])
                                        ]))
                self.mineMissedInMessages(newData['newRating'][0])

            if len(newData['newModerate']):
                GO.bot.sendLog(u'RSDN. Синхронизация. Обработка модерирования.')
                for moderate in newData['newModerate'][0]:
                    mdrcount[GO.storage.updateModerate(moderate)] += 1
                self.mineMissedInMessages(newData['newRating'][0])

            for mid in GO.storage.getBrokenMessages(list(self.forums.keys())):
                if mid not in self.missedMessages:
                        self.missedMessages.append(mid)
            #print len(newData['newRating']), len(newData['newModerate']), len(newData['newMessages']), len(self.missedMessages)
            if len(newData['newRating']) == 0 and len(newData['newModerate']) == 0 and len(newData['newMessages']) == 0 and len(self.missedMessages) == 0:
                break
        GO.bot.sendLog(u'RSDN. Синхронизация. Собщения: принято %d, из них новых %d, обновлено %d.'%(msgcount[True]+msgcount[False], msgcount[False], msgcount[True]))
        GO.bot.sendLog(u'RSDN. Синхронизация. Оценки: принято %d, из них новых %d, обновлено %d.'%(ratcount[True]+ratcount[False], ratcount[False], ratcount[True]))
        GO.bot.sendLog(u'RSDN. Синхронизация. Модерирование: принято %d, из них новых %d, обновлено %d.'%(mdrcount[True]+mdrcount[False], mdrcount[False], mdrcount[True]))
        newUsers = self.getNewUsers()
        if newUsers != None:
            usrcount = { True: 0, False: 0 }
            for newUsersBit in newUsers:
                for user in newUsersBit['users'][0]:
                    usrcount[GO.storage.updateRsdnUsers(user)] += 1
                    GO.bot.sendRsdnNotification(u'Новый пользователь `%s`, `%s`, `%s`: %s'%(
                                                                                user['userName'],
                                                                                user['userNick'],
                                                                                user['realName'],
                                                                                self.getMemberUrlById(user['userId'])
                                                                              ))
            GO.bot.sendLog(u'RSDN. Синхронизация. Новые пользователи: принято %d, из них новых %d, обновлено %d.'%(usrcount[True]+usrcount[False], usrcount[False], usrcount[True]))
        if len(self.missedMembers):
            users = self.loadUsersByIds(self.missedMembers)
            self.missedMembers = []
            if users:
                usrcount = { True: 0, False: 0 }
                for user in users['users'][0]:
                    usrcount[GO.storage.updateRsdnUsers(user)] += 1
                GO.bot.sendLog(u'RSDN. Синхронизация. Пропущенные пользователи: принято %d, из них новых %d, обновлено %d.'%(usrcount[True]+usrcount[False], usrcount[False], usrcount[True]))
        GO.bot.sendLog(u'RSDN. Синхронизация. Закончено.')

    def getUser(self, uid):
        GO.bot.sendLog(u'RSDN. Получение пользователя по его идентификатору.')
        data = self.loadUsersByIds([uid])
        if data != None and list(data['users']):
            user = data['users'][0][0]
            GO.storage.updateRsdnUsers(user)
            return user
        return None

    def loadUsersByIds(self, ids):
        if len(self.forums) == 0: return
        (ok, client) = self._client()
        if ok:
            GO.bot.sendLog(u'RSDN. Получение пользователей. Запуск. Учетных записей в запросе: %d.'%len(ids))
            request = client.factory.create('UserByIdsRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            for uid in ids:
                request.userIds.int.append(uid)
            answer = client.service.GetUserByIds(request)
            GO.bot.sendLog(u'RSDN. Получение пользователей. Закончено.')
            return answer
        return None

    def getTopic(self, mid):
        return self.getTopics([mid])[0]

    def getTopics(self, mids):
        (ok, client) = self._client()
        if ok:
            results = []
            GO.bot.sendLog(u'RSDN. Получение топиков. Запуск. Топиков в запросе: %d.'%len(mids))
            request = client.factory.create('TopicRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            for mid in mids:
                request.messageIds.int.append(mid)
            answer = client.service.GetTopicByMessage(request)
            GO.bot.sendLog(u'RSDN. Получение топиков. Сообщения загружены.')
            if len(answer['Messages']):
                GO.bot.sendLog(u'RSDN. Получение топиков. Обработка сообщений.')
                msgcount = { True: 0, False: 0 }
                mdrcount = { True: 0, False: 0 }
                ratcount = { True: 0, False: 0 }
                message = dict()
                message['members'] = dict()
                message['exists'] = True
                for m in answer['Messages'][0]:
                    msgcount[GO.storage.updateRsdnMessages(m)] += 1
                    nick = m['userNick']
                    message['members'][nick] = 1 if nick not in message['members'] else message['members'][nick] + 1
                    if m['messageId'] == mid:
                        message['self'] = {
                                            'subject': m['subject'], 
                                            'user'   : nick,
                                            'message': m['message'], 
                                            'date'   : m['messageDate'],
                                            'mid'    : m['messageId'], 
                                            'closed' : m['closed']
                                          }
                    if m['parentId'] == 0:
                        message['top'] = {
                                            'subject': m['subject'], 
                                            'user'   : nick,
                                            'date'   : m['messageDate'],
                                            'mid'    : m['messageId'], 
                                            'closed' : m['closed']
                                          }
                self.mineMissedInMessages(answer['Messages'][0])
                message['count'] = msgcount[True]+msgcount[False]
                if len(answer['Rating']):
                    GO.bot.sendLog(u'RSDN. Получение топиков. Обработка рейтинга.')
                    self.mineMissedInMessages(answer['Rating'][0])
                    for rating in answer['Rating'][0]:
                        ratcount[GO.storage.updateRating(rating)] += 1
                if len(answer['Moderate']):
                    GO.bot.sendLog(u'RSDN. Получение топиков. Обработка модерирования.')
                    self.mineMissedInMessages(answer['Moderate'][0])
                    for moderate in answer['Moderate'][0]:
                        mdrcount[GO.storage.updateModerate(moderate)] += 1
                GO.bot.sendLog(u'RSDN. Получение топиков. Сообщения: принято %d, из них новых %d, обновлено %d.'%(msgcount[True]+msgcount[False], msgcount[False], msgcount[True]))
                GO.bot.sendLog(u'RSDN. Получение топиков. Оценки:, принято %d, из них новых %d, обновлено %d.'%(ratcount[True]+ratcount[False], ratcount[False], ratcount[True]))
                GO.bot.sendLog(u'RSDN. Получение топиков. Модерирование: принято %d, из них новых %d, обновлено %d.'%(mdrcount[True]+mdrcount[False], mdrcount[False], mdrcount[True]))
                results.append(message)
            else:
                results.append({'exists': False})
            GO.bot.sendLog(u'RSDN. Получение топиков. Закончено.')
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
        while not self.terminate:
            time.sleep(1)
        self.timerDataSync.stop()
        self.timerForumListSync.stop()

