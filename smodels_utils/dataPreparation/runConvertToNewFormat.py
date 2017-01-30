#!/usr/bin/env python

"""
.. module:: convertToNewFormat
   :synopsis: Tries to create convertNew.py (allowing the new format) from convert.py

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""


import sys,os,glob



databasePath = '/home/lessa/smodels-database'

for f in glog.glob(databasePath+'/*/*/*/convert.py'):
    print f