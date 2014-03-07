# Copyright (c) Xiaolin Zhang. ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

import exceptions
import re
from tchelper import utils


class TrafficControl:
    """Traffic Control class is a wrap to `tc` command.
       The main function of this class is, with cgroup, to shape network traffic
       of egress on each NIC/interfase. Put it more precisely, we achieve this   
       by using HTB (Hierarchical Token Bucket) to divide traffic link among 
       different service/process or by IP matching. HTB ensures that the amount
       of the traffic provided to each class is at least as the minimum of the 
       amount it requests. When a class requests less than the amount assigned, 
       the remaining (excess) bandwidth is distributed to other classes 
       proportionally.
       For more information please refer to HTB's homepage:
       http://luxik.cdi.cz/~devik/qos/htb/
    """
    
    def __init__(self):
        self.deps = self._check_deps()        
        
    def _check_deps(self):
        """TC depends on iproute2
           `dpkg --list | grep iproute`
           ii iproute 20120521-3ubuntu1 amd64 networking and traffic control tools

        """
        cmd = 'dpkg --list | grep iproute'
        p = '^ii\s+iproute'
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            lines = proc.stdout.readlines()
            for line in lines:
                if re.match(p, line):
                    return True
        return False
        
    def list_device(self):
        """Get a list of all nics on hosts
           `cat /proc/net/dev`
           Inter-|   Receive                                                |  Transmit
            face |   bytes packets errs drop fifo frame compressed multicast|  bytes packets errs drop fifo colls carrier compressed
             eth0:  124882     732    0    0    0     0          0         0   91831     634    0    0    0     0       0          0
               lo:   47629     523    0    0    0     0          0         0   47629     523    0    0    0     0       0          0
           virbr0:       0       0    0    0    0     0          0         0       0       0    0    0    0     0       0          0
           lxcbr0:       0       0    0    0    0     0          0         0    7495      34    0    0    0     0       0          0

        """
        proc = utils.run('cat /proc/net/dev')
        rc = proc.wait()
        devs = []
        if rc == 0:
            lines = proc.stdout.readlines()
            for line in lines:
                segments = line.split(':')
                if len(segments) > 1:
                    devs.append(segments[0].strip())
        return devs
        
    def check_device(self, dev):
        """Check if the device is valid.
        @param:
         dev: dev string, e.g. eth0
        @return:
         true: if dev is a valid,
         false: otherwise.
        """
        if dev in self.list_device():
            return True
        return False
       
    def get_qdisc(self, dev='eth0'):
        """Get qdisc for a nic/dev.
           `tc qdisc show dev eth0`
           qdisc htb 1: root refcnt 2 r2q 10 default 20 direct_packets_stat 2
           @param:
            dev: dev string, e.g. eth0
           @return:
            list of qdisc.
        """
        if not self.check_device(dev):
            return None
        cmd = 'tc qdisc show dev %s' % dev
        proc = utils.run(cmd)
        qdiscs = []
        if (proc.wait() == 0):
            lines = proc.stdout.readlines()
            for line in lines:
                qdiscs.append(line)
        if len(qdiscs) == 0:
            return None
        return qdiscs
    
    def get_class(self, dev='eth0', classid='', parent='', root=False):
        """Get all classes for a nic/dev.
           `tc class show dev eth0 [classid ID] [parent ID | root] `
           class htb 1:10 parent 1:1 prio 0 rate 500000bit ceil 500000bit burst 1600b cburst 1600b 
           class htb 1:1 root rate 1000Kbit ceil 1000Kbit burst 1600b cburst 1600b 
           class htb 1:20 parent 1:1 leaf 2: prio 0 rate 500000bit ceil 500000bit burst 1600b cburst 1600b 
           @param:
            dev    : dev string, e.g. eth0
            classid: match this classid
            parent : whose parent is
            root   : get root class
           @return:
            list of classes.
        """
        if not self.check_device(dev):
            return None
        cmd = 'tc class show dev %s' % dev
        if classid:
            cmd += ' classid %s' % classid
        if root:
            cmd += ' root'
        elif parent:
            cmd += ' parent %s' % parent
        proc = utils.run(cmd)
        classes = []
        if (proc.wait() == 0):
            lines = proc.stdout.readlines()
            for line in lines:
                classes.append(line)
        if len(classes) == 0:
            return None
        return classes
    
    def get_filter(self, dev='eth0', classid='', root=False, protocol='ip'):
        """Get all filters for a dev under a class id
           `tc filter dev eth0`
           @param:
            dev     : dev string, e.g. eth0
            classid : match classid
            root    : root filter
            protocol: ip only for now
           @return:
            list of filters
        """
        if not self.check_device(dev):
            return None
        cmd = 'tc filter show dev %s protocol %s' % (dev, protocol)
        if classid:
            cmd += ' classid %s' % classid
        elif root:
            cmd += ' root'
        proc = utils.run(cmd)
        filters = []
        if (proc.wait() == 0):
            lines = proc.stdout.readline()
            for line in lines:
                filters.append(line)
        if len(filters) == 0:
            return None
        return filters
    
    def add_qdisc(self, dev='eth0', parent='', root=False, qdisc_id='1:', 
                  disc='htb', defaultid=''):
        """Add a qdisc for a nic/dev
           `tc qdisc add dev eth0 root handle 10: htb default 10`
           `tc qdisc add dev eth0 parent 1:10 handle 10: sfq perturb 10`
           @param:
            dev      : device string, e.g. eth0
            root     : root qdisc
            parent   : parent
            major    : major number, handle name is `major:`
            disc     : discipline, default is htb
            defaultid: default classid if no filters matched
        """
        if not self.check_device(dev):
            return None
        cmd = 'tc qdisc add dev %s' % dev
        if root:
            cmd += ' root handle %s' % qdisc_id
        elif parent:
            cmd += ' parent %s handle %s' % (parent, qdisc_id)
        if disc == 'htb':
            cmd += ' %s' % disc
            if defaultid:
                cmd += ' default %s' % defaultid
        elif disc == 'sfq':
            cmd += ' %s perturb 10' % disc
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            return True
        return False
    
    def add_class(self, dev='eth0', parent='', classid='', disc='htb', 
                  rate='1mbit', leaf=False, ceil='10gbit'):
        """Add a classes for a nic/dev
           `tc class add dev eth0 parent 1:0 classid 1:1 htb rate 1mbit`
           @param:
            dev    : dev string
            parent : parent
            classid: major:minor
            disc   : discipline, htb
            rate   : rate request.
            leaf   : a leaf class?
           Notes:
            mbps = 1024 kbps = 1024 * 1024 bps => byte/s
            mbit = 1024 kbit => kilo bit/s.
            mb = 1024 kb = 1024 * 1024 b => byte
            mbit = 1024 kbit => kilo bit.
        """
        if not self.check_device(dev):
            return None
        cmd = 'tc class add dev %s' % dev
        if parent:
            cmd += ' parent %s' % parent
        cmd += ' classid %s %s rate %s ceil %s' % (classid, disc, rate, ceil)
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            if leaf:
                qdiscid = classid.split(':')[1] + ':'
                self.add_qdisc(dev, disc='sfq', parent=classid, qdisc_id=qdiscid)
            return True
        return False
        
    def _get_flowid(self, src=''):
        """Get flowid by src IP.
           @params:
            src: IP address of the source
        """
        segs = src.split('.')
        if len(segs) != 4:
            return None
        seg_ints = []
        for seg in segs:
            try:
                seg_int = int(seg)
                if seg_int >= 0 and seg_int < 256:
                    seg_ints.append(seg_int)
            except exceptions.ValueError:
                return None
        return '%s:%s' % (seg_ints[2], seg_ints[3])
        
    def add_filter(self, dev='eth0', parent='', protocol='ip', 
                   src='', cgroup=False, qdisc_id='10:', prio=10):
        """Add a filter for a qdisc, by matching src ip or cgroup
           (TODO: xiaolin): some works with flowid, others classid, rules?
           `tc filter add dev eth0 parent 1:0 protocol ip prio 10 u32 \
            match ip src 1.2.3.4 flowid 1:11`
           `tc filter add dev eth0 parent 10: protocol ip prio 10 handle 1: cgroup`
           @param:
            dev: dev string
            parent: under which classid
            protocol: ip only
            src: ip of the source
            cgroup: if this is cgroup filter
            qdisc_id: filter id for cgroup
            prio: priority
           @return:
            True: filter added successfully;
            False: otherwise.
        """
        if not self.check_device(dev):
            return None
        cmd = 'tc filter add dev %s' % dev
        if parent:
            cmd += ' parent %s' % parent
        if cgroup:
            cmd += ' protocol %s prio %s handle %s cgroup' % \
                   (protocol, prio, qdisc_id)
        else:
            flowid = self._get_flowid(src)
            classid = '%s%s' % (parent, flowid.split(':')[1])
            cmd += ' protocol %s prio %s u32 match ip src %s flowid %s' % \
                   (protocol, prio, src, classid)
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            return True
        return False
        
    def del_qdisc(self, dev='eth0', parent='', root=False, qdisc_id='10:', 
                  disc='htb', defaultid=''):
        """Del a qdisc for a nic/dev
           `tc qdisc del dev eth0 root handle 1: htb default 12`
           @param:
            dev      : device string, e.g. eth0
            root     : root qdisc
            parent   : parent
            major    : major number, handle name is `major:`
            disc     : discipline, default is htb
            defaultid: default classid if no filters matched
        """
        if not self.check_device(dev):
            return None
        cmd = 'tc qdisc del dev %s' % dev
        if root:
            cmd += ' root'
        elif parent:
            cmd += ' parent %s' % parent
        cmd += ' handle %s %s' % (qdisc_id, disc)
        if defaultid:
            cmd += ' default %s' % defaultid
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            return True
        return False
    
    def del_class(self, dev='eth0', parent='', classid='', disc='htb', 
                  rate='1mbit'):
        """Del a classes for a nic/dev
           `tc class del dev eth0 parent 1:0 classid 1:1 htb rate 1mbit`
           @param:
            dev    : dev string
            parent : parent
            classid: major:minor
            disc   : discipline, htb
            rate   : rate request.
           Notes:
            mbps = 1024 kbps = 1024 * 1024 bps => byte/s
            mbit = 1024 kbit => kilo bit/s.
            mb = 1024 kb = 1024 * 1024 b => byte
            mbit = 1024 kbit => kilo bit.
        """
        if not self.check_device(dev):
            return None
        cmd = 'tc class del dev %s' % dev
        if parent:
            cmd += ' parent %s' % parent
        cmd += ' classid %s %s rate %s' % (classid, disc, rate)
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            return True
        return False
    
    def del_filter(self, dev='eth0', parent='', protocol='ip', 
                   src='', cgroup=False, qdisc_id='10:', prio=10):
        """Del a filter for a qdisc, cgroup or ip src
           `tc filter del dev eth0 parent 1:0 protocol ip prio 10 u32 \
            match ip src 1.2.3.4 flowid 1:11`
           `tc filter del dev eth0 parent 10: protocol ip prio 10 handle 1: cgroup`
           @param:
            dev: dev string
            parent: under which classid
            protocol: ip only
            src: ip of the source
            cgroup: if this is cgroup filter
            qdisc_id: filter id for cgroup
            prio: priority
        """
        if not self.check_device(dev):
            return ''
        cmd = 'tc filter del dev %s' % dev
        if parent:
            cmd += ' parent %s' % parent
        if cgroup:
            cmd += ' protocol %s prio %s handle %s cgroup' % \
                   (protocol, prio, qdisc_id)
        else:
            flowid = _get_flowid(src)
            cmd += ' protocol %s prio %s u32 match ip src %s flowid %s' % \
                   (protocol, prio, src, flowid)
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            return True
        return False
        
    def set_qdisc(self, dev='eth0', parent='', root=False, qdisc_id='10:', 
                  disc='htb', defaultid=''):
        """Set a qdisc for a nic/dev
           `tc qdisc replace dev eth0 root handle 1: htb default 12`
           @param:
            dev      : device string, e.g. eth0
            root     : root qdisc
            parent   : parent
            major    : major number, handle name is `major:`
            disc     : discipline, default is htb
            defaultid: default classid if no filters matched
        """
        if not self.check_device(dev):
            return ''
        cmd = 'tc qdisc replace dev %s' % dev
        if root:
            cmd += ' root'
        elif parent:
            cmd += ' parent %s' % parent
        cmd += ' handle %s %s' % (qdisc_id, disc)
        if defaultid:
            cmd += ' default %s' % defaultid
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            return True
        return False
    
    def set_class(self, dev='eth0', parent='', classid='', disc='htb', 
                  rate='1mbit', ceil='10gbit'):
        """Set a classes for a nic/dev
           `tc class replace dev eth0 parent 1:0 classid 1:1 htb rate 1mbit`
           @param:
            dev    : dev string
            parent : parent
            classid: major:minor
            disc   : discipline, htb
            rate   : rate request.
           Notes:
            mbps = 1024 kbps = 1024 * 1024 bps => byte/s
            mbit = 1024 kbit => kilo bit/s.
            mb = 1024 kb = 1024 * 1024 b => byte
            mbit = 1024 kbit => kilo bit.
        """
        if not self.check_device(dev):
            return ''
        cmd = 'tc class replace dev %s' % dev
        if parent:
            cmd += ' parent %s' % parent
        cmd += ' classid %s %s rate %s ceil %s' % (classid, disc, rate, ceil)
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            return True
        return False
    
    def set_filter(self, dev='eth0', parent='', protocol='ip', 
                   src='', cgroup=False, qdisc_id='10:', prio=10):
        """Set a filter for a qdisc, cgroup or ip src
           `tc filter replace dev eth0 parent 1:0 protocol ip prio 10 u32 \
            match ip src 1.2.3.4 flowid 1:11`
           `tc filter replace dev eth0 parent 10: protocol ip prio 10 handle 1: cgroup`
           @param:
            dev: dev string
            parent: under which classid
            protocol: ip only
            qdisc_id: filter id
        """
        if not self.check_device(dev):
            return ''
        cmd = 'tc filter replace dev %s' % dev
        if parent:
            cmd += ' parent %s' % parent
        if cgroup:
            cmd += ' protocol %s prio %s handle %s cgroup' % \
                   (protocol, prio, qdisc_id)
        else:
            flowid = _get_flowid(src)
            classid = '%s%s' % (parent, flowid.split(':')[1])
            cmd += ' protocol %s prio %s u32 match ip src %s calssid %s' % \
                   (protocol, prio, src, classid)
        proc = utils.run(cmd)
        if (proc.wait() == 0):
            return True
        return False


def get_tc():
    """Get a tc handler."""
    tco = TrafficControl();
    if tco.deps:
        return tco
    return None

