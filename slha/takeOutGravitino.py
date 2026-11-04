#!/usr/bin/env python3

""" very simple script that replaces gravitinos (1000039) with neutralinos
    (LSP) """

import subprocess, glob
from pbase.constants import LSP

def sed ( fname ):
    f = open ( fname, "rt" )
    lines = f.readlines()
    f.close()
    newlines = []
    for line in lines:
        if "chi_10" in line:
            continue
        t = line.replace("1000039", str(LSP))
        newlines.append ( t )
    f = open ( fname, "wt" )
    for newl in newlines:
        f.write ( newl )
    f.close()

def takeOut ( tarball ):
    cmd = "rm T*slha"
    subprocess.getoutput ( cmd )
    cmd = f"tar xzvf {tarball}"
    subprocess.getoutput ( cmd )
    files = glob.glob ( "T*slha" )
    for f in files:
        sed ( f )
    cmd = f"tar czvf {tarball} T*slha"
    subprocess.getoutput ( cmd )

takeOut ( "TStauStauDisp.tar.gz" )
