#!/usr/bin/env python3

import gzip, glob, pickle, sys, os

def setup():
    # codedir = "/mnt/hephy/pheno/ww/git/"
    codedir = "/scratch-cbe/users/wolfgan.waltenberger/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/protomodels/" % codedir )
    # os.chdir ( "/mnt/hephy/pheno/ww/git/smodels-utils/protomodels" )
    # rundir = "/mnt/hephy/pheno/ww/rundir"
    rundir = "/scratch-cbe/users/wolfgan.waltenberger/rundir/"
    if os.path.exists ( "./rundir.conf" ):
        with open ( "./rundir.conf" ) as f:
            rundir = f.read().strip()
    os.chdir ( rundir )
    return rundir

def write( rundir, nmax, alsoZeroes = False ):
    """
    :param alsoZeroes: write out even if Z=0.
    """
    print ( "gathering files, include zeroes in Z? %s" % alsoZeroes )
    files = glob.glob ( "training_*.gz" ) 
    All = []
    brk = False
    for fname in files:
        if brk:
            break
        print ( "gathering file %s" % fname )
        try:
            with gzip.open ( fname, "r" ) as f:
                lines = f.readlines()
                for line in lines:
                    evaled = eval(line)
                    if alsoZeroes:
                        All.append ( line )
                    else:
                        if evaled["Z"]>0.:
                            All.append ( line )
                    if len(All) >= nmax:
                        brk = True
                        break
        except ( EOFError, OSError ) as e:
            print ( "skipped %s: %s" % ( fname, e ) )
    with open ( "%s/training.pcl" % rundir, "wb" ) as g:
        for line in All:
            pickle.dump ( eval(line), g, pickle.HIGHEST_PROTOCOL )
    print ( "[gatherTrainingSamples] wrote %d lines" % len(All) )

def read( rundir ):
    with open ( "training.pcl", "rb" ) as g:
        ctr=0
        try:
            while True:
                d = pickle.load ( g )
                if False: # ctr == 0:
                    print ( "d", d )
                ctr+=1
        except EOFError:
            pass
        print ( "[gatherTrainingSamples] found %d lines" % ctr )


if __name__ == "__main__":
    rundir = setup()
    import argparse
    argparser = argparse.ArgumentParser(
            description='collect the training samples into one big pickle file' )
    argparser.add_argument ( '-n', '--nmax',
            help='maximum number of entries to collect. 0 means all. [0]',
            type=int, default=0 )
    argparser.add_argument ( '-r', '--read',
            help='read and check training.pcl, instead of producing it', 
            action="store_true" )
    args = argparser.parse_args()
    if args.read:
        read( rundir )
    else:
        write( rundir, args.nmax, alsoZeroes=False )
