#!/usr/bin/env python3

import subprocess, os

def showPath ( path ):
    print ( f"show {path}" )
    if not os.path.exists ( path ):
        print ( f"{path}: does not exist" )
        return
    cmd = f"cd {path}; ln -s ~/git/protomodels/snippets/show_steps.py; ./show_steps.py; cd .."
    o = subprocess.getoutput ( cmd )
    lines = o.split()
    print ( f"{path}: {' '.join(lines[-2:])}" )

def show():
    for i in range(1,11):
        path = f"rundir_fakebg{i}_f10"
        showPath ( path )
    for i in range(1,11):
        path = f"rundir_fakebg{i}_f07"
        showPath ( path )
    for p in [ "rundir4", "rundir5", "rundir6", "rundir7" ]:
        showPath ( p )
    for p in [ "rundir_fake_ewk3", "rundir_fake_ewkoff3", "rundir_fake_stops3" ]:
        showPath ( p )
    o = subprocess.getoutput ( f"./printSimpleHiscoreList.py" )
    print ( o )

if __name__ == "__main__":
    show()
