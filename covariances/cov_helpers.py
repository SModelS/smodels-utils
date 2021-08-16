#!/usr/bin/env python3

""" helper functions around the simplified likelihoods business """

import math

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

