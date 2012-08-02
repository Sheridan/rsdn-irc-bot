#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, socket, os, re, time
from threading import Thread, Lock
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO
# ------------------------------------------------------------------------------
class CIrcChannel(object):
    def __init__(self, irc, name, topic):
        self._users   = CIrcUsers(irc)
        self._irc     = irc
        self._name   = name
        self._topic  = topic
        self._joined = False

    def set_topic(self, topic):
        self.change_topic(topic)
        self._irc.set_channel_topic(self, topic)

    def name        (self        ): return self._name
    def topic       (self        ): return self._topic
    def joined      (self        ): return self._joined
    def add_user    (self, user  ): return self._users.add_user_obj(user)
    def users       (self        ): return self._users.users()
    def remove_user (self, user  ): self._users.remove_user_obj(user)
    def send_message(self, text  ): self._irc.send_channel_message(self, text)
    def set_mode    (self, mode  ): self._irc.set_channel_mode(self, mode)
    def set_samode  (self, mode  ): self._irc.set_channel_samode(self, mode)
    def join        (self        ): self._irc.join_channel(self._name)
    def change_topic(self, topic ): self._topic  = topic
    def set_joined  (self, joined): self._joined = joined
# ------------------------------------------------------------------------------
class CIrcChannels(object):
    def __init__(self, irc):
        self._irc  = irc
        self._data = dict()

    def add(self, name, topic):
        if not self.exists(name):
            self._data[name] = CIrcChannel(self._irc, name, topic)
        return self._data[name]

    def remove     (self, name   ): del    self._data[name]
    def __getitem__(self, name   ): return self._data[name]
    def exists     (self, name   ): return name in self._data.keys()
    def channels   (self         ): return self._data.values()
# ------------------------------------------------------------------------------
class CIrcUser(object):
    def __init__(self, irc, user_id):
        self._irc    = irc
        self.rename(user_id)

    def rename(self, user_id):
        self._user_id  = user_id
        self._nick  = self._user_id[                        0:self._user_id.find('!')]
        self._ident = self._user_id[self._user_id.find('!')+1:self._user_id.find('@')]
        self._host  = self._user_id[self._user_id.find('@')+1:                       ]

    def send_message(self,          text): self._irc.send_private_message(self, text)
    def send_notice (self,          text): self._irc.send_notice(self, text)
    def set_mode    (self, channel, mode): self._irc.set_user_mode(channel, self, mode)
    def set_samode  (self, channel, mode): self._irc.set_user_samode(channel, self, mode)
    def change_nick (self,          nick): self._nick = nick
    def nick        (self               ): return self._nick
    def ident       (self               ): return self._ident
    def host        (self               ): return self._host
    def user_id     (self               ): return self._user_id
# ------------------------------------------------------------------------------
class CIrcUsers(object):
    def __init__(self, irc):
        self._irc  = irc
        self._data = dict()
    def to_nick(self, user_nick_or_user_id):
        return user_nick_or_user_id if '!' not in user_nick_or_user_id else user_nick_or_user_id[0:user_nick_or_user_id.find('!')]

    def add(self, user_id):
        user = CIrcUser(self._irc, user_id)
        if user.nick() not in self._data:
            self._data[user.nick()] = user
            return user
        return self._data[user.nick()]

    def change_user_nick(self, user_id, nick):
        user = self._data[self.to_nick(user_id)]
        self.remove_user_obj(user)
        user.change_nick(nick)
        self.add_user_obj(user)

    def remove_user_obj(self, user): 
        if user.nick() in self._data.keys():
            del self._data[user.nick()]

    def add_by_parts(self, nick, ident, host   ): return self.add('%s!%s@%s'%(nick,ident,host))
    def add_user_obj(self, user                ):        self._data[user.nick()] = user
    def remove      (self, user_nick_or_user_id):        self.remove_user_obj(self._data[self.to_nick(user_nick_or_user_id)])
    def __getitem__ (self, user_nick_or_user_id): return self._data[self.to_nick(user_nick_or_user_id)]
    def exists      (self, user_nick_or_user_id): return self.to_nick(user_nick_or_user_id) in self._data.keys()
    def users       (self                      ): return self._data.values()
# ------------------------------------------------------------------------------
class CIrcMessage(object):
    def __init__(self, irc, text, user):
        self._irc   = irc
        self._user = user
        self._text = text

    def user(self): return self._user
    def text(self): return self._text
# ------------------------------------------------------------------------------
class CIrcChannelMessage(CIrcMessage):
    def __init__(self, irc, text, user, channel):
        CIrcMessage.__init__(self, irc, text, user)
        self._channel = channel

    def channel(self      ): return self._channel
    def reply  (self, text): self._irc.send_channel_reply(self._channel, self._user, text)
# ------------------------------------------------------------------------------
class CIrcPrivateMessage(CIrcMessage):
    def __init__(self, irc, text, user):
        CIrcMessage.__init__(self, irc, text, user)
    def reply(self, text): self._user.send_message(text)
# ------------------------------------------------------------------------------
class CIrc(Thread):
    def __init__(self, host, port, nick, ident, hostname, realname, irc_debug = False):
        Thread.__init__(self)
        self._irc_debug = irc_debug
        self._terminate = False
        self._realname   = realname
        self._host       = host
        self._port       = port
        self._mutex      = Lock()
        self._connected  = False
        self._channels   = CIrcChannels(self)
        self._users      = CIrcUsers(self)
        self._me         = CIrcUser(self, u'%s!%s@%s'%(nick, ident, hostname))

    # ------------------------------------- base ------------------------------------------------
    def putcmd(self, cmd):
        if self._connected:
            cmd = GO.utf8(cmd)
            self._mutex.acquire()
            if self._irc_debug: print '[-c2s-] %s'%cmd
            self._sock.sendall(cmd)
            self._sock.sendall('\r\n')
            self._mutex.release()

    def connect(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._host, self._port))
        self._connected = True

    def disconnect(self):
        self.quit()
        self._connected = False
        self._sock.close()

    def terminate(self):
        self._terminate = True
        self.disconnect()

    def run(self):
        self.connect()
        self.login()
        time.sleep(1)
        line      = ''
        while not self._terminate:
            for char in self._sock.recv(1024):
                if char not in '\r\n':
                    line += char
                    continue
                if char == '\r': continue
                if char == '\n':
                    if self._irc_debug: print '[-s2c-] %s'%line
                    prefix     = ''
                    command    = ''
                    arguments  = ''
                    if line[0] == ':':
                        line   = line[1:]
                        i      = line.find(' ')
                        prefix = GO.unicod(line[0:i])
                        line   = line[i+1:]
                    i = line.find(' ')
                    command   = 'on_%s'%line[0:i]
                    arguments = GO.unicod(line[i+1:])
                    if command in dir(self): Thread(target=getattr(self, command), args=(prefix, arguments)).start()
                    line = ''

    # ------------------------------------- base ------------------------------------------------
    # ------------------------------------- commands actions-------------------------------------
    def on_PING(self, prefix, arguments):
        """ PONG """
        self.putcmd('PONG %s'%arguments)

    def on_322(self, prefix, arguments):
    # :irc.rsdn.ru 322 RSDNServ #bot.log 4 :Лог работы робота
        """ LIST return channel """
        channel = self._channels.add(arguments.split(' ')[1].lower(), arguments[arguments.find(':'):])
        if 'on_channel_in_list' in dir(self):
            getattr(self, 'on_channel_in_list')(channel)

    def on_352(self, prefix, arguments):
    #  RSDNServ #флэйм tmp_acnt rsdn-454FD1D1.dynamic.avangarddsl.ru irc.rsdn.ru scumware[] H@ :0 Философ
        """ Users, who reply on WHO """
        data    = arguments.split(' ')
        channel = self._channels[data[1].lower()]
        user    = self._users.add_by_parts(data[5], data[2], data[3])
        channel.add_user(user)
        if 'on_user_join_channel' in dir(self):
            getattr(self, 'on_user_join_channel')(channel, user)

    def on_JOIN(self, prefix, arguments):
    # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP JOIN :#unix
        """ User JOIN channel """
        channel_name = arguments[1:].lower()
        if prefix[0:prefix.find('!')] == self._me.nick():
            channel = self._channels.add(channel_name, '')
            channel.set_joined(True)
            if 'on_me_join_channel' in dir(self):
                getattr(self, 'on_me_join_channel')(channel)
        else:
            channel = self._channels[channel_name]
            user    = self._users.add(prefix)
            channel.add_user(user)
            if 'on_user_join_channel' in dir(self):
                getattr(self, 'on_user_join_channel')(channel, user)

    def on_PART(self, prefix, arguments):
        #  :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP PART #bot.log :Once you know what it is you want to be true, instinct is a very useful device for enabling you to know that it is
        """ User PART channel """
        channel = self._channels[arguments.split(' ')[0].lower()]
        user = self._users[prefix]
        channel.remove_user(user)
        if 'on_user_part_channel' in dir(self):
            user = channel[prefix]
            getattr(self, 'on_user_part_channel')(channel, user)

    def on_QUIT(self, prefix, arguments):
        #  :ssssssss!Sheridan@5FC2A92.D42BA605.60BBCFB.IP QUIT :Quit: Konversation terminated!
        """ User QUIT irc """
        user = self._users[prefix]
        self._users.remove_user_obj(user)
        for channel in self._channels.channels():
            channel.remove_user(user)
        if 'on_user_quit' in dir(self):
            getattr(self, 'on_user_quit')(user)

    def on_NICK(self, prefix, arguments):
        # :o_O!o_O@138A86B6.14305381.3F6D259C.IP NICK :^_^
        """user changed nick"""
        old_nick = self._users[prefix].nick()
        new_nick = arguments[1:]
        self._users.change_user_nick(prefix, new_nick)
        user = self._users[new_nick]
        if 'on_user_nick_change' in dir(self):
            getattr(self, 'on_user_nick_change')(user, old_nick, new_nick)

    def on_KICK(self, prefix, arguments):
        # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP KICK #test Sheridan|Home :why
        """ User kicked """
        user_who_kick = self._users[prefix]
        channel       = self._channels[arguments.split(' ')[0].lower()]
        kicked_user   = self._users[arguments.split(' ')[1]]
        why           = arguments.split(' ')[2][1:]
        channel.remove_user(kicked_user)
        if 'on_user_kicked' in dir(self):
            getattr(self, 'on_user_kicked')(channel, user_who_kick, kicked_user, why)

    def on_PRIVMSG(self, prefix, arguments):
        # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP PRIVMSG #bot.log :ффффффффф
        # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP PRIVMSG RSDNServ :ааааааааааааа
        """ Message received """
        target = arguments[0:arguments.find(' ')]
        text   = arguments[arguments.find(' ')+2:]
        user   = self._users[prefix]
        if target == self._me.nick():
            if 'on_private_message' in dir(self):
                getattr(self, 'on_private_message')(CIrcPrivateMessage(self, text, user))
        else:
            if 'on_channel_message' in dir(self):
                channel = self._channels[target.lower()]
                getattr(self, 'on_channel_message')(CIrcChannelMessage(self, text, user, channel))

    def on_001(self, prefix, arguments):
        """ Welcome message """
        if 'on_welcome' in dir(self):
            getattr(self, 'on_welcome')()

    def on_443(self, prefix, arguments):
        """ Nickname in use """
        if 'on_my_nick_in_use' in dir(self):
            getattr(self, 'on_my_nick_in_use')()

    def on_TOPIC(self, prefix, arguments):
    # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP TOPIC #Help :aa
        """somebody changed topic"""
        channel = self._channels[arguments[0:arguments.find(' ')].lower()]
        topic   = arguments[arguments.find(' ')+2:]
        channel.change_topic(topic)
        if 'on_channel_topic_changed' in dir(self):
            getattr(self, 'on_channel_topic_changed')(channel)
    # ------------------------------------- commands actions-------------------------------------
    # ------------------------------------- me & IRC manage -------------------------------------
    
    # ------------------------------------- me & IRC manage -------------------------------------
    # ------------------------------------- Tools -------------------------------------
    def split_message(self, text, limit=200): 
        temp = u''
        result = []
        for part in re.split(r"\s+", text, 0, re.UNICODE):
            temp += u' '+part
            if len(temp) >= limit:
                result.append(temp)
                temp = u''
        if len(temp) > 0:
            result.append(temp)
        return result
    # ------------------------------------- Tools -------------------------------------
    # ------------------------------------- IRC manage ------------------------------------------
    def login(self):
        self.set_nick(self._me.nick())
        self.set_user(self._me.ident(), self._me.host(), self._realname)

    def join_channel(self, channel):
        self.putcmd(u'JOIN %s'%channel)
        self.putcmd(u'WHO %s' %channel)

    def request_channels    (self                     ):  self.putcmd(u'LIST')
    def quit                (self                     ):  self.putcmd(u'QUIT')
    def kill                (self, nick, text         ):  self.putcmd(u'KILL %s %s'       %(nick, text))
    def set_nick            (self, nick               ):  self.putcmd(u'NICK %s'          % nick)
    def set_user            (self, ident, host, real  ):  self.putcmd(u'USER %s 0 %s :%s' %(ident, host, real))
    def auth_oper           (self, login, password    ):  self.putcmd(u'OPER %s %s'       %(login, password))
    def set_channel_topic   (self, channel, topic     ):  self.putcmd(u'TOPIC %s :%s'     %(channel.name(), topic))
    def set_user_mode       (self, channel, user, mode):  self.putcmd(u'MODE %s %s %s'    %(channel.name(), mode, user.nick()))
    def set_user_samode     (self, channel, user, mode):  self.putcmd(u'SAMODE %s %s %s'  %(channel.name(), mode, user.nick()))
    def set_channel_mode    (self, channel, mode      ):  self.putcmd(u'MODE %s %s'       %(channel.name(), mode))
    def set_channel_samode  (self, channel, mode      ):  self.putcmd(u'SAMODE %s %s'     %(channel.name(), mode))
    def send_channel_message(self, channel, text      ): [self.putcmd(u'PRIVMSG %s :%s'   %(channel.name(), text_part))              for text_part in self.split_message(text)]
    def send_channel_reply  (self, channel, user, text): [self.putcmd(u'PRIVMSG %s :%s:%s'%(channel.name(), user.nick(), text_part)) for text_part in self.split_message(text)]
    def send_private_message(self, user, text         ): [self.putcmd(u'PRIVMSG %s :%s'   %(user.nick(), text_part))                 for text_part in self.split_message(text)]
    def send_notice         (self, user, text         ): [self.putcmd(u'NOTICE %s :%s'    %(user.nick(), text_part))                 for text_part in self.split_message(text)]
    # ------------------------------------- IRC manage -------------------------------------------
    # ------------------------------------- checks -------------------------------------------
    def is_on_channel(self, channel): return self._channels.exists(channel.name())
    # ------------------------------------- checks -------------------------------------------
    # ------------------------------------- data -------------------------------------------
    def user   (self, nick): return self._users[nick]    if self._users.exists(nick) else None
    def channel(self, name): return self._channels[name] if self._channels.exists(name) else None
    # ------------------------------------- data -------------------------------------------
