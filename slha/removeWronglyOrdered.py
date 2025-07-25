#!/usr/bin/env python3

""" remove all slha files with the wrong order """

import glob, copy, subprocess, argparse

def main():
    files = glob.glob("T*slha")
    pretend = False
    for f in files:
        tokens = f.split("_")
        masses = list ( map ( int, tokens[1:3] ) )
        hasEquals = False
        for ctr,m1 in enumerate(masses[:-1]):
            if m1 == masses[ctr+1]:
                print ( f"{f} has equals" )
                if True:
                    print ( "removing", masses )
                    cmd = f"rm {f}"
                    if not pretend:
                        subprocess.getoutput ( cmd )
        smasses = copy.deepcopy( masses)
        smasses.sort ( reverse=True )
        issorted = (smasses == masses )
        if not issorted:
            print ( "removing", masses )
            cmd = f"rm {f}"
            if not pretend:
                subprocess.getoutput ( cmd )

main()
