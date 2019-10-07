#!/usr/bin/env python3

def main( nmin, nmax, cont ):
    pfile, states = None, None
    if cont.lower() not in [ "none", "" ]:
        if not os.path.exists ( cont ):
            print ( "error: supplied a save states file %s, but it doesnt exist" % args.cont )
        else:
            import pickle
            try:
                with open ( cont, "rb" ) as f:
                    states = pickle.load ( f )
                pfile = cont
            except Exception as e:
                print ( "error when trying to load pickle file %s: %s" % ( cont, e ) )
                pfile = None
    import socket, copy
    print ( "I am already inside the python script! Hostname is", socket.gethostname()  )
    import sys
    sys.path.insert(0,"/users/wolfgan.waltenberger/git/smodels/")
    sys.path.insert(0,"/users/wolfgan.waltenberger/git/smodels-utils/")
    import os
    os.chdir ( "/users/wolfgan.waltenberger/git/smodels-utils/combinations/" )
    from combinations import walker
    walkers = []
    for i in range(nmin,nmax):
        if pfile is None:
            w = walker.RandomWalker( walkerid=i, dump_training = True,  )
            walkers.append ( w )
        else:
            nstates = len(states )
            ctr = ( i - args.min ) % nstates
            print ( "fromModel %d: loading %d/%d" % ( i, ctr, nstates ) )
            w = walker.RandomWalker.fromModel ( states[ctr], 10000, "aggressive", 
                    True, False )
            walkers.append ( w )
    walker.startWalkers ( walkers )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description="walkers run on a worker")
    argparser.add_argument ( '--nmin', nargs='?', help='minimum worker id [0]',
                        type=int, default=0 )
    argparser.add_argument ( '--nmax', nargs='?', help='maximum worker id [10]',
                        type=int, default=10 )
    argparser.add_argument ( '-f', '--cont', help='continue with saved states [""]',
                        type=str, default="" )
    args=argparser.parse_args()
    main( args.nmin, args.nmax, args.cont )
