#!/usr/bin/env python3

""" this script does something very similar as plotDBDict,
namely it draws distributions of p-values, but for various 
fudge factors """

from matplotlib import pyplot as plt
import numpy as np
from chelpers import filterByAnaId, filterByBG, splitBySqrts, splitByCollaboration

def getPValues ( data : dict, statmodel : str ) -> dict:
    """ extract the right p-values from the entire entries """
    ret = {}
    for label, xdata in data.items():
        if not label in ret:
            ret[label] = []
        for entry in xdata:
            ret[label].append ( entry[ f"p_{statmodel}" ] )
    return ret

def countAnalyses ( data : list ) -> int:
    """
    :returns: the number of analyses
    """
    anaIds = set()
    for entry in data:
        id = entry["id"]
        labels = [ "-agg", "-multibin", "-strong", "-ewk" ]
        for label in labels:
            id = id.replace( label, "" )
        anaIds.add ( id )
    return len(anaIds)

def drawP ( args : dict ):
    """ draw a histogram of the pvalues 
    :args dictionary:
    :iparam fudge: draw for that fudge factor
    :iparam inputFile: path to input data create by createData.py
    :iparam outfile: png file
    :iparam statmodel: norm or lognorm for nuisances
    """
    with open(args["inputfile"],"rt") as f:
        data = eval(f.read())
    fudge = args["fudge"]
    statmodel = args["statmodel"]
    dropThese = []
    monojets = [ "CMS-EXO-20-004", "ATLAS-EXOT-2018-06" ]
    softleptons = [ "ATLAS-SUSY-2018-16-hino", "ATLAS-SUSY-2018-16" ]
    dEdx = [ "ATLAS-SUSY-2018-42" ]
    multiL = [ "ATLAS-SUSY-2017-03" ]
    Hbb = [ "CMS-SUS-20-004" ]
    dropThese = monojets + softleptons + dEdx + multiL + Hbb
    # dropThese = [] ## do not drop
    data = filterByAnaId ( data[fudge], dropThese )
    # data = data[fudge]
    data = filterByBG ( data, args["min_bg"] )
    nSRs = len(data)
    print ( f"[drawP] we are drawing {nSRs} entries" )
    splitdata = splitBySqrts ( data )
    splitdata = splitByCollaboration ( data )
    pvalues = getPValues ( splitdata, statmodel )
    allpvalues = [ x for v in pvalues.values() for x in v ]
    bins = np.linspace(0,1,args["nbins"]+1)
    plt.hist ( pvalues.values(), label = pvalues.keys(), 
               bins = bins, stacked=True )
    #for label, ps in pvalues.items():
    #    plt.hist ( ps, label = label, bins = bins )
    plt.legend()
    from chelpers import computeT
    Ts = computeT ( allpvalues, None )
    p=Ts["p"]
    plt.title ( f"Distribution of p-values, fudge={fudge:.1f} P={p:.2f}" )
    plt.xlabel ( "p-values" )
    plt.ylabel ( "occurrence [stacked]" )
    ax = plt.gca()
    nAnas = countAnalyses ( data )
    
    plt.text ( .67, -.12, 
            f"this plot contains {nSRs} SRs from {nAnas} analyses", 
            transform=ax.transAxes, c="grey", fontsize=7 )  
    outfile = args["outputfile"].replace("@@FUDGE@@",str(fudge))
    outfile = outfile.replace("@@STATMODEL@@",statmodel)
    plt.savefig ( outfile )
    from smodels_utils.plotting.mpkitty import timg
    timg ( outfile )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=
            "Produces p-values plots for a specific fudge factor")
    ap.add_argument('-i', '--inputfile',
            help='input file [data.dict]', default='data.dict' )
    ap.add_argument('-o', '--outputfile',
            help='output file [pvalues@@FUDGE@@.png]', 
            default='pvalues@@FUDGE@@_@@STATMODEL@@.png' )
    ap.add_argument('-s', '--statmodel',
            help='statmodel norm or lognorm [norm]', 
            default='norm' )
    ap.add_argument('-f', '--fudge', type=float,
            help='fudge factor [1.0]', default=1.0 )
    ap.add_argument('-m', '--min_bg', type=float,
            help='minimum number of expected background events [2.5]', default=2.5 )
    ap.add_argument('-n', '--nbins', type=int,
            help='number of bins in histogram [10]', default=10)
    args = ap.parse_args()
    drawP( vars(args) )
