#!/usr/bin/env python3

""" a simple class that performs global modifications on a list of results.
Used to ``take out potential signals'' i.e. put all observations to values
expected from background, by sampling the background model. """

import copy, os, sys, time, subprocess
from scipy import stats
from protomodel import ProtoModel
from manipulator import Manipulator
from smodels.tools.physicsUnits import fb, GeV
from smodels.theory.model import Model
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory import decomposer

class ExpResModifier:
    def __init__ ( self, modificationType = "expected" ):
        self.modificationType = modificationType
        self.protomodel = None
        self.logfile = "modifier.log"
        self.startLogger()

    def interact ( self, listOfExpRes ):
        import IPython
        IPython.embed( using=False )

    def bgUpperLimit ( self, dataset ):
        """ fix the upper limits, use expected (if exists) as observed """
        for i,txname in enumerate(dataset.txnameList):
            if hasattr ( txname, "txnameDataExp" ) and txname.txnameDataExp != None:
                self.log ( "fixing UL result %s" % dataset.globalInfo.id )
                txnd = copy.deepcopy ( txname.txnameDataExp )
                dataset.txnameList[i].txnameData = txnd
        return dataset

    def pprint ( self, *args ):
        """ logging """
        print ( "[expResModifier] %s" % ( " ".join(map(str,args))) )
        with open( self.logfile, "a" ) as f:
            f.write ( "[modifier] %s\n" % ( " ".join(map(str,args)) ) )

    def startLogger ( self ):
        subprocess.getoutput ( "mv %s modifier.old" % self.logfile )

    def log ( self, *args ):
        """ logging to file """
        # logfile = "walker%d.log" % self.walkerid
        with open( self.logfile, "a" ) as f:
            f.write ( "[modifier] %s\n" % ( " ".join(map(str,args)) ) )

    def produceProtoModel ( self, filename ):
        """ try to produce a protomodel from pmodel
        :param filename: filename of pmodel dictionary
        :returns: none if not succesful, else protomodel object
        """
        if filename == "":
            return None
        if not os.path.exists ( filename ):
            self.pprint ( "When trying to construct protomodel, %s does not exist" % filename )
            return None
        walkerid = 0
        dbpath = "../../smodels-database/"
        expected = False
        select = "all"
        keep_meta = True
        M = ProtoModel ( walkerid, dbpath, expected, select, keep_meta )
        M.createNewSLHAFileName ( prefix="erm" )
        ma = Manipulator ( M )
        with open ( filename, "rt" ) as f:
            m = eval ( f.read() )
        ma.initFromDict ( m )
        ma.M.computeXSecs(nevents=10000 )
        ma.printXSecs()
        self.protomodel = ma.M
        return self.protomodel

    def modifyDatabase ( self, db, outfile="", suffix="fake1", pmodel="" ):
        """ modify the database, possibly write out to a pickle file
        :param outfile: if not empty, write the database into file
        :param suffix: suffix to append to database version
        :param pmodel: if not empty, then this is the file name of the signal
                       model. in this case fake a signal
        :returns: the database
        """
        listOfExpRes = db.getExpResults()
        self.produceProtoModel ( pmodel )
        self.log ( "%d results before faking bgs" % len(listOfExpRes) )
        updatedListOfExpRes = self.fakeBackgrounds ( listOfExpRes )
        self.log ( "%d results after faking bgs" % len(updatedListOfExpRes) )
        updatedListOfExpRes = self.addSignals ( updatedListOfExpRes )
        self.log ( "%d results after adding signals" % len(updatedListOfExpRes) )
        db.expResultList = updatedListOfExpRes
        newver = db.databaseVersion + suffix
        db.txt_meta.databaseVersion = newver
        db.pcl_meta.databaseVersion = newver
        self.pprint ( "Constructed fake database with %d (of %d) results" % \
                ( len(updatedListOfExpRes), len(listOfExpRes) ) )
        if outfile != "":
            db.createBinaryFile( outfile )
        return db

    def sampleEfficiencyMap ( self, dataset ):
        """ for the given dataset,
        sample from background and put the value as observed """
        orig = dataset.dataInfo.observedN
        exp = dataset.dataInfo.expectedBG
        err = dataset.dataInfo.bgError
        lmbda = stats.norm.rvs ( exp, err )
        if lmbda < 0.:
            lmbda = 0.
        obs = stats.poisson.rvs ( lmbda )
        self.log ( "effmap replacing nobs=%.2f (bg=%.2f) by nobs=%.2f for %s" % \
                ( orig, exp, obs, dataset.globalInfo.id ) )
        dataset.dataInfo.observedN = obs
        dataset.dataInfo.origN = orig
        return dataset

    def addSignalForEfficiencyMap ( self, dataset, tpred, lumi ):
        """ add a signal to this efficiency map. background sampling is
            already taken care of """
        self.log ( " `- add EM matching tpred %s/%s: %s" % \
                ( tpred.analysisId(), tpred.dataId(), tpred.xsection.value ) )
        orig = dataset.dataInfo.observedN
        sigLambda = float ( tpred.xsection.value * lumi )
        sigN = stats.poisson.rvs ( sigLambda )
        self.log ( "effmap adding sigN=%.2f to %.2f" % \
                   ( sigN, orig ) )
        dataset.dataInfo.observedN = orig + sigN
        return dataset

    def addSignalForULMap ( self, dataset, tpred, lumi ):
        """ add a signal to this UL result. background sampling is
            already taken care of """
        self.log ( " `- add UL matching tpred %s/%s: %s" % \
                ( tpred.analysisId(), tpred.dataId(), tpred.xsection.value ) )
        sigmaN = tpred.xsection.value.asNumber(fb)
        for i,txname in enumerate(dataset.txnameList):
            txnd = txname.txnameData
            for yi,y in enumerate(txnd.y_values):
                txnd.y_values[yi]+=sigmaN
            dataset.txnameList[i].txnameData = txnd
        return dataset

    def produceTopoList ( self ):
        """ create smstopolist """
        model = Model ( BSMList, SMList )
        model.updateParticles ( inputFile=self.protomodel.currentSLHA )
        mingap=10*GeV
        sigmacut = 0.02*fb
        self.topos = decomposer.decompose ( model, sigmacut, minmassgap=mingap )

    def addSignals ( self, listOfExpRes ):
        """ thats the method that adds a typical signal """
        if self.protomodel == None:
            return listOfExpRes
        self.log ( "now adding the signals" )
        ret = []
        self.produceTopoList()
        for expRes in listOfExpRes:
            tpreds = theoryPredictionsFor ( expRes, self.topos )
            if tpreds == None:
                ret.append ( expRes )
                continue
            lumi = expRes.globalInfo.lumi
            #self.pprint ( "adding a signal for %s (lumi %s)" % \
            #              ( expRes.id(), lumi ) )
            for i,dataset in enumerate(expRes.datasets):
                dt = dataset.dataInfo.dataType
                dsname = dataset.dataInfo.dataId
                if dt == "upperLimit":
                    for tpred in tpreds:
                        if tpred.dataId() == None:
                            expRes.datasets[i] = self.addSignalForULMap ( dataset, tpred, lumi )
                    ## expRes.datasets[i] = self.fixUpperLimit ( dataset )
                elif dt == "efficiencyMap":
                    for tpred in tpreds:
                        if dsname == tpred.dataId():
                            expRes.datasets[i] = self.addSignalForEfficiencyMap ( dataset, tpred, lumi )
                else:
                    print ( "[expResModifier] dataset type %s unknown" % dt )
            ret.append ( expRes )
        self.log ( "done adding signals" )
        return ret

    def fakeBackgrounds ( self, listOfExpRes ):
        """ thats the method that samples the backgrounds """
        ret = []
        self.log ( "now fake backgrounds" )
        for expRes in listOfExpRes:
            for i,dataset in enumerate(expRes.datasets):
                dt = dataset.dataInfo.dataType
                if dt == "upperLimit":
                    expRes.datasets[i] = self.bgUpperLimit ( dataset )
                elif dt == "efficiencyMap":
                    expRes.datasets[i] = self.sampleEfficiencyMap ( dataset )
                else:
                    print ( "[expResModifier] dataset type %s unknown" % dt )
            ret.append ( expRes )
        self.log ( "done faking the backgrounds" )
        return ret

def check ( picklefile ):
    """ check the picklefile """
    print ( "now checking the modified database" )
    db = Database ( picklefile )
    listOfExpRes = db.getExpResults()
    for er in listOfExpRes:
        datasets = er.datasets
        for ds in datasets:
            txnl = ds.txnameList
            for txn in txnl:
                x = txn.txnameData.dataType
    print ( "were good", db.databaseVersion )


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
                        description='experimental results modifier. used to take out potential signals from the database by setting all observations to values sampled from the background expectations' )
    argparser.add_argument ( '-d', '--database',
            help='database to use [../../smodels-database]',
            type=str, default="../../smodels-database" )
    argparser.add_argument ( '-o', '--outfile',
            help='file to write out database pickle [""]',
            type=str, default="" )
    argparser.add_argument ( '-s', '--suffix',
            help='suffix for database version ["fake1"]',
            type=str, default="fake1" )
    argparser.add_argument ( '-P', '--pmodel',
            help='supply filename of a pmodel, in which case create a signal-infused database [""]',
            type=str, default="" )
    argparser.add_argument ( '-v', '--verbose',
            help='print results to stdout', action='store_true' )
    argparser.add_argument ( '-i', '--interact',
            help='interactive mode', action='store_true' )
    argparser.add_argument ( '-c', '--check',
            help='check the pickle file <outfile>', action='store_true' )
    args = argparser.parse_args()
    from smodels.experiment.databaseObj import Database
    db = Database ( args.database )
    modifier = ExpResModifier()
    er = modifier.modifyDatabase ( db, args.outfile, args.suffix, args.pmodel )

    if args.check:
        check ( args.outfile )

    if args.interact:
        modifier.interact ( er )
