#!/usr/bin/env python3

from computeBills import SLParams
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory import decomposer
from smodels.tools.theoryPredictionsCombiner import TheoryPredictionsCombiner
from smodels.theory.model import Model
from smodels.share.models.SMparticles import SMList
from smodels.share.models.mssm import BSMList
from smodels.experiment.databaseObj import Database
from smodels.base.physicsUnits import fb, GeV
from smodels_utils.plotting import mpkitty as plt
import numpy as np

def fetch():
    dbpath = "../../smodels-database/"
    database = Database( dbpath )
    dTypes = ["efficiencyMap"]
    anaids = [ 'CMS-SUS-20-004-slv1' ]
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

def checkBills():
    print ( "=======" )
    print ( "Bills  " )
    print ( "=======" )
    import numpy as np
    from scipy import stats as st
    exec(open("./slHHmet_750.py").read(),globals())
    NBINS = nbins
    BG_M1 = np.array(background)
    BG_M2 = np.array(covariance).reshape([NBINS,NBINS]) #!
    #print np.linalg.eigvals(BG_M2)
    BG_M3 = np.array(third_moment)
    # BG_M3 = np.array( [0.]*len(BG_M3) )
    # print ( "BG_M3", BG_M3 )
    SIGNAL = np.array(signal)
    DATA = np.array(data)

    ## Create the key SL params objects
    slp1 = SLParams(BG_M1, BG_M2, obs=DATA, sig=SIGNAL)
    for mu in [ 0., 0.4 ]:
        nll = - slp1.maxloglike( mu )
        print ( "[checkSLV2 Bills] mu", mu, "nll", nll )

def checkSModelS():
    print ( "=======" )
    print ( "SModelS" )
    print ( "=======" )
    r = fetch()['CMS-SUS-20-004-slv1']
    slhafile = "TChiHH_750_1_750_1.slha"
    tpv1 = getTheoryPrediction ( r, slhafile )
    llhd = tpv1.likelihood ( mu=0.4, nll=True )
    print ( "[checkSLv2 SModelS] nll(0.4)=", llhd )
    llhd = tpv1.likelihood ( mu=0., nll=True )
    print ( "[checkSLv2 SModelS] nll(0.)=", llhd )

if __name__ == "__main__":
    checkBills()
    checkSModelS()
