#!/usr/bin/python

""" script that pushes slha tarballs back to server """

from __future__ import print_function

import sys, os, glob
import commands as C

def usage ():
    print ( f"Usage: {sys.argv[0]} [Txname] [Txname]" )
    print ( "       pushes slha tarballs to smodels server." )
    print ( "       if no arguments are given, pushes all that are found in working directory." )
    sys.exit()

which=sys.argv[1:]
if len(which) == 0:
    """ ok, push all found in working directory. """
    which=glob.glob ( "*.tar" )

for ctr,w in enumerate(which):
    if w[-4:]!=".tar": which[ctr]+=".tar"


cmd=f"scp {str(' '.join(which))} smodels.hephy.at:/var/www/downloads/tarballs"
print ( cmd )
C.getoutput ( cmd )
