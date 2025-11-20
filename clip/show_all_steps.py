#!/usr/bin/env python3

import subprocess

def showPath ( path ):
    o = subprocess.getoutput ( f"cd {path}; ./show_steps.py; cd .." )
    lines = o.split()
    print ( f"{path}: {' '.join(lines[-2:])}" )

def show():
    for i in range(1,11):
        path = f"rundir_fakebg{i}_f10"
        showPath ( path )
    for i in range(1,11):
        path = f"rundir_fakebg{i}_f07"
        showPath ( path )
    for p in [ "rundir4", "rundir5", "rundir6" ]:
        showPath ( p )

if __name__ == "__main__":
    show()
