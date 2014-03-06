#!/usr/bin/env python
# -*- coding: utf-8 -*-
# bsbdaemon -- daemon helper class for pybsb package
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


import daemon
import logging
import argparse
import sys
import signal
import errno
import os
import time
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
try:
    from setproctitle import setproctitle
except ImportError:
    log.error('unable to load setproctitle python module')
    def setproctitle(proctitle):
        log.error('unable to set proctitle to %s, module setproctitle not aviable' % proctitle)
try:
    # on gentoo the pidlock is owned by newer versions of lockfile
    import lockfile.pidlockfile as pidlockfile
except ImportError:
    # on raspi, pidlock is shiped with daemon
    import daemon.pidlockfile as pidlockfile



class BSBDaemon(object):

    def __init__(self,pidfile=None,argparser=argparse.ArgumentParser('BSB Daemon'),stdin=None,stdout=None,stderr=None,files_preserve=[]):
        self.daemon = daemon.DaemonContext()
        self.daemon.stdin = stdin
        self.daemon.stdout = stdout
        self.daemon.stderr = stderr
        self.daemon.files_preserve = files_preserve
        self.debug = 0
        self.running = False
        parser = argparser
        parser.add_argument('--nodetach', help='dont detach and startup ...',action='store_true')
        parser.add_argument('--pidfile', help='pidfile, specifiy the full path',default=None)
        parser.add_argument('mode',help='operation mode',choices=['start', 'status', 'stop','restart'],default='status',nargs='?')
        log.debug('Parsing command line args')
        self.args = parser.parse_args()
        # Pid file handling here ;-)
        if self.args.pidfile != None:
            pidfile=self.args.pidfile
        log.debug('Prepare Pidfile %s',pidfile)
        self.get_pidfile(pidfile)
        # Check for stale pif file and release if is so
        log.debug('Prepare Pidfile for usage')
        self.running = self.check_pidfile()



    def run(self,proctitle=None):
        if self.args.mode == 'status':
            sys.stderr.write('Analyze pidfile %s\n' % self.pidfile.path)
            if self.running == True:
                sys.stderr.write('Prozess running with pid %i\n' % self.pidfile.read_pid())
            else:
                sys.stderr.write('No running prozess found\n')
            return None
        elif self.args.mode == 'stop':
            if self.running == True:
                self._stop()
            else:
                sys.stderr.write('No prozess found to stop\n')
            return None
        elif self.args.mode == 'restart':
            if self.running == True:
                self._stop()
                time.sleep(1)
            if self._start():
                return self.daemon
            else:
                return None
        elif self.args.mode == 'start':
            if self._start():
                if proctitle:
                    setproctitle(proctitle)
                if self.args.nodetach:
                    return self.pidfile
                else:
                    return self.daemon
            else:
                return None
        
    def get_pidfile(self, pfname):
        if pfname is None:
            pfname = u'/var/run/%s.pid\n' % sys.argv[0]
        log.debug(u'Pidfile name evaluated to %s',pfname)
        if not isinstance(pfname, basestring):
            log.error(u"Not a filesystem path: %s",pfname)
            error = ValueError(u"Not a filesystem path: %s" % pfname)
            raise error
        if not os.path.isabs(pfname):
            log.error(u"Not an absolute path: %s",pfname)
            error = ValueError(u"Not an absolute path: %s" % pfname)
            raise error
        path = os.path.dirname(pfname)
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                log.error(u'Checking pidfile dir problem %s',e.message)
                raise e
        try:
            log.debug('Performing write test to %s',pfname)
            if os.path.isfile(pfname):
                # Write test without delete
                tf = open(pfname,'a')
                tf.close()
            else:
                # Write test with delete
                tf = open(pfname,'a')
                tf.close()
                os.remove(pfname)
        except (OSError,IOError) as e:
            log.error('Write test to pid file was unsucessfull: %s',e.message)
            raise e
        self.pidfile = pidlockfile.PIDLockFile(pfname)
        
    def check_pidfile(self):
        if self.pidfile.is_locked():
            log.debug('Pidfile is allready locked / existing')
            if self.pidfile.i_am_locking() == False:
                log.debug('It\'s not my pidfile')
                fpid = self.pidfile.read_pid()
                if fpid is not None:
                    try:
                        log.debug('sending signal DFL to prozess with pid %d',fpid)
                        os.kill(fpid, signal.SIG_DFL)
                        return True
                    except OSError as e:
                        if e.errno == errno.ESRCH:
                            # The specified PID does not exist
                            log.info('pid %d not in the system, breaking the pidfile lock' % fpid)
                            self.pidfile.break_lock()
                            return False
                    if fpid == 0:
                        # cant't be, so the content of the pidfile is corrupt
                        log.info('i can\'t be the pid 0, so break the pidfile lock')
                        self.pidfile.break_lock()
                        return False
                return False
            else:
                log.debug('Ohh, it\'s my pidfile ...')
                return True
        else:
            return False
        


    def _start(self):
        log.debug('Prepare to run the daemon')
        self.running = self.check_pidfile()
        if self.running == True:
            log.error('Prozess allready running with pid %d',self.pidfile.read_pid())
            return False
        else:
            self.daemon.pidfile = self.pidfile
            log.info('Ready to fork ;-)')
            return True



    def _stop(self):
        fpid = self.pidfile.read_pid()
        try:
            os.kill(fpid, signal.SIGTERM)
            log.info('Send kill to prozess with pid %d',fpid)
        except OSError as e:
            log.error('Failed to terminate %d: %s',(fpid,e))


