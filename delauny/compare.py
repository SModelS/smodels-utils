#!/usr/bin/env python3

""" code to compare delaunay triangulations """

import os

def getTriangulation ( picklefile : os.PathLike ):
    from smodels.experiment.databaseObj import Database
    obj = Database ( picklefile )
    ers = obj.expResultList
    for er in ers:
        for ds in er.datasets:
            for txn in ds.txnameList:
                print ( f"{er.globalInfo.id}:{ds.dataInfo.dataId}:{txn}" )
                simplices = txn.txnameData.tri.simplices
    # import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

if __name__ == "__main__":
    getTriangulation ( "../../smodels-database/" )
