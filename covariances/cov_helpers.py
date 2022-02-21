#!/usr/bin/env python3

""" helper functions around the simplified likelihoods business """

import math

def computeLlhdHisto ( tpred, xmin, xmax, nbins = 10 ):
    """ compute the likelhoods for theory prediction
    :param tpred: a theory prediction
    :param xmin: minimum mu
    :param xmax: maximum mu
    :param nbins: the number of bins
    :returns dictionary of normalized likelihoods and normalization constant
    """

    import numpy as np
    dx = ( xmax - xmin ) / nbins
    S = 0.
    rng = np.arange ( xmin, xmax, dx) 
    ret = {}
    for mu in rng:
        l = tpred.likelihood ( mu )
        S+=l 
        ret[mu]=l
    for k,v in ret.items():
        ret[k]=ret[k]/S
    return ret, S

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
            
    xmin, xmax = -1., 5. ## first guess
    hasConverged = False
    ctIt = 0
    while not hasConverged:
        if ctIt > 10:
            break
        hasConverged = True
        ctIt += 1
        factor = ( 1. + 1. / ctIt )
        llhds, S = computeLlhdHisto ( tpred, xmin, xmax, 10 )
        v = list ( llhds.values() )
        if False:
        print ( f"[cov_helpers] iteration {ctIt}: xmin={xmin}, xmax={xmax} llhds={v[0],v[-1]}" )
        if v[0] > .01 and xmin < 0.:
            xmin = xmin * factor
            hasConverged = False
        if v[0] > .01 and xmin > 0.:
            xmin = xmin - factor
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

