#!/usr/bin/python

""" very simple script that collects all validation plots in a simple 
    (local) validation html page """

import glob

def write():
    db = "/home/walten/git/smodels-database/"
    html=open("index.html","w")
    html.write ( "<html><body>\n" )
    html.write ( "<h1>Validation</h1>\n" )
    html.write ( "<table>\n" )
    files = glob.glob ( "%s/*/*/*/validation/*.png" % db )
    for f in files:
        print f
        html.write ( "  <tr><td><img src=%s></img>\n" % f )
    html.write ( "</body></html>\n" )
    html.close()

if __name__ == "__main__":
    write()
