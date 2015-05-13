#!/usr/bin/env python

"""
.. module:: tools.checkInterpolation.py
   :synopsis:  Checks the interpolation error in the database.
"""

import sys,os
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))

from smodels.experiment.databaseObjects import Database
from smodels.tools.physicsUnits import GeV, fb, TeV, pb


def rmvPoints(txnameData):
    """
    Remove points from a TxnameData object and returns the points.
    :param txnameData: TxNameData object
    :return: list of points [[mass1,val1],[mass2,val2]...]
    """
    
    #Make sure data is loaded
    txnameData.loadData()
    pts = []
    maxN = 10.     
    reducedData = txnameData.data[:]
    for pt in txnameData.data:
        if len(pts) < len(txnameData.data)/4. and len(pts) < maxN:
            reducedData.remove(pt)
            pts.append(pt)
            
    #Reload the reduced data grid:
    txnameData.store_value = reducedData
    txnameData.loadData()
            
    return pts

def checkInterpolationFor(expIds = ['all'], txnames=['all'], datasetIDs = ['all']):
    """
    Remove points from the data grid and interpolate on them.
    Returns the maximum relative error for each txname grid.
    """

    #Load the database
    database = Database(os.path.join(home,'smodels-database'))
    expResults = database.getExpResults(analysisIDs=expIds, txnames=txnames, 
                                        datasetIDs=datasetIDs)
    
    #Get all the txName objects:
    txnames = []
    for expRes in expResults:
        for dataset in expRes.datasets:
            txnames += dataset.txnameList
    
    
    #Loop over each grid and generate a reduced grid partially removing
    #the original points
    removedPts = []
    for txname in txnames:
        removedPts.append(rmvPoints(txname.txnameData))
        
    #Now interpolate for the removed points
    maxErrors = [0.]*len(txnames)
    for itx,txname in enumerate(txnames):
        for pt in removedPts[itx]:            
            val = txname.txnameData.getValueFor(pt[0])
            if val is None or val == pt[1]: continue
            maxErrors[itx] = max(maxErrors[itx],2.*abs(val-pt[1])/(pt[1]+val))
            
    
    #Print results
    for itx,txname in enumerate(txnames):
        print txname,maxErrors[itx]
        
        
if __name__ == "__main__":
    
    expIds = ['ATLAS-SUSY-2013-02']
    txnames = ['T2']
    datasetIDs = ['all']
    checkInterpolationFor(expIds,txnames,datasetIDs)    

    
        