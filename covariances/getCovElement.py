#!/usr/bin/env python3

""" get a certain element of a covariance matrix """

from smodels.experiment.databaseObj import Database
from smodels.base.smodelsLogging import setLogLevel
import math, sys

def getVariance( expRes, srName : str ):
    """ retrieve the variance of srName in expRes """
    dsOrder = expRes.globalInfo.datasetOrder
    print ( f"dsOrder={dsOrder}" )
    cov = expRes.globalInfo.covariance
    poses = [ i for i,x in enumerate(dsOrder) if x == srName ]
    pos = poses[0]
    print ( f"we want the {pos}th element ({srName} of {expRes.globalInfo.id})" )
    print ( f"obs({pos})={expRes.datasets[pos].dataInfo.observedN}" )
    print ( f"bg({pos})={expRes.datasets[pos].dataInfo.expectedBG}" )
    print ( f"cov({pos},{pos})={cov[pos][pos]:.3f}" )
    print ( f"sigma({pos},{pos})={math.sqrt(cov[pos][pos]):.3f}" )

def getCovariance( expRes, srName1 : str, srName2 : str ):
    """ retrieve the variance of srName in expRes """
    dsOrder = expRes.globalInfo.datasetOrder
    cov = expRes.globalInfo.covariance
    poses1 = [ i for i,x in enumerate(dsOrder) if x == srName1 ]
    pos1 = poses1[0]
    poses2 = [ i for i,x in enumerate(dsOrder) if x == srName2 ]
    pos2 = poses2[0]
    print ( f"{srName1} is at {pos1}" )
    print ( f"{srName2} is at {pos2}" )
    print ( f"cov({pos1},{pos2})={cov[pos1][pos2]:.3f}" )
    # print ( f"rho({pos1},{pos})={math.sqrt(cov[pos][pos]):.3f}" )

def getExample():
    anaId =  "CMS-SUS-21-002" 
    sr = "H_SR0"
    setLogLevel("info")
    d=Database("../../smodels-database")
    e=d.getExpResults ( analysisIDs = [ anaId ], 
                        dataTypes = [ "efficiencyMap" ] )
    print ( f"{len(e)} results" )
    getVariance ( e[0], sr )

def get():
    import argparse
    ap = argparse.ArgumentParser( description="retrieve individual covariance matrix entries" )
    ap.add_argument('-s', '--sr1', type=str, default="H_SR0",
                    help='first signal region name [H_SR0]' )
    ap.add_argument('--sr2', type=str, default="H_SR1",
                    help='second signal region name [H_SR1]' )
    ap.add_argument('-a', '--analysisId', type=str, default="CMS-SUS-21-002",
                    help='analysis id [CMS-SUS-21-002]' )
    ap.add_argument('-d', '--dbpath', type=str, default="../../smodels-database",
                    help='database path [../../smodels-database]' )
    args=ap.parse_args()
    d = Database ( args.dbpath )
    e=d.getExpResults ( analysisIDs = [ args.analysisId ], 
                        dataTypes = [ "efficiencyMap" ] )
    if len(e) == 0:
        print ( f"could not find {args.analysisId} in {args.dbpath}" )  
        sys.exit()

    getVariance ( e[0], args.sr1 )
    getCovariance ( e[0], args.sr1, args.sr2 )
    
if __name__ == "__main__":
    get()
