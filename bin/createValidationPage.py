#!/usr/bin/python

""" very simple script that collects all validation plots in a simple 
    (local) validation html page """

from __future__ import print_function
import glob
import os
try:
    import commands as C
except:
    import subprocess as C

def write():
    home="/home/walten"
    db = "%s/git/smodels-database/" % home
    outfile = "newFormat.html"
    if False:
        db = "%s/git/branches/smodels-database/" % home
        outfile = "develop.html"
    html=open( outfile ,"w")
    html.write ( "<html><body>\n" )
    html.write ( "<h1>Validation: %s</h1>\n" % db )
    html.write ( "<table>\n" )
    files = glob.glob ( "%s/*/*/*/validation/*_pretty.pdf" % db )
    for f in files:
        pngversion = f.replace(".pdf",".png" )
        if not os.path.exists ( pngversion ):
            cmd = "convert %s %s" % ( f, pngversion )
            C.getoutput ( cmd )
        print ( f )
        html.write ( "  <tr><td><img src=%s></img>\n" % pngversion )
    html.write ( "</body></html>\n" )
    html.close()

if __name__ == "__main__":
    write()
