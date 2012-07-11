#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, string, os, json

class CConfigurable(object):

    def __init__(self, filename):
        json_data=open(filename)
        self.config = json.load(json_data)
        json_data.close()
