#!/usr/bin/env python3

import numpy as np
import scipy.stats
from matplotlib import pyplot as plt
import matplotlib.lines as mlines
from smodels.tools import statistics

def run():
    nobs = 35
    nb = 30
    nsig = 3
    mumax = ( nobs - nb ) / nsig
    sigmaobs = np.sqrt ( nobs ) / nsig
    sigmaexp_true = np.sqrt ( nb ) / nsig
    oUL = sigmaobs * 1.96 + mumax
    eUL = sigmaexp_true * 1.96
    print ( "oUL",oUL,"eUL",eUL )
    truellhds={}
    S = 0.
    xmax = 10.
    dx = .01
    xr= np.arange(0.,xmax,dx )
    for x in xr:
        llhd = scipy.stats.norm.pdf(x,mumax,sigmaobs)
        S += llhd
        truellhds[x]=llhd
    for x,l in truellhds.items():
        truellhds[x]=l/S/dx
    obs95, mu95obs = 0., 0.
    for x,l in truellhds.items():
        obs95 += l*dx
        if obs95 > .95: ## linear interpolation would be better
            mu95obs = x - dx/2.
            break
    mu95exp = 1.96 * sigmaexp_true
    print ( "mu95exp", mu95exp )
    print ( "mu95obs", mu95obs )
    approxllhds={}
    for x in xr:
        llhd = statistics.likelihoodFromLimits ( mu95obs, mu95exp, x )
        approxllhds[x]=llhd

    plt.plot( list(truellhds.keys()), list(truellhds.values()) )
    plt.plot ( [ 5./3., 5./3.], [ 0., .25 ] )
    plt.plot( list(approxllhds.keys()), list(approxllhds.values()) )
    plt.savefig("test.png")

if __name__ == "__main__":
    run()
