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

    def logChannelMessage(self, nickname, channel, message):
        cursor = self.connection.cursor()
        nickname_id = self.getNicknameId(nickname)
        cursor.execute("INSERT INTO channels_logs (nickname_id, channel, message) VALUES (%s, %s, %s)", (nickname_id, channel, message))
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
