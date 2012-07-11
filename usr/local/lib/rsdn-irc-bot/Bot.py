#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, socket, string, os, re, random, time
from threading import Lock
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr

sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO, Commander, Timer
from Configurable import CConfigurable

class CBot(SingleServerIRCBot, CConfigurable):
    def __init__(self):
        CConfigurable.__init__(self, '/etc/rsdn-irc-bot/bot.conf')
        self.operators = self.config['operators']
        self.terminate = False
        self.channelsListObserveTimer = Timer.CTimer(int(self.config['timers']['channels_list_observe']), self.channelsListObserve)
        SingleServerIRCBot.__init__(self, [(self.config['connection']['host'], int(self.config['connection']['port']))], self.config['auth']['nick'], self.config['auth']['realname'])
        self.commander = Commander.CCommander()

    def stop(self):
        self.sendLog('Offline')
        self.channelsListObserveTimer.stop()
        GO.rsdn.stop()
        self.disconnect()
        self.die()

    def channelsListObserve(self):
        self.sendLog('Проверяю список каналов...')
        self.connection.list()

    def on_nicknameinuse(self, c, e):
        c.oper(self.config['auth']['nick'], self.config['auth']['oper_password'])
        c.nick('%s_%d'%(self.config['auth']['nick'],random.randint(0,100)))
        c.send_raw('kill %s %s'%(self.config['auth']['nick'], 'What the fuck!'))
        c.nick(self.config['auth']['nick'])

    def on_welcome(self, c, e):
        c.oper(self.config['auth']['nick'], self.config['auth']['oper_password'])
        #while self.connection.get_nickname() != self.config['auth']['nick']: time.sleep(1)
        self.joinChannel(self.config['channels']['notifications'], u'Все сообщения о активности на RSDN')
        self.joinChannel(self.config['channels']['log'], u'Лог работы робота')
        GO.rsdn.start()
        self.channelsListObserveTimer.start()
        self.sendLog('Online')

    def on_privmsg(self, c, e):
        pass

    def on_list(self, c, e):
        channel = e.arguments()[0]
        for chname, chobj in self.channels.items():
            if channel == chname:
                return
        
        self.joinChannel(channel)

    def on_pubmsg(self, c, e):
        nickname = e.source()
        channel  = e.target()
        text     = ' '.join(e.arguments())
        if not self.publicCommand(nickname, channel, text):
          GO.storage.logChannelMessage(nm_to_n(nickname), channel, text)

    def on_join(self, c, e):
        channel = e.target()
        c.send_raw('sajoin %s %s'%(nm_to_n(e.source()), GO.utf8(self.config['channels']['notifications'])))
        if self.isOperator(e.source(), channel):
            self.setUserMode(e.source(), channel, '+o')

    def publicCommand(self, nickname, channel, text):
        prefix = text[0]
        if prefix in '!@#':
            command = re.split('\s+', text[1:].strip())
            cmd = command[0]
            parametres = command[1:]
            if cmd in GO.commands.keys() and prefix in GO.commands[cmd]['pfx']:
                if not GO.commands[cmd]['adm'] or GO.commands[cmd]['adm'] and self.isOperator(nickname, channel):
                    result = getattr(self.commander, cmd)(nickname, channel, parametres)
                    #print result
                    for ok, text in result:
                        if ok:
                            self.sendReply(prefix, nickname, channel, text)
                        else:
                            self.sendNotice(nickname, text)
                    return True
        return False

    def setUserMode(self, user, channel, mode):
        self.connection.send_raw('MODE %s %s %s'%(channel, mode, nm_to_n(user)))

    def setChannelMode(self, channel, mode):
        self.connection.send_raw('MODE %s %s'%(channel, mode))

    def isOperator(self, nick, channel):
        for operator in self.operators['global']:
                if re.match(operator, nick):
                    return True
        for channel in self.operators['channels']:
            for operator in self.operators['channels'][channel]:
                if re.match(operator, nick):
                    return True
        return False

    def sendReply(self, prefix, nickname, channel, text):
        if prefix == '!':
            self.sendChannelReply(nickname, channel, text)
        elif prefix == '@':
            self.sendPrivate(nickname, text)
        elif prefix == '#':
            self.sendNotice(nickname, text)

    def sendNotice(self, nickname, text):
        self.connection.notice(nm_to_n(nickname), text)

    def sendChannelReply(self, nickname, channel, text):
        self.connection.send_raw('PRIVMSG %s %s: %s'%(channel, nm_to_n(nickname), text))

    def sendChannelText(self, channel, text):
        self.connection.send_raw('PRIVMSG %s %s'%(channel, text))

    def sendPrivate(self, nickname, text):
        self.connection.send_raw('PRIVMSG %s %s'%(nm_to_n(nickname), text))

    def joinChannel(self, channelName, topic=None):
        if channelName[0] != '#':
            channelName = '#' + channelName
        if self.config['debug']['enable'] == 'true' and channelName in self.config['debug']['channels'] or \
           channelName in [self.config['channels']['notifications'], self.config['channels']['log']] or \
           self.config['debug']['enable'] != 'true':
            self.sendLog('Вхожу на канал %s'%GO.utf8(channelName))
            self.connection.send_raw('samode %s -lri'%(channelName))
            self.connection.join(channelName)
            self.connection.send_raw('samode %s +o %s'%(channelName, self.connection.get_nickname()))
            if topic:
                self.connection.topic(GO.utf8(channelName), GO.utf8(topic))

    def sendRsdnNotification(self, text):
        self.sendChannelText(GO.utf8(self.config['channels']['notifications']), text)

    def sendLog(self, text):
        self.sendChannelText(GO.utf8(self.config['channels']['log']), text)
