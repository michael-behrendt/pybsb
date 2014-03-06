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

import serial
import os
import select
import datetime
import time
import sys

import pybsb.bsb_message as bsb_message
import pybsb.bsb_cache as bsb_cache
# Try to import wiringpi2 --> on pc to test is not aviable, so fake it ...
try:
    import wiringpi2 as wiringpi
except ImportError:
    import pybsb.wiringpi2_fake as wiringpi
    



# Now set the pin 25 to up so we can send data ;-)
try:
    wiringpi.wiringPiSetupGpio()
    wiringpi.pinMode(25,1) # Set Pin 25 to output
    wiringpi.digitalWrite(25,1) # 3.3V so sender is enabled ...

    if os.path.exists('/dev/ttyAMA0'):
      device='/dev/ttyAMA0'
    else:
      device='/dev/ttyUSB0'
      device='/dev/ttyS11'
      
    logfile = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/../logs/bsbtrace.log')
    
    msgnr = 0
    lastsend = 0
    
    
            
    if __name__ == "__main__":
        with open(logfile,'a') as logf:
            logf.write('# Start Logging ...\n')
            print 'Open Serial port %s' % device
            ser = serial.Serial(device, 4800, timeout=(24.0/4800.0),parity=serial.PARITY_ODD)
            cache = bsb_cache.Bsb_cache(600)
#            ser = serial.Serial(device, 4800, timeout=0,parity=serial.PARITY_ODD)
            inputs = [ ser ]
            outputs = [ ]
            val = ''
            while True:
                readable, writable, exceptional = select.select(inputs, outputs, inputs)
                val += readable[0].read(32)
                while len(val) > 11:
    #                print 'Bevor ' + val.encode('hex')
                    msg = bsb_message.Bsb_message()
                    val = msg.setrawval(val)
    #                print 'Uebrig ' + val.encode('hex')
    #                print msg.valid()
    #                print msg.lendif()
                    if msg.lendif() > 0:
    #                   print 'Nachlesen von %i bytes' % msg.lendif()
    #                   print val.encode('hex')
                        break
                    mstate =  msg.check_parse_status()
                    if mstate != 0  or True:
                        dat = str(datetime.datetime.now())
                        print ""
                        print dat + " :"
                        print ""
                        print msg
                        cache.append(msg)                    
                        sys.stdout.flush()
                        logf.write(dat + " " + bsb_message.pstate.get(mstate,'State?') + " " + msg.getlogval())
    #  This is bad for the sd card in the pi ...                    
                        logf.flush()
    #                    os.fsync(logf.fileno())
                        msgnr += 1
    #                    if msgnr >= 4 and False:
                        if time.time() > lastsend + 60 and False: 
                            msgnr = 0
                            lastsend = time.time()
                            time.sleep(0.5)
                            print 'Sending Message .....'
                            smsg = bsb_message.Bsb_message()
                            smsg.start_new_msg()
        #                    smsg.PARAM='3d050521' # Aussentemp
        #                    smsg.PARAM='3d0507b0' # Status Heizung
                            smsg.PARAM='3d0509b5'
                            smsg.TYP=0x06
        #                    smsg.setDataDirDateTime(datetime.datetime.today())
                            smsg.prepare_to_send()
                            print smsg
                            ser.write(smsg.getrawval())
        #                    mm = '2378fff4f9c2fafadef8ed'.decode('hex')
        #                    print mm
        #                    ser.write(mm)

finally:
    wiringpi.digitalWrite(25,0) #0V so sender is disabled ...
    wiringpi.pinMode(25,0) # Set Pin 25 to input
    
