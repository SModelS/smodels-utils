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

def filterByAnaGroups ( data : Union[dict,list], dropThese : str ) \
        -> Union[dict,list]:
    """ filter by analysis groups
    :param dropThese: string describing analysis groups to drop,
    e.g. "darkmatter+electroweakinos"
    """
    if type(data)==dict:
        ret = {}
        for ffactor,entries in data.items():
            ret[ffactor] = filterByAnaGroups ( entries, dropThese )
        return ret

    # data is a list
    ret = []
    from ptools.moreHelpers import namesForSetsOfTopologies
    grouptxns = namesForSetsOfTopologies ( dropThese )[0].split(",")

    for entry in data:
        if not areTxnsInGroups ( entry["txns"], grouptxns ):
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

def areTxnsInGroups ( txns : Union[str,tuple],
                      group : Union[tuple,str] ) -> bool:
    """ do we find some of the txns in group?

    :txns: either e.g. 'T1', or ( 'T1', 'T2' )
    :group: e.g. 'electroweakinos'

    :returns: true if any of txns is in the group
    """
    from ptools.moreHelpers import namesForSetsOfTopologies
    grouptxns = group
    if type(group)==str:
        grouptxns = namesForSetsOfTopologies ( group )[0].split(",")
    if type(txns) == str: ## turn into tuple
        txns = ( txns, )
    for txn in txns:
        if txn in grouptxns:
            return True
    return False

def splitByAnalysisGroups ( data : Union[dict,list] ) -> dict:
    """ split up data by analysis groups (darkmatter,gluinos,...)
    """
    from smodels_utils.helper.various import getCollaboration
    groups = [ "darkmatter", "rest",
        "electroweakinos", "stops" ]
    if type(data) == list:
        ret = { x: [] for x in groups }
        for entry in data:
            coll = getCollaboration ( entry["id"] )
            #if coll == "CMS":
            #    continue
            hasAdded = False
            txns = entry["txns"]
            for group in groups:
                inGrp = areTxnsInGroups ( txns, group )
                # print ( f"@@1 txns {txns} in {group}? {inGrp} hasAdded {hasAdded}" )
                if inGrp and not hasAdded:
                    ret[group].append ( entry )
                    hasAdded = True
            if not hasAdded:
                ret["rest"].append ( entry )
        return ret
    ## data is a dictionary
    ret = { x: {} for x in groups }
    for ffactor, entries in data.items():
        for x in groups:
            ret[x][ffactor]=[]
        for entry in entries:
            coll = getCollaboration ( entry["id"] )
            #if coll == "CMS":
            #    continue
            hasAdded = False
            txns = entry["txns"]
            for group in groups:
                inGrp = areTxnsInGroups ( txns, group )
                # print ( f"@@1 txns {txns} in {group}? {inGrp} hasAdded {hasAdded}" )
                if inGrp and not hasAdded:
                    ret[group][ffactor].append ( entry )
                    hasAdded = True
            if not hasAdded:
                ret["rest"][ffactor].append ( entry )
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

def filterByBG ( data : Union[dict,list], min_bg : Union[None,float],
                 filterBy : str = "bg" ) -> Union[dict,list]:
    """ filter the data by expected background yield
    :param min_bg: minimum number of background expected events.
    if none, then dont filter
    :param filterBy: can also filter by obs
    """
    if type(data)==dict:
        ret = {}
        for label,entries in data.items():
            ret[label] = filterByBG ( entries, min_bg )
        return ret
    ret = []
    for entry in data:
        if min_bg is None or entry[ filterBy ] >= min_bg:
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
    assert method in [ "wasserstein", "KL", "default", "fold", "KS", "AD", "combo" ], f"unknown method {method}"
    if method == "combo":
        ad = computeAD ( p_values )
        T = ad["T"]/6.
        ws = computeWasserstein ( p_values )
        T += ws["T"]/0.055
        ks = computeKS ( p_values )
        T += ks["T"]/0.13
        chi2 = computeChi2 ( p_values, bins )
        T += chi2["T"]/25.
        return { "type": "combo", "T": T }
    if method == "KS":
        ret = computeKS ( p_values )
        return ret
    if method == "AD":
        ret = computeAD ( p_values )
        return ret
    if method == "wasserstein":
        ret = computeWasserstein ( p_values )
        return ret
    if method == "KL":
        ret = computeKLDivergence ( p_values )
        return ret
    return computeChi2 ( p_values, bins, method )

def computeChi2( p_values : list , bins : Union[str,None,list,int] = None,
       method :str = "default" ) -> dict:
    """ binned chi2 test """
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
    if n_pvalues == 0:
        return { "T": 0, "nbins": n_bins, "p": 0 }
    T_i = [ ((c - n_pvalues*p_i)**2) / (n_pvalues*p_i) for c in counts ]
    T = float ( sum ( T_i ) )
    from scipy.stats import chi2
    p = float ( 1. - chi2.cdf ( T, df = n_bins - 1 ) )
    return { "T": T, "nbins": n_bins, "p": p }

def computeWasserstein( p_values : list ):
    """ given a list of p-values
    return the Wasserstein distance to a uniform distribution

    :returns: dictionary with test statistic, ndf, and p-value for test statistic
    """
    from scipy.stats import wasserstein_distance
    samples = np.array ( p_values )
    #print ( f"len [{len(p_values)}]" )
    uniform_ref = np.random.uniform(0., 1., size=len(p_values)*300 )
    wd = wasserstein_distance(samples, uniform_ref)
    return { "wd": wd, "type": "wasserstein", "T": wd }

def computeKS( p_values : list ):
    """ given a list of p-values
    return the KS statistic

    :returns: dictionary with test statistic
    """
    from scipy.stats import kstest
    samples = np.array ( p_values )
    x = np.asarray(samples).ravel()
    if x.size == 0:
        raise ValueError("samples must contain at least one value")

    # scipy's 'uniform' takes (loc, scale)
    D, p = kstest(x, 'uniform', args=(0., 1.))

    return { "KS": D, "type": "KS", "T": D }

def anderson_darling_uniform_stat(samples, a=None, b=None, eps=1e-12):
    """
    Compute Anderson-Darling A^2 statistic for testing samples ~ Uniform(a,b).
    - samples: 1D array-like
    - a, b: support of the hypothesised uniform. If None, infer from samples (min/max).
    - eps: small clipping constant to avoid log(0).
    Returns: float A2 (statistic)
    """
    x = np.sort(np.asarray(samples).ravel())
    n = x.size
    if n == 0:
        raise ValueError("samples must contain at least one value")
    if a is None:
        a = float(x[0])
    if b is None:
        b = float(x[-1])
    if b == a:
        raise ValueError("a and b must differ (non-degenerate uniform)")

    # compute F(x) for uniform and clip into (0,1)
    F_x = (x - a) / (b - a)
    F_x = np.clip(F_x, eps, 1.0 - eps)

    # compute the S sum in the formula
    i = np.arange(1, n + 1)
    term1 = np.log(F_x)
    term2 = np.log(1.0 - F_x[::-1])  # reversed for Y_{n+1-i}
    S = np.sum(((2 * i - 1) / n) * (term1 + term2))

    A2 = -n - S
    return float(A2)

def computeAD( p_values : list ):
    """ given a list of p-values
    return the AD statistic

    :returns: dictionary with test statistic
    """
    rng = np.random.default_rng(0)
    x = np.asarray(p_values).ravel()
    n = x.size
    if n == 0:
        raise ValueError("samples must contain at least one value")
    a, b = 0., 1.
    n_sim = 0

    # If a/b are None we will estimate from the observed sample,
    # and in Monte-Carlo we must estimate them from each simulated sample likewise.
    infer_a = (a is None)
    infer_b = (b is None)

    # compute observed A2 with chosen/estimated a,b
    if infer_a:
        a_obs = float(np.min(x))
    else:
        a_obs = float(a)
    if infer_b:
        b_obs = float(np.max(x)) if infer_b else float(b)
    # but careful: if only one of a/b is None, handle appropriately
    if (not infer_a) and (not infer_b):
        a_obs = float(a); b_obs = float(b)
    elif (not infer_a) and infer_b:
        b_obs = float(np.max(x))
    elif infer_a and (not infer_b):
        a_obs = float(np.min(x))

    A2_obs = anderson_darling_uniform_stat(x, a=a_obs, b=b_obs)

    pval = None
    if n_sim and n_sim > 0:
        sim_stats = np.empty(n_sim, dtype=float)
        for j in range(n_sim):
            sim = rng.uniform(a_obs, b_obs, size=n)  # simulate under the hypothesised uniform on [a_obs,b_obs]
            # if a/b are inferred from data, re-estimate on the simulated sample the same way
            a_sim = float(np.min(sim)) if infer_a else a_obs
            b_sim = float(np.max(sim)) if infer_b else b_obs
            sim_stats[j] = anderson_darling_uniform_stat(sim, a=a_sim, b=b_sim)
        # p-value: proportion of simulated A2 >= observed A2 (plus 1 for mid-p / conservatism)
        pval = (np.sum(sim_stats >= A2_obs) + 1) / (n_sim + 1)

    return {"T": float(A2_obs), "A2": float(A2_obs), "p_value": pval, "n_sim": int(n_sim)}

def computeKLDivergence( p_values : list ):
    """ given a list of p-values
    return the Wasserstein distance to a uniform distribution

    :returns: dictionary with test statistic, ndf, and p-value for test statistic
    """
    from scipy.stats import entropy
    samples = np.array ( p_values )
    counts, bin_edges = np.histogram( p_values, bins=20, range=(0., 1.), density=True)
    q = np.full_like(counts, 1.)
    mask = counts > 0
    kl = entropy(counts[mask], q[mask])
    return { "wd": kl, "type": "KL", "T": kl }
