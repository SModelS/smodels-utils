#!/usr/bin/env python3

import pickle, os
from randomWalk import Model # RandomWalker

def discuss ( walker, name ):
    print ( "Currently %s Z is: %.3f [%d/%d unfrozen particles] " % \
            (name, walker.Z, len(walker.unFrozenParticles()),len(walker.masses.keys()) ) )

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
    discuss ( walkers[k], sc )
