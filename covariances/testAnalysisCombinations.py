#!/usr/bin/env python3

"""
.. module:: testAnalysisCombinations
   :synopsis: Testbed for llhd combinations, plots likelihods

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import sys
sys.path.insert(0, "../")

from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory import decomposer
from smodels.tools.theoryPredictionsCombiner import TheoryPredictionsCombiner
from smodels.theory.model import Model
from smodels.share.models.SMparticles import SMList
from smodels.share.models.mssm import BSMList
from smodels.experiment.databaseObj import Database
import unittest
import numpy as np
import os
from smodels_utils.plotting import mpkitty as plt
from covariances.cov_helpers import getSensibleMuRange, computeLlhdHisto
import time

def getSetupTStauStau():
    """ collect the experimental results """
    dbpath = "../../smodels-database/"
    database = Database( dbpath )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2018-04' ]
    dsids = [ 'SRhigh', 'SRlow' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2018-04' ]

    # dsids = [ "SRtN2", "6NJet8_1000HT1250_200MHT300", "3NJet6_1250HT1500_300MHT450", "ar8" ]
    # dsids = [ 'SRWZ_6', 'SRWZ_7', 'SRWZ_8', 'SRWZ_9' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    jsonf = list ( comb_results[0].globalInfo.jsonFiles.keys() )
    ret = { "slhafile": "TStauStau_220_151_220_151.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": (-6., 10. ),
            "dictname": "staustau.dict",
            "output": "combo_1804.png"
    }
    if jsonf[0] == "simplified.json":
        ret["output"]="combo_1804simplified.png"
        ret["label"]="simplified"
    return ret

def getSetupTChiWZ():
    """ collect the experimental results """
    dbpath = "../../smodels-database/" # +../../branches/smodels-database/" 
    # dbpath = "../../smodels-database/"
    # dbpath = "../../smodels/test/database/"
    database = Database( dbpath )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2017-03', 'ATLAS-SUSY-2018-06'  ]
    dsids = [ 'SR2l_Int', 'SR_ISR', 'SR_low' ]
    dsids = [ 'SR_ISR', 'SR_low' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2018-06' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "TChiWZ_460_230_460_230.slha", 
            "SR": exp_results,
            "comb": comb_results,
            "dictname": "chiwz.dict",
            "murange": ( -4., 12. ),
            "output": "combo_1806.png"
    }
    return ret

def getSetupT6bbHH():
    """ collect the experimental results """
    dbpath = "../../smodels-database/" # +../../branches/smodels-database/" 
    # dbpath = "../../smodels-database/"
    # dbpath = "../../smodels/test/database/"
    database = Database( dbpath )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2018-31', 'ATLAS-SUSY-2018-xx'  ]
    dsids = [ 'SRB', 'SRA_M' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2018-31' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    jsonf = list ( comb_results[0].globalInfo.jsonFiles.keys() )
    ret = { "slhafile": "T6bbHH_504_241_111_504_241_111.slha", 
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -1.5, 2. ),
            "dictname": "t6bbhh.dict",
            "output": "combo_1831.png",
    }
    if "simplif" in jsonf[0]:
        ret["output"] = "combo_1831simplified.png"
        ret["label"]="simplified"
    return ret

def getSetupTChiWZ09():
    """ collect the experimental results """
    dbpath = "../../smodels-database/" # +../../branches/smodels-database/" 
    # dbpath = "../../smodels-database/"
    # dbpath = "../../smodels/test/database/"
    database = Database( dbpath )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2017-03', 'ATLAS-SUSY-2019-09'  ]
    #anaids = [ 'ATLAS-SUSY-2019-09'  ]
    dsids = [ 'SR2l_Int', 'SRWZ_10', 'SRWZ_20' ]
    #dsids = [ 'all' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2019-09' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "TChiWZ_460_230_460_230.slha", 
            "SR": exp_results,
            "comb": comb_results,
            "dictname": "1909.dict",
            "output": "combo_1909.png",
            "murange": (-4,5),
    }
    return ret

def getSetupTChiWH():
    """ collect the experimental results """
    dbpath = "../../smodels-database/" # +../../branches/smodels-database/" 
    # dbpath = "../../smodels-database/"
    # dbpath = "../../smodels/test/database/"
    database = Database( dbpath )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2017-01', 'ATLAS-SUSY-2019-08'  ]
    dsids = [ 'SRHad-Low', 'SR_MM_Low_MCT', 'SR_HM_Med_MCT' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                      datasetIDs=dsids, dataTypes=dTypes, useNonValidated=True )

    anaids = [ 'ATLAS-SUSY-2019-08' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "TChiWH_525_80_525_80.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -2.5, 2.5 ),
            "dictname": "1908.dict",
            "output": "combo_1908.png",
    }
    return ret

def testAnalysisCombo( D ):
    """ this method should simply test if the fake result and the
        covariance matrix are constructed appropriately """
    exp_results = D["SR"]
    comb_results = D["comb"]
    slhafile = D["slhafile"]
    from validation.validationHelpers import retrieveValidationFile
    retrieveValidationFile ( slhafile )
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile)
    smstopos = decomposer.decompose(model)
    tpreds = []
    llhds = {}
    totllhd = {}
    combine = []
    llmin,llmax = float("inf"), 0.
    ernames = set ( [ x.globalInfo.id for x in exp_results ] )
    print ( f"[testAnalysisCombinations] {len(exp_results)} results:", ", ".join(ernames)  )
    for er in exp_results:
        ts = theoryPredictionsFor(er, smstopos,
            combinedResults=False, useBestDataset=False, marginalize=False)
        print ( f"{ts} preds" )
        if ts == None:
            continue
        for t in ts:
            tpreds.append(t)
            combine.append(t)
    for er in comb_results:
        ts = theoryPredictionsFor(er, smstopos,
            combinedResults=True, useBestDataset=False, marginalize=False)
        print ( f"   --- {er.globalInfo.id}: {len(ts)} SR results, {len(ts)} comb results" )
        for t in ts:
            print ( f"   combined result {t.dataset.globalInfo.id}" )
        # ts = tsc
        if ts == None:
            continue
        for t in ts:
            tpreds.insert(0,t) ## put them in front so they always have same color
    #xmin, xmax = getSensibleMuRange ( tpreds )
    # xmin, xmax = -6., 10.
    xmin, xmax = -2.5, 4.5
    if "murange" in D:
        xmin, xmax = D["murange"]
            
    dictname = "llhds.dict"
    if "dictname" in D:
        dictname = D["dictname"]
    g = open ( dictname, "wt" )
    g.write ( "llhds={\n" )
    nplots = 0
    times = {}
    for t in tpreds:
        args = { "ls": "-" }
        dId = "combined"
        if hasattr ( t.dataset, "dataInfo" ):
            dId = t.dataset.dataInfo.dataId
        else:
            args["linewidth"]=2
        #if dId.find("_")>-1:
        #    dId = dId[:dId.find("_")]
        Id = f"{t.dataset.globalInfo.id}:{dId}"
        print ( f"[testAnalysisCombinations] looking at {Id}", end=" ", flush=True )
        t0 = time.time()
        t.computeStatistics()
        lsm = t.lsm()
        #thetahat_sm = t.dataset.theta_hat
        # print("er", Id, "lsm", lsm, "thetahat_sm", thetahat_sm, "lmax", t.lmax() )
        l, S = computeLlhdHisto ( t, xmin, xmax, nbins = 100, equidistant=False )
        llmin = min ( list( l.values() ) + [ llmin ] )
        llmax = max ( list ( l.values() ) + [ llmax ] )
        llhds[Id]=l
        for k,v in l.items():
            if not k in totllhd:
                totllhd[k]=1.
            if not "combine" in Id:
                totllhd[k]=totllhd[k]*v
        yv = list ( l.values() )
        if False:
            import random
            for i,y in enumerate(yv):
                yv[i]=y*random.uniform(.9,1.1)
        plt.plot ( l.keys(), yv, label=Id, **args )
        sl="{"
        for k,v in l.items():
            sl+=f"{k:.3f}: {v:.3g}, "
        if len(sl)>3:
            sl=sl[:-2]+"}"
        g.write ( f"'{Id}': {sl},\n" )
        t = time.time()
        times[Id]=(t-t0)
    g.write("}\n" )
    g.write("times={" )
    for i,(k,v) in enumerate(times.items() ):
        if i > 0:
            g.write ( ", " )
        g.write ( f"{k}: {v:.3f}" )
    g.write(str(times))
    g.write("}\n")
    g.close()
    totS = sum(totllhd.values())
    for k,v in totllhd.items():
        totllhd[k]=totllhd[k]/totS
    llmin = min ( list( totllhd.values() ) + [ llmin ] )
    llmax = max ( list ( totllhd.values() ) + [ llmax ] )

    plt.plot ( totllhd.keys(), totllhd.values(), label=r"$\Pi_i l_i$" )
    if len(tpreds)==0:
        print ( f"[testAnalysisCombinations] no tpreds found to combine" )
        sys.exit()
    print ( f"[testAnalysisCombinations] now multiplying {len(combine)} tpreds" )
    combiner = TheoryPredictionsCombiner(combine)
    combiner.computeStatistics()
    #print ( "a")
    r = combiner.getRValue()
    #print ( "r", r )
    r = combiner.getRValue( expected=True )
    #print ( "r", r )
    mu_hat, sigma_mu, lmax = combiner.findMuHat(allowNegativeSignals=True,
                                                extended_output=True)
    # mu_hat = 1.
    plt.plot ( [ mu_hat, mu_hat ], [ llmin, llmax ], linestyle="-", c="k", label=r"$\hat\mu$" )
   # plt.plot ( [ mu_hat-sigma_mu, mu_hat-sigma_mu ], [ llmin, .7*llmax ], linestyle=":", c="k" )
    #plt.plot ( [ mu_hat+sigma_mu, mu_hat+sigma_mu ], [ llmin, .7*llmax ], linestyle=":", c="k" )
    # plt.yscale ( "log" )
    ulmu = combiner.getUpperLimitOnMu()
    #ulmu = 1.
    # lmax = 1.
    print ( f"[testAnalysisCombinations] mu_hat {mu_hat:.2g} lmax {lmax:.2g} ul_mu {ulmu:.2f}" )
    plt.plot ( [ ulmu, ulmu ], [ llmin, llmax*.25 ], linestyle="dotted", c="k", label=r"ul$_\mu$" )

    slha = slhafile 
    p = slha.find("_")
    if False: # p > 0:
        slha = slha[:p]
    label = ""
    if "label" in D:
        label = D["label"]+" "
    plt.title ( f"pyhf {label}likelihoods for {slha}" )
    plt.legend()
    # plt.legend(bbox_to_anchor=(1.1, 1.05)) # place outside
    plt.xlabel ( r"$\mu$" )
    output = "combo.png"
    if "output" in D:
        output = D["output"]
    plt.savefig ( output )
    plt.kittyPlot()
    print ( f"[testAnalysisCombinations] saved to {output}" )

def runSlew():
    """ run them all """
    print ( "[testAnalysisCombinations] run all functions" )
    import sys
    funcs = dir( sys.modules[__name__] )
    setups = []
    for f in funcs:
        if f.startswith ( "getSetup" ) and not f.endswith ( "etup" ):
            setups.append ( f )
    for f in setups:
        print ( f"[testAnalysisCombinations] running {f}" )
        D = eval( f"{f}()" )
        testAnalysisCombo( D )
    sys.exit()

def getSetup():
    # D = getSetupT6bbHH()
    # D = getSetupTChiWZ()
    D = getSetupTChiWH()
    # D = getSetupTChiWZ09()
    # D = getSetupTStauStau()
    return D


if __name__ == "__main__":
    # runSlew()
    D = getSetup()
    testAnalysisCombo( D )
