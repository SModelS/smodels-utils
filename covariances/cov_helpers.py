#!/usr/bin/env python3

""" helper functions around the simplified likelihoods business """

import math

def _computeLlhds ( tpred, xmin, xmax, nbins = 10 ):
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
    return ret

def getSensibleMuRange ( tpred, nfinalbins=None ):
    """ given a theory prediction, get a sensible range for mu.
        sensible meaning, smallest interval that covers 99% of the llhd 
    :param tpred: the theory prediction
    :param nfinalbins: if integer, then run with this as final number of bins
    """
    xmin, xmax = -1., 5. ## first guess
    hasConverged = False
    ctIt = 0
    while not hasConverged:
        hasConverged = True
        ctIt += 1
        llhds = _computeLlhds ( tpred, xmin, xmax )
        # print ( f"iteration {ctIt}: xmin={xmin}, xmax={xmax} llhds={llhds}" )
        v = list ( llhds.values() )
        if v[0] > .01 and xmin < 0.:
            xmin = xmin * 2.
            hasConverged = False
        if v[0] > .01 and xmin > 0.:
            xmin = xmin - 1.
            hasConverged = False
        if v[-1] > .01:
            xmax = xmax * 1.5
            hasConverged = False
        if v[0] < 1e-9: ## too far
            xmin = xmin * 1.3
    if nfinalbins != None:
        llhds = _computeLlhds ( tpred, xmin, xmax, nfinalbins )
    return llhds
    

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

