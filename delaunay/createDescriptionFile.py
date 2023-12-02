#!/usr/bin/env python3

""" the code that writes all the simplices into a dictionary 
So we can later compare the dictionaries.
"""

import os, socket, argparse

def getTriangulation ( picklefile : os.PathLike ):
    from smodels.experiment.databaseObj import Database
    obj = Database ( picklefile )
    ers = obj.expResultList
    observed, expected = {}, {}
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
    with open ( "simplices.py", "wt" ) as f:
        f.write ( f"# {socket.gethostname()}\n" )
        f.write ( f"# database v{obj.databaseVersion}\n" )
        f.write ( f"# picklefile={picklefile}\n" )
        f.write ( f"observed={observed}\n" )
        f.write ( f"expected={observed}\n" )
        f.close()
                    
    # import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="creates simplices dictionary file")
    ap.add_argument('-d', '--dbpath',
            help='path to database [../../smodels-database]', 
            default='../../smodels-database')
    args = ap.parse_args()
    getTriangulation ( args.dbpath )
