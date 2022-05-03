#!/usr/bin/env python3

""" helper functions around the simplified likelihoods business """

import math

def printIndicator ( i ):
    if i == 0:
        return
    if i % 50 == 0:
        print ( ":", flush=True, end="" )
        return
    if i % 10 == 0:
        print ( ".", flush=True, end="" )

def computeLlhdHisto ( tpred, xmin, xmax, nbins = 10,
       equidistant = True, verbose = False, normalize = True,
       expected = False ):
    """ compute the likelhoods for theory prediction
    :param tpred: a theory prediction
    :param xmin: minimum mu
    :param xmax: maximum mu
    :param nbins: the number of bins
    :param equidistant: if False, allow for denser binning at center
    :param normalize: if true, normalize histogram
    :returns dictionary of normalized likelihoods and normalization constant
    """

    import numpy as np
    dx = ( xmax - xmin ) / nbins
    S = 0.
    rng = np.arange ( xmin, xmax, dx)
    center = ( xmin + xmax ) / 2.
    fourth = ( xmax - xmin ) / 4.
    oned = 1+ 1e-6
    if not equidistant:
        dx = 2* ( xmax - xmin ) / nbins
        rng = list ( np.arange ( xmin, xmax*oned, dx) )
        #print ( "rng1", xmin, xmax, dx, len(rng) )
        rng2 = list ( np.arange ( (xmin+fourth+dx/2.)/2., (xmax-fourth)*oned/2., dx/2.) )

        rng3 = list ( np.arange ( center - fourth/2. + dx/4., (center + fourth/2.)*oned, dx/2. ) )
        #print ( "rng2", (xmin+fourth+dx/.2)/2., (xmax-fourth)*oned/2., dx/2., len(rng2) )
        #print ( "rng3", len(rng3) )
        rng += rng2
        rng += rng3
        rng = list ( set ( rng ) )
        rng.sort()
        #print ( "rng", len(rng), [ round(x,3) for x in rng ] )

    ret = {}
    print ( ">> computing llhds:", end=" " )
    for i,mu in enumerate(rng):
        printIndicator ( i )
        l = tpred.likelihood ( mu, useCached=False, expected = expected )
        if l == None:
            l = float("nan")
        if tpred.dataset.getType() == "combined":
            if verbose:
                print ( f"[cov_helpers] {tpred.dataset.globalInfo.id} mu={mu:.3f} l={l:.3g}" )
        if l not in [ None ] and math.isfinite( l ):
            S+=l
            ret[mu]=l
    print ( "" )
    if normalize and S <= 0.:
        print ( f"[cov_helpers] would like to normalize but S={S}" )
    # print ( f"Normalizing {normalize} {S}" )
    if normalize and S > 0.:
        for k,v in ret.items():
            ret[k]=ret[k]/S
    return ret, S

def createLine ( xv, ymin, ymax, addJitter = False, jitter=.08 ):
    """ create a vertical line at xv from ymin to ymax,
    potentially add jitter """
    if not addJitter or jitter == 0.:
        return { "x": [xv,xv], "y": [ymin, ymax] }
    import random
    nsteps = 20
    xr, yr = [], []
    for i in range(nsteps+1):
        x_ = xv * random.uniform(1.-jitter,1.+jitter)
        xr.append ( x_ )
        y_ = ymin + i*(ymax-ymin)/nsteps
        yr.append ( y_ )
    # print ( f"line {xr} {yr} from {xv} {ymin} {ymax}" )
    return { "x": xr, "y": yr }

def addJitter ( yvalues, jitter=.015 ):
    """ add jitter to the y-values """
    import random
    maxy = max(yvalues)
    for i,y in enumerate(yvalues):
        yvalues[i]+=maxy*random.uniform( -jitter,+jitter )

def getSensibleMuRange ( tpred ):
    """ given a theory prediction, get a sensible range for mu.
        sensible meaning, smallest interval that covers 99% of the llhd
    :param tpred: the theory prediction or list of theory predictions
    """
    if type ( tpred ) in [ tuple, list ]:
        minx, maxx = [], []
        minxtot, maxxtot = float("inf"), -float("inf")
        for t in tpred:
            xmin, xmax = getSensibleMuRange ( t )
            if xmin < minxtot:
                minxtot = xmin
            if xmax > maxxtot:
                maxxtot = xmax
        return minxtot, maxxtot

    xmin, xmax = -2., 10. ## first guess
    hasConverged = False
    ctIt = 0
    while not hasConverged:
        if ctIt > 30:
            print ( f"[cov_helpers:getSensibleMuRange] after {ctIt} iterations no convergence" )
            break
        hasConverged = True
        ctIt += 1
        factor = ( 1. + 1. / ctIt )
        llhds, S = computeLlhdHisto ( tpred, xmin, xmax, 10 )
        v = list ( llhds.values() )
        if False:
            print ( f"[cov_helpers] iteration {ctIt}: xmin={xmin}, xmax={xmax} llhds={v[0],v[-1]}" )
        if v[0] > .05 and xmin < 0.:
            xmin = xmin * 2 * factor
            hasConverged = False
        if v[0] > .02 and xmin < 0.:
            xmin = xmin * factor
            hasConverged = False
        if v[0] > .01 and xmin > 0.:
            xmin = xmin - factor
            hasConverged = False
        if v[-1] > .03:
            xmax = xmax * 2 * factor
            hasConverged = False
        if v[-1] > .01:
            xmax = xmax * factor
            hasConverged = False
        if v[0] < 1e-3 and xmin < 0.: ## too far
            xmin = xmin / factor
            hasConverged = False
        if v[0] < 1e-3 and xmin > 0.: ## too far
            xmin = xmin * factor
            hasConverged = False
        if v[-1] < 1e-4: ## too far
            xmax = xmax / factor
            hasConverged = False
    k = list ( llhds.keys() )
    return min(k), max(k)

def computeCorrelationMatrix ( cov : list ) -> list:
    """ given a covariance matrix, compute a correlation matrix
    :param cov: covariance matrix
    :returns: correlation matrix
    """
    n=len(cov)

    pairs = {}

    ret = [ [.0]*n for x in range(n) ]

    for i in range(n):
        ret[i][i]=1.
        for j in range(i+1,n):
            cor = cov[i][j]/math.sqrt(cov[i][i]*cov[j][j] )
            ret[i][j] = cor
            ret[j][i] = cor

    return ret

def cutMatrix ( m : list, nmin : int, nmax : int ) -> list:
    """ return only nmin - nmax columns and rows of matrix
    """
    n = nmax - nmin
    ret = [ [.0]*n for x in range(n) ]

    for i in range(nmin,nmax):
        for j in range(i,nmax):
            ret[i-nmin][j-nmin] = m[i][j]
            ret[j-nmin][i-nmin] = m[i][j]

    return ret

def withinMuRange ( mu, murange ):
    """ check if mu is within the given murange """
    return murange[0] < mu < murange[1]
