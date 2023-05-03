#!/usr/bin/env python3

from smodels.tools import runtime
import random
runtime._experimental = True
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.tools.statsTools import StatsComputer
from smodels.experiment.databaseObj import Database
from smodels.theory import decomposer
from smodels.theory.model import Model
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
import numpy as np
import sys

def setup14021():
    anaid = "CMS-SUS-14-021"
    slhafile = "T2bbWW_111_34_111_34.slha"
    mus = np.arange ( -1.5, 2.01, .03 )
    # alright so this should use the SRSL1c signal region,
    # which has oUL = 5.787E-01*fb and eUL = 5.777E-01*fb
    # however we get oUL_mu = 9.73E-01 and eUL_mu = 8.51E-01
    return { "anaid": anaid, "slhafile": slhafile, "mus": mus,
             "combined": False }

def pprint ( *args ):
    print ( * args )

def setup16033():
    anaid = "CMS-SUS-16-033"
    slhafile = "T2tt_720_80_720_80.slha"
    mus = np.arange ( -1., 1.51, .018 )
    # the signal region is SR6_Njet2_Nb2_HT500_MHT500
    # which has oUL = 2.46*fb, eUL = 1.85*fb  
    # however, we get oUL_mu = .218, eUL_mu = .24
    # we cannot combine
    combined = False
    return { "anaid": anaid, "slhafile": slhafile, "mus": mus,
             "combined": combined }

def setup16050():
    anaid = "CMS-SUS-16-050"
    slhafile = "T2tt_720_80_720_80.slha"
    mus = np.arange ( -1., 1.51, .018 )
    # the signal region is SR6_Njet2_Nb2_HT500_MHT500
    # which has oUL = 2.46*fb, eUL = 1.85*fb  
    # however, we get oUL_mu = .218, eUL_mu = .24
    # we cannot combine
    combined = False
    return { "anaid": anaid, "slhafile": slhafile, "mus": mus,
             "combined": combined }

def setup19006():
    anaid = "CMS-SUS-19-006"
    # anaid = "CMS-SUS-19-006-agg"
    slhafile = "T2tt_720_80_720_80.slha"
    mus = np.arange ( -.5, .5, .018 )
    # the signal region is SR6_Njet2_Nb2_HT500_MHT500
    # which has oUL = 2.46*fb, eUL = 1.85*fb  
    # however, we get oUL_mu = .218, eUL_mu = .24
    # we cannot combine
    combined = True
    return { "anaid": anaid, "slhafile": slhafile, "mus": mus, "combined": combined }

def normalizeLlhds ( container : list ):
    T = np.nansum(container)
    if T == 0.:
        return container
    for i,c in enumerate(container):
        container[i]=c/T
    return container

def normalizeNLLs ( container : list ):
    """ for NLLs we just find the minimum """
    if len(container)==0:
        return container
    nllMin = min(container)
    for i,c in enumerate(container):
        container[i]=c-nllMin
    return container

def wiggle ( container : list , r : float = .03 ):
    T = np.nansum(container)
    if T == 0.:
        return
    for i,c in enumerate(container):
        container[i]=c*random.uniform(1-r,1+r)
    return container

def run():
    dbpath = "debug" # "official"
    dbpath = "../../smodels-database" 
    db = Database ( dbpath )
    #ret = setup16033()
    # ret = setup14021()
    ret = setup19006()
    # ret = setup16050()
    combined = ret["combined"]
    mus = ret["mus"]
    anaid, slhafile, mus = ret["anaid"], ret["slhafile"], ret["mus"]
    anaidUL = anaid.replace("-agg","").replace("-adl","")

    er = db.getExpResults ( analysisIDs = [ anaidUL ], dataTypes = [ "upperLimit" ] )
    if er == []:
        print ( f"could not find an upperLimit result for {anaid}" )
        sys.exit()
    erUL = er[0]
    er = db.getExpResults ( analysisIDs = [ anaid ], dataTypes = [ "efficiencyMap" ] )
    if er == []:
        print ( f"could not find an efficiencyMap result for {anaid}" )
        sys.exit()
    erEff = er[0]
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile)
    toplist = decomposer.decompose(model, doCompress=True, doInvisible=True )
    prUL = theoryPredictionsFor(erUL, toplist, combinedResults=False )
    prEff = theoryPredictionsFor(erEff, toplist, combinedResults=combined )
    # prEff = theoryPredictionsFor(erEff, toplist, useBestDataset = not combined, combinedResults=combined )
    #pprint ( f"prEff is {prEff[0]} {prEff[0].dataset}, {len(prEff)} predictions" )
    uls, ul0s, effs = [], [], []
    ulsE, ul0sE, effsE = [], [], []
    computer = StatsComputer.forTruncatedGaussian ( prUL[0], corr = 0. )
    ret = computer.get_five_values ( False )
    # pprint ( f"truncated gaussian returned {ret}" )
    doEfficiencies = False
    for mu in mus:
        ul = prUL[0].likelihood ( mu=mu, return_nll=True )
        print ( f"ul for {mu:.2f} is {ul}" )
        if ul == None:
            print ( f"warning: ul is None for mu={mu:.2f}. (do we have euls?)" )
        uls.append ( ul )
        ul0 = computer.likelihood ( poi_test=mu, expected=False, return_nll=True )
        ul0s.append ( ul0 )
        effN = prEff[0].likelihood ( mu=mu, return_nll=True )
        eff = prEff[0].likelihood ( mu=mu, return_nll=False )
        print ( f"[plotCorrectedLlhds] llhd for {prEff[0].dataId()} {mu:.2f} is {effN},{eff}" )
        effs.append ( effN )
        if doEfficiencies:
            ulE = prUL[0].likelihood ( mu=mu, expected=True, return_nll=True )
            ulsE.append ( ulE )
            ul0E = computer.likelihood ( poi_test=mu, expected=True, return_nll=True )
            ul0sE.append ( ul0E )
            effE = prEff[0].likelihood ( mu=mu, expected=True, return_nll=True )
            effsE.append ( effE )
    for x in [ uls, ul0s, effs, ulsE, ul0sE, effsE  ]:
        normalizeNLLs ( x )
    wiggle ( uls )
    from smodels_utils.plotting import mpkitty as plt
    plt.plot ( mus, uls, label = "from limits, corr=0.6", c="r" )
    plt.plot ( mus, ul0s, label = "from limits, no corr", c="g" )
    plt.plot ( mus, effs, label = "from efficiencies", c="k" )
    if doEfficiencies:
        plt.plot ( mus, ulsE, label = "from limits, corr=0.6, expected", c="r", ls="dotted" )
        plt.plot ( mus, ul0sE, label = "from limits, no corr, expected", c="g", ls="dotted" )
        plt.plot ( mus, effsE, label = "from efficiencies, expected", ls="dotted", c="k" )
    plt.xlabel ( r"$\mu$" )
    plt.title ( f"comparison of likelihoods, {anaid}" )
    plt.legend()
    plt.savefig ( f"{anaid}.png" )
    plt.show()

if __name__ == "__main__":
    run()
