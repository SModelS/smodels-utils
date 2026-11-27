#!/usr/bin/env python3

"""
.. module:: yieldWriter
   :synopsis: this is a module meant to get yields,
   in dicts. For debugging ML models.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import math
from smodels.matching.theoryPrediction import TheoryPrediction
from smodels.base.smodelsLogging import logger

_cacheAttribute = "_statsMlYieldsCache"
_validationMus = [ 0., 1., 100. ]


def generalInfo ( theoryPred : TheoryPrediction ) -> dict:
    """ this is the general info block, extracts  masses, txnames
    :returns: dictionary with particle masses, and txnames
    """
    from smodels.base.physicsUnits import GeV
    masses = {}
    for node in theoryPred.smsList[0].nodes:
        if node.particle.isSM:
            continue
        mass = float(node.particle.mass.asNumber(GeV))
        name = node.particle.label
        name = name.replace("+","")
        masses[name] = mass
    Dict = { "masses": masses,
             "txnames": list( set(map(str,theoryPred.txnames))) }
    return Dict

def formatMu ( mu : float ) -> str:
    """ 100. -> '100', .0010 -> '.001', etc """
    smu = str(int(mu)) if mu==int(mu) else f"{mu:.1g}"
    return smu

def _cacheFor ( theoryPred : TheoryPrediction ) -> dict:
    """ the cache lives on the prediction, so all printers share it """
    cache = getattr ( theoryPred, _cacheAttribute, None )
    if cache is None:
        cache = { "base": None, "nlls": {}, "expected": {}, "yields": {} }
        setattr ( theoryPred, _cacheAttribute, cache )
    return cache

def clearNllCache ( theoryPred : TheoryPrediction ):
    """ drop all cached nlls and yields, so the next call recomputes them """
    cache = _cacheFor ( theoryPred )
    cache["nlls"].clear()
    cache["expected"].clear()
    cache["yields"].clear()
    cache["base"] = None

def _same ( a, b ) -> bool:
    """ compare numbers/lists with a small tolerance for float noise """
    if isinstance ( a, ( int, float ) ) and isinstance ( b, ( int, float ) ):
        return math.isclose ( a, b, rel_tol = 1e-12, abs_tol = 1e-12 )
    if isinstance ( a, ( list, tuple ) ) and isinstance ( b, ( list, tuple ) ):
        return len(a) == len(b) and all ( _same(x,y) for x,y in zip(a,b) )
    return a == b

def validateCachedNlls ( theoryPred : TheoryPrediction, mus : list,
                         expected_also : bool = True,
                         maxChecks : int = 3 ) -> bool:
    """ spot-check cached nlls (and yields) against freshly computed values.

    :returns: False if a mismatch was found. In that case the cache is
              cleared, so the caller can safely recompute everything.
    """
    from smodels.statistics.basicStats import observed, apriori
    cache = _cacheFor ( theoryPred )
    cachedMus = [ mu for mu in mus if mu in cache["nlls"] and
                  ( not expected_also or mu in cache["expected"] ) ]
    if not cachedMus:
        return True
    # check the physically interesting mus first, then whatever else is cached
    checkMus = [ mu for mu in _validationMus if mu in cachedMus ]
    for mu in cachedMus:
        if mu not in checkMus:
            checkMus.append ( mu )
    for mu in checkMus[:maxChecks]:
        smu = formatMu ( mu )
        fresh = { f"nll_mu{smu}": theoryPred.nll ( mu=mu ),
                  f"nllA_mu{smu}": theoryPred.nll ( mu=mu,
                       evaluationType = observed, asimov = 0 ) }
        if expected_also:
            fresh [ f"nllE_mu{smu}" ] = theoryPred.nll ( mu=mu,
                       evaluationType = apriori )
            fresh [ f"nllEA_mu{smu}" ] = theoryPred.nll ( mu=mu,
                       evaluationType = apriori, asimov = 0 )
        base = cache["base"]
        for key, value in fresh.items():
            old = cache["nlls"].get(mu,{}).get(key)
            if old is None:
                old = cache["expected"].get(mu,{}).get(key)
            if old is None or not _same ( old, value ):
                logger.error ( f"cached {key} for mu={mu} is {old}, "
                               f"freshly computed is {value}" )
                clearNllCache ( theoryPred )
                return False
        if base is not None and base["computer"] is not None and mu in cache["yields"]:
            freshYields = base["computer"].totalYieldsFromSignals ( mu )
            if not _same ( cache["yields"][mu], freshYields ):
                logger.error ( f"cached yields for mu={mu} are "
                               f"{cache['yields'][mu]}, freshly computed are {freshYields}" )
                clearNllCache ( theoryPred )
                return False
    return True

def yieldsToDicts ( theoryPred : TheoryPrediction,
        mus : list = [ 0., .001, .2, .4, 1., 2., 5., 100. ],
        expected_also : bool = False ) -> list[dict]:
    """ a function for debugging only: writes the actual NN input
    into a file called filename

    Values are cached on the theoryPrediction, so a second printer asking
    for additional mus does not need to recompute the nlls it already has.

    :param theoryPred: The theory prediction to write yields out for
    e.g. yields_<anaId>_<massparams>.json
    :param mus: list of mu_values to compute quantities for
    :param expected_also: if true, then also add a priori expected

    :returns: list of all dictionaries
    """
    from smodels.statistics.basicStats import observed, apriori
    gI = theoryPred.dataset.globalInfo

    # from pathlib import Path
    # Path("yields/").mkdir(exist_ok=True)
    dicts = []
    Dict = { "anaId": gI.id } # , "masses": masses,
    # "txnames":list( set(map(str,theoryPred.txnames))) }
    # Dict["mus"]=mus
    if type(theoryPred.statsComputer) == str:
        Dict["statsComputer"]=theoryPred.statsComputer
        dicts.append ( Dict )
        return dicts

    cache = _cacheFor ( theoryPred )
    if cache["base"] is None:
        ms = theoryPred.statsComputer.getMostSensitiveModel()
        def removeZeros ( nsig : dict ) -> dict:
            return { k:v for k,v in nsig.items() if v > 0. }
        computer = None
        nsignals = {}
        for comp in theoryPred.statsComputer.subComputers:
            if not hasattr ( comp, "totalYieldsFromSignals" ):
                continue
            if comp.name != ms.name:
                ## only the one used
                continue
            computer = comp
            nsignals = removeZeros ( comp.data.nsignals )
            break
        cache["base"] = { "most_sensitive": ms.name,
                          "ul(mu)": ms.getUpperLimitOnMu(),
                          "nll_min": theoryPred.nll_min(),
                          "model": ms.name,
                          "computer": computer,
                          "nsignals": nsignals }
    base = cache["base"]
    for key in [ "most_sensitive", "ul(mu)", "nll_min" ]:
        Dict[key] = base[key]

    for mu in mus:
        smu = formatMu ( mu )
        entry = cache["nlls"].get(mu)
        if entry is None:
            entry = { f"nll_mu{smu}": theoryPred.nll ( mu=mu ),
                      f"nllA_mu{smu}": theoryPred.nll ( mu=mu,
                           evaluationType = observed, asimov = 0 ) }
            cache["nlls"][mu] = entry
        Dict.update ( entry )
        if expected_also:
            entry = cache["expected"].get(mu)
            if entry is None:
                entry = { f"nllE_mu{smu}": theoryPred.nll ( mu=mu,
                               evaluationType = apriori ),
                          f"nllEA_mu{smu}": theoryPred.nll ( mu=mu,
                               evaluationType = apriori, asimov = 0 ) }
                cache["expected"][mu] = entry
            Dict.update ( entry )
    dicts.append ( Dict )

    computer = base["computer"]
    if computer is not None:
        Dict = { "model": base["model"], "nsignals": base["nsignals"] }
        for mu in mus:
            smu = formatMu ( mu )
            yields = cache["yields"].get(mu)
            if yields is None:
                yields = computer.totalYieldsFromSignals ( mu )
                cache["yields"][mu] = yields
            Dict[ f"yields_mu{smu}" ] = yields
        dicts.append ( Dict )

    return dicts
