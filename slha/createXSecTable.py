#!/usr/bin/env python3

""" simple script to create cross section table from
list of files. """

import glob, pyslha

def createTable ( fname : str = "TRV1*slha" ):
    files = glob.glob ( fname )
    values = {}
    for f in files:
        pf = pyslha.readSLHAFile ( f )
        tokens = f.split("_")
        mass = int ( tokens[1] )
        xsecs = list ( pf.xsections.values() )
        xsec = xsecs[0].xsecs[0].value
        values[mass]=xsec
    masses = list ( values.keys() )
    masses.sort()
    g = open ( "xsecs.txt", "wt" )
    g.write ( "# created with createXSecTable.py\n" )
    for m in masses:
        g.write ( f"{m:4d} {values[m]}\n" )
        print ( f"{m:4d} {values[m]}" )

if __name__ == "__main__":
    createTable ( )
