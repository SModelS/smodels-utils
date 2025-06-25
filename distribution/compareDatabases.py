#!/usr/bin/env python3

from smodels.experiment.databaseObj import Database
from smodels_utils.helper.terminalcolors import *


def compare ( db1 : str, db2 : str ) -> bool:
    """ compare db1 with db2, hilight differences!
    :returns: true if they are identical 
    """
    d1 = Database ( db1 )
    d2 = Database ( db2 )
    if d1 == d2:
        return True
    print ( f"equal operator says they are not the same" )
    el1 = d1.expResultList
    el2 = d2.expResultList
    print ( f"d1: {len(el1)} results, d2: {len(el2)} results" )
    for e1,e2 in zip(el1,el2):
        col = ""
        if e1.globalInfo.id != e2.globalInfo.id:
            col = RED
        print ( col, e1.globalInfo.id, e2.globalInfo.id, RESET )
        ds1 = e1.datasets
        ds2 = e2.datasets
        for d1, d2 in zip ( ds1, ds2 ):
            print ( "    ", d1.dataInfo.dataId, d2.dataInfo.dataId )
    return False

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="simple script to create the smodels-analyses.json files" )
    ap.add_argument('-d1', '--dbpath1',
            help='path to database1 [unittest]',
            default='unittest')
    ap.add_argument('-d2', '--dbpath2',
            help='path to database2 [unittest]',
            default='unittest')
    args = ap.parse_args()
    compare ( args.dbpath1, args.dbpath2 )
