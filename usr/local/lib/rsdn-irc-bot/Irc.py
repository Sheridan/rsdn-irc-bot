#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, socket, string, os, re, time
from threading import Thread, Lock
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO
# ------------------------------------------------------------------------------
class CIrcChannel(object):
    def __init__(self, irc, name, topic):
        self.users   = CIrcUsers(irc)
        self.irc     = irc
        self._name   = name
        self._topic  = topic
        self._joined = False
    def set_topic(self, topic):
        self.change_topic(topic)
        self.irc.set_channel_topic(self, topic)
    def name             (self                   ): return self._name
    def topic            (self                   ): return self._topic
    def joined           (self                   ): return self._joined
    def add_user         (self, user_id          ): return self.users.add(user_id)
    def add_user_by_parts(self, nick, ident, host): return self.users.add_by_parts(nick, ident, host)
    def __getitem__      (self, user_nick_or_full): return self.users[user_nick_or_full]
    def remove_user      (self, user_nick_or_full): self.users.remove(user_nick_or_full)
    def send_message     (self, text             ): self.irc.send_channel_message(self, text)
    def set_mode         (self, mode             ): self.irc.set_channel_mode(self, mode)
    def set_samode       (self, mode             ): self.irc.set_channel_samode(self, mode)
    def join             (self                   ): self.irc.join_channel(self._name)
    def change_topic     (self, topic            ): self._topic = topic
    def set_joined       (self, joined           ): self._joined = joined
# ------------------------------------------------------------------------------
class CIrcChannels(object):
    def __init__(self, irc):
        self.irc  = irc
        self.data = dict()
    def add(self, name, topic):
        if not self.has_name(name):
            self.data[name] = CIrcChannel(self.irc, name, topic)
        return self.data[name]
    def remove     (self, name   ): del self.data[name]
    def __getitem__(self, name   ): return self.data[name]
    def has        (self, channel): return self.has_name(channel.name())
    def has_name   (self, channel): return channel in self.data.keys()
# ------------------------------------------------------------------------------
class CIrcUser(object):
    def __init__(self, irc, user_id):
        self.irc    = irc
        self._full  = user_id
        self._nick  = self._full[                     0:self._full.find('!')]
        self._ident = self._full[self._full.find('!')+1:self._full.find('@')]
        self._host  = self._full[self._full.find('@')+1:                   ]
    def send_message(self,          text): self.irc.send_private_message(self, text)
    def send_notice (self,          text): self.irc.send_notice(self, text)
    def set_mode    (self, channel, mode): self.irc.set_user_mode(channel, self, mode)
    def set_samode  (self, channel, mode): self.irc.set_user_samode(channel, self, mode)
    def nick (self): return self._nick
    def ident(self): return self._ident
    def host (self): return self._host
    def full (self): return self._full
# ------------------------------------------------------------------------------
class CIrcUsers(object):
    def __init__(self, irc):
        self.irc  = irc
        self.data = dict()
    def to_nick(self, user_nick_or_full):
        return user_nick_or_full if '!' not in user_nick_or_full else user_nick_or_full[0:user_nick_or_full.find('!')]
    def add(self, user_id):
        user = CIrcUser(self.irc, user_id)
        if user.nick() not in self.data:
            self.data[user.nick()] = user
            return user
        return self.data[user.nick()]
    def add_by_parts(self, nick, ident, host): return self.add('%s!%s@%s'%(nick,ident,host))
    def remove      (self, user_nick_or_full): del    self.data[self.to_nick(user_nick_or_full)]
    def __getitem__ (self, user_nick_or_full): return self.data[self.to_nick(user_nick_or_full)]
# ------------------------------------------------------------------------------
class CIrcMessage(object):
    def __init__(self, irc, text, user):
        self.irc   = irc
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
    def reply  (self, text): self.irc.send_channel_reply(self._channel, self._user, text)
# ------------------------------------------------------------------------------
class CIrcPrivateMessage(CIrcMessage):
    def __init__(self, irc, text, user):
        CIrcMessage.__init__(self, irc, text, user)
    def reply(self, text): self._user.send_message(text)
# ------------------------------------------------------------------------------
class CIrc(Thread):
    def __init__(self, host, port, nick, ident, hostname, realname, irc_debug = False):
        Thread.__init__(self)
        self.irc_debug = irc_debug
        self._terminate = False
        self.realname   = realname
        self.host       = host
        self.port       = port
        self.mutex      = Lock()
        self.connected  = False
        self.channels   = CIrcChannels(self)
        self.me         = CIrcUser(self, u'%s!%s@%s'%(nick,ident,hostname))

    # ------------------------------------- base ------------------------------------------------
    def putcmd(self, cmd):
        if self.connected:
            cmd = GO.utf8(cmd)
            self.mutex.acquire()
            if self.irc_debug: print '[-c2s-] %s'%cmd
            self.sock.sendall(cmd)
            self.sock.sendall('\r\n')
            self.mutex.release()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.connected = True

    def disconnect(self):
        self.putcmd(u'QUIT')
        self.connected = False
        self.sock.close()

    def terminate(self):
        self._terminate = True
        self.disconnect()

    def run(self):
        self.connect()
        self.login()
        time.sleep(1)
        prev_line = ''
        line      = ''
        while not self._terminate:
            for char in self.sock.recv(1024):
                if char not in '\r\n':
                   line += char
                   continue
                if char == '\r': continue
                if char == '\n':
                    if self.irc_debug: print '[-s2c-] %s'%line
                    prefix     = ''
                    command    = ''
                    asrguments = ''
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
    """ PONG """
    def on_PING(self, prefix, arguments):
        self.putcmd('PONG %s'%arguments)

    """ LIST return channel """
    def on_322(self, prefix, arguments):
    # :irc.rsdn.ru 322 RSDNServ #bot.log 4 :Лог работы робота
        channel = self.channels.add(arguments.split(' ')[1].lower(), arguments[arguments.find(':'):])
        if 'on_channel_in_list' in dir(self):
            getattr(self, 'on_channel_in_list')(channel)

    """ Users, who reply on WHO """
    def on_352(self, prefix, arguments):
    #  RSDNServ #флэйм tmp_acnt rsdn-454FD1D1.dynamic.avangarddsl.ru irc.rsdn.ru scumware[] H@ :0 Философ
        data = arguments.split(' ')
        channel = self.channels[data[1].lower()]
        user = channel.add_user_by_parts(data[5], data[2], data[3])
        if 'on_user_join_channel' in dir(self):
            getattr(self, 'on_user_join_channel')(channel, user)

    """ User JOIN channel """
    def on_JOIN(self, prefix, arguments):
    # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP JOIN :#unix
        channel_name = arguments[1:].lower()
        if prefix[0:prefix.find('!')] == self.me.nick():
            channel = self.channels.add(channel_name, '') if not self.channels.has_name(channel_name) else self.channels[channel_name]
            channel.set_joined(True)
            if 'on_me_join_channel' in dir(self):
                getattr(self, 'on_me_join_channel')(channel)
        else:
            channel = self.channels[channel_name]
            user = channel.add_user(prefix)
            if 'on_user_join_channel' in dir(self):
                getattr(self, 'on_user_join_channel')(channel, user)

    """ User PART channel """
    def on_PART(self, prefix, arguments):
        #  :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP PART #bot.log :Once you know what it is you want to be true, instinct is a very useful device for enabling you to know that it is
        channel = self.channels[arguments.split(' ')[0].lower()]
        channel.remove_user(prefix)
        if 'on_user_part_channel' in dir(self):
            user = channel[prefix]
            getattr(self, 'on_user_part_channel')(channel, user)

    """ Message received """
    def on_PRIVMSG(self, prefix, arguments):
        # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP PRIVMSG #bot.log :ффффффффф
        # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP PRIVMSG RSDNServ :ааааааааааааа
        target = arguments[0:arguments.find(' ')]
        text   = arguments[arguments.find(' ')+2:]
        if target == self.me.nick():
            if 'on_private_message' in dir(self):
                getattr(self, 'on_private_message')(CIrcPrivateMessage(self, text, CIrcUser(self, prefix)))
        else:
            if 'on_channel_message' in dir(self):
                channel = self.channels[target.lower()]
                user = channel[prefix]
                getattr(self, 'on_channel_message')(CIrcChannelMessage(self, text, user, channel))

    """ Welcome message """
    def on_001(self, prefix, arguments):
        if 'on_welcome' in dir(self):
            getattr(self, 'on_welcome')()

    """ Nickname in use """
    def on_443(self, prefix, arguments):
        if 'on_my_nick_in_use' in dir(self):
            getattr(self, 'on_my_nick_in_use')()

    def on_TOPIC(self, prefix, arguments):
    # :Sheridan|Work!Sheridan@5FC2A92.D42BA605.60BBCFB.IP TOPIC #Help :aa
        channel = self.channels[arguments[0:arguments.find(' ')].lower()]
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
        self.set_nick(self.me.nick())
        self.set_user(self.me.ident(), self.me.host(), self.realname)

    def join_channel(self, channel):
        self.putcmd(u'JOIN %s'%channel)
        self.putcmd(u'WHO %s' %channel)

    def request_channels    (self                     ):  self.putcmd(u'LIST')
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
    def is_on_channel(self, channel): return self.channels.has(channel)
    # ------------------------------------- checks -------------------------------------------
