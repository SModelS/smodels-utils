#!/usr/bin/env python3

""" print the overall status of a validation run, 
    mostly intended for running on HPC """
    
import glob, os, time, colorama
from typing import Tuple, Dict

def getAnalysisTxName ( directory : os.PathLike ):
    parfile = os.path.join ( directory, "results", "parameter.ini" )
    with open ( parfile, "rt" ) as h:
        lines = h.readlines()
        h.close()
        analysis="unknown"
        txname="unknown"
        for line in lines:
            if "analyses" in line:
                analysis = line.replace("analyses","").replace("=","").strip()
            if "txnames" in line:
                txname = line.replace("txnames","").replace("=","").strip()
    return analysis,txname

def statusOneValidation( directory : os.PathLike, D : Dict ) -> Tuple:
    slhas = glob.glob ( os.path.join ( directory, "*slha" ) )
    if not os.path.exists ( os.path.join ( directory, "results" ) ):
        return 0,0
    results = glob.glob ( os.path.join ( directory, "results", "T*py" ) )
    analysis,txname = getAnalysisTxName ( directory )
    pre,post="",""
    if len(results)==0:
        pre,post=colorama.Fore.RED,colorama.Fore.RESET
    if len(results)==len(slhas):
        pre,post=colorama.Fore.GREEN,colorama.Fore.RESET
    jobid="          "
    if directory in D:
        jobid=f"({D[directory]})"
    print ( f"{directory}{jobid}  {analysis+':'+txname:30s} {pre}{len(results)}/{len(slhas)}{post}" )
    return len(results),len(slhas)

def sort ( dirs : list ) -> list:
    tmp = {}
    for d in dirs:
        analysis,txname = getAnalysisTxName ( d )
        tmp[analysis+txname]=d
    keys = list ( tmp.keys() )
    keys.sort()
    ret=[]
    for k in keys:
        ret.append ( tmp[k] )
    return ret

def oldsort ( dirs : list ) -> list:
    tmp = {}
    for d in dirs:
        timestamp = os.stat ( d ).st_mtime
        while timestamp in tmp.keys():
            timestamp += 1
        tmp[timestamp]=d
    keys = list ( tmp.keys() )
    keys.sort()
    ret=[]
    for k in keys:
        ret.append ( tmp[k] )
    return ret

def getJobIds() -> Dict:
    import subprocess
    o = subprocess.getoutput ( "slurm q | grep _V" )
    lines = o.split("\n")
    D={}
    for line in lines:
        tokens = line.split()
        jobid = int(tokens[0])
        tmpf = tokens[2][:-3]
        D[tmpf]=jobid
    return D

def globalStatus():
    D=getJobIds()
    dirs = glob.glob ( "_V*" )
    dirs += glob.glob ( "tmp*" )
    dirs = sort ( dirs )
    totslha,totresult=0,0
    for d in dirs:
        results,slhas=statusOneValidation ( d, D )
        totslha+=slhas
        totresult+=results
    ratio = totresult/totslha
    print ()
    if os.path.exists ( "previous.txt" ):
        with open ( "previous.txt", "rt" ) as h:
            print( h.read().strip() )
    print ( f"                   {len(dirs)} total: {totresult}/{totslha} {ratio*100:.2f}%" )
    previous ( totresult, totslha, len(dirs) )

def previous ( totresult : int, totslha : int, ndirs : int ):
    with open ( "previous.txt", "wt" ) as h:
        ratio = totresult/totslha
        h.write ( f"{time.asctime()} {ndirs}: {totresult}/{totslha} {ratio*100:.2f}%\n" )
        h.close()

if __name__ == "__main__":
    globalStatus()
