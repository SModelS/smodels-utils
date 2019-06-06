#!/usr/bin/env python3

import pickle, os
from randomWalk import Model # RandomWalker
from scipy import stats

def discuss ( model, name ):
    print ( "Currently %7s Z is: %.3f [%d/%d unfrozen particles, %d predictions] " % \
            (name, model.Z, len(model.unFrozenParticles()),len(model.masses.keys()),len(model.bestCombo) ) )

def discussBest ( model ):
    """ a detailed discussion of number 1 """
    p = 1. - stats.norm.cdf ( model.Z )
    print ( "Current best: %.3f, p=%.2g [%d/%d unfrozen particles, %d predictions] " % \
            (model.Z, p, len(model.unFrozenParticles()),len(model.masses.keys()),len(model.bestCombo) ) )

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='Lists the current hiscores.' )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file with hiscores [hiscore.pcl]',
            type=str, default="hiscore.pcl" )
    argparser.add_argument ( '-d', '--detailed',
            help='detailed descriptions', action="store_true" )
    args = argparser.parse_args()
    f=open(args.picklefile,"rb")
    walkers = pickle.load ( f )
    f.close()
    names = { 0: "highest", 1: "second", 2: "third" }
    for c,model in enumerate(walkers):
        if model == None:
            break
        sc = "%dth" % (c+1)
        if c in names.keys():
            sc = names[c]
        if c==0:
            discussBest ( model )
        else:
            discuss ( model, sc )

if __name__ == "__main__":
    main()
