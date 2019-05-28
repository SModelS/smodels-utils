#!/usr/bin/env python3

import pickle, os, sys
from randomWalk import Model # RandomWalker
import IPython

picklefile = "best.pcl"
if len(sys.argv)>1:
    picklefile = sys.argv[1]

f=open(picklefile,"rb" )
hiscores = pickle.load(f)
f.close()
print ( "Check variable: hiscores" )
IPython.embed()
