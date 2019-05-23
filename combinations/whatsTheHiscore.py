#!/usr/bin/env python3

import pickle, os
from randomWalk import RandomWalker

def discuss ( walker, name ):
    print ( "Currently %s Z is: %.3f [%d/%d unfrozen particles] " % \
            (name, walker.Z, len(walker.unFrozenParticles()),len(walker.masses.keys()) ) )

f=open("hiscore.pcl","rb")
walker = pickle.load ( f )
f.close()
discuss ( walker, "highest" )
if not os.path.exists ( "oldhiscore.pcl" ):
    sys.exit()

f=open("oldhiscore.pcl","rb")
second = pickle.load ( f )
f.close()
discuss ( second, "second" )
