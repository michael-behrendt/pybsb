#!/usr/bin/env python
# -*- coding: utf-8 -*-
# bsb_logger -- logs and sends messages of the bsb bus system
# Copyright (C) 2013  Daniel Heule <daniel.heule@gmail.com>
#
# This file is part of pybsb.
#
# pybsb is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License.
#
# pybsb is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pybsb.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Daniel Heule"
__copyright__ = "Copyright 2013, Daniel Heule"
__credits__ = ["Daniel Heule"]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Daniel Heule"
__email__ = "daniel.heule@gmail.com"
__status__ = "Development"

import time
import logging
from collections import deque

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class Bsb_cache(object):
    
    __stack = deque()
    __cachetime = 0
    
    def __init__(self, mytime):
        log.info('initialized Bsb_cache with %i seconds' % mytime)
        self.__cachetime = mytime
    
    def append(self,msg):
        if msg.TYP != 0x06:
            log.debug('append new message %s to cache' % msg.PARAM)
            self.__stack.appendleft(msg)
            while self.__stack[-1]._lastmod + self.__cachetime < time.time():
                self.__stack.pop()
                log.debug('dropping one to old message from cache')
            log.debug('new cache wattermark: %i' % len(self.__stack))
        else:
            log.debug('i don\'t append the message, since it\'s type 0x06')
    
    def get(self,msgparam):
        log.debug('search message %s' % msgparam)
        for i in self.__stack:
            if i.PARAM == msgparam:
                log.debug('found a message')
                return i
        log.debug('no message found')
        return None
        
    def get_in_time(self,msgparam,fromtime):
        log.debug('search message %s in the last %i s' % (msgparam,time.time() -fromtime))
        i = self.get(msgparam)
        if i != None:
            if i._lastmod >= fromtime:
                log.debug('found a message')
                return i
        log.debug('no message found')
        return None
        
    def getall(self,msgparam):
        log.debug('search all messages %s' % msgparam)
        ret = []
        for i in self.__stack:
            if i.PARAM == msgparam:
                ret.append(i)
        log.debug('found %i messages' % len(ret))
        return ret
