#!/usr/bin/python

""" very simple script that collects all validation plots in a simple 
    (local) validation html page. FIXME seems obsolete, check out 
    smodels-utils/validation/createWikiPage.py """

from __future__ import print_function
import glob
import time
import os, sys
import commands as C
    
def copy( db, outfile ):
    www = "/var/www/walten/validation" 
    a=C.getoutput ( "cp %s.html %s" % (outfile, www ) )
    print ( a )
    # return 
    for i in [ "8TeV", "13TeV" ]:
        C.getoutput ( "cp -r %s/%s %s/%s" % (db, i, www, outfile ) )

def write( db, outfile ):
    html=open( outfile + ".html" ,"w")
    html.write ( "<html><body>\n" )
    html.write ( "<h1>Validation -- %s, %s</h1>\n" % (outfile, time.asctime() ) )
    html.write ( "<table>\n" )
    files = glob.glob ( "%s/*/*/*/validation/*_pretty.pdf" % db )
    files.sort()
    for f in files:
        pngname = f.replace( ".pdf",".png" )
        if not os.path.exists ( pngname ):
            cmd = "convert %s %s" % (f, pngname ) 
            C.getoutput ( cmd )
        print (f)
        url = pngname.replace ( db, outfile+"/" )
        html.write ( "  <tr><td><img src=%s></img>\n" % url )
    html.write ( "</body></html>\n" )
    html.close()
    copy( db, outfile )

if __name__ == "__main__":
    print ( "Probably obsolete. checkout out ../validation/createWikiPage.py" )
    sys.exit()
    db = "/home/walten/git/smodels-database/"
    outfile = "newFormat"
    write( db, outfile )

    db = "/home/walten/git/branches/smodels-database/"
    outfile = "develop"
    write( db, outfile )
