#!/usr/bin/env python3    

from smodels.experiment.databaseObj import Database
from smodels.decomposition import decomposer
from smodels.base import runtime
from smodels.tools.particlesLoader import load
from smodels.base.model import Model
from smodels.base.physicsUnits import GeV
import os, copy, time, sys
sys.path.insert(0,"../../" )
from smodels.share.models.SMparticles import SMList
from smodels.matching.theoryPrediction import theoryPredictionsFor
from smodels.statistics.basicStats import observed, apriori, aposteriori
import warnings

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*RefResolver is deprecated.*",
    module=r"pyhf\.schema\.validator",
)

def keyExists ( key ):
    key_file = f"results/{key}"
    return os.path.exists  ( key_file )

def createSLHAFile() -> os.PathLike:
    slhafile = os.path.abspath('ewkinos.slha')
    mLSP, mC1 = 150, 300
    key = mC1*1000+mLSP
    exists = True
    while exists:
        import random
        mLSP = int ( random.uniform ( 100, 400 ) )
        mC1 = int ( random.uniform ( mLSP + 5, 1000 ) )
        key = mC1*1000+mLSP
        exists = keyExists ( key )
    masses = { 1000022: mLSP, 1000023: mC1,
               1000024: mC1 }
    decays = { 1000024: { ( 1000022, 24 ): 1 },
               1000023: { ( 1000022, 23 ): 1 },
               1000022: {} }
    ssms = { ( 1000023, 1000024 ) : 1, (-1000024, 1000023 ) : 1,
             ( 1000023, 1000023 ) : 1, (-1000024, 1000024 ) : 1 }
    pmodel = { "masses": masses, "decays": decays, "ssmultipliers": ssms }
    from protomodels.builder.manipulator import Manipulator
    from protomodels.base.runEnviron import RunEnviron
    environ = RunEnviron()
    ma = Manipulator( pmodel, environ )
    slhafile = "ewkinos.slha"
    slhafile = f"slhafiles/{key}.slha"
    ma.createSLHAFile ( slhafile, addXsecs = True )
    return { "file": slhafile, "mLSP": mLSP, "mC1": mC1, "key": key }

def readStats():
    fname = "stats"
    ret = {}
    if not os.path.exists ( fname ):
        return ret
    with open ( fname, "rt" ) as f:
        ret = eval ( f.read() )
    """
    import glob
    for f in glob.glob ( "results/*" ):
        t = eval(f.read())
    """
    return ret

def createOnePoint( db ):
    s = createSLHAFile()
    print ( f"[statsNLL] created for {s['key']}" )
    slhafile = s["file"]
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
            sigma = nlls["p1"]-nlls["center"]
            delta = nlls["center"]-nlls["orig"]
            pull = delta / sigma
            nlls["pull"] = pull
        except TypeError as e:
            pass
        if not "p1" in nlls:
            continue ## missing sigma
        if anaId in res:
            res[anaId].update ( nlls )
        else:
            res[anaId]=nlls
    print ( res )
    from ptools.helpers import py_dumps
    import shutil
    if os.path.exists ( "stats" ):
        shutil.copyfile ( "stats", "stats.all" )
    key = s["key"]
    stats = readStats()
    if len(res)>0:
        stats[key]=res
    ds = py_dumps ( stats ) + "\n"
    d1 = py_dumps ( res ) + "\n"
    with open ( f"results/{key}", "wt" ) as f:
        f.write ( d1 )
    with open ( "stats", "wt" ) as f:
        f.write ( ds )

def loop():
    print ( f"[statsNLL] Instantiate the database" )
    db = Database ( "../../smodels-database/" )
    print ( f"[statsNLL] Lets go" )
    db.getExpResults()
    while True:
        try:
            createOnePoint( db )
        except Exception as e:
            print ( f"[statsNLL] {e} -- ignoring" )

def create():
    from multiprocessing import Process
    processes = []
    for i in range(5):
        p = Process ( target = loop )
        p.start()
        processes.append ( p )
    for p in processes:
        p.join()

def interpret():
    with open ( "stats", "rt" ) as f:
        txt=f.read()
    d=eval(txt)
    import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

if __name__ == "__main__":
    create()
    print ( readStats() )
    # interpret()
