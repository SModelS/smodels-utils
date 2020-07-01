#!/usr/bin/env python3

import numpy as np
import scipy.stats
from matplotlib import pyplot as plt
import matplotlib.lines as mlines
from smodels.tools import statistics

def run( nobs, nb, nsig ):
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

    plt.plot( list(truellhds.keys()), list(truellhds.values()), label="true LLHD" )
    maxy = max ( list ( truellhds.values() ) + list ( approxllhds.values() ) )
    plt.plot ( [ mumax, mumax ], [ 0., maxy ], label="$\mu_\mathrm{max}$" )
    plt.plot( list(approxllhds.keys()), list(approxllhds.values()), label="approx." )
    plt.legend()
    plt.savefig("test.png")

def main():
    nobs,nbg,nsig = 35.30,3
    run( nobs, nb, nsig )

if __name__ == "__main__":
    main()
