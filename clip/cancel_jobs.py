#!/usr/bin/env python3

import subprocess, argparse

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="cancel certain jobs")
    argparser.add_argument ( '-p','--pending', help='cancel pending jobs',
                             action="store_true" )
    argparser.add_argument ( '-a','--all', help='cancel all jobs',
                             action="store_true" )
    args=argparser.parse_args()
    grp = "| grep QOSMax"
    if args.all:
        grp = ""
    if args.pending:
        grp = "| grep PENDING"
    a= subprocess.getoutput ( "slurm q %s" % grp )
    print ( "cancelling", end=" " )
    for line in a.split("\n" ):
        jobid = line[:8].strip()
        print ( "%s" % jobid, end=" " )
        subprocess.getoutput ( "scancel %s" % jobid )
    print ( "done." )

main()
