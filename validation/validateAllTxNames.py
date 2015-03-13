#!/usr/bin/env python

import sys,os



from plotProducer import validateTxName
from smodels.experiment.databaseObjects import DataBase

database = DataBase(os.path.join(os.path.expanduser("~"),"smodels-database/"))

txnames = []
for expRes in database.getExpResults(datasetIDs=[None]):
    for tx in expRes.getTxNames():
        if not tx.txname in txnames: txnames.append(tx.txname)

for txname in txnames:
    if not os.path.isfile("../slha/"+txname+".tar"):
        print 'missing .tar file for',txname
        continue
    try:
        print 'running for',txname
        expResList = database.getExpResults(datasetIDs=[None],txnames=[txname])
        k=1.
	if 'TChi' in txname: k = 1.25
        slhadir = '/home/lessa/smodels-utils/slha/'+txname+'.tar'
        validateTxName(expResList,txname,slhadir,kfactor=k)
    except:
        print 'Error when validating',txname
        
