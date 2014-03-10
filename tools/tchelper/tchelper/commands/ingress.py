# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

import os
import re
import sys

from tchelper import command
from tchelper import tc
from tchelper import utils


class Command(command.Command):
    NAME = 'ingress'

    parser = command.Command.parser
    parser.add_option('--dst', action='store', type='string',
                      dest='dst', default='10.10.10.10',
                      help='Specify the dst ip of the shaping packets')
    parser.add_option('--rate', action='store', type='string',
                      dest='rate', default='1mbit',
                      help='Specify the rate for egress network traffic '
                      '[%default]')
    parser.add_option('--ceil', action='store', type='string',
                      dest='ceil', default='',
                      help='Specify the ceil for egress network traffic '
                      '[%default]')
    parser.add_option('--dev', action='store', type='string',
                      dest='dev', default='eth0',
                      help='Attached to which NIC to control traffic '
                      '[%default]')

    parser.usage = "%%prog %s [options]" % NAME

    def run(self, args):
        ok = False
        maxrate = '10gbit'
        dev = self.options.dev
        rate = self.options.rate
        ceil = self.options.ceil
        if not ceil:
            ceil = rate
        dst = self.options.dst

        # calling tc to shape the traffic
        tco = tc.get_tc()
        if not tco:
            if self.options.debug:
                print "System doesn't support tc, please install iproute first"
            return False

        # redirect all ingress to ifb
        ifb = 'ifb0'
        if dev == 'eth1':
            ifb = 'ifb1'
        # up interface
        cmd = 'ip link set dev %s up' % ifb
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            if self.options.debug:
                print "Up interface %s successfully." % ifb
        else:
            if self.options.debug:
                print "Up interface %s failed." % ifb

        # check qdisc
        qdiscs = tco.get_qdisc(dev)
        for qdisc in qdiscs:
            if re.match('^qdisc\s*ingress', qdisc):
                break
        else:
            tco.add_qdisc(dev, ingress=True)
        # check filter
        if not tco.get_filter(dev, parent="ffff:"):
                if self.options.debug:
                    print "filter need be created"
                if not tco.mirror_ingress(dev, ifb):
                    if self.options.debug:
                        print "create a new mirror filter failed"
        
        # trying to find root qdisc for nic
        qdiscs = tco.get_qdisc(ifb)
        for qdisc in qdiscs:
            if re.match('^qdisc\s*htb.*?root', qdisc):
                break
        else:
            # delete root qdisc
            # if not tco.del_qdisc(ifb, root=True):
            #    if self.options.debug:
            #        print "delete root qdisc failed"
            # create a root qdisc :1 with default flowid=1:
            if not tco.add_qdisc(ifb, root=True, defaultid=300):
                if self.options.debug:
                    print "add qdisc root failed"
                return ok
            # add top child class for root
            if not tco.add_class(ifb, parent='1:',
                                 classid="1:1", rate=maxrate):
                if self.options.debug:
                    print "add top child class for root failed"
                return ok

        # separate net:host from dst ip address
        segs = self.options.dst.split('.')
        if len(segs) != 4:
            if self.options.debug:
                print "Check dst: it is malformat"
            return ok
        seg_ints = []
        for seg in segs:
            try:
                seg_int = int(seg)
                if seg_int >= 0 and seg_int < 256:
                    seg_ints.append(seg_int)
            except exceptions.ValueError:
                if self.options.debug:
                    print "Check dst: it is malformat"
                return ok
        net = seg_ints[2]
        host = seg_ints[3]

        # check net class
        #if not tco.get_class(ifb, classid='1:%s' % net, parent='1:1'):
        #    if not tco.add_class(ifb, parent='1:1',
        #                         classid="1:%s" % net, rate=maxrate):
        #        if self.options.debug:
        #            print "add net class failed"
        #        return ok
        #    # add qdisc for net class
        #    if not tco.add_qdisc(ifb, parent="2:%s" %net ,
        #                         qdisc_id='%s:' % net):
        #        if self.options.debug:
        #            print "add qdisc for net class failed"
        #        return ok

        # check class
        # TODO(xiaolin): Remove assumption that all classes are under
        #                parent 1:1
        if not tco.get_class(ifb, parent="1:1",
                             classid="1:%s" % host):
            if self.options.debug:
                print "class need be created"
            # create a new class
            if not tco.add_class(ifb, parent="1:1",
                                 classid="1:%s" % host,
                                 rate=rate, ceil=ceil, leaf=True):
                if self.options.debug:
                    print "create a new class falied"
                return ok
        else:
            if self.options.debug:
                print "class need be updated"
            # update the class
            if not tco.set_class(ifb, parent="1:1",
                                 classid="1:%s" % (host),
                                 rate=rate, ceil=ceil):
                if self.options.debug:
                    print "update class failed"
                return ok

        # check filter
        if not tco.get_filter(ifb, classid="1:%s" % host):
            if self.options.debug:
                print "filter need be created"
            if not tco.add_filter(ifb, parent="1:", dst=dst):
                if self.options.debug:
                    print "create a new filter failed"
                return ok

        print ok
        return True
