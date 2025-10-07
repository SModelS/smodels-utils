#!/usr/bin/env python3

""" the script used to draw the test statistic of thie binned chi2
test as a function of the fudge factor """

from chelpers import computeT
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

def draw( Ts : dict ):
    """ the drawing method """
    from matplotlib import pyplot as plt
    xs, ys = list ( Ts.keys() ), list ( Ts.values() )
    plt.plot ( xs, ys )
    outfile = "T.png"
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
    Ts = getHistoTestStats ( data, bins )
    draw ( Ts )

if __name__ == "__main__":
    create()
