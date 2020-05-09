#!/usr/bin/env python3

""" simple tool to fetch all sorts of files from clip """

import subprocess, sys, copy, argparse

def fetch ( files ):
    """ fetch the files in list """
    files = set ( files ) ## remove dupes
    for i in files:
        cmd="scp wolfgan.waltenberger@clip-login-1:/scratch-cbe/users/wolfgan.waltenberger/rundir/%s ." % i
        print ( cmd )
        ret = subprocess.run(cmd.split(" "), stderr=sys.stderr, stdout=sys.stdout)

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='file fetching utility, fetches from clip' )
    argparser.add_argument ( '-a', '--all', help='all files', action="store_true" )
    argparser.add_argument ( '--scan', help='files from scan', action="store_true" )
    argparser.add_argument ( '--states', help='the states', action="store_true" )
    argparser.add_argument ( '--pmodels', help='the pmodels', action="store_true" )
    argparser.add_argument ( '--png', help='the png files', action="store_true" )
    argparser.add_argument ( '--ssms', help='the ssm files', action="store_true" )
    argparser.add_argument ( '--copy', help='the copy of the hiscore file', 
                             action="store_true" )
    argparser.add_argument ( '-2', '--two', help='the second hiscore file', 
                             action="store_true" )
    args = argparser.parse_args()
    files= [ "hiscore.pcl" ]
    if args.scan:
        files = [ "scanM*.pcl", "mp*.pcl", "ssm*.pcl" ]
    if args.states:
        files = [ "states.pcl" ]
    if args.two:
        files = [ "hiscore2.pcl" ]
    if args.copy:
        files = [ "hiscoreCopy.pcl" ]
    if args.pmodels:
        files = [ "pmodel?.py" ]
    if args.png:
        files = [ "*.png" ]
    if args.ssms:
        files = [ "ssm*.pcl" ]
    if args.all:
        files = [ "scanM*.pcl", "mp*.pcl", "ssm*.pcl", "*png", "ssm*.pcl", "pmodel?.py"  ]
    fetch ( files )

if __name__ == "__main__":
    main()
