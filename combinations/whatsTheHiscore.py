#!/usr/bin/env python3

import pickle, os, fcntl
from randomWalk import Model # RandomWalker
from scipy import stats

def discuss ( model, name ):
    print ( "Currently %7s Z is: %.3f [%d/%d unfrozen particles, %d predictions] (walker #%d)" % \
            (name, model.Z, len(model.unFrozenParticles()),len(model.masses.keys()),len(model.bestCombo), model.walkerid ) )

def discussBest ( model, detailed ):
    """ a detailed discussion of number 1 """
    p = 1. - stats.norm.cdf ( model.Z )
    print ( "Current           best: %.3f, p=%.2g [%d/%d unfrozen particles, %d predictions] (walker #%d)" % \
            (model.Z, p, len(model.unFrozenParticles()),len(model.masses.keys()),len(model.bestCombo), model.walkerid ) )
    if detailed:
        print ( "Solution was found in step #%d" % model.step )
        for i in model.bestCombo:
            print ( "  prediction in best combo: %s (%s)" % ( i.analysisId(), i.dataType() ) )

def store ( models, trimmed, savefile, nmax ):
    """ store the best models in another hiscore file """
    from hiscore import Hiscore
    h = Hiscore ( 0, True, savefile )
    h.hiscores = models[:nmax]
    h.trimmed = trimmed[:nmax]
    h.save()


def sortByZ ( models ):
    models.sort ( reverse=True, key = lambda x: x.Z )
    return models

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
    allmodels = sortByZ ( allmodels )
    alltrimmed = sortByZ ( alltrimmed )
    return allmodels, alltrimmed

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='Lists the current hiscores.' )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file with hiscores [None]. If None, compile from hi*pcl',
            type=str, default=None )
    argparser.add_argument ( '-s', '--savefile',
            help='save compiled list to file [None]. If None, dont save',
            type=str, default=None )
    argparser.add_argument ( '-n', '--nmax',
            help='maximum number of entries to show. Also maximum number of entries to store, if -s [10]',
            type=int, default=10 )
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
    if args.savefile is not None:
        store ( models, trimmed, args.savefile, args.nmax )

if __name__ == "__main__":
    main()
