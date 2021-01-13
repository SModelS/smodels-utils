#!/usr/bin/env python3

""" remove the slurm log files of the walkers before a certain slurm job id """

import glob, os, fire

def remove ( before ):
    files = glob.glob ( "walk-*.out" )
    for f in files:
        nr = f.replace("walk-","").replace(".out","")
        nr = int ( nr )
        if nr < before:
            os.unlink ( f )

def grep ( pattern ):
    files = glob.glob ( "walk-*.out" )
    for f in files:
        with open ( f, "rt" ) as h:
            txt = h.read()
            if pattern in txt:
                print ( "removing", f )
                os.unlink ( f )

if __name__ == "__main__":
    fire.Fire ( { "remove": remove, "grep": grep } )
#    before = 12049757
#    remove ( before )
