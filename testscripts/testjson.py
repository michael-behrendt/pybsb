#!/usr/bin/env python
# -*- coding: utf-8 -*-
# testjson -- send and recive test json messages to the bsb.py daemon
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

import socket
import json
import time


# Raumtemperatur
testdata1 = { 'PARAM' : '3d2d0215',
#             'cached'  : 0 ,
             'nosend'  : True,
             'timeout' : 15,
             'onlycache' : False }

# Aussentemperatur
testdata2 = { 'PARAM' : '053d0521',
             'cached'  : 300 ,
             'onlycache' : False }

# Heizungsstatus
testdata3 = { 'PARAM' : '053d07b0',
             'cached'  : 300 ,
             'onlycache' : True }             
             

js = json.JSONDecoder()

try:
  s = socket.socket()
  s.connect(('localhost',12000))
  s.settimeout(8.0)
  i = 0
  while i < 3:
      i += 1
      fromt = time.time()
      s.send(json.dumps(testdata2) + '\n\n')
      data = s.recv(1024)
      if '\n\n' in data:
          try:
              a = json.loads(data.strip())
              try:
                  print a['value'], a['unit'], time.time() - fromt
              except KeyError:
                  print a
          except ValueError as e:
              print 'Json decoding of %s failed: %s' % (data.strip(), e.message )
      else:
          print 'No double lineend ins buffer found, data recived: "%s"' % data.strip()
      time.sleep(15)
#      s.close()
finally:
    s.close()
    print 'Done ...'

