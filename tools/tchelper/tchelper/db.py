# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

from __future__ import with_statement
import MySQLdb as mdb

from tchelper import utils


class DBClient():
    """Simple MySQL DB client.
    """

    def __init__(self, host='localhost', user='test', password='pass',
                 db='testdb'):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.conn = None

    def _connect(self):
        self.conn = mdb.connect(self.host, self.user, self.password, self.db)
        
    def _close(self):
        if self.conn:
            self.conn.close()
    
    def get_bandwidths(self, uuid=None, table='db_ipaddress'):
        if not self.conn:
            self._connect()
        if self.conn:
            cmd = "select ip, bandwidth from %s where ip_type='E'" % table
            if uuid:
                cmd += ' and uuid=%s' % uuid
            with self.conn:
                cur = self.conn.cursor(mdb.cursors.DictCursor)
                cur.execute(cmd)
                rows = cur.fetchall()
            if not rows:
                print "could not find rows"
            return rows
        print "lost db connection, please (re)try later"
        return None
