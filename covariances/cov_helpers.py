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

def cutMatrix ( m : list, n : int ) -> list:
    """ return only first n columns and rows of matrix """
    ret = [ [.0]*n for x in range(n) ]

    for i in range(n):
        for j in range(i,n):
            ret[i][j] = m[i][j]
            ret[j][i] = m[i][j]

    return ret

