#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys,socket, string, os, re, datetime
import psycopg2, psycopg2.pool
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO
from Configurable import CConfigurable
from threading import Lock

class CStorage(CConfigurable):
    def __init__(self):
        CConfigurable.__init__(self, '/etc/rsdn-irc-bot/storage.conf')
        self.pool = psycopg2.pool.ThreadedConnectionPool(2, 10, database=self.config['database'], user=self.config['user'], password=self.config['password'], host=self.config['host'], port=self.config['port'])
        self.debug = self.config['debug'] == 'true'

    def print_sql(self, sql):
        if self.debug:
            print '[-db-] %s'%re.sub(r'(\s+)', ' ', sql)

    def prepare(self, sql, data):
        connection = self.pool.getconn()
        cursor = connection.cursor()
        cursor.execute(sql, data)
        self.print_sql(cursor.query)
        return [connection, cursor]

    def queryRow(self, sql, data=tuple()):
        con = self.prepare(sql, data)
        result = con[1].fetchone()
        con[1].close()
        self.pool.putconn(con[0])
        return result

    def query(self, sql, data=tuple()):
        con = self.prepare(sql, data)
        result = con[1].fetchall()
        con[1].close()
        self.pool.putconn(con[0])
        return result

    def execute(self, sql, data=tuple()):
        con = self.prepare(sql, data)
        con[0].commit()
        con[1].close()
        self.pool.putconn(con[0])

    def callproc(self, procname, data=tuple()):
        connection = self.pool.getconn()
        cursor = connection.cursor()
        cursor.callproc(procname, data)
        self.print_sql(cursor.query)
        result = cursor.fetchall()
        cursor.close()
        self.pool.putconn(connection)
        return result

    def getNicknameId(self, nickname):
        sql = "SELECT id FROM nicknames WHERE nickname = %s"
        uid = self.queryRow(sql, (nickname,))
        if uid == None:
            self.execute("INSERT INTO nicknames (nickname) VALUES (%s)", (nickname,))
            uid = self.queryRow(sql, (nickname,))
        return uid[0]

    def logChannelMessage(self, nickname, channel, message, is_bot_command):
        nickname_id = self.getNicknameId(nickname)
        self.execute("INSERT INTO channels_logs (nickname_id, channel, message, is_bot_command) VALUES (%s, %s, %s, %s)", (nickname_id, channel, message, is_bot_command))
        self.execute("update nicknames set last_seen = %s", (datetime.datetime.now(),))

    def getTopOfChannel(self, channel, num):
        return self.query("""
            select nicknames.nickname, count(channels_logs.nickname_id) from channels_logs
            left join nicknames on nicknames.id=channels_logs.nickname_id
            where channel=%s
            group by nicknames.nickname
            order by 2 desc
            limit %s
        """, (channel, num))

    def getRsdnRowVersion(self, name):
        sql = "SELECT value FROM rsdn_row_versions WHERE name = %s"
        rid = self.queryRow(sql, (name,))
        if rid == None:
            self.execute("INSERT INTO rsdn_row_versions (name, value) VALUES (%s, %s)", (name, ''))
            rid = self.queryRow(sql, (name,))
        return rid[0]

    def setRsdnRowVersion(self, name, value):
        self.execute("update rsdn_row_versions set value=%s where name=%s", (value, name))

    def updateRsdnMessages(self, soap_message_info):
        return self.callproc('update_rsdn_messages',
                         (
                              soap_message_info['messageId'],
                              soap_message_info['topicId'],
                              soap_message_info['parentId'],
                              soap_message_info['userId'],
                              soap_message_info['forumId'],
                              soap_message_info['subject'],
                              soap_message_info['messageName'],
                              soap_message_info['message'],
                              soap_message_info['articleId'],
                              soap_message_info['messageDate'],
                              soap_message_info['updateDate'],
                              soap_message_info['userRole'],
                              soap_message_info['userTitle'],
                              soap_message_info['lastModerated'],
                              soap_message_info['closed']
                          ))[0][0]

    def updateRsdnUsers(self, soap_user_info):
    #i_id bigint, 
    #i_usernick character varying, 
    #i_username character varying, 
    #i_realname character varying, 
    #i_homepage character varying,
    # i_wherefrom character varying, 
    #  i_origin character varying,
    #   i_specialization character varying, 
    #    i_userclass smallint
        return self.callproc('update_rsdn_users', (
                              soap_user_info['userId'],
                              soap_user_info['userNick'],
                              soap_user_info['userName'],
                              soap_user_info['realName'],
                              soap_user_info['homePage'],
                              soap_user_info['whereFrom'],
                              soap_user_info['origin'],
                              soap_user_info['specialization'],
                              soap_user_info['userClass']
                          ))[0][0]

    def updateRating(self, soap_rating):
        exists = self.queryRow("SELECT count(*) FROM rsdn_rating WHERE messageid = %s and topicid = %s and userid = %s", (soap_rating['messageId'], soap_rating['topicId'], soap_rating['userId']))[0] > 0
        sql = ''
        if not exists:
            #GO.bot.sendLog("RSDN DB. Новая оценка")
            sql = """
                INSERT INTO rsdn_rating(userrating, rate, ratedate, messageid, topicid, userid)
                VALUES (%s, %s, %s, %s, %s, %s);
            """
        else:
            sql = """
                update rsdn_rating
                set userrating=%s, rate=%s, ratedate=%s
                where messageid=%s and topicid=%s and userid=%s;
            """
        self.execute(sql, (
                              soap_rating['userRating'],
                              soap_rating['rate'],
                              soap_rating['rateDate'],
                              soap_rating['messageId'],
                              soap_rating['topicId'],
                              soap_rating['userId']
                          ))
        return exists

    def updateModerate(self, soap_moderate):
        exists = self.queryRow("SELECT count(*) FROM rsdn_moderate WHERE messageid=%s and topicid=%s and userid=%s and forumid=%s", (soap_moderate['messageId'], soap_moderate['topicId'], soap_moderate['userId'], soap_moderate['forumId']))[0] > 0
        sql = ''
        if not exists:
            #GO.bot.sendLog("RSDN DB. Новая отметка модерирования")
            sql = """
                INSERT INTO rsdn_moderate(crerate, messageid, topicid, userid, forumid)
                VALUES (%s, %s, %s, %s, %s);
            """
        else:
            sql = """
                update rsdn_moderate
                set crerate=%s
                where messageid=%s and topicid=%s and userid=%s and forumid=%s;
            """
        self.execute(sql, (
                              soap_moderate['create'],
                              soap_moderate['messageId'],
                              soap_moderate['topicId'],
                              soap_moderate['userId'],
                              soap_moderate['forumId']
                          ))
        return exists

    def isIdInDb(self, iid, iid_field_name, table):
        return self.queryRow("SELECT 1 FROM %s WHERE %s = %s"%(table, iid_field_name, '%s'), (iid,)) != None

    def isUserInDb(self, uid):
        return self.isIdInDb(uid, 'id', 'rsdn_users') if uid else True

    def isMessageInDb(self, mid):
        return self.isIdInDb(mid, 'id', 'rsdn_messages') if mid else True

    def getUserIdByName(self, userName):
        return self.queryRow("SELECT id FROM rsdn_users WHERE username = %s", (userName,))

    def getTodayEvents(self, channel):
        result = dict()
        result['ch_msgs'] = self.queryRow("SELECT count(id) FROM channels_logs WHERE date(date_and_time) = date(now()) and is_bot_command='false' and channel=%s", (channel, ))[0]
        result['ch_bot']  = self.queryRow("SELECT count(id) FROM channels_logs WHERE date(date_and_time) = date(now()) and is_bot_command='true' and channel=%s", (channel, ))[0]
        fid = GO.rsdn.getForumId(channel[1:].lower())
        if fid:
            result['f_msgs'] = self.queryRow("SELECT count(id) FROM rsdn_messages WHERE date(messagedate) = date(now()) and forumid=%s", (fid, ))[0]
        else:
            result['f_msgs'] = u'Неприменимо'
        return result

    def getUserStats(self, uid):
        result = dict()
        result['f_msgs'] = self.queryRow("select count(id) from rsdn_messages where userid=%s", (uid, ))[0]
        sql = """
            select rsdn_users.username, count(rsdn_messages.id) 
            from rsdn_messages
            left join rsdn_users on rsdn_users.id = rsdn_messages.userid
            where rsdn_messages.parentid in (select id from rsdn_messages where userid=%s)
            group by rsdn_users.username
            order by 2 desc
            limit 10
        """
        result['t10_o2u'] = ', '.join(['%s:%s'%(mber,cnt) for mber, cnt in self.query(sql, (uid, ))])
        sql = """
            select rsdn_users.username, count(rsdn_messages.id)
            from rsdn_messages
            left join rsdn_users on rsdn_users.id = rsdn_messages.userid
            where rsdn_messages.id in (select parentid from rsdn_messages where userid=%s)
            group by rsdn_users.username
            order by 2 desc
            limit 10
        """
        result['t10_u2o'] = ', '.join(['%s:%s'%(mber,cnt) for mber, cnt in self.query(sql, (uid, ))])
        return result;

    def getDBStat(self):
        result = dict()
        for table in self.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"):
            result[table[0]] = self.queryRow("SELECT count(*) FROM %s"%table[0])[0]
        return result
        
    def getBrokenMessages(self, fids):
        sfids = ', '.join(map(str,fids))
        return self.query("""
            select i from 
                (
                    select distinct t1.parentid as i from rsdn_messages t1
                    where not exists (select * from rsdn_messages t2 where t1.parentid=t2.id) and t1.parentid != 0 and forumid in (%s)
                union
                    select distinct t1.topicid as i from rsdn_messages t1
                    where not exists(select * from rsdn_messages t2 where t1.topicid=t2.id) and t1.topicid != 0 and forumid in (%s)
                ) t
        """%(sfids, sfids))
        
    def count_rating(self, data):
        smile      = 0
        plus       = 0
        minus      = 0
        rate_num   = 0
        rate_total = 0
        for (userrating, rate) in data:
            if rate > 0:
                rate_num += 1
                rate_total += rate*userrating
            elif rate ==  0: minus += 1
            elif rate == -2: smile += 1
            elif rate == -4: plus  += 1
        return '%d(%d), +%d, -%d, %d x :)'%(rate_total, rate_num, plus, minus, smile)
    
    def getTopicRating(self, mid):
        return self.count_rating(self.query('select userrating, rate from rsdn_rating where messageid=%s', (mid, )))
        
    def getUserToOtherRating(self, uid):
        return self.count_rating(self.query('select userrating, rate from rsdn_rating where userid=%s', (uid, ))) # оценки выствленные uid пользователем другим сообщениям

    def getOtherToUserRating(self, uid):
        return self.count_rating(self.query("""
            select rsdn_rating.userrating, rsdn_rating.rate
            from rsdn_rating 
            left join rsdn_messages on rsdn_messages.id = rsdn_rating.messageid
            where rsdn_messages.userid=%s
            """
            , (uid, ))) # оценки выствленные другими пользователями сообщениям uid пользователя
        
    def getUser(self, uid):
        return self.queryRow("select usernick, username, realname, homepage, wherefrom, origin, userclass, specialization from rsdn_users where id=%s", (uid, ))
        
    def getMessage(self, mid):
        return self.queryRow("""
            select topicid, parentid, userid, forumid, subject, messagename, 
                   message, articleid, messagedate, updatedate, userrole, usertitle, 
                   lastmoderated, closed
            from rsdn_messages 
            where id=%s
            """, (mid, ))
        