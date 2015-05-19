#!/usr/bin/env python

import sys,os
home = os.path.expanduser("~")
sys.path.insert(0,os.path.join(home,"smodels-utils/"))
sys.path.insert(0,os.path.join(home,"smodels/"))


from validation.plotProducer import validateExpRes, getExpIdFromPath, getDatasetIdsFromPath
from smodels.experiment.databaseObjects import Database
import logging
from smodels.theory.crossSection import logger as cl
from smodels.theory.slhaDecomposer import logger as dl
from smodels.experiment.txnameObject import logger as tl
cl.setLevel(level=logging.DEBUG) 
dl.setLevel(level=logging.DEBUG)
tl.setLevel(level=logging.INFO)


print "exp id=",getExpIdFromPath(),"datasetid=",getDatasetIdsFromPath()

database = Database(os.path.join(home,"smodels-database"))
#How to validate all plots for all Txnames in one ExpRes:
expRes = database.getExpResults(analysisIDs=[getExpIdFromPath()],datasetIDs=getDatasetIdsFromPath() )
slhamain = os.path.join(home,"smodels-utils/slha")
kfactorDict = { "TChiWZ": 1.2, "TChiWW": 1.2, "TChiChipmSlepL": 1.2, "TChiChipmSlepStau": 1.2, "TChiChipmStauStau": 1.2, \
                "TChiSlepSnu": 1.2, "TChiStauSnu": 1.2, "TChiWH": 1.2, "TChiWZoff": 1.2 }
## kfactorDict= {} 
for i in expRes:
    validateExpRes(i,slhamain, kfactorDict = kfactorDict )

