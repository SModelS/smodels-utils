#!/usr/bin/env python3

""" script that creates a database pickle file with superseded
results only. """

import argparse
from smodels.experiment.databaseObj import Database

def create ( infile, outfile, filtered ):
    """
    :param filtered: if true, then remove superseded entries instead of the other way round
    """
    db = Database ( infile )
    olders = db.expResultList
    newers, supers, fastlims = [], [], []
    superseded = []
    for er in olders:
        gI = er.globalInfo
        if hasattr ( gI, "supersedes" ):
            superseded.append ( gI.supersedes )

    for er in olders:
        gI = er.globalInfo
        if hasattr ( gI, "supersededBy" ) or gI.id in superseded:
            newers.append ( er )
        elif hasattr ( gI, "contact" ) and "fastlim" in gI.contact.lower():
                fastlims.append ( er )
        else:
            supers.append ( er )
    if filtered:
        db.subs[0].expResultList = supers
    else:
        db.subs[0].expResultList = newers
    db.subs = [ db.subs[0] ]
    sstring = "superseded"
    if filtered:
        sstring = "nosuperseded"
    db.subs[0].txt_meta.databaseVersion = db.databaseVersion + sstring
    db.createBinaryFile ( outfile )

def main( ):
    ap = argparse.ArgumentParser( description="script that creates a database pickle file with superseded results only" )
    ap.add_argument('-i', '--infile', help='name of input database -- pickle file or path [../../smodels-database]', default="../../smodels-database" )
    ap.add_argument('-o', '--outfile', help='name of output pickle file [superseded.pcl]', default="superseded.pcl" )
    ap.add_argument('-f', '--filter', help='invert the selection, remove superseded entries',
                     action="store_true" )
    args = ap.parse_args()

    if args.filter and args.outfile == "superseded.pcl":
        args.outfile = "filtered.pcl"
    create ( args.infile, args.outfile, args.filter )

main()
