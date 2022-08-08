#!/usr/bin/env python3

""" script that creates a database pickle file with superseded
results only. """

import argparse
import sys,os

def main( ):
    ap = argparse.ArgumentParser( description="script that creates a database pickle file with superseded results only" )
    ap.add_argument('-i', '--infile', help='name of input database -- pickle file or path [../../smodels-database]', default="../../smodels-database" )
    ap.add_argument('-o', '--outfile', help='name of output pickle file [superseded.pcl]', default="superseded.pcl" )
    ap.add_argument('-f', '--filter', help='invert the selection, remove superseded entries',
                     action="store_true" )
    ap.add_argument('-P', '--smodelsPath', help='path to the SModelS folder [None]', default=None)                     
    args = ap.parse_args()

    if args.filter and args.outfile == "superseded.pcl":
        args.outfile = "filtered.pcl"

    if args.smodelsPath:
        sys.path.append(os.path.abspath(args.smodelsPath))


    try:
        from smodels_utils.helper.databaseManipulations import createSupersededPickle
    except ModuleNotFoundError:
        sys.path.append('../')
        from smodels_utils.helper.databaseManipulations import createSupersededPickle
    
    createSupersededPickle ( args.infile, args.outfile, args.filter )

if __name__ == "__main__":
    main()
