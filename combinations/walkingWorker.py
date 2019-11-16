#!/usr/bin/env python3

def main( nmin, nmax, cont, dbpath = "/mnt/hephy/pheno/ww/git/smodels-database/" ):
    import sys, os
    sys.path.insert(0,"/mnt/hephy/pheno/ww/git/smodels/")
    sys.path.insert(0,"/mnt/hephy/pheno/ww/git/smodels-utils/")
    sys.path.insert(0,"/mnt/hephy/pheno/ww/git/smodels-utils/combinations/")
    os.chdir ( "/mnt/hephy/pheno/ww/rundir" )
    pfile, states = None, None
    if cont.lower() not in [ "none", "" ]:
        if not os.path.exists ( cont ):
            print ( "error: supplied a save states file %s, but it doesnt exist" % cont )
        else:
            import pickle
            try:
                with open ( cont, "rb" ) as f:
                    states = pickle.load ( f )
                pfile = cont
            except Exception as e:
                print ( "error when trying to load pickle file %s: %s" % ( cont, e ) )
                pfile = None
    print ( "[walkingWorker] called main with '%s', pfile is '%s'" % ( cont, pfile ) )
    import socket, copy
    print ( "I am already inside the python script! Hostname is", socket.gethostname()  )
    from combinations import walker
    walkers = []
    for i in range(nmin,nmax):
        if pfile is None:
            print ( "[walkingWorker] from zero %d" % ( i ) )
            w = walker.RandomWalker( walkerid=i, dump_training = True, 
                                     dbpath = dbpath  )
            walkers.append ( w )
        else:
            nstates = len(states )
            ctr = i % nstates
            print ( "[walkingWorker] fromModel %d: loading %d/%d" % ( i, ctr, nstates ) )
            w = walker.RandomWalker.fromProtoModel ( states[ctr], 100000, "aggressive", 
                    walkerid = i, dump_training=True, expected = False,
                    dbpath = dbpath )
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
