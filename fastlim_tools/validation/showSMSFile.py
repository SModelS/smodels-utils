#!/usr/bin/env python

"""
.. module:: showSMSFile
   :synopsis: Facility to print to screen in a more readable format the content of a .sms file

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""


import sys,os
sys.path.append('../runTools')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
sys.path.append(os.path.join(home,'smodels-database'))
from fastlimOutput import compareFiles, fastlimParser
from smodels.tools.physicsUnits import GeV, fb, TeV
from gridFastlim import runFastlim
from gridSmodels import runSmodelS
from smodels.theory import slhaDecomposer, crossSection, theoryPrediction
from fastlimOutput import formatOutput
from smodels.tools import databaseBrowser
from gridFastlim import getSlhaFiles, prepareSLHA
from signalregions import SRs
from collections import OrderedDict


infile = sys.argv[1]
if not os.path.isfile(infile):
    print 'Error: file %s not found' %infile
    sys.exit()
    
ifile = open(infile,'r')
smsdict = eval(ifile.read().replace('\n',''))
ifile.close()
for key,val in smsdict['extra'].items():
    print key,'=',val
res = []
for expres in smsdict['ExptRes']:
    res.append([expres['AnalysisName'],expres['DataSet'],expres['tval'],expres['exptlimit']])
res = sorted(res)
for r in res:
    print r[0],r[1],'\n',r[2],r[3]
        