# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

import os
import re
import sys

from tchelper import command
from tchelper import tc


class Command(command.Command):
    NAME = 'stat'

    parser = command.Command.parser
    parser.add_option('--parent', action='store', type='string',
                      dest='parent', default='1:',
                      help='Specify the parent of tree-like hierarchy')
    parser.add_option('--dev', action='store', type='string',
                      dest='dev', default='eth0',
                      help='Attached to which NIC to control traffic [%default]')

    parser.usage = "%%prog %s [options]" % NAME

    def run(self, args):
        ok = False
        dev = self.options.dev
        parent = self.options.parent
        output = 'dev: %s\n' % dev
        
        # get tc handler
        tco = tc.get_tc()
        if not tco:
            if self.options.debug:
                print "System doesn't support tc, please install iproute first"
            # ok = False
        else:
            # trying to find qdisc for nic
            qdiscs = tco.get_qdisc(dev)
            if qdiscs:
                for qdisc in qdiscs:
                    output += "qdisc: %s" % qdisc
            
            # trying to find classes
            classes = tco.get_class(dev)
            if classes:
                for a_class in classes:
                    output += "class: %s" % a_class 

            # trying to find filters
            filters = tco.get_filter(dev)
            if filters:
                for a_filter in filters:
                    output += "filter: %s" % a_filter
                    
        print output
        return True
