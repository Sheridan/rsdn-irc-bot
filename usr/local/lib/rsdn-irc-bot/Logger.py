#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys,socket, string, os, re, datetime
from threading import Thread, Lock
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))

class CLogger(object):
    def __init__(self, config, storage):
        self.config = config
        self.storage = storage

    def channelLog(self, msg):
        user = msg.source()
        channel = msg.target()
        message = " ".join(msg.arguments())
        dt = datetime.datetime.now()
        directory = "%s/%s"%(self.config['channel'], channel)
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = "%s/%s.xmlpart"%(directory, dt.strftime('%Y-%m-%d'))
        f = open(filename, 'a+')
        f.write('<usermessage><time>%s</time><user>%s</user><channel>%s</channel><msg><![CDATA[\n%s\n]]></msg></usermessage>\n'%(dt.strftime('%H:%M:%S'), user, channel, message))
        f.close()