#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Global Object
import sys, os
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import Bot, RSDNSync, Storage

public_commands = {
        'op'    : { 'pfx': '!' , 'adm': True , 'hlp': u'Получить статус оператора канала', 'epl': u'!op' },
        'deop'  : { 'pfx': '!' , 'adm': True , 'hlp': u'Снять статус оператора канала', 'epl': u'!deop' },
        'mute'  : { 'pfx': '!' , 'adm': True , 'hlp': u'Сделать канал модерируемым', 'epl': u'!mute' },
        'demute': { 'pfx': '!' , 'adm': True , 'hlp': u'Сделать канал немодерируемым', 'epl': u'!demute' },
        'g'     : { 'pfx': '!@', 'adm': False, 'hlp': u'Вывести ссылк на поисковые системы с подставленной фразой для поиска', 'epl': u'!g <фраза>' },
        'top'   : { 'pfx': '!@', 'adm': False, 'hlp': u'Вывести статистику активных пользователей канала', 'epl': u'!top <число>' },
        'mid'   : { 'pfx': '!@', 'adm': False, 'hlp': u'Вывести информацию о сообщении форума', 'epl': u'!mid <id сообщения форума>' },
        'uid'   : { 'pfx': '!@', 'adm': False, 'hlp': u'Вывести информацию о пользователе форума', 'epl': u'!uid <id или имя (не ник!) пользователя форума>' },
        'pwgen' : { 'pfx': '!@', 'adm': False, 'hlp': u'Сгенерировать пароль. Параметры - флаги и длинна. Флаги: `a`-lowercase alpha, `A`-uppercase aplpha, `d`- digits, `p`-пунктуация, `s`-пробел. Пароль выводится внутри <> скобок.', 'epl': u'!pwgen <флаги> <длинна>' },
        'help'  : { 'pfx': '!@', 'adm': False, 'hlp': u'Помощь по командам бота', 'epl': '!help' },
        'today' : { 'pfx': '!@', 'adm': False, 'hlp': u'Дневная статистика', 'epl': u'!today' },
        'dbstat': { 'pfx': '!@', 'adm': True , 'hlp': u'Получить статистику БД', 'epl': u'!dbstat' },
                  }
prvate_commands = {
        'register': { 'adm': False , 'hlp': u'Зарегестрировать свой ник', 'epl': u'register <nickname> <rsdn nickname> <rsdn password>' },
        'auth'    : { 'adm': False , 'hlp': u'Авторизироваться', 'epl': u'auth <rsdn nickname> <rsdn password>' }
                  }

storage = Storage.CStorage()
bot     = Bot.CBot()
rsdn    = RSDNSync.CRSDNSync()


def utf8(s):
    try:
        if   type(s) == type(u''):
            return s.encode('utf8')
        elif type(s) == type(''):
            return s
        else: 
            print 'Не тот тип: %s (%s) '%(type(s), s)
    except UnicodeDecodeError:
        print 'utf8. Unicode error: ' + s
        bot.stop()
        
def unicod(s):
    try:
        if   type(s) == type(u''):
            return s
        elif type(s) == type(''):
            return unicode(s.decode('utf8'))
        else: 
            print 'Не тот тип: %s (%s) '%(type(s), s)
    except UnicodeDecodeError:
        print 'Unicode. Unicode error: ' + s
        bot.stop()
