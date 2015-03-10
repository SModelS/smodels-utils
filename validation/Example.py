#!/usr/bin/env python

import sys,os



from plotProducer import validateTxName,validatePlot,validateExpRes
from smodels.experiment.databaseBrowser import Browser
from smodels.experiment.databaseObjects import DataBase
import logging
from smodels.theory.crossSection import logger as cl
from smodels.theory.slhaDecomposer import logger as dl
from smodels.experiment.txnameObject import logger as tl
cl.setLevel(level=logging.WARNING) 
dl.setLevel(level=logging.WARNING)
tl.setLevel(level=logging.WARNING)

database = DataBase("/home/lessa/smodels-database/")
expResList = database.getExpResults(txnames=['TChiWZ'],datasetIDs=[None])
slhadir = '/home/lessa/smodels-utils/slha/TChiWZ.tar'
kfactor = 1.25
validateTxName(expResList,'TChiWZ',slhadir,kfactor)

# # 
# # 
# #How to validate one single plot for a UL analysis:
# expRes = database.getExpResults(analysisIDs=['CMS-SUS-13-004'],
#                                 datasetIDs=[None],txnames=['T2tt'])
# slhadir = '/home/lessa/smodels-utils/slha/T2tt.tar'
# txnameStr = 'T2tt'
# axes = '2*Eq(mother,x)_Eq(lsp,y)'
# validatePlot(expRes,txnameStr,axes,slhadir)

# #How to validate one single plot for a efficiency map analysis:
# expRes = database.getExpResults(analysisIDs=['ATLAS-CONF-2013-024'],
#                                 datasetIDs=['ANA1-CUT0','ANA1-CUT1','ANA1-CUT2',
#                                             'ANA2-CUT0','ANA2-CUT1','ANA2-CUT2',
#                                             'ANA3-CUT0','ANA3-CUT1','ANA3-CUT2',
#                                             'ANA4-CUT0','ANA4-CUT1','ANA4-CUT2',
#                                             'ANA5-CUT0','ANA5-CUT1','ANA5-CUT2',
#                                             'ANA7-CUT0','ANA7-CUT1','ANA7-CUT2'],
#                                 txnames=['T2tt'])
# slhadir = '/home/lessa/smodels-utils/slha/T2tt_10000_NLL_8TeV_slhas.tar'
# txnameStr = 'T2tt'
# axes = '2*Eq(mother,x)_Eq(lsp,y)'
# validatePlot(expRes,txnameStr,axes,slhadir)

 
#How to validate all plots for a single Txname in one ExpRes:
# expRes = database.getExpResults(analysisIDs=['CMS-SUS-13-004'],datasetIDs=[None],
#                                 txnames=['T1bbbb'])
# txname = 'T1bbbb'
# slhadir = '/home/lessa/smodels-utils/slha/T1bbbb.tar'
# validateTxName(expRes,txname,slhadir)
# 
# #How to validate all plots for all Txnames in one ExpRes:
# expRes = database.getExpResults(analysisIDs=['CMS-SUS-13-004'],datasetIDs=[None])
# slhaDir = '/home/lessa/smodels-utils/slha/'
# validateExpRes(expRes,slhaDir)
