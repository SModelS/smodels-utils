#!/usr/bin/env python3

""" the code that writes all the simplices into a dictionary 
So we can later compare the dictionaries.
"""

import os, socket, argparse, time, subprocess, sys
from typing import Union, List

def removePickles ( picklefile : os.PathLike, really : bool  ):
    if really and not picklefile.endswith( ".pcl" ):
        cmd = f"rm -rf {picklefile}/**/.pcl {picklefile}/*.pcl" 
        print ( f"removing all old pickles: {cmd}" )
        subprocess.getoutput ( cmd )
        # sys.exit()

def getTriangulation ( picklefile : os.PathLike, anaIds : List,
                       outfile : Union[None,os.PathLike] ) -> os.PathLike:
    hostname = socket.gethostname()
    if outfile == None:
        outfile = hostname
    from smodels.experiment.databaseObj import Database
    obj = Database ( picklefile )
    osimplices, esimplices = {}, {}
    opoints, epoints = {}, {}
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
    return f"{outfile}.pcl"

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="creates simplices dictionary file")
    ap.add_argument('-d', '--dbpath',
            help='path to database [../../smodels-database]', 
            default='../../smodels-database')
    ap.add_argument('-o', '--outfile',
            help='output file without extension. if none, then hostname [None]', 
            default=None )
    ap.add_argument('-u', '--upload',
            help='upload file to clip-login-1',  action="store_true" )
    ap.add_argument('-s', '--subset',
            help='use only predefined subset of analyses',  action="store_true" )
    ap.add_argument('-k', '--keep_pickles',
            help='keep old pickle files',  action="store_true" )
    args = ap.parse_args()
    anaIds = [ "all" ]
    # for starters its sufficient to look only at a few
    if args.subset:
        anaIds = [ "CMS-SUS-21-002" ]
    removePickles ( args.dbpath, not args.keep_pickles )
    of = getTriangulation ( args.dbpath, anaIds, args.outfile )
    if args.upload:
        cmd = f"scp {of} clip-login-1:git/smodels-utils/delaunay/"
        subprocess.getoutput ( cmd )
