#!/usr/bin/env python3

""" a first start at the random walk idea """

import random, copy, pickle, sys, os, time, subprocess, math
import multiprocessing, numpy, colorama
from smodels.tools.runtime import nCPUs
from hiscore import Hiscore
from model import Model
from history import History
from regressor import Regressor
import helpers
from pympler.asizeof import asizeof

def cleanDirectory ():
    subprocess.getoutput ( "mkdir -p tmp" )
    subprocess.getoutput ( "mv .cur*slha tmp/" )
    subprocess.getoutput ( "mv walker*.log tmp/" )
    subprocess.getoutput ( "mv exceptions.log tmp/" )

class RandomWalker:
    def __init__ ( self, walkerid=0, nsteps=10000, strategy="aggressive",
                   use_regressor=False ):
        """ initialise the walker
        :param nsteps: maximum number of steps to perform
        """
        if type(walkerid) != int or type(nsteps) != int or type(strategy)!= str:
            self.pprint ( "Wrong call of constructor: %s, %s, %s" % ( walkerid, nsteps, strategy ) )
            sys.exit()
        self.walkerid = walkerid ## walker id, for parallel runs
        self.model = Model( self.walkerid )
        self.strategy = strategy
        self.hiscoreList = None
        self.history = History ( walkerid )
        self.record_history = False
        self.maxsteps = nsteps
        self.use_regressor = use_regressor
        self.regressor = None
        if use_regressor:
            self.turnOnRegress()
        self.takeStep() ## the first step should be considered as "taken"

    def turnOnRegress ( self ):
        self.use_regressor=True
        self.regressor = Regressor ( walkerid=self.walkerid )


    @classmethod
    def fromModel( cls, model, nsteps=10000, strategy="aggressive",
                        hiscore=False, walkerid=0, use_regressor=False ):
        ret = cls( walkerid, nsteps, strategy, use_regressor )
        ret.model = model
        if use_regressor:
            ret.regressor = Regressor ( walkerid=walkerid )
        return ret

    def pprint ( self, *args ):
        """ logging """
        print ( "[walk:%d-%s] %s" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args))) )
        self.log ( *args )

    def freezeRandomParticle ( self ):
        """ freezes a random unfrozen particle """
        unfrozen = self.model.unFrozenParticles( withLSP = False )
        if len(unfrozen)<2:
            return 0 ## freeze only if at least 3 unfrozen particles exist
        p = random.choice ( unfrozen )
        self.model.masses[p]=1e6
        self.model.normalizeAllBranchings() ## adjust everything
        self.pprint ( "Freezing %s (keep branchings)." % ( helpers.getParticleName(p) ) )
        return 1

    def freezeMostMassiveParticle ( self ):
        """ freezes the most massive unfrozen particle """
        unfrozen = self.model.unFrozenParticles( withLSP=False )
        if len(unfrozen)<2:
            return 0 ## freeze only if at least 3 unfrozen particles exist
        pid,minmass=0,0
        for i in unfrozen:
            if self.model.masses[i]>minmass:
                minmass = self.model.masses[i]
                pid = i
        # p = random.choice ( unfrozen )
        self.model.masses[pid]=1e6
        self.model.normalizeAllBranchings() ## adjust everything
        self.pprint ( "Freezing most massive %s (%.1f)" % ( helpers.getParticleName(pid), minmass ) )
        return 1

    def onestep ( self ):
        self.model.clean()
        self.model.step+=1
        nUnfrozen = len ( self.model.unFrozenParticles() )
        nTotal = len ( self.model.masses.keys() )
        self.pprint ( "Step %d has %d/%d unfrozen particles: %s" % ( self.model.step, nUnfrozen, nTotal, ", ".join ( map ( helpers.getParticleName, self.model.unFrozenParticles() ) ) ) )
        if False:
            self.pprint ( "memory footprint (kb): walker %d, model %d, hiscore %d, regressor %d, history %d, oldmodel %d" %\
                    ( asizeof(self)/1024,asizeof(self.model)/1024,asizeof(self.hiscoreList)/1024,asizeof(self.regressor)/1024, asizeof(self.history)/1024,asizeof(self.oldmodel)/1024 ) )
        nChanges = 0
        mu = 1. - .7 / (self.model.Z+1.) ## make it more unlikely when Z is high
        uUnfreeze = random.gauss( mu ,.5)
        if uUnfreeze > nUnfrozen/float(nTotal):
            # in every nth step unfreeze random particle
            self.log ( "unfreeze random particle" )
            nChanges += self.unfreezeRandomParticle()
        uBranch = random.uniform(0,1)
        if uBranch > .3: # do this about every third time
            self.log ( "randomly change branchings" )
            nChanges += self.randomlyChangeBranchings()
        uSSM = random.uniform(0,1)
        if uSSM > .75: # do this everytime else
            self.log ( "randomly change signal strengths" )
            nChanges += self.randomlyChangeSignalStrengths()

        mu = .4 / (self.model.Z+1.) ## make it more unlikely when Z is high
        uFreeze = random.gauss(mu,.5)
        if uFreeze < nUnfrozen/float(nTotal):
            # in every nth step freeze random particle
            if random.uniform(0,1)<.3:
                self.log ( "freeze most massive particle" )
                nChanges+=self.freezeMostMassiveParticle()
            else:
                self.log ( "freeze random particle" )
                nChanges+=self.freezeRandomParticle()
        if nChanges == 0:
            self.log ( "take random mass step" )
            self.takeRandomMassStep()
        self.log ( "now create slha file" )
        self.model.predict( self.strategy )
        self.log ( "found highest Z: %.2f" % self.model.Z )
        if self.hiscoreList != None:
            self.log ( "check if result goes into hiscore list" )
            self.hiscoreList.newResult ( self.model ) ## add to high score list
            self.log ( "done check for result to go into hiscore list" )
        self.train ()
        self.model.computePrior()
        self.pprint ( "best combo for strategy ``%s'' is %s: %s: [Z=%.2f]" % ( self.strategy, self.model.letters, self.model.description, self.model.Z ) )
        self.log ( "step %d finished." % self.model.step )

    def train ( self ):
        """ train the regressor """
        if self.regressor == None:
            return
        predictedZ = float ( self.regressor.predict ( self.model ) )
        self.pprint ( "Before training step, predicted vs computed Z: %.5f, %.5f" % ( predictedZ, self.model.Z ) )
        self.regressor.train ( self.model, self.model.Z )
        predictedZ = float ( self.regressor.predict ( self.model ) )
        self.pprint ( "After training step, predicted vs computed Z: %.5f, %.5f" % ( predictedZ, self.model.Z ) )
        if self.regressor.training % 100 == 0 or self.regressor.training == 3 or self.regressor.training == 20:
            self.regressor.save()

    def revert ( self ):
        """ revert the last step. go back. """
        if not hasattr ( self, "oldmodel" ):
            self.pprint ( "I have been asked to revert to old model, but i dont have one" )
        self.model = copy.deepcopy ( self.oldmodel )

    def supplyHiscoreList ( self, Hiscorelist ):
        """ supply hiscore list, to avoid loading n times. """
        self.hiscoreList = Hiscorelist
        self.hiscoreList.walkerid = self.walkerid

    def takeStep ( self ):
        """ take the step, save it as last step """
        self.oldmodel = copy.deepcopy ( self.model )
        self.oldmodel.clean()

    def saveState ( self ):
        """ write out current state, for later retrieval """
        with open("state.pcl","wb") as f:
            pickle.dump ( self, f )

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[walk:%d] %s%s" % ( col, self.walkerid, " ".join(map(str,args)), colorama.Fore.RESET ) )

    def log ( self, *args ):
        """ logging to file """
        with open( "walker%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[walk:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def randomlyChangeSignalStrengths ( self ):
        """ randomly change one of the signal strengths """
        unfrozenparticles = self.model.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.pprint ( "not enough unfrozen particles to change random signal strength" )
            return 0
        p = random.choice ( unfrozenparticles )
        if not p in self.model.ssmultipliers:
            self.model.ssmultipliers[p]=1.
        newSSM=self.model.ssmultipliers[p]*random.gauss(1.,.1)
        if newSSM == 0.:
            self.pprint ( "Huh? ssmultiplier is 0?? Change to 1." )
            newSSM = 1.
        self.model.ssmultipliers[p]=newSSM
        self.pprint ( "changed signal strength multiplier of %s: %.2f." % (helpers.getParticleName(p), newSSM ) )
        return 1

    def randomlyChangeBranchings ( self ):
        """ randomly change the branchings of a single particle """
        unfrozenparticles = self.model.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.pprint ( "not enough unfrozen particles to change random branching" )
            return 0
        p = random.choice ( unfrozenparticles )
        openChannels = []
        for dpid,br in self.model.decays[p].items():
            if dpid in self.model.unFrozenParticles():
                openChannels.append ( dpid )
        if len(openChannels) < 2:
            # not enough channels open to tamper with branchings!
            return 0
        dx =.1/numpy.sqrt(len(openChannels)) ## maximum change per channel
        S=0.
        for i in self.model.decays[p].keys(): ## openChannels[:-1]:
            oldbr = self.model.decays[p][i]
            Min,Max = max(0.,oldbr-dx), min(oldbr+dx,1.)
            br = random.uniform ( Min, Max )
            #br = oldbr+random.uniform(-dx,dx)
            #if br < 0.: br = 0.
            #if br > 1.: br = 1.
            self.model.decays[p][i]=br
            S+=br
        if True: # S > 1.: ## correct for too large sums
            for i,v in self.model.decays[p].items():
                self.model.decays[p][i] = v / S
            S = 1.
        control = sum ( [  x for x in self.model.decays[p].values() ] )
        if abs ( control - 1.0 ) > 1e-5:
            self.pprint ( "control %s" % control )
        #    sys.exit()
        brvec=[]
        for x in self.model.decays[p].values():
            if x<1e-5:
                brvec.append("")
            else:
                brvec.append("%.2f" % x )
        self.pprint ( "changed branchings of %s: %s: s=%.2f" % (helpers.getParticleName(p), ",".join( brvec  ), control ) )
        return 1

    def takeRandomMassStep ( self ):
        """ take a random step in mass space for all unfrozen particles """
        dx = 40. / numpy.sqrt ( len(self.model.unFrozenParticles() ) ) / ( self.model.Z + 1. )
        for i in self.model.unFrozenParticles():
            tmp = self.model.masses[i]+random.uniform(-dx,dx)
            if tmp > self.model.maxMass:
                tmp = self.model.maxMass
            if tmp < self.model.masses[self.model.LSP]: ## the LSP is the LSP.
                tmp = self.model.masses[self.model.LSP]
            self.model.masses[i]=tmp
        for squark in [ 1, 2, 3, 4, 5, 6 ]:
            sq1,sq2=1000000+squark,2000000+squark
            if not sq1 in self.model.masses or not sq2 in self.model.masses:
                continue
            msq1,msq2 = self.model.masses[sq1], self.model.masses[sq2]
            if msq2 < msq1:
            ### sq1 should always be lighter than sq2
             self.model.masses[sq2]=msq1
             self.model.masses[sq1]=msq2
        if 1000023 in self.model.masses and 1000025 in self.model.masses:
            mchi20 = self.model.masses[1000023]
            mchi30 = self.model.masses[1000025]
            if mchi20 > mchi30:
                self.model.masses[1000023] = mchi30
                self.model.masses[1000025] = mchi20

    def unfreezeRandomParticle ( self ):
        """ unfreezes a random frozen particle """
        frozen = self.model.frozenParticles()
        if len(frozen)==0:
            return 0
        p = random.choice ( frozen )
        self.model.masses[p]=random.uniform ( self.model.masses[Model.LSP], self.model.maxMass )
        self.model.normalizeAllBranchings() ## adjust everything
        self.pprint ( "Unfreezing %s: m=%f" % ( helpers.getParticleName(p), self.model.masses[p] ) )
        return 1


    def walk ( self ):
        """ Now perform the random walk """
        self.unfreezeRandomParticle() ## start with unfreezing a random particle
        while self.model.step<self.maxsteps:
            ## only the first walker records history
            if self.record_history:
                self.history.add ( self.model )
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
                with open("exceptions.log","a") as f:
                    f.write ( "taking a step resulted in exception: %s, %s\n" % (type(e), e ) )
                sys.exit(-1)
            self.model.computePrior()
            # self.pprint ( "prior times llhd, before versus after: %f -> %f" % ( self.oldmodel.priorTimesLlhd(), self.model.priorTimesLlhd() ) )
            #ratio = 1.
            #if self.oldmodel.Z > 0.:
            #    ratio = self.model.Z / self.oldmodel.Z
            ratio = 1.
            if self.oldmodel.priorTimesLlhd() > 0.:
                ratio = math.exp ( - self.oldmodel.priorTimesLlhd()) / math.exp ( - self.model.priorTimesLlhd() )
                # ratio = self.model.priorTimesLlhd() / self.oldmodel.priorTimesLlhd()
            if self.oldmodel.Z > 0. and self.model.Z < 0.7 * self.oldmodel.Z:
                ## no big steps taken here.
                self.highlight ( "info", "Z=%.2f -> 0. Revert." % self.oldmodel.Z )
                self.revert()
                continue

            if ratio >= 1.:
                self.highlight ( "info", "Z: %.3f -> %.3f: take the step" % ( self.oldmodel.Z, self.model.Z ) )
                if self.model.Z < 0.7 * self.oldmodel.Z:
                    self.pprint ( " `- weird, though, Z decreases. Please check." )
                    self.pprint ( "oldllhd %f" % self.oldmodel.llhd )
                    self.pprint ( "oldprior", self.oldmodel.prior )
                    self.pprint ( "llhd", self.model.llhd )
                    self.pprint ( "prior", self.model.prior )
                    sys.exit()
                self.takeStep()
            else:
                u=random.uniform(0.,1.)
                if u > ratio:
                    self.pprint ( "u=%.2f > %.2f; Z: %.2f -> %.2f: revert." % (u,ratio,self.oldmodel.Z, self.model.Z) )
                    self.revert()
                else:
                    self.pprint ( "u=%.2f <= %.2f ; %.2f -> %.2f: take the step, even though old is better." % (u, ratio,self.oldmodel.Z,self.model.Z) )
                    self.takeStep()
        self.saveState()

def _run ( w ):
    if w.walkerid==0 and args.regressor:
        w.turnOnRegress()
    try:
        w.walk()
    except Exception as e:
        import time
        with open("exceptions.log","a") as f:
            f.write ( "time %s\n" % time.asctime() )
            f.write ( "walker %d threw: %s\n" % ( w.walkerid, e ) )
            if hasattr ( w.model, "currentSLHA" ):
                f.write ("slha file was %s\n" % w.model.currentSLHA )

if __name__ == "__main__":
    print ( "[walk] ramping up" )
    import argparse
    argparser = argparse.ArgumentParser(
            description='model walker. builds BSM models of interest')
    argparser.add_argument ( '-s', '--strategy',
            help='combination strategy [aggressive]',
            type=str, default="aggressive" )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug,info,warn,error [info]',
            type=str, default="info" )
    argparser.add_argument ( '-n', '--nsteps',
            help='number of steps [100000]',
            type=int, default=100000 )
    argparser.add_argument ( '-p', '--ncpus',
            help='number of CPUs. -1 means all. [1]',
            type=int, default=1 )
    argparser.add_argument ( '-r', '--regressor',
            help='use the NN regressor', action='store_true' )
    argparser.add_argument ( '-c', '--cont',
            help='continue with saved states [""]',
            type=str, default="" )
    argparser.add_argument ( '-H', '--history', help='record history',
                             action="store_true" )
    args = argparser.parse_args()
    cleanDirectory()
    ncpus = args.ncpus
    if ncpus < 0:
        ncpus = nCPUs() + ncpus + 1
    walkers = []

    if args.cont!="" and os.path.exists ( args.cont ) and \
                   os.stat( args.cont ).st_size > 100:
        with open( args.cont, "rb" ) as f:
            hiscores = pickle.load ( f )
        while len(walkers)<ncpus:
            ctr=0
            for v in hiscores: # .items()):
                if ctr >= ncpus:
                    break
                if v == None:
                    # no hiscore? start from scratch!
                    walker = RandomWalker( ctr, args.nsteps, args.strategy, False )
                    walker.takeStep()
                    walkers.append ( walker )
                    continue
                v.createNewSLHAFileName()
                v.walkerid = ctr
                walkers.append ( RandomWalker.fromModel ( v, use_regressor=False ) )
                walkers[-1].walkerid = ctr
                walkers[-1].takeStep() # make last step a taken one
                ctr+=1
    else:
        for w in range(ncpus):
            walkers.append ( RandomWalker( w, args.nsteps, args.strategy, False ) )

    print ( "[walk] loading hiscores" )
    hiscore = Hiscore ( 0, True )
    for w in walkers:
        w.supplyHiscoreList ( hiscore )
    onoff="off"
    if args.history:
        onoff="on"
        walkers[0].record_history = True
    print ( "[walk] record histories is %s" % onoff )

    print ( "[walk] starting %d walkers" % len(walkers) )
    if len ( walkers ) == 1:
        walkers[0].walk() ## just one, start directly
    else:
        p = multiprocessing.Pool ( ncpus )
        p.map ( _run, walkers )
