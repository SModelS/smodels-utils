#!/usr/bin/env python3

# Import those parts of smodels that are needed for this exercise
from smodels.tools.physicsUnits import GeV
from smodels.experiment.databaseObj import Database
from smodels.tools.combinations import getCombinedUpperLimitFor
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory.decomposer import decompose
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
import pickle, random, os, glob, time
import numpy as np
from matplotlib import pyplot as plt

def getMasses ( slhafile ):
    tokens = slhafile.replace("TChiWH_","").replace(".slha","")
    tokens = tokens.split("_")
    masses = tuple( map ( int, tokens ) )[:2]
    return masses

def create( slhafile ):
    print ( "creating pickle, adding", slhafile )
    ## Load the official database
    db = Database( "../../smodels-database/" )
    D = read()
    masses = getMasses ( slhafile )
    if masses in D:
        return

    # Select desired result:
    resultID = ["ATLAS-SUSY-2019-08"]
    txname = ["TChiWH"]
    expResult = db.getExpResults( analysisIDs=resultID,txnames=txname,
                                      dataTypes='efficiencyMap')[0]
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile)
    topos = decompose ( model )
    tpreds = theoryPredictionsFor ( expResult, topos )
    llhds={}
    #xvalues = list ( np.arange(.03,1.,.03) )
    #xvalues += list ( np.arange( 1.04, 3., .1 ) )
    xvalues = list ( np.arange(.0 , 2.5, .01 ) )
    for ctr,i in enumerate(xvalues):
        print ( f"computing {i}: {ctr+1}/{len(xvalues)}" )
        llhds[i] = tpreds[1].getLikelihood(i)
    print ( "llhds", llhds )
    print ( "tpreds", tpreds )
    D = read()
    D[ masses ] = { "preds": tpreds, "llhds": llhds }
    print ( "writing out", masses )
    with open ( "cache.pcl", "wb" ) as f:
        pickle.dump ( D, f )
        f.close()

def read():
    if not os.path.exists ( "cache.pcl" ):
        return {}
    for i in range(10):
        try:
            with open ( "cache.pcl", "rb" ) as f:
                D = pickle.load ( f )
                f.close()
            return D
        except Exception as e:
            time.sleep(5.)
    raise Exception ( "stop this" )


def get95CLsb ( llhds ):
    """ from the dictionary of llhds find the 95% CLsb values """
    S = 0.
    muold=0.
    for ctr,(mu,llhd) in enumerate(llhds.items()):
        deltamu = mu - muold 
        S += deltamu * llhd
        muold = mu
    cdf = 0.
    muold=0.
    for ctr,(mu,llhd) in enumerate(llhds.items()):
        deltamu = mu - muold 
        cdf += llhd / S * deltamu
        print ( "mu", mu, "cdf", cdf )
        muold = mu

def describe():
    D=read()
    print ( D )
    
def writeAll():
    """ use glob to write for all TChiWH """
    files = glob.glob ( "TChiWH_*slha" )
    random.shuffle ( files )
    files = files[:10]
    for f in files:
        D=read()
        masses = getMasses ( f )
        p = os.fork ()
        if p == 0:
            create ( f )
        else:
            time.sleep ( 5. )
 
if __name__ == "__main__":
    writeAll()
    """
    slhafile = "TChiWH_700_100_700_100.slha"
    create( slhafile )
    tpreds, llhds = read()
    ul = tpreds[1].upperLimit
    print ( "ul", ul )
    import IPython
    IPython.embed( using=False )
    """
