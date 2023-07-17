#!/usr/bin/env python3
    
from smodels.experiment.databaseObj import Database
import fnmatch

def listTopologyNames ( pattern ):
    db = Database ( "official" )
    ers = db.getExpResults()
    txnames = set()
    print ( "pattern", pattern )
    for er in ers:
        for ds in er.datasets:
            for txn in ds.txnameList:
                if fnmatch.filter ( [ str(txn) ], pattern ):
                    txnames.add ( str(txn) )
    print ( f"{len(txnames)} names: {','.join(txnames)}" )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='List topology names of following a certain pattern')
    argparser.add_argument ( '-p', '--pattern', help='pattern [T*]',
                             type=str, default='T*' )
    args = argparser.parse_args()
    listTopologyNames( args.pattern )
