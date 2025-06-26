#!/usr/bin/env python3

from smodels.experiment.databaseObj import Database
from smodels_utils.helper.terminalcolors import *

def getDatasetByName ( er, dsName : str ):
    """ get a SModelS dataset, given the experimental result object
    plus the dataset name """
    for ds in er.datasets:
        if ds.dataInfo.dataId == dsName:
            return ds
    return None

def compareOneResult ( er1, er2 ):
    """ compare a single experimental result """
    col = ""
    if er1.globalInfo.id != er2.globalInfo.id:
        col = RED
    print ( col, er1.globalInfo.id, er2.globalInfo.id, RESET )
    ds1 = [ x.dataInfo.dataId for x in er1.datasets ]
    ds1.sort()
    ds2 = [ x.dataInfo.dataId for x in er2.datasets ]
    ds2.sort()
    if len(ds1)!=len(ds2):
        print ( f"ds1 has {len(ds1)} entries, ds2 has {len(ds2)} entries" )
    for d1, d2 in zip ( ds1, ds2 ):
        col = ""
        if d1 != d2:
            col = RED
            print ( "    ", col, d1, "<->", d2, RESET )

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
    print ( f"db1 is {db1} db2 is {db2}" )
    print ( f"d1: {len(el1)} results, d2: {len(el2)} results" )
    print ( f"sms1: {d1.expSMSDict} sms2: {d2.expSMSDict}" )
    if True:
        for e1,e2 in zip(el1,el2):
            compareOneResult ( e1, e2 )
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
