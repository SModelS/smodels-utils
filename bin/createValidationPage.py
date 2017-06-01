#!/usr/bin/python

""" very simple script that collects all validation plots in a simple 
    (local) validation html page """

from __future__ import print_function
import glob
    
db = "/home/walten/git/smodels-database/"
outfile = "newFormat"

if False:
    db = "/home/walten/git/branches/smodels-database/"
    outfile = "develop"

def copy():
    import commands
    www = "/var/www/walten/validation" 
    commands.getoutput ( "cp %s.html %s" % (outfile, www ) )
    return
    for i in [ "8TeV", "13TeV" ]:
        commands.getoutput ( "cp -r %s/%s %s/%s" % (db, i, www, outfile ) )

def write():
    html=open( outfile + ".html" ,"w")
    html.write ( "<html><body>\n" )
    html.write ( "<h1>Validation -- %s</h1>\n" % outfile )
    html.write ( "<table>\n" )
    files = glob.glob ( "%s/*/*/*/validation/*.png" % db )
    files.sort()
    for f in files:
        print f
        url = f.replace ( db, outfile+"/" )
        html.write ( "  <tr><td><img src=%s></img>\n" % url )
    html.write ( "</body></html>\n" )
    html.close()
    copy()

if __name__ == "__main__":
    write()
