#!/usr/bin/env python3

"""
Main code for submitting a walk
"""

from modelWalker.walkingWorker import main

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description="walkers run on a worker")
    argparser.add_argument ( '-n', '--nmin', nargs='?', help='minimum worker id [40]',
                        type=int, default=40 )
    argparser.add_argument ( '-N', '--nmax', nargs='?', help='maximum worker id [90]',
                        type=int, default=90 )
    argparser.add_argument ( '-C', '--cheat', nargs='?', help='cheat code [0]',
                        type=int, default=0 )
    argparser.add_argument ( '-f', '--cont', help='continue with saved states [""]',
                        type=str, default="default" )
    argparser.add_argument ( '-R', '--rundir',
                        help='override the default rundir [None]',
                        type=str, default=None )
    argparser.add_argument ( '-m', '--maxsteps', nargs='?', help='maximum number of steps [10000]',
                        type=int, default=1000000 )
    argparser.add_argument ( '-e', '--nevents', nargs='?', help='number of MC events for computing cross-sections [100000]',
                        type=int, default=100000 )

    args=argparser.parse_args()
    main( args.nmin, args.nmax, args.cont, cheatcode = args.cheat,
            rundir = args.rundir, maxsteps = args.maxsteps, nevents = args.nevents)
