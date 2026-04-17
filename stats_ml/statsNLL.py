#!/usr/bin/env python3    

from smodels.experiment.databaseObj import Database
from smodels.decomposition import decomposer
from smodels.base import runtime
from smodels.tools.particlesLoader import load
from smodels.base.model import Model
from smodels.base.physicsUnits import GeV
import os, copy
from smodels.share.models.SMparticles import SMList
from smodels.matching.theoryPrediction import theoryPredictionsFor
from smodels.statistics.basicStats import observed, apriori, aposteriori

def removeAllMLModels ( db : Database ):
    ers = db.getExpResults()
    for er in ers:
        if hasattr ( er.globalInfo, "mlModel" ):
            del er.globalInfo.mlModel

def run():
    import warnings

    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=r".*RefResolver is deprecated.*",
        module=r"pyhf\.schema\.validator",
    )
    print ( f"Instantiate the dataabases" )
    db = Database ( "../../smodels-database/" )
    db2 = Database ( "../../smodels-database/" )
    print ( f"Lets go" )
    removeAllMLModels ( db2 )
    db.getExpResults()
    slhafile = os.path.abspath('ewkinos.slha')
    runtime.modelFile = "smodels.share.models.mssm"
    BSMList = load()
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile,
            ignorePromptQNumbers = ['eCharge','colordim','spin'])

    topDict = decomposer.decompose(model, sigmacut=0.001,
                           massCompress=True, invisibleCompress=True,
                           minmassgap=5*GeV)
    allPredsML = theoryPredictionsFor( db, topDict, 
            combinedResults=True )
    allPredsNoML = theoryPredictionsFor( db, topDict, 
            combinedResults=True )

    for p in allPredsML:
        nll = p.nll()
        print ( p.globalInfo.id, nll )

    for p in allPredsNoML:
        nll = p.nll()
        print ( p.globalInfo.id, nll )

if __name__ == "__main__":
    run()
