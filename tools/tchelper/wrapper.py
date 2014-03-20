#!/usr/bin/env python2.7
# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

import sys

import tchelper.commands

COMMANDS = tchelper.commands.__all__

def usage():
    str = ''
    str += 'Usage: %s <cmd> [options] [args]\n' % sys.argv[0]
    str += '\t<cmd> := %s' % '|'.join(COMMANDS)
    return str

if len(sys.argv) <= 1:
    print(usage())
    sys.exit(1)

cmd = sys.argv[1]

if cmd not in COMMANDS:
    print(usage())
    sys.exit(1)

mod = __import__('tchelper.commands' + '.' + cmd, fromlist=[cmd,])

#
# Run subcommand
#
parser = mod.Command.parser
options, args = parser.parse_args()

if options.debug:
    print options

cmd = mod.Command(options)
cmd.run(args[1:])
