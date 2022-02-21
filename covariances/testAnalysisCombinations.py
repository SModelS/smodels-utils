#!/usr/bin/env python3

"""
.. module:: tpc
   :synopsis: Testbed for llhd combinations

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

def llhdHisto ( tpred, normalize ):
    """ create a 'histogram' of likelihood values, as a function of mu """
    ret = {}
    rng = np.arange ( -8.0, 15., .03 )
    S=0.
    for mu in rng:
        l = tpred.likelihood ( mu )
        S+=l
        ret[mu]=l
    for k,v in ret.items():
        ret[k]=v/S
    # print ( "hist", ret )
    return ret

def testConstruction():
    """ this method should simply test if the fake result and the
        covariance matrix are constructed appropriately """
    database = Database("official+../smodels-database/" )
    dTypes = ["efficiencyMap"]
    anaids = ["CMS-SUS-16-033", "CMS-SUS-13-012", "ATLAS-CONF-2013-037", "CMS-PAS-SUS-16-052-agg", "ATLAS-SUSY-2018-22", "CMS-SUS-19-006-agg", "ATLAS-SUSY-2019-09-eff", "ATLAS-SUSY-2019-09" ]
    anaids = [ "CMS-SUS-16-033", "CMS-PAS-SUS-16-052-agg", "ATLAS-SUSY-2018-22", "CMS-SUS-19-006-agg", "ATLAS-SUSY-2019-09-eff", "ATLAS-SUSY-2019-09" ]
    # anaids = ["ATLAS-SUSY-2018-22" ]
    dsids = [ "SR1_Njet2_Nb0_HT500_MHT500", "SR2_Njet3_Nb0_HT1500_MHT750", "3NJet6_1250HT1500_300MHT450", "SRtN2", "SR3_Njet5_Nb0_HT500_MHT_500" ]
    dsids = [ "all" ]
    # slhafile = "test/testFiles/slha/T1tttt.slha"
    slhafile = "T2_1233_1007_1233_1007.slha"
    # slhafile = "TChiWZ_820_680_820_680.slha"
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile)
    smstopos = decomposer.decompose(model)
    tpreds = []
    llhds = {}
    totllhd = {}
    llmin,llmax = float("inf"), 0.
    print ( f"i see {len(exp_results)} expresults" )
    for er in exp_results:
        ts = theoryPredictionsFor(er, smstopos,
            combinedResults=False, useBestDataset=False, marginalize=False)
        if ts == None:
            continue
        tsc = theoryPredictionsFor(er, smstopos,
            combinedResults=True, useBestDataset=False, marginalize=False)
        print ( f"{len(ts)} SR results, {len(tsc)} comb results" )
        # ts += tsc
        ts = tsc
        for t in ts:
            t.computeStatistics()
            dId = "combined"
            if hasattr ( t.dataset, "dataInfo" ):
                dId = t.dataset.dataInfo.dataId
            #if dId.find("_")>-1:
            #    dId = dId[:dId.find("_")]
            Id = f"{er.globalInfo.id}:{dId}"
            lsm = t.lsm()
            #thetahat_sm = t.dataset.theta_hat
            # print("er", Id, "lsm", lsm, "thetahat_sm", thetahat_sm, "lmax", t.lmax() )
            l = llhdHisto ( t, True )
            llmin = min ( list( l.values() ) + [ llmin ] )
            llmax = max ( list ( l.values() ) + [ llmax ] )
            llhds[Id]=l
            for k,v in l.items():
                if not k in totllhd:
                    totllhd[k]=1.
                totllhd[k]=totllhd[k]*v
            plt.plot ( l.keys(), l.values(), label=Id )
            tpreds.append(t)
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
    print ( "mu_hat", mu_hat, "lmax", lmax )
    ulmu = combiner.getUpperLimitOnMu()
    print ( "ulmu", ulmu )
    plt.plot ( [ ulmu, ulmu ], [ llmin, llmax*.25 ], linestyle="dotted", c="k", label=r"ul$_\mu$" )

    slha = slhafile 
    p = slha.find("_")
    if p > 0:
        slha = slha[:p]
    plt.title ( f"likelihoods {slha}" )
    plt.legend()
    plt.xlabel ( r"$\mu$" )
    plt.savefig ( "combo.png" )
    plt.kittyPlot()

if __name__ == "__main__":
    testConstruction()
