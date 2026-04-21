#!/usr/bin/env python3    

""" simple pulls plot from stats file """

import numpy as np

def getValues():
    filename = "stats"
    with open ( filename, "rt" ) as f:
        d = eval(f.read())
    ret = []
    for point, entry in d.items():
        for anaid, values in entry.items():
            pull = values["pull"]
            ret.append ( pull )
            print ( f"[{point}] {anaid:10s}: {pull:.2f}" )
    return ret

def plot():
    d = getValues()
    from matplotlib import pyplot as plt
    import scipy
    plt.hist ( d, label="histo" )
    stdnmx = np.arange(-3,3,.1)
    scale = len(d)
    stdnmy = [ scipy.stats.norm.pdf(x) * scale for x in stdnmx ]
    plt.plot ( stdnmx, stdnmy, c="black", linestyle="dotted",
               label="standard normal" )
    plt.xlabel ( "pulls" )
    plt.title ( "pulls of nll estimates" )
    outfile = "pulls.png"
    plt.savefig ( outfile )
    from smodels_utils.plotting.mpkitty import timg
    timg ( outfile )

if __name__ == "__main__":
    plot()
