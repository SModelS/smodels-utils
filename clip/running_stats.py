#!/usr/bin/env python3

""" FIXME should rename, contains all the helpers to interact efficiently with 
slurm
"""

import glob, stat, os, time, subprocess, colorama

def cancelJobsByString ( text : str ):
    """ cancel jobs that have text in their job names """
    print ( f"cancel all jobs that have {text} in their names." )
    o = subprocess.getoutput ( f"slurm q | grep {text}" )
    lines = o.split("\n")
    jobids = []
    for line in lines:
        tokens = line.split()
        if len(tokens)==0:
            continue
        try:
            jobid = int(tokens[0])
            jobids.append ( jobid )
        except ValueError as e:
            pass
    cmd = f"scancel {' '.join(map(str,jobids))}"
    print ( f"scancel {' '.join(map(str,jobids))}" )
    o = subprocess.getoutput ( cmd )



def getRundir():
    # ret="/scratch-cbe/users/wolfgan.waltenbergerrundir/"
    ret="/scratch-cbe/users/wolfgan.waltenberger/rundir/"
    if os.path.exists ( "rundir.conf" ):
        with open ( "rundir.conf" ) as f:
            ret = f.read()
    return ret.strip()

def prettyPrint ( myset : set ):
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
    #if curctr > curbeg:
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
    if len(ret)>150:
        ret=ret[:147]+"..."
    return ret

def walker_stats():
    print ( )
    print ( "walker*log info:" )
    print ( "================" )
    rundir = getRundir()
    logs = glob.glob ( f"{rundir}/walker*log" )
    running, pending = set(), set()
    t0 = time.time()
    for log in logs:
        ds = t0 - os.stat ( log ).st_mtime # no of seconds in the past
        dh = ds / 3600. # number of hours in the past
        walkerp = log.find("walker" )
        lognr =  int ( log[walkerp+6:-4] )
        if lognr > 1000:
            continue
        if ds/60. > 180: ## in minutes
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
    print ( f"  stuck ({len(pending)}):", prettyPrint ( pending ) )
    print ( f"running ({len(running)}):", prettyPrint ( running ) )
    if len(notaccounted)>0:
        print ( f"not found ({len(notaccounted)}):", prettyPrint ( notaccounted ) )

def running_stats():
    lines = subprocess.getoutput ( "slurm q | head -n 3 | tail -n 2" ).split("\n")
    print ( )
    print ( "most recent jobs:" )
    print ( "=================" )
    for line in lines:
        tokens = list(filter(None,line.split(" ")))
        print ( "   ".join ( tokens ) )

    lines = subprocess.getoutput ( "slurm q | tail -n 2" ).split("\n")
    print ( )
    print ( "longest running jobs:" )
    print ( "=====================" )
    for line in lines:
        tokens = list(filter(None,line.split(" ")))
        print ( "   ".join ( tokens ) )

def count_jobs():
    #print ( "slurm q says:" )
    #print ( "=============" )
    pend = subprocess.getoutput ( "slurm q | grep PEND | wc -l" )
    try:
        pend = int (pend )
    except:
        pass
    running = subprocess.getoutput ( "slurm q | grep RUNNING | wc -l" )
    try:
        running= int ( running )
    except:
        pass
    lpend = "%s%s%s" % ( colorama.Fore.YELLOW, pend, colorama.Fore.RESET )
    lrun = "%s%s%s" % ( colorama.Fore.GREEN, running, colorama.Fore.RESET )
    ltot = "%s%s%s" % ( colorama.Fore.RED, pend+running, colorama.Fore.RESET )
    print ( "pending", lpend, "running", lrun, "total", ltot )
    remaining = subprocess.getoutput ( "slurm q | grep -v PEND | grep -v RUNNING | grep -v NODELIST | wc -l" )
    if int(remaining)>0:
        print ( "remaining", remaining )

def count_dupes():
    A = subprocess.getoutput ( "slurm q" )
    jobs = []
    for a in A.split("\n"):
        tokens = a.split(" ")
        T = ""
        for t in tokens:
            if "RUN" in t and "_" in t:
                T = t
        if "." in T:
            T=T[:T.find(".")]
        jobs.append ( T )
    for j in set(jobs):
        if jobs.count(j)>1:
            print ( "job",j,"#",jobs.count(j) )

if __name__ == "__main__":
    #count_dupes()
    count_jobs()
    running_stats()
