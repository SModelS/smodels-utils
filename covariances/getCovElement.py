#!/usr/bin/env python3

""" get a certain element of a covariance matrix """

from smodels.experiment.databaseObj import Database
from smodels.base.smodelsLogging import setLogLevel
import math

def get():
    anaId =  "CMS-PAS-SUS-16-052" 
    sr = "SR1LcY"
    # sr = "SR1VLaX"
    setLogLevel("info")
    d=Database("../../smodels-database")
    e=d.getExpResults ( analysisIDs = [ anaId ], 
                        dataTypes = [ "efficiencyMap" ] )
    print ( "%d results" % len(e) )
    dsOrder = e[0].globalInfo.datasetOrder
    cov = e[0].globalInfo.covariance
    poses = [ i for i,x in enumerate(dsOrder) if x == sr ]
    pos = poses[0]
    print ( dsOrder )
    print ( "we want the %d element" % pos )
    print ( "cov(%d,%d)=%f" % ( pos, pos, cov[pos][pos] ) )
    print ( "sigma(%d,%d)=%f" % ( pos, pos, math.sqrt(cov[pos][pos] )) )
    

get()
