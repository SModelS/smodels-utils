#!/usr/bin/env python3    

""" simple pulls plot from stats file """

import numpy as np
import os, sys
from ptools.helpers import py_dumps

def readStats( resultsfolder : str ):
    ret={}
    import glob
    for fname in glob.glob ( f"{resultsfolder}/*" ):
        bname = os.path.basename ( fname )
        with open ( fname, "rt" ) as f:
            t = eval(f.read())
            ret[bname]=t
    return ret

def writeStats( stats ):
    ds = py_dumps ( stats ) + "\n"
    with open ( "stats", "wt" ) as f:
        f.write ( ds )

def getValues( what : str = "pull" ):
    filename = "stats"
    with open ( filename, "rt" ) as f:
        d = eval(f.read())
    ret = []
    for point, entry in d.items():
        for anaid, values in entry.items():
            if anaid == "params":
                continue
            if not what in values:
                continue
            pull = values[ what ]
            if abs(pull)<6:
                ret.append ( pull )
            print ( f"[{point}] {anaid:15s}: {pull:.2f}" )
    return ret

def plot( what : str ):
    d = getValues( what )
    from matplotlib import pyplot as plt
    import scipy
    plt.hist ( d, label="histo", bins=20 )
    stdnmx = np.arange(-3,3,.1)
    scale = len(d)
    stdnmy = [ scipy.stats.norm.pdf(x) * scale for x in stdnmx ]
    plt.plot ( stdnmx, stdnmy, c="black", linestyle="dotted",
               label="standard normal" )
    plt.xlabel ( "pulls" )
    plt.title ( f"pulls of {what.replace('pull','')} estimates" )
    outfile = f"{what}.png"
    plt.savefig ( outfile )
    from smodels_utils.plotting.mpkitty import timg
    timg ( outfile )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="plot the pulls")
    ap.add_argument('-w', '--what',
            help='what to plot [pull]',
            default = "pull", type = str )
    ap.add_argument( '-c', '--create_stats', help="create stats",
                     action="store_true" )
    ap.add_argument('-r', '--resultsfolder', help="folder for results [results]",
                     default="results", type = str )
    args = ap.parse_args()
    if True: # args.create_stats:
        stats = readStats( args.resultsfolder )
        writeStats ( stats )
        # sys.exit()
    plot( args.what )
