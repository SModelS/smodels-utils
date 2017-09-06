#!/usr/bin/python

""" script that fetches slha tarballs from server """

from __future__ import print_function

import sys, urllib
import commands as C

def usage ():
    print ( "Usage: %s [Txname] [Txname]" % sys.argv[0] )
    print ( "       fetches slha tarballs from smodels server." )
    print ( "       if no arguments are given, fetch all." )
    sys.exit()

url="http://smodels.hephy.at/downloads/tarballs"

which=sys.argv[1:]
if len(which) == 0:
    """ ok, fetch the 'ls' file """
    d=urllib.urlopen ( "%s/ls" % url )
    for l in d.readlines():
        which.append ( l.replace("\n","" ) )

for ctr,w in enumerate(which):
    if w[0] != "T":
        usage()
    if w[-4:]!=".tar":
        which[ctr]=w+".tar"

for w in which:
    print ( "Trying to fetch %s ... " % w, end="" )
    a=C.getoutput ( "wget -a wget.log %s/%s" % ( url, w ) )
    if len(a):
        print ( "Error: %s" % a )
    else:
        print ( " done." )
