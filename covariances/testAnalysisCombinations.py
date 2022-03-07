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

def getExpResults():
    """ collect the experimental results """
    database = Database("official+../../smodels-database/+../../branches/smodels-database/" )
    # we assume the ~/git/smodels-database to point to the "adl" branch
    # we assume the ~/git/branches/smodels-database to point to the "pyhf" branch
    # database = Database("official+../smodels-database/" )
    dTypes = ["efficiencyMap"]
    # anaids = ["CMS-SUS-16-033", "CMS-SUS-13-012", "ATLAS-CONF-2013-037", "CMS-PAS-SUS-16-052-agg", "ATLAS-SUSY-2018-22", "CMS-SUS-19-006-agg", "ATLAS-SUSY-2019-09-eff", "ATLAS-SUSY-2019-09" ]
    # anaids = [ "CMS-SUS-16-048", "CMS-SUS-16-050-agg", "CMS-PAS-SUS-16-052-agg", "ATLAS-SUSY-2018-22", "CMS-SUS-19-006-agg", "ATLAS-SUSY-2019-09-eff" ]
    anaids = ["ATLAS-SUSY-2019-09", "CMS-SUS-16-039-agg", "ATLAS-SUSY-2018-06" ]
    anaids = [ "ATLAS-SUSY-2018-06-eff" ]
    anaids = [ "CMS-SUS-13-012", "ATLAS-CONF-2013-037" ]
    # dsids = [ "SR1_Njet2_Nb0_HT500_MHT500", "SR2_Njet3_Nb0_HT1500_MHT750", "3NJet6_1250HT1500_300MHT450", "SRtN2", "SR3_Njet5_Nb0_HT500_MHT_500" ]
    dsids = [ "3NJet6_1250HT1500_300MHT450", "SRtN2" ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    return exp_results

def testConstruction():
    """ this method should simply test if the fake result and the
        covariance matrix are constructed appropriately """
    exp_results = getExpResults()
    # slhafile = "T2_1233_1007_1233_1007.slha"
    # slhafile = "T2tt_1130_650_1130_650.slha"
    # slhafile = "test/testFiles/slha/T1tttt.slha"
    slhafile = "TChiWZ_820_680_820_680.slha"
    slhafile = "TChiWZ_460_230_460_230.slha"
    slhafile = "T1tttt.slha"
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile)
    smstopos = decomposer.decompose(model)
    tpreds = []
    llhds = {}
    totllhd = {}
    llmin,llmax = float("inf"), 0.
    ernames = set ( [ x.globalInfo.id for x in exp_results ] )
    print ( f"[testAnalysisCombinations] {len(exp_results)} results:", ", ".join(ernames)  )
    for er in exp_results:
        ts = theoryPredictionsFor(er, smstopos,
            combinedResults=False, useBestDataset=False, marginalize=False)
        if ts == None:
            continue
        tsc = theoryPredictionsFor(er, smstopos,
            combinedResults=True, useBestDataset=False, marginalize=False)
        print ( f"   --- {er.globalInfo.id}: {len(ts)} SR results, {len(tsc)} comb results" )
        for t in tsc:
            print ( f"   combined result {t.dataset.globalInfo.id}" )
        # ts += tsc
        # ts = tsc
        for t in ts:
            tpreds.append(t)
    xmin, xmax = getSensibleMuRange ( tpreds )
    xmin, xmax = -.5, .5
            
    for t in tpreds:
        t.computeStatistics()
        dId = "combined"
        if hasattr ( t.dataset, "dataInfo" ):
            dId = t.dataset.dataInfo.dataId
        #if dId.find("_")>-1:
        #    dId = dId[:dId.find("_")]
        Id = f"{t.dataset.globalInfo.id}:{dId}"
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
            totllhd[k]=totllhd[k]*v
        yv = list ( l.values() )
        if False:
            import random
            for i,y in enumerate(yv):
                yv[i]=y*random.uniform(.9,1.1)
        plt.plot ( l.keys(), yv, label=Id )
    totS = sum(totllhd.values())
    for k,v in totllhd.items():
        totllhd[k]=totllhd[k]/totS
    llmin = min ( list( totllhd.values() ) + [ llmin ] )
    llmax = max ( list ( totllhd.values() ) + [ llmax ] )

    plt.plot ( totllhd.keys(), totllhd.values(), label="total" )
    combiner = TheoryPredictionsCombiner(tpreds)
    combiner.computeStatistics()
    mu_hat, sigma_mu, lmax = combiner.findMuHat(allowNegativeSignals=True,
                                                extended_output=True)
    plt.plot ( [ mu_hat, mu_hat ], [ llmin, llmax ], linestyle="-", c="k", label=r"$\hat\mu$" )
   # plt.plot ( [ mu_hat-sigma_mu, mu_hat-sigma_mu ], [ llmin, .7*llmax ], linestyle=":", c="k" )
    #plt.plot ( [ mu_hat+sigma_mu, mu_hat+sigma_mu ], [ llmin, .7*llmax ], linestyle=":", c="k" )
    # plt.yscale ( "log" )
    ulmu = combiner.getUpperLimitOnMu()
    print ( f"[testAnalysisCombinations] mu_hat {mu_hat:.2g} lmax {lmax:.2g} ul_mu {ulmu:.2f}" )
    plt.plot ( [ ulmu, ulmu ], [ llmin, llmax*.25 ], linestyle="dotted", c="k", label=r"ul$_\mu$" )

    slha = slhafile 
    p = slha.find("_")
    if False: # p > 0:
        slha = slha[:p]
    plt.title ( f"likelihoods for {slha}" )
    plt.legend()
    # plt.legend(bbox_to_anchor=(1.1, 1.05)) # place outside
    plt.xlabel ( r"$\mu$" )
    plt.savefig ( "combo.png" )
    plt.kittyPlot()

if __name__ == "__main__":
    testConstruction()
