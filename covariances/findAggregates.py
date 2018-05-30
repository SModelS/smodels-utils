#!/usr/bin/python3

""" Identify a good example for how to combine results. """


import sys, numpy
import colorama
from math import sqrt
from smodels.experiment.databaseObj import Database
import IPython
import pickle
import tempfile
import os

# dbname="http://smodels.hephy.at/database/official113"
dbname="/home/walten/git/smodels-database"
d=Database( dbname, subpickle=True )
#ids= ['CMS-PAS-SUS-16-052' ]
ids= ['CMS-SUS-16-050' ]
if len(sys.argv)>1:
    ids = [ sys.argv[1] ]
    if sys.argv[1]=="-h" or sys.argv[1]=="--help":
        print ( "usage: findAggregates.py [CMS-PAS-SUS-16-052|CMS-SUS-16-050]" )
        sys.exit()
results=d.getExpResults( analysisIDs=ids, dataTypes=["efficiencyMap"],
                         useNonValidated=True )
result=results[0]

def getDatasets():
    datasets={}
    for _,ds in enumerate ( result.datasets ):
        i=_+1
#        print ( i, ds.dataInfo.dataId )
        datasets[i]=ds.dataInfo.dataId
        datasets[ ds.dataInfo.dataId ] = i
    return datasets

cov = result.globalInfo.covariance 
n=len(cov)
# n=2

for i in range(n):
    for j in range(i+1,n):
        print ( "cov[%d,%d]=%f" % ( i+1,j+1, cov[i][j]/sqrt(cov[i][i]*cov[j][j] ) ) )
