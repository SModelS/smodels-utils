#!/usr/bin/env python

import sys,os
home = os.path.expanduser("~")
sys.path.insert(0,os.path.join(home,"smodels-utils/"))
sys.path.insert(0,os.path.join(home,"smodels/"))


from validation.plotProducer import validateExpRes, getExpIdFromPath
from smodels.experiment.databaseObjects import DataBase
import logging
from smodels.theory.crossSection import logger as cl
from smodels.theory.slhaDecomposer import logger as dl
from smodels.experiment.txnameObject import logger as tl
cl.setLevel(level=logging.DEBUG) 
dl.setLevel(level=logging.DEBUG)
tl.setLevel(level=logging.DEBUG)


print "exp id=",getExpIdFromPath()

database = DataBase(os.path.join(home,"smodels-database"))
#How to validate all plots for all Txnames in one ExpRes:
expRes = database.getExpResults(analysisIDs=[getExpIdFromPath()],datasetIDs=[None])
slhamain = os.path.join(home,"smodels-utils/slha")
# kfactorDict = { "TChiWZ": 1.25, "TChiWW": 1.25 }
kfactorDict= {} 
validateExpRes(expRes,slhamain, kfactorDict = kfactorDict )

