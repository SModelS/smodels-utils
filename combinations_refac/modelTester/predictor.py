#!/usr/bin/env python3

""" store the theory predictions in pickle """

from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment.databaseObj import Database
from smodels.theory.model import Model
import pickle, time, os

class Predictor:
    def __init__ ( self, walkerid, dbpath = "./default.pcl",
                   expected = False, select = "all" ):
        self.walkerid = walkerid
        self.modifier = None
        self.select = select
        self.expected = expected
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

    def predict ( self, inputFile, allpreds=False, llhdonly=True,
                  sigmacut = 0.02*fb ):
        """ taken an slha input file, return theory predictions
        :param allpreds: return all predictions, not just best + combined
        :param llhdonly: return only predictions with llhds
        :returns: list of predictions
        """
        if not os.path.exists ( inputFile ):
            self.pprint ( "error, cannot find inputFile %s" % inputFile )
            return []
        model = Model ( BSMList, SMList )
        model.updateParticles ( inputFile=inputFile )

        mingap=10*GeV

        self.log ( "Now decomposing" )
        topos = decomposer.decompose ( model, sigmacut, minmassgap=mingap )
        self.log ( "decomposed model into %d topologies." % len(topos) )


        bestDataSet=True
        combinedRes=True

        if allpreds:
            bestDataSet=False
            combinedRes=False

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

if __name__ == "__main__":
    inputFile="gluino_squarks.slha"
    p = Predictor ( 0 )
    predictions = p.predict ( inputFile )

    with open("predictions.pcl", "wb" ) as f:
        pickle.dump ( predictions, f )
