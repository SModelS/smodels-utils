#!/usr/bin/env python3

"""
.. module:: sparticleNames
        :synopsis: assign sparticle names to pids ( 1000021 <-> ~g or Xg, ... ),
        pids to names, categorizes particles, etc.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function
import sys, os
sys.path.insert(0,"../../../" )
sys.path.insert(0,"/scratch-cbe/users/wolfgan.waltenberger/git/" )

from protomodels.ptools.sparticleNames import SParticleNames

if __name__ == "__main__":
    """ as a script, we simply print out the paths """
    print ( "sparticle names" )
    namer = SParticleNames()
    ctr=0
    f=open("index.html","wt" )
    f.write ( "<html><body>\n" )
    for (key,value) in namer.ids.items():
       ctr+=1
       print ()
       line = "pid %d: %s" % ( key, namer.htmlName ( key ) )
       print ( line )
       print ()
       f.write ( line + "<br>\n" )
    f.close()
       # print ( "%8d %8s   |" % (key,value), end="" )
       #if ctr==3:
       #  print ()
       #  ctr=0
