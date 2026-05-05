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
from smodels_utils.helper.terminalcolors import *
import warnings
from ptools.helpers import py_dumps
import numpy as np

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*RefResolver is deprecated.*",
    module=r"pyhf\.schema\.validator",
)

flags = { "verbose": False }

def pprint ( *args ):
    if flags["verbose"] == False:
        return
    print ( f"[statsNLL] {' '.join(args)}" )

def pprintVar ( var : str, value : float ):
    pprint ( f"{var}: {value:.2f}" )

def keyExists ( key, resultsfolder ):
    key_file = f"{resultsfolder}/{key}"
    return os.path.exists  ( key_file )

def createSLHAFile( doStaus : bool, doEWKinos : bool,
                    resultsfolder : str  ) \
        -> dict:
    mLSP, mC1, mStau = 150, 300, 300
    mList = ( mLSP, mC1, mStau )
    key = abs ( hash ( mList ) )
    exists = True
    while exists:
        import random
        mLSP = int ( random.uniform ( 100, 200 ) )
        mC1 = int ( random.uniform ( mLSP + 5, 600 ) )
        mStau = int ( random.uniform ( mLSP + 10, 440 ) )
        mList = ( mLSP, mC1, mStau )
        key = abs ( hash ( mList ) )
        exists = keyExists ( key, resultsfolder )
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
    return { "file": slhafile, "mLSP": mLSP, "mC1": mC1, "key": key,
             "mStau": mStau, "doEWKinos": doEWKinos }

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

def createOnePoint( db, doStaus : bool, doEWKinos : bool, resultsfolder : str ):
    s = createSLHAFile( doStaus = doStaus, doEWKinos = doEWKinos,
                        resultsfolder = resultsfolder )
    print ( f"[statsNLL] {GREEN}---------------------------------{RESET}" )
    print ( f"[statsNLL] starting {GREEN}{s['key']}{RESET}" )
    print ( f"[statsNLL] mLSP={s['mLSP']:.1f} mStau={s['mStau']:.1f}" )
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
        pprint ( f"first query of {YELLOW}{anaId}{RESET}" )
        nll = p.nll( mu = 1., asimov = None )
        pprintVar ( "nll", nll )
        CLs = p.CLs ( mu = 1., evaluationType = observed )
        pprintVar ( "CLs", CLs )
        nll_min = p.nll_min ( )
        pprintVar ( "nll_min", nll_min )
        nllA = p.nll( mu = 1. , asimov = 1 )
        nllA_min = p.nll_min ( evaluationType = aposteriori )
        pprintVar ( "nllA_min", nllA_min )
        nllA0 = p.nll( mu = 0., asimov = 1 )
        pprintVar ( "nllA", nllA )
        print ( )
        nllE = p.nll( mu = 1., evaluationType = apriori )
        pprintVar ( "nllE", nllE )
        nllEA = p.nll( asimov = 1, evaluationType = apriori )
        pprintVar ( "nllEA", nllEA )
        ul = p.getUpperLimitOnMu( pmSigma = 0 )
        pprintVar ( "ul", ul )
        ulE = p.getUpperLimitOnMu( evaluationType = apriori )
        pprintVar ( "ulE", ulE )
        ulEpost = p.getUpperLimitOnMu( evaluationType = aposteriori )
        pprintVar ( "ulEpost", ulEpost )
        nlls = { }
        prefix = "orig" if isOrig else "nn"
        nlls[f"{prefix}_ul"]=ul
        if not isOrig:
            # print ( f"@@statsNLL now getUL for pmSigma=1" )
            ulp1 = p.getUpperLimitOnMu( pmSigma = 1 )
            pprintVar ( "ulp1", ulp1 )
            nlls[f"{prefix}_ulp1"]=ulp1
            CLsp1 = p.CLs ( mu=1, evaluationType = observed, pmSigma = 1 )
            nlls[f"{prefix}_CLsp1"]=CLsp1
            pprintVar ( "CLsp1", CLsp1 )
            ulm1 = p.getUpperLimitOnMu( pmSigma = -1 )
            pprintVar ( "ulm1", ulm1 )
            nlls[f"{prefix}_ulm1"]=ulm1
            ulEp1 = p.getUpperLimitOnMu( evaluationType = apriori, pmSigma = 1 )
            nlls[f"{prefix}_ulEp1"]=ulEp1
            pprintVar ( "ulEp1", ulEp1 )
            ulEpostp1 = p.getUpperLimitOnMu( evaluationType = aposteriori, 
                                             pmSigma = 1 )
            pprintVar ( "ulEpostp1", ulEpostp1 )
            nlls[f"{prefix}_ulEpostp1"]=ulEpostp1
            ulEm1 = p.getUpperLimitOnMu( evaluationType = apriori, pmSigma = -1 )
            nlls[f"{prefix}_ulEm1"]=ulEm1
            pprintVar ( "ulEm1", ulEm1 )
        nlls[f"{prefix}_ulE"]=ulE
        nlls[f"{prefix}_CLs"]=CLs
        nlls[f"{prefix}_ulEpost"]=ulEpost
        nlls[f"{prefix}_nll"]=nll
        nlls[f"{prefix}_nll_min"]=nll_min
        nlls[f"{prefix}_nllA"]=nllA
        nlls[f"{prefix}_nllA_min"]=nllA_min
        nlls[f"{prefix}_nllA0"]=nllA0
        nlls[f"{prefix}_nllE"]=nllE
        nlls[f"{prefix}_nllEA"]=nllEA
        if type(p.statsComputer.upperLimitComputer)==NNUpperLimitComputer:
            nll_p1 = p.nll ( mu=1., pmSigma = 1 )
            nll_m1 = p.nll ( mu=1., pmSigma = -1 )
            nllA_p1 = None
            try:
                nllA_p1 = p.nll (  mu=1., asimov=1, pmSigma = 1 )
            except Exception as e:
                pprint ( f"Exception: {e}" )
            nllE_p1 = None
            try:
                nllE_p1 = p.nll ( mu= 1., evaluationType=aposteriori,
                                  pmSigma = 1 )
                pprintVar ( "nllEp1", nllE_p1 )
            except Exception as e:
                pprint ( f"Exception: {e}" )
            nllEA_p1 = None
            try:
                nllEA_p1 = p.nll ( 1., asimov=1, evaluationType=aposteriori,
                                   pmSigma = 1 )
            except Exception as e:
                pprint ( f"Exception: {e}" )
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
        print ( )
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
        if not "nn_nll_p1" in nlls:
            print ( f"[statsNLL] no nn_nll_p1: {nlls}" )
            continue
        if not "orig_nll" in nlls:
            print ( f"[statsNLL] no orig_nll: {nlls}" )
            continue
        if "nn_nll_p1" in nlls and "orig_nll" in nlls:
            sigma = abs ( nlls["nn_nll_p1"]-nlls["nn_nll"] )
            delta = nlls["nn_nll"]-nlls["orig_nll"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_nll"] = pull
                pprintVar ( f"pull_nll", pull )
                doAdd = True
        if "nn_CLsp1" in nlls and "orig_CLs" in nlls and "nn_CLs" in nlls:
            sigma = abs ( nlls["nn_CLsp1"]-nlls["nn_CLs"] )
            delta = nlls["nn_CLs"]-nlls["orig_CLs"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_CLs"] = pull
                pprintVar ( "pull_CLs", pull )
                doAdd = True
        if "nn_ulp1" in nlls and "orig_ul" in nlls and "nn_ul" in nlls and \
                "nn_ulm1" in nlls:
            sigma1 = abs ( nlls["nn_ulp1"]-nlls["nn_ul"] )
            sigma2 = abs ( nlls["nn_ulm1"]-nlls["nn_ul"] )
            sigma = max ( sigma1, sigma2 )
            delta = nlls["nn_ul"]-nlls["orig_ul"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ul"] = pull
                pprintVar ( "pull_ul", pull )
                doAdd = True
        if "nn_ulp1" in nlls and "orig_ul" in nlls and "nn_ul" in nlls:
            sigma = abs ( nlls["nn_ulp1"]-nlls["nn_ul"] )
            delta = nlls["nn_ul"]-nlls["orig_ul"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ulp1"] = pull
                pprintVar ( "pull_ul", pull )
                doAdd = True
        if "nn_ulm1" in nlls and "orig_ul" in nlls and "nn_ul" in nlls:
            sigma = abs ( nlls["nn_ulm1"]-nlls["nn_ul"] )
            delta = nlls["nn_ul"]-nlls["orig_ul"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ulm1"] = pull
                pprintVar ( f"pull_ulm1", pull )
                doAdd = True
        if "nn_ulEp1" in nlls and "orig_ulE" in nlls:
            sigma = abs ( nlls["nn_ulEp1"]-nlls["nn_ulE"] )
            delta = nlls["nn_ulE"]-nlls["orig_ulE"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ulE"] = pull
                pprintVar ( "pull_ulE", pull )
                doAdd = True
        if "nn_ulEpostp1" in nlls and "orig_ulEpost" in nlls:
            sigma = abs ( nlls["nn_ulEpostp1"]-nlls["nn_ulEpost"] )
            delta = nlls["nn_ulEpost"]-nlls["orig_ulEpost"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ulEpost"] = pull
                pprintVar ( "pull_ulEpost", pull )
                doAdd = True
        if "nn_ulE_m1" in nlls and "orig_ulE" in nlls:
            sigma = abs ( nlls["nn_ulE_m1"]-nlls["nn_ulE"] )
            delta = nlls["nn_ulE"]-nlls["orig_ulE"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_ulE_m1"] = pull
                pprintVar ( "pull_ulE_m1", pull )
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
        if "nn_nllE_p1" in nlls and "orig_nllE" in nlls:
            sigma = abs ( nlls["nn_nllE_p1"]-nlls["nn_nllE"] )
            delta = nlls["nn_nllE"]-nlls["orig_nllE"]
            if sigma>0.:
                pull = delta / sigma
                nlls["pull_nllE"] = pull
                pprintVar ( "pull_nllE", pull )
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

    sfound = ",".join ( [ f"{anaid}: pull_nll={values['pull_nll']:.2f}" \
                          for anaid,values in cleaned.items() ] )
    # sfound = ",".join ( [ f"{anaid}" for anaid,values in cleaned.items() ] )
    print ( f"[statsNLL] found {sfound}" )
    import shutil
    if os.path.exists ( "stats" ):
        shutil.copyfile ( "stats", "stats.all" )
    key = s["key"]
    cleaned["params"]=s
    d1 = py_dumps ( cleaned ) + "\n"
    with open ( f"{resultsfolder}/{key}", "wt" ) as f:
        f.write ( d1 )


def loop( doEWKinos : bool, resultsfolder : str ):
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
            createOnePoint( db, doStaus, doEWKinos, resultsfolder )
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
    ap.add_argument( '-N', '--no_err_on_min', help="assume nll_min* to have zero errors",
                     action="store_true" )
    ap.add_argument('-e', '--ewkinos', help="add ewkinos",
                     action="store_true" )
    ap.add_argument('-r', '--resultsfolder', help="folder for results [results]",
                     default="results", type = str )
    args = ap.parse_args()
    if args.verbose:
        flags["verbose"] = True
    if args.no_err_on_min:
        from smodels.statistics.nnInterface import nnSettings
        nnSettings["errs_on_min"]=False

    for path in [ args.resultsfolder, "slhafiles" ]:
        if not os.path.exists ( path ):
            os.mkdir ( path )
    if args.nprocesses == 1:
        loop( args.ewkinos, args.resultsfolder )
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
