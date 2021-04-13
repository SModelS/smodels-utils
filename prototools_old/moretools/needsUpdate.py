#!/usr/bin/env python3

import sys, os, glob, subprocess

rundir = "/scratch-cbe/users/wolfgan.waltenberger/"

def discuss ( d ):
    if not os.path.exists ( f"{d}/states.dict" ):
        return
    ms = os.stat ( f"{d}/states.dict" ).st_mtime
    files = glob.glob ( f"{d}/walker*log" )
    for f in files:
        if "walker0.log" in f:
            continue
        mt = os.stat ( f ).st_mtime
        fshort = f.replace ( f"{rundir}/rundir.","")
        if mt > ms:
            print ( f"{d} needs update" )
            break

def main():
    Dirs = glob.glob ( f"{rundir}rundir.*" )
    Dirs.sort()
    for d in Dirs:
        discuss ( d )

main()
