#!/usr/bin/env python3

""" store the theory predictions in pickle """

from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment.databaseObj import Database
from smodels.theory.model import Model
import pickle, time

class Predictor:
    def __init__ ( self, walkerid ):
        self.walkerid = walkerid
        self.database=Database("../../smodels-database/") 

    def pprint ( self, *args ):
        """ logging """
        print ( "[predict:%d] %s" % (self.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        with open( "walker%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[predict:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def predict ( self, inputFile, allpreds=False, llhdonly=True ):
        """ taken an slha input file, return theory predictions 
        :param allpreds: return all predictions, not just best + combined
        :param llhdonly: return only predictions with llhds
        :returns: list of predictions
        """
        model = Model ( BSMList, SMList )
        model.updateParticles ( inputFile=inputFile )

        mingap=10*GeV
        sigmacut=0.02*fb

        self.log ( "Now decomposing" )
        topos = decomposer.decompose ( model, sigmacut, minmassgap=mingap )
        self.log ( "decomposed model into %d topologies." % len(topos) )

        listOfExpRes = self.database.getExpResults()

        bestDataSet=True
        combinedRes=True

        if allpreds:
            bestDataSet=False
            combinedRes=False

        preds = []
        self.log ( "start getting preds" )
        from smodels.tools import runtime
        runtime._experimental = True
        for expRes in listOfExpRes:
            predictions = theoryPredictionsFor ( expRes, topos, useBestDataset=bestDataSet,
                                                 combinedResults=combinedRes )
            if predictions == None:
                predictions = []
            if allpreds:
                combpreds = theoryPredictionsFor ( expRes, topos, useBestDataset=False,
                                                   combinedResults=True )
                if combpreds != None:
                    for c in combpreds:
                        predictions.append ( c )
            for prediction in predictions:
                prediction.computeStatistics()
                if (not llhdonly) or (prediction.likelihood != None):
                    preds.append ( prediction )
        self.log ( "return %s" % len(preds) )
        return preds

if __name__ == "__main__":
    inputFile="gluino_squarks.slha"
    p = Predictor ()
    predictions = p.predict ( inputFile )

    with open("predictions.pcl", "wb" ) as f:
        pickle.dump ( predictions, f )
