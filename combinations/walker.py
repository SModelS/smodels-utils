#!/usr/bin/env python3

""" a first start at the random walk idea """

import random, copy, pickle, sys, os, time, math, socket
if sys.version_info[0]==2:
    import commands as subprocess # python2.7
else:
    import subprocess
import numpy, colorama
try:
    import smodels
except:
    import setPath
sys.path.insert(0,"/scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/combinations/")
from smodels.tools.runtime import nCPUs
from smodels.tools.physicsUnits import GeV
from hiscore import Hiscore
from protomodel import ProtoModel, rthresholds
from manipulator import Manipulator
from history import History
import helpers
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
                   dbpath = "../../smodels-database/", expected = False,
                   select = "all", catch_exceptions = True,
                   rundir = None ):
        """ initialise the walker
        :param nsteps: maximum number of steps to perform, negative is infinity
        :param cheatcode: cheat mode. 0 is no cheating, 1 is with ranges, 2
                      is the Z323 model.
        :param expected: remove possible signals from database
        :param select: select only subset of results
        :param catch_exceptions: should we catch exceptions
        """
        if type(walkerid) != int or type(nsteps) != int or type(strategy)!= str:
            self.pprint ( "Wrong call of constructor: %s, %s, %s" % ( walkerid, nsteps, strategy ) )
            sys.exit(-2)
        self.walkerid = walkerid ## walker id, for parallel runs
        self.rundir = rundir
        self.hiscoreList = Hiscore ( walkerid, True, "%s/H%d.pcl" % ( rundir, walkerid ),
                                     backup=False )
        self.hiscoreList.nkeep = 1
        protomodel = ProtoModel( self.walkerid, dbpath = dbpath, 
                            expected = expected, select = select,
                            keep_meta = True )
        self.manipulator = Manipulator ( protomodel, strategy )
        if cheatcode > 0:
            self.manipulator.cheat ( cheatcode )
            self.manipulator.predict()
            self.pprint ( "Cheat model gets Z=%.2f, K=%.2f" % \
                          ( self.manipulator.M.Z, self.manipulator.M.K ) )
        self.catch_exceptions = catch_exceptions
        self.history = History ( walkerid )
        self.doBayesian = True ## bayesian or frequentist?
        self.record_history = False
        self.maxsteps = nsteps
        self.accelerator = None
        if dump_training:
            from accelerator import Accelerator
            ## we use the accelerator only to dump the training data
            self.accelerator = Accelerator ( walkerid= walkerid, 
                                dump_training= True,
                                is_trained = False  )
        self.takeStep() ## the first step should be considered as "taken"

    def hostname ( self ):
        return socket.gethostname()

    def setWalkerId ( self, Id ):
        self.walkerid = Id
        self.manipulator.setWalkerId ( Id )
        self.history.walkerid = Id
        if self.accelerator != None:
            self.accelerator.walkerid = Id


    #def turnOnRegress ( self, accelerator=None ):
    #    self.accelerator = accelerator

    @classmethod
    def fromProtoModel( cls, protomodel, nsteps=10000, strategy="aggressive", 
                   walkerid=0, dump_training = False, 
                   dbpath="../../smodels-database/", expected = False, 
                   select = "all", catch_exceptions = True, keep_meta = True,
                   rundir = None ):
        ret = cls( walkerid, nsteps=nsteps, dbpath = dbpath, 
                   catch_exceptions = catch_exceptions, rundir = rundir )
        ret.manipulator.M = protomodel
        ret.manipulator.setWalkerId ( walkerid )
        ret.protomodel.expected = expected
        ret.protomodel.step = protomodel.step
        ret.protomodel.select = select
        ret.protomodel.dbpath = dbpath
        ret.protomodel.createNewSLHAFileName()
        ret.protomodel.initializeSSMs ( overwrite = False )
        ret.protomodel.initializePredictor()
        ret.protomodel.backup()
        if dump_training:
            ## we use the accelerator only to dump the training data
            from accelerator import Accelerator
            ret.accelerator = Accelerator ( walkerid= walkerid, dump_training=True,
                                        is_trained = False )
        return ret

    @classmethod
    def fromDictionary( cls, dictionary, nsteps=10000, strategy="aggressive", 
                   walkerid=0, dump_training = False, 
                   dbpath="../../smodels-database/", expected = False, 
                   select = "all", catch_exceptions = True, keep_meta = True, 
                   rundir = None ):
        ret = cls( walkerid, nsteps=nsteps, dbpath = dbpath, 
                   catch_exceptions = catch_exceptions, rundir = rundir )
        ret.manipulator.M = ProtoModel( walkerid, dbpath, expected, select, keep_meta )
        ret.manipulator.initFromDict ( dictionary )
        ret.manipulator.setWalkerId ( walkerid )
        ret.protomodel = ret.manipulator.M
        ret.protomodel.nevents = 100000
        ret.protomodel.expected = expected
        ret.protomodel.select = select
        ret.protomodel.dbpath = dbpath
        ret.protomodel.createNewSLHAFileName()
        ret.protomodel.initializeSSMs ( overwrite = False )
        ret.protomodel.initializePredictor()
        ret.protomodel.backup()
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

    # lets start doing everything via the manipulator,
    # not talking to the protomodel directly.
    @property
    def protomodel(self):
        return self.manipulator.M

    @protomodel.setter
    def protomodel(self, protomodel):
        self.manipulator.M = protomodel

    def checkIfToTeleport ( self ):
        """ check if we should teleport. If we should then also
            perform the teleportation. """
        bestK = self.hiscoreList.globalMaxK()
        if bestK < 1.:
            self.log ( "K is smaller than one. no teleporting." )
        ourK = -2.
        if hasattr ( self.manipulator.M, "K" ) and self.manipulator.M.K > -2:
            ourK = self.manipulator.M.K
        dK = ( bestK - ourK ) / 10.
        prob = min ( 1., 1. - math.exp ( -dK )  )
        prob = max ( 0., .1 * prob )
        a = random.uniform ( 0., 1. )
        doTP = ( a < prob )
        self.log ( "check if to teleport, Kmax=%.2f, ours is=%.2f, p=%.2f, a=%.2f: %s" % \
                   ( bestK, ourK, prob, a, str(doTP) ) )
        if doTP:
            self.manipulator.teleportToHiscore()

    def onestep ( self ):
        self.protomodel.clean()
        self.protomodel.step+=1
        nUnfrozen = len ( self.protomodel.unFrozenParticles() )
        nTotal = len ( self.protomodel.masses.keys() )
        self.pprint ( "Step %d has %d/%d unfrozen particles: %s" % ( self.protomodel.step, nUnfrozen, nTotal, ", ".join ( map ( helpers.getParticleName, self.protomodel.unFrozenParticles() ) ) ) )
        if False:
            self.pprint ( "memory footprint (kb): walker %d, model %d, accelerator %d, history %d" %\
                    ( asizeof(self)/1024,asizeof(self.protomodel)/1024,asizeof(self.accelerator)/1024, asizeof(self.history)/1024 ) )
        nChanges = 0
        denom = self.protomodel.Z+1.
        if denom < 1.:
            denom = 1.
        mu = 1. - .7 / denom ## make it more unlikely when Z is high
        uUnfreeze = random.gauss( mu ,.5)
        if uUnfreeze > nUnfrozen/float(nTotal):
            # in every nth step unfreeze random particle
            self.log ( "unfreeze random particle" )
            nChanges += self.manipulator.randomlyUnfreezeParticle()
        uBranch = random.uniform(0,1)
        if uBranch > .8: # do this about every third time
            self.log ( "randomly change branchings" )
            nChanges += self.manipulator.randomlyChangeBranchings()
        uSSM = random.uniform(0,1)
        if uSSM > .75: # do this everytime else
            self.log ( "randomly change signal strengths" )
            nChanges += self.manipulator.randomlyChangeSignalStrengths()

        ## randomly try a merger
        uM = random.uniform(0,1)
        if uM < .05:
            self.log ( "randomly try merger" )
            nChanges += self.manipulator.randomlyAttemptAMerger()

        mu = .4 / denom ## make it more unlikely when Z is high
        uFreeze = random.gauss(mu,.5)
        if uFreeze < nUnfrozen/float(nTotal):
            # in every nth step freeze random particle
            if random.uniform(0,1)<.3:
                self.log ( "freeze most massive particle" )
                nChanges+=self.manipulator.freezeMostMassiveParticle()
            else:
                self.log ( "freeze random particle" )
                nChanges+=self.manipulator.randomlyFreezeParticle()
        uMass = random.uniform ( 0., 1. )
        if nChanges == 0 or uMass > .95:
            self.log ( "take random mass step" )
            nChanges+=self.manipulator.randomlyChangeMasses()
        if self.catch_exceptions: 
            try:
                self.manipulator.predict()
            except Exception as e:
                self.pprint ( "error ``%s'' (%s) encountered when trying to predict. lets revert" % (str(e),type(e) ) )
                self.protomodel.restore()
                return
        else:
            self.manipulator.predict ()

        self.log ( "found highest Z: %.2f" % self.protomodel.Z )
        
        if self.hiscoreList != None:
            self.log ( "check if result goes into hiscore list" )
            self.hiscoreList.newResult ( self.protomodel ) ## add to high score list
            self.log ( "done check for result to go into hiscore list" )
        # self.hiqueue.put( [ hiscoreList ] )
        self.train ()
        nUnfrozen = len ( self.protomodel.unFrozenParticles() )
        self.pprint ( "best combo for strategy ``%s'' is %s: %s: [K=%.2f, Z=%.2f, %d unfrozen]" % \
            ( self.manipulator.strategy, self.protomodel.letters, self.protomodel.description, self.protomodel.K, self.protomodel.Z, nUnfrozen ) )
        smaxstp = "%s" % self.maxsteps
        if self.maxsteps < 0:
            smaxstp = "inf"
        self.checkIfToTeleport()
        self.log ( "now check for swaps" )
        self.manipulator.checkSwaps()
        self.log ( "step %d/%s finished." % ( self.protomodel.step, smaxstp ) )

    def train ( self ):
        """ train the accelerator """
        ## currently we dont train, we just dump the data
        if self.accelerator != None:
            self.accelerator.dumpTrainingData ( self.protomodel )
        return # we dont train for now

    def predict ( self ):
        """ call predict with good # events """

    def gradientAscent ( self ):
        """ Z is big enough, the loss is small enough. use the gradient. """
        if self.accelerator.torchmodel == None or self.accelerator.is_trained == False:
            ## we dont have a (trained) model, we dont ascend
            self.pprint ( "gradient ascent? no!" )
            return
        self.pprint ( "gradient ascent? yes!" )
        predictedZ = float ( self.accelerator.predict ( self.protomodel ) )
        self.pprint ( "Gradient ascent predicted vs computed Z: %.5f <-> %.5f" % ( predictedZ, self.protomodel.Z ) )
        self.accelerator.train ( self.protomodel, self.protomodel.Z ) # only done to get gradient
        if not hasattr ( self.accelerator, "grad" ) or type(self.accelerator.grad) == type(None):
            self.pprint ( "accelerator has no grad %d" % hasattr ( self.accelerator, "grad" ) )
            sys.exit()
            return
        # self.log ( "shall we perform gradient ascent?" )
        # self.log ( "attrs %s %s" % ( self.accelerator.loss, self.accelerator.torchmodel.last_ypred ) )
        #if self.accelerator.loss > 1. or ( hasattr ( self.accelerator.torchmodel, "last_ypred" ) and self.accelerator.torchmodel.last_ypred in [ float("nan"), None ] ):
        #    return ## dont make gradient ascent when accelerator loss is too high
        self.pprint ( "performing a gradient ascent. Z before %.2f" % self.protomodel.Z )
        oldZ = self.protomodel.Z
        self.protomodel.backup()
        self.accelerator.plusDeltaM ( self.protomodel, rate=.1 ) ## move!!
        try:
            self.manipulator.predict ()
        except Exception as e:
            self.pprint ( "could not get prediction for gradient ascended model. revert" )
            self.protomodel.restore()
            return
        self.pprint ( "Z after gradient ascent %.2f, before was %.2f" % ( self.protomodel.Z, oldZ ) )
        if oldZ > self.protomodel.Z:
            self.pprint ( "old value was better. revert" )
            self.protomodel.restore()
        else:
            self.pprint ( "keep gradient ascended model" )

    def takeStep ( self ):
        """ take the step, save it as last step """
        if self.accelerator != None and hasattr ( self.accelerator, "grad" ):
            self.oldgrad = self.accelerator.grad
        ## the muhat multiplier gets multiplied into the signal strengths
        self.manipulator.resolveMuhat()
        ## and backup!
        self.protomodel.backup()

    def saveState ( self ):
        """ write out current state, for later retrieval """
        with open("state.pcl","wb") as f:
            pickle.dump ( self, f )

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[walk:%d] %s%s" % ( col, self.walkerid, " ".join(map(str,args)), colorama.Fore.RESET ) )

    def decideOnTakingStep ( self, ratio ):
        """ depending on the ratio, decide on whether to take the step or not.
            If ratio > 1., take the step, if < 1, let chance decide. """
        if ratio >= 1.:
            if self.doBayesian:
                self.highlight ( "info", "K: %.3f -> %.3f: r=%.4f, take the step" % ( self.protomodel.oldK(), self.protomodel.K, ratio ) )
                if self.protomodel.K > 0. and self.protomodel.K < 0.7 * self.protomodel.oldK():
                    self.pprint ( " `- weird, though, K decreases. Please check." )
                    sys.exit(-2)
            else:
                self.highlight ( "info", "Z: %.3f -> %.3f: take the step" % ( self.protomodel.oldZ(), self.protomodel.Z ) )
                if self.protomodel.Z < 0.7 * self.protomodel.oldZ():
                    self.pprint ( " `- weird, though, Z decreases. Please check." )
                    sys.exit(-2)
            self.takeStep()
        else:
            u=random.uniform(0.,1.)
            if u > ratio:
                if self.doBayesian:
                    self.pprint ( "u=%.2f > %.2f; K: %.2f -> %.2f: revert." % (u,ratio,self.protomodel.oldK(), self.protomodel.K) )
                else:
                    self.pprint ( "u=%.2f > %.2f; Z: %.2f -> %.2f: revert." % (u,ratio,self.protomodel.oldZ(), self.protomodel.Z) )
                self.protomodel.restore()
                if hasattr ( self, "oldgrad" ) and self.accelerator != None:
                    self.accelerator.grad = self.oldgrad
            else:
                self.pprint ( "u=%.2f <= %.2f ; %.2f -> %.2f: take the step, even though old is better." % (u, ratio,self.protomodel.oldZ(),self.protomodel.Z) )
                self.takeStep()

    def computeRatio ( self ):
        """ get the ratio of posteriors/likelihoods """
        ratio = 1.
        if self.doBayesian:
            oldK = self.protomodel.oldK()
            K = self.protomodel.K
            if oldK > -20. and K < oldK:
                ratio = numpy.exp(.5*( K - oldK ) )
            return ratio

        oldZ = self.protomodel.oldZ()
        Z = self.protomodel.Z
        if oldZ > 0. and Z < oldZ:
            ratio = numpy.exp(.5*( (Z**2) - (oldZ**2) ) )
        return ratio

    def log ( self, *args ):
        """ logging to file """
        with open( "%s/walker%d.log" % ( self.rundir, self.walkerid ), "a" ) as f:
            f.write ( "[walk:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def walk ( self ):
        """ Now perform the random walk """
        self.manipulator.randomlyUnfreezeParticle() ## start with unfreezing a random particle
        while self.maxsteps < 0 or self.protomodel.step<self.maxsteps:
            # self.gradientAscent() # perform at begining
            ## only the first walker records history
            if self.record_history:
                self.history.add ( self.protomodel )
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
            if self.protomodel.rmax > rthresholds[0]:
                tp = self.protomodel.rvalues[0][2]
                masses = []
                try:
                    masses = [ int(y.asNumber(GeV)) for y in tp.mass[0] ]
                except:
                    pass
                ana="%s(%s,%s,m=%s)" % \
                     ( tp.analysisId(), ",".join( map ( str, tp.txnames ) ), tp.dataType(True), masses )
                self.highlight ( "info", "rmax[%s]=%.2f > %.1f (r2=%.2f): revert." % \
                        ( ana, self.protomodel.rmax, rthresholds[0], self.protomodel.r2 ) )
                self.protomodel.restore()
                if hasattr ( self, "oldgrad" ) and self.accelerator != None:
                    self.accelerator.grad = self.oldgrad
                continue

            # obtain the ratio of posteriors
            ratio = self.computeRatio()
            self.decideOnTakingStep ( ratio )
            # self.gradientAscent()
        self.saveState()
        self.pprint ( "Was asked to stop after %d steps" % self.maxsteps )

def _run ( walker, catchem ):
    if not catchem:
        walker.walk()
        return
    try:
        walker.walk()
    except Exception as e:
        import time
        with open("exceptions.log","a") as f:
            f.write ( "time %s\n" % time.asctime() )
            f.write ( "walker %d threw: %s\n" % ( walker.walkerid, e ) )
            if hasattr ( walker.model, "currentSLHA" ):
                f.write ("slha file was %s\n" % walker.model.currentSLHA )
        import colorama
        print ( "%swalker %d threw: %s%s\n" % ( colorama.Fore.RED, walker.walkerid, e, colorama.Fore.RESET ) )

def startWalkers ( walkers ):
    catchem=False
    processes=[]
    for walker in walkers:
        p = multiprocessing.Process ( target=_run, args=( walker, catchem ) )
        p.start()
        processes.append(p)
    for p in processes:
        p.join()

if __name__ == "__main__":
    print ( "[walk] ramping up" )
    import argparse
    argparser = argparse.ArgumentParser(
            description='model walker. builds BSM models of interest')
    argparser.add_argument ( '-s', '--strategy',
            help='combination strategy [aggressive]',
            type=str, default="aggressive" )
    argparser.add_argument ( '-S', '--select',
            help='select only a subset of results (all,ul,em) [all]',
            type=str, default="all" )
    argparser.add_argument ( '-d', '--database',
            help='path to database [../../smodels-database]',
            type=str, default="../../smodels-database" )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug,info,warn,error [info]',
            type=str, default="info" )
    argparser.add_argument ( '-r', '--accelerator',
            help='use accelerator to perform gradient ascent, supply pickle file name [None]',
            type=str, default="" )
    argparser.add_argument ( '-n', '--nsteps',
            help='number of steps, negative means infinity [-1]',
            type=int, default=-1 )
    argparser.add_argument ( '-p', '--ncpus',
            help='number of CPUs. -1 means all. [1]',
            type=int, default=1 )
    argparser.add_argument ( '-E', '--no_catch',
            help='do not catch exceptions', action='store_true' )
    argparser.add_argument ( '-D', '--no_dump_training',
            help='do not dump data for training', action='store_true' )
    argparser.add_argument ( '-e', '--expected',
            help='run only with expected values', action='store_true' )
    argparser.add_argument ( '-C', '--cheat',
            help='cheat mode, 0 means, dont cheat. Disregarded, if --cont. [0]', 
            type=int, default=0 )
    argparser.add_argument ( '-f', '-c', '--cont',
            help='continue with saved states [""]',
            type=str, default="" )
    argparser.add_argument ( '-H', '--history', help='record history',
                             action="store_true" )
    args = argparser.parse_args()
    cleanDirectory()
    select = args.select.lower()
    catchem = not args.no_catch ## catch exceptions?
    if "efficien" in select:
        select = "em"
    if "upper" in select:
        select = "ul"
    if "none" in select:
        select = "all"
    if select == "":
        select = "all"
    dump_training = not args.no_dump_training
    ncpus = args.ncpus
    if ncpus < 0:
        ncpus = nCPUs() + ncpus + 1
    walkers = []

    contfile = args.cont
    if contfile == "default":
        # contfile = "./states.pcl"
        contfile = "./states.dict"
    if contfile!="" and not(os.path.exists ( contfile )):
        print ( "[walker] ERROR contfile %s supplied but does not exist" % contfile )
        sys.exit()
    if contfile!="" and os.stat( contfile ).st_size <= 100:
        print ( "[walker] ERROR contfile %s supplied but seems empty" % contfile )
        sys.exit()
    if contfile!="" and os.path.exists ( contfile ) and \
                   os.stat( contfile ).st_size > 100:
        states = []
        if contfile.endswith ( ".pcl" ):
            with open( contfile, "rb" ) as f:
                states = pickle.load ( f )
        if contfile.endswith ( ".dict" ):
            with open( contfile, "rt" ) as f:
                states = eval ( f.read() )
        ctr=0
        while len(walkers)<ncpus:
            for v in states: # .items()):
                if ctr >= ncpus:
                    break
                if v == None:
                    # no state? start from scratch!
                    walker = RandomWalker( ctr+1, args.nsteps, args.strategy, 
                                           dump_training = dump_training, 
                                           cheatcode = args.cheat, 
                                           dbpath = args.database, 
                                           expected = args.expected,
                                           select = select, 
                                           catch_exceptions = catchem )
                    walker.takeStep()
                    walkers.append ( walker )
                    continue
                if type(v) == dict:
                    walkers.append ( RandomWalker.fromDictionary ( v, walkerid = ctr+1, 
                                dump_training = dump_training, dbpath = args.database,
                                expected = args.expected, select = select,
                                catch_exceptions = catchem,
                                keep_meta = True ) )
                else:
                    v2 = copy.deepcopy ( v )
                    v2.createNewSLHAFileName()
                    v2.walkerid = ctr+1
                    walkers.append ( RandomWalker.fromProtoModel ( v2, walkerid = ctr+1, 
                                dump_training = dump_training, dbpath = args.database,
                                expected = args.expected, select = select,
                                catch_exceptions = catchem,
                                keep_meta = True ) )
                walkers[-1].setWalkerId ( ctr+1 )
                walkers[-1].takeStep() # make last step a taken one
                ctr+=1
    else:
        for ctr in range(ncpus):
            walkers.append ( RandomWalker( ctr+1, args.nsteps, 
                                    strategy = args.strategy, 
                                    dump_training = dump_training, 
                                    cheatcode = args.cheat, 
                                    dbpath = args.database, 
                                    expected = args.expected, 
                                    select = select,
                                    catch_exceptions = catchem ) )

    if args.accelerator not in [ "", "none", "None" ]:
        from accelerator import Accelerator
        for walker in walkers:
            walker.accelerator = Accelerator ( walkerid = walker.walkerid, 
                                           torchmodel = args.accelerator,
                                           dump_training = dump_training,
                                           is_trained = True )
    #print ( "[walk] loading hiscores" )
    onoff="off"
    if args.history:
        onoff="on"
        walkers[0].record_history = True
    print ( "[walk] history recording is %s" % onoff )

    print ( "[walk] starting %d walkers" % len(walkers) )
    startWalkers ( walkers )
