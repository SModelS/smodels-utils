#!/usr/bin/python

""" script that fetches slha tarballs from server """

from __future__ import print_function

import sys, urllib, os, os.path
try:
    import commands as C ## python2
except Exception as e:
    import subprocess as C

def usage ():
    print ( f"Usage: {sys.argv[0]} [-h|--help] [Txname] [Txname]" )
    print ( "       fetches slha tarballs from smodels server." )
    print ( "       if no arguments are given, fetch all." )
    sys.exit()

def fetch ( which ):
    url="http://smodels.hephy.at/downloads/tarballs"

    if len(which) == 0:
        """ ok, fetch the 'ls' file """
        d=urllib.urlopen ( f"{url}/ls" )
        for l in d.readlines():
            which.append ( l.replace("\n","" ) )

    for ctr,w in enumerate(which):
        if w[0] != "T":
            usage()
        if w[-4:]!=".tar":
            which[ctr]=w+".tar"

    for w in which:
        print ( f"Trying to fetch {w} ... ", end="" )
        destdir = os.path.dirname ( __file__ )
        cmd = f"wget -a wget.log -O {destdir}/{w} {url}/{w}"        
        #print ( cmd, "argv0=", destdir  )
        a=C.getoutput ( cmd )
        if len(a):
            print ( f"Error: {a}" )
            return False
        else:
            print ( " done." )
            return True

if __name__ == "__main__":
    which=sys.argv[1:]
    if len(which) and which[0] in [ "-h", "--help" ]:
        usage()
    fetch ( which )
