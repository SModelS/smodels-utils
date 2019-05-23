#!/usr/bin/env python3

import pickle
from randomWalk import RandomWalker

f=open("hiscore.pcl","rb")
walker = pickle.load ( f )
f.close()
print ( "Currently highest Z is: %.2f" % walker.Z )
