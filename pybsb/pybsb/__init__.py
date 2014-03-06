#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pybsb -- python classes for bsb bus system
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

__all__ = [ 'bsb_message','wiringpi2_fake', 'bsb_cache','bsbdaemon']

import os

# Get my log path
logpath = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/../../logs/') + '/'

server_address = 'localhost'
client_target = 'localhost'
port = 12000


jsonrequest = {}
jsonrequest['roomtemp']      = { 'PARAM': '3d2d0215' , 'onlycache': True}
jsonrequest['outtemp']       = { 'PARAM': '053d0521'}
jsonrequest['wpstatus']      = { 'PARAM': '053d07b0'}
jsonrequest['twstatus']      = { 'PARAM': '053d07a2'}
jsonrequest['twnennsoll']    = { 'PARAM': '313d06b9'}
jsonrequest['twredsoll']     = { 'PARAM': '313d06ba'}
jsonrequest['roomsoll']      = { 'PARAM': '2d3d0593'}
jsonrequest['ruecklaufwp']   = { 'PARAM': '593d0537'}
jsonrequest['ruecklaufsoll'] = { 'PARAM': '593d0767'}
jsonrequest['quellein']      = { 'PARAM': '593d05b9'}
jsonrequest['quelleout']     = { 'PARAM': '593d05ba'}
jsonrequest['twsoll']        = { 'PARAM': '313d074b'}
jsonrequest['twtemp1']       = { 'PARAM': '313d052f'}
jsonrequest['twtemp2']       = { 'PARAM': '313d0530'}
jsonrequest['vorlaufwp']     = { 'PARAM': '593d052d'}
jsonrequest['vorlaufsoll']   = { 'PARAM': '213d0667'}
jsonrequest['vorlauftemp']   = { 'PARAM': '213d0518'}
jsonrequest['outtempged']    = { 'PARAM': '053d05f0'}
jsonrequest['outtempgem']    = { 'PARAM': '053d05f2'}
jsonrequest['time']          = { 'PARAM': '0500006c'}

for i in jsonrequest.keys():
    jsonrequest[i].update({'cached'  : 300 })
