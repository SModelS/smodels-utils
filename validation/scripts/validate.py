#!/usr/bin/env python

import argparse, types
argparser = argparse.ArgumentParser(description="validate all results for this analysis")
argparser.add_argument ( '-r', '--recycle', help='recycle py files',
								action='store_true')
args=argparser.parse_args()

import sys,os
home = os.path.expanduser("~")
home = "../../../../../"
database_home = "../../../../"

sys.path.insert(0,os.path.join(home,"smodels-utils/"))
sys.path.insert(0,os.path.join(home,"smodels/"))

from validation.plotProducer import validateExpRes, getExpIdFromPath, \
                                    getDatasetIdsFromPath
from smodels.experiment.databaseObj import Database
import logging
from smodels.theory.crossSection import logger as cl
from smodels.theory.slhaDecomposer import logger as dl
from smodels.experiment.txnameObj import logger as tl
cl.setLevel(level=logging.WARNING)
dl.setLevel(level=logging.WARNING)
tl.setLevel(level=logging.INFO)

database = Database( database_home )

expIds = getExpIdFromPath()
print "Experimental Id:",expIds
dsIds = datasetIDs=getDatasetIdsFromPath()
print "Dataset Ids:",", ".join ( map ( str, dsIds[:3] ) ),
if len(dsIds)>3:
    print ", ...",
print

#How to validate all plots for all Txnames in one ExpRes:
expRes = database.getExpResults ( analysisIDs=[ expIds ],datasetIDs= dsIds )

if expRes == []:
    print "[validate.py] Error: could not find any experimental results."
    f=open("../globalInfo.txt")
    lines=f.readlines()
    f.close()
    for line in lines:
        if line[:3]=="id:":
            Id=line[4:]
            Id=Id.replace("\n","")
            if Id != getExpIdFromPath():
                print "[validate.py] Error: path directory ``%s'' does not match exp id ``%s'' in ../globalInfo.txt" % ( getExpIdFromPath(), Id  )
                sys.exit()

slhamain = os.path.join(home,"smodels-utils/slha")
kfactorDict = { "TChiWZ": 1.2, "TChiWW": 1.2, "TChiChipmSlepL": 1.2,
                "TChiChipmSlepStau": 1.2, "TChiChipmStauStau": 1.2,
                "TChiSlepSnu": 1.2, "TChiStauSnu": 1.2, "TChiWH": 1.2,
                "TChiWZoff": 1.2 }
#kfactorDict= {}
for i in expRes:
    validateExpRes(i,slhamain, kfactorDict = kfactorDict, recycle_data=args.recycle )
