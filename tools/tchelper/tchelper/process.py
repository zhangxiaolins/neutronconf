# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

from __future__ import with_statement
import os
import os.path

from cghelper import fileops
from cghelper import utils


class Process(object):
    def __init__(self, pid):
        self.pid = pid

        items = fileops.read('/proc/%d/stat' % pid).split(' ')
        self.name = items[1].lstrip('(').rstrip(')')
        self.state = items[2]
        self.ppid = int(items[3])
        self.pgid = int(items[4])
        self.sid = int(items[5])
        if not self.is_kthread():
            self.name = self._get_fullname()
            cmdline = fileops.read('/proc/%d/cmdline' % self.pid)
            self.cmdline = cmdline.rstrip('\0').replace('\0', ' ')
        else:
            self.cmdline = self.name

        if os.path.exists('/proc/%d/autogroup' % pid):
            autogroup = fileops.read('/proc/%d/autogroup' % pid)
        else:
            autogroup = None
        if autogroup:
            # Ex. "/autogroup-324 nice 0"
            self.autogroup = autogroup.split(' ')[0].replace('/', '')
        else:
            # kthreads don't belong to any autogroup
            self.autogroup = None

    def _get_fullname(self):
        cmdline = fileops.read('/proc/%d/cmdline' % self.pid)
        if '\0' in cmdline:
            args = cmdline.rstrip('\0').split('\0')
            if ' ' in args[0]:
                name = args[0].split(' ')[0]
            else:
                name = args[0]
        else:
            #args = [cmdline,]
            args = cmdline.split(' ')
            name = args[0]
        if name[0] == '/':
            name = os.path.basename(name)
        name = name.rstrip(':')
        if len(args) >= 2:
            scripts = ['python', 'ruby', 'perl']
            # Want to catch /usr/bin/python1.7 ...
            if len([s for s in scripts if s in name]) > 0:
                name = os.path.basename(' '.join(args[0:2]))
        return name

    def is_kthread(self):
        return self.pgid == 0 and self.sid == 0

    def is_group_leader(self):
        return self.pid == self.pgid

    def is_session_leader(self):
        return self.pid == self.sid

    def is_running(self):
        return self.state == 'R'


def exists(pid, thread=True):
    if not thread:
        return os.path.exists("/proc/%d" % pid)
    else:
        ps = utils.run("ps -eL | awk '{if ($2 == %s) print $1;}'" % str(pid))
        ret = ps.wait()
        if ret == 0 and ps.stdout:
            return True
        return False
