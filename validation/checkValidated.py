#!/usr/bin/env python

import sys,os
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))

from smodels.experiment.databaseObjects import DataBase

database = DataBase(os.path.join(os.path.expanduser("~"),"smodels-database/"))

validated = []
not_validated = []
for expRes in database.getExpResults(datasetIDs=[None]):
    for txname in expRes.getTxNames():
        if 'assigned' in txname.getInfo('constraint'): continue
        if txname.getInfo('validated'): validated.append(txname)  
        else: not_validated.append(txname)

print '# Validated Txnames =',len(validated)

print '# Not Validated Txnames =',len(not_validated)
for txname in not_validated:
    print txname.getInfo('txnameFile')