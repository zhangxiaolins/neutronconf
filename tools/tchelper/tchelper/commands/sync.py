# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

from netaddr import IPNetwork, IPAddress
import os
import re
import sys

from tchelper import command
from tchelper import db
from tchelper import tc
from tchelper.timeout import timeout


class Command(command.Command):
    NAME = 'sync'

    parser = command.Command.parser
    parser.add_option('--host', action='store', type='string',
                      dest='host', default='192.168.1.108',
                      help='Specify the host ip of MySQL DB')
    parser.add_option('--user', action='store', type='string',
                      dest='user', default='cloud',
                      help='Specify the user of the MySQL DB')
    parser.add_option('--password', action='store', type='string',
                      dest='password', default='56d7c46f',
                      help='Specify the password of the MySQL DB')
    parser.add_option('--db', action='store', type='string',
                      dest='db', default='cassiopeia',
                      help='Specify the db of the MySQL DB')
    parser.add_option('--dev', action='store', type='string',
                      dest='dev', default='eth0',
                      help='Attached to which NIC to control traffic [%default]')
    parser.add_option('--cidr', action='store', type='string',
                      dest='cidr', default='223.202.61.0/26',
                      help='Specify the network cidr')

    parser.usage = "%%prog %s [options]" % NAME

    @timeout(300)
    def run(self, args):
        pairs = self._get_data()
        network = self.options.cidr
        for pair in pairs:
            src, rate = pair['ip'], str(pair['bandwidth'])
            rate += "mbit"
            if IPAddress(src) in IPNetwork(network):
                self._setup_one(self.options.dev, rate, rate, src)

    def _get_data(self):
        client = db.DBClient(self.options.host,
                             self.options.user,
                             self.options.password,
                             self.options.db)
        pairs = client.get_bandwidths()
        return pairs

    def _setup_one(self, dev, rate, ceil, src):
        ok = False
        maxrate = '10gbit'
        
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
                # delete root qdisc
                #if not tco.del_qdisc(dev, root=True):
                #    if self.options.debug:
                #        print "delete root qdisc failed"
                # create a root qdisc :1 with default flowid=1:
                if not tco.add_qdisc(dev, root=True, defaultid=300):
                    if self.options.debug:
                        print "add qdisc root failed"
                    return ok
                # add top child class for root
                if not tco.add_class(dev, parent='1:', 
                                     classid="1:1", rate=maxrate):
                    if self.options.debug:
                        print "add top child class for root failed"
                    return ok

            # separate net:host from src ip address
            segs = src.split('.')
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
            
            # check net class
            #if not tco.get_class(dev, classid='1:%s' % net, parent='1:1'):
            #    if not tco.add_class(dev, parent='1:1', 
            #                         classid="1:%s" % net, rate=maxrate):
            #        if self.options.debug:
            #            print "add net class failed"
            #        return ok
            #    # add qdisc for net class
            #    if not tco.add_qdisc(dev, parent="1:%s" %net , 
            #                         qdisc_id='%s:' % net):
            #        if self.options.debug:
            #            print "add qdisc for net class failed"
            #        return ok

            # check class
            if not tco.get_class(dev, parent="1:1", 
                                 classid="1:%s" % host):
                if self.options.debug:
                    print "class need be created"
                # create a new class
                if not tco.add_class(dev, parent="1:1", 
                                     classid="1:%s" % host,
                                     rate=rate, ceil=ceil, leaf=True):
                    if self.options.debug:
                        print "create a new class falied"
                    return ok
            else:
                if self.options.debug:
                    print "class need be updated"
                # update the class
                if not tco.set_class(dev, parent="%s:" % net, 
                                     classid="%s:%s" % (net, host),
                                     rate=rate, ceil=ceil):
                    if self.options.debug:
                        print "update class failed"
                    return ok
                
            # check filter
            if not tco.get_filter(dev, classid="1:%s" % host):
                if self.options.debug:
                    print "filter need be created"
                if not tco.add_filter(dev, parent="1:", src=src):
                    if self.options.debug:
                        print "create a new filter failed"
                    return ok
                    
        print ok
        return True
