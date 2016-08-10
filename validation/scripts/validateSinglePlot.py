#!/usr/bin/env python

import argparse, types
argparser = argparse.ArgumentParser(description="validates one pair of txname / axes")
argparser.add_argument ( '-T', '--txname', nargs='?', help='txname [T1]',
                type=types.StringType, default='T1' )
argparser.add_argument ( '-a', '--axes', nargs='?', 
                help='axes description [2*Eq(mother,x)_Eq(lsp,y)]',
                type=types.StringType, default='2*Eq(mother,x)_Eq(lsp,y)' )
argparser.add_argument ( '-k', '--kfactor', nargs='?', help='k factor [1.0]',
                type=types.FloatType, default=1.0 )
argparser.add_argument ( '-r', '--recycle', help='recycle py files',
								action='store_true')
args=argparser.parse_args()

import sys,os
home = os.path.expanduser("~")
home = "../../../../../"
database_home = "../../../../"

sys.path.insert(0,os.path.join(home,"smodels-utils/validation"))
sys.path.insert(0,os.path.join(home,"smodels-utils"))
sys.path.insert(0,os.path.join(home,"smodels/"))

from validation.plotProducer import validateTxName,validatePlot,validateExpRes, \
                                    getExpIdFromPath, getDatasetIdsFromPath
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
expRes = database.getExpResults(analysisIDs=[expIds],datasetIDs=dsIds )

## axes="2*Eq(mother,x)_Eq(lsp,y)"
slhamain = os.path.join(home,"smodels-utils/slha/")

for i in expRes:
    slha = slhamain+"%s.tar" % args.txname
    print validatePlot(i,args.txname,args.axes,slha, kfactor=args.kfactor, 
            recycle_data=args.recycle )
