#!/usr/bin/env python3

""" get a certain element of a covariance matrix """

from smodels.experiment.databaseObj import Database
from smodels.base.smodelsLogging import setLogLevel
import math, sys
import numpy as np

def getVariance( expRes, srName : str ):
    """ retrieve the variance of srName in expRes """
    dsOrder = expRes.globalInfo.datasetOrder
    print ( f"dsOrder={' '.join(dsOrder)}" )
    cov = expRes.globalInfo.covariance
    poses = [ i for i,x in enumerate(dsOrder) if x == srName ]
    if len(poses)==0:
        if srName not in [ None, "None", "none" ]:
            print ( f"could not find {srName} in {expRes.globalInfo.id}" )
        return
    pos = poses[0]
    print ( f"we want the {pos}th element ({srName} of {expRes.globalInfo.id})" )
    print ( f"obs({srName})={expRes.datasets[pos].dataInfo.observedN}" )
    print ( f"bg({srName})={expRes.datasets[pos].dataInfo.expectedBG}" )
    print ( f"cov({srName},{srName})={cov[pos][pos]:.3f}" )
    print ( f"sigma({srName},{srName})={math.sqrt(cov[pos][pos]):.3f}" )

def getCovariance( expRes, srName1 : str, srName2 : str ):
    """ retrieve the variance of srName in expRes """
    dsOrder = expRes.globalInfo.datasetOrder
    cov = expRes.globalInfo.covariance
    poses1 = [ i for i,x in enumerate(dsOrder) if x == srName1 ]
    if len(poses1)==0:
        if srName1 not in [ None, "None", "none" ]:
            print ( f"could not find {srName1} in {expRes.globalInfo.id}" )
        return
    pos1 = poses1[0]
    poses2 = [ i for i,x in enumerate(dsOrder) if x == srName2 ]
    if len(poses2)==0:
        if srName2 not in [ None, "None", "none" ]:
            print ( f"could not find {srName2} in {expRes.globalInfo.id}" )
        return
    pos2 = poses2[0]
    #print ( f"{srName1} is at {pos1}" )
    #print ( f"{srName2} is at {pos2}" )
    print ( f"cov({srName1},{srName2})={cov[pos1][pos2]:.3f}" )
    print ( f"rho({pos1},{pos2})={cov[pos1][pos2]/np.sqrt(cov[pos1][pos1]*cov[pos2][pos2]):.3f}" )

def getExample():
    anaId =  "CMS-SUS-21-002" 
    sr = "H_SR0"
    setLogLevel("info")
    d=Database("../../smodels-database")
    e=d.getExpResults ( analysisIDs = [ anaId ], 
                        dataTypes = [ "efficiencyMap" ] )
    print ( f"{len(e)} results" )
    getVariance ( e[0], sr )


def checkAll( expRes ):
    """ retrieve the variance of srName in expRes """
    dsOrder = expRes.globalInfo.datasetOrder
    cov = expRes.globalInfo.covariance
    isPositiveDefinite = True
    for i in range(len(cov)):
        for j in range(i+1,len(cov)):
            covij = cov[i][j]
            vari = cov[i][i]
            varj = cov[j][j]
            det = vari * varj - covij * covij
            rho = covij / np.sqrt ( vari * varj )
            if det <= 0:
                isPositiveDefinite = False
                print ( f"=============================" )
                print ( f"error, not positive definite" )
                print ( i,j, rho, det )
            if abs(rho) > .9:
                print ( f"=============================" )
                print ( f"warning, very high rho:" )
                print ( f"{dsOrder[i]}[{i:3d}],{dsOrder[j]}[{j:3d}]: rho={rho:.3f}, det={det:.3f}" )
                print ( f"var({dsOrder[i]})={vari}" )
                print ( f"var({dsOrder[j]})={varj}" )
                print ( f"cov({dsOrder[i]},{dsOrder[j]})={covij}" )
    if isPositiveDefinite:
        print ( f"[getCovElement] matrix seems to be positive definite." )
    else:
        print ( f"[getCovElement] ERROR: matrix is violating positive definiteness" )


def get():
    import argparse
    ap = argparse.ArgumentParser( description="retrieve individual covariance matrix entries" )
    ap.add_argument('-s', '--sr1', type=str, default="H_SR0",
                    help='first signal region name [H_SR0]' )
    ap.add_argument('--sr2', type=str, default=None,
                    help='second signal region name [None]' )
    ap.add_argument('-a', '--analysisId', type=str, default="CMS-SUS-21-002",
                    help='analysis id [CMS-SUS-21-002]' )
    ap.add_argument('-d', '--dbpath', type=str, default="../../smodels-database",
                    help='database path [../../smodels-database]' )
    ap.add_argument('--check_all', help="check all sub-matrices",
                    action="store_true" )
    args=ap.parse_args()
    d = Database ( args.dbpath )
    e=d.getExpResults ( analysisIDs = [ args.analysisId ], 
                        dataTypes = [ "efficiencyMap" ] )
    if len(e) == 0:
        print ( f"could not find {args.analysisId} in {args.dbpath}" )  
        sys.exit()
    if args.check_all:
        checkAll ( e[0] )
        sys.exit()

    getVariance ( e[0], args.sr1 )
    getCovariance ( e[0], args.sr1, args.sr2 )
    
if __name__ == "__main__":
    get()
