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
from ptools.helpers import py_dumps

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*RefResolver is deprecated.*",
    module=r"pyhf\.schema\.validator",
)

verbose = False

def pprint ( *args ):
    if verbose:
        return
    print ( f"[statsNLL] {' '.join(args)}" )

def keyExists ( key ):
    key_file = f"results/{key}"
    return os.path.exists  ( key_file )

def createSLHAFile() -> os.PathLike:
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
    doStaus = True
    doEWKinos = True
    masses = { 1000022: mLSP }
    decays = { 1000022: {} }
    ssms = {}
    if doEWKinos:
        masses[1000023]= mC1
        masses[1000024]= mC1
        decays[1000024]= { ( 1000022, 24 ): 1 }
        decays[1000023]= { ( 1000022, 24 ): 1 }
        decays[1000023]= { ( 1000022, 23 ): .5, ( 1000022, 25 ): .5 }
        ssms[ ( 1000023, 1000024 ) ] = 1 
        ssms[ (-1000024, 1000023 ) ] = 1
        ssms[ ( 1000023, 1000023 ) ] = 1
        ssms[ (-1000024, 1000024 ) ] = 1
    if doStaus:
        masses[1000015]= mStau
        decays[1000015]= { ( 1000022, 15 ) : 1 }
        ssms[ ( -1000015, 1000015 ) ] = 1
    pmodel = { "masses": masses, "decays": decays, "ssmultipliers": ssms }
    from protomodels.builder.manipulator import Manipulator
    from protomodels.base.runEnviron import RunEnviron
    environ = RunEnviron()
    ma = Manipulator( pmodel, environ, walkerid = "statsNLL" )
    # slhafile = "ewkinos.slha"
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
    import glob
    for fname in glob.glob ( "results/*" ):
        bname = os.path.basename ( fname )
        with open ( fname, "rt" ) as f:
            t = eval(f.read())
            ret[bname]=t
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
        anaId = p.dataset.globalInfo.id
        isOrig = True if "-orig" in anaId else False
        pprint ( f"first query of {p}" )
        nll = p.nll( asimov = None )
        pprint ( f"nll {nll}" )
        nllA = p.nll( asimov = 1. )
        pprint ( f"nllA {nllA}" )
        nllE = p.nll( expectationType = aposteriori )
        pprint ( f"nllE {nllE}" )
        nllEA = p.nll( asimov = 1., expectationType = aposteriori )
        pprint ( f"nllEA {nllEA}" )
        ul = p.getUpperLimitOnMu()
        pprint ( f"ul {ul}" )
        ulp1 = p.getUpperLimitOnMu( pmSigma = 1 )
        ulE = p.getUpperLimitOnMu( evaluationType = aposteriori )
        ulEp1 = p.getUpperLimitOnMu( evaluationType = aposteriori, pmSigma = 1 )
        nlls = { }
        # print ( f"@@X anaId is {anaId} computer is {type(p.statsComputer.upperLimitComputer)} isNN {type(p.statsComputer.upperLimitComputer)==NNUpperLimitComputer}" )
        prefix = "orig" if isOrig else "center"
        nlls[f"{prefix}ul"]=ul
        if not isOrig:
            nlls[f"{prefix}ulp1"]=ulp1
            nlls[f"{prefix}ulEp1"]=ulEp1
        nlls[f"{prefix}ulE"]=ulE
        nlls[f"{prefix}"]=nll
        nlls[f"{prefix}A"]=nllA
        nlls[f"{prefix}E"]=nllE
        nlls[f"{prefix}EA"]=nllEA
        if type(p.statsComputer.upperLimitComputer)==NNUpperLimitComputer:
            nll_p1 = p.statsComputer.upperLimitComputer.nll ( 1.,
                        pmSigma = 1 )
            nll_m1 = p.statsComputer.upperLimitComputer.nll ( 1.,
                        pmSigma = -1 )
            nll_p1A = None
            try:
                nll_p1A = p.statsComputer.upperLimitComputer.nll ( 1., asimov=1.,
                        pmSigma = 1 )
            except Exception as e:
                pass
            nll_p1E = None
            try:
                nll_p1E = p.statsComputer.upperLimitComputer.nll ( 1., 
                    evaluationType=aposteriori, pmSigma = 1 )
            except Exception as e:
                pass
            nll_p1EA = None
            try:
                nll_p1EA = p.statsComputer.upperLimitComputer.nll ( 1., asimov=1.,
                    evaluationType=aposteriori, pmSigma = 1 )
            except Exception as e:
                pass
            if nll_p1 == None:
                print ( f"[statsNLL] nll_p1 is None for {anaId}" )
            if nll_p1 != None:
                nlls["p1"] = nll_p1
            if nll_m1 != None:
                nlls["m1"] = nll_m1
            if nll_p1A != None:
                nlls["p1A"] = nll_p1A
            if nll_p1E != None:
                pprint ( f"nllEp1 nll_p1E" )
                nlls["p1E"] = nll_p1E
            if nll_p1EA != None:
                nlls["p1EA"] = nll_p1EA
        short_anaId = anaId.replace("-orig","")
        if short_anaId in res:
            res[short_anaId].update ( nlls )
        else:
            res[short_anaId]=nlls
    print ( f"[statsNLL] done with smodels" )
    if len(res)==0:
        return
    cleaned = {}
    for anaId, nlls in res.items():
        doAdd = False
        if "p1" in nlls and "orig" in nlls:
            sigma = nlls["p1"]-nlls["center"]
            delta = nlls["center"]-nlls["orig"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull"] = pull
                doAdd = True
        if "centerulp1" in nlls and "origul" in nlls:
            sigma = nlls["centerulp1"]-nlls["centerul"]
            delta = nlls["centerul"]-nlls["origul"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pullul"] = pull
                doAdd = True
        if "m1" in nlls and "orig" in nlls:
            sigma = nlls["m1"]-nlls["center"]
            delta = nlls["center"]-nlls["orig"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pullm1"] = pull
                doAdd = True
        if "p1A" in nlls and "origA" in nlls:
            sigma = nlls["p1A"]-nlls["centerA"]
            delta = nlls["centerA"]-nlls["origA"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pullA"] = pull
                doAdd = True
        if "p1E" in nlls and "origE" in nlls:
            sigma = nlls["p1E"]-nlls["centerE"]
            delta = nlls["centerE"]-nlls["origE"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pullE"] = pull
                doAdd = True
        if "p1EA" in nlls and "origEA" in nlls:
            sigma = nlls["p1EA"]-nlls["centerEA"]
            delta = nlls["centerEA"]-nlls["origEA"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pullEA"] = pull
        if doAdd:
            cleaned[anaId]=nlls
    print ( f"[statsNLL] done cleaning" )
    if len(cleaned)==0:
        return
        
    sfound = ",".join ( [ f"{anaid}: {values['pull']}" for anaid,values in cleaned.items() ] )
    print ( f"[statsNLL] found {sfound}" )
    import shutil
    if os.path.exists ( "stats" ):
        shutil.copyfile ( "stats", "stats.all" )
    key = s["key"]
    stats = readStats()
    cleaned["params"]=s
    if len(cleaned)>0:
        stats[key]=cleaned
    d1 = py_dumps ( cleaned ) + "\n"
    with open ( f"results/{key}", "wt" ) as f:
        f.write ( d1 )
    writeStats( stats )

def writeStats( stats ):
    ds = py_dumps ( stats ) + "\n"
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
            print ( f"[statsNLL.createOnePoint] {type(e)}: {e} -- ignoring" )

def create():
    import argparse
    ap = argparse.ArgumentParser(description="produces the stats for the nll pulls")
    ap.add_argument('-n', '--nprocesses',
            help='number of processes [1]',
            default = 5, type = int )
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
    verbose = True
    create()
    #stats = readStats()
    #writeStats ( stats )
    # interpret()
