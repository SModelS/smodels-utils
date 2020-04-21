#!/usr/bin/env python3

import sys, os

def setup():
    # codedir = "/mnt/hephy/pheno/ww/git/"
    codedir = "/scratch-cbe/users/wolfgan.waltenberger/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/combinations/" % codedir )
    rundir = "/scratch-cbe/users/wolfgan.waltenberger/rundir/"
    # rundir = "/mnt/hephy/pheno/ww/rundir/"
    # rundir = "./"
    if os.path.exists ( "./rundir.conf" ):
        with open ( "./rundir.conf" ) as f:
            rundir = f.read().strip()
    rundir = rundir.replace ( "~", os.environ["HOME"] )
    os.chdir ( rundir )
    return rundir

def main( nmin, nmax, cont, 
          dbpath = "/scratch-cbe/users/wolfgan.waltenberger/git/smodels-database/",
          cheatcode = 0 ):
    """ a worker node to set up to run walkers 
    :param nmin: the walker id of the first walker
    :param nmax: the walker id of the last walker (?)
    :param cont: start with protomodels given in the pickle file 'cont'
    :param cheatcode: in case we wish to start from a cheat model
    """
    import sys, os
    rundir = setup()
    pfile, states = None, None
    if cont == "default":
        import os
        cont = "%s/states.pcl" % rundir
        if not os.path.exists ( cont ):
            cont = "default"
    if cont.lower() not in [ "none", "" ]:
        if not os.path.exists ( cont ):
            print ( "error: supplied a save states file ,,%s'', but it doesnt exist" % cont )
        else:
            import pickle
            try:
                with open ( cont, "rb" ) as f:
                    states = pickle.load ( f )
                pfile = cont
            except Exception as e:
                print ( "error when trying to load pickle file %s: %s" % ( cont, e ) )
                pfile = None
    # print ( "[walkingWorker] called main with cont='%s', pfile='%s'." % ( cont, pfile ) )
    import socket, copy
    # print ( "[walkingWorker] I am already inside the python script! Hostname is", socket.gethostname()  )
    from combinations import walker
    walkers = []
    for i in range(nmin,nmax):
        if pfile is None:
            print ( "[walkingWorker] starting %d with cheatcode %d" % ( i, cheatcode ) )
            w = walker.RandomWalker( walkerid=i, dump_training = True, 
                                     dbpath = dbpath, cheatcode = cheatcode  )
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
    argparser.add_argument ( '-n', '--nmin', nargs='?', help='minimum worker id [0]',
                        type=int, default=40 )
    argparser.add_argument ( '-N', '--nmax', nargs='?', help='maximum worker id [10]',
                        type=int, default=90 )
    argparser.add_argument ( '-C', '--cheat', nargs='?', help='cheat code [0]',
                        type=int, default=0 )
    argparser.add_argument ( '-f', '--cont', help='continue with saved states [""]',
                        type=str, default="default" )
    args=argparser.parse_args()
    main( args.nmin, args.nmax, args.cont, cheatcode = args.cheat )
