#!/usr/bin/env python3

""" the code that writes all the simplices into a dictionary 
So we can later compare the dictionaries.
"""

import os, socket, argparse, time, subprocess, sys
from typing import Union

def getTriangulation ( picklefile : os.PathLike, 
                       outfile : Union[None,os.PathLike] ):
    hostname = socket.gethostname()
    if outfile == None:
        outfile = hostname
    from smodels.experiment.databaseObj import Database
    removeOldPickles = True
    if removeOldPickles and not picklefile.endswith( ".pcl" ):
        cmd = f"rm -rf {picklefile}/**/.pcl {picklefile}/*.pcl" 
        print ( f"removing all old pickles: {cmd}" )
        subprocess.getoutput ( cmd )
        # sys.exit()
    obj = Database ( picklefile )
    osimplices, esimplices = {}, {}
    opoints, epoints = {}, {}
    # ers = obj.expResultList
    anaIds = [ "all" ]
    # for starters its sufficient to look only at a few
    anaIds = [ "CMS-SUS-21-002" ]
    ers = obj.getExpResults( analysisIDs = anaIds ) # we only do validated etc
    for er in ers:
        for ds in er.datasets:
            for txn in ds.txnameList:
                stxn = f"{er.globalInfo.id}:{ds.dataInfo.dataId}:{txn}"
                print ( stxn )
                tri = txn.txnameData.tri
                simplices = tri.simplices.tolist()
                osimplices[stxn]=simplices
                opoints[stxn] = list ( tri.points )
                if hasattr ( txn, "txnameDataExp" ) and txn.txnameDataExp is not None:
                    simplices = tri.simplices.tolist()
                    esimplices[stxn]=simplices
                    epoints[stxn] = list ( tri.points )
    writePythonFile=False
    if writePythonFile:
        with open ( f"{outfile}.py", "wt" ) as f:
            f.write ( f"# hostname {hostname}\n" )
            f.write ( f"# database v{obj.databaseVersion}\n" )
            f.write ( f"# picklefile {picklefile}\n" )
            f.write ( f"osimplices={osimplices}\n" )
            f.write ( f"esimplices={esimplices}\n" )
            f.close()
    meta = { "hostname": hostname, "time": time.asctime(),
             "dbversion": obj.databaseVersion, "picklefile": picklefile }
    f = open ( f"{outfile}.pcl", "wb" )
    import pickle
    dump = { "meta": meta, "osimplices": osimplices, "esimplices": esimplices, 
             "opoints": opoints, "epoints": epoints }
    pickle.dump ( dump, f )
    f.close()
                    
    # import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="creates simplices dictionary file")
    ap.add_argument('-d', '--dbpath',
            help='path to database [../../smodels-database]', 
            default='../../smodels-database')
    ap.add_argument('-o', '--outfile',
            help='output file without extension. if none, then hostname [None]', 
            default=None )
    args = ap.parse_args()
    getTriangulation ( args.dbpath, args.outfile )
