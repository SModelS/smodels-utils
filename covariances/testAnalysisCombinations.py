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
import time
from smodels_utils.plotting import mpkitty as plt
from covariances.cov_helpers import getSensibleMuRange, computeLlhdHisto
from smodels.tools import runtime
runtime._experimental = True

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
    if "simplified" in jsonf[0]:
        ret["output"]="combo_1804simplified.png"
        ret["label"]="simplified"
    return ret

def getSetupRExp():
    """ collect the experimental results """
    dbpath = "../../smodels/test/database/"
    database = Database( dbpath )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-CONF-2013-037', 'CMS-SUS-13-012' ]
    dsids = [ 'SRtN3', '3NJet6_1000HT1250_600MHTinf' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "gluino_squarks.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": (-10., 20. ),
            "dictname": "rexp.dict",
            "output": "debug_rexp.png"
    }
    return ret

def getSetupSabine():
    """ collect the experimental results """
    dbpath = "../../smodels-database/"
    database = Database( dbpath )
    dTypes = ["all"]
    anaids = [ 'ATLAS-SUSY-2018-41-eff', 'CMS-SUS-20-001' ]
    dsids = [ 'all' ]
    # dsids = [ 'SRtN3', '3NJet6_1000HT1250_600MHTinf' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    #dsids = [ 'all' ]
    #comb_results = database.getExpResults(analysisIDs=anaids,
    #                                     datasetIDs=dsids, dataTypes=dTypes)
    comb_results = []
    ret = { "slhafile": "Mtwo700.0_muPos100.0.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": (-5., 6. ),
            "dictname": "rsabine.dict",
            "output": "sabine.png"
    }
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

def getSetupUL():
    """ collect the experimental results """
    dbpath = "../../smodels-database/" # +../../branches/smodels-database/"
    # dbpath = "../../smodels-database/"
    # dbpath = "../../smodels/test/database/"
    database = Database( dbpath )
    dTypes = ["all"]
    anaids = [ 'ATLAS-SUSY-2018-40' ]
    dsids = [ 'MultiBin1', 'MultiBin2', 'MultiBin3', 'SingleBin', None ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2018-31x' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    jsonf = [ "x" ]
    if len(comb_results)>0:
        jsonf = list ( comb_results[0].globalInfo.jsonFiles.keys() )
    ret = { "slhafile": "T6bbHH_504_241_111_504_241_111.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -1.5, 2. ),
            "dictname": "ul.dict",
            "output": "ul_1840.png",
    }
    if "simplif" in jsonf[0]:
        ret["output"] = "combo_1840simplified.png"
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

def writeDictFile ( dictname, llhds, times, fits, setup ):
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
    setup.pop("SR")
    setup.pop("comb")
    g.write("setup="+str(setup)+"\n" )
    g.close()


def getLlhdAt ( prodllhd, ulmu ):
    ret = 1.0
    dist=float("inf")
    for k,v in prodllhd.items():
        d = (k-ulmu)**2
        if d < dist:
            dist = d
            ret = v
    return ret

def plotLlhds ( llhds, fits, setup ):
    """ plot the likelihoods in llhds,
        additional stuff in fits, setup is the setup dictionary
    :param fits: dictionary that contains ulmu, mu_hat
    :param setup: dictionary that contains slhafile, and more
    """
    prodllhd={}
    alllhds = []
    for Id,l in llhds.items():
        args = { "ls": "-" }
        if "combine" in Id:
            args["linewidth"]=2
            args["c"]="r"
        alllhds += list( l.values() )
        for k,v in l.items():
            if not k in prodllhd:
                prodllhd[k]=1.
            if not "combine" in Id:
                prodllhd[k]=prodllhd[k]*v
        yv = list ( l.values() )
        if setup["addjitter"]:
            import random
            for i,y in enumerate(yv):
                yv[i]=y*random.uniform(.9,1.1)
        plt.plot ( l.keys(), yv, label=Id, **args )
    totS = sum(prodllhd.values())
    for k,v in prodllhd.items():
        prodllhd[k]=prodllhd[k]/totS
    llmin, llmax = 0., 1.
    if len(alllhds)>0:
        llmin = min ( alllhds )
        llmax = max ( alllhds )

    plt.plot ( prodllhd.keys(), prodllhd.values(), c="k", label=r"$\Pi_i l_i$" )

    if "mu_hat" in fits:
        mu_hat = fits["mu_hat"]
        ulmu = fits["ulmu"]
        lmax = max ( prodllhd.values() )
        print ( f"[testAnalysisCombinations] mu_hat {mu_hat:.2g} lmax {lmax:.2g} ul_mu {ulmu:.2f}" )
        # mu_hat = 1.
        plt.plot ( [ mu_hat ]*2, [ llmin, .95 * lmax ], linestyle="-.", c="k", label=r"$\hat\mu$ ($\Pi_i l_i$)" )
        llhd_ulmu = getLlhdAt ( prodllhd, ulmu )
        plt.plot ( [ ulmu ]*2, [ llmin, .95 * llhd_ulmu ], linestyle="dotted", 
                   c="k", label=r"ul$_\mu$ ($\Pi_i l_i$)" )

    if True and "llhd_combo(ul)" in fits:
        # print ( f"[testAnalysisCombinations] combo ul_mu {ulmu:.2f}" )
        llhdul = fits["llhd_combo(ul)"]  
        # print ( "[testAnalysisCombinations] llhd at", fits["muhat_combo"], "(combo) is", llhdul )
        plt.plot ( [ fits["ul_combo"] ] *2, [ llmin, .95* llhdul ], linestyle="dotted", c="r", label=r"ul$_\mu$ (pyhf combo)" )
        # lmax = llmax
        lmax = fits["lmax_combo"]
        plt.plot ( [ fits["muhat_combo"] ] *2 , [ llmin, .95 * lmax ], linestyle="-.", c="r", label=r"$\hat\mu$ (pyhf combo)" )

    if True and "llhd_ul" in fits:
        # print ( f"[testAnalysisCombinations] ul ul_mu {ulmu:.2f}" )
        llhdul = fits["llhd_ul"]  
        # print ( "llhd at", fits["ul_ul"], "is", llhdul )
        plt.plot ( [ fits["ul_ul"] ] *2, [ llmin, llhdul ], linestyle="dotted", c="r", label=r"ul$_\mu$ (pyhf ul)" )
        lmax = llmax
        plt.plot ( [ fits["muhat_ul"] ] *2 , [ llmin, .95 * lmax ], linestyle="-.", c="r", label=r"$\hat\mu$ (ul)" )



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
    plt.kittyPlot( output )
    print ( f"[testAnalysisCombinations] saved to {output}" )

def createLlhds ( tpreds, setup ):
    """ given the setup and tpreds, create llhds dicts
    """
    #xmin, xmax = getSensibleMuRange ( tpreds )
    # xmin, xmax = -6., 10.
    xmin, xmax = -2.5, 4.5
    if "murange" in setup:
        xmin, xmax = setup["murange"]

    expected = setup["expected"]
    normalize = setup["normalize"]
    times, llhds, sums = {}, {}, {}
    for t in tpreds:
        dId = "combined"
        if hasattr ( t.dataset, "dataInfo" ):
            dId = t.dataset.dataInfo.dataId
        #if dId.find("_")>-1:
        #    dId = dId[:dId.find("_")]
        Id = f"{t.dataset.globalInfo.id}:{dId}"
        print ( f"[testAnalysisCombinations] looking at {Id}", end=" ", flush=True )
        t0 = time.time()
        t.computeStatistics( expected = expected )
        lsm = t.lsm()
        #thetahat_sm = t.dataset.theta_hat
        # print("er", Id, "lsm", lsm, "thetahat_sm", thetahat_sm, "lmax", t.lmax() )
        l, S = computeLlhdHisto ( t, xmin, xmax, nbins = 100, 
                normalize = normalize, equidistant=False, expected = expected )
        llhds[Id]=l
        sums[Id] = S
        t1 = time.time()
        times[Id]=(t1-t0)
    return llhds, sums, times

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
    return llhds, times, fits, setup

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
            oldsetup = setup
            llhds, times, fits, newsetup = readDictFile ( dictname )
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
    expected = setup["expected"]
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
            if t.dataset.dataInfo.dataId == None:
                lmax = t.lmax( allowNegativeSignals = True, expected = expected )
                muhat = t.muhat( allowNegativeSignals = True, expected = expected )
                fits["muhat_ul"] = muhat
                fits["lmax_ul"] = lmax
                print ( f"[testAnalysisCombinations] UL: {t.dataset.globalInfo.id}: muhat={muhat:.3f} lmax={lmax:.3g}" )
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
        ull = ts[0].getUpperLimit()
        if type(ull) != type(None):
            ul = float ( ull / ts[0].xsection.value )
            fits["ul_combo"] = ul
            llhd_ul = ts[0].likelihood (  ul, expected = expected )
            fits["llhd_combo(ul)"] = llhd_ul
        muhat = ts[0].muhat( allowNegativeSignals = True, expected = expected )
        # print ( f"[testAnalysisCombinations] when writing {ul} {llhd_ul}" )
        fits["muhat_combo"] = muhat
        fits["lmax_combo"] = ts[0].lmax( allowNegativeSignals = True, expected= expected )
    nplots = 0
    llhds, sums, times = createLlhds ( tpreds, setup )
    if len(comb_results)>0 and len(ts)>0 and "llhd_combo(ul)" in fits:
        Id = f"{ts[0].dataset.globalInfo.id}:combined"
        if Id in sums:
            S=sums[Id]
            fits["llhd_combo(ul)"] = fits["llhd_combo(ul)"] / S
            fits["lmax_combo"] = fits["lmax_combo"] / S

    print ( f"[testAnalysisCombinations] now multiplying {len(combine)} tpreds" )
    if len(combine)>0:
        combiner = TheoryPredictionsCombiner(combine)
        combiner.computeStatistics()
        r = combiner.getRValue()
        r = combiner.getRValue( expected=True )
        mu_hat, sigma_mu, lmax = combiner.findMuHat(expected=expected,
                allowNegativeSignals=True, extended_output=True)
        ulmu = combiner.getUpperLimitOnMu( expected = expected )
        fits.update ( { "mu_hat": mu_hat, "ulmu": ulmu, "lmax": lmax } )

    plotLlhds ( llhds, fits, setup )
    if len(tpreds)==0:
        print ( f"[testAnalysisCombinations] no tpreds found to combine" )
        sys.exit()
    writeDictFile ( dictname, llhds, times, fits, setup )

def runSlew( rewrite = False ):
    """ run them all 
    :param rewrite: if true, rewrite the dicts, rerun the computations
    """
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
        setup["rewrite"]=rewrite
        testAnalysisCombo( setup )
    sys.exit()

def getSetup( rewrite = False, expected = False, addjitter=False ):
    # setup = getSetupT6bbHH()
    # setup = getSetupTChiWZ()
    # setup = getSetupTChiWH()
    # setup = getSetupTChiWZ09()
    # setup = getSetupTStauStau()
    setup = getSetupSabine()
    # setup = getSetupRExp()
    # setup = getSetupUL()
    setup["rewrite"]=rewrite
    setup["expected"]=expected
    setup["addjitter"]=addjitter
    setup["normalize"]=False
    return setup


if __name__ == "__main__":
    rewrite = True
    # runSlew( rewrite )
    setup = getSetup( rewrite, expected = True )
    testAnalysisCombo( setup )
