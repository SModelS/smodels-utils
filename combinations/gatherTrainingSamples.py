#!/usr/bin/env python3

import gzip, glob, pickle

def write( alsoZeroes = False ):
    """
    :param alsoZeroes: write out even if Z=0.
    """
    print ( "gathering files, include zeroes in Z? %s" % alsoZeroes )
    files = glob.glob ( "training_*.gz" ) 
    All = []
    for fname in files:
        print ( "gathering file %s" % fname )
        with gzip.open ( fname, "r" ) as f:
            lines = f.readlines()
            for line in lines:
                evaled = eval(line)
                if alsoZeroes:
                    All.append ( line )
                else:
                    if evaled["Z"]>0.:
                        All.append ( line )
    with open ( "training.pcl", "wb" ) as g:
        for line in All:
            pickle.dump ( eval(line), g, pickle.HIGHEST_PROTOCOL )
    print ( "[gatherTrainingSamples] wrote %d lines" % len(All) )

def read():
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
    import argparse
    argparser = argparse.ArgumentParser(
            description='collect the training samples into one big pickle file' )
    argparser.add_argument ( '-r', '--read',
            help='read and check training.pcl, instead of producing it', 
            action="store_true" )
    args = argparser.parse_args()
    if args.read:
        read()
    else:
        write()
