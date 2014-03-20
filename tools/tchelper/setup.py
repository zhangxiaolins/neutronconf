#!/usr/bin/python
# Copyright (c) Xiaolin Zhang ALL RIGHTS RESERVED.
# Author: zhangxiaolins@gmail.com

from setuptools import setup, Extension
from tchelper.version import VERSION

setup(name='tc-helper',
      version=VERSION,
      description='Utility helpers for traffic control of Linux',
      scripts=['bin/tchelper'],
      packages=['tchelper', 'tchelper.commands'],
      ext_package='tchelper',
      author='Xiaolin Zhang',
      author_email='zhangxiaolins@gmail.com',
     )
