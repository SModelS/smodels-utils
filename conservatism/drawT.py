#!/usr/bin/env python3

""" the script used to draw the test statistic of thie binned chi2
test as a function of the fudge factor """

from chelpers import computeT, filterByAnaId, filterByBG, splitByCollaboration,\
     splitBySqrts, splitBySqrtsAndCollaboration, splitByAnalysisGroups, \
     filterByAnaGroups
import numpy as np
from typing import Union

def getPValues ( data : list, statmodel : str = "norm" ) -> list:
    """ from a list of entries in data.dict, extract the p values 
    :param statmodel: norm or lognorm
    """
    ret = []
    for d in data:
        ret.append ( d[ f"p_{statmodel}" ] )
    return ret

def getHistoTestStats ( data : dict, bins : list ) -> dict:
    """ retrieve the test statistics of the histogram,
    typically the T value """
    Ts = {}
    method = "default"
    for fudge,entry in data.items():
        pvalues = getPValues ( entry, "norm" )
        tstats = computeT ( pvalues, bins, method = method )
        T = tstats["T"]
        Ts[fudge]=T
    return Ts

def draw( data : dict, bins : list ):
    """ the drawing method """
    Ts = getHistoTestStats ( data, bins )
    splitdata = splitBySqrtsAndCollaboration ( data )
    # splitdata = splitByAnalysisGroups ( data )
    # splitdata = splitBySqrts ( splitdata["ATLAS"] )
    split = splitdata.keys()
    Tss={}
    from matplotlib import pyplot as plt
    xs, ys = list ( Ts.keys() ), list ( Ts.values() )
    for s in split:
        Tss[s] = getHistoTestStats ( splitdata[s], bins )
        xsS, ysS = list ( Tss[s].keys() ), list ( Tss[s].values() )
        plt.plot ( xsS, ysS, label=rf"$\mathrm{{T}}_{{{s}}}(f)$" )
    ## get the fudge value that minimizes T
    min_fudge = min( Ts, key=Ts.get )
    plt.scatter ( min_fudge, Ts[min_fudge], color="red", s=30,
                  label = r"$\hat{f}$" )
    plt.plot ( xs, ys, label=r"$\mathrm{T}(f)$", linewidth=4 )
    plt.legend()
    outfile = "T.png"
    plt.title ( "finding the optimal fudge factor" )
    plt.xlabel ( "fudge factor $f$" )
    plt.ylabel ( "T values" )
    plt.savefig ( outfile )
    from smodels_utils.plotting.mpkitty import timg
    timg ( outfile )

def create ( args : dict ):
    with open( args["inputfile"],"rt") as f:
        data = eval(f.read())
    Ts  = []
    ## standard bins for now
    n_bins =args["nbins"]
    bins = list ( map ( float, np.linspace(0,1,n_bins+1) ) )
    """
    monojets = [ "CMS-EXO-20-004", "ATLAS-EXOT-2018-06" ]
    softleptons = [ "ATLAS-SUSY-2018-16-hino", "ATLAS-SUSY-2018-16" ]
    dEdx = [ "ATLAS-SUSY-2018-42" ]
    multiL = [ "ATLAS-SUSY-2017-03" ]
    Hbb = [ "CMS-SUS-20-004" ]
    dropThese = monojets + softleptons + dEdx + multiL + Hbb
    # dropThese = []
    data = filterByAnaId ( data, dropThese )
    """
    print ( f"[drawT] before filtering we have {len(data[1.0])} entries" )
    data = filterByAnaGroups ( data, "darkmatter+electroweakinos" )
    print ( f"[drawT] after filtering by analysis groups we have  {len(data[1.0])} entries" )
    data = filterByBG ( data, args["min_bg"] )
    draw ( data, bins )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=
            "Produces T-values plots from a createDict.py dict file")
    ap.add_argument('-i', '--inputfile',
            help='input file [data.dict]', default='data.dict' )
    ap.add_argument('-n', '--nbins', type=int,
            help='number of bins in histogram [10]', default=10)
    ap.add_argument('-m', '--min_bg', type=float,
            help='minimum background exptectation to consider analysis [3.5]', default=3.5 )
    args = ap.parse_args()
    create( vars(args) )
