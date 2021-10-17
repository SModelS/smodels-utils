#!/usr/bin/env python3

from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.experiment.databaseObj import Database
from smodels.theory import decomposer
from smodels.theory.model import Model

def run():
    db = Database ( "debug" )
    er = db.getExpResults ( analysisIDs = [ "CMS-SUS-12-024" ], dataTypes = [ "upperLimit" ] )
    erUL = er[0]
    er = db.getExpResults ( analysisIDs = [ "CMS-SUS-12-024" ], dataTypes = [ "efficiencyMap" ] )
    erEff = er[0]
    slhafile = "inputFiles/slha/"

if __name__ == "__main__":
    run()
