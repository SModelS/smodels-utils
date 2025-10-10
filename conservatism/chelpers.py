#!/usr/bin/env python3
# coding: utf-8

""" simple module that contains helpers for 
conservatism estimates """

from typing import Union
import numpy as np

def filterByAnaId ( data : Union[dict,list], dropThese : list ) \
        -> Union[dict,list]:
    """ filter by analysis ids 
    :param dropThese: list of analysis ids to drop
    """
    if type(data)==dict:
        ret = {}
        for label,entries in data.items():
            ret[label] = filterByAnaId ( entries, dropThese )
        return ret
    ret = []
    for entry in data:
        if entry["id"] in dropThese:
            continue
        else:
            ret.append ( entry )
    return ret

def splitBySqrts ( data : list ) -> dict:
    """ split up data by sqrts """
    from smodels_utils.helper.various import getSqrts
    if type(data)==dict:
        ret = { 8: {}, 13: {} }
        for label,entries in data.items():
            ret[8][label]=[]
            ret[13][label]=[]
            for entry in entries:
                coll = getSqrts ( entry["id"] )
                ret[coll][label].append ( entry )
        return ret
    ret = {}
    for entry in data:
        sqrts = getSqrts ( entry["id"] )
        ssqrts = f"{sqrts} TeV"
        if not ssqrts in ret:
            ret[ssqrts]=[]
        ret[ssqrts].append ( entry )
    return ret

def splitByCollaboration ( data : Union[dict,list] ) -> dict:
    """ split up data by collaboration """
    from smodels_utils.helper.various import getCollaboration
    if type(data)==dict:
        ret = { "CMS": {}, "ATLAS": {} }
        for label,entries in data.items():
            ret["CMS"][label]=[]
            ret["ATLAS"][label]=[]
            for entry in entries:
                coll = getCollaboration ( entry["id"] )
                ret[coll][label].append ( entry )
        return ret
    ret = {}
    for entry in data:
        coll = getCollaboration ( entry["id"] )
        if not coll in ret:
            ret[coll]=[]
        ret[coll].append ( entry )
    return ret


def splitByAnalysisGroups ( data : Union[dict,list] ) -> dict:
    """ split up data by sqrts _and_ collaboration """
    if type(data) == list:
        print ( f"[chelpers] splitByAnalysisGroups" )
    from smodels_utils.helper.various import getCollaboration, \
            getSqrts, getYear
    ret = { }
    for ffactor,entries in data.items():
        for entry in entries:
            sqrts = getSqrts ( entry["id"] )
            coll = getCollaboration ( entry["id"] )
            if coll == "CMS":
                continue
            year = getYear ( entry["id"] )
            label = f"{year}"
            if not label in ret:
                ret[label]={}
            if not ffactor in ret[label]:
                ret[label][ffactor]=[]
            #label = f"{coll}{year}"
            ret[label][ffactor].append ( entry )
    return ret

    
def splitBySqrtsAndCollaboration ( data : Union[dict,list] ) -> dict:
    """ split up data by sqrts _and_ collaboration """
    from smodels_utils.helper.various import getCollaboration, getSqrts
    if type(data)==dict:
        labels = [ "CMS8", "ATLAS8", "CMS13", "ATLAS13" ]
        ret = { x: {} for x in labels }
        for ffactor,entries in data.items():
            for x in labels:
                ret[x][ffactor]=[]
            for entry in entries:
                sqrts = getSqrts ( entry["id"] )
                coll = getCollaboration ( entry["id"] )
                label = f"{coll}{sqrts}"
                ret[label][ffactor].append ( entry )
        return ret
    ret = {}
    for entry in data:
        coll = getCollaboration ( entry["id"] )
        sqrts = getSqrts ( entry["id"] )
        label = f"{coll}{sqrts}"
        if not label in ret:
            ret[label]=[]
        ret[label].append ( entry )
    return ret

def filterByBG ( data : Union[dict,list], min_bg : float ) -> Union[dict,list]:
    """ filter the data by expected background yield """
    if type(data)==dict:
        ret = {}
        for label,entries in data.items():
            ret[label] = filterByBG ( entries, min_bg )
        return ret
    ret = []
    for entry in data:
        if entry["bg"]>min_bg:
            ret.append ( entry )
    return ret

def computeT( p_values : list , bins : Union[str,None,list,int] = None,
       method :str = "default" ) -> dict:
    """ given a list of p-values, and a binning,
    return the binned chi2 test statistic
    :param bins: either list of bins, or number of bins, or None (default),
    or "default" or "half"
    :param method: default, or fold

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
        if method == "fold": ## folding
            for i in range(n_bins):
                if bins[i]<1-p<bins[i+1]:
                    counts[i] += 1
    n_pvalues = sum(counts)
    T_i = [ ((c - n_pvalues*p_i)**2) / (n_pvalues*p_i) for c in counts ]
    T = float ( sum ( T_i ) )
    from scipy.stats import chi2
    p = float ( 1. - chi2.cdf ( T, df = n_bins - 1 ) )
    return { "T": T, "nbins": n_bins, "p": p }

