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
    anaids = [ 'CMS-SUS-20-004', 'CMS-SUS-20-004-slv1' ]
    dsids = [ 'all' ]
    results = database.getExpResults(analysisIDs=anaids,
            datasetIDs=dsids, dataTypes=dTypes, useNonValidated = True )
    ret = {}
    for r in results:
        ret[r.globalInfo.id]=r
    return ret

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

def plot ( chi2v2, chi2v1, setup ):
    plt.clf()
    slhafile = setup["slhafile"]
    xrange = setup["xrange"]
    full = setup["full"]
    slv1 = setup["SLv1"]
    slv2 = setup["SLv2"]
    chi2 = chi2v2
    minChi2 = min ( chi2.values() )
    minChi2v1 = min ( chi2v1.values() )
    values = np.array ( list ( chi2.values() ) ) - minChi2
    valuesv1 = np.array ( list ( chi2v1.values() ) ) - minChi2v1
    plt.plot ( chi2.keys(), values, c="green", label="SModelS SLv2" )
    plt.plot ( chi2v1.keys(), valuesv1, c="magenta", label="SModelS SLv1" )
    plt.plot ( full[0], full[1], c="blue", label="Bill, full" )
    plt.plot ( slv1[0], slv1[1], c="black", label="Bill, slv1" )
    plt.plot ( slv2[0], slv2[1], c="red", label="Bill, slv2" )
    plt.legend()
    ax = plt.gca()
    ax.set_ylim ( [0,10.] )
    plt.title ( rf"$\Delta\chi^2$, {slhafile}" )
    plt.ylabel ( r"$\Delta\chi^2$")
    plt.xlabel ( r"signal strength $\mu$")
    plt.kittyPlot ( f"chi2_{slhafile}.png" )

def getSetup( i=1 ):
    bills = {}
    bills[1] = { "slhafile": "TChiHH_300_0_300_0.slha",
              "xrange": { "min": -.3, "max": 4., "delta": .1 },
              "full": [ [0.0, 0.0625, 0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5, 0.5625, 0.625, 0.6875, 0.75, 0.8125, 0.875, 0.9375, 1.0], [0.0009691, 0.0411193, 0.1329959, 0.2649894, 0.452793, 0.6973918, 0.9997511, 1.3608103, 1.7814781, 2.2626238, 2.8050761, 3.4096148, 4.0769662, 4.8079994, 5.6025722, 6.4611683, 7.3840528] ],
              "SLv1": [ [0.0, 0.034482758620689655, 0.06896551724137931, 0.10344827586206896, 0.13793103448275862, 0.1724137931034483, 0.20689655172413793, 0.24137931034482757, 0.27586206896551724, 0.3103448275862069, 0.3448275862068966, 0.3793103448275862, 0.41379310344827586, 0.4482758620689655, 0.48275862068965514, 0.5172413793103449, 0.5517241379310345, 0.5862068965517241, 0.6206896551724138, 0.6551724137931034, 0.6896551724137931, 0.7241379310344828, 0.7586206896551724, 0.7931034482758621, 0.8275862068965517, 0.8620689655172413, 0.896551724137931, 0.9310344827586207, 0.9655172413793103, 1.0] , [3.5605982077266276, 3.055926561300282, 2.599778420875964, 2.189080004033201, 1.8210323828741366, 1.4930930272218745, 1.2029553514756515, 0.9485274740352736, 0.7279119100369371, 0.5393856985843968, 0.38138225036115614, 0.25247489990971417, 0.1513615642035404, 0.07685139697659338, 0.027852748256577797, 0.0033624770625237943, 0.0024565607890849606, 0.024281739891648613, 0.06804819128754502, 0.13302301536140249, 0.21852464449273157, 0.32391771864990915, 0.44860857446957425, 0.5920414065994919, 0.7536947497766278, 0.9330784140049673, 1.1297308290714057, 1.3432157787342192, 1.5731218432721903, 1.8190589880712196]],
              "SLv2": [ [0.0, 0.034482758620689655, 0.06896551724137931, 0.10344827586206896, 0.13793103448275862, 0.1724137931034483, 0.20689655172413793, 0.24137931034482757, 0.27586206896551724, 0.3103448275862069, 0.3448275862068966, 0.3793103448275862, 0.41379310344827586, 0.4482758620689655, 0.48275862068965514, 0.5172413793103449, 0.5517241379310345, 0.5862068965517241, 0.6206896551724138, 0.6551724137931034, 0.6896551724137931, 0.7241379310344828, 0.7586206896551724, 0.7931034482758621, 0.8275862068965517, 0.8620689655172413, 0.896551724137931, 0.9310344827586207, 0.9655172413793103, 1.0], [1.957612574767552, 1.6169531482366892, 1.3131524231702087, 1.0449536236410495, 0.8109718740695655, 0.6097527570845784, 0.4398200033721764, 0.2997198644524701, 0.18804493993789606, 0.10345575961520126, 0.044691664018955635, 0.010575955446483931, 1.70333142364143e-05, 0.012006398409027952, 0.045614931654483826, 0.09998788226627653, 0.1743396451908268, 0.2679481498931864, 0.3801494285609124, 0.5103325132388647, 0.657934401925246, 0.8224358064127557, 1.0033568729689364, 1.2002535419775597, 1.4127141841139519, 1.6403565058124059, 1.8828249269402022, 2.1397880757195935, 2.4109366036816198, 2.6959813146726788] ] }
    bills[2] = { "slhafile": "TChiHH_750_0_750_0.slha",
              "xrange": { "min": -.8, "max": 4., "delta": .1 },
               "full": [[],[]], "SLv2": [[],[]], "SLv1": [[],[]] }
    bills[3] = { "slhafile": "TChiHH_450_0_450_0.slha",
              "xrange": { "min": -.1, "max": 3., "delta": .1 },
               "full": [[],[]], "SLv2": [[],[]], "SLv1": [[],[]] }
    return bills[i]

def main():
    res = fetch()
    for i in [ 1,2,3]:
        setup = getSetup( i)
        slhafile = setup["slhafile"]
        tpV2 = getTheoryPrediction ( res["CMS-SUS-20-004"], slhafile )
        tpV1 = getTheoryPrediction ( res["CMS-SUS-20-004-slv1"], slhafile )
        xrange = setup["xrange"]
        chi2v2 = computeChi2s( tpV2, xrange )
        chi2v1 = computeChi2s( tpV1, xrange )
        plot ( chi2v2, chi2v1, setup )

if __name__ == "__main__":
    main()
