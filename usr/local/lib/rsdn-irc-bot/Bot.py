#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, os, re, random, time
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO, Commander, Timer, Irc
from Configurable import CConfigurable

# -------------------------------------------------------------
class CBotCommand(object):
    def __init__(self, user, command, arguments):
        self._arguments = arguments
        self._command   = command
        self._user = user

    def reply_error(self, text): self._user.send_notice(text)
    def arguments  (self      ): return self._arguments
    def command    (self      ): return self._command
    def user_from  (self      ): return self._user
# -------------------------------------------------------------
class CChannelBotCommand(CBotCommand, Irc.CIrcChannelMessage):
    def  __init__(self, irc, text, user, channel, command, arguments):
        CBotCommand.__init__(self, user, command, arguments)
        Irc.CIrcChannelMessage.__init__(self, irc, text, user, channel)
# -------------------------------------------------------------
class CChannelToPrivateBotCommand(CChannelBotCommand):
    def                    __init__(self, irc, text, user, channel, command, arguments):
        CChannelBotCommand.__init__(self, irc, text, user, channel, command, arguments)

    def reply(self, text): self.user().send_message(text)
# -------------------------------------------------------------
class CPrivateBotCommand(CBotCommand, Irc.CIrcPrivateMessage):
    def  __init__(self, irc, text, user, command, arguments):
        CBotCommand.__init__(self, user, command, arguments)
        Irc.CIrcPrivateMessage.__init__(self, irc, text, user)
# -------------------------------------------------------------
class CBot(CConfigurable, Irc.CIrc):
    def __init__(self):
        CConfigurable.__init__(self, '/etc/rsdn-irc-bot/bot.conf')
        Irc.CIrc.__init__(  self,
                        self.config['connection']['host'], 
                        int(self.config['connection']['port']), 
                        self.config['auth']['nick'], 
                        self.config['auth']['ident'], 
                        self.config['auth']['hostname'], 
                        self.config['auth']['realname'],
                        self.config['debug']['irc'] == 'true')
        self.operators = self.config['operators']
        self._channels_list_observe_timer = Timer.CTimer(int(self.config['timers']['channels_list_observe']), self.request_channels)
        self.commander = Commander.CCommander()
        self.bot_channels = self.config['debug']['channels']+self.config['channels'].values()
        self.debug = self.config['debug']['bot'] == 'true'
        self.channel_topics = dict()
        self.store_channel_topic(self.config['channels']['log'], u'Лог работы робота')
        self.store_channel_topic(self.config['channels']['notifications'], u'Все сообщения о активности на RSDN')
        self.log_channel = None
        self.notifications_channel = None

    # --------------------------------- Reactions on CIrc events -----------------------------------
    def on_my_nick_in_use(self):
        self.set_nick(self.config['auth']['nick'], random.randint(0,100))
        self.auth_oper(self.config['auth']['nick'], self.config['auth']['oper_password'])
        self.kill(self.config['auth']['nick'], 'What the fuck!')
        time.sleep(3)
        self.login()

    def on_welcome(self):
        self.auth_oper(self.config['auth']['oper']['login'], self.config['auth']['oper']['password'])
        self.join_channel(self.config['channels']['log'])
        self.join_channel(self.config['channels']['notifications'])
        time.sleep(3)
        GO.rsdn.start()
        self._channels_list_observe_timer.start()
        self.send_channel_log('Online')

    def on_channel_in_list(self, channel):
        if self.can_i_work_with_channel(channel.name()):
            if not channel.joined():
                channel.join()
            self.check_channel_topic(channel)

    def on_user_join_channel(self, channel, user):
        if self.is_operator(user, channel):
            user.set_mode(channel, '+o')

    def on_me_join_channel(self, channel):
        channel.set_samode('-lri')
        self._me.set_samode(channel, '+o')
        self.check_channel_topic(channel)
        if not self.log_channel            and channel.name() == self.config['channels']['log']:           self.log_channel           = channel
        if not self.notifications_channel  and channel.name() == self.config['channels']['notifications']: self.notifications_channel = channel

    def on_channel_message(self, message):
        prefix = message.text()[0]
        is_robot_command = prefix in '!@'
        if is_robot_command:
            command = re.split('\s+', message.text()[1:].strip())
            cmd = command[0]
            parametres = command[1:]
            if cmd in GO.public_commands.keys() and prefix in GO.public_commands[cmd]['pfx']:
                if not GO.public_commands[cmd]['adm'] or GO.public_commands[cmd]['adm'] and self.is_operator(message.user(), message.channel()):
                    if   prefix == '!': getattr(self.commander, cmd)(CChannelBotCommand         (self, message.text(), message.user(), message.channel(), cmd, parametres))
                    elif prefix == '@': getattr(self.commander, cmd)(CChannelToPrivateBotCommand(self, message.text(), message.user(), message.channel(), cmd, parametres))
        GO.storage.store_channel_message(message.user().nick(), message.channel().name(), message.text(), is_robot_command)

    # --------------------------------- Reactions on CIrc events -----------------------------------
    # --------------------------------- Self methods -----------------------------------------------
    def is_operator(self, user, channel):
        for operator in self.operators['global']:
            if re.match(operator, user.user_id()):
                return True
        for op_channel in self.operators['channels']:
            for operator in self.operators['channels'][op_channel]:
                if re.match(operator, user.user_id()):
                    return True
        return False

    def store_channel_topic(self, channel, topic):
        self.channel_topics[channel.lower()] = topic

    def join_forum_channel(self, forum_sname):
        channel_name = u'#%s'%forum_sname
        if self.can_i_work_with_channel(channel_name):
            self.join_channel(channel_name)

    def can_i_work_with_channel(self, channel_name):
        return not self.debug or self.debug and channel_name.lower() in self.bot_channels

    def check_channel_topic(self, channel):
        if channel.name().lower() in self.channel_topics.keys() and self.channel_topics[channel.name().lower()] != channel.topic():
            channel.set_topic(self.channel_topics[channel.name().lower()])

    def send_channel_notification(self, forum_sname, text):
        channel_name = u'#%s'%forum_sname
        if self.can_i_work_with_channel(channel_name):
            self._channels[channel_name].send_message(text)
    # --------------------------------- Self methods -----------------------------------------------

    def stop(self):
        self.send_channel_log('Offline')
        self._channels_list_observe_timer.stop()
        self.quit()
        self._terminate()
        GO.rsdn.stop()
        GO.storage.stop()

    def send_rsdn_notification(self, text):
        if self.notifications_channel != None and self.notifications_channel.joined():
            self.notifications_channel.send_message(text)

    def send_channel_log(self, text):
        if self.log_channel != None and self.log_channel.joined():
            self.log_channel.send_message(text)
