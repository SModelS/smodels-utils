#!/usr/bin/env python3

import os
try:
    from torch import multiprocessing
except:
    import multiprocessing
from tools import helpers
from walker.randomWalker import RandomWalker

def _run ( walker, catchem, seed=None ):

    #Set random seed
    if seed is not None:
        helpers.seedRandomNumbers(seed)
    if not catchem:
        walker.walk()
        return
    try:
        walker.walk(catchem)
    except Exception as e:
        import time
        with open("exceptions.log","a") as f:
            f.write ( "time %s\n" % time.asctime() )
            f.write ( "walker %d threw: %s\n" % ( walker.walkerid, e ) )
            if hasattr ( walker.model, "currentSLHA" ):
                f.write ("slha file was %s\n" % walker.model.currentSLHA )
        import colorama
        print ( "%swalker %d threw: %s%s\n" % ( colorama.Fore.RED, walker.walkerid, e, colorama.Fore.RESET ) )

def startWalkers ( walkers, seed=None,  catchem=False):

    processes=[]
    for walker in walkers:
        p = multiprocessing.Process ( target=_run, args=( walker, catchem, seed ) )
        p.start()
        processes.append(p)
    for p in processes:
        p.join()


def main( nmin, nmax, cont,
          dbpath = "<rundir>/database.pcl",
          cheatcode = 0, dump_training = False, rundir=None, maxsteps = 10000,
          nevents = 100000, seed = None,  catchem=True ):
    """ a worker node to set up to run walkers
    :param nmin: the walker id of the first walker
    :param nmax: the walker id + 1 of the last walker
    :param cont: start with protomodels given in the pickle file 'cont'
    :param cheatcode: in case we wish to start from a cheat model
    :param dump_training: dump training data for the NN
    :param rundir: overrride default rundir, if None use default
    :param maxsteps: maximum number of steps to be taken
    :param nevents: number of MC events when computing cross-sections
    :param seed: random seed number (optional)
    :param catchem: If True will catch the exceptions and exit.
    """

    if rundir != None and "<rundir>" in dbpath:
        dbpath=dbpath.replace("<rundir>","%s/" % rundir )
    pfile, states = None, None
    if cont == "default":
        cont = "%s/states.dict" % rundir
        if not os.path.exists ( cont ):
            cont = "default"
    if cont.lower() not in [ "none", "" ]:
        if not os.path.exists ( cont ):
            print ( "[walkingWorker] error: supplied a save states file ,,%s'', but it doesnt exist" % cont )
        else:
            import pickle
            try:
                if cont.endswith ( ".dict" ):
                    with open( cont, "rt" ) as f:
                        states = eval ( f.read() )
                else:
                    with open ( cont, "rb" ) as f:
                        states = pickle.load ( f )
                pfile = cont
            except Exception as e:
                print ( "error when trying to load pickle file %s: %s" % ( cont, e ) )
                pfile = None
    # print ( "[walkingWorker] called main with cont='%s', pfile='%s'." % ( cont, pfile ) )

    # print ( "[walkingWorker] I am already inside the python script! Hostname is", socket.gethostname()  )
    walkers = []
    for i in range(nmin,nmax):
        if pfile is None:
            print ( "[walkingWorker] starting %d @ %s with cheatcode %d" % ( i, rundir, cheatcode ) )
            w = RandomWalker( walkerid=i, nsteps = maxsteps, dump_training = dump_training,
                                     dbpath = dbpath, cheatcode = cheatcode, rundir = rundir,
                                     nevents = nevents )
            walkers.append ( w )
        elif pfile.endswith(".pcl"):
            nstates = len(states )
            ctr = i % nstates
            print ( "[walkingWorker] fromModel %d: loading %d/%d" % ( i, ctr, nstates ) )
            w = RandomWalker.fromProtoModel ( states[ctr], "aggressive",
                    walkerid = i, nsteps = maxsteps, dump_training=dump_training, expected = False,
                    dbpath = dbpath, rundir = rundir )
            walkers.append ( w )
        else:
            nstates = len(states )
            ctr = i % nstates
            print ( "[walkingWorker] fromDict %d: loading %d/%d" % ( i, ctr, nstates ) )
            w = RandomWalker.fromDictionary ( states[ctr], nsteps = maxsteps, 
                    strategy = "aggressive", walkerid = i, dump_training=dump_training, 
                    dbpath = dbpath, expected = False, rundir = rundir, nevents = nevents )
            walkers.append ( w )
    startWalkers ( walkers, seed=seed, catchem=catchem )
