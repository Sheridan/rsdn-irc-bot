#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, string, os, re, random, urllib2
from xml.dom.minidom import parseString
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO

class CCommander(object):

    def _checkInt(self, val, minimum, maximum):
        if val == None or val == '':
            return [0, u'Отсутствует параметр, почитайте #help']
        try:
            num = int(val)
        except ValueError:
            return [0, u'Не вижу числа, почитайте #help']
        if num < minimum:
            return [0, u'Число слишком маленькое']
        if num > maximum:
            return [0, u'Число слишком большое']
        return [1, num]

    def _checkFlags(self, val, flags):
        val = val.strip()
        for flag in val:
            if flag not in flags:
                return [0, u'Неизвестный флаг `%s`, почитайте #help'%flag]
        return [1, val]

    def _checkString(self, val):
        if val == None or val == '':
            return [0, u'Отсутствует параметр, почитайте #help']
        return [1, val]

    def mute  (self, cmd): cmd.channel().set_mode('+m')
    def demute(self, cmd): cmd.channel().set_mode('-m')
    def op    (self, cmd): cmd.user().set_mode(cmd.channel(), '+o')
    def deop  (self, cmd): cmd.user().set_mode(cmd.channel(), '-o')
    
    def g(self, cmd):
        (ok, kw) = self._checkString(' '.join(cmd.arguments()))
        if ok:
            kw = '%20'.join(kw.split(' '))
            engines = [u'http://img.meta.ua/rsdnsearch/?q=%s',
                       u'https://www.google.ru/#q=%s',
                       u'http://yandex.ru/yandsearch?text=%s',
                       u'http://lmgtfy.com/?q=%s',
                       u'http://www.wolframalpha.com/input/?i=%s']
            cmd.reply(u' '.join([engine%kw for engine in engines]))
        else: cmd.reply_error(kw)

    def mid(self, cmd):
        (ok, mid) = self._checkInt(''.join(cmd.arguments()), 1, 2147483646)
        if ok:
            data = GO.rsdn.getTopic(mid)
            if data['exists']:
                cmd.reply(u'Пост находится в топике `%s` ( %s ) за дату %s, от пользователя %s. Ответы %s.'%(
                                                                                            data['top']['subject'], 
                                                                                            GO.rsdn.getMessageUrlById(data['top']['mid']),
                                                                                            data['top']['date'],
                                                                                            data['top']['user'],
                                                                                            u'запрещены' if data['top']['closed'] else u'разрешены'))
                cmd.reply(u'Пост `%s` ( %s ) написан %s пользователем %s. Ответы %s.'%(
                                                                                            data['self']['subject'], 
                                                                                            GO.rsdn.getMessageUrlById(data['self']['mid']),
                                                                                            data['self']['date'],
                                                                                            data['self']['user'],
                                                                                            u'запрещены' if data['self']['closed'] else u'разрешены'))
                #self.bot.sendPrivate(nickname, '---- Текст сообщения ----')
                #for msg in data['self']['message'].split('\n'):
                #    self.bot.sendPrivate(nickname, msg)
                #self.bot.sendPrivate(nickname, '-------------------------')
                cmd.reply(u'Участники: %s'%(u', '.join(['%s:%s'%(mber,cnt) for mber, cnt in data['members'].items()])))
                cmd.reply(u'Всего сообщений в топике: %d'%data['count'])
                rate = GO.storage.getTopicRating(mid)
                cmd.reply(u'Оценка сообщения (из БД): %s'%rate)
            else: cmd.reply_error(u'Сообщение не существует или ошибка сервера')
        else: cmd.reply_error(kw)

    def uid(self, cmd):
        (ok, uid) = self._checkInt(''.join(cmd.arguments()), 1, 2147483646)
        if not ok:
            (ok, uid) = self._checkString(''.join(cmd.arguments()))
            if not ok: 
                cmd.reply_error(uid)
                return
            uid = GO.storage.getUserIdByName(uid)
            if uid == None: 
                cmd.reply_error(u'Не могу найти у себя этого пользователя')
                return
        data = GO.rsdn.getUser(uid)
        if data != None:
            dbdata = GO.storage.getUserStats(uid)
            cmd.reply(u'Имя: %s, ник: %s, реальное имя: %s. Город: %s. Специализация: %s. Web: %s. '%(
                                                                                        data['userName'], 
                                                                                        data['userNick'],
                                                                                        data['realName'],
                                                                                        data['whereFrom'],
                                                                                        data['specialization'],
                                                                                        data['homePage']))
            cmd.reply(u'Сообщений (в БД): %s'%(dbdata['f_msgs']))
            cmd.reply(u'top10 отвечающих пользователю (из БД): %s'%dbdata['t10_o2u'])
            cmd.reply(u'top10 ответов пользователям (из БД): %s'%dbdata['t10_u2o'])
            cmd.reply(u'Оценки, выставленные пользователем (из БД): %s'%GO.storage.getUserToOtherRating(uid))
            cmd.reply(u'Оценки, выставленные пользователю (из БД): %s'%GO.storage.getOtherToUserRating(uid))
        else: cmd.reply_error(u'Пользователя не существует или ошибка сервера')

    def top(self, cmd):
        (ok, num) = self._checkInt(''.join(cmd.arguments()), 2, 30)
        if not ok: 
            cmd.reply_error(num)
            return
        reply = []
        print GO.storage.getTopOfChannel(cmd.channel().name(), num)
        for line in GO.storage.getTopOfChannel(cmd.channel().name(), num):
            reply.append(u'%s: %s'%line)
        return cmd.reply(u'Top%s флеймеров канала %s: %s'%(num, cmd.channel().name(), ', '.join(reply)))

    def help(self, cmd):
        cmd.reply(u'RSDNServ, робот интеграции RSDN в IRC. https://github.com/Sheridan/rsdn-irc-bot')
        cmd.reply(u'--- Комманды каналов ---')
        cmd.reply(u'Каждая комманда предваряется префиксом. ! - ответы бота видны для всех на канале, @ - ответы бота отправляются в приват')
        for command in GO.public_commands.keys():
            cmd.reply(u'%s: %s. Возможные префиксы: %s. Доступна %s. Пример: %s'%
                                       (command, 
                                       GO.public_commands[command]['hlp'],
                                       GO.public_commands[command]['pfx'],
                                       u'администраторам робота' if GO.public_commands[command]['adm'] else u'всем',
                                       GO.public_commands[command]['epl']
                                       ))

    def pwgen(self, cmd):
        if len(cmd.arguments()) < 2: 
            cmd.reply_error(u'Пропущен один из параметров')
            return
        (flags, length) = cmd.arguments()[0:2]
        (ok, length) = self._checkInt(length, 3, 64)
        if not ok: 
            cmd.reply_error(length)
            return
        (ok, flags) = self._checkFlags(flags, 'aAdps')
        if not ok: 
            cmd.reply_error(flags)
            return
        source = ''
        for flag in flags:
            if   flag == 'a': source += string.ascii_lowercase
            elif flag == 'A': source += string.ascii_uppercase
            elif flag == 'd': source += string.digits
            elif flag == 'p': source += string.punctuation
            elif flag == 's': source += ' '
        cmd.reply(u'<%s>'%''.join(random.choice(source) for x in range(length)))

    def today(self, cmd):
        data = GO.storage.getTodayEvents(cmd.channel().name())
        cmd.reply(u'Сообщений на канале: %s, обращений к роботу: %s, сообщений на форуме канала: %s'%(data['ch_msgs'], data['ch_bot'], data['f_msgs']))

    def dbstat(self, cmd):
        stat = GO.storage.getDBStat()
        for table in stat.keys():
            cmd.reply(u'Количество записей в таблице %s: %d'%(table, stat[table]))

    def wiki(self, cmd):
        (ok, kw) = self._checkString('%20'.join(cmd.arguments()))
        if ok:
            downloaded = urllib2.urlopen('http://ru.wikipedia.org/w/api.php?format=xml&action=opensearch&search=%s'%GO.utf8(kw))
            dom = parseString(downloaded.read())
            downloaded.close()
            root = dom.getElementsByTagName('SearchSuggestion')[0].getElementsByTagName('Section')[0]
            cnt = root.getElementsByTagName('Item').length
            if   cnt == 0:
                cmd.reply(u'Нет такого в википедии')
            elif cnt  > 1:
                for a in root.getElementsByTagName('Item'):
                    if a.getElementsByTagName('Text')[0].firstChild.data.strip() == u' '.join(cmd.arguments()):
                        cmd.reply(u'%s (%s)'%(a.getElementsByTagName('Description')[0].firstChild.data.strip(), a.getElementsByTagName('Url')[0].firstChild.data.strip()))
                cmd.reply(u'Варианты: %s'%u', '.join([a.getElementsByTagName('Text')[0].firstChild.data.strip() for a in root.getElementsByTagName('Item')]))
            elif cnt == 1:
                i = root.getElementsByTagName('Item')[0]
                cmd.reply(u'%s (%s)'%(i.getElementsByTagName('Description')[0].firstChild.data.strip(), i.getElementsByTagName('Url')[0].firstChild.data.strip()))
        else:
            cmd.reply_error(kw)
