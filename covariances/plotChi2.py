#!/usr/bin/env python3

from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory import decomposer
from smodels.tools.theoryPredictionsCombiner import TheoryPredictionsCombiner
from smodels.theory.model import Model
from smodels.share.models.SMparticles import SMList
from smodels.share.models.mssm import BSMList
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import fb, GeV
from smodels_utils.plotting import mpkitty as plt
import numpy as np

def fetch():
    dbpath = "../../smodels-database/"
    database = Database( dbpath )
    dTypes = ["efficiencyMap"]
    anaids = [ 'CMS-SUS-20-004' ]
    dsids = [ 'all' ]
    results = database.getExpResults(analysisIDs=anaids,
            datasetIDs=dsids, dataTypes=dTypes, useNonValidated = True )[0]
    return results

def getTheoryPrediction( res, slhafile ):
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile)
    sigmacut = 0.005*fb
    mingap = 5.*GeV
    smstopos = decomposer.decompose(model, sigmacut, doCompress=True,
           doInvisible=True, minmassgap=mingap )
    ts = theoryPredictionsFor(res, smstopos,
        combinedResults=True, useBestDataset=False, marginalize=False)
    return ts[0]

def computeChi2s( tp, xrange : dict  ):
    chi2s = {}
    for i in np.arange ( xrange["min"], xrange["max"], xrange["delta"] ):
        llhd = tp.likelihood ( i )
        chi2 = -2.*np.log ( llhd )
        chi2s[i]= chi2
    return chi2s

def plot ( chi2, slhafile ):
    minChi2 = min ( chi2.values() )
    values = np.array ( list ( chi2.values() ) ) - minChi2
    plt.plot ( chi2.keys(), values )
    ax = plt.gca()
    ax.set_ylim ( [0,10.] )
    plt.title ( rf"$\Delta\chi^2$, {slhafile}" )
    plt.ylabel ( r"$\Delta\chi^2$")
    plt.xlabel ( r"signal strength $\mu$")
    plt.kittyPlot ( f"chi2_{slhafile}.png" )

def getSetup( i=1 ):
    bills = {}
    bills[1] = { "slhafile": "TChiHH_300_0_300_0.slha",
              "xrange": { "min": -.3, "max": 4., "delta": .1 } }
    bills[2] = { "slhafile": "TChiHH_750_0_750_0.slha",
              "xrange": { "min": -.8, "max": 4., "delta": .1 } }
    bills[3] = { "slhafile": "TChiHH_450_0_450_0.slha",
              "xrange": { "min": -.1, "max": 3., "delta": .1 } }
    return bills[i]

def main():
    res = fetch()
    for i in [ 1,2,3]:
        setup = getSetup( i)
        slhafile = setup["slhafile"]
        tp = getTheoryPrediction ( res, slhafile )
        xrange = setup["xrange"]
        chi2 = computeChi2s( tp, xrange )
        plot ( chi2, slhafile = slhafile )

if __name__ == "__main__":
    main()
