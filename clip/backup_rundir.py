#!/usr/bin/env python3

import sys, os, subprocess

def mkdir ( path : os.PathLike ):
    if not os.path.exists ( path ):
        os.mkdir ( path )

def execute ( cmd : str ):
    o = subprocess.getoutput ( cmd )
    print ( f"[backup_rundir] {cmd} {o}" )

def backup( path ):
    bu_path = f"/groups/hephy/pheno/ww/production/{path}"
    print ( f"[backup_rundir] backing up '{path}' to '{bu_path}'" )
    mkdir ( bu_path ) 
    for fname in [ "logs", "Pmodels", "dictfiles", "all_hiscores", "*.dict" ]:
        cmd = f"cp -r {path}/{fname} {bu_path}"
        execute ( cmd )

def backup_all():
    dirs = [ "rundir4", "rundir5", "rundir6", "rundir7", "rundir_fake_ewk3", \
             "rundir_fake_stops3", "rundir_fake_ewkoff3" ]
    for i in range(1,10):
        dirs.append ( f"rundir_fakebg{i}_f10" )
        dirs.append ( f"rundir_fakebg{i}_f07" )
    for d in dirs:
        backup ( d )

if __name__ == "__main__":
    backup_all()
    """
    if len(sys.argv)<2:
        print ( f"[backup_rundir] syntax: backup_rundir.py [directory]" )
        return
    path = sys.argv[1]
    backup( path)
    """
