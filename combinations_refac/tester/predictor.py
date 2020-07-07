#!/usr/bin/env python3

""" store the theory predictions in pickle """

from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment.databaseObj import Database
from smodels.theory.model import Model
from tester.combiner import Combiner
import pickle, time, os

class Predictor:
    def __init__ ( self, walkerid, dbpath = "./default.pcl",
                   expected = False, select = "all" ):
        self.walkerid = walkerid
        self.modifier = None
        self.select = select
        self.expected = expected
        self.rthreshold = 1.7 ## threshold for rmax
        if expected:
            from expResModifier import ExpResModifier
            self.modifier = ExpResModifier()
        force_load = None
        if dbpath.endswith ( ".pcl" ):
            force_load = "pcl"
        self.database=Database( dbpath, force_load = force_load )
        self.fetchResults()

    def filterForAnaIdsTopos ( self, anaIds, topo ):
        """ filter the list of expRes, keep only anaIds """
        keepExpRes = []
        nbefore = len(self.listOfExpRes)
        for er in self.listOfExpRes:
            eid = er.globalInfo.id
            if not eid in anaIds:
                continue
            txnames = [ x.txName for x in er.getTxNames() ]
            if not topo in txnames: ## can safely skip
                continue
            newDS = []
            for dataset in er.datasets:
                newTxNames = []
                for txName in dataset.txnameList:
                    if txName.txName != topo:
                        continue
                    newTxNames.append ( txName )
                if len(newTxNames)>0:
                    dataset.txnameList = newTxNames
                    newDS.append ( dataset )
            if len(newDS)>0:
                er.datasets = newDS
                keepExpRes.append ( er )
        self.pprint ( "filtered for %s, keeping %d/%d expRes" % \
                      ( topo, len(keepExpRes), nbefore) )
        self.listOfExpRes = keepExpRes

    def filterForTopos ( self, topo ):
        """ filter the list of expRes, keep only the ones for topo """
        keepExpRes = []
        nbefore = len(self.listOfExpRes)
        for er in self.listOfExpRes:
            txnames = [ x.txName for x in er.getTxNames() ]
            if not topo in txnames: ## can safely skip
                continue
            newDS = []
            for dataset in er.datasets:
                newTxNames = []
                for txName in dataset.txnameList:
                    if txName.txName != topo:
                        continue
                    newTxNames.append ( txName )
                if len(newTxNames)>0:
                    dataset.txnameList = newTxNames
                    newDS.append ( dataset )
            if len(newDS)>0:
                er.datasets = newDS
                keepExpRes.append ( er )
        self.pprint ( "filtered for %s, keeping %d/%d expRes" % \
                      ( topo, len(keepExpRes), nbefore) )
        self.listOfExpRes = keepExpRes

    def fetchResults ( self ):
        """ fetch the list of results, perform all selecting
            and modding """

        dataTypes = [ "all" ]
        if self.select == "em":
            dataTypes = [ "efficiencyMap" ]
        if self.select == "ul":
            dataTypes = [ "upperLimit" ]

        listOfExpRes = self.database.getExpResults( dataTypes = dataTypes,
                                                    useNonValidated=True )
        if self.modifier:
            listOfExpRes = self.modifier.modify ( listOfExpRes )

        self.listOfExpRes = listOfExpRes
        if False:
            f=open("expresults.txt","wt")
            for expRes in self.listOfExpRes:
                f.write ( "%s %s\n" % (expRes.id(), expRes.datasets[0] ) )
            f.close()

    def pprint ( self, *args ):
        """ logging """
        print ( "[predict:%d] %s" % (self.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        with open( "walker%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[predict:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def predict ( self, protomodel, sigmacut = 0.02*fb,
                  strategy = "aggressive"):
        """ Compute the predictions and statistical variables.

        :returns: True
        """

        #First run SModelS using all results and considering only the best signal region.
        bestpreds = self.runSModelS( protomodel.currentSLHA, sigmacut,  allpreds=False,
                                           llhdonly=False )
        #Extract  the relevant prediction information and store in the protomodel:
        self.updateModelPredictions(protomodel,bestpreds)
        self.log ( "model is excluded? %s" % str(protomodel.excluded) )

        #Compute the maximum allowed (global) mu value given the r-values stored in protomodel
        protomodel.mumax = self.getMaxAllowedMu(protomodel)

        # now use all prediction with likelihood values to compute the Z of the model
        predictions = self.runSModelS( protomodel.currentSLHA, sigmacut, allpreds=True,
                                               llhdonly=True )
        # Compute significance and store in the model:
        self.computeSignificance( protomodel, predictions, strategy )
        self.log ( "done with prediction. best Z=%.2f (muhat=%.2f)" % ( protomodel.Z, protomodel.muhat ) )
        protomodel.cleanBestCombo()

        #Recompute predictions with higher accuracy for high score models:
        if protomodel.Z > 2.7 and protomodel.nevents < 55000:
            protomodel.nevents = 100000
            protomodel.createSLHAFile()
            self.predict(protomodel,sigmacut=sigmacut, strategy= strategy)

        return True

    def runSModelS(self, inputFile, sigmacut, allpreds, llhdonly):

        if not os.path.exists ( inputFile ):
            self.pprint ( "error, cannot find inputFile %s" % inputFile )
            return []
        model = Model ( BSMList, SMList )
        model.updateParticles ( inputFile=inputFile )

        mingap=10*GeV

        self.log ( "Now decomposing" )
        topos = decomposer.decompose ( model, sigmacut, minmassgap=mingap )
        self.log ( "decomposed model into %d topologies." % len(topos) )

        if allpreds:
            bestDataSet=False
            combinedRes=False
        else:
            bestDataSet=True
            combinedRes=True


        preds = []
        self.log ( "start getting preds" )
        from smodels.tools import runtime
        runtime._experimental = True
        for expRes in self.listOfExpRes:
            predictions = theoryPredictionsFor ( expRes, topos,
                                                 useBestDataset=bestDataSet,
                                                 combinedResults=combinedRes )
            if predictions == None:
                predictions = []
            if allpreds:
                combpreds = theoryPredictionsFor ( expRes, topos,
                                                   useBestDataset=False,
                                                   combinedResults=True )
                if combpreds != None:
                    for c in combpreds:
                        predictions.append ( c )
            for prediction in predictions:
                prediction.computeStatistics()
                if (not llhdonly) or (prediction.likelihood != None):
                    preds.append ( prediction )
        self.log ( "return %d predictions " % len(preds) )

        return preds

    def updateModelPredictions(self, protomodel, predictions):
        """ Extract information from list of theory predictions and store in the protomodel.
        :param predictions: all theory predictions
        :returns: list of tuples with observed r values, r expected and
                  theory prediction info (sorted with highest r-value first)
        """

        rvalues = [0.0,0.0] #If there are no predictions set rmax and r2 to 0
        tpList = []
        combiner = Combiner( self.walkerid )
        for theorypred in predictions:
            r = theorypred.getRValue(expected=False)
            if r == None:
                self.pprint ( "I received %s as r. What do I do with this?" % r )
                r = 23.
            rexp = theorypred.getRValue(expected=True)
            tpList.append( (r, rexp, combiner.removeDataFromTheoryPred ( theorypred ) ) )
            rvalues.append(r)
        rvalues.sort(reverse = True )
        srs = "%s" % ", ".join ( [ "%.2f" % x for x in rvalues[:3] ] )
        self.log ( "received r values %s" % srs )
        protomodel.rvalues = rvalues[:]
        protomodel.rmax = rvalues[0]
        protomodel.r2 = rvalues[1]
        protomodel.excluded = protomodel.rmax > self.rthreshold
        protomodel.tpList = tpList[:]

    def getMaxAllowedMu(self, protomodel):
        """ Compute the maximum (global) signal strength normalization
            given the predictions.
        """

        mumax = float("inf")
        if protomodel.rmax > 0.:
            mumax = self.rthreshold / protomodel.rmax

        return mumax

    def computeSignificance(self, protomodel, predictions, strategy):

        combiner = Combiner( self.walkerid )
        self.log ( "now find highest significance for %d predictions" % len(predictions) )
        ## find highest observed significance
        mumax = protomodel.mumax
        protomodel.rmax = protomodel.rmax * mumax
        protomodel.r2 = protomodel.r2 * mumax
        bestCombo,Z,llhd,muhat = combiner.findHighestSignificance ( predictions, strategy,
                                                expected=False, mumax = mumax )
        prior = combiner.computePrior ( protomodel )
        if hasattr ( protomodel, "keep_meta" ) and protomodel.keep_meta:
            protomodel.bestCombo = bestCombo
        else:
            protomodel.bestCombo = combiner.removeDataFromBestCombo ( bestCombo )
        protomodel.Z = Z
        protomodel.K = combiner.computeK ( Z, prior )
        protomodel.llhd = llhd
        protomodel.muhat = muhat
        protomodel.letters = combiner.getLetterCode(protomodel.bestCombo)
        protomodel.description = combiner.getComboDescription(protomodel.bestCombo)

if __name__ == "__main__":
    inputFile="gluino_squarks.slha"
    p = Predictor ( 0 )
    predictions = p.predict ( inputFile )

    with open("predictions.pcl", "wb" ) as f:
        pickle.dump ( predictions, f )
