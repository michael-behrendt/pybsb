#!/usr/bin/env python
# -*- coding: utf-8 -*-
# wiringpi2_fake -- Fake module for wiringpi2, emulate calls on pc where the lib is not aviable
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

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

def wiringPiSetupGpio():
    log.debug('You called wiringpi_fake.wiringPiSetupGpio(), on PC, this is normal, on RSPI please install wiringPI2 !')

def pinMode(pin,mode):
    log.debug('You called wiringpi_fake.pinMode(), on PC, this is normal !')
    
    
def digitalWrite(pin,mode):
    log.debug('You called wiringpi_fake.digitalWrite(), on PC, this is normal !')

