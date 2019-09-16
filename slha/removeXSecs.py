#!/usr/bin/env python3

""" remove all cross sections from files """

import glob

def main():
    files = glob.glob("*.slha" )
    for fl in files:
        print ( "cleaning %s" % fl )
        f = open ( fl, "rt" )
        lines = f.readlines()
        f.close()
        g = open ( fl, "wt" )
        for line in lines:
            if "XSECTION" in line:
                break
            g.write ( line )

main()
