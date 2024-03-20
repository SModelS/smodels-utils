#!/usr/bin/env python3

""" add xsecs to slha files """

import glob, os, subprocess, sys

def hasXSecs( filename ):
    with open ( filename, "rt" ) as f:
        lines=f.readlines()
        f.close()
    for line in lines:
        if line.startswith ( "XSEC" ):
            # check for 13 tev xsecs
            if " 1.30E+04 " in line or " 13000 " in line:
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

def addXSecs( dirname, pretend = False, parallel : bool = False ):
    files = [ dirname ]
    if os.path.isdir ( dirname ):
        files = glob.glob( dirname+"T*slha" )
    ctr=0
    hasXS = 0
    locked = 0
    for f in files:
        has = hasXSecs ( f )
        if has:
            print ( f"[addXSecs] skipping {f}: has xsecs" ) 
            hasXS += 1
            continue
        if isLocked ( f ):
            print ( f"[addXSecs] skipping {f}: is locked" ) 
            locked += 1
            continue
        else:
            print ( f"[addXSecs] computing for {f}" ) 
            ctr+=1
            if ctr < 40:
                cmd = f"../../smodels/smodelsTools.py xseccomputer -f {f} -8 -N -P -e 200000 -v info -c 1 -s 8 13 "
                pid = 0
                if parallel:
                    pid = os.fork()
                if pid == 0:
                    lock ( f )
                    print ( "cmd", cmd )
                    o = ""
                    if not pretend:
                        o = subprocess.getoutput ( cmd )
                    print ( "o", o )
                    unlock ( f )
                    if parallel:
                        sys.exit()
    # print ( f"{ctr}/{len(files)} processing, {hasXS} have xsecs, {locked} locked" )

if __name__ == "__main__":
    files = glob.glob ( "T*.slha" )
    # files = glob.glob ( "tmp*/" )
    for f in files:
        addXSecs( f, pretend = False, parallel = False )
