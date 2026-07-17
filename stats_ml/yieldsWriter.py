#!/usr/bin/env python3

"""
.. module:: yieldWriter
   :synopsis: this is a module meant to get yields,
   in dicts. For debugging ML models.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from smodels.matching.theoryPrediction import TheoryPrediction

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

def yieldsToDicts ( theoryPred : TheoryPrediction,
        mus : list = [ 0., .001, .2, .4, 1., 2., 5., 100. ],
        expected_also : bool = False ) -> list[dict]:
    """ a function for debugging only: writes the actual NN input
    into a file called filename

    :param theoryPred: The theory prediction to write yields out for
    e.g. yields_<anaId>_<massparams>.json
    :param mus: list of mu_values to compute quantities for
    :param expected_also: if true, then also add a priori expected

    :returns: list of all dictionaries
    """
    from smodels.base.physicsUnits import GeV
    masses = []
    for node in theoryPred.smsList[0].nodes:
        if node.particle.isSM:
            continue
        masses.append ( float(node.particle.mass.asNumber(GeV)) )
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
    ms = theoryPred.statsComputer.getMostSensitiveModel()
    Dict["most_sensitive"]=ms.name
    Dict["ul(mu)"]=ms.getUpperLimitOnMu()
    # mus = [ 0., .001, .2, .4, 1., 2., 5., 100. ]
    from smodels.statistics.basicStats import observed, apriori
    for mu in mus:
        smu = formatMu ( mu )
        # smu = str(int(mu)) if mu==int(mu) else f"{mu:.1g}"
        Dict[f"nll_mu{smu}"]=theoryPred.nll ( mu=mu )
        Dict[f"nllA_mu{smu}"]=theoryPred.nll ( mu=mu,
                             evaluationType = observed, asimov = 0 )
        if expected_also:
            Dict[f"nllE_mu{smu}"] = theoryPred.nll ( mu=mu,\
                    evaluationType = apriori )
            Dict[f"nllEA_mu{smu}"] = theoryPred.nll ( mu=mu,\
                    evaluationType = apriori, asimov = 0 )
    dicts.append ( Dict )

    def removeZeros ( nsig : dict ) -> dict:
        newD = {}
        for k,v in nsig.items():
            if v > 0.:
                newD[k]=v
        return newD

    for computer in theoryPred.statsComputer.subComputers:
        if not hasattr ( computer, "totalYieldsFromSignals" ):
            continue
        if computer.name != ms.name:
            ## only the one used
            continue
        Dict = {}
        Dict["model"]=computer.name
        Dict["nsignals"]=removeZeros ( computer.nsignals )
        for mu in mus:
            smu = str(int(mu)) if mu==int(mu) else f"{mu:.1g}"
            yields = computer.totalYieldsFromSignals( mu )
            Dict[ f"yields_mu{smu}" ]= yields
        dicts.append ( Dict )

    return dicts
