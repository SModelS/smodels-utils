#!/usr/bin/env python3

""" remove all T* folders that appear wrongly ordered """

import glob, os, sys, subprocess

def correctlyOrdered ( numbers ):
    lastN = 999999
    for n in numbers:
        if n > lastN:
            return False
        lastN = n
    return True

def run():
    files = glob.glob ( "T*_*jet*" )
    for f in files:
        p = f.find("jet")
        string = f[p+4:]
        numbers = list ( map ( int, string.split("_") ) )
        cO = correctlyOrdered(numbers)
        if cO == False:
            cmd = "rm -r %s" % f
            print ( cmd )
            subprocess.getoutput ( cmd )

run()
