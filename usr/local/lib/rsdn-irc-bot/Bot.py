#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, socket, string, os, re, random, time
from threading import Lock
from threading import Thread, Lock
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO, Commander, Timer, Irc
#from Irc import CIrc
from Configurable import CConfigurable

class CBot(CConfigurable, Irc.CIrc):
    def __init__(self):
        CConfigurable.__init__(self, '/etc/rsdn-irc-bot/bot.conf')
        Irc.CIrc.__init__(  self,
                        self.config['connection']['host'], 
                        int(self.config['connection']['port']), 
                        self.config['auth']['nick'], 
                        self.config['auth']['ident'], 
                        self.config['auth']['hostname'], 
                        self.config['auth']['realname'])
        self.operators = self.config['operators']
        self.channelsListObserveTimer = Timer.CTimer(int(self.config['timers']['channels_list_observe']), self.request_channels)
        self.commander = Commander.CCommander()
        self.bot_channels = self.config['debug']['channels']+self.config['channels'].values()
        self.debug = self.config['debug']['enable'] == 'true'
        self.channel_topics = dict()
        self.store_channel_topic(self.config['channels']['log'], u'Лог работы робота')
        self.store_channel_topic(self.config['channels']['notifications'], u'Все сообщения о активности на RSDN')
        self.log_channel = None
        self.notifications_channel = None

    # --------------------------------- Reactions on CIrc events -----------------------------------
    def on_my_nick_in_use(self):
        self.set_nick(self.config['auth']['nick'],random.randint(0,100))
        self.auth_oper(self.config['auth']['nick'], self.config['auth']['oper_password'])
        self.kill(self.config['auth']['nick'], 'What the fuck!')
        time.sleep(3)
        self.login()

    def on_welcome(self):
        self.auth_oper(self.config['auth']['oper']['login'], self.config['auth']['oper']['password'])
        self.join_channel(self.config['channels']['log'])
        self.join_channel(self.config['channels']['notifications'])
        GO.rsdn.start()
        self.channelsListObserveTimer.start()
        self.sendLog('Online')

    def on_channel_in_list(self, channel):
        if self.can_i_work_with_channel(channel.name()):
            channel.join()

    def on_user_join_channel(self, channel, user):
        if self.isOperator(user, channel):
            user.set_mode(channel, '+o')

    def on_me_join_channel(self, channel):
        if channel.name() == self.config['channels']['log']:
            self.log_channel = channel
        if channel.name() == self.config['channels']['notifications']:
            self.notifications_channel = channel
        channel.set_samode('-lri')
        self.me.set_samode(channel, '+o')
        if channel.name() in self.channel_topics.keys() and self.channel_topics[channel.name()] != channel.topic():
            channel.set_topic(self.channel_topics[channel.name()])

    def on_channel_message(self, message):
        prefix = message.text()[0]
        is_robot_command = prefix in '!@'
        if is_robot_command:
            command = re.split('\s+', message.text()[1:].strip())
            cmd = command[0]
            parametres = command[1:]
            if cmd in GO.public_commands.keys() and prefix in GO.public_commands[cmd]['pfx']:
                if not GO.public_commands[cmd]['adm'] or GO.public_commands[cmd]['adm'] and self.isOperator(message.user(), message.channel()):
                    result = getattr(self.commander, cmd)(message.user().nick(), message.channel().name(), parametres)
                    #print result
                    for ok, text in result:
                        if not ok:
                            text = u'Что то не так. %s'%text
                        if   prefix == '!': message.reply(text)
                        elif prefix == '@': message.user().send_message(text)
        GO.storage.logChannelMessage(message.user().nick(), message.channel().name(), message.text(), is_robot_command)

    # --------------------------------- Reactions on CIrc events -----------------------------------
    # --------------------------------- Self methods -----------------------------------------------
    def isOperator(self, user, channel):
        for operator in self.operators['global']:
                if re.match(operator, user.full()):
                    return True
        for op_channel in self.operators['channels']:
            for operator in self.operators['channels'][op_channel]:
                if re.match(operator, user.full()):
                    return True
        return False

    def store_channel_topic(self, channel, topic):
        self.channel_topics[channel] = topic

    def go_join_channel(self, channel_name):
        if self.can_i_work_with_channel(channel_name):
            self.join_channel(channel_name)

    def can_i_work_with_channel(self, channel_name):
        return not self.debug or self.debug and channel_name in self.bot_channels
    # --------------------------------- Self methods -----------------------------------------------













    

    #def user_mode_changed(self, prefix, arguments):
    #    # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP MODE #bot.log -o RSDNServ
    #    data = arguments.split(' ')
    #    if len(data) == 3:
    #        who = self.user_prefix_split(prefix)
    #        channel     = data[0]
    #        mode        = data[1]
    #        target_user = data[2]
    #        if target_user == GO.utf8(self.config['auth']['nick']):
    #            mode_prefix = mode[0]
    #            mode = mode[1:]
    #            if mode_prefix == '-':
    #                self.putcmd(u'SAMODE %s +o %s'%(channel, self.config['auth']['nick']))
    #                self.set_user_mode(self.config['auth']['nick'], channel, '+%s'%mode)
    #                self.set_user_mode(who['nick'], channel, '-%s'%mode)

    #def user_has_been_kicked(self, prefix, arguments):
    #    #  :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP KICK #bot.log RSDNServ :Sheridan|Work
    #    data = arguments.split(' ')
    #    who = self.user_prefix_split(prefix)
    #    channel     = data[0]
    #    target_user = data[1]
    #    if target_user == GO.utf8(self.config['auth']['nick']):
    #        self.status.remove_channel(channel)
    #        self.go_join_channel(channel)
    #        self.putcmd(u'KICK %s %s'%(channel, who['nick']))

    def stop(self):
        self.sendLog('Offline')
        self.channelsListObserveTimer.stop()
        GO.rsdn.stop()
        self.terminate()

    def sendRsdnNotification(self, text):
        if self.notifications_channel != None and self.notifications_channel.joined():
            self.notifications_channel.send_message(text)

    def sendLog(self, text):
        if self.log_channel != None and self.log_channel.joined():
            self.log_channel.send_message(text)
