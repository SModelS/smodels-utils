#!/usr/bin/env python3

""" simple tool to fetch all sorts of files from clip """

import subprocess, sys, copy, argparse, colorama

def fetch ( files, rundir ):
    """ fetch the files in list """
    print ( colorama.Fore.GREEN + "fetching:",", ".join ( files ) )
    print ( colorama.Fore.RESET )
    files = set ( files ) ## remove dupes
    basedir = "/scratch-cbe/users/wolfgan.waltenberger/"
    for i in files:
        cmd="scp wolfgan.waltenberger@clip-login-1:%s%s/%s ." % \
            ( basedir, rundir, i )
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
    argparser.add_argument ( '--llhds', help='the llhd files', action="store_true" )
    argparser.add_argument ( '--fake', help='the fake* databases', action="store_true" )
    argparser.add_argument ( '--copy', help='the copy of the hiscore file', 
                             action="store_true" )
    argparser.add_argument ( '-2', '--two', help='the second hiscore file', 
                             action="store_true" )
    argparser.add_argument ( '-R', '--rundir', help='name of remote rundir folder [rundir]', 
                             type=str, default="rundir" )
    args = argparser.parse_args()
    # files= [ "hiscore.hi" ]
    files = set()
    store = { "scan": [ "scanM*.pcl", "ssm*.pcl" ], 
              "states": [ "states.dict" ],
              "llhds": [ "llhd*pcl", "mp*pcl" ],
              "two": [ "hiscore2.hi" ],
              "fake": [ "fake*.pcl", "signal*.pcl" ],
              "copy": [ "hiscoreCopy.hi" ],
              "pmodels": [ "pmodel?.py" ],
              "png": [ "*.png" ],
              "ssms": [ "ssm*.pcl" ]
    }
    for k,v in args.__dict__.items():
        if v == True or args.all:
            if k in store:
                for f in store[k]:
                    files.add ( f )
    if len(files) == 0 or args.all: ## the default
        files.add ( "hiscore.hi" )
    fetch ( files, args.rundir )

if __name__ == "__main__":
    main()
