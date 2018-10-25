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
not_lo, not_nlo = 0, 0

for f in files:
    has_lo  = False
    has_nlo = False
    p = pyslha.readSLHAFile ( f )
    for k,xsecs in p.xsections.items():
        for x in xsecs.xsecs:
            order = x.qcd_order_str
            if "LO" in order or "Born" in order: ## FIXME why??
                has_lo = True
            if "NL" in order:
                has_nlo=True
                break
    if not has_nlo:
        if not has_lo:
            print ( "%s has neither LO nor NLO" % f )
            not_lo += 1
        else:
            print  ("%s has only LO" % f )
            cmd = "~/git/smodels/smodelsTools.py xseccomputer -N -P -8 -O -f %s" % f
            if not pretend:
                a = subprocess.getoutput ( cmd )
                print ( a )
            not_nlo += 1

print ( "%d/%d with NLL." % ( total - not_lo - not_nlo, total ) )
print ( "%d/%d with LO only." %  ( not_nlo, total ) )
print ( "%d/%d with no xsecs." % ( not_lo, total ) )
