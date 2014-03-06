#!/usr/bin/env python
# -*- coding: utf-8 -*-
# logdecoder -- decode writen bsb logfiles for human ;-)
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



import sys
import fileinput
sys.path.append('../pybsb/')
import pybsb.bsb_message as bsb_message

bsbmsg = bsb_message.Bsb_message()


def decodeline(line):
    startpos = line.lower().find('dc')
    if startpos:
        msg = line[startpos:].replace(' ','').strip().decode('hex')
        bsbmsg.setval(msg)
        print str(bsbmsg)
    else:
        startpos = line.lower().find('23')
        if startpos:
            msg = line[startpos:].replace(' ','').strip().decode('hex')
            bsbmsg.setrawval(msg)
            print str(bsbmsg)


try:
    if len(sys.argv) == 2 and sys.argv[1] == '--tail':
        # Würgaround buffer problem with pipes and fileinput ...
        while True:
            line = sys.stdin.readline()
            decodeline(line)
    else: 
        for line in fileinput.input(bufsize=10):
            decodeline(line)

finally:
  print 'Done ...'
