#!/usr/bin/env python

import sys,os
sys.path.insert(0,"/home/walten/git/smodels-utils/validation/")
sys.path.insert(0,"/home/walten/git/smodels-utils/")
sys.path.insert(0,"/home/walten/git/smodels/")

from validation.plotProducer import validateTxName,validatePlot,validateExpRes, getExpIdFromPath
from smodels.experiment.databaseObjects import DataBase
import logging
from smodels.theory.crossSection import logger as cl
from smodels.theory.slhaDecomposer import logger as dl
from smodels.experiment.txnameObject import logger as tl
cl.setLevel(level=logging.DEBUG) 
dl.setLevel(level=logging.DEBUG)
tl.setLevel(level=logging.DEBUG)

database = DataBase("../../../../")

#How to validate all plots for all Txnames in one ExpRes:
expRes = database.getExpResults(analysisIDs=[getExpIdFromPath()],datasetIDs=[None])

## axes="2*Eq(mother,x)_Eq(inter0,106.0)_Eq(lsp,y)"
axes="2*Eq(mother,x)_Eq(inter0,2.0*y)_Eq(lsp,y)"
slhamain = '../../../../../smodels-utils/slha/'
## txname="T6bbWW"

if len (sys.argv)<2:
    print "please supply txname"
    sys.exit()
    
txname=sys.argv[1]
print validatePlot(expRes,txname,axes,slhamain+"%s.tar" % txname )

