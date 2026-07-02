#!/usr/bin/env python3

"""
.. module:: yieldWriter
   :synopsis: this is a module with just a single function
   that writes the yields into a json file. For debugging
   ML models.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os
from typing import Optional
from smodels.matching.theoryPrediction import TheoryPrediction

def writeOutYields ( theoryPred : TheoryPrediction,
        filename : Optional[os.PathLike] = None,
        mus : list = [ 0., .001, .2, .4, 1., 2., 5., 100. ] ):
    """ a function for debugging only: writes the actual NN input
    into a file called filename

    :param theoryPred: The theory prediction to write yields out for
    :param filename: output file name, if None, then it is
    yields_<massparams>.json
    :param mus: list of mu_values to compute quantities for
    """

    from smodels.base.physicsUnits import GeV
    masses = []
    for node in theoryPred.smsList[0].nodes:
        if node.particle.isSM:
            continue
        masses.append ( float(node.particle.mass.asNumber(GeV)) )
    if filename == None:
        filename = f"yields_{'_'.join(map(str,map(int,masses)))}.json"
    gI = theoryPred.dataset.globalInfo
    if "-orig" in gI.id:
        return
    print ( f"[nnInterface] writing yields for {gI.id} to {filename}" )
    dicts = []
    Dict = { "anaId": gI.id, "masses": masses,
             "txnames":list( set(map(str,theoryPred.txnames))) }
    Dict["mus"]=mus
    ms = theoryPred.statsComputer.getMostSensitiveModel()
    Dict["most_sensitive"]=ms.name
    Dict["ul(mu)"]=ms.getUpperLimitOnMu()
    # mus = [ 0., .001, .2, .4, 1., 2., 5., 100. ]
    from smodels.statistics.basicStats import observed
    for mu in mus:
        smu = str(int(mu)) if mu==int(mu) else f"{mu:.1g}" 
        Dict[f"nll_mu{smu}"]=theoryPred.nll ( mu=mu, writeYields = False )
        Dict[f"nllA_mu{smu}"]=theoryPred.nll ( mu=mu, 
                             evaluationType = observed, asimov = 0 )
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

    with open ( filename, "wt" ) as f:
        import json
        d = json.dumps ( dicts, indent=4 )
        f.write ( d )
        f.close()
