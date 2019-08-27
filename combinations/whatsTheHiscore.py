#!/usr/bin/env python3

import pickle, os, fcntl
from randomWalk import Model # RandomWalker
from scipy import stats

def discuss ( model, name ):
    print ( "Currently %7s Z is: %.3f [%d/%d unfrozen particles, %d predictions] " % \
            (name, model.Z, len(model.unFrozenParticles()),len(model.masses.keys()),len(model.bestCombo) ) )

def discussBest ( model, detailed ):
    """ a detailed discussion of number 1 """
    p = 1. - stats.norm.cdf ( model.Z )
    print ( "Current           best: %.3f, p=%.2g [%d/%d unfrozen particles, %d predictions] " % \
            (model.Z, p, len(model.unFrozenParticles()),len(model.masses.keys()),len(model.bestCombo) ) )
    if detailed:
        print ( "Solution was found in step #%d" % model.step )
        for i in model.bestCombo:
            print ( "  prediction in best combo: %s (%s)" % ( i.analysisId(), i.dataType() ) )

def compile():
    """ compile the list from individual hi*pcl """
    import glob
    files = glob.glob ( "hi?.pcl" ) + glob.glob ( "hi??.pcl" )
    allmodels,alltrimmed=[],[]
    for f in files:
        with open( f,"rb+") as f:
            fcntl.flock( f, fcntl.LOCK_EX )
            models = pickle.load ( f )
            trimmed = pickle.load ( f )
            fcntl.flock( f, fcntl.LOCK_UN )
            allmodels += models
            alltrimmed += trimmed
    return allmodels, alltrimmed

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='Lists the current hiscores.' )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file with hiscores [None]. If None, compile from hi*pcl',
            type=str, default=None )
    argparser.add_argument ( '-n', '--nmax',
            help='maximum number of entries to show [20]',
            type=int, default=20 )
    argparser.add_argument ( '-d', '--detailed',
            help='detailed descriptions', action="store_true" )
    args = argparser.parse_args()
    if args.picklefile == None:
        models,trimmed = compile()
    else:
        with open(args.picklefile,"rb+") as f:
            fcntl.flock( f, fcntl.LOCK_EX )
            models = pickle.load ( f )
            trimmed = pickle.load ( f )
            fcntl.flock( f, fcntl.LOCK_UN )
    names = { 0: "highest", 1: "second", 2: "third" }
    for c,model in enumerate(models):
        if c >= args.nmax:
            break
        if model == None:
            break
        sc = "%dth" % (c+1)
        if c in names.keys():
            sc = names[c]
        if c==0:
            discussBest ( model, args.detailed )
        else:
            discuss ( model, sc )

if __name__ == "__main__":
    main()
