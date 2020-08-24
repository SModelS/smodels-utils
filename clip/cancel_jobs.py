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
    argparser.add_argument ( '-d','--dry_run', help='dry-run just tell what you would do',
                             action="store_true" )
    argparser.add_argument ( '-r','--run', help='cancel all RUN jobs (ie the walkers only)',
                             action="store_true" )
    argparser.add_argument ( '-H','--hiscore', help='cancel all hiscore jobs',
                             action="store_true" )
    argparser.add_argument ( '-P', '--pattern', help='cancel all jobs that have <pattern> in the name',
                             type=str, default=None )
    args=argparser.parse_args()
    grp = "| grep QOSMax"
    if args.all:
        grp = ""
    if args.pattern != None:
        grp = "| grep %s" % args.pattern
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
    if args.dry_run:
        print ( "dry run, but here is what I would do:" )
    print ( "cancelling", end=" " )
    for line in a.split("\n" ):
        jobid = line[:8].strip()
        print ( "%s" % jobid, end=" " )
        if not args.dry_run:
            subprocess.getoutput ( "scancel %s" % jobid )
    print ( "done." )

main()
