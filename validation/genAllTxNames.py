#!/usr/bin/env python

import sys,os,logging
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
from smodels.theory.crossSection import logger as cl
from smodels.theory.slhaDecomposer import logger as dl
from smodels.experiment.txnameObject import logger as tl
from gridSModelS import logger as gl
cl.setLevel(level=logging.ERROR) 
dl.setLevel(level=logging.ERROR)
tl.setLevel(level=logging.ERROR)
gl.setLevel(level=logging.ERROR)


from smodels.experiment.databaseObjects import Database
import subprocess

database = Database(os.path.join(os.path.expanduser("~"),"smodels-database/"))

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
        
