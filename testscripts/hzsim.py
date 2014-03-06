#!/usr/bin/env python
# -*- coding: utf-8 -*-
# hzsim -- simulates recorded bsb messages on a serial-0-modem link
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
import serial
from time import sleep


def bitswapper(toreverse):
    msg = bytearray(toreverse)
    for i in range(len(msg)):
        msg[i] = msg[i] ^ 0xff
    return str(msg)
 
#device='/dev/ttyUSB1'
# Local loopback serial can be created with:
# socat PTY,link=/dev/ttyS10,mode=660 PTY,link=/dev/ttyS11,mode=660 &
device='/dev/ttyS10'
delay=1.5

testmsg=('dc8a000b063d0d05194f8c'.decode('hex'),
         'dc800a0e070d3d0519000ee061aa'.decode('hex'),
         'dc86000b063d0d05195e3b'.decode('hex'),
         'dc86000b063d0d05195e3b08dc'.decode('hex'),
         '86000b063d0d05195e3b'.decode('hex'),
         'dc80060e070d3d0519000ee086d4'.decode('hex'),
         'dc80060f070d3d0519000fe086d4'.decode('hex'), # Wrong leng
         'dc800a0e07053d056f00fd8ef54a'.decode('hex'), # Wrong CRC
         'dc8a000b063d0505215176'.decode('hex'),
         'dc800a0e07053d052100009336d6'.decode('hex'), # 2.3 grad aussentemp 
         'dc807f0e023100021201004d577f'.decode('hex')
         )


testraw=()


    
for msgt in testmsg:
    tup = ( bitswapper(msgt), )
    testraw += tup


try:
    ser = serial.Serial(device, 4800, timeout=delay,parity=serial.PARITY_ODD)
#    while True:
    if True:
        if len(sys.argv) > 1 and sys.argv[1] == '--extern':
            print 'lade nun testdaten von %s' % sys.argv[2]
            f = open(sys.argv[2],'r')
            for line in f:
                startpos = line.lower().find('dc')
                if startpos:
                    print line[startpos:].replace(' ','').strip()
                    msg = bytearray(line[startpos:].replace(' ','').strip().decode('hex'))
                    bmsg = bitswapper(msg)
                    ser.write(bmsg)
                    r = ser.read(11)
                    while(r != ''):
                        print r.encode('hex')
                        ser.write(r)
                        r = ser.read()
            print 'Ende des Testfiles erreicht, starte von vorne'
        else:
            for i in testraw:
                #ser.write(i[0:5])
                #ser.flush()
                #sleep(200.0/4800.0)
                #sleep(10.0)
                #ser.write(i[5:])
                #ser.flush()
                print i.encode('hex')
                ser.write(i)
                ser.flushInput()
                sleep(delay)            
finally:
  print 'Done ...'
