# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

import subprocess

def run(cmd):
  print cmd
  proc = subprocess.Popen([cmd], shell=True, stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE)
  return proc
