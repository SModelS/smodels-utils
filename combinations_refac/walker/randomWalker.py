#!/usr/bin/env python3

""" a first start at the random walk idea """

import random, pickle, sys, time, math, socket
if sys.version_info[0]==2:
    import commands as subprocess # python2.7
else:
    import subprocess
import numpy, colorama
try:
    import smodels
except:
    from tools import setPath
sys.path.insert(0,"/scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/combinations/")
from walker.hiscore import Hiscore
from builder.protomodel import ProtoModel
from builder.manipulator import Manipulator
from tester.predictor import Predictor
from tools import helpers
from pympler.asizeof import asizeof
try:
    from torch import multiprocessing
except:
    import multiprocessing

def cleanDirectory ():
    subprocess.getoutput ( "mkdir -p tmp" )
    subprocess.getoutput ( "mv .cur*slha tmp/" )
    subprocess.getoutput ( "mv walker*.log tmp/" )
    subprocess.getoutput ( "mv exceptions.log tmp/" )

class RandomWalker:
    def __init__ ( self, walkerid=0, nsteps=10000, strategy="aggressive",
                   dump_training = False, cheatcode = 0,
                   dbpath = "<rundir>/database.pcl", expected = False,
                   select = "all", catch_exceptions = True,
                   rundir = None, nevents = 100000 ):
        """ initialise the walker
        :param nsteps: maximum number of steps to perform, negative is infinity
        :param cheatcode: cheat mode. 0 is no cheating, 1 is with ranges, 2
                      is the Z323 model.
        :param expected: remove possible signals from database
        :param select: select only subset of results
        :param catch_exceptions: should we catch exceptions
        :param nevents: number of MC events when computing cross-sections
        """
        if type(walkerid) != int or type(nsteps) != int or type(strategy)!= str:
            self.pprint ( "Wrong call of constructor: %s, %s, %s" % ( walkerid, nsteps, strategy ) )
            sys.exit(-2)
        self.walkerid = walkerid ## walker id, for parallel runs
        self.rundir = rundir
        if rundir == None:
            self.rundir = "./"

        #Initialize Predictor
        self.predictor =  Predictor( self.walkerid, dbpath=dbpath,
                              expected=expected, select=select )

        #Initialize Hiscore (with access to the predictor)
        self.hiscoreList = Hiscore ( walkerid, True, "%s/H%d.pcl" % ( rundir, walkerid ),
                                     backup=False, predictor=self.predictor )
        self.hiscoreList.nkeep = 1

        #Initialize ProtoModel and Manipulator:
        protomodel = ProtoModel( self.walkerid,
                            keep_meta = True, nevents = nevents)

        self.manipulator = Manipulator ( protomodel, strategy )
        self.catch_exceptions = catch_exceptions
        self.maxsteps = nsteps
        self.accelerator = None

        if cheatcode <= 0:
            self.takeStep() # the first step should be considered as "taken"
            #Set current Z and K values to threshold values
            self.currentZ = -0.1
            self.currentK = -20.0
        else:
            self.manipulator.cheat ( cheatcode )
            self.predictor.predict(self.protomodel)
            self.pprint ( "Cheat model gets Z=%.2f, K=%.2f" % \
                          ( self.manipulator.M.Z, self.manipulator.M.K ) )
            self.manipulator.backupModel()
            self.hiscoreList.newResult ( self.manipulator.M )
            self.currentK = self.manipulator.M.K
            self.currentZ = self.manipulator.M.Z
        if dump_training:
            from accelerator import Accelerator
            ## we use the accelerator only to dump the training data
            self.accelerator = Accelerator ( walkerid= walkerid,
                                dump_training= True,
                                is_trained = False  )

    def hostname ( self ):
        return socket.gethostname()

    def setWalkerId ( self, Id ):
        self.walkerid = Id
        self.manipulator.setWalkerId ( Id )
        if self.accelerator != None:
            self.accelerator.walkerid = Id

    #def turnOnRegress ( self, accelerator=None ):
    #    self.accelerator = accelerator

    @classmethod
    def fromProtoModel( cls, protomodel, nsteps=10000, strategy="aggressive",
                   walkerid=0, dump_training = False,
                   dbpath="<rundir>/database.pcl", expected = False,
                   select = "all", catch_exceptions = True, keep_meta = True,
                   rundir = None):
        ret = cls( walkerid, nsteps=nsteps, dbpath = dbpath, expected=expected, select=select,
                   catch_exceptions = catch_exceptions, rundir = rundir )
        ret.manipulator.M = protomodel
        ret.manipulator.setWalkerId ( walkerid )
        ret.manipulator.M.createNewSLHAFileName()
        ret.manipulator.M.initializeSSMs ( overwrite = False )
        ret.manipulator.backupModel()
        if dump_training:
            ## we use the accelerator only to dump the training data
            from accelerator import Accelerator
            ret.accelerator = Accelerator ( walkerid= walkerid, dump_training=True,
                                        is_trained = False )
        return ret

    @classmethod
    def fromDictionary( cls, dictionary, nsteps=10000, strategy="aggressive",
                   walkerid=0, dump_training = False,
                   dbpath="<rundir>/database.pcl", expected = False,
                   select = "all", catch_exceptions = True, keep_meta = True,
                   rundir = None, nevents = 100000):
        ret = cls( walkerid, nsteps=nsteps, dbpath = dbpath, expected=expected, select=select,
                   catch_exceptions = catch_exceptions, rundir = rundir, nevents = nevents )
        ret.manipulator.M = ProtoModel( walkerid, keep_meta )
        ret.manipulator.initFromDict ( dictionary )
        ret.manipulator.setWalkerId ( walkerid )
        ret.manipulator.M.createNewSLHAFileName()
        ret.manipulator.M.initializeSSMs ( overwrite = False )
        ret.manipulator.backupModel()
        if dump_training:
            ## we use the accelerator only to dump the training data
            from accelerator import Accelerator
            ret.accelerator = Accelerator ( walkerid= walkerid, dump_training=True,
                                        is_trained = False )
        return ret

    def pprint ( self, *args ):
        """ logging """
        if not hasattr ( self, "walkerid" ):
            self.walkerid=-1
        print ( "[walk:%d:%s-%s] %s" % ( self.walkerid, self.hostname(), time.strftime("%H:%M:%S"), " ".join(map(str,args))) )
        self.log ( *args )

    @property
    def protomodel(self):
        return self.manipulator.M

    @protomodel.setter
    def protomodel(self, protomodel):
        self.manipulator.M = protomodel

    def onestep ( self ):
        #Remove data about best combo
        self.protomodel.cleanBestCombo()
        #Add one step
        self.protomodel.step+=1
        printMemUsage = False
        if printMemUsage:
            self.pprint ( "memory footprint (kb): walker %d, model %d, accelerator %d" %\
                    ( asizeof(self)/1024,asizeof(self.protomodel)/1024,asizeof(self.accelerator)/1024 ))

        #Take a step in the model space:
        self.manipulator.randomlyChangeModel()

        nUnfrozen = len( self.protomodel.unFrozenParticles() )
        nTotal = len ( self.protomodel.particles )
        self.pprint ( "Step %d has %d/%d unfrozen particles: %s" % ( self.protomodel.step, nUnfrozen, nTotal, ", ".join ( map ( helpers.getParticleName, self.protomodel.unFrozenParticles() ) ) ) )

        #Try to create a simpler model
        #(merge pre-defined particles of their mass difference is below dm)
        protomodelSimp = self.manipulator.simplifyModel(dm=200.0)

        self.predictor.predict(self.manipulator.M)
        if self.catch_exceptions:
            try:
                self.predictor.predict(self.manipulator.M)
                if protomodelSimp:
                    self.predictor.predict(protomodelSimp)
            except Exception as e:
                self.pprint ( "error ``%s'' (%s) encountered when trying to predict. lets revert" % (str(e),type(e) ) )
                self.manipulator.restoreModel()
                return
        else:
            self.predictor.predict(self.manipulator.M)
            if protomodelSimp:
                self.predictor.predict(protomodelSimp)

        #Now keep the model with highest score:
        if protomodelSimp:
            if self.manipulator.M.Z is None or (protomodelSimp.Z is not None
                        and (protomodelSimp.Z > self.manipulator.M.Z)):
                self.manipulator.M = protomodelSimp

        #If no combination could be found, return
        if self.manipulator.M.Z is None:
            return

        #the muhat multiplier gets multiplied into the signal strengths
        self.manipulator.rescaleByMuHat()

        #Sanity check (the model should never be excluded after rescaling):
        self.protomodel.excluded = self.protomodel.rmax > self.predictor.rthreshold
        if self.protomodel.excluded:
            self.highlight ( "info", "rmax=%.2f, excluded = %s (r2=%.2f): should never happen." % \
                ( self.protomodel.rmax, self.protomodel.excluded, self.protomodel.r2 ) )
            sys.exit(-2)

        self.log ( "found highest Z: %.2f" % self.protomodel.Z )

        # self.train ()
        nUnfrozen = len ( self.protomodel.unFrozenParticles() )
        self.pprint ( "best combo for strategy ``%s'' is %s: %s: [K=%.2f, Z=%.2f, %d unfrozen]" % \
            ( self.manipulator.strategy, self.protomodel.letters, self.protomodel.description, self.protomodel.K, self.protomodel.Z, nUnfrozen ) )
        smaxstp = "%s" % self.maxsteps
        if self.maxsteps < 0:
            smaxstp = "inf"

        #For low scoring models, teleport to a high score model:
        if self.checkIfToTeleport( pmax=0.5, norm = 10.0 ):
            # if we teleport the rest becomes irrelevant
            return

        self.log ( "freeze pids that arent in best combo, we dont need them" )
        self.manipulator.freezePidsNotInBestCombo()
        self.log ( "step %d/%s finished." % ( self.protomodel.step, smaxstp ) )

        self.log ( "check if result goes into hiscore list" )
        self.hiscoreList.newResult ( self.protomodel ) ## add to high score list
        self.log ( "done check for result to go into hiscore list" )

    def checkIfToTeleport ( self, pmax=0.1, norm = 10.0 ):
        """ check if we should teleport to a high score model. If we should then also
            perform the teleportation. The teleportation is done only if the model
            has a score smaller then the best score in hiscoreList.
            The teleportation probability is given by pmax*(1-exp^(K-bestK)/norm),
            so pmax is the maximum probability (when K -> -infinity).

        :param pmax: Maximum probability for teleportation.
        :param norm: Normalization for K distance.
        """
        bestK = self.hiscoreList.globalMaxK()
        if bestK < 1.:
            self.log ( "K is smaller than one. no teleporting." )
        ourK = -2.
        if hasattr ( self.manipulator.M, "K" ) and self.manipulator.M.K > -2:
            ourK = self.manipulator.M.K
        #The current model already is the best, do nothing.
        if ourK >= bestK:
            return False
        #Otherwise compute the teleportation probability:
        dK = ( ourK - bestK ) / norm
        prob = pmax*(1. - math.exp( dK ))
        a = random.uniform ( 0., 1. )
        doTP = ( a < prob ) ## do teleport, yes or no
        self.log ( "check if to teleport, Kmax=%.2f, ours is=%.2f, p=%.2f, a=%.2f: %s" % \
                   ( bestK, ourK, prob, a, str(doTP) ) )
        if doTP:
            self.manipulator.teleportToHiscore()
        return doTP

    def takeStep ( self ):
        """ take the step, save it as last step """
        if self.accelerator != None and hasattr ( self.accelerator, "grad" ):
            self.oldgrad = self.accelerator.grad
        ## Backup model
        self.manipulator.backupModel()
        # Update current K and Z values
        self.currentK = self.protomodel.K
        self.currentZ = self.protomodel.Z

    def saveState ( self ):
        """ write out current state, for later retrieval """
        with open("state.pcl","wb") as f:
            pickle.dump ( self, f )

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[walk:%d] %s%s" % ( col, self.walkerid, " ".join(map(str,args)), colorama.Fore.RESET ) )

    def decideOnTakingStep ( self ):
        """ depending on the ratio of K values, decide on whether to take the step or not.
            If ratio > 1., take the step, if < 1, let chance decide. """
        ratio = 1.
        K = self.currentK
        newK = self.protomodel.K
        if K > -20. and newK < K:
            ratio = numpy.exp(.5*( newK - K))

        if ratio >= 1.:
            self.highlight ( "info", "K: %.3f -> %.3f: r=%.4f, take the step" % ( self.currentK,
                        self.protomodel.K, ratio ) )
            if self.protomodel.K > 0. and self.protomodel.K < 0.7 * self.currentK:
                self.pprint ( " `- weird, though, K decreases. Please check." )
                sys.exit(-2)
            self.takeStep()
        else:
            u=random.uniform(0.,1.)
            if u > ratio:
                self.pprint ( "u=%.2f > %.2f; K: %.2f -> %.2f: revert." % (u,ratio,self.currentK,
                                self.protomodel.K) )
                self.manipulator.restoreModel()
                if hasattr ( self, "oldgrad" ) and self.accelerator != None:
                    self.accelerator.grad = self.oldgrad
            else:
                self.pprint ( "u=%.2f <= %.2f ; %.2f -> %.2f: take the step, even though old is better." % (u, ratio,self.currentK,self.protomodel.Z) )
                self.takeStep()

    def log ( self, *args ):
        """ logging to file """
        with open( "%s/walker%d.log" % ( self.rundir, self.walkerid ), "a" ) as f:
            f.write ( "[walk:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def walk ( self, catchem=False ):
        """ Now perform the random walk """

        self.manipulator.randomlyUnfreezeParticle(force = True) ## start with unfreezing a random particle
        self.manipulator.backupModel()
        while self.maxsteps < 0 or self.protomodel.step<self.maxsteps:

            if not catchem:
                self.onestep()
            else:
                try:
                    self.onestep()
                except Exception as e:
                    # https://bioinfoexpert.com/2016/01/18/tracing-exceptions-in-multiprocessing-in-python/
                    self.pprint ( "taking a step resulted in exception: %s, %s" % (type(e), e ) )
                    import traceback
                    traceback.print_stack( limit=None )
                    except_type, except_class, tb = sys.exc_info()
                    extracted = traceback.extract_tb(tb)
                    for point in extracted:
                        self.pprint ( "extracted: %s" % point )
                    with open("%s/exceptions.log" % self.rundir,"a") as f:
                        f.write ( "%s: taking a step resulted in exception: %s, %s\n" % (time.asctime(), type(e), e ) )
                        f.write ( "   `- exception occured in walker #%s\n" % self.protomodel.walkerid )
                    sys.exit(-1)

            #If no combination was found, go back
            if self.protomodel.K is None:
                self.manipulator.restoreModel()
                continue

            # obtain the ratio of posteriors
            self.decideOnTakingStep ()
            # self.gradientAscent()
        self.saveState()
        self.pprint ( "Was asked to stop after %d steps" % self.maxsteps )

def _run ( walker, catchem, seed=None ):

    #Set random seed
    if seed is not None:
        helpers.seedRandomNumbers(seed)
    if not catchem:
        walker.walk()
        return
    try:
        walker.walk(catchem)
    except Exception as e:
        import time
        with open("exceptions.log","a") as f:
            f.write ( "time %s\n" % time.asctime() )
            f.write ( "walker %d threw: %s\n" % ( walker.walkerid, e ) )
            if hasattr ( walker.model, "currentSLHA" ):
                f.write ("slha file was %s\n" % walker.model.currentSLHA )
        import colorama
        print ( "%swalker %d threw: %s%s\n" % ( colorama.Fore.RED, walker.walkerid, e, colorama.Fore.RESET ) )

def startWalkers ( walkers, seed=None,  catchem=False):

    processes=[]
    for walker in walkers:
        p = multiprocessing.Process ( target=_run, args=( walker, catchem, seed ) )
        p.start()
        processes.append(p)
    for p in processes:
        p.join()
