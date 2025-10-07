#!/usr/bin/env python3
# coding: utf-8

""" simple module that contains helpers for 
conservatism estimates """

from typing import Union
import numpy as np

def computeT( p_values : list , bins : Union[str,None,list,int] = None ) -> dict:
    """ given a list of p-values, and a binning,
    return the binned chi2 test statistic
    :param bins: either list of bins, or number of bins, or None (default),
    or "default" or "half"

    :returns: dictionary with test statistic, ndf, and p-value for test statistic
    """
    if bins == None:
        n_bins = 10
        bins = list ( map ( float, np.linspace(0,1,n_bins+1) ) )
    if bins == "default":
        n_bins = 10
        bins = list ( map ( float, np.linspace(0,1,n_bins+1) ) )
    if bins == "half":
        n_bins = 10
        bins = list ( map ( float, np.linspace(0.5,1,n_bins+1) ) )
    if type(bins) == int:
        bins = list ( map ( float, np.linspace(0,1,bins+1) ) )
        
    n_bins = len(bins) - 1
    ## the i index runs over bins
    p_i = 1/n_bins # we compare against uniform
    counts = [0]*n_bins
    for p in p_values:
        for i in range(n_bins):
            if bins[i]<p<bins[i+1]:
                counts[i] += 1
    n_pvalues = sum(counts)
    T_i = [ ((c - n_pvalues*p_i)**2) / (n_pvalues*p_i) for c in counts ]
    T = float ( sum ( T_i ) )
    from scipy.stats import chi2
    p = float ( 1. - chi2.cdf ( T, df = n_bins - 1 ) )
    return { "T": T, "nbins": n_bins, "p": p }

