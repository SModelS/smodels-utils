#!/usr/bin/env python3    

from smodels.experiment.databaseObj import Database
from smodels.decomposition import decomposer
from smodels.base import runtime
from smodels.tools.particlesLoader import load
from smodels.base.model import Model
from smodels.base.physicsUnits import GeV
import os, copy, time
from smodels.share.models.SMparticles import SMList
from smodels.matching.theoryPrediction import theoryPredictionsFor
from smodels.statistics.basicStats import observed, apriori, aposteriori

def create():
    import warnings

    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=r".*RefResolver is deprecated.*",
        module=r"pyhf\.schema\.validator",
    )
    print ( f"[statsNLL] Instantiate the database" )
    db = Database ( "../../smodels-database/" )
    print ( f"[statsNLL] Lets go" )
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
    print ( f"[statsNLL] decomposed to {len(topDict)} elements" )
    t0 = time.time()
    allPreds = theoryPredictionsFor( db, topDict, 
            combinedResults=True )
    t1 = time.time()
    print ( f"[statsNLL] we have {len(allPreds)} predictions from ML in {t1-t0:.2f}s" )
    res = {}
    for p in allPreds:
        if p.dataType() != "combined":
            continue ## irrelevant
        nll = p.nll()
        anaId = p.dataset.globalInfo.id
        isOrig = True if "-orig" in anaId else False
        nlls = { }
        anaId = anaId.replace("-orig","")
        if isOrig:
            nlls["orig"]=nll
        else:
            nlls["center"]=nll
        try:
            nll_p1 = p.statsComputer.upperLimitComputer.nll ( 1.,
                        pmSigma = 1 )
            nlls["p1"] = float ( nll_p1 )
        except TypeError as e:
            pass
        if anaId in res:
            res[anaId].update ( nlls )
        else:
            res[anaId]=nlls
    print ( res )
    from ptools.helpers import py_dumps
    cmd = "cat stats >> stats.all"
    import subprocess
    subprocess.getoutput ( cmd )
    with open ( "stats", "wt" ) as f:
        ds = py_dumps ( res )
        f.write ( ds + "\n" )

def interpret():
    with open ( "stats", "rt" ) as f:
        txt=f.read()
    d=eval(txt)
    import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

if __name__ == "__main__":
    # create()
    interpret()
