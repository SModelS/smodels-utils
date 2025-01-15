#!/usr/bin/env python3

""" Identify efficiency maps that never make it above a certain threshold """

import sys, numpy, subprocess
from math import sqrt
from smodels.experiment.databaseObj import Database
import IPython
import pickle
import tempfile
import os
import argparse


def main():
    ap = argparse.ArgumentParser( description= "find aggregate regions based on correlations." )
    ap.add_argument('-a','--analysis',help="name of analysis to discuss [CMS-SUS-16-050]",
                    default = "CMS-SUS-16-050", type=str )
    ap.add_argument('-d','--database',help="path to database [../../smodels-database]",
                    default = "../../smodels-database", type=str )
    ap.add_argument('-m','--min',help="minimum efficiency value [1e-4]",
                    default = 1e-4, type=float )
    ap.add_argument('-D','--dry_run',help="dry_run dont erase",
                    action="store_true" )
    args = ap.parse_args()
    d=Database( args.database )

    if "52" in args.analysis:
        args.analysis = "CMS-PAS-SUS-16-052"
    if "50" in args.analysis:
        args.analysis = "CMS-SUS-16-050"
    ids = [ args.analysis ]
    results=d.getExpResults( analysisIDs=ids, dataTypes=["efficiencyMap"],
                             useNonValidated=True )
    result=results[0]
    nkicked, ntot = 0, 0
    for ds in result.datasets:
        for txn in ds.txnameList:
            maxeff = max ( txn.txnameData.y_values )
            kick = False
            ntot += 1
            skick="not kicking"
            cmd = None
            if maxeff < args.min:
                kick=True
                nkicked += 1
                skick="kicking"
                ana = args.analysis+ "-eff"
                cmd = f"rm -rf {args.database}/13TeV/CMS/{ana}/{ds.dataInfo.dataId}/{txn.txName}.txt"
                print ( cmd )
                if not args.dry_run:
                    subprocess.getoutput ( cmd )

            print ( skick, "dataset", ds.dataInfo.dataId, "txn", txn.txName, "m", maxeff, "kick", kick )
    print ( "kicking %d/%d txnames" % ( nkicked, ntot ) )


main()
