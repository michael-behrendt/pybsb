#!/usr/bin/env python
# -*- coding: utf-8 -*-
# bsbdclient -- client class to easy access the bsbd daemon
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



import logging
import socket
import json


import pybsb

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# Helper functions for client programms


def getbsb(req):
    try:
        s = socket.socket()
        s.connect((pybsb.client_target,pybsb.port))
        s.send(json.dumps(req) + '\n\n')
        f = s.makefile()
        line1 = f.readline()
        line2 = f.readline()
    finally:
        s.close()
    if line2 == '\n':
        try:
            return json.loads(line1)
        except ValueError as e:
            log.error('Json decoding of %s failed: %s' % (line1, e.message ))
            return None