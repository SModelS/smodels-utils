#!/usr/bin/env python3

import glob, stat, os, time, subprocess

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
    if curctr > curbeg:
        seqs.append ( (curbeg, curctr) )
    ret = ""
    seqs.sort()
    for tseq in seqs:
        dt = tseq[1]-tseq[0]
        if dt == 0:
            ret += "%d," % tseq[0]
        elif dt == 1:
            ret += "%d,%d,"% ( tseq[0], tseq[1] )
        else:
            ret += "%d-%d," % ( tseq[0], tseq[1] )
    if len(ret)>1:
        ret = ret[:-1]
    if len(ret)==0:
        ret="none"
    return ret

def running_stats():
    print ( )
    print ( "walker*log info:" )
    print ( "================" )
    rundir = getRundir()
    logs = glob.glob ( "%s/walker*log" % rundir )
    running, pending = set(), set()
    t0 = time.time()
    for log in logs:
        ds = os.stat ( log ).st_mtime - t0 # no of seconds in the past
        dh = ds / 3600. # number of hours in the past
        walkerp = log.find("walker" )
        lognr =  int ( log[walkerp+6:-4] )
        if ds < -900:
            pending.add ( lognr )
        else:
            running.add ( lognr )
    un = running.union(pending)
    all = []
    if len(un)>0:
        all = range ( 0, max(un) )
    notaccounted=set()
    for i in all:
        if not i in running and not i in pending:
            notaccounted.add ( i )
    print ( "    stuck (%d):" % len(pending), prettyPrint ( pending ) )
    print ( "  running (%d):" % len(running), prettyPrint ( running ) )
    print ( "not found (%d):" % len(notaccounted), prettyPrint ( notaccounted ) )

def count_jobs():
    print ( "slurm q says:" )
    print ( "=============" )
    pend = subprocess.getoutput ( "slurm q | grep PEND | wc -l" )
    print ( "pending", pend )
    running = subprocess.getoutput ( "slurm q | grep RUNNING | wc -l" )
    print ( "running", running )
    remaining = subprocess.getoutput ( "slurm q | grep -v PEND | grep -v RUNNING | grep -v NODELIST | wc -l" )
    if int(remaining)>0:
        print ( "remaining", remaining )

if __name__ == "__main__":
    count_jobs()
    running_stats()
