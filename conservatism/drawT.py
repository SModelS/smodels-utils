#!/usr/bin/env python3

""" the script used to draw the test statistic of thie binned chi2
test as a function of the fudge factor """

from chelpers import computeT, filterByAnaId, filterByBG, splitByCollaboration,\
     splitBySqrts
import numpy as np

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
    for fudge,entry in data.items():
        pvalues = getPValues ( entry, "norm" )
        tstats = computeT ( pvalues, bins )
        T = tstats["T"]
        Ts[fudge]=T
    return Ts

def draw( data : dict, bins : list ):
    """ the drawing method """
    Ts = getHistoTestStats ( data, bins )
    #TsCMS = getHistoTestStats ( splitdata["CMS"], bins )
    from matplotlib import pyplot as plt
    xs, ys = list ( Ts.keys() ), list ( Ts.values() )
    #xsCMS, ysCMS = list ( TsCMS.keys() ), list ( TsCMS.values() )
    plt.plot ( xs, ys, label="T(f)" )
    #plt.plot ( xsCMS, ysCMS, label="T_{CMS}(f)" )
    ## get the fudge value that minimizes T
    min_fudge = min( Ts, key=Ts.get )
    plt.scatter ( min_fudge, Ts[min_fudge], color="red", s=30,
                  label = r"$\hat{f}$" )
    plt.legend()
    outfile = "T.png"
    plt.title ( "finding the optimal fudge factor" )
    plt.xlabel ( "fudge factor $f$" )
    plt.ylabel ( "T values" )
    plt.savefig ( outfile )
    from smodels_utils.plotting.mpkitty import timg
    timg ( outfile )

def create():
    with open("data.dict","rt") as f:
        data = eval(f.read())
    Ts  = []
    ## standard bins for now
    n_bins = 10
    bins = list ( map ( float, np.linspace(0,1,n_bins+1) ) )
    dropThese = []
    monojets = [ "CMS-EXO-20-004", "ATLAS-EXOT-2018-06" ]
    softleptons = [ "ATLAS-SUSY-2018-16-hino", "ATLAS-SUSY-2018-16" ]
    dEdx = [ "ATLAS-SUSY-2018-42" ]
    multiL = [ "ATLAS-SUSY-2017-03" ]
    Hbb = [ "CMS-SUS-20-004" ]
    dropThese = monojets + softleptons + dEdx + multiL + Hbb
    data = filterByAnaId ( data, dropThese )
    data = filterByBG ( data, 2.1 )
    draw ( data, bins )

if __name__ == "__main__":
    create()
