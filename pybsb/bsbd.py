#!/usr/bin/env python
# -*- coding: utf-8 -*-
# bsb -- messagehandler of the bsb bus system
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
__version__ = "0.0.2"
__maintainer__ = "Daniel Heule"
__email__ = "daniel.heule@gmail.com"
__status__ = "Development"

import serial
import os
import select
import time
import socket
import json
import logging
import logging.handlers


import pybsb
import pybsb.bsbdaemon

# Configure logging:
log = logging.getLogger('bsb')
log.setLevel(logging.DEBUG)

# Define my formaters ;-)
formater = logging.Formatter('%(asctime)s.%(msecs)03d %(name)s %(levelname)8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
bformat = logging.Formatter('%(asctime)s.%(msecs)03d %(message)s',datefmt='%Y-%m-%d %H:%M:%S')


blog = logging.getLogger('bsbbus')
blog.setLevel(logging.DEBUG)

# set console log handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# add formater to ch
ch.setFormatter(formater)


# set handler for application log files
alf = logging.handlers.WatchedFileHandler(pybsb.logpath + 'bsbd.log')
alf.setLevel(logging.DEBUG)
alf.setFormatter(formater)
# set handler for bsb log files
blf = logging.handlers.WatchedFileHandler(pybsb.logpath + 'bsb_bus_trace.log')
blf.setLevel(logging.INFO)
blf.setFormatter(bformat)
# set handler for bsb error only files
belf = logging.handlers.WatchedFileHandler(pybsb.logpath + 'bsb_bus_errors.log','a',None,True)
belf.setLevel(logging.ERROR)
belf.setFormatter(bformat)


# add ch + alf to log
log.addHandler(alf)

# setup handler for blog (bsb)
blog.addHandler(blf)
blog.addHandler(belf)

# log wiringpi2_fake log only to console
logging.getLogger('pybsb').setLevel(logging.DEBUG)
#enable the next line to get debug from all my libs
#logging.getLogger('pybsb').addHandler(ch)



import pybsb.bsb_message as bsb_message
import pybsb.bsb_cache as bsb_cache    
# Try to import wiringpi2 --> on pc to test is not aviable, so fake it ...
try:
    import wiringpi2 as wiringpi
except ImportError:
    import pybsb.wiringpi2_fake as wiringpi





def main():
    log.info('Startup BSBd')
    # Now set the pin 25 to up so we can send data ;-)
    def dropsock(s):
        # Remove a socket from all monitoring lists
        log.debug('Droping all data from client %s:%s' % peers.get(s,('Unknown',0)) )
        if s in outputs:
            outputs.remove(s)
        if s in inputs:
            inputs.remove(s)
        if s in readable:
            readable.remove(s)
        if s in writable:
            writable.remove(s)
        if s in exceptional:
            exceptional.remove(s)
        s.close()
        
        # Remove buffers for socket
        if s in instr:
            del instr[s]
        if s in outstr:
            del outstr[s]
        if s in injson:
            del injson[s]
        if s in reqparam:
            del reqparam[s]
        if s in peers:
            del peers[s]
        if s in toclose:
            del toclose[s]
        # If socket who is dead is in writeable or exeptional, kickit
        
    try:
        log.info('set gpio port 25 to output and high --> sender enable')
        wiringpi.wiringPiSetupGpio()
        wiringpi.pinMode(25,1) # Set Pin 25 to output
        wiringpi.digitalWrite(25,1) # 3.3V so sender is enabled ...
    
        if os.path.exists('/dev/ttyAMA0'):
          device='/dev/ttyAMA0'
        else:
          device='/dev/ttyUSB0'
          device='/dev/ttyS11'
        

        server_address = (pybsb.server_address, pybsb.port)
        
        
        #msgnr = 0
        lastread = 0
        lastclean = 0
    
        #time to min wait after last read on bus ( time wich takes to transmit 5 bytes)
        #don't set tis value to big or to smal !!!!
        waittime = 11.0 / 4800.0 * 5
        
        log.info('start bsb bustrace logging to %s' % pybsb.logpath + 'bsb_bus_trace.log')
        log.info('open serial port %s' % device)
        ser = serial.Serial(device, 4800, timeout=(24.0/4800.0),parity=serial.PARITY_ODD)
        log.debug('initalising bsb_cache for 600s')
        cache = bsb_cache.Bsb_cache(600)
        # Create a TCP/IP socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(0)
        # Bind the socket to the port          
        log.info('start listening on %s port %s' % server_address)
        server.bind(server_address)
        # Listen for incoming connections
        server.listen(5)
        # Initial input for select statement
        inputs = [ ser, server]
        outputs = [ ]
        val = ''
        # instr[s] = 'stringrecivedsofor if it doesn't contain 3 linefeed'
        instr = {}
        # injson[s] = 'json request objects, ready to feed to the bsb'
        injson = {}
        # reqparam[s] = 'Request Param per socket'
        reqparam = {}
        # outstr[s] = 'string representation ready to send back to tcp client'
        outstr = {}
        # peers[s] = 'Connected endpoint'
        peers = {}
        # toclose[s] --> connections which should be closed after next send if time is over ...
        toclose = {}
        while True:
            # Wait for at least one of the sockets to be ready for processing
            try:
                readable, writable, exceptional = select.select(inputs, outputs, inputs)
            except socket.error as e:
                log.warning('something is going wrong on select, %s' % e.strerror)
            # Handle inputs
            for s in readable:
                # Server Socket has a new connection
                if s is server:
                    try:
                        # A "readable" server socket is ready to accept a connection
                        connection, client_address = s.accept()
                        peers[connection] = client_address
                        toclose[connection] = time.time() + 5
                        log.info('new connection from %s:%s' % client_address)
                        connection.setblocking(0)
                    except socket.error as e:
                        log.warning('exception on new server connection: %s' % e.strerror)
                    inputs.append(connection)
                    # Give the connection a str for data we want to recive
                    instr[connection] = ""
                # Serial is ready to read    
                elif s is ser:
                    #log.debug('ready to read from serial')
                    val += s.read(32)
                    lastread = time.time()
                    while len(val) >= 11:
                        # create new bsb message
                        #log.debug('read more as 11 bytes from serial, create a new bsb_message')
                        msg = bsb_message.Bsb_message()
                        # feed the data to the message, data wich is to mutch is coming back
                        val = msg.setrawval(val)
                        if msg.lendif() > 0:
                            # message not complete, read more from bus
                            #log.debug('message not yet complete, continue to read data from serial')
                            break
                        # Now we have a complete bsb message, check the state of the message
                        #log.debug('new complete message read from BSB, start parsing')
                        mstate =  msg.check_parse_status()
                        if mstate == 0:
                            blog.info(bsb_message.pstate.get(mstate,'State?') + " " + msg.getlogval())
                        else:
                            blog.error(bsb_message.pstate.get(mstate,'State?') + " " + msg.getlogval())
                        # Feed the message to te cache  ...
                        cache.append(msg)
                        # Check fo new request we can eventualy answer ..
                        t = time.time()
                        for i in reqparam.keys():
                            j = reqparam[i]
                            if 'busdump' in j and j['busdump'] == True:
                                a = {}
                                try:
                                    a = msg.decode_data()
                                except Exception as e:
                                    a['error'] = e.message
                                a['msgdump'] = str(msg)
                                outstr[i] = json.dumps(a) + '\n\n'
                                if j['timeout'] < t:
                                    del reqparam[i]
                                log.debug('sending busdump to client %s:%s' % peers[i])
                                outputs.append(i)
                            else:
                                r = cache.get_in_time(j['PARAM'],j['time'])
                                if r != None:
                                    a = {}
                                    try:
                                        a = r.decode_data()
                                    except Exception as e:
                                        a['error'] = e.message
                                    outstr[i] = json.dumps(a) + '\n\n'
                                    del reqparam[i]
                                    log.debug('sending answer %s to client' % j['PARAM'])
                                    outputs.append(i)
                                else:
                                    if j['timeout'] < t:
                                        a = {}
                                        a['error'] = 'timeout, no answer from bus'
                                        outstr[i] = json.dumps(a) + '\n\n'
                                        del reqparam[i]
                                        outputs.append(i)
                # Client socket ready to read ...
                else:
                    #log.debug('ready to read from tcp client %s:%s' % peers[s])
                    try:
                        data = s.recv(1024)
                    except socket.error as e:
                        log.warn('problem while read data from client %s:%s %s' % ( peers[s] + (e.strerror, ) ) )
                    if data:
                        # A readable client socket has data
                        log.info('command from client %s:%s recieved: %s' % ( peers[s] + (data.strip(),)))
                        instr[s] += data
                        if '\n\n' in instr[s]:
                            try:
                                injson[s] = json.loads(instr[s])
                                # put ser to outputs, so its clear that we have something to send to bsb....
                                outputs.append(ser)
                            except ValueError as e:
                                log.warning('json decoding failed: %s' % e.message)
                                a = {}
                                a['error'] = 'json decoding failed: %s' % e.message
                                outstr[s] = json.dumps(a) + '\n\n'
                                instr[s] = ''
                                outputs.append(s)
                    else:
                        # Interpret empty result as closed connection
                        log.warning('closing connection to client %s:%s after reading no data' % peers[s])
                        # Stop listening for input on the connection
                        dropsock(s)

            # Handle outputs
            for s in writable:
                #serial is ready to send (or we should send something)
                if s is ser:
                    #log.debug('ready to send to serial')
                    # check if some time is gone since the last read on the bus ... 
                    if ( lastread + waittime > time.time() ):
                        # if the time is to short, wait 1 char len and go to select loop
                        log.debug('time since last read was to short, retry later')
                        time.sleep(11.0 / 4800.0)
                        continue
                    try:
                        #handle first message
                        i = injson.keys().pop()
                        j = injson[i]
                        if 'loglevel' in j:
                            ll = j['loglevel'].upper()
                            log.setLevel(ll)
                            log.critical('New global loglevel set to %s' % ll)
                            a = {}
                            a['newloglevel'] = ll
                            outstr[i] = json.dumps(a) + '\n\n'
                            del injson[i]
                            outputs.append(i)
                        else:
                            reqparam[i] = {}
                            reqparam[i]['PARAM'] = j['PARAM']
                            if 'TYP' in j:
                                reqparam[i]['TYP'] = j['TYP']
                            else:
                                reqparam[i]['TYP'] = 0x06
                            t = time.time()
                            if 'cached' in j:
                                reqparam[i]['time'] = t - j['cached']
                            else:
                                reqparam[i]['time'] = t
                            if 'timeout' in j:
                                reqparam[i]['timeout'] = t + j['timeout']
                                toclose[i] = t + j['timeout'] + 5
                            else:
                                reqparam[i]['timeout'] = t + 1.5
                            r = cache.get_in_time(reqparam[i]['PARAM'],reqparam[i]['time'])
                            if r != None:
                                log.info('BSB-Message found in the cache, send it back')
                                # a = answer dict
                                a = {}
                                try:
                                    a = r.decode_data()
                                except Exception as e:
                                    a['error'] = e.message
                                outstr[i] = json.dumps(a) + '\n\n'
                                del reqparam[i]
                                del injson[i]
                                outputs.append(i)
                            elif 'onlycache' in j and j['onlycache'] == True:
                                log.warning('Only Cached results, but no Answer in the cache')
                                a = {}
                                a['error'] = 'onlycache set, but no answer in the cache'
                                outstr[i] = json.dumps(a) + '\n\n'
                                del reqparam[i]
                                del injson[i]
                                outputs.append(i)
                            elif 'nosend' in j and j['nosend'] == True:
                                log.warning('nosend set, only passiv waiting for the message from BSB-bus')
                                if 'busdump' in j and j['busdump'] == True:
                                    log.info('busdump requested')
                                    reqparam[i]['busdump'] = True
                                del injson[i]
                            else:
                                log.info('No answer in the cache, send the request to the BSB-bus')
                                smsg = bsb_message.Bsb_message()
                                smsg.start_new_msg()
                                smsg.PARAM=j['PARAM'][2:4]+j['PARAM'][0:2]+j['PARAM'][4:]
                                if 'TYP' in j:
                                    smsg.TYP = j['TYP']
                                if 'set' in j and j['set'] == True:
                                    smsg.set_data(j['newval'])
                                smsg.prepare_to_send()
                                mymsg = smsg.getrawval()
                                if(ser.inWaiting() == 0):
                                    ser.write(mymsg)
                                    l = len(mymsg)
                                    msgchk = ser.read(l)
                                    while len(msgchk) < l:
                                        msgchk += ser.read(1)
                                    lastread = time.time()
                                    if mymsg == msgchk:
                                        #msg send ok
                                        del injson[i]
                                        log.debug('message send sucessfully to the bus')
                                    else:
                                        log.error('send to the bus failed, collision detected, i try again later')
                                    # Since i have read my send message allready from bus, we must log it ;-)
                                    smsg.setrawval(msgchk)
                                    mstate =  smsg.check_parse_status()
                                    blog.info(bsb_message.pstate.get(mstate,'State?') + " " + smsg.getlogval())
                                    #print smsg
                                else:
                                    log.debug('data ready to read: %i bytes, sending msg later' % ser.inWaiting())
                    except ( KeyError, ValueError, IndexError ) as e:
                        a = {}
                        a['error'] = 'not all required keys submited: %s' % e.message
                        outstr[i] = json.dumps(a) + '\n\n'
                        if i in reqparam:
                            del reqparam[i]
                        if i in injson:
                            del injson[i]
                        outputs.append(i)
                        # Nicht alle oder ungültige keys sind angekommen
                    finally:
                        # if no more to send, drop serial from sender list ...
                        if len(injson) == 0 and s in outputs:
                             outputs.remove(s)
                else:
                    try:
                        msg = outstr[s]
                    except KeyError:
                        # No messages waiting so stop checking for writability.
                        log.warning('output for %s:%s is empty', peers[s])
                    else:
                        log.info('sending "%s" to %s:%s' % ((msg.strip(),) + peers[s]))
                        try:
                            s.send(msg)
                        except ( socket.error, socket.timeout ) as e:
                            log.warning('problem sending to socket: %s' % e.strerror)
                    finally:
                        if s in outputs:
                            outputs.remove(s)
                        instr[s] = ''
                        

            # Handle "exceptional conditions"
            for s in exceptional:
                log.warning('handling exceptional condition for: %s:%s' % peers[s])
                # Stop listening for input on the connection
                dropsock(s)
            
            # Handle sockets for witch is time to close ...
            if lastclean + 30 < time.time():
                lastclean = time.time()
                for s in toclose.keys():
                    if toclose[s] < lastclean:
                        log.debug('dropping connection to %s:%s, timeout reached' % peers[s])
                        dropsock(s)
    
    finally:
        log.info('set gpio port 25 low and to input --> sender disable')
        wiringpi.digitalWrite(25,0) #0V so sender is disabled ...
        wiringpi.pinMode(25,0) # Set Pin 25 to input
        



if __name__=="__main__":
    daemon = pybsb.bsbdaemon.BSBDaemon(pidfile='/var/run/bsbd/bsbd.pid',files_preserve=[alf.stream,blf.stream,belf.stream])
    if daemon.args.nodetach:
       log.addHandler(ch) 
    d = daemon.run(proctitle='bsbd')
    if d is not None:
        with d:
            main()
