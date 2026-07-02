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
        filename : Optional[os.PathLike] = None ):
    """ a function for debugging only: writes the actual NN input
    into a file called filename

    :param theoryPred: The theory prediction to write yields out for
    :param filename: output file name, if None, then it is
    yields_<massparams>.json
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
    ms = theoryPred.statsComputer.getMostSensitiveModel()
    Dict["most_sensitive"]=ms.name
    Dict["ul_min"]=ms.getUpperLimitOnMu()
    mus = [ 0., .001, .2, .4, 1., 2., 5., 100. ]
    for mu in mus:
        smu = str(int(mu)) if mu==int(mu) else f"{mu:.2f}" 
        Dict[f"nll_mu{smu}"]=theoryPred.nll ( mu=mu, writeYields = False )
        Dict["nllA_mu{smu}"]=theoryPred.nll ( mu=mu, 
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
        Dict = {}
        # m = computer.data
        yields_0 = computer.totalYieldsFromSignals( 0. )
        yields_1 = computer.totalYieldsFromSignals( 1. )
        yields_5 = computer.totalYieldsFromSignals( 5. )
        # scaled_yields = computer.scaleYields ( yields, m )
        # nn_input = scaled_yields.tolist()
        Dict["model"]=computer.name
        Dict["nsignals"]=removeZeros ( computer.nsignals )
        Dict["yields_mu0"]= yields_0
        Dict["yields_mu1"]= yields_1
        Dict["yields_mu5"]= yields_5
        # Dict["nn_input"]=nn_input
        dicts.append ( Dict )

    with open ( filename, "wt" ) as f:
        import json
        d = json.dumps ( dicts, indent=4 )
        f.write ( d )
        f.close()
