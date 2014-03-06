#!/usr/bin/env python
# -*- coding: utf-8 -*-
# bsbxagent -- bridge some status data to snmp, so you can use cacti or similar
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
__version__ = "0.1.1"
__maintainer__ = "Daniel Heule"
__email__ = "daniel.heule@gmail.com"
__status__ = "Development"

import logging
import logging.handlers

import json
import sys
import time


sys.path.append('../pybsb')
import pyagentx
from pyagentx.agent import Agent
import pybsb.bsbdaemon
import pybsb.bsbdclient
import pybsb






log = logging.getLogger('bsbxagent')
log2 = logging.getLogger('pyagentx')
log3 = logging.getLogger('pybsb')
log.setLevel(logging.DEBUG)
log2.setLevel(logging.DEBUG)
log3.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(name)s %(levelname)8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
lf = logging.handlers.WatchedFileHandler(pybsb.logpath + 'bsbxagent.log')
lf.setLevel(logging.DEBUG)
lf.setFormatter(formatter)
log.addHandler(lf)
log2.addHandler(lf)
log3.addHandler(lf)

class MyAgent(Agent):

    js = json.JSONDecoder()
    
    def setup(self):
        self.register('1.3.6.1.4.1.42507.2.3.1', self.update,120)

    def update(self):
        # Status Values
        status = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['wpstatus'])
        if status and 'value' in status and 'data' in status:
            son = 1
            if status['data'] != '0019':
                son = 2
            log.info('New hsBSBStWP: %s' % status['value'])
            self.append('1.1.1', pyagentx.TYPE_INTEGER,son)
            self.append('1.1.2', pyagentx.TYPE_OCTETSTRING, status['value'])
            self.append('1.1.3', pyagentx.TYPE_INTEGER, int(status['data']))
        status = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['twstatus'])
        if status and 'value' in status and 'data' in status:
            son = 1
            if 'geladen' not in status['value'].lower():
                son = 2
            log.info('New hsBSBStTw: %s' % status['value'])
            self.append('1.2.1', pyagentx.TYPE_INTEGER,son)
            self.append('1.2.2', pyagentx.TYPE_OCTETSTRING, status['value'])
            self.append('1.2.3', pyagentx.TYPE_INTEGER, int(status['data']))
        
        # Trinkwasser Values
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['twnennsoll'])
        if temp and 'value' in temp:
                log.info('hsBSBTwNennSoll: %0.3f' % temp['value'])
                self.append('7.1.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('7.1.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['twredsoll'])
        if temp and 'value' in temp:
                log.info('hsBSBTwRedSoll: %0.3f' % temp['value'])
                self.append('7.2.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('7.2.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])        
                
        
        # Diagnose Erzeuger
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['quellein'])
        if temp and 'value' in temp:
                log.info('hsBSBQuIn: %0.3f' % temp['value'])
                self.append('13.1.1.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.1.1.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
                
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['quelleout'])
        if temp and 'value' in temp:
                log.info('hsBSBQuOut: %0.3f' % temp['value'])
                self.append('13.1.2.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.1.2.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
                
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['vorlaufwp'])
        if temp and 'value' in temp:
                log.info('hsBSBVorlaufWP: %0.3f' % temp['value'])
                self.append('13.1.3.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.1.3.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
                
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['ruecklaufwp'])
        if temp and 'value' in temp:
                log.info('hsBSBRuecklaufWP: %0.3f' % temp['value'])
                self.append('13.1.4.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.1.4.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
                
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['ruecklaufsoll'])
        if temp and 'value' in temp:
                log.info('hsBSBRuecklaufSollWP: %0.3f' % temp['value'])
                self.append('13.1.5.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.1.5.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
        
        # Diagnose Verbraucher
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['roomtemp'])
        if temp and 'value' in temp:
                log.info('hsBSBRoom1t: %0.3f' % temp['value'])
                self.append('13.2.1.1.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.2.1.1.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
                
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['roomsoll'])
        if temp and 'value' in temp:
                log.info('hsBSBRoomSoll: %0.3f' % temp['value'])
                self.append('13.2.2.1.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.2.2.1.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
                
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['vorlaufsoll'])
        if temp and 'value' in temp:
                log.info('hsBSBVorlaufSoll: %0.3f' % temp['value'])
                self.append('13.2.3.1.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.2.3.1.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
         
         # Ist bei meiner WP immer 0.0 da kein vorlauf sendsor ausserhalb wp verbaut wurde
#        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['vorlauftemp'])
#        if temp and 'value' in temp:
#                log.info('hsBSBVorlauf: %0.3f' % temp['value'])
#                self.append('13.2.4.1.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
#                self.append('13.2.4.1.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])

        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['outtemp'])
        if temp and 'value' in temp:
                log.info('hsBSBOutTAct: %0.3f' % temp['value'])
                self.append('13.2.5.1.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.2.5.1.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])

        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['outtempged'])
        if temp and 'value' in temp:
                log.info('hsBSBOutTGed: %0.3f' % temp['value'])
                self.append('13.2.5.2.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.2.5.2.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])

        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['outtempgem'])
        if temp and 'value' in temp:
                log.info('hsBSBOutTGem: %0.3f' % temp['value'])
                self.append('13.2.5.3.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.2.5.3.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])

        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['twsoll'])
        if temp and 'value' in temp:
                log.info('hsBSBTwSoll: %0.3f' % temp['value'])
                self.append('13.2.6.1.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.2.6.1.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])

        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['twtemp1'])
        if temp and 'value' in temp:
                log.info('hsBSBTwTemp1: %0.3f' % temp['value'])
                self.append('13.2.6.2.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.2.6.2.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])
                
        temp = pybsb.bsbdclient.getbsb(pybsb.jsonrequest['twtemp2'])
        if temp and 'value' in temp:
                log.info('hsBSBTwTemp2: %0.3f' % temp['value'])
                self.append('13.2.6.3.1', pyagentx.TYPE_INTEGER, int(temp['value']*1000))
                self.append('13.2.6.3.2', pyagentx.TYPE_OCTETSTRING,'%0.3f' % temp['value'])

        self.append('100.1', pyagentx.TYPE_OCTETSTRING,str(time.strftime('%Y-%m-%d %H:%M:%S')))
        
        
def main():
    log.info('Startup BSBxagent')
    a = MyAgent()
    try:
        a.debug = 0
        a.start()
    except:
        log.exception('i was terminated by:')
    finally:
        a.stop()


if __name__=="__main__":
    daemon = pybsb.bsbdaemon.BSBDaemon(pidfile='/var/run/xagent/bsbxagent.pid',files_preserve=[lf.stream])
    d = daemon.run(proctitle='bsbxagent')
    if d is not None:
        with d:
            main()
