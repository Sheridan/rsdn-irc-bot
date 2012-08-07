#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, os, re, datetime
import psycopg2, psycopg2.pool
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO
from Configurable import CConfigurable

class CStorage(CConfigurable):
    def __init__(self):
        CConfigurable.__init__(self, '/etc/rsdn-irc-bot/storage.conf')
        self.pool = psycopg2.pool.ThreadedConnectionPool(3, 20, 
                                                         database = self.config['database'], 
                                                         user     = self.config['user'], 
                                                         password = self.config['password'], 
                                                         host     = self.config['host'], 
                                                         port     = self.config['port'])
        self.debug = self.config['debug'] == 'true'

    def stop(self):
        self.pool.closeall()

    def print_sql(self, sql):
        if self.debug:
            print '[-db-] %s'%re.sub(r'(\s+)', ' ', sql)

    def prepare(self, sql, data):
        connection = self.pool.getconn()
        cursor = connection.cursor()
        cursor.execute(sql, data)
        self.print_sql(cursor.query)
        return [connection, cursor]

    def query_row(self, sql, data=tuple()):
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
        connection.commit()
        cursor.close()
        self.pool.putconn(connection)
        return result

    def get_irc_nickname_id(self, nickname):
        sql = "SELECT id FROM nicknames WHERE nickname = %s"
        uid = self.query_row(sql, (nickname,))
        if uid == None:
            self.execute("INSERT INTO nicknames (nickname) VALUES (%s)", (nickname,))
            uid = self.query_row(sql, (nickname,))
        return uid[0]

    def store_channel_message(self, nickname, channel, message, is_bot_command):
        nickname_id = self.get_irc_nickname_id(nickname)
        self.execute("INSERT INTO channels_logs (nickname_id, channel, message, is_bot_command) VALUES (%s, %s, %s, %s)", (nickname_id, channel, message, is_bot_command))
        self.execute("update nicknames set last_seen = %s where id = %s", (datetime.datetime.now(), nickname_id))

    def get_channel_top(self, channel, num):
        return self.query("""
            select nicknames.nickname, count(channels_logs.nickname_id) from channels_logs
            left join nicknames on nicknames.id=channels_logs.nickname_id
            where channel=%s
            group by nicknames.nickname
            order by 2 desc
            limit %s
        """, (channel, num))

    def get_rsdn_sync_row_version(self, name):
        sql = "SELECT value FROM rsdn_row_versions WHERE name = %s"
        rid = self.query_row(sql, (name,))
        if rid == None:
            self.execute("INSERT INTO rsdn_row_versions (name, value) VALUES (%s, %s)", (name, ''))
            rid = self.query_row(sql, (name,))
        return rid[0]

    def set_rsdn_sync_row_version(self, name, value):
        self.execute("update rsdn_row_versions set value=%s where name=%s", (value, name))

    def update_rsdn_messages(self, soap_message_info):
        #print soap_message_info
        #print '-------------------------------------------------------------'
        return self.callproc('update_rsdn_messages', (
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

    def update_rsdn_members(self, soap_user_info):
        #print soap_user_info
        #print '-------------------------------------------------------------'
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

    def update_rsdn_rating(self, soap_rating):
        exists = self.query_row("SELECT count(*) FROM rsdn_rating WHERE messageid = %s and topicid = %s and userid = %s", (soap_rating['messageId'], soap_rating['topicId'], soap_rating['userId']))[0] > 0
        sql = ''
        if not exists:
            #GO.bot.send_channel_log("RSDN DB. Новая оценка")
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

    def update_rsdn_moderate(self, soap_moderate):
        exists = self.query_row("SELECT count(*) FROM rsdn_moderate WHERE messageid=%s and topicid=%s and userid=%s and forumid=%s", (soap_moderate['messageId'], soap_moderate['topicId'], soap_moderate['userId'], soap_moderate['forumId']))[0] > 0
        sql = ''
        if not exists:
            #GO.bot.send_channel_log("RSDN DB. Новая отметка модерирования")
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

    def record_into_db(self, iid, iid_field_name, table):
        return self.query_row("SELECT 1 FROM %s WHERE %s = %s"%(table, iid_field_name, '%s'), (iid,)) != None

    def is_rsdn_member_into_db (self, uid): return self.record_into_db(uid, 'id', 'rsdn_users'   ) if uid else True
    def is_rsdn_message_into_db(self, mid): return self.record_into_db(mid, 'id', 'rsdn_messages') if mid else True

    def get_rsdn_member_id_by_name(self, userName):
        return self.query_row("SELECT id FROM rsdn_users WHERE username = %s", (userName,))

    def get_today_events(self, channel):
        result = dict()
        result['ch_msgs'] = self.query_row("SELECT count(id) FROM channels_logs WHERE date(date_and_time) = date(now()) and is_bot_command='false' and channel=%s", (channel, ))[0]
        result['ch_bot']  = self.query_row("SELECT count(id) FROM channels_logs WHERE date(date_and_time) = date(now()) and is_bot_command='true' and channel=%s", (channel, ))[0]
        fid = GO.rsdn.get_forum_id(channel[1:].lower())
        if fid:
            result['f_msgs'] = self.query_row("SELECT count(id) FROM rsdn_messages WHERE date(messagedate) = date(now()) and forumid=%s", (fid, ))[0]
        else:
            result['f_msgs'] = u'Неприменимо'
        return result

    def get_rsdn_member_stats(self, uid):
        result = dict()
        result['f_msgs'] = self.query_row("select count(id) from rsdn_messages where userid=%s", (uid, ))[0]
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
        return result

    def get_db_stats(self):
        result = dict()
        for table in self.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"):
            result[table[0]] = self.query_row("SELECT count(*) FROM %s"%table[0])[0]
        return result

    def get_broken_messages(self, fids):
        sfids = ', '.join(map(str, fids))
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

    def get_rsdn_topic_rating(self, mid):
        return self.count_rating(self.query('select userrating, rate from rsdn_rating where messageid=%s', (mid, )))

    def get_rsdn_member_rate_others(self, uid):
        return self.count_rating(self.query('select userrating, rate from rsdn_rating where userid=%s', (uid, ))) # оценки выствленные uid пользователем другим сообщениям

    def get_rsdn_others_rate_member(self, uid):
        return self.count_rating(self.query("""
            select rsdn_rating.userrating, rsdn_rating.rate
            from rsdn_rating 
            left join rsdn_messages on rsdn_messages.id = rsdn_rating.messageid
            where rsdn_messages.userid=%s
            """
            , (uid, ))) # оценки выствленные другими пользователями сообщениям uid пользователя

    def get_rsdn_member(self, uid):
        return self.query_row("select usernick, username, realname, homepage, wherefrom, origin, userclass, specialization from rsdn_users where id=%s", (uid, ))

    def get_rsdn_member_id(self, username):
        result = self.query_row("select id from rsdn_users where username = %s", (username, ))
        if result != None:
            return result[0]
        return 0

    def get_rsdn_message(self, mid):
        return self.query_row("""
            select topicid, parentid, userid, forumid, subject, messagename, 
                   message, articleid, messagedate, updatedate, userrole, usertitle, 
                   lastmoderated, closed
            from rsdn_messages 
            where id=%s
            """, (mid, ))
        
    def get_channel_log(self, channel_name, date):
        return self.query("""
            select
                 channels_logs.date_and_time::time as t, 
                 nicknames.nickname,
                 channels_logs.message
            from channels_logs
            left join nicknames on nicknames.id = channels_logs.nickname_id
            where 
                channels_logs.channel = %s and 
                channels_logs.is_bot_command = false and
                date(channels_logs.date_and_time) = %s
            order by t
        """, (channel_name, date))

    def register_nickname(self, nickname, rsdn_member_id):
        self.execute("update nicknames set rsdn_user_id = %s where nickname = %s", (rsdn_member_id, nickname))

    def unregister_nickname(self, nickname):
        self.execute("update nicknames set rsdn_user_id = 0 where nickname = %s", (nickname, ))
        
    def nickname_is_registered(self, nickname):
        result = self.query_row("select rsdn_user_id from nicknames where nickname = %s", (nickname, ))
        if result != None:
            return result[0] > 0
        return False

    def get_registered_nicknames(self, rsdn_member_id):
        return self.query("select nickname from nicknames where rsdn_user_id = %s", (rsdn_member_id, ))


