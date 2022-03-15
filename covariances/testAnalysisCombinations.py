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

def writeDictFile ( dictname, llhds, times, fits ):
    """ write out the likelihoods.dict file 
    :param dictname: name of file, e.g. likelihoods.dict
    """
    g = open ( dictname, "wt" )
    g.write ( "llhds={\n" )
    for Id,l in llhds.items():
        sl="{"
        for k,v in l.items():
            sl+=f"{k:.3f}: {v:.3g}, "
        if len(sl)>3:
            sl=sl[:-2]+"}"
        g.write ( f"'{Id}': {sl},\n" )
    g.write("}\n" )
    g.write("times={" )
    for i,(k,v) in enumerate(times.items() ):
        if i > 0:
            g.write ( ", " )
        g.write ( f"'{k}': {v:.3f}" )
    g.write("}\n")
    g.write("fits="+str(fits)+"\n" )
    g.close()

def plotLlhds ( llhds, fits, setup ):
    """ plot the likelihoods in llhds,
        additional stuff in fits, setup is the setup dictionary 
    :param fits: dictionary that contains ulmu, mu_hat
    :param setup: dictionary that contains slhafile, and more
    """
    llmin,llmax = float("inf"), 0.
    totllhd={}
    for Id,l in llhds.items():
        args = { "ls": "-" }
        if "combine" in Id:
            args["linewidth"]=2
            args["c"]="r"
        llmin = min ( list( l.values() ) + [ llmin ] )
        llmax = max ( list ( l.values() ) + [ llmax ] )
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
    totS = sum(totllhd.values())
    for k,v in totllhd.items():
        totllhd[k]=totllhd[k]/totS
    llmin = min ( list( totllhd.values() ) + [ llmin ] )
    llmax = max ( list ( totllhd.values() ) + [ llmax ] )

    plt.plot ( totllhd.keys(), totllhd.values(), label=r"$\Pi_i l_i$" )

    if True:
        mu_hat = fits["mu_hat"]
        ulmu = fits["ulmu"]
        lmax = fits["lmax"]
        print ( f"[testAnalysisCombinations] mu_hat {mu_hat:.2g} lmax {lmax:.2g} ul_mu {ulmu:.2f}" )
        # mu_hat = 1.
        plt.plot ( [ mu_hat, mu_hat ], [ llmin, llmax ], linestyle="-", c="k", label=r"$\hat\mu$ (product)" )
        plt.plot ( [ ulmu, ulmu ], [ llmin, llmax*.25 ], linestyle="dotted", c="k", label=r"ul$_\mu$ (product)" )

    if True:
        #mu_hat = fits["mu_hat"]
        ulmu = fits["ul_combo"]
        # lmax = fits["lmax"]
        print ( f"[testAnalysisCombinations] combo ul_mu {ulmu:.2f}" )
        # mu_hat = 1.
        # plt.plot ( [ mu_hat, mu_hat ], [ llmin, llmax ], linestyle="-", c="k", label=r"$\hat\mu$ (product)" )
        plt.plot ( [ ulmu, ulmu ], [ llmin, llmax*.25 ], linestyle="dotted", c="magenta", label=r"ul$_\mu$ (pyhf combo)" )

    slha = setup["slhafile"]
    p = slha.find("_")
    if False: # p > 0:
        slha = slha[:p]
    label = ""
    if "label" in setup:
        label = setup["label"]+" "
    plt.title ( f"pyhf {label}likelihoods for {slha}" )
    plt.legend()
    # plt.legend(bbox_to_anchor=(1.1, 1.05)) # place outside
    plt.xlabel ( r"$\mu$" )
    output = "combo.png"
    if "output" in setup:
        output = setup["output"]
    plt.savefig ( output )
    plt.kittyPlot()
    print ( f"[testAnalysisCombinations] saved to {output}" )

def createLlhds ( tpreds, setup ):
    """ given the setup and tpreds, create llhds dicts 
    """
    #xmin, xmax = getSensibleMuRange ( tpreds )
    # xmin, xmax = -6., 10.
    xmin, xmax = -2.5, 4.5
    if "murange" in setup:
        xmin, xmax = setup["murange"]
            
    times, llhds = {}, {}
    for t in tpreds:
        dId = "combined"
        if hasattr ( t.dataset, "dataInfo" ):
            dId = t.dataset.dataInfo.dataId
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
        llhds[Id]=l
        t1 = time.time()
        times[Id]=(t1-t0)
    return llhds, times

def readDictFile ( dictname ):
    """ read the dict file, as a cache """
    f = open ( dictname, "rt" )
    txt = f.read()
    f.close()
    try:
        exec(txt,globals())
    except Exception as e:
        print ( f"[testAnalysisCombinations] could not read dict file {dictname}, deleting" )
        os.unlink ( dictname )
        return [ None ]*3
    print ( f"[testAnalysisCombinations] recycling llhds from {dictname}, delete if you dont want that" )
    return llhds, times, fits

def testAnalysisCombo( setup ):
    """ this method should simply test if the fake result and the
        covariance matrix are constructed appropriately 
    :param setup: dictionary, describing setup
    """
    dictname = "llhds.dict"
    if not "rewrite" in setup:
        setup["rewrite"]=False
    if "dictname" in setup:
        dictname = setup["dictname"]
        if os.path.exists ( dictname ) and setup["rewrite"] == False:
            llhds, times, fits = readDictFile ( dictname )
            if llhds != None:
                plotLlhds ( llhds, fits, setup )
                return

    exp_results = setup["SR"]
    comb_results = setup["comb"]
    slhafile = setup["slhafile"]
    from validation.validationHelpers import retrieveValidationFile
    retrieveValidationFile ( slhafile )
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile)
    smstopos = decomposer.decompose(model)
    tpreds = []
    llhds = {}
    totllhd = {}
    combine = []
    ernames = set ( [ x.globalInfo.id for x in exp_results ] )
    print ( f"[testAnalysisCombinations] {len(exp_results)} results:", ", ".join(ernames)  )
    fits = {}
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
        ul = float ( ts[0].getUpperLimit() / ts[0].xsection.value )
        muhat = 1. # ts[0].muhat
        fits["ul_combo"] = ul
        fits["muhat_combo"] = muhat
    nplots = 0
    llhds, times = createLlhds ( tpreds, setup )

    print ( f"[testAnalysisCombinations] now multiplying {len(combine)} tpreds" )
    combiner = TheoryPredictionsCombiner(combine)
    combiner.computeStatistics()
    r = combiner.getRValue()
    r = combiner.getRValue( expected=True )
    mu_hat, sigma_mu, lmax = combiner.findMuHat(allowNegativeSignals=True,
                                                extended_output=True)
    ulmu = combiner.getUpperLimitOnMu()
    fits.update ( { "mu_hat": mu_hat, "ulmu": ulmu, "lmax": lmax } )

    plotLlhds ( llhds, fits, setup )
    if len(tpreds)==0:
        print ( f"[testAnalysisCombinations] no tpreds found to combine" )
        sys.exit()
    writeDictFile ( dictname, llhds, times, fits )

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
        setup = eval( f"{f}()" )
        testAnalysisCombo( setup )
    sys.exit()

def getSetup():
    # setup = getSetupT6bbHH()
    setup = getSetupTChiWZ()
    # setup = getSetupTChiWH()
    # setup = getSetupTChiWZ09()
    # setup = getSetupTStauStau()
    return setup


if __name__ == "__main__":
    # runSlew()
    setup = getSetup()
    setup["rewrite"]=False
    testAnalysisCombo( setup )
