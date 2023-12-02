#!/usr/bin/env python3

""" the code that writes all the simplices into a dictionary 
So we can later compare the dictionaries.
"""

import os, socket, argparse, time
from typing import Union

def getTriangulation ( picklefile : os.PathLike, 
                       outfile : Union[None,os.PathLike] ):
    hostname = socket.gethostname()
    if outfile == None:
        outfile = hostname
    from smodels.experiment.databaseObj import Database
    obj = Database ( picklefile )
    observed, expected = {}, {}
    # ers = obj.expResultList
    ers = obj.getExpResults() # we only do validated etc
    for er in ers:
        for ds in er.datasets:
            for txn in ds.txnameList:
                stxn = f"{er.globalInfo.id}:{ds.dataInfo.dataId}:{txn}"
                print ( stxn )
                simplices = txn.txnameData.tri.simplices.tolist()
                observed[stxn]=simplices
                if hasattr ( txn, "txnameDataExp" ) and txn.txnameDataExp is not None:
                    simplices = txn.txnameDataExp.tri.simplices.tolist()
                    expected[stxn]=simplices
    writePythonFile=False
    if writePythonFile:
        with open ( f"{outfile}.py", "wt" ) as f:
            f.write ( f"# hostname {hostname}\n" )
            f.write ( f"# database v{obj.databaseVersion}\n" )
            f.write ( f"# picklefile {picklefile}\n" )
            f.write ( f"observed={observed}\n" )
            f.write ( f"expected={observed}\n" )
            f.close()
    meta = { "hostname": hostname, "time": time.asctime(),
             "dbversion": obj.databaseVersion, "picklefile": picklefile }
    f = open ( f"{outfile}.pcl", "wb" )
    import pickle
    pickle.dump ( meta, f )
    pickle.dump ( observed, f )
    pickle.dump ( expected, f )
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
