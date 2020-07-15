#!/usr/bin/env python3

"""
Main code for submitting a walk
"""

from walker.walkingWorker import main

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
                        type=int, default=10000 )
    argparser.add_argument ( '-e', '--nevents', nargs='?', help='number of MC events for computing cross-sections [10000]',
                        type=int, default=10000 )
    argparser.add_argument ( '-s','--seed',
            help='seed the random number generators [None]',
            type=int, default=None )
    argparser.add_argument ( '-E', '--no_catch',
            help='if set, do not catch exceptions', action='store_true' )

    args=argparser.parse_args()

    catchem = not args.no_catch

    if args.seed is not None:
        from tools import helpers
        helpers.seedRandomNumbers(args.seed)


    main( args.nmin, args.nmax, args.cont, cheatcode = args.cheat,
            rundir = args.rundir, maxsteps = args.maxsteps, nevents = args.nevents,
            seed = args.seed, catchem = catchem )
