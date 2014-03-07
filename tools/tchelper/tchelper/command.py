# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

import optparse

from tchelper.version import VERSION


class Command():
    NAME = 'tchelper'
    parser = optparse.OptionParser(version="%s %s" % (NAME, VERSION))
    parser.add_option('--debug', action='store_true', dest='debug',
                      default=False, help='Show debug messages')
    parser.usage = "%%prog %s [options]" % NAME

    def __init__(self, options):
        self.options = options
