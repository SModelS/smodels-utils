#!/usr/bin/env python3

import glob, os, subprocess, sys

def hasXSecs( filename ):
    with open ( filename, "rt" ) as f:
        lines=f.readlines()
        f.close()
    for line in lines:
        if line.startswith ( "XSEC" ):
            return True
    return False

def lock ( f ):
    if not os.path.exists ( f ):
        return
    if "/" in f:
        p1 = f.rfind("/")
        f = f[p1+1:]
    cmd = f"touch .{f}.lock"
    subprocess.getoutput ( cmd )

def unlock ( f ):
    if "/" in f:
        p1 = f.rfind("/")
        f = f[p1+1:]
    cmd = f"rm -rf .{f}.lock"
    subprocess.getoutput ( cmd )
    
def isLocked ( f ):
    if "/" in f:
        p1 = f.rfind("/")
        f = f[p1+1:]
    return os.path.exists ( f".{f}.lock" )

def addXSecs( dirname, pretend = False ):
    files = glob.glob( dirname+"T*slha" )
    ctr=0
    hasXS = 0
    locked = 0
    for f in files:
        if hasXSecs ( f ):
            hasXS += 1
            continue
        if isLocked ( f ):
            locked += 1
            continue
        else:
            ctr+=1
            if ctr < 40:
                cmd = f"../../smodels/smodelsTools.py xseccomputer -f {f} -8 -N -P -e 200000 -v info -c 1 -s 13.6 "
                pid = os.fork()
                if pid == 0:
                    lock ( f )
                    print ( "cmd", cmd )
                    o = ""
                    if not pretend:
                        o = subprocess.getoutput ( cmd )
                    print ( "o", o )
                    unlock ( f )
                    sys.exit()
    print ( f"{ctr}/{len(files)} processing, {hasXS} have xsecs, {locked} locked" )

if __name__ == "__main__":
    files = glob.glob ( "tmp*/" )
    for f in files:
        addXSecs( f, pretend = False )
