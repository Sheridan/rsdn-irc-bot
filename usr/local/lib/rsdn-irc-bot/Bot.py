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
        self.channelsListObserveTimer.stop()
        GO.rsdn.stop()
        self.disconnect()
        self.die()

    def channelsListObserve(self):
        self.connection.list()

    def on_nicknameinuse(self, c, e):
        c.oper(self.config['auth']['nick'], self.config['auth']['oper_password'])
        c.nick('%s_%d'%(self.config['auth']['nick'],random.randint(0,100)))
        c.send_raw("kill %s %s"%(self.config['auth']['nick'], "What the fuck!"))
        c.nick(self.config['auth']['nick'])

    def on_welcome(self, c, e):
        c.oper(self.config['auth']['nick'], self.config['auth']['oper_password'])
        #while self.connection.get_nickname() != self.config['auth']['nick']: time.sleep(1)
        GO.rsdn.start()
        self.channelsListObserveTimer.start()

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

        #elif cmd == "mute"  : self.commander.mute  (e.source(), channel)
        #elif cmd == "demute": self.commander.demute(e.source(), channel)
        #elif cmd == "op"    : self.commander.op    (e.source(), channel)
        #elif cmd == "deop"  : self.commander.deop  (e.source(), channel)
        #elif cmd == "g"     : self.commander.g     (nick, channel, "%20".join(command[1:]))
        #elif cmd == "top"   : self.commander.top   (nick, channel, command)
        #elif cmd == "mid"   : self.commander.mid   (nick, ' '.join(command[1:]))
        #else: nick = nm_to_n(nickname)
        #    return False
        

    #def setOperators(self, operators):
    #    self.operators = operators

    def setUserMode(self, user, channel, mode):
        self.connection.send_raw("MODE %s %s %s"%(channel, mode, nm_to_n(user)))

    def setChannelMode(self, channel, mode):
        self.connection.send_raw("MODE %s %s"%(channel, mode))

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
        self.connection.send_raw("PRIVMSG %s %s: %s"%(channel, nm_to_n(nickname), text))

    def sendChannelText(self, channel, text):
        self.connection.send_raw("PRIVMSG %s %s"%(channel, text))

    def sendPrivate(self, nickname, text):
        self.connection.send_raw("PRIVMSG %s %s"%(nm_to_n(nickname), text))

    def joinChannel(self, channelName, topic=None):
        if channelName[0] != '#':
            channelName = str('#' + channelName)
        if self.config['debug']['enable'] == 'true' and channelName not in self.config['debug']['channels']:
            return
        self.connection.send_raw("samode %s -lri"%(channelName))
        self.connection.join(channelName)
        self.connection.send_raw("samode %s +o %s"%(channelName, self.connection.get_nickname()))
        if topic:
            self.connection.topic(channelName, unicode(topic).encode('utf8'))

