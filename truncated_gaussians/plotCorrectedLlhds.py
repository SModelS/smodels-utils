#!/usr/bin/env python3

from smodels.tools import runtime
runtime._experimental = True
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.experiment.databaseObj import Database
from smodels.theory import decomposer
from smodels.theory.model import Model
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
import numpy as np

def run():
    db = Database ( "debug" )
    anaid = "CMS-SUS-14-021"
    er = db.getExpResults ( analysisIDs = [ anaid ], dataTypes = [ "upperLimit" ] )
    erUL = er[0]
    er = db.getExpResults ( analysisIDs = [ anaid ], dataTypes = [ "efficiencyMap" ] )
    erEff = er[0]
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    slhafile = "T2bbWW_111_34_111_34.slha"
    model.updateParticles(inputFile=slhafile)
    toplist = decomposer.decompose(model, doCompress=True, doInvisible=True )
    prUL = theoryPredictionsFor(erUL, toplist, combinedResults=False, marginalize=False)
    prEff = theoryPredictionsFor(erEff, toplist, combinedResults=False, marginalize=False)
    uls, ul0s, effs = [], [], []
    mus = np.arange ( 0., 5., .1 )
    mus = np.arange ( -1.5, 2.01, .1 )
    for mu in mus:
        ul = prUL[0].getLikelihood ( mu=mu )
        uls.append ( ul )
        ul0 = prUL[0].likelihoodFromLimits ( mu=mu, corr = 0. )
        ul0s.append ( ul0 )
        eff = prEff[0].getLikelihood ( mu=mu )
        # print ( mu, eff, ul )
        effs.append ( eff )
    suls,sul0s, seffs = sum(uls), sum(ul0s), sum(effs)
    for i in range(len(uls)):
        uls[i] = uls[i] / suls
    for i in range(len(ul0s)):
        ul0s[i] = ul0s[i] / sul0s
    for i in range(len(effs)):
        effs[i] = effs[i] / seffs
    from smodels_utils.plotting import mpkitty as plt
    plt.plot ( mus, uls, label = "from limits" )
    plt.plot ( mus, ul0s, label = "from limits, no corr" )
    plt.plot ( mus, effs, label = "from efficiencies" )
    plt.xlabel ( r"$\mu$" )
    plt.title ( "comparison of likelihoods" )
    plt.legend()
    plt.savefig ( "llhds.png" )
    plt.show()

if __name__ == "__main__":
    run()
