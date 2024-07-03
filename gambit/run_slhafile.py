#!/usr/bin/env python3

""" a first version of a SModelS backend for gambit/colliderbit 
depends only SModelS (pip install smodels), nothing else.
"""

import os
from typing import Dict

def run_smodels ( slhafile : os.PathLike ) -> Dict:
    """ given the path to an slha file, this little script runs
    SModelS, returns the results as dictionary.

    :returns: dictionary with analysis Ids as keys, and (negative log) 
    likelihoods, and r-values 
    (r := predicted cross section / upper limit on cross section ) 
    as values
    """
    if not os.path.exists ( slhafile ):
        print ( f"[run_smodels] slha file {slhafile} not found" )
        return {}

    ## some imports
    from smodels.base.model import Model
    from smodels.share.models.SMparticles import SMList
    from smodels.particlesLoader import load
    from smodels.experiment.databaseObj import Database
    from smodels.base.physicsUnits import fb, GeV
    from smodels.decomposition import decomposer
    from smodels.matching.theoryPrediction import theoryPredictionsFor

    ## the database, we could use something other than the official
    ## database
    dbpath = "official"
    database = Database(dbpath)
    BSMList = load()
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    slhafile = os.path.abspath(os.path.expanduser(slhafile))

    ## a few minor parameters that can be adapted
    model.updateParticles(inputFile=slhafile,
        ignorePromptQNumbers = ['eCharge','colordim','spin'])
    sigmacut=0.05*fb
    mingap = 5.*GeV

    ## here we decompose our model into its simplified model
    ## spectrum
    topDict = decomposer.decompose(model, sigmacut, massCompress=True,
        invisibleCompress=True, minmassgap=mingap )

    ## now we get theory predictions, ie. we match the experimental
    ## results with the decomposed theory
    ## 'combinedResults' means that we combine signal regions, if we
    ## can
    allPredictions = theoryPredictionsFor(database, topDict, 
            combinedResults=True )
    return_dict = {}

    ## from these results, lets create a dictionary for gambit
    for theoryPrediction in allPredictions:
        tpId = theoryPrediction.analysisId()+":"+theoryPrediction.dataType ( short=True )
        robs = theoryPrediction.getRValue()
        rexp = theoryPrediction.getRValue( expected = True )
        tp_dict = { "robs": robs, "rexp": rexp }
        if theoryPrediction.dataType() in [ 'efficiencyMap', 'combined' ]:
            theoryPrediction.computeStatistics()
            tp_dict["nll_BSM"]=theoryPrediction.likelihood ( return_nll=True )
            tp_dict["nll_SM"]=theoryPrediction.lsm ( return_nll = True )
            tp_dict["nll_min"]=theoryPrediction.lmax ( return_nll = True )
        return_dict[tpId]=tp_dict
    return return_dict


if __name__ == "__main__":
    ## simple executable to run this
    import argparse
    ap = argparse.ArgumentParser(description=\
            "first candidate for gambit/colliderbit SModelS backend")
    ap.add_argument('-f', '--slhafile', required = True,
            help='slhafile to run SModelS for', type = str )
    args = ap.parse_args()
    r = run_smodels ( args.slhafile )
    print ( r )
