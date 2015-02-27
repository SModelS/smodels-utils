#!/usr/bin/env python

import sys,os



from plotProducer import validateTxName,validatePlot,validateExpRes
from smodels.experiment.databaseBrowser import Browser
from smodels.experiment.databaseObjects import DataBase

database = DataBase("/home/lessa/smodels-database/")


# #How to validate one single plot:
# browser = Browser(database)
# browser.loadExpResultsWith({'id' : ['CMS-SUS-13-004']})
# expRes = browser[0]
# txname = expRes.getTxnameWith({'txname': 'T1bbbb'})
# slhadir = '/home/lessa/smodels-utils/slha/T1bbbb'
# axes = txname.getInfo('axes')
# if isinstance(axes,list): axes = axes[0]
# validatePlot(expRes,txname,axes,slhadir)
# 
# #How to validate all plots for a single Txname in one ExpRes:
# browser = Browser(database)
# browser.loadExpResultsWith({'id' : ['CMS-SUS-13-004']})
# expRes = browser[0]
# txname = expRes.getTxnameWith({'txname': 'T1bbbb'})
# slhadir = '/home/lessa/smodels-utils/slha/T1bbbb'
# validateTxName(expRes,txname,slhadir)

#How to validate all plots for all Txnames in one ExpRes:
browser = Browser(database)
browser.loadExpResultsWith({'id' : ['CMS-SUS-13-004']})
expRes = browser[0]
slhamain = '/home/lessa/smodels-utils/slha/'
slhaDict = {'T1bbbb': os.path.join(slhamain,'T1bbbb'),
            'T1tttt': os.path.join(slhamain,'T1tttt'),
            'T2tt': os.path.join(slhamain,'T2tt'),
            'T1ttttoff': os.path.join(slhamain,'T1tttt'),
            'T2ttoff': os.path.join(slhamain,'T2tt')}

validateExpRes(expRes,slhaDict)
