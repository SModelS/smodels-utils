#!/usr/bin/env python3

""" script that creates a database pickle file with superseded
results only. """

import argparse
from smodels.experiment.databaseObj import Database

def create ( infile, outfile ):
    db = Database ( infile )
    olders = db.expResultList
    newers = []
    superseded = []
    for er in olders:
        gI = er.globalInfo
        if hasattr ( gI, "supersedes" ):
            superseded.append ( gI.supersedes )

    for er in olders:
        gI = er.globalInfo
        if hasattr ( gI, "supersededBy" ) or gI.id in superseded:
            newers.append ( er )
    db.subs[0].expResultList = newers
    db.subs = [ db.subs[0] ]
    db.subs[0].txt_meta.databaseVersion = db.databaseVersion + "superseded"
    db.createBinaryFile ( outfile )

def main( ):
    ap = argparse.ArgumentParser( description="script that creates a database pickle file with superseded results only" )
    ap.add_argument('-i', '--infile', help='name of input database -- pickle file or path [../../smodels-database]', default="../../smodels-database" )
    ap.add_argument('-o', '--outfile', help='name of output pickle file [superseded.pcl]', default="superseded.pcl" )
    args = ap.parse_args()

    create ( args.infile, args.outfile )

main()
