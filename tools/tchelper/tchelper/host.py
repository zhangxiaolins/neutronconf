# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

from __future__ import with_statement
import multiprocessing
import os
import os.path
import re

import fileops

class CPUInfo():
    def get_online(self):
        return fileops.read("/sys/devices/system/cpu/online").strip()

    def get_total_usage(self):
        line = fileops.readlines('/proc/stat')[0]
        line = line[5:]  # get rid of 'cpu  '
        usages = [int(x) for x in line.split(' ')]
        return sum(usages) / multiprocessing.cpu_count()


class MemInfo(dict):
    def get_online(self):
        if not os.path.exists('/sys/devices/system/node/'):
            return '0'
        else:
            return fileops.read('/sys/devices/system/node/online').strip()

    _p = re.compile('^(?P<key>[\w\(\)]+):\s+(?P<val>\d+)')
    def _update(self):
        for line in fileops.readlines('/proc/meminfo'):
            m = self._p.search(line)
            if m:
                self[m.group('key')] = int(m.group('val')) * 1024

    def _calc(self):
        self['MemUsed'] = self['MemTotal'] - self['MemFree'] - self['Buffers'] - self['Cached']
        self['SwapUsed'] = self['SwapTotal'] - self['SwapFree'] - self['SwapCached']
        self['MemKernel'] = self['Slab'] + self['KernelStack'] + self['PageTables'] + self['VmallocUsed']

    def update(self):
        self._update()
        self._calc()
