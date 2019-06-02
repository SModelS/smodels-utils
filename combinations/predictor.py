#!/usr/bin/env python3

""" store the theory predictions in pickle """

from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment.databaseObj import Database
from smodels.theory.model import Model
import pickle

def predict ( inputFile ):
    """ taken an slha input file, return theory predictions """
    model = Model ( BSMList, SMList )
    model.updateParticles ( inputFile=inputFile )

    mingap=10*GeV
    sigmacut=0.02*fb

    # print ( "[predict] Now decomposing" )
    topos = decomposer.decompose ( model, sigmacut, minmassgap=mingap )
    # print ( "[predict] decomposed model into %d topologies." % len(topos) )

    database=Database("../../smodels-database/") 
    # database=Database("../../smodels/test/database/") 
    listOfExpRes = database.getExpResults()

    ret = []
    for expRes in listOfExpRes:
        #predictions = theoryPredictionsFor ( expRes, topos, useBestDataset=True,
        #                                     combinedResults=True )
        predictions = theoryPredictionsFor ( expRes, topos, useBestDataset=False,
                                             combinedResults=False )
        if predictions == None:
            continue
        combpred = theoryPredictionsFor ( expRes, topos, useBestDataset=False,
                                             combinedResults=True )
        if combpred != None:
            for c in combpred: predictions.append ( c )
        for prediction in predictions:
            prediction.computeStatistics()
            if prediction.likelihood != None:
                ret.append ( prediction )
    return ret

if __name__ == "__main__":
    inputFile="gluino_squarks.slha"
    predictions = predict ( inputFile )

    f=open("predictions.pcl", "wb" )
    pickle.dump ( predictions, f )
    f.close()
