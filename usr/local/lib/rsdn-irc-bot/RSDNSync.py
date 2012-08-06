#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, os, time, datetime, suds
from threading import Thread
from suds.client import Client, WebFault
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO, Timer
from Configurable import CConfigurable

class CRSDNSync(Thread, CConfigurable):
    def __init__(self):
        Thread.__init__(self)
        CConfigurable.__init__(self, '/etc/rsdn-irc-bot/rsdn.conf')
        self._terminate                    = False
        self.timer_sync_forums_list        = Timer.CTimer(int(self.config['timers']['sync_forum_list']), self.sync_forums_list)
        self.timer_sync_rsdn_data          = Timer.CTimer(int(self.config['timers']['sync_data'])      , self.sync_forums_data)
        self.forums                        = dict()
        self._missed_rsdn_messages_mids    = []
        self._missed_rsdn_members_uids     = []
        self.max_broken_per_sync_iteration = int(self.config['limits']['max_broken_messages_per_iteration'])
        self.min_broken_per_sync_iteration = int(self.config['limits']['min_broken_messages_per_iteration'])

    def _client(self):
        client = Client('http://www.rsdn.ru/ws/janusAT.asmx?WSDL')
        try:
            client.service.Check()
        except URLError(err):
           print err
           return [0, err]
        return [1, client]

    def get_message_url_by_id(self, mid): return u'http://www.rsdn.ru/forum/message/%d.aspx : mid %d'%(mid,mid)
    def get_member_url_by_id (self, uid): return u'http://www.rsdn.ru/Users/%d.aspx : uid %d'%(uid,uid)
    def get_forum_url_by_id  (self, fid): return u'http://rsdn.ru/forum/%s/ : fid %d'%(self.forums[fid]['sname'],fid)

    def sync_forums_list(self):
        (ok, client) = self._client()
        if ok:
            GO.bot.send_channel_log(u'RSDN. Список форумов. Запуск.')
            request = client.factory.create('ForumRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            request.forumsRowVersion = 0
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
                GO.bot.store_channel_topic(u'#%s'%forum['sname'], u'%s :: %s ( %s )'%(forum['gname'], forum['name'], self.get_forum_url_by_id(fid)))
                GO.bot.join_forum_channel(forum['sname'])
            GO.bot.send_channel_log(u'RSDN. Список форумов. Закончено.')

    def download_part_of_all(self):
        GO.bot.send_channel_log(u'RSDN. Дополнительная синхронизация. Запуск.')
        mids = []
        f = open('/home/rsdn/mid', 'r')
        mid = int(f.read())+1
        f.close()
        if mid > 1:
            startmid = mid
            GO.bot.send_channel_log(u'RSDN. Дополнительная синхронизация. Начинаем сканировать с %d'%mid)
            x = 0
            while x < 1000:
                mids.append(mid)
                while mid > 1 and mid in mids or GO.storage.is_rsdn_message_into_db(mid):
                    mid += 1
                x += 1
            f = open('/home/rsdn/mid', 'w')
            f.write('%d'%mid)
            f.close()
            x = 0
            GO.bot.send_channel_log(u'RSDN. Дополнительная синхронизация. Сканирование остановлено на %d. Просмотрено: %d'%(mid, mid-startmid))
            self.get_rsdn_topics(mids)
        GO.bot.send_channel_log(u'RSDN. Дополнительная синхронизация. Закончено.')

    def sync_new_data(self):
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
            request.ratingRowVersion   = GO.storage.get_rsdn_sync_row_version('ratingRowVersion')
            request.messageRowVersion  = GO.storage.get_rsdn_sync_row_version('messageRowVersion')
            request.moderateRowVersion = GO.storage.get_rsdn_sync_row_version('moderateRowVersion')
            if len(self._missed_rsdn_messages_mids) > self.min_broken_per_sync_iteration:
                for mid in self._missed_rsdn_messages_mids[:self.max_broken_per_sync_iteration]:
                    if not GO.storage.is_rsdn_message_into_db(mid):
                        request.breakMsgIds.int.append(mid)
                self._missed_rsdn_messages_mids = self._missed_rsdn_messages_mids[self.max_broken_per_sync_iteration:]
            answer = client.service.GetNewData(request)
            GO.storage.set_rsdn_sync_row_version('ratingRowVersion'  , answer['lastRatingRowVersion']  )
            GO.storage.set_rsdn_sync_row_version('messageRowVersion' , answer['lastForumRowVersion']   )
            GO.storage.set_rsdn_sync_row_version('moderateRowVersion', answer['lastModerateRowVersion'])
            return answer
        return None

    def sync_new_users(self):
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
                request.lastRowVersion = GO.storage.get_rsdn_sync_row_version('usersRowVersion')
                answer = client.service.GetNewUsers(request)
                done = answer['lastRowVersion'] == GO.storage.get_rsdn_sync_row_version('usersRowVersion')
                GO.storage.set_rsdn_sync_row_version('usersRowVersion', answer['lastRowVersion'])
                if not done:
                    result.append(answer)
            return result
        return None

    #def mineMissedInMessages(self, objects):
    #    for obj in objects:
    #        for s in ['parentId', 'topicId', 'messageId']:
    #            try:
    #                if obj[s] not in self._missed_rsdn_messages_mids and not GO.storage.is_rsdn_message_into_db(obj[s]):
    #                    self._missed_rsdn_messages_mids.append(obj[s])
    #            except: pass
    #        try:
    #            if obj['userId'] not in self._missed_rsdn_members_uids and not GO.storage.is_rsdn_member_into_db(obj['userId']):
    #                self._missed_rsdn_members_uids.append(obj['userId'])
    #        except: pass

    def sync_forums_data(self):
        #self.download_part_of_all()
        GO.bot.send_channel_log(u'RSDN. Синхронизация. Запуск.')
        msgcount = { True: 0, False: 0 }
        mdrcount = { True: 0, False: 0 }
        ratcount = { True: 0, False: 0 }
        sync_iteration = 0
        while True:
            msgcnt = 0
            ratcnt = 0
            mdrcnt = 0
            sync_iteration += 1
            GO.bot.send_channel_log(u'RSDN. Синхронизация. Итерация: %d.'%sync_iteration)
            GO.bot.send_channel_log(u'RSDN. Синхронизация. Будет загружено отсутствующих сообщений: %d'%(self.max_broken_per_sync_iteration if len(self._missed_rsdn_messages_mids) > self.max_broken_per_sync_iteration else len(self._missed_rsdn_messages_mids)))
            newData = self.sync_new_data()
            GO.bot.send_channel_log(u'RSDN. Синхронизация. Сообщения загружены. В итерацию не попало %d отсутствующих сообщений'%len(self._missed_rsdn_messages_mids))
            if newData == None:
                break
            if len(newData['newMessages']):
                GO.bot.send_channel_log(u'RSDN. Синхронизация. Обработка сообщений.')
                for message in newData['newMessages'][0]:
                    msgcount[GO.storage.update_rsdn_messages(message)] += 1
                    fid = message['forumId']
                    if fid and self.date_is_today(message['messageDate']):
                        forum_name = self.forums[fid]['sname']
                        text = u'`%s`. Автор: %s'%(
                                                   message['subject'], 
                                                   message['userNick'],
                                                  )
                        urls = u' | '.join([
                                              u'#%s'%forum_name,
                                              self.get_forum_url_by_id(fid),
                                              self.get_message_url_by_id(message['messageId']), 
                                              self.get_member_url_by_id(message['userId'])
                                          ])
                        GO.bot.send_rsdn_notification(u'В форуме `%s` новое сообщение: %s'%(
                                                                                          self.forums[fid]['name'],
                                                                                          text
                                                                                         ))
                        GO.bot.send_rsdn_notification(urls)
                        if message['parentId'] == 0:
                            GO.bot.send_channel_notification(forum_name, u'Новый топик %s'%text)
                            GO.bot.send_channel_notification(forum_name, urls)
                        else:
                            parent_msg = GO.storage.get_rsdn_message(message['parentId'])
                            if parent_msg != None:
                                GO.bot.send_user_notification(parent_msg[2], u'В форуме `%s` ответ на сообщение `%s`: %s'%(
                                                                                          self.forums[fid]['name'],
                                                                                          GO.unicod(parent_msg[4]),
                                                                                          text
                                                                                         ))
                                GO.bot.send_user_notification(parent_msg[2], urls)
                #self.mineMissedInMessages(newData['newMessages'][0])

            if len(newData['newRating']):
                GO.bot.send_channel_log(u'RSDN. Синхронизация. Обработка рейтинга.')
                for rating in newData['newRating'][0]:
                    ratcount[GO.storage.update_rsdn_rating(rating)] += 1
                    if self.date_is_today(rating['rateDate']):
                        target_msg = GO.storage.get_rsdn_message(rating['messageId'])
                        if target_msg == None: 
                            self.get_rsdn_topic(rating['messageId'])
                            target_msg = GO.storage.get_rsdn_message(rating['messageId'])
                        from_user = GO.storage.get_rsdn_member(rating['userId'])
                        if from_user == None:
                            self.get_rsdn_member(rating['userId'])
                            from_user = GO.storage.get_rsdn_member(rating['userId'])
                        rate = rating['rate']
                        r = ''
                        if   rate  >  0: r = u'%d'%(rating['userRating']*rate)
                        elif rate ==  0: r = u'-1'
                        elif rate == -2: r = u':)'
                        elif rate == -4: r = u'+1'
                        text = u'Оценка %s сообщению `%s` от пользователя %s'%(
                                                                                r, 
                                                                                GO.unicod(target_msg[4]) if target_msg != None else u'--нет-в-бд--', 
                                                                                GO.unicod(from_user[1])  if target_msg != None else u'--нет-в-бд--'
                                                                              )
                        urls = u' | '.join([
                                              self.get_message_url_by_id(rating['messageId']), 
                                              self.get_member_url_by_id(rating['userId'])
                                            ])
                        GO.bot.send_rsdn_notification(text)
                        GO.bot.send_rsdn_notification(urls)
                        if target_msg != None:
                            GO.bot.send_user_notification(target_msg[2], u'В форуме `%s` ответ на сообщение `%s`: %s'%(
                                                                                          self.forums[fid]['name'],
                                                                                          GO.unicod(target_msg[4]),
                                                                                          text
                                                                                         ))
                            GO.bot.send_user_notification(target_msg[2], urls)
                #self.mineMissedInMessages(newData['newRating'][0])

            if len(newData['newModerate']):
                GO.bot.send_channel_log(u'RSDN. Синхронизация. Обработка модерирования.')
                for moderate in newData['newModerate'][0]:
                    mdrcount[GO.storage.update_rsdn_moderate(moderate)] += 1
                #self.mineMissedInMessages(newData['newModerate'][0])

            GO.bot.send_channel_log(u'RSDN. Синхронизация. Получение списка отсутствующих сообщений.')
            for mid in GO.storage.get_broken_messages(list(self.forums.keys())):
                if mid not in self._missed_rsdn_messages_mids:
                        self._missed_rsdn_messages_mids.append(mid)
            #print len(newData['newRating']), len(newData['newModerate']), len(newData['newMessages']), len(self._missed_rsdn_messages_mids)
            if len(newData['newRating']) == 0 and len(newData['newModerate']) == 0 and len(newData['newMessages']) == 0 and len(self._missed_rsdn_messages_mids) < self.min_broken_per_sync_iteration:
                break
        GO.bot.send_channel_log(u'RSDN. Синхронизация. Собщения: принято %d, из них новых %d, обновлено %d.'%(msgcount[True]+msgcount[False], msgcount[False], msgcount[True]))
        GO.bot.send_channel_log(u'RSDN. Синхронизация. Оценки: принято %d, из них новых %d, обновлено %d.'%(ratcount[True]+ratcount[False], ratcount[False], ratcount[True]))
        GO.bot.send_channel_log(u'RSDN. Синхронизация. Модерирование: принято %d, из них новых %d, обновлено %d.'%(mdrcount[True]+mdrcount[False], mdrcount[False], mdrcount[True]))
        newUsers = self.sync_new_users()
        if newUsers != None:
            usrcount = { True: 0, False: 0 }
            for newUsersBit in newUsers:
                for user in newUsersBit['users'][0]:
                    usrcount[GO.storage.update_rsdn_members(user)] += 1
                    GO.bot.send_rsdn_notification(u'Новый пользователь `%s`, `%s`, `%s`: %s'%(
                                                                                user['userName'],
                                                                                user['userNick'],
                                                                                user['realName'],
                                                                                self.get_member_url_by_id(user['userId'])
                                                                              ))
            GO.bot.send_channel_log(u'RSDN. Синхронизация. Новые пользователи: принято %d, из них новых %d, обновлено %d.'%(usrcount[True]+usrcount[False], usrcount[False], usrcount[True]))
        if len(self._missed_rsdn_members_uids):
            users = self.load_members_by_ids(self._missed_rsdn_members_uids)
            self._missed_rsdn_members_uids = []
            if users:
                usrcount = { True: 0, False: 0 }
                for user in users['users'][0]:
                    usrcount[GO.storage.update_rsdn_members(user)] += 1
                GO.bot.send_channel_log(u'RSDN. Синхронизация. Пропущенные пользователи: принято %d, из них новых %d, обновлено %d.'%(usrcount[True]+usrcount[False], usrcount[False], usrcount[True]))
        GO.bot.send_channel_log(u'RSDN. Синхронизация. Закончено.')

    def get_rsdn_member(self, uid):
        GO.bot.send_channel_log(u'RSDN. Получение пользователя по его идентификатору (%d).'%uid)
        data = self.load_members_by_ids([uid])
        if data != None and list(data['users']):
            user = data['users'][0][0]
            GO.storage.update_rsdn_members(user)
            return user
        return None

    def load_members_by_ids(self, ids):
        if len(self.forums) == 0: return
        (ok, client) = self._client()
        if ok:
            GO.bot.send_channel_log(u'RSDN. Получение пользователей. Запуск. Учетных записей в запросе: %d.'%len(ids))
            request = client.factory.create('UserByIdsRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            for uid in ids:
                request.userIds.int.append(uid)
            answer = client.service.GetUserByIds(request)
            GO.bot.send_channel_log(u'RSDN. Получение пользователей. Закончено.')
            return answer
        return None

    def get_rsdn_topic(self, mid):
        return self.get_rsdn_topics([mid])[0]

    def get_rsdn_topics(self, mids):
        (ok, client) = self._client()
        if ok:
            results = []
            GO.bot.send_channel_log(u'RSDN. Получение топиков. Запуск. Топиков в запросе: %d.'%len(mids))
            request = client.factory.create('TopicRequest')
            request.userName = self.config['auth']['user']
            request.password = self.config['auth']['password']
            for mid in mids:
                request.messageIds.int.append(mid)
            answer = client.service.GetTopicByMessage(request)
            GO.bot.send_channel_log(u'RSDN. Получение топиков. Сообщения загружены.')
            if len(answer['Messages']):
                GO.bot.send_channel_log(u'RSDN. Получение топиков. Обработка сообщений.')
                msgcount = { True: 0, False: 0 }
                mdrcount = { True: 0, False: 0 }
                ratcount = { True: 0, False: 0 }
                message = dict()
                message['members'] = dict()
                message['exists'] = True
                for m in answer['Messages'][0]:
                    msgcount[GO.storage.update_rsdn_messages(m)] += 1
                    nick = m['userNick']
                    message['members'][nick] = 1 if nick not in message['members'] else message['members'][nick] + 1
                    if m['messageId'] in mids:
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
                #self.mineMissedInMessages(answer['Messages'][0])
                message['count'] = msgcount[True]+msgcount[False]
                if len(answer['Rating']):
                    GO.bot.send_channel_log(u'RSDN. Получение топиков. Обработка рейтинга.')
                    #self.mineMissedInMessages(answer['Rating'][0])
                    for rating in answer['Rating'][0]:
                        ratcount[GO.storage.update_rsdn_rating(rating)] += 1
                if len(answer['Moderate']):
                    GO.bot.send_channel_log(u'RSDN. Получение топиков. Обработка модерирования.')
                    #self.mineMissedInMessages(answer['Moderate'][0])
                    for moderate in answer['Moderate'][0]:
                        mdrcount[GO.storage.update_rsdn_moderate(moderate)] += 1
                GO.bot.send_channel_log(u'RSDN. Получение топиков. Сообщения: принято %d, из них новых %d, обновлено %d.'%(msgcount[True]+msgcount[False], msgcount[False], msgcount[True]))
                GO.bot.send_channel_log(u'RSDN. Получение топиков. Оценки:, принято %d, из них новых %d, обновлено %d.'%(ratcount[True]+ratcount[False], ratcount[False], ratcount[True]))
                GO.bot.send_channel_log(u'RSDN. Получение топиков. Модерирование: принято %d, из них новых %d, обновлено %d.'%(mdrcount[True]+mdrcount[False], mdrcount[False], mdrcount[True]))
                results.append(message)
            else:
                results.append({'exists': False})
            GO.bot.send_channel_log(u'RSDN. Получение топиков. Закончено.')
        else:
            results.append({'exists': False})
        return results

    def auth_rsdn_member(self, username, password):
        uid = GO.storage.get_rsdn_member_id(username)
        if uid > 0:
            (ok, client) = self._client()
            if ok:
                GO.bot.send_channel_log(u'RSDN. Авторизация пользователя.')
                try:
                    request = client.factory.create('UserByIdsRequest')
                    request.userName = username
                    request.password = password
                    request.userIds.int.append(uid)
                    answer = client.service.GetUserByIds(request)
                    GO.bot.send_channel_log(u'RSDN. Авторизация пользователя. Успешно.')
                    return [True, uid]
                except WebFault, e:
                    GO.bot.send_channel_log(u'RSDN. Авторизация пользователя. Провал.')
                    return [False, uid]
            return [False, 0]
        return [False, 0]

    def get_forum_id(self, short_name):
        for fid in self.forums.keys():
            if self.forums[fid]['sname'] == short_name:
                return fid
        return None

    def date_is_today(self, date):
        return datetime.date.today() == date.date()

    def stop(self):
        self._terminate = True

    def run(self):
        self.timer_sync_forums_list.start()
        self.timer_sync_rsdn_data.start()
        while not self._terminate: time.sleep(1)
        self.timer_sync_rsdn_data.stop ()
        self.timer_sync_forums_list.stop ()

