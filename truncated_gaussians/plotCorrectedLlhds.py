#!/usr/bin/env python3

from smodels.tools import runtime
runtime._experimental = True
from smodels.theory.theoryPrediction import theoryPredictionsFor, fiveValuesFromLimits
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
    return { "anaid": anaid, "slhafile": slhafile, "mus": mus }

def setup16033():
    anaid = "CMS-SUS-16-033"
    slhafile = "T2tt_720_80_720_80.slha"
    mus = np.arange ( -1., 1.51, .018 )
    return { "anaid": anaid, "slhafile": slhafile, "mus": mus }

def run():
    db = Database ( "debug" )
    mus = np.arange ( -1.5, 2.01, .03 )
    ret = setup16033()
    # ret = setup14021()
    anaid, slhafile, mus = ret["anaid"], ret["slhafile"], ret["mus"]

    er = db.getExpResults ( analysisIDs = [ anaid ], dataTypes = [ "upperLimit" ] )
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
    prEff = theoryPredictionsFor(erEff, toplist, combinedResults=False )
    uls, ul0s, effs = [], [], []
    for mu in mus:
        ul = prUL[0].likelihood ( mu=mu )
        if ul == None:
            print ( f"warning: ul is None for mu={mu}. (do we have euls?)" )
        uls.append ( ul )
        ret = fiveValuesFromLimits ( prUL[0], mu=mu, corr = 0.01 )
        ul0 = ret["lbsm"]
        ul0s.append ( ul0 )
        eff = prEff[0].likelihood ( mu=mu )
        # print ( mu, eff, ul, ul0 )
        effs.append ( eff )
    suls,sul0s, seffs = sum(uls), sum(ul0s), sum(effs)
    for i in range(len(uls)):
        uls[i] = uls[i] / suls
    for i in range(len(ul0s)):
        ul0s[i] = ul0s[i] / sul0s
    for i in range(len(effs)):
        effs[i] = effs[i] / seffs
    from smodels_utils.plotting import mpkitty as plt
    print ( "mus", max(uls), max(ul0s) )
    plt.plot ( mus, uls, label = "from limits, corr=0.6" )
    plt.plot ( mus, ul0s, label = "from limits, no corr" )
    plt.plot ( mus, effs, label = "from efficiencies" )
    plt.xlabel ( r"$\mu$" )
    plt.title ( f"comparison of likelihoods, {anaid}" )
    plt.legend()
    plt.savefig ( f"{anaid}.png" )
    plt.show()

if __name__ == "__main__":
    run()
