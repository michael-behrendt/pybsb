#!/usr/bin/env python
# -*- coding: utf-8 -*-
# bsb_message -- parse and generate messages of the bsb bus system
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


#import glob
import crcmod.predefined
import struct
import csv
import time
import datetime
import pytz
import os
import logging


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

_hwadrtab = { }
    
_typtab   = { 0x00: 'Broadcast Update',
              0x02: 'Info / Status Update',
              0x03: 'Wert Setzen',
              0x04: 'Quitierung für Wert Setzen',
              0x06: 'Wert-Abfrage',
              0x07: 'Wert-Antwort',
              0x0f: 'Aufforderung Min/Max Reset',
              0x10: 'Quitierung für Min/Max Reset'}    
    
_paramtab   = { }

_datatabs = { }

_statustexte = { }

_datafuntab = { }

_paramstatus = { 0x00: 'Wert Aktiv',
                 0x01: 'Wert Inaktiv',
                 0x05: 'Wert setzen Inaktiv',
                 0x06: 'Wert setzen Aktiv'}
                 
_paramdir = { 0x00: 'Lesezugriff',
              0x01: 'Schreibzugriff'}
              
_paramonoff = { 0x00: 'Aus',
                0xff: 'Ein'}
              
_myhwaddr = 0x07 #Raumgeraet 2
                 
_set_src_high_bit8 = True
_ignore_src_high_bit8 = True


pstate = { 0: 'ok     ',
           1: 'unknown',
           2: 'error  ',
           3: 'crc_err',
           4: 'dec_err'}
           
mytz='Europe/Zurich'
log.debug('Initailize localtz timezone to %s',mytz)
localtz = pytz.timezone(mytz)

class Bsb_message(object):
    
    _msg_val = ''
    _valid = False
    _SOF = 0xff
    _SRC = 0xff
    _RCV = 0xff
    _LEN = 0xff
    _TYP = 0xff
    _PARAM = ''
    _DATA = ''
    _CRC = ''
    _GARBAGE = None
    
    _status = 0
    
    __headerwidth = 7    
    __datawidth = 45
    __descwidth = 25
    
    _exceptions = False
    
    _lastmod = None
  
    
    def __init__(self):
        self._xmodem_crc = crcmod.predefined.Crc('xmodem')
    
    def setrawval(self,val):
        bval = bytearray(val)
        for i in range(len(bval)):
           bval[i] = bval[i] ^ 0xff
        self._msg_val = str(bval)
        self._parse()
        if self._SOF != 0xdc:
            log.debug('Start frame not 0xdc, discarding input %s',self._msg_val.encode('hex'))
            return ''
        elif self._LEN != None and self._LEN >= 11 and len(self._msg_val) == self._LEN:
            return ''
        elif self._LEN != None and self._LEN >= 11 and len(self._msg_val) > self._LEN:
            log.debug('We have to many bytes of data')
            if self._msg_val[self._LEN] == chr(0xdc):
                log.debug('Start bit of next message ok, give back the overflowing bytes')
                ueberschuss = len(self._msg_val) - self._LEN
                self._msg_val = self._msg_val[0:self._LEN]
                return val[-1 * ueberschuss:]
            else:
                log.debug('Start bit of next message wrong, trying to search start of next message')
                self._GARBAGE = self._msg_val[self._LEN:]
                self._msg_val = self._msg_val[0:self._LEN]
                p = self._GARBAGE.find(chr(0xdc))
                if p >= 1:
                    log.debug('next start found, give back the bits')
                    self._GARBAGE = self._GARBAGE[:p]
                    return val[self._LEN+p:]
                log.debug('No start frame found, discard all bits')
                return ''
        else:
            return val
        
    
    def setval(self,val):
         self._msg_val = val
         self._parse()
         return self._valid == True 
         
    def getrawval(self):
        val = bytearray(self._msg_val)
        for i in range(len(val)):
           val[i] = val[i] ^ 0xff
        return str(val)
        
        
    def getval(self):
        return self._msg_val
     
    def getlogval(self):
        msg = ''
        try:
            msg += self._msg_val[0].encode('hex') + ' '
            msg += self._msg_val[1:3].encode('hex') + ' '
            msg += self._msg_val[3].encode('hex') + ' '
            msg += self._msg_val[4].encode('hex') + ' '
            msg += self._msg_val[5:9].encode('hex') + ' '
            msg += self._msg_val[9:self._LEN-2].encode('hex') + ' '
            msg += self._msg_val[self._LEN-2:].encode('hex')
        except IndexError:
            msg += ' ---> MSG DATA LEN ERROR ... \n'
        return msg

    def get_RCV(self):
        return self._TYP
    
    def set_RCV(self,val):
        if _hwadrtab.has_key(val):
            self._RCV = val
        else:
            raise ValueError('ERROR: Unknown Value in RCV')
        
    RCV = property(get_RCV,set_RCV)    
    
    
    def get_TYP(self):
        return self._TYP
    
    def set_TYP(self,val):
        if _typtab.has_key(val):
            self._TYP = val
        else:
            raise ValueError('ERROR: Unknown Value in TYP')
        
    TYP = property(get_TYP,set_TYP)

    def get_PARAM(self):
        return self._PARAM.encode('hex')
    
    def set_PARAM(self,val):
        binparam = val.decode('hex')
        if _paramtab.has_key(binparam):
            self._PARAM = binparam
        else:
            raise ValueError('ERROR: Unknown Value in PARAM')
        
    PARAM = property(get_PARAM,set_PARAM)

    def start_new_msg(self):
        self._SOF = 0xdc
        self._SRC = _myhwaddr | 0x80
        self._RCV = 0x00
        self._TYP = 0x06
        
    def prepare_to_send(self):
        self._LEN = 11 + len(self._DATA)
        self._CRC = ''
        self._set_msg_from_intern()
        mycrc = self._xmodem_crc.new(self._msg_val)
        self._CRC = mycrc.digest()
        self._set_msg_from_intern()
        return self.valid()
        
    def _set_msg_from_intern(self):
        self._msg_val = chr(self._SOF)+chr(self._SRC)+chr(self._RCV)+chr(self._LEN)+chr(self._TYP)+self._PARAM+self._DATA+self._CRC
        self._lastmod = time.time()
        
    def __str__(self):
        return  '{0}\n{1}\n{2}\n{3}\n{4}\n{5}\n{6}\n{7}\n{8}{9:=<120s}'.format(self._prt_SOF(),self._prt_SRC(),self._prt_RCV(),self._prt_LEN(),self._prt_TYP(),self._prt_param(),self._prt_data(),self._prt_CRC(),self._prt_garbage(),'') 
    
    def check_parse_status(self):
        # Status: 0 -> ok, 1 -> Unknown, 2 -> Error, 3 -> CRC not valid
        self._status = 0
        if not ( self._check_SOF() and self._check_CRC() and self._check_LEN() and self._check_garbage()):
            self._status = 2
        elif not ( self._check_SRC() and self._check_RCV() and self._check_TYP() and self._check_param() and self._check_data_fun()):
            self._status = 1
        elif not self.valid():
            self._status = 3
        elif not self._check_data_val():
            self._status = 4
        return self._status

        
    
    def _check_SOF(self):
        return self._SOF == 0xdc
        
    def _prt_SOF(self):
        if self._check_SOF():
            msg = '(OK)'
        else:
            msg = '(ERROR)'
        return '{0:{hw}} : {1:<#{dw}x}{2:{dcw}}'.format('SOF',self._SOF,msg,hw=self.__headerwidth,dw=self.__datawidth,dcw=self.__descwidth)


    def _check_CRC(self):
        mycrc = self._xmodem_crc.new(self._msg_val[:-2])
        return self._CRC == mycrc.digest()
        
    def _prt_CRC(self):
        if self._check_CRC():
            msg = '(OK)'
        else:
            mycrc = self._xmodem_crc.new(self._msg_val[:-2])
            msg = '(ERROR)   ==> correct CRC: %s' % hex(mycrc.crcValue)
        return '{0:{hw}} : {1:{dw}}{2:{dcw}}'.format('CRC','0x' + self._CRC.encode('hex'),msg,hw=self.__headerwidth,dw=self.__datawidth,dcw=self.__descwidth)
 
 
    def _check_LEN(self):
        return len(self._msg_val) == self._LEN
        
    def _prt_LEN(self):
        if self._check_LEN():
            msg = '(OK)      ==> %02d' % self._LEN
        else:
            msg = '(ERROR)   ==> correct LEN: %02d' % len(self._msg_val)
        return '{0:{hw}} : {1:<{dw}}{2:{dcw}}'.format('LEN',"{0:#04x}".format(self._LEN),msg,hw=self.__headerwidth,dw=self.__datawidth,dcw=self.__descwidth)
 
    
    def _check_SRC(self):
        if _ignore_src_high_bit8:
            mysrc = self._SRC & 0x7f
        else:
            mysrc = self._SRC
        return _hwadrtab.has_key(mysrc)
            
    def _prt_SRC(self):
        if _ignore_src_high_bit8:
            mysrc = self._SRC & 0x7f
        else:
            mysrc = self._SRC
        if _hwadrtab.has_key(mysrc):
            msg = '(OK)      ==> %03d %s' % (mysrc,_hwadrtab[mysrc])
        else:
            msg = '(UNKNOWN) ==> Value: {0:#03d} {0:#04x} {0:#05o} {0:#010b}'.format(self._SRC)
        return '{0:{hw}} : {1:<{dw}}{2:{dcw}}'.format('SRC',"{0:#04x}".format(self._SRC),msg,hw=self.__headerwidth,dw=self.__datawidth,dcw=self.__descwidth)
    
    
    
    
    def _check_RCV(self):
        return _hwadrtab.has_key(self._RCV)
    
    def _prt_RCV(self):
        if self._check_RCV():
            msg = '(OK)      ==> %03d %s' % (self._RCV, _hwadrtab[self._RCV])
        else:
            msg = '(UNKNOWN) ==> Value: {0:#03d} {0:#04x} {0:#05o} {0:#010b}'.format(self._RCV)
        return '{0:{hw}} : {1:<{dw}}{2:{dcw}}'.format('RCV',"{0:#04x}".format(self._RCV),msg,hw=self.__headerwidth,dw=self.__datawidth,dcw=self.__descwidth)
       
       
    def _check_TYP(self):
        return _typtab.has_key(self._TYP)
    
    def _prt_TYP(self):
        if _typtab.has_key(self._TYP):
            msg = '(OK)      ==> %03d %s' % (self._TYP, _typtab[self._TYP])
        else:
            msg = '(UNKNOWN) ==> Value: {0:#03d} {0:#04x} {0:#05o} {0:#010b}'.format(self._TYP)
        return '{0:{hw}} : {1:<{dw}}{2:{dcw}}'.format('TYP',"{0:#04x}".format(self._TYP),msg,hw=self.__headerwidth,dw=self.__datawidth,dcw=self.__descwidth)


    
    
    
    def _check_param(self):
        return _paramtab.has_key(self._PARAM)
        
    def _prt_param(self):
        if len(self._PARAM) == 4:
            if _paramtab.has_key(self._PARAM):
                msg = '(OK)      ==> %s' % _paramtab[self._PARAM]
            else:
                msg = '(UNKNOWN) ==> Value: {0[0]:#04x} {0[1]:#04x} {0[2]:#04x} {0[3]:#04x}'.format(bytearray(self._PARAM))
        else:
                msg = '(ERROR SIZE) ==> Value: 0x{0}'.format(self._PARAM.encode('hex'))
        return '{0:{hw}} : {1:<{dw}}{2:{dcw}}'.format('PARAM','0x'+ self._PARAM.encode('hex'),msg,hw=self.__headerwidth,dw=self.__datawidth,dcw=self.__descwidth)
    
    
    
 
    def _check_garbage(self):
        return self._GARBAGE == None
   
    def _prt_garbage(self):
        msg = '(OK)'
        if self._GARBAGE != None:
            msg = '(ERROR)   ==> Garbage Detected'
            return '{0:{hw}} : {1:<{dw}}{2:{dcw}}\n'.format('GARBAGE','0x'+ str(self._GARBAGE).encode('hex'),msg,hw=self.__headerwidth,dw=self.__datawidth,dcw=self.__descwidth)
        else:
            return ''
    

    def valid(self):
        mycrc = self._xmodem_crc.new(self._msg_val)
        if mycrc.crcValue == 0:
            self._valid = True
        else:
            self._valid = False
#        print self._xmodem_crc.hexdigest()
        return self._valid
        
    def lendif(self):
        if self._SOF != 0xdc:
            return -2
        if len(self._msg_val) < 11:
            return 11 - len(self._msg_val)
        else:
            try:
                myl = self._LEN - len(self._msg_val)
            except:
                myl = -1
            return myl
        
    def _parse(self):
#        print self._msg_val.encode('hex')
        try:
            bdata = bytearray(self._msg_val)
            self._SOF = bdata[0]
            self._SRC = bdata[1]
            self._RCV = bdata[2]
            self._LEN = bdata[3]
            if self._LEN > 33:
                self._LEN = 33
            if self._LEN < 11:
                self._LEN = 11
            self._TYP = bdata[4]
            self._PARAM = str(bdata[5:9])
            self._DATA = str(bdata[9:self._LEN-2])
            self._CRC  = str(bdata[self._LEN-2:self._LEN])
        except IndexError:
            self._valid = False
        else:
            self.valid()
        self._lastmod = time.time()
        return self._valid


#=============== Decode selectors  funktions.... ==============================
 

    def decode_data(self):
        if _datafuntab.has_key(self._PARAM) and hasattr(self,'_data_' + _datafuntab.get(self._PARAM)):
                msg = getattr(self, '_data_' + _datafuntab.get(self._PARAM))()
                msg['data'] = self._DATA.encode('hex')
                msg['timestamp'] = self._lastmod
                msg['paramname'] = _paramtab.get(self._PARAM,'Unbekannter Parameter')
                if 'value' not in msg:
                    msg['value'] = ''
        else:
                raise AssertionError('decode funktion for %s not defined' % self._PARAM.encode('hex'))
        return msg    
    
    

    def set_data(self,newval):
        if _datafuntab.has_key(self._PARAM) and hasattr(self,'_set_' + _datafuntab.get(self._PARAM)):
                getattr(self, '_set_' + _datafuntab.get(self._PARAM))(newval)
        else:
                raise AssertionError('set funktion for %s not defined' % self._PARAM.encode('hex'))
        return self.prepare_to_send()
    
    
    def _check_data_fun(self):
        if len(self._DATA) > 0:
            if _datafuntab.has_key(self._PARAM) and hasattr(self,'_print_' + _datafuntab.get(self._PARAM)):
                return True
            else:
                return False
        else:
            return True
 
           
    def _check_data_val(self):
        if len(self._DATA) > 0:
            if _datafuntab.has_key(self._PARAM) and hasattr(self,'_data_' + _datafuntab.get(self._PARAM)):
                try:
                    getattr(self, '_data_' + _datafuntab.get(self._PARAM))()
                except Exception:
                    return False
                else:
                    return True
            else:
                return False
        else:
            return True
              
    def _prt_data(self):
        if _datafuntab.has_key(self._PARAM) and hasattr(self,'_print_' + _datafuntab.get(self._PARAM)):
                msg = getattr(self, '_print_' + _datafuntab.get(self._PARAM),self._print_unknown)()
        else:
                msg = self._print_unknown()
        return '{0:{hw}} : {1:<{dw}}{2:{dcw}}'.format('DATA','0x'+ self._DATA.encode('hex'),msg,hw=self.__headerwidth,dw=self.__datawidth,dcw=self.__descwidth)


#
#=============  Data decode part =======================================
#
#Von hier an kommen alle data / decode / set funkionen
#_print_funktion 
#        -> Dekodiert die Daten in einen String
#        -> Keine Exceptions zu erwarten
#_data_funktion 
#        -> Dekodiert die Daten in ein Array, 
#        -> wirft exeption falls ein Fehler auftritt
#_set_funktion
#        -> Erwartet input parameter und setzt daraus eine gültigen Message inhalt
#
#




# __data_unknown not usefull, exception is trowed instead ...               
    
    def _print_unknown(self):
        if len(self._DATA):
            return '(UNKNOWN)'
        else:
            return '(OK)'
        
       
    def _set_unknown(self,data):
        self._DATA = data.decode('hex')






    def _data_status_fixwert(self):
        ret = { 'unit' : 'txt', 'unitdisplay': False }
        if len(self._DATA) == 2:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown state value.. 0x%s' % self._DATA[0].encode('hex'))
            try:
                ret['value'] = _datatabs.get(self._PARAM,_statustexte)[self._DATA[1:]]
            except KeyError:
                raise NotImplementedError('Unknown state fix value.. 0x%s' % self._DATA[1:].encode('hex'))
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_fixwert .. 0x%s' % self._DATA.encode('hex'))
        return ret
        
    def _print_status_fixwert(self):
        try:
            d = self._data_status_fixwert()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %s' % ( d['state'], d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_fixwert(self):
        raise NotImplementedError()









    def _data_status_onoff(self):
        ret = { 'unit' : 'txt', 'unitdisplay': False }
        if len(self._DATA) == 2:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown state fix value.. 0x%s' % self._DATA[0].encode('hex'))
            try:
                ret['value'] = _paramonoff[ord(self._DATA[1])]
            except KeyError:
                raise NotImplementedError('Unknown On/Off value.. 0x%s' % self._DATA[1].encode('hex'))
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_onoff .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_onoff(self): 
        try:
            d = self._data_status_onoff()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %s' % ( d['state'], d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_onoff(self):
        raise NotImplementedError()











    def _data_status_holiday(self):
        ret = { 'unit' : 'txt', 'unitdisplay': False }
        if len(self._DATA) == 9:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown Status value.. 0x%s' % self._DATA[0].encode('hex'))
            # self._DATA[1] ==> Unknown, nomaly ff
            if self._DATA[1] != 'ff'.decode('hex'):
                raise NotImplementedError('Unknown Datapart has changed .. 0x%s' % self._DATA[1].encode('hex'))
            # self._DATA[4:9] ==> Unknown, normaly ffffffff16
            if self._DATA[4:9] != 'ffffffff16'.decode('hex'):
                raise NotImplementedError('Unknown Datapart has changed .. 0x%s' % self._DATA[4:9].encode('hex'))
            ret['value'] = '%02i.%02i' % ( ord(self._DATA[3]), ord(self._DATA[2]) )
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_holiday .. 0x%s' % self._DATA.encode('hex'))
        return ret
            
    def _print_status_holiday(self): 
        try:
            d = self._data_status_holiday()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %s' % ( d['state'], d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_holiday(self):
        raise NotImplementedError()









    def _data_dir_datetime(self):
        ret = { 'unit' : 'datetime', 'unitdisplay': False }
        if len(self._DATA) == 9:
            # self._DATA[4] ==> Wochentag
            # self._DATA[8] ==> Zeitzone
            try:
                ret['state'] = _paramdir[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown Dir value.. 0x%s' % self._DATA[0].encode('hex'))
            b = bytearray(self._DATA)
            ret['value'] = str(localtz.localize(datetime.datetime(1900+b[1],b[2],b[3],b[5],b[6],b[7])))
            ret['dst'] = b[8]
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for dir_datetime .. 0x%s' % self._DATA.encode('hex'))
        return ret
        
        
    def _print_dir_datetime(self):
        try:
            d = self._data_dir_datetime()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %s DST: %d' % ( d['state'], d['value'], d['dst'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_dir_datetime(self,ts):
        if type(ts) in (str,unicode):
            if ts == 'now':
                ts = datetime.datetime.now()
            else:
                ts = datetime.datetime.strptime(ts, '%Y-%m-%d  %H:%M:%S')
        if type(ts) != datetime.datetime:
            raise TypeError('ERROR: Please submit object of type str or datetime not %s' % type(ts))
        else:
            ts = localtz.localize(ts)
        # Summertime ?
        if ts.dst().total_seconds() != 0:
            dst = 1
        else:
            dst = 0
        self.PARAM='0500006c' # Zeit
        self.TYP=0x00
        self.RCV=0x7f
        d = bytearray(9)
        d[0] = 0x01  # Wert setzen
        d[1] = ts.year - 1900
        d[2] = ts.month
        d[3] = ts.day
        d[4] = ts.isoweekday()
        d[5] = ts.hour
        d[6] = ts.minute
        d[7] = ts.second
        d[8] = dst
        self._DATA = str(d)










    def _data_dir_onoff(self):
        ret = { 'unit' : 'txt', 'unitdisplay': False }
        if len(self._DATA) == 2:
            try:
                ret['value'] = _paramonoff[ord(self._DATA[1])]
            except KeyError:
                raise NotImplementedError('Unknown On/Off value.. 0x%s' % self._DATA[1].encode('hex'))
            try:
                ret['dir'] = _paramdir[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown dir value.. 0x%s' % self._DATA[0].encode('hex'))
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_onoff .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_dir_onoff(self): 
        try:
            d = self._data_dir_onoff()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %s' % ( d['dir'], d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_dir_onoff(self):
        raise NotImplementedError()












    def _data_dir_fixwert(self):
        ret = { 'unit' : 'txt', 'unitdisplay': False }
        if len(self._DATA) == 2:
            try:
                ret['value'] = _datatabs.get(self._PARAM,_statustexte)[self._DATA[1]]
            except KeyError:
                raise NotImplementedError('Unknown Status value.. 0x%s' % self._DATA[1].encode('hex'))
            try:
                ret['dir'] = _paramdir[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown dir value.. 0x%s' % self._DATA[0].encode('hex'))
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for dir_fixwert .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_dir_fixwert(self): 
        try:
            d = self._data_dir_fixwert()
            if 'dir' in d:
                msg = '(OK)      ==> %s ==> %s' % ( d['dir'], d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_dir_fixwert(self):
        raise NotImplementedError()

        









    
    def _data_temp_64_00(self):
        ret = { 'unit' : '°C', 'unitdisplay': True}
        if len(self._DATA) == 3:
            if self._DATA[2] != '00'.decode('hex'):
                raise NotImplementedError('Unknown Datapart has changed .. 0x%s' % self._DATA[2].encode('hex'))
            ret['value'] = self._decode_sshort_64(self._DATA[0:2])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for temp_64_00 .. 0x%s' % self._DATA.encode('hex'))
        return ret
        
    def _print_temp_64_00(self):
        try:
            d = self._data_temp_64_00()
            if 'value' in d:
                msg = '(OK)      ==> %0.2f %s' % ( d['value'], d['unit'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg
 
    def _set_temp_64_00(self):
        raise NotImplementedError()
           





        


    def _data_status_temp64(self):
        ret = { 'unit' : '°C', 'unitdisplay': True}
        if len(self._DATA) == 3:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = self._decode_sshort_64(self._DATA[1:3])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_temp64 .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_temp64(self): 
        try:
            d = self._data_status_temp64()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %0.2f' % ( d['state'], d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_temp64(self):
        raise NotImplementedError()
        
        




    def _data_status_hourmin(self):
        ret = { 'unit' : 'time', 'unitdisplay': False}
        if len(self._DATA) == 3:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = '%02d:%02d' % (ord(self._DATA[1]),ord(self._DATA[2]))
            ret['hour'] = ord(self._DATA[1])
            ret['min'] = ord(self._DATA[2])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_temp64 .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_hourmin(self): 
        try:
            d = self._data_status_hourmin()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %s' % ( d['state'], d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_hourmin(self):
        raise NotImplementedError()
        
        








    def _data_status_runhours(self):
        ret = { 'unit' : 'h', 'unitdisplay': True}
        if len(self._DATA) == 5:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = self._decode_long(self._DATA[1:5])/3600.0
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_runhours .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_runhours(self): 
        try:
            d = self._data_status_runhours()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %0.2f %s' % ( d['state'], d['value'], d['unit'])
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_runhours(self):
        raise NotImplementedError()
        










    def _data_status_runhours2(self):
        ret = { 'unit' : 'h', 'unitdisplay': True}
        if len(self._DATA) == 2:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = ord(self._DATA[1])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_runminutes .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_runhours2(self): 
        try:
            d = self._data_status_runhours2()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %02i %s' % ( d['state'], d['value'], d['unit'])
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_runhours2(self):
        raise NotImplementedError()
        









    def _data_status_runminutes(self):
        ret = { 'unit' : 'min', 'unitdisplay': True}
        if len(self._DATA) == 2:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = ord(self._DATA[1])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_runminutes .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_runminutes(self): 
        try:
            d = self._data_status_runminutes()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %02i %s' % ( d['state'], d['value'], d['unit'])
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_runminutes(self):
        raise NotImplementedError()
        










    def _data_status_counter(self):
        ret = { 'unit' : 'counter', 'unitdisplay': False}
        if len(self._DATA) == 5:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = self._decode_long(self._DATA[1:5])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_counter .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_counter(self): 
        try:
            d = self._data_status_counter()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %4i' % ( d['state'], d['value'])
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_counter(self):
        raise NotImplementedError()











    def _data_status_counter2(self):
        ret = { 'unit' : 'counter', 'unitdisplay': False}
        if len(self._DATA) == 2:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = ord(self._DATA[1])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_counter2 .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_counter2(self): 
        try:
            d = self._data_status_counter2()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %2i' % ( d['state'], d['value'])
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_counter2(self):
        raise NotImplementedError()




        


    def _data_status_short(self):
        ret = { 'unit' : 'short int', 'unitdisplay': False }
        if len(self._DATA) == 3:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = self._decode_short(self._DATA[1:3])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_counter .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_short(self): 
        try:
            d = self._data_status_short()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %4i' % ( d['state'], d['value'])
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_short(self):
        raise NotImplementedError()






    def _data_status_sshort(self):
        ret = { 'unit' : 'short int', 'unitdisplay': False }
        if len(self._DATA) == 3:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = self._decode_sshort(self._DATA[1:3])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_counter .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_sshort(self): 
        try:
            d = self._data_status_sshort()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %4i' % ( d['state'], d['value'])
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_sshort(self):
        raise NotImplementedError()





    def _data_status_slope(self):
        ret = { 'unit' : 'steigung', 'unitdisplay': False}
        if len(self._DATA) == 3:
            try:
                ret['state'] = _paramstatus[ord(self._DATA[0])]
            except KeyError:
                raise NotImplementedError('Unknown status value.. 0x%s' % self._DATA[0].encode('hex'))
            ret['value'] = self._decode_sshort_50(self._DATA[1:3])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_slope .. 0x%s' % self._DATA.encode('hex'))
        return ret
     
    def _print_status_slope(self): 
        try:
            d = self._data_status_slope()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %0.2f' % ( d['state'], d['value'])
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_slope(self):
        raise NotImplementedError()










    def _data_zeit_prog(self):
        ret = { 'unit' : 'timewindows', 'unitdisplay': False}
        if len(self._DATA) == 12:
            t = tuple(bytearray(self._DATA))
            ret['t1'] = {}
            ret['t2'] = {}
            ret['t3'] = {}
            if t[0] != 152:         
                ret['t1']['from'] = '%02i:%02i' % t[0:2]
                ret['t1']['to'] = '%02i:%02i' % t[2:4]
            else:
                ret['t1']['from'] = ret['t1']['to'] = '--:--'
            if t[4] != 152: 
                ret['t2']['from'] = '%02i:%02i' % t[4:6]
                ret['t2']['to'] = '%02i:%02i' % t[6:8]
            else:
                ret['t2']['from'] = ret['t2']['to'] = '--:--'
            if t[8] != 152:
                ret['t3']['from'] = '%02i:%02i' % t[8:10]
                ret['t3']['to'] = '%02i:%02i' % t[10:12]
            else:
                ret['t3']['from'] = ret['t3']['to'] = '--:--'
            ret['value'] = '%s - %s / %s - %s / %s - %s' % (ret['t1']['from'], ret['t1']['to'], ret['t2']['from'], ret['t2']['to'], ret['t3']['from'], ret['t3']['to'])
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for zeit_prog .. 0x%s' % self._DATA.encode('hex'))
        return ret
        
    def _print_zeit_prog(self):
        try:
            d = self._data_zeit_prog()
            if 'value' in d:
                msg = '(OK)      ==> %s ' % ( d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_zeit_prog(self):
        raise NotImplementedError()













    def _data_status_tw(self):
        
        _myunknown = { 
                chr(0x00): { '0041'.decode('hex'): 'Normal',  '0051'.decode('hex'): 'Ferien HK1'},
                chr(0x01): { '0045'.decode('hex'): 'Normal',  '0051'.decode('hex'): 'Ferien HK1', '004d'.decode('hex'): 'Ladung Aktiv'},
                }

        ret = { 'unit' : 'txt', 'unitdisplay': False }
        if len(self._DATA) == 3:
            try:
                ret['state'] = _twstatus[self._DATA[0]]
            except KeyError:
                raise NotImplementedError('Unknown twstatus value.. 0x%s' % self._DATA[0].encode('hex'))
            try:
                ret['value'] = _myunknown[self._DATA[0]][self._DATA[1:3]]
            except KeyError:
                raise NotImplementedError('Unknown data value has changed.. 0x%s' % self._DATA.encode('hex'))
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_holiday .. 0x%s' % self._DATA.encode('hex'))
        return ret
            
    def _print_status_tw(self): 
        try:
            d = self._data_status_tw()
            if 'value' in d:
                msg = '(OK)      ==> %s ==> %s' % ( d['state'], d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_tw(self):
        raise NotImplementedError()
    










    def _data_status_hk(self):
        
        _mystate = { 
                chr(0x00): 'Aus',
                chr(0x01): 'Heizbetrieb Normal',
                chr(0x05): 'Heizbetrieb ECO',
                chr(0x45): 'Ferien HK1'
                }

        ret = { 'unit' : 'txt / timewindows', 'unitdisplay': False}
        if len(self._DATA) == 10:
            try:
                ret['progstate'] = _betriebsniveau[self._DATA[0]]
            except KeyError:
                raise NotImplementedError('Unknown progstate value.. 0x%s' % self._DATA[0].encode('hex'))
            try:
                ret['actstate'] = _reduzierstatus[self._DATA[1]]
            except KeyError:
                raise NotImplementedError('Unknown actstate value.. 0x%s' % self._DATA[1].encode('hex'))
            ret['timewindow'] = '%s - %s / %s - %s / %s - %s' % ( self._decode_time(self._DATA[2]),
                                                                   self._decode_time(self._DATA[3]),
                                                                   self._decode_time(self._DATA[4]),
                                                                   self._decode_time(self._DATA[5]),
                                                                   self._decode_time(self._DATA[6]),
                                                                   self._decode_time(self._DATA[7]) )   
            
            if ord(self._DATA[8]) != 0:
                raise NotImplementedError('Unknown data byte 8 has changed (0x00) !! .. 0x%s' % self._DATA[8].encode('hex'))                        
            try:
                ret['value'] = _mystate[self._DATA[9]]
            except KeyError:
                raise NotImplementedError('Unknown value at byte 9.. 0x%s' % self._DATA.encode('hex'))
        elif len(self._DATA) > 0:
            raise ValueError('Data to Long/Short for status_hk .. 0x%s' % self._DATA.encode('hex'))
        return ret
            
    def _print_status_hk(self): 
        try:
            d = self._data_status_hk()
            if 'value' in d:
                msg = '(OK)      ==> %s / %s / %s / %s' % ( d['progstate'], d['actstate'], d['timewindow'], d['value'] )
            else:
                msg = '(OK)'
        except Exception as e:
            msg = '(ERROR)   ==> %s' % e.message
        return msg

    def _set_status_hk(self):
        raise NotImplementedError()





#============ Data decode / unpack funktions ==================================



    def _decode_sshort_64(self,data):
        # Erwartet 2 bytes signed short in string verpackt ...
        return struct.unpack('!h',str(data[0:2]))[0]/64.0
        
    def _decode_sshort_50(self,data): 
        # Erwartet 2 bytes signed short in string verpackt ...
        return struct.unpack('!h',str(data[0:2]))[0]/50.0
        
    def _decode_short(self,data): 
        # Erwartet 2 bytes unsigned short in string verpackt ...
        return struct.unpack('!H',str(data[0:2]))[0]
        
    def _decode_sshort(self,data): 
        # Erwartet 2 bytes signed short in string verpackt ...
        return struct.unpack('!h',str(data[0:2]))[0]
    
    def _decode_long(self,data):
        # Erwartet 4 bytes unsigned long in string verpackt ...
        return struct.unpack('!L',str(data[0:4]))[0]
        
    def _decode_time(self,data):
        if ord(data[0]) == 0xff:
            return '--:--'
        h = ord(data[0]) * 10 / 60
        m = ord(data[0]) * 10 % 60
        return '%02i:%02i' % ( h,m )




#============= End of Bsb_message class, import & generate some static data ===


for i in range(16):
    _hwadrtab[(0x00 | (i*16))]='Segment {} Grundgerät, Regler'.format(i)
    _hwadrtab[(0x03 | (i*16))]='Segment {} Erw. Modul 1'.format(i)
    _hwadrtab[(0x04 | (i*16))]='Segment {} Erw. Modul 2'.format(i)
    _hwadrtab[(0x06 | (i*16))]='Segment {} Raumgerät 1'.format(i)
    _hwadrtab[(0x07 | (i*16))]='Segment {} Raumgerät 2'.format(i)
    _hwadrtab[(0x0A | (i*16))]='Segment {} Bediengerät 1'.format(i)
    _hwadrtab[(0x0B | (i*16))]='Segment {} Bediengerät 2'.format(i)
    _hwadrtab[(0x0F | (i*16))]='Segment {} Servicegerät'.format(i)

_hwadrtab[0x7f]='Broadcast Message'

__mypath = os.path.dirname(os.path.realpath(__file__))


#_paramtab   = { 0x053d07a3: 'Status Heizkreis 1',
#                0x0d3d0519: 'Diagnose Erzeuger / Kesseltemperatur'
#                    }
with open(__mypath + '/paramtab.txt') as paramtab:
    reader = csv.reader(paramtab,delimiter='\t')
    for row in reader:
        if len(row) == 2:
            addr1 = row[1]
            addr2 = row[1][2:4]+row[1][0:2]+row[1][4:8]
            _paramtab[addr1.decode('hex')] = row[0]
            _paramtab[addr2.decode('hex')] = row[0]
        if len(row) == 3:
            addr1 = row[1]
            addr2 = row[1][2:4]+row[1][0:2]+row[1][4:8]
            _paramtab[addr1.decode('hex')] = row[0]
            _paramtab[addr2.decode('hex')] = row[0]
            if len(row[2]):
                _datafuntab[addr1.decode('hex')] = row[2]
                _datafuntab[addr2.decode('hex')] = row[2]
                
                
for k,i in _datafuntab.iteritems():
    if not hasattr(Bsb_message,'_print_' + i):
        raise LookupError('Function data_%s for %s not defined !' % (i,k.encode('hex')))
    if not hasattr(Bsb_message,'_data_' + i):
        raise LookupError('Function decode_%s for %s not defined !' % (i,k.encode('hex')))
    

with open(__mypath + '/statustexte_de.csv') as statustab:
    reader = csv.reader(statustab,delimiter='\t')
    for row in reader:
        if len(row) >= 2:
            i = int(row[0])
            s = ''
            while i:
                s += chr(i & 255)
                i >>= 8
            if s == '':
                s = chr(0)
            _statustexte[s] = row[1]


_reduzierstatus = { chr(0): 'Frostschutz', chr(1): 'Reduziert', chr(2): 'Komfort'}

_betriebsniveau = { chr(0): 'Frostschutz', chr(1): 'Automatik', chr(2): 'Reduziert', chr(3): 'Komfort'}

_twstatus = { chr(0): 'Trinkwasserbetrieb Aus', chr(1): 'Trinkwasserbetrieb Ein' }

_offon = { chr(0): 'Aus', chr(1): 'Ein' }

_twladung = { chr(0): 'Absolut', chr(1): 'Gleitend', chr(2): 'Kein (parallel)', chr(3): 'Gleitend, absolut'}

_twlegio = { chr(0): 'Aus', chr(1): 'Periodisch', chr(2): 'Fixer Wochentag'}

_tag = { chr(1): 'Montag', chr(2): 'Dienstag', chr(3): 'Mittwoch', chr(4): 'Donnerstag', chr(5): 'Freitag', chr(6): 'Samstag', chr(7): 'Sonntag'}

_perio = {chr(1): 'Jeden Tag', chr(2): 'Jeden 2. Tag', chr(3): 'Jeden 3. Tag', chr(4): 'Jeden 4. Tag', chr(5): 'Jeden 5. Tag', chr(6): 'Jeden 6. Tag', chr(7): 'Jeden 7. Tag' }

_verdichterfolge = { chr(0): '1-2', chr(1): '2-1'}

_unknownstatus = { chr(0): 'Keine Funktion'}

_twpstatus = { chr(0): '24h/Tag', 
               chr(1): 'Alle Zeitprogramme Heiz-/Kühlkreise', 
               chr(2): 'Zeitprogramm 4', 
               chr(3): 'Niedertarif',
               chr(4): 'Zeitprogramm 4 oder Niedertarif'}

def assignfixw(param,fwtab):
    param2 = param[2:4]+param[0:2]+param[4:8]
    _datatabs[param.decode('hex')] = fwtab
    _datatabs[param2.decode('hex')] = fwtab


assignfixw('2d3d04c2',_reduzierstatus)
assignfixw('3d310571',_twstatus)
assignfixw('053d09a5',_unknownstatus)
assignfixw('053d09a6',_unknownstatus)
assignfixw('053d09a7',_unknownstatus)
assignfixw('053d0a81',_unknownstatus)
assignfixw('053d0a82',_unknownstatus)
assignfixw('053d0a83',_unknownstatus)
assignfixw('053d0a01',_unknownstatus)
assignfixw('053d09a8',_unknownstatus)
assignfixw('253d0722',_twpstatus)
assignfixw('3d2d0574',_betriebsniveau)
assignfixw('313d0721',_twladung)
assignfixw('313d0759',_twlegio)
assignfixw('313d075e',_tag)
assignfixw('313d0738',_perio)
assignfixw('313d08ab',_offon)
assignfixw('593d05c9',_verdichterfolge)
#if __name__ == "__main__":

