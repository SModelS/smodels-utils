#!/usr/bin/env python3

import subprocess, argparse

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="cancel certain jobs")
    argparser.add_argument ( '-p','--pending', help='cancel pending jobs',
                             action="store_true" )
    argparser.add_argument ( '-a','--all', help='cancel all jobs',
                             action="store_true" )
    argparser.add_argument ( '-b','--bake', help='cancel all baking jobs',
                             action="store_true" )
    argparser.add_argument ( '-s','--server', help='cancel all server jobs',
                             action="store_true" )
    argparser.add_argument ( '-r','--run', help='cancel all RUN jobs (ie the walkers only)',
                             action="store_true" )
    argparser.add_argument ( '-H','--hiscore', help='cancel all hiscore jobs',
                             action="store_true" )
    args=argparser.parse_args()
    grp = "| grep QOSMax"
    if args.all:
        grp = ""
    if args.bake:
        grp = "| grep ' B'"
    if args.pending:
        grp = "| grep PENDING"
    if args.hiscore:
        grp = "| grep HI"
    if args.server:
        grp = "| grep SERVER"
    if args.run:
        grp = "| grep RUN_"
    a= subprocess.getoutput ( "slurm q %s" % grp )
    print ( "cancelling", end=" " )
    for line in a.split("\n" ):
        jobid = line[:8].strip()
        print ( "%s" % jobid, end=" " )
        subprocess.getoutput ( "scancel %s" % jobid )
    print ( "done." )

main()
