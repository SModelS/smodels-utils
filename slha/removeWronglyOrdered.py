#!/usr/bin/env python3

""" remove all slha files with the wrong order """

import glob, copy, subprocess

def main():
    files = glob.glob("T*slha")
    for f in files:
        tokens = f.split("_")
        masses = list ( map ( int, tokens[1:4] ) )
        smasses = copy.deepcopy( masses)
        smasses.sort ( reverse=True )
        issorted = (smasses == masses )
        print ( masses, issorted )
        if not issorted:
            cmd = "rm %s" % f
            subprocess.getoutput ( cmd )

main()
