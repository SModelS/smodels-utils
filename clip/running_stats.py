#!/usr/bin/env python3

import glob, stat, os, time

def getRundir():
    ret="/mnt/hephy/pheno/ww/rundir/"
    if os.path.exists ( "rundir.conf" ):
        with open ( "rundir.conf" ) as f:
            ret = f.read()
    return ret.strip()

def prettyPrint ( myset ):
    """ a pretty string listing the elements in myset """
    curbeg = 0
    curctr = 0
    seqs = []
    for i,el in enumerate ( myset ):
        if el == curbeg:
            continue
        if i == 0:
            curbeg = el
            curctr = el
            continue
        if el == curctr+1:
            curctr+=1
            continue
        seqs.append ( (curbeg,curctr) )
        curbeg = el
        curctr = el
    ret = ""
    for tseq in seqs:
        dt = tseq[1]-tseq[0]
        if dt == 0:
            ret += "%d," % tseq[0]
            continue
        if dt == 1:
            ret += "%d,%d,"% ( tseq[0], tseq[1] )
            continue
        ret += "%d-%d," % ( tseq[0], tseq[1] )
    if len(ret)>1:
        ret = ret[:-1]
    return ret

def main():
    rundir = getRundir()
    logs = glob.glob ( "%s/walker*log" % rundir )
    running, pending = set(), set()
    t0 = time.time()
    for log in logs:
        ds = os.stat ( log ).st_mtime - t0 # no of seconds in the past
        dh = ds / 3600. # number of hours in the past
        walkerp = log.find("walker" )
        lognr =  int ( log[walkerp+6:-4] )
        if dh < -2:
            pending.add ( lognr )
        else:
            running.add ( lognr )
    print ( "pending", prettyPrint ( pending ) )
    print ( "running", prettyPrint ( running ) )

main()
