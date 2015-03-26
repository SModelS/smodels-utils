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


from plotProducer import validateTxName
from smodels.experiment.databaseObjects import Database
database = Database(os.path.join(os.path.expanduser("~"),"smodels-database/"))


def main(txname):

    if not os.path.isfile("../slha/"+txname+".tar"):
        print 'missing .tar file for',txname
        return False
    try:
        print 'running for',txname
        expResList = database.getExpResults(datasetIDs=[None],txnames=[txname])
        k=1.
        if 'TChi' in txname: k = 1.25
        slhadir = '/home/lessa/smodels-utils/slha/'+txname+'.tar'
        validateTxName(expResList,txname,slhadir,kfactor=k)
    except:
        print 'Error when validating',txname


if __name__ == '__main__':
    if len(sys.argv)>1:
        txname=sys.argv[1]
    main( txname )
        
