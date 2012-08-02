#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import json

class CConfigurable(object):

    def __init__(self, filename):
        fp = open(filename, 'r')
        self.config = json.load(fp)
        fp.close()
