#!/usr/bin/env python3

import sys, os, subprocess

def mkdir ( path : os.PathLike ):
    if not os.path.exists ( path ):
        os.mkdir ( path )

def execute ( cmd : str ):
    o = subprocess.getoutput ( cmd )
    print ( f"[backup_rundir] {cmd} {o}" )

def backup():
    if len(sys.argv)<2:
        print ( f"[backup_rundir] syntax: backup_rundir.py [directory]" )
        return
    path = sys.argv[1]
    bu_path = f"/groups/hephy/pheno/ww/production/{path}"
    print ( f"[backup_rundir] backing up '{path}' to '{bu_path}'" )
    mkdir ( bu_path ) 
    for fname in [ "logs", "Pmodels", "dictfiles", "all_hiscores", "*.dict" ]:
        cmd = f"cp -r {path}/{fname} {bu_path}"
        execute ( cmd )

if __name__ == "__main__":
    backup()
