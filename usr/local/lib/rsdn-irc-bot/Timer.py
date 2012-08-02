#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import time
from threading import Thread

class CTimer(Thread):

    def __init__(self, interval, target):
        Thread.__init__(self)
        self.interval = interval
        self.target = target
        self.terminate = False

    def run(self):
        doit = True
        while doit:
            self.target()
            for x in range(0, int(self.interval)):
                if self.terminate:
                    doit = False
                    break
                time.sleep(1)

    def stop(self):
        self.terminate = True
