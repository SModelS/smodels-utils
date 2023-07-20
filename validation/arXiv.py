#!/usr/bin/env python3

""" stupid script that unifies all arxiv lines in convert.py, globalInfo.txt """

import glob, sys

files = glob.glob ( "../../smodels-database/*/*/*/convert.py" )
files += glob.glob ( "../../smodels-database/*/*/*/globalInfo.txt" )

for f in files:
    h = open ( f )
    lines = h.readlines()
    h.close()
    hasChanged = False
    for i,l in enumerate(lines):
        # arXiv:1308.1586v2 -> https://arxiv.org/abs/1809.05548
        if "arXiv" in l:
            newl = l.replace("arXiv:","https://arxiv.org/abs/" )
            lines[i]=newl
            hasChanged = True
            print ( f, newl )
    if hasChanged:
        h = open ( f, "wt" )
        for line in lines:
            h.write ( line )
        h.close()
