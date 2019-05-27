#!/usr/bin/env python3

import pickle, os
from randomWalk import Model # RandomWalker
from scipy import stats

def discuss ( model, name ):
    print ( "Currently %7s Z is: %.3f [%d/%d unfrozen particles] " % \
            (name, model.Z, len(model.unFrozenParticles()),len(model.masses.keys()) ) )

def detailedDiscussion ( model ):
    """ a detailed discussion of number 1 """
    p = 1. - stats.norm.cdf ( model.Z )
    print ( "Current winner: %.3f. p=%.2g [%d/%d unfrozen particles] " % \
            (model.Z, p, len(model.unFrozenParticles()),len(model.masses.keys()) ) )

def main():
    f=open("hiscore.pcl","rb")
    walkers = pickle.load ( f )
    f.close()
    keys = list ( walkers.keys() )
    keys.sort( reverse=True )
    names = { 0: "highest", 1: "second", 2: "third" }
    for c,k in enumerate(keys):
        sc = "%dth" % (c+1)
        if c in names.keys():
            sc = names[c]
        if c==0:
            detailedDiscussion ( walkers[k] )
        else:
            discuss ( walkers[k], sc )

if __name__ == "__main__":
    main()
