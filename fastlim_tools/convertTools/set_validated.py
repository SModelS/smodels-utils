#!/usr/bin/python

import os
import sys
import commands

def correct  ( filename, value ):
    old = filename + ".old"
    cmd = "cp %s %s" % ( filename, old )
    commands.getoutput ( cmd )
    with open( old ) as f:
        with open ( filename, "w" ) as g:
            lines = f.readlines()
            for l in lines:
                if l == "" or l == "\n": continue
                if "validated: " in l:
                    g.write ( "validated: %s\n" % value )
                else:
                    g.write ( "%s" % l )
    cmd = "rm %s" % old
    commands.getoutput ( cmd )
    print filename

def run ( value ):
    for root, dirs, files in os.walk("."):
        for f in files:
            if f[0]=="T" and f[-4:] == ".txt":
                filename =os.path.join ( root, f )
                correct ( filename, value )

value=sys.argv[1]
run ( value )
