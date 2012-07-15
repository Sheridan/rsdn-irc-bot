#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, socket, string, os, re, random, time
from threading import Lock
from threading import Thread, Lock


sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO, Commander, Timer
from Configurable import CConfigurable

class CBotStatus(object):
    def __init__(self):
        self.data = dict()
        self.data['channels'] = dict()

    def add_channel(self, channel):
        if not self.is_on_channel(channel):
            self.data['channels'][channel] = dict()

    def is_on_channel(self, channel):
        return channel in self.data['channels'].keys()
        
    def remove_channel(self, channel):
        if self.is_on_channel(channel):
            del self.data['channels'][channel]

    def add_user_to_channel(self, channel, user):
        self.add_channel(channel)
        if not self.is_user_on_channel(channel, user):
            self.data['channels'][channel][user] = dict()
    
    def is_user_on_channel(self, channel, user):
       return self.is_on_channel(channel) and user in self.data['channels'][channel].keys()
    
    def remove_user_from_channel(self, channel):
        if self.is_user_on_channel(channel, user):
            del self.data['channels'][channel][user]

class CBot(Thread, CConfigurable):
    def __init__(self):
        CConfigurable.__init__(self, '/etc/rsdn-irc-bot/bot.conf')
        Thread.__init__(self)
        self.mutex = Lock()
        self.operators = self.config['operators']
        self.terminate = False
        self.channelsListObserveTimer = Timer.CTimer(int(self.config['timers']['channels_list_observe']), self.request_channels)
        self.commander = Commander.CCommander()
        self.connected = False
        self.status = CBotStatus()
        self.bot_channels = [c.encode('utf8') for c in self.config['debug']['channels']+self.config['channels'].values()]
        self.debug = self.config['debug']['enable'] == 'true'

    def putcmd(self, cmd):
        if self.connected:
            self.mutex.acquire()
            cmd = GO.utf8(cmd)
            print '[-c2s-] %s'%cmd
            self.sock.sendall(cmd)
            self.sock.sendall('\r\n')
            self.mutex.release()
    
    #def put_cmd(self, cmd, params):
    #    self.mutex.acquire()
    #    print '[-c2s-] %s'%cmd
    #    self.sock.sendall(cmd)
    #    self.sock.sendall(params)
    #    self.sock.sendall('\r\n')
    #    self.mutex.release()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.config['connection']['host'], int(self.config['connection']['port'])))
        self.connected = True
        #self.file = self.sock.makefile('rb')

    def disconnect(self):
        self.putcmd('QUIT')
        self.connected = False
        self.sock.close()

    def auth_oper(self):
        self.putcmd('OPER %s %s'%(self.config['auth']['nick'], self.config['auth']['oper_password']))
        
    def set_user_mode(self, nickname, channel, mode):
        self.putcmd('MODE %s %s %s'%(channel, mode, nickname))

    def set_channel_mode(self, channel, mode):
        self.putcmd('MODE %s %s'%(channel, mode))
        
    def login(self, nick_in_use=False):
        if nick_in_use:
            self.putcmd('NICK %s_%d'%(self.config['auth']['nick'],random.randint(0,100)))
            self.auth_oper()
            self.putcmd('KILL %s %s'%(self.config['auth']['nick'], 'What the fuck!'))
            time.sleep(3)
        self.putcmd('NICK %s'%self.config['auth']['nick'])
        self.putcmd('USER %s %s %s :%s'%(self.config['auth']['username'], self.config['auth']['hostname'], self.config['auth']['servername'], self.config['auth']['realname']))

    def start_robot(self):
        self.auth_oper()
        self.join_channel(self.config['channels']['log'], u'Лог работы робота')
        self.join_channel(self.config['channels']['notifications'], u'Все сообщения о активности на RSDN')
        GO.rsdn.start()
        self.channelsListObserveTimer.start()
        self.sendLog('Online')

    def request_channels(self):
        self.putcmd('LIST')

    def join_channel(self, channel, topic=None):
        if channel[0] != '#':
            channel = '#' + channel
        channel = GO.unicod(channel)
        #print type(channel), channel
        if self.can_i_work_with_channel(channel) and not self.status.is_on_channel(channel):
            self.sendLog(u'Вхожу на канал %s'%channel)
            self.putcmd(u'SAMODE %s -lri'%channel)
            self.putcmd(u'JOIN %s'%channel)
            self.putcmd(u'SAMODE %s +o %s'%(channel, self.config['auth']['nick']))
            self.putcmd(u'WHO %s'%channel)
            if topic:
                #print type(topic), topic
                self.putcmd(u'TOPIC %s :%s'%(channel, topic))
            self.status.add_channel(channel)

    def whoreply(self, arguments):
        #  RSDNServ #флэйм tmp_acnt rsdn-454FD1D1.dynamic.avangarddsl.ru irc.rsdn.ru scumware[] H@ :0 Философ
        data = arguments.split(' ')
        self.user_entered(data[1], data[5], data[2], data[3])

    def user_entered(self, channel, nickname, ident, host):
        if nickname != GO.utf8(self.config['auth']['nick']):
            self.status.add_user_to_channel(channel, nickname)
            if self.isOperator('%s!%s@%s'%(nickname,ident,host), channel):
                self.set_user_mode(nickname, channel, '+o')

    def received_message(self, prefix, arguments):
        user = self.user_prefix_split(prefix)
        target = arguments[0:arguments.find(' ')]
        text   = arguments[arguments.find(' ')+2:]
        if target == GO.utf8(self.config['auth']['nick']):
            pass
        else:
            self.channel_received(user, target, text)

    def user_prefix_split(self, prefix):
        user = dict()
        user['full']  = prefix
        user['nick']  = prefix[0:prefix.find('!')]
        user['ident'] = prefix[prefix.find('!')+1:prefix.find('@')]
        user['host']  = prefix[prefix.find('@')+1:]
        print user
        return user

    def run(self):
        self.connect()
        self.login()
        prev_line = ''
        line = ''
        while not self.terminate:
            #time.sleep(1)
            for char in self.sock.recv(1024):
                if char not in '\r\n':
                   line += char
                   continue
                if char == '\r': continue
                if char == '\n':
                    print '[-s2c-] %s'%line
                    prefix = ''
                    command = ''
                    asrguments = ''
                    if line[0] == ':':
                        line = line[1:]
                        i = line.find(' ')
                        prefix = line[0:i]
                        line = line[i+1:]
                    i = line.find(' ')
                    command = line[0:i]
                    arguments = line[i+1:]
                    if   command == 'PING'    : self.putcmd('PONG %s'%arguments)
                    elif command == '322'     : self.join_channel(arguments.split(' ')[1])
                    elif command == '352'     : self.whoreply(arguments)
                    elif command == 'PRIVMSG' : self.received_message(prefix, arguments)
                    elif command == '001'     : self.start_robot()
                    elif command == '433'     : self.login(True)
                    #print [prefix, command, arguments]
                    line = ''


    def stop(self):
        self.sendLog('Offline')
        self.channelsListObserveTimer.stop()
        GO.rsdn.stop()
        self.disconnect()
        self.terminate = True

    def can_i_work_with_channel(self, channel):
        #channel = GO.unicod(channel)
        return not self.debug or self.debug and channel in self.bot_channels

    def on_list(self, c, e):
        channel = e.arguments()[0]
        for chname, chobj in self.channels.items():
            if channel == chname:
                return
        self.join_channel(channel)

    def private_received(self, user, text):
        print (user['nick'], text)

    def channel_received(self, user, channel, text):
        prefix = text[0]
        if prefix in '!@':
            command = re.split('\s+', text[1:].strip())
            cmd = command[0]
            parametres = command[1:]
            if cmd in GO.public_commands.keys() and prefix in GO.public_commands[cmd]['pfx']:
                if not GO.public_commands[cmd]['adm'] or GO.public_commands[cmd]['adm'] and self.isOperator(user['full'], channel):
                    result = getattr(self.commander, cmd)(user['nick'], channel, parametres)
                    #print result
                    for ok, text in result:
                        if ok:
                            self.send_reply(prefix, user, channel, text)
                        else:
                            self.send_reply(prefix, user, channel, u'Что то не так. %s'%text)
                    return True
        return False

    def isOperator(self, nick, channel):
        for operator in self.operators['global']:
                if re.match(operator, nick):
                    return True
        for channel in self.operators['channels']:
            for operator in self.operators['channels'][channel]:
                if re.match(operator, nick):
                    return True
        return False

    def send_reply(self, prefix, user, channel, text):
        if prefix == '!':
            self.send_channel_reply(user, channel, text)
        elif prefix == '@':
            self.send_private(user, text)

    def send_notice(self, user, text):
        self.putcmd(u'NOTICE %s :%s'%(user['nick'], text))

    def send_channel_reply(self, user, channel, text):
        self.putcmd(u'PRIVMSG %s :%s: %s'%(channel, user['nick'], text))

    def sendChannelText(self, channel, text):
        #print type(channel), type(text)
        self.putcmd(u'PRIVMSG %s :%s'%(channel, text))

    def send_private(self, user, text):
        self.putcmd(u'PRIVMSG %s :%s'%(user['nick'], text))

    def sendChannelNotification(self, channel, text):
        if self.config['debug']['enable'] != 'true':
            self.sendChannelText(channel, text)

    def sendRsdnNotification(self, text):
        self.sendChannelText(self.config['channels']['notifications'], text)

    def sendLog(self, text):
        self.sendChannelText(self.config['channels']['log'], text)

numeric_events = {
    "001": "welcome",
    "002": "yourhost",
    "003": "created",
    "004": "myinfo",
    "005": "featurelist",  # XXX
    "200": "tracelink",
    "201": "traceconnecting",
    "202": "tracehandshake",
    "203": "traceunknown",
    "204": "traceoperator",
    "205": "traceuser",
    "206": "traceserver",
    "207": "traceservice",
    "208": "tracenewtype",
    "209": "traceclass",
    "210": "tracereconnect",
    "211": "statslinkinfo",
    "212": "statscommands",
    "213": "statscline",
    "214": "statsnline",
    "215": "statsiline",
    "216": "statskline",
    "217": "statsqline",
    "218": "statsyline",
    "219": "endofstats",
    "221": "umodeis",
    "231": "serviceinfo",
    "232": "endofservices",
    "233": "service",
    "234": "servlist",
    "235": "servlistend",
    "241": "statslline",
    "242": "statsuptime",
    "243": "statsoline",
    "244": "statshline",
    "250": "luserconns",
    "251": "luserclient",
    "252": "luserop",
    "253": "luserunknown",
    "254": "luserchannels",
    "255": "luserme",
    "256": "adminme",
    "257": "adminloc1",
    "258": "adminloc2",
    "259": "adminemail",
    "261": "tracelog",
    "262": "endoftrace",
    "263": "tryagain",
    "265": "n_local",
    "266": "n_global",
    "300": "none",
    "301": "away",
    "302": "userhost",
    "303": "ison",
    "305": "unaway",
    "306": "nowaway",
    "311": "whoisuser",
    "312": "whoisserver",
    "313": "whoisoperator",
    "314": "whowasuser",
    "315": "endofwho",
    "316": "whoischanop",
    "317": "whoisidle",
    "318": "endofwhois",
    "319": "whoischannels",
    "321": "liststart",
    "322": "list",
    "323": "listend",
    "324": "channelmodeis",
    "329": "channelcreate",
    "331": "notopic",
    "332": "currenttopic",
    "333": "topicinfo",
    "341": "inviting",
    "342": "summoning",
    "346": "invitelist",
    "347": "endofinvitelist",
    "348": "exceptlist",
    "349": "endofexceptlist",
    "351": "version",
    "352": "whoreply",
    "353": "namreply",
    "361": "killdone",
    "362": "closing",
    "363": "closeend",
    "364": "links",
    "365": "endoflinks",
    "366": "endofnames",
    "367": "banlist",
    "368": "endofbanlist",
    "369": "endofwhowas",
    "371": "info",
    "372": "motd",
    "373": "infostart",
    "374": "endofinfo",
    "375": "motdstart",
    "376": "endofmotd",
    "377": "motd2",        # 1997-10-16 -- tkil
    "381": "youreoper",
    "382": "rehashing",
    "384": "myportis",
    "391": "time",
    "392": "usersstart",
    "393": "users",
    "394": "endofusers",
    "395": "nousers",
    "401": "nosuchnick",
    "402": "nosuchserver",
    "403": "nosuchchannel",
    "404": "cannotsendtochan",
    "405": "toomanychannels",
    "406": "wasnosuchnick",
    "407": "toomanytargets",
    "409": "noorigin",
    "411": "norecipient",
    "412": "notexttosend",
    "413": "notoplevel",
    "414": "wildtoplevel",
    "421": "unknowncommand",
    "422": "nomotd",
    "423": "noadmininfo",
    "424": "fileerror",
    "431": "nonicknamegiven",
    "432": "erroneusnickname", # Thiss iz how its speld in thee RFC.
    "433": "nicknameinuse",
    "436": "nickcollision",
    "437": "unavailresource",  # "Nick temporally unavailable"
    "441": "usernotinchannel",
    "442": "notonchannel",
    "443": "useronchannel",
    "444": "nologin",
    "445": "summondisabled",
    "446": "usersdisabled",
    "451": "notregistered",
    "461": "needmoreparams",
    "462": "alreadyregistered",
    "463": "nopermforhost",
    "464": "passwdmismatch",
    "465": "yourebannedcreep", # I love this one...
    "466": "youwillbebanned",
    "467": "keyset",
    "471": "channelisfull",
    "472": "unknownmode",
    "473": "inviteonlychan",
    "474": "bannedfromchan",
    "475": "badchannelkey",
    "476": "badchanmask",
    "477": "nochanmodes",  # "Channel doesn't support modes"
    "478": "banlistfull",
    "481": "noprivileges",
    "482": "chanoprivsneeded",
    "483": "cantkillserver",
    "484": "restricted",   # Connection is restricted
    "485": "uniqopprivsneeded",
    "491": "nooperhost",
    "492": "noservicehost",
    "501": "umodeunknownflag",
    "502": "usersdontmatch",
}
