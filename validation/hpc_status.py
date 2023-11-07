#!/usr/bin/env python3

""" print the overall status of a validation run, 
    mostly intended for running on HPC """
    
import glob, os, time
from typing import Tuple

def statusOneValidation( directory : os.PathLike ) -> Tuple:
    slhas = glob.glob ( os.path.join ( directory, "*slha" ) )
    if not os.path.exists ( os.path.join ( directory, "results" ) ):
        return 0,0
    results = glob.glob ( os.path.join ( directory, "results", "T*py" ) )
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
    print ( f"{directory}  {analysis+':'+txname:30s} {len(results)}/{len(slhas)}" )
    return len(results),len(slhas)

def globalStatus():
    dirs = glob.glob ( "_V*" )
    dirs += glob.glob ( "tmp*" )
    totslha,totresult=0,0
    for d in dirs:
        results,slhas=statusOneValidation ( d )
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
