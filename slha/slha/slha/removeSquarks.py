#!/usr/bin/env python3

import subprocess
import numpy as np

for i in [ 1,2,3,4 ]:
    for p in [ 1, 2, -1, -2 ]:
        for j in [ 1, 2, 3, 4 ]:
            for q in [ 1, 2, -1, -2 ]:
                pid1=p*1000000+i*np.sign(p)
                pid2=q*1000000+j*np.sign(q)
                print ( pid1, pid2 )
                cmd = "./removeXSecs.py -p %d -q %d" % ( pid1, pid2 )
                subprocess.getoutput ( cmd )
