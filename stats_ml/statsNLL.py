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
from smodels.statistics.nnInterface import NNUpperLimitComputer
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
    mLSP, mC1, mStau = 150, 300, 300
    mList = ( mLSP, mC1, mStau )
    key = abs ( hash ( mList ) )
    exists = True
    while exists:
        import random
        mLSP = int ( random.uniform ( 100, 300 ) )
        mC1 = int ( random.uniform ( mLSP + 5, 600 ) )
        mStau = int ( random.uniform ( mLSP + 10, 600 ) )
        mList = ( mLSP, mC1, mStau )
        key = abs ( hash ( mList ) )
        exists = keyExists ( key )
    masses = { 1000022: mLSP, 1000023: mC1,
               1000024: mC1, 1000015: mStau }
    decays = { 1000024: { ( 1000022, 24 ): 1 },
               1000023: { ( 1000022, 23 ): .5, ( 1000022, 25 ): .5 },
               1000015: { ( 1000022, 15 ) : 1 },
               1000022: {} }
    ssms = { ( 1000023, 1000024 ) : 1, (-1000024, 1000023 ) : 1,
             ( -1000015, 1000015 ) : 1,
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
    print ( f"[statsNLL] starting {s['key']}" )
    slhafile = s["file"]
    runtime.modelFile = "smodels.share.models.mssm"
    BSMList = load()
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile,
            ignorePromptQNumbers = ['eCharge','colordim','spin'])

    topDict = decomposer.decompose(model, sigmacut=0.00,
                           massCompress=True, invisibleCompress=True,
                           minmassgap=5*GeV)
    key = list(topDict.keys())[0]
    print ( f"[statsNLL] decomposed to {len(topDict[key])} elements" )
    t0 = time.time()
    allPreds = theoryPredictionsFor( db, topDict, 
            combinedResults=True )
    t1 = time.time()
    sanas = ", ".join ( [ x.dataset.globalInfo.id for x in allPreds ] )
    print ( f"[statsNLL] found {len(allPreds)} preds in {t1-t0:.1f}s: {sanas}" )
    res = {}
    for p in allPreds:
        if p.dataType() != "combined":
            continue ## irrelevant
        nll = p.nll()
        anaId = p.dataset.globalInfo.id
        isOrig = True if "-orig" in anaId else False
        nlls = { }
        # print ( f"@@X anaId is {anaId} computer is {type(p.statsComputer.upperLimitComputer)} isNN {type(p.statsComputer.upperLimitComputer)==NNUpperLimitComputer}" )
        if isOrig:
            nlls["orig"]=nll
        else:
            nlls["center"]=nll
        if type(p.statsComputer.upperLimitComputer)==NNUpperLimitComputer:
            nll_p1 = p.statsComputer.upperLimitComputer.nll ( 1.,
                        pmSigma = 1 )
            if nll_p1 == None:
                print ( f"nll_p1 is None" )
            if nll_p1 != None:
                nlls["p1"] = float ( nll_p1 )
        short_anaId = anaId.replace("-orig","")
        if short_anaId in res:
            res[short_anaId].update ( nlls )
        else:
            res[short_anaId]=nlls
    if len(res)==0:
        return
    cleaned = {}
    for anaId, nlls in res.items():
        if "p1" in nlls and "orig" in nlls:
            sigma = nlls["p1"]-nlls["center"]
            delta = nlls["center"]-nlls["orig"]
            pull = delta / sigma
            nlls["pull"] = pull
            cleaned[anaId]=nlls
        
    print ( f"[statsNLL] found {cleaned}" )
    from ptools.helpers import py_dumps
    import shutil
    if os.path.exists ( "stats" ):
        shutil.copyfile ( "stats", "stats.all" )
    key = s["key"]
    stats = readStats()
    if len(cleaned)>0:
        stats[key]=cleaned
    ds = py_dumps ( stats ) + "\n"
    d1 = py_dumps ( cleaned ) + "\n"
    with open ( f"results/{key}", "wt" ) as f:
        f.write ( d1 )
    with open ( "stats", "wt" ) as f:
        f.write ( ds )

def loop():
    print ( f"[statsNLL] Instantiate the database" )
    db = Database ( "../../smodels-database/" )
    print ( f"[statsNLL] Lets go" )
    db.getExpResults( dataTypes = "efficiencyMap" )
    while True:
        try:
            createOnePoint( db )
        except Exception as e:
            print ( f"[statsNLL] {e} -- ignoring" )

def create():
    import argparse
    ap = argparse.ArgumentParser(description="produces the stats for the nll pulls")
    ap.add_argument('-n', '--nprocesses',
            help='number of processes [1]',
            default = 1, type = int )
    args = ap.parse_args()

    for path in [ "results", "slhafiles" ]:
        if not os.path.exists ( path ):
            os.mkdir ( path )
    if args.nprocesses == 1:
        loop()
        return
    from multiprocessing import Process
    processes = []
    for i in range(args.nprocesses):
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
