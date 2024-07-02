#!/usr/bin/env python3

""" a first version of a SModelS backend for gambit/colliderbit """

import os

def run_smodels ( slhafile : os.PathLike ):
    if not os.path.exists ( slhafile ):
        print ( f"[run_smodels] slha file {slhafile} not found" )
        return
    from smodels.base.model import Model
    from smodels.share.models.SMparticles import SMList
    from smodels.particlesLoader import load
    from smodels.experiment.databaseObj import Database
    from smodels.base.physicsUnits import fb, GeV, TeV
    from smodels.decomposition import decomposer
    from smodels.base import runtime
    from smodels.matching.theoryPrediction import theoryPredictionsFor
    dbpath = "official"
    database = Database(dbpath)
    runtime.modelFile = "smodels.share.models.mssm"
    BSMList = load()
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    slhafile = os.path.abspath(os.path.expanduser(slhafile))
    model.updateParticles(inputFile=slhafile,
        ignorePromptQNumbers = ['eCharge','colordim','spin'])
    sigmacut=0.05*fb
    mingap = 5.*GeV
    topDict = decomposer.decompose(model, sigmacut, massCompress=True,
        invisibleCompress=True, minmassgap=mingap )
    allPredictions = theoryPredictionsFor(database, topDict, 
            combinedResults=True )
    return_dict = {}
    for theoryPrediction in allPredictions:
        tpId = theoryPrediction.analysisId()+":"+theoryPrediction.dataType ( short=True )
        robs = theoryPrediction.getRValue()
        rexp = theoryPrediction.getRValue( expected = True )
        tp_dict = { "robs": robs, "rexp": rexp }
        if theoryPrediction.dataType() == 'efficiencyMap':
            theoryPrediction.computeStatistics()
            tp_dict["nll_BSM"]=theoryPrediction.likelihood ( return_nll=True )
            tp_dict["nll_SM"]=theoryPrediction.lsm ( return_nll = True )
            tp_dict["nll_min"]=theoryPrediction.lmax ( return_nll = True )
        return_dict[tpId]=tp_dict

    return return_dict

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=\
            "first candidate for gambit/colliderbit SModelS backend")
    ap.add_argument('-f', '--slhafile', required = True,
            help='slhafile to run SModelS for', type = str )
    args = ap.parse_args()
    r = run_smodels ( args.slhafile )
    print ( r )
