#!/usr/bin/env python3

""" correct the neutralino masses in T5GQ """

import glob

def correct ( filename ):
    print ( "correcting", filename )
    tokens = filename.split("_")
    N1 = int(tokens[3] )
    print ( "N1", tokens[3] )
    f=open ( filename, "rt" ) 
    lines = f.readlines()
    f.close()
    newname = "new.slha"
    newname = filename
    f=open ( newname, "wt" ) 
    for line in lines:
        if line.startswith("   1000022"):
            oldline = line
            line = f"   1000022     {int(N1)}.0     # ~chi_10\n"
            print ( "fixing", oldline, "->", line )
        f.write ( line )
    f.close()

def run():
    files = glob.glob("T5GQ*slha")
    for f in files:
        correct ( f )

run()
