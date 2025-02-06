#!/usr/bin/env python3

""" get a certain element of a covariance matrix """

from smodels.experiment.databaseObj import Database
from smodels.base.smodelsLogging import setLogLevel
import math

def get():
    anaId =  "CMS-SUS-21-002" 
    sr = "H_SR0"
    setLogLevel("info")
    d=Database("../../smodels-database")
    e=d.getExpResults ( analysisIDs = [ anaId ], 
                        dataTypes = [ "efficiencyMap" ] )
    print ( f"{len(e)} results" )
    dsOrder = e[0].globalInfo.datasetOrder
    cov = e[0].globalInfo.covariance
    poses = [ i for i,x in enumerate(dsOrder) if x == sr ]
    pos = poses[0]
    print ( dsOrder )
    print ( f"we want the {pos} element" )
    print ( f"cov({pos},{pos})={cov[pos][pos]}" )
    print ( f"sigma({pos},{pos})={math.sqrt(cov[pos][pos])}" )
    

if __name__ == "__main__":
    get()
