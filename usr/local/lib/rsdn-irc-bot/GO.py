#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Global Object
import sys, os
sys.path.append(os.path.abspath('/usr/local/lib/rsdn-irc-bot/'))
import Bot, RSDNSync, Storage

public_commands = {
        "op"    : { 'pfx': '!'  , 'adm': True , 'hlp': 'Получить статус оператора канала', 'epl': '!op' },
        "deop"  : { 'pfx': '!'  , 'adm': True , 'hlp': 'Снять статус оператора канала', 'epl': '!deop' },
        "mute"  : { 'pfx': '!'  , 'adm': True , 'hlp': 'Сделать канал модерируемым', 'epl': '!mute' },
        "demute": { 'pfx': '!'  , 'adm': True , 'hlp': 'Сделать канал немодерируемым', 'epl': '!demute' },
        "g"     : { 'pfx': '!@#', 'adm': False, 'hlp': 'Вывести ссылк на поисковые системы с подставленной фразой для поиска', 'epl': '!g <фраза>' },
        "top"   : { 'pfx': '!@#', 'adm': False, 'hlp': 'Вывести статистику активных пользователей канала', 'epl': '!top <число>' },
        "mid"   : { 'pfx': '!@#', 'adm': False, 'hlp': 'Вывести информацию о сообщении форума', 'epl': '!mid <id сообщения форума>' },
        "uid"   : { 'pfx': '!@#', 'adm': False, 'hlp': 'Вывести информацию о пользователе форума', 'epl': '!uid <id или имя (не ник!) пользователя форума>' },
        "pwgen" : { 'pfx': '!@#', 'adm': False, 'hlp': 'Сгенерировать пароль. Параметры - флаги и длинна. Флаги: `a`-lowercase alpha, `A`-uppercase aplpha, `d`- digits, `p`-пунктуация, `s`-пробел. Пароль выводится внутри <> скобок.', 'epl': '!pwgen <флаги> <длинна>' },
        "help"  : { 'pfx': '!@#', 'adm': False, 'hlp': 'Помощь по командам бота', 'epl': '!help' },
        "today" : { 'pfx': '!@#', 'adm': False, 'hlp': 'Дневная статистика', 'epl': '!today' }
                  }
prvate_commands = {
        "register": { 'adm': False , 'hlp': 'Зарегестрировать свой ник', 'epl': 'register <nickname> <rsdn nickname> <rsdn password>' },
        "auth"    : { 'adm': False , 'hlp': 'Авторизироваться', 'epl': 'auth <rsdn nickname> <rsdn password>' }
                  }

storage = Storage.CStorage()
bot     = Bot.CBot()
rsdn    = RSDNSync.CRSDNSync()


def utf8(s):
    try:
        return unicode(s).encode('utf8')
    except UnicodeDecodeError:
        print 'Unicode error: ' + s
        bot.stop()
