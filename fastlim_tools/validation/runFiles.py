#!/usr/bin/env python

"""
.. module:: runFiles
   :synopsis: Used to run fastlim for a list of SLHA files

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import sys,os
sys.path.append('../runTools')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
from gridFastlim import runFastlimFor

fastlimdir = os.path.join(os.getcwd(),'../fastlim-1.0/')

slhadir = './SLHA/strong_lt_TeV_focus'
#Runs Fastlim on slhaDir to generate the output as .sms files
result = runFastlimFor(slhadir,fastlimdir,expResID=None,txname=None)
