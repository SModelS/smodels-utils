#!/usr/bin/env python3

import subprocess
import sys
import glob
import random
import pyslha
import IPython

pretend = False
if len(sys.argv)>1 and sys.argv[1] in [ "-p", "--pretend" ]:
    pretend = True

files = glob.glob ( "T*slha" )
random.shuffle ( files )
# files = glob.glob ( "T5ZZ_1566_877_1_1566_877_1.slha" )
total = len (files)
ctr = 0

for f in files:
    has_nlo = False
    p = pyslha.readSLHAFile ( f )
    for k,xsecs in p.xsections.items():
        for x in xsecs.xsecs:
            order = x.qcd_order_str
            if "NL" in order:
                has_nlo=True
                break
    if not has_nlo:
        print  ("%s has only LO" % f )
        cmd = "~/git/smodels/smodelsTools.py xseccomputer -N -P -8 -O -f %s" % f
        if not pretend:
            subprocess.getoutput ( cmd )
        ctr += 1

print ( "%d/%d with LO only." % ( ctr, total ) )
