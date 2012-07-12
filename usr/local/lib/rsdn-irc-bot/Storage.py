#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys,socket, string, os, re, datetime
import psycopg2
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO
from Configurable import CConfigurable

class CStorage(CConfigurable):
    def __init__(self):
        CConfigurable.__init__(self, '/etc/rsdn-irc-bot/storage.conf')
        self.connection = psycopg2.connect(database=self.config['database'], user=self.config['user'], password=self.config['password'], host=self.config['host'], port=self.config['port'])

    def getNicknameId(self, nickname):
        sql = "SELECT id FROM nicknames WHERE nickname = %s"
        cursor = self.connection.cursor()
        cursor.execute(sql, (nickname,))
        uid = cursor.fetchone()
        if uid == None:
            cursor.execute("INSERT INTO nicknames (nickname) VALUES (%s)", (nickname,))
            self.connection.commit()
            cursor.execute(sql, (nickname,))
            uid = cursor.fetchone()
        cursor.close()
        return uid[0]

    def logChannelMessage(self, nickname, channel, message, is_bot_command):
        cursor = self.connection.cursor()
        nickname_id = self.getNicknameId(nickname)
        cursor.execute("INSERT INTO channels_logs (nickname_id, channel, message, is_bot_command) VALUES (%s, %s, %s, %s)", (nickname_id, channel, message, is_bot_command))
        cursor.execute("update nicknames set last_seen = %s", (datetime.datetime.now(),))
        self.connection.commit()
        cursor.close()

    def getTopOfChannel(self, channel, num):
        top = ''
        cursor = self.connection.cursor()
        cursor.execute("""
        select nicknames.nickname, count(channels_logs.nickname_id) from channels_logs
        left join nicknames on nicknames.id=channels_logs.nickname_id
        where channel=%s
        group by nicknames.nickname
        order by 2 desc
        limit %s
        """, (channel,num))
        result = cursor.fetchall()
        cursor.close()
        return result

    def getRsdnRowVersion(self, name):
        sql = "SELECT value FROM rsdn_row_versions WHERE name = %s"
        cursor = self.connection.cursor()
        cursor.execute(sql, (name,))
        uid = cursor.fetchone()
        if uid == None:
            cursor.execute("INSERT INTO rsdn_row_versions (name, value) VALUES (%s, %s)", (name, ''))
            self.connection.commit()
            cursor.execute(sql, (name,))
            uid = cursor.fetchone()
        cursor.close()
        return uid[0]

    def setRsdnRowVersion(self, name, value):
        cursor = self.connection.cursor()
        cursor.execute("update rsdn_row_versions set value=%s where name=%s", (value, name))
        self.connection.commit()
        cursor.close()

    def updateRsdnMessages(self, soap_message_info):
        sql = ''
        if not self.isMessageInDb(soap_message_info['messageId']):
            GO.bot.sendLog("RSDN DB. Новое сообщение")
            sql = """
            INSERT INTO rsdn_messages(
                topicid, parentid, userid, forumid, subject, messagename, 
                message, articleid, messagedate, updatedate, userrole, usertitle, 
                lastmoderated, closed, id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
        else:
            sql = """
            UPDATE rsdn_messages
            SET topicid=%s, parentid=%s, userid=%s, forumid=%s, subject=%s, 
                messagename=%s, message=%s, articleid=%s, messagedate=%s, updatedate=%s, 
                userrole=%s, usertitle=%s, lastmoderated=%s, closed=%s
            WHERE id=%s;
            """
        cursor = self.connection.cursor()
        cursor.execute(sql, (
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
                              soap_message_info['closed'],
                              soap_message_info['messageId']
                          ))
        self.connection.commit()
        cursor.close()

    def updateRsdnUsers(self, soap_user_info):
        sql = ''
        if not self.isUserInDb(soap_user_info['userId']):
            GO.bot.sendLog("RSDN DB. Новый пользователь")
            sql = """
            INSERT INTO rsdn_users(usernick, username, realname, homepage, wherefrom, origin, userclass, specialization, id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
        else:
            sql = """
            UPDATE rsdn_users
            SET usernick=%s, username=%s, realname=%s, homepage=%s, wherefrom=%s, origin=%s, userclass=%s, specialization=%s
            WHERE id=%s;
            """
        cursor = self.connection.cursor()
        cursor.execute(sql, (
                              soap_user_info['userNick'],
                              soap_user_info['userName'],
                              soap_user_info['realName'],
                              soap_user_info['homePage'],
                              soap_user_info['whereFrom'],
                              soap_user_info['origin'],
                              soap_user_info['userClass'],
                              soap_user_info['specialization'],
                              soap_user_info['userId']
                          ))
        self.connection.commit()
        cursor.close()

    def isIdInDb(self, iid, iid_field_name, table):
        cursor = self.connection.cursor()
        cursor.execute("SELECT %s FROM %s WHERE %s = %s"%(iid_field_name, table, iid_field_name, '%s'), (iid,))
        res = cursor.fetchone()
        cursor.close()
        return res != None

    def isUserInDb(self, uid):
        return self.isIdInDb(uid, 'id', 'rsdn_users') if uid else True
    
    def isMessageInDb(self, mid):
        return self.isIdInDb(mid, 'id', 'rsdn_messages')
        
    def getUserIdByName(self, userName):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM rsdn_users WHERE username = %s", (userName,))
        res = cursor.fetchone()
        cursor.close()
        return None if res == None else res
        

    def getTodayEvents(self, channel):
        result = dict()
        cursor = self.connection.cursor()
        cursor.execute("SELECT count(id) FROM channels_logs WHERE date(date_and_time) = date(now()) and is_bot_command='false' and channel=%s", (channel, ))
        result['ch_msgs'] = cursor.fetchone()[0]
        cursor.execute("SELECT count(id) FROM channels_logs WHERE date(date_and_time) = date(now()) and is_bot_command='true' and channel=%s", (channel, ))
        result['ch_bot'] = cursor.fetchone()[0]
        fid = GO.rsdn.getForumId(channel[1:].lower())
        if fid:
            cursor.execute("SELECT count(id) FROM rsdn_messages WHERE date(messagedate) = date(now()) and forumid=%s", (fid, ))
            result['f_msgs'] = cursor.fetchone()[0]
        else:
            result['f_msgs'] = 'Неприменимо'
        cursor.close()
        return result

    def getUserStats(self, uid):
        result = dict()
        cursor = self.connection.cursor()
        cursor.execute("select count(id) from rsdn_messages where userid=%s", (uid, ))
        result['f_msgs'] = cursor.fetchone()[0]
        cursor.execute("""
        select rsdn_users.username, count(rsdn_messages.id) 
        from rsdn_messages
        left join rsdn_users on rsdn_users.id = rsdn_messages.userid
        where rsdn_messages.parentid in (select id from rsdn_messages where userid=%s)
        group by rsdn_users.username
        order by 2 desc
        limit 10
        """, (uid, ))
        result['t10_o2u'] = ', '.join(['%s:%s'%(mber,cnt) for mber, cnt in cursor.fetchall()])
        cursor.execute("""
        select rsdn_users.username, count(rsdn_messages.id)
        from rsdn_messages
        left join rsdn_users on rsdn_users.id = rsdn_messages.userid
        where rsdn_messages.id in (select parentid from rsdn_messages where userid=%s)
        group by rsdn_users.username
        order by 2 desc
        limit 10
        """, (uid, ))
        result['t10_u2o'] = ', '.join(['%s:%s'%(mber,cnt) for mber, cnt in cursor.fetchall()])
        cursor.close()
        return result;

