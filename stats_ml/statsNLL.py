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
import numpy as np

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*RefResolver is deprecated.*",
    module=r"pyhf\.schema\.validator",
)

verbose = False

def pprint ( *args ):
    if verbose == False:
        return
    print ( f"[statsNLL] {' '.join(args)}" )

def keyExists ( key ):
    key_file = f"results/{key}"
    return os.path.exists  ( key_file )

def createSLHAFile( doStaus : bool = True, doEWKinos : bool = False ) \
        -> os.PathLike:
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

def createOnePoint( db, doStaus : bool, doEWKinos : bool ):
    s = createSLHAFile( doStaus = doStaus, doEWKinos = doEWKinos )
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
        nll = p.nll( mu = 1., asimov = None )
        pprint ( f"nll {nll}" )
        nll_min = p.nll_min ( )
        pprint ( f"nll_min {nll_min}" )
        nllA = p.nll( mu = 1. , asimov = 1 )
        if not hasattr ( p, "nll_min" ):
            print ( f"@@X {p} {type(p)} doesnt have a nll_min" )
        nllA_min = p.nll_min ( evaluationType = aposteriori )
        pprint ( f"nllA_min {nllA_min}" )
        nllA0 = p.nll( mu = 0., asimov = 1 )
        pprint ( f"nllA {nllA}" )
        print ( )
        print ( f"@@UTIL0 get nll for mu=1 aposteriori isOrig {isOrig} no pmSigma" )
        nllE = p.nll( mu = 1., evaluationType = aposteriori)
        pprint ( f"nllE {nllE}" )
        print ( f"@@UTIL1 nllE {nllE}" )
        print ( )
        nllEA = p.nll( asimov = 1, evaluationType = aposteriori )
        pprint ( f"nllEA {nllEA}" )
        ul = p.getUpperLimitOnMu( pmSigma = 0 )
        pprint ( f"ul {ul}" )
        ulE = p.getUpperLimitOnMu( evaluationType = aposteriori )
        pprint ( f"ulE {ulE}" )
        nlls = { }
        prefix = "orig" if isOrig else "nn"
        nlls[f"{prefix}_ul"]=ul
        if not isOrig:
            ulp1 = p.getUpperLimitOnMu( pmSigma = 1 )
            pprint ( f"ulp1 {ulp1}" )
            nlls[f"{prefix}_ulp1"]=ulp1
            ulm1 = p.getUpperLimitOnMu( pmSigma = -1 )
            pprint ( f"ulm1 {ulm1}" )
            nlls[f"{prefix}_ulm1"]=ulm1
            ulEp1 = p.getUpperLimitOnMu( evaluationType = aposteriori, pmSigma = 1 )
            nlls[f"{prefix}_ulEp1"]=ulEp1
            pprint ( f"ulEp1 {ulEp1}" )
            ulEm1 = p.getUpperLimitOnMu( evaluationType = aposteriori, pmSigma = -1 )
            nlls[f"{prefix}_ulEm1"]=ulEm1
            pprint ( f"ulEm1 {ulEm1}" )
        nlls[f"{prefix}_ulE"]=ulE
        nlls[f"{prefix}_nll"]=nll
        nlls[f"{prefix}_nll_min"]=nll_min
        nlls[f"{prefix}_nllA"]=nllA
        nlls[f"{prefix}_nllA_min"]=nllA_min
        nlls[f"{prefix}_nllA0"]=nllA0
        nlls[f"{prefix}_nllE"]=nllE
        nlls[f"{prefix}_nllEA"]=nllEA
        if type(p.statsComputer.upperLimitComputer)==NNUpperLimitComputer:
            nll_p1 = p.statsComputer.upperLimitComputer.nll ( 1.,
                        pmSigma = 1 )
            nll_m1 = p.statsComputer.upperLimitComputer.nll ( 1.,
                        pmSigma = -1 )
            nllA_p1 = None
            try:
                nllA_p1 = p.statsComputer.upperLimitComputer.nll (
                        mu=1., asimov=1, pmSigma = 1 )
            except Exception as e:
                pass
            nllE_p1 = None
            try:
                nllE_p1 = p.nll ( mu= 1., evaluationType=aposteriori,
                                  pmSigma = 1 )
                nllE_p1 = p.statsComputer.upperLimitComputer.nll ( 1.,
                    evaluationType=aposteriori, pmSigma = 1 )
                print ( f"@@UTIL2 nllE_p1 {nllE_p1}" )
                pprint ( f"nllEp1 {nll_p1E}" )
            except Exception as e:
                pass
            nllEA_p1 = None
            try:
                nllEA_p1 = p.statsComputer.upperLimitComputer.nll ( 1., asimov=1,
                    evaluationType=aposteriori, pmSigma = 1 )
            except Exception as e:
                pass
            if nll_p1 == None:
                print ( f"[statsNLL] nll_p1 is None for {anaId}" )
            if nll_p1 != None:
                nlls[f"{prefix}_nll_p1"] = nll_p1
            if nll_m1 != None:
                nlls[f"{prefix}_nll_m1"] = nll_m1
            if nllA_p1 != None:
                nlls[f"{prefix}_nllA_p1"] = nllA_p1
            if nllE_p1 != None:
                nlls[f"{prefix}_nllE_p1"] = nllE_p1
            if nllEA_p1 != None:
                nlls[f"{prefix}_nllEA_p1"] = nllEA_p1
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
        newnlls = {}
        for k,v in nlls.items():
            ## drop the infinities
            if not np.isfinite(v):
                continue
            newnlls[k]=v
        nlls = newnlls
        doAdd = False
        if "nn_nll_p1" in nlls and "orig_nll" in nlls:
            sigma = abs ( nlls["nn_nll_p1"]-nlls["nn_nll"] )
            delta = nlls["nn_nll"]-nlls["orig_nll"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_nll"] = pull
                doAdd = True
        if "nn_ulp1" in nlls and "orig_ul" in nlls:
            sigma = abs ( nlls["nn_ulp1"]-nlls["nn_ul"] )
            delta = nlls["nn_ul"]-nlls["orig_ul"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ul"] = pull
                pprint ( f"pull_ul {pull}" )
                doAdd = True
        if "nn_ulm1" in nlls and "orig_ul" in nlls:
            sigma = abs ( nlls["nn_ulm1"]-nlls["nn_ul"] )
            delta = nlls["nn_ul"]-nlls["orig_ul"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ulm1"] = pull
                pprint ( f"pull_ulm1 {pull}" )
                doAdd = True
        if "nn_ulEp1" in nlls and "orig_ulE" in nlls:
            sigma = abs ( nlls["nn_ulEp1"]-nlls["nn_ulE"] )
            delta = nlls["nn_ulE"]-nlls["orig_ulE"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ulE"] = pull
                pprint ( f"pull_ulE {pull}" )
                doAdd = True
        if "nn_ulE_m1" in nlls and "orig_ulE" in nlls:
            sigma = abs ( nlls["nn_ulE_m1"]-nlls["nn_ulE"] )
            delta = nlls["nn_ulE"]-nlls["orig_ulE"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ulE_m1"] = pull
                pprint ( f"pull_ulE_m1 {pull}" )
                doAdd = True
        if "nn_nll_m1" in nlls and "orig_nll" in nlls:
            sigma = abs ( nlls["nn_nll_m1"]-nlls["orig_nll"] )
            delta = nlls["nn_nll"]-nlls["orig_nll"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_nll_m1"] = pull
                doAdd = True
        if "nn_nllA_p1" in nlls and "orig_nllA" in nlls:
            sigma = abs ( nlls["nn_nllA_p1"]-nlls["nn_nllA"] )
            delta = nlls["nn_nllA"]-nlls["orig_nllA"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_nllA"] = pull
                doAdd = True
        if "nn_nllE_p1E" in nlls and "orig_nllE" in nlls:
            sigma = abs ( nlls["nn_nllE_p1"]-nlls["nn_nllE"] )
            delta = nlls["nn_nllE"]-nlls["orig_nllE"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_nllE"] = pull
                doAdd = True
        if "nn_nllEA_p1" in nlls and "orig_nllEA" in nlls:
            sigma = abs ( nlls["nn_nllEA_p1"]-nlls["nn_nllEA"] )
            delta = nlls["nn_nllEA"]-nlls["orig_nllEA"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_nllEA"] = pull
        if doAdd:
            cleaned[anaId]=nlls
    print ( f"[statsNLL] done cleaning" )
    if len(cleaned)==0:
        return

    sfound = ",".join ( [ f"{anaid}: pull_nll={values['pull_nll']:.2f}" for anaid,values in cleaned.items() ] )
    print ( f"[statsNLL] found {sfound}" )
    import shutil
    if os.path.exists ( "stats" ):
        shutil.copyfile ( "stats", "stats.all" )
    key = s["key"]
    cleaned["params"]=s
    d1 = py_dumps ( cleaned ) + "\n"
    with open ( f"results/{key}", "wt" ) as f:
        f.write ( d1 )
    """
    stats = readStats()
    if len(cleaned)>0:
        stats[key]=cleaned
    writeStats( stats )
    """

"""
def writeStats( stats ):
    ds = py_dumps ( stats ) + "\n"
    with open ( "stats", "wt" ) as f:
        f.write ( ds )
"""

def loop( doEWKinos : bool ):
    print ( f"[statsNLL] Instantiate the database" )
    db = Database ( "../../smodels-database/" )
    print ( f"[statsNLL] Lets go" )
    anaIds = [ "ATLAS-SUSY-2018-04" ]
    if doEWKinos:
        anaIds = [ "ATLAS-SUSY-2018-04", "ATLAS-SUSY-2019-09",
                   "ATLAS-SUSY-2019-08", "ATLAS-SUSY-2018-16",
                   "ATLAS-SUSY-2018-32" ]
    all_ids = []
    for aid in anaIds:
        all_ids.append ( aid )
        all_ids.append ( aid+"-orig" )
    db.getExpResults( analysisIDs = all_ids, dataTypes = "efficiencyMap" )
    doStaus = True
    # doEWKinos = False
    while True:
        try:
            createOnePoint( db, doStaus, doEWKinos )
        except Exception as e:
            print ( f"[statsNLL.createOnePoint] {type(e)}: {e} -- ignoring" )
            import traceback
            traceback.print_exc()

def create():
    import argparse
    ap = argparse.ArgumentParser(description="produces the stats for the nll pulls")
    ap.add_argument('-n', '--nprocesses',
            help='number of processes [1]',
            default = 5, type = int )
    ap.add_argument( '-v', '--verbose', help="be more verbose",
                     action="store_true" )
    ap.add_argument('-e', '--ewkinos', help="add ewkinos",
                     action="store_true" )
    args = ap.parse_args()
    if args.verbose:
        verbose = True

    for path in [ "results", "slhafiles" ]:
        if not os.path.exists ( path ):
            os.mkdir ( path )
    if args.nprocesses == 1:
        loop( args.ewkinos )
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
    #stats = readStats()
    #writeStats ( stats )
    # interpret()
