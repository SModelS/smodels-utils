#!/usr/bin/env python

import sys,os



from plotProducer import validateTxName,validatePlot,validateExpRes
from smodels.experiment.databaseBrowser import Browser
from smodels.experiment.databaseObjects import DataBase
import subprocess

database = DataBase(os.path.join(os.path.expanduser("~"),"smodels-database/"))

txnames = []
for expRes in database.getExpResults(datasetIDs=[None]):
    for tx in expRes.getTxNames():
        if not tx.txname in txnames: txnames.append(tx.txname)

for txname in txnames:
    if not os.path.isfile("../slha/templates/"+txname+".template"):
        print 'missing template for',txname
        continue
    try:
        print 'running for',txname 
        r = subprocess.check_call(["./createFilesForTxName.py",txname])        
    except:
        print 'Error when generating for',txname
        
