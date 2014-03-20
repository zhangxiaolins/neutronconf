# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

import os
import re
import sys

from tchelper import command
from tchelper import tc


class Command(command.Command):
    NAME = 'unset'

    parser = command.Command.parser
    parser.add_option('--src', action='store', type='string',
                      dest='src', default='10.10.10.10',
                      help='Specify the src ip of the shaping packets')
    parser.add_option('--rate', action='store', type='string',
                      dest='rate', default='1mbit',
                      help='Specify the rate for egress network traffic [%default]')
    parser.add_option('--dev', action='store', type='string',
                      dest='dev', default='eth0',
                      help='Attached to which NIC to control traffic [%default]')

    parser.usage = "%%prog %s [options]" % NAME

    def run(self, args):
        ok = False

        # calling tc to shape the traffic
        tco = tc.get_tc()
        if not tco:
            if self.options.debug:
                print "System doesn't support tc, please install iproute first"
            # ok = False
        else:
            # trying to find root qdisc for nic
            qdiscs = tco.get_qdisc(dev)
            htb_root = False
            for qdisc in qdiscs:
                if re.match('^qdisc\s*htb.*?root', qdisc):
                    htb_root = True
            if not htb_root:
                if self.options.debug:
                    print "no qdisc root found"
                return ok

            # separate net:host from src ip address
            segs = self.options.src.split('.')
            if len(segs) != 4:
                if self.options.debug:
                    print "Check src: it is malformat"
                return ok
            seg_ints = []
            for seg in segs:
                try:
                    seg_int = int(seg)
                    if seg_int >= 0 and seg_int < 256:
                        seg_ints.append(seg_int)
                except exceptions.ValueError:
                    if self.options.debug:
                        print "Check src: it is malformat"
                    return ok
            net = seg_ints[2]
            host = seg_ints[3]

            # delete filter
            if not tco.del_filter(dev, parent="%s:" % net, src=src):
                if self.options.debug:
                    print "delete filter failed"
                return ok
            # delete class
            if not tco.del_class(dev, parent="%s:" % net, 
                                 classid="%s:%s" % (net, host),
                                 rate=rate):
                if self.options.debug:
                    print "delete class failed"
                return ok
        print ok
        return True
