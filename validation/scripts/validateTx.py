#!/usr/bin/env python

import argparse, types
argparser = argparse.ArgumentParser(description="validates one pair of txname / axes")
argparser.add_argument ( '-T', '--txname', nargs='?', help='txname',
                type=types.StringType, default='T1' )
argparser.add_argument ( '-a', '--axes', nargs='?', help='axes description',
                type=types.StringType, default='2*Eq(mother,x)_Eq(lsp,y)' )
args=argparser.parse_args() 
print validatePlot(expRes,args.txname,args.axes,slhamain+"%s.tar" % args.txname )


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

## axes="2*Eq(mother,x)_Eq(lsp,y)"
slhamain = '../../../../../smodels-utils/slha/'
## txname="T6bbWW"

