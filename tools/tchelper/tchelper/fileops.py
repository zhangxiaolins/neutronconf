# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

from __future__ import with_statement
import os


def read(path):
    with open(path) as f:
        return f.read()


def readlines(path):
    with open(path) as f:
        return [c.rstrip('\n') for c in f.readlines()]


def write(path, cont):
    with open(path, 'w+') as f:
        return f.write(str(cont))


def append(path, cont):
    with open(path, 'a+') as f:
        value = str(cont) + "\n"
        return f.write(value)
        

def mkdir(path, mode=0777):
    os.mkdir(path, mode)


def rmdir(path):
    os.rmdir(path)


def mkdir_p(path):
    os.makedirs(path)


def exists(path):
    return os.path.exists(path)
