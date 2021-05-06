#!/usr/bin/env python3

""" script that creates a database pickle file with superseded
results only. """

import argparse

def main( ):
    ap = argparse.ArgumentParser( description="script that creates a database pickle file with superseded results only" )
    ap.add_argument('-i', '--infile', help='name of input database -- pickle file or path [../../smodels-database]', default="../../smodels-database" )
    ap.add_argument('-o', '--outfile', help='name of output pickle file [superseded.pcl]', default="superseded.pcl" )
    ap.add_argument('-f', '--filter', help='invert the selection, remove superseded entries',
                     action="store_true" )
    args = ap.parse_args()

    if args.filter and args.outfile == "superseded.pcl":
        args.outfile = "filtered.pcl"
    from smodels_utils.helper.databaseManipulations import createSuperseded
    createSuperseded ( args.infile, args.outfile, args.filter )

if __name__ == "__main__":
    main()
