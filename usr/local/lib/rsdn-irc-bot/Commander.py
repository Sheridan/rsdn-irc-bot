#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, string, os, re, random
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import GO

class CCommander(object):

    def _checkInt(self, val, minimum, maximum):
        if val == None or val == '':
            return [0, "Отсутствует параметр, почитайте #help"]
        try:
            num = int(val)
        except ValueError:
            return [0, "Не вижу числа, почитайте #help"]
        if num < minimum:
            return [0, "Число слишком маленькое"]
        if num > maximum:
            return [0, "Число слишком большое"]
        return [1, num]

    def _checkFlags(self, val, flags):
        val = val.strip()
        for flag in val:
            if flag not in flags:
                return [0, 'Неизвестный флаг `%s`, почитайте #help'%flag]
        return [1, val]

    def _checkString(self, val):
        if val == None or val == '':
            return [0, "Отсутствует параметр, почитайте #help"]
        return [1, val]

    def mute(self, nickname, channel, parametres):
        GO.bot.setChannelMode(channel, '+m')
        return []

    def demute(self, nickname, channel, parametres):
        GO.bot.setChannelMode(channel, '-m')
        return []

    def op(self, nickname, channel, parametres):
        GO.bot.setUserMode(nickname, channel, '+o')
        return []

    def deop(self, nickname, channel, parametres):
        GO.bot.setUserMode(nickname, channel, '-o')
        return []

    def g(self, nickname, channel, parametres):
        (ok, kw) = self._checkString(' '.join(parametres))
        if not ok: return [[0, kw]]
        kw = '%20'.join(kw.split(' '))
        engines = ['http://img.meta.ua/rsdnsearch/?q=%s',
                   'https://www.google.ru/#q=%s',
                   'http://yandex.ru/yandsearch?text=%s',
                   'http://lmgtfy.com/?q=%s',
                   'http://www.wolframalpha.com/input/?i=%s']
        return [[1, ' '.join([engine%kw for engine in engines])]]

    def mid(self, nickname, channel, parametres):
        (ok, mid) = self._checkInt(''.join(parametres), 1, 2147483646)
        if not ok: return [[0, mid]]
        data = GO.rsdn.getTopic(mid)
        if data['exists']:
            result = []
            result.append([1, 'Пост находится в топике `%s` ( %s ) за дату %s, от пользователя %s. Ответы %s.'%(
                                                                                        data['top']['subject'], 
                                                                                        GO.rsdn.getMessageUrlById(data['top']['mid']),
                                                                                        data['top']['date'],
                                                                                        data['top']['user'],
                                                                                        'запрещены' if data['top']['closed'] else 'разрешены')])
            result.append([1, 'Пост `%s` ( %s ) написан %s пользователем %s. Ответы %s.'%(
                                                                                        data['self']['subject'], 
                                                                                        GO.rsdn.getMessageUrlById(data['self']['mid']),
                                                                                        data['self']['date'],
                                                                                        data['self']['user'],
                                                                                        'запрещены' if data['self']['closed'] else 'разрешены')])
            #self.bot.sendPrivate(nickname, '---- Текст сообщения ----')
            #for msg in data['self']['message'].split('\n'):
            #    self.bot.sendPrivate(nickname, msg)
            #self.bot.sendPrivate(nickname, '-------------------------')
            result.append([1, 'Участники: %s'%(', '.join(['%s:%s'%(mber,cnt) for mber, cnt in data['members'].items()]))])
            result.append([1, 'Всего сообщений в топике: %d'%data['count']])
            return result
        return [[0, 'Сообщение не существует или ошибка сервера']]

    def uid(self, nickname, channel, parametres):
        (ok, uid) = self._checkInt(''.join(parametres), 1, 2147483646)
        if not ok: 
            (ok, uid) = self._checkString(''.join(parametres))
            if not ok: return [[0, uid]]
            uid = GO.storage.getUserIdByName(uid)
            if uid == None: return [[0, 'Не могу найти у себя этого пользователя']]
        data = GO.rsdn.getUser(uid)
        if data != None:
            dbdata = GO.storage.getUserStats(uid)
            result = []
            result.append([1, 'Имя: %s, ник: %s, реальное имя: %s. Город: %s. Специализация: %s. Web: %s. '%(
                                                                                        GO.utf8(data['userName']), 
                                                                                        GO.utf8(data['userNick']),
                                                                                        GO.utf8(data['realName']),
                                                                                        GO.utf8(data['whereFrom']),
                                                                                        GO.utf8(data['specialization']),
                                                                                        GO.utf8(data['homePage'])
                                                                                                             )])
            result.append([1, 'Сообщений (в БД): %s'%(dbdata['f_msgs'])])
            result.append([1, 'top10 отвечающих пользователю: %s'%dbdata['t10_o2u']])
            result.append([1, 'top10 ответов пользователям: %s'%dbdata['t10_u2o']])
            return result
        return [[0, 'Пользователя не существует или ошибка сервера']]

    def top(self, nickname, channel, parametres):
        (ok, num) = self._checkInt(''.join(parametres), 2, 30)
        if not ok: return [[0, num]]
        reply = []
        for line in GO.storage.getTopOfChannel(channel, num):
            reply.append("%s: %s"%line)
        return [[1, "Top%s флеймеров канала %s: %s"%(num, channel, ', '.join(reply))]]

    def help(self, nickname, channel, parametres):
        result = []
        result.append([1, 'RSDNServ, робот интеграции RSDN в IRC. https://github.com/Sheridan/rsdn-irc-bot'])
        result.append([1, '--- Комманды каналов ---'])
        result.append([1, 'Каждая комманда предваряется префиксом. ! - ответы бота видны для всех на канале, @ - ответы бота отправляются в приват, # - ответы бота отправляются нотайсами на канал'])
        for cmd in GO.public_commands.keys():
          result.append([1, '%s: %s. Возможные префиксы: %s. Доступна %s. Пример: %s'%
                                       (cmd, 
                                       GO.public_commands[cmd]['hlp'],
                                       GO.public_commands[cmd]['pfx'],
                                       'администраторам робота' if GO.public_commands[cmd]['adm'] else 'всем',
                                       GO.public_commands[cmd]['epl']
                                       )])
        return result

    def pwgen(self, nickname, channel, parametres):
        if len(parametres) < 2: return [[0, "Пропущен один из параметров"]]
        (flags, length) = parametres[0:2]
        (ok, length) = self._checkInt(length, 3, 64)
        if not ok: return [[0, length]]
        (ok, flags) = self._checkFlags(flags, 'aAdps')
        if not ok: return [[0, flags]]
        source = ''
        for flag in flags:
            if   flag == 'a': source += string.ascii_lowercase
            elif flag == 'A': source += string.ascii_uppercase
            elif flag == 'd': source += string.digits
            elif flag == 'p': source += string.punctuation
            elif flag == 's': source += ' '
        return [[1, '<%s>'%''.join(random.choice(source) for x in range(length))]]

    def today(self, nickname, channel, parametres):
        data = GO.storage.getTodayEvents(channel)
        return [[1, 'Сообщений на канале: %s, обращений к роботу: %s, сообщений на форуме канала: %s'%(data['ch_msgs'], data['ch_bot'], data['f_msgs'])]]

    def dbstat(self, nickname, channel, parametres):
        result = []
        stat = GO.storage.getDBStat()
        for table in stat.keys():
            result.append([1, 'Количество записей в таблице %s: %d'%(table, stat[table])])
        return result