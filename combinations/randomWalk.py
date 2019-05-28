#!/usr/bin/env python3

""" a first start at the random walk idea """

import random, copy, pickle, sys, os, time
import multiprocessing
from predictor import predict
from combiner import Combiner
from smodels.tools.runtime import nCPUs
import colorama
from hiscore import Hiscore
from model import Model

class RandomWalker:
    def __init__ ( self, walkerid=0, nsteps=10000, strategy="aggressive" ):
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
        self.maxsteps = nsteps
        self.takeStep() ## the first step should be considered as "taken"

    @classmethod
    def fromModel(cls, model, nsteps=10000, strategy="aggressive", hiscore=False, walkerid=0 ):
        ret = cls( walkerid, nsteps, strategy )
        ret.model = model
        return ret

    def removeDataFromBestCombo ( self, bestCombo ):
        """ remove the data from all theory predictions, we dont need them. """
        for combo in bestCombo:
            eR = combo.expResult
            for ds in eR.datasets:
                for tx in ds.txnameList:
                    del tx.txnameData
        return bestCombo

    def pprint ( self, *args ):
        """ logging """
        print ( "[walk:%d-%s] %s" % ( self.walkerid, time.strftime("%H:%M"), " ".join(map(str,args))) )
        self.log ( *args )

    def onestep ( self ):
        self.model.step+=1
        nUnfrozen = len ( self.model.unFrozenParticles() )
        nTotal = len ( self.model.masses.keys() )
        self.pprint ( "Step %d has %d/%d unfrozen particles: %s" % ( self.model.step, nUnfrozen, nTotal, ", ".join ( map ( self.model.getParticleName, self.model.unFrozenParticles() ) ) ) )
        # uUnfreeze = random.uniform(0,1)
        nChanges = 0
        uUnfreeze = random.gauss(.5,.5)
        if uUnfreeze > nUnfrozen/float(nTotal):
            # in every nth step unfreeze random particle
            self.log ( "unfreeze random particle" )
            nChanges += self.model.unfreezeRandomParticle()
        uBranch = random.uniform(0,1)
        if uBranch > .5: # do this often
            self.log ( "randomly change branchings" )
            nChanges += self.model.randomlyChangeBranchings()
        uSSM = random.uniform(0,1)
        if uSSM > .75: # do this less often
            self.log ( "randomly change signal strengths" )
            nChanges += self.model.randomlyChangeSignalStrengths()

        # uFreeze = random.uniform(0,1)
        uFreeze = random.gauss(.5,.5)
        if uFreeze < nUnfrozen/float(nTotal):
            # in every nth step freeze random particle
            if random.uniform(0,1)<.5:
                self.log ( "freeze most massive particle" )
                nChanges+=self.model.freezeMostMassiveParticle()
            else:
                self.log ( "freeze random particle" )
                nChanges+=self.model.freezeRandomParticle()
        if nChanges == 0:
            self.log ( "take random mass step" )
            self.model.takeRandomMassStep()
        self.log ( "now create slha file" )
        self.model.createSLHAFile()
        self.log ( "now create xsecs for %s" % self.model.currentSLHA )
        self.model.computeXSecs()
        self.log ( "done computing xsecs" )
        #predictions = predict ( self.model.currentSLHA )
        #self.log ( "I got %d predictions" % ( len(predictions) ) )
        #combiner = Combiner()
        # bestCombo,Z,llhd = combiner.findHighestSignificance ( predictions, self.strategy )
        bestCombo,Z,llhd = self.model.predict( self.strategy )
        self.log ( "found highest Z: %.2f" % Z )
        self.model.bestCombo = self.removeDataFromBestCombo ( bestCombo )
        self.model.llhd = (1. - llhd ) ## we wish to minimize likelihood, find the most unexpected fluctuation
        self.model.Z = Z
        if self.hiscoreList != None:
            self.log ( "check if result goes into hiscore list" )
            self.hiscoreList.newResult ( self.model ) ## add to high score list
        self.model.computePrior()
        self.pprint ( "best combo for strategy ``%s'' is %s: %s: [Z=%.2f]" % ( self.strategy, combiner.getLetterCode(bestCombo), combiner.getComboDescription(bestCombo), Z ) )
        self.log ( "step %d finished." % self.model.step )

    def revert ( self ):
        """ revert the last step. go back. """
        self.model = copy.deepcopy ( self.oldmodel )

    def supplyHiscoreList ( self, Hiscorelist ):
        """ supply hiscore list, to avoid loading n times. """
        self.hiscoreList = Hiscorelist
        self.hiscoreList.walkerid = self.walkerid

    def takeStep ( self ):
        """ take the step, save it as last step """
        self.oldmodel = copy.deepcopy ( self.model )

    def saveState ( self ):
        """ write out current state, for later retrieval """
        f=open("state.pcl","wb")
        pickle.dump ( self, f )
        f.close()

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[walk:%d] %s%s" % ( col, self.walkerid, " ".join(map(str,args)), colorama.Fore.RESET ) )

    def log ( self, *args ):
        """ logging to file """
        f=open( "walker%d.log" % self.walkerid, "a" )
        f.write ( "[walk:%d - %s] %s\n" % ( self.walkerid, time.asctime(), " ".join(map(str,args)) ) )
        f.close()

    def walk ( self ):
        """ Now perform the random walk """
        self.model.unfreezeRandomParticle() ## start with unfreezing a random particle
        while self.model.step<self.maxsteps:
            self.onestep()
            self.model.computePrior()
            self.pprint ( "prior times llhd, before versus after: %f -> %f" % ( self.oldmodel.priorTimesLlhd(), self.model.priorTimesLlhd() ) )
            #ratio = 1.
            #if self.oldmodel.Z > 0.:
            #    ratio = self.Z / self.oldmodel.Z
            ratio = 1.
            if self.oldmodel.priorTimesLlhd() > 0.:
                ratio = self.model.priorTimesLlhd() / self.oldmodel.priorTimesLlhd()
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
                    print ( "[walk] u=%.2f > %.2f; Z: %.2f -> %.2f: revert." % (u,ratio,self.oldmodel.Z, self.model.Z) )
                    self.revert()
                else:
                    print ( "[walk] u=%.2f <= %.2f ; %.2f -> %.2f: take the step, even though old is better." % (u, ratio,self.oldmodel.Z,self.model.Z) )
                    self.takeStep()
        self.saveState()

def _run ( w ):
    w.walk()

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='model walker. builds BSM models of interest')
    argparser.add_argument ( '-s', '--strategy',
            help='combination strategy [aggressive]',
            type=str, default="aggressive" )
    argparser.add_argument ( '-n', '--nsteps',
            help='number of steps [10000]',
            type=int, default=10000 )
    argparser.add_argument ( '-p', '--ncpus',
            help='number of CPUs. -1 means all. [1]',
            type=int, default=1 )
    argparser.add_argument ( '-c', '--cont',
            help='continue with saved states [""]',
            type=str, default="" )
    args = argparser.parse_args()
    ncpus = args.ncpus
    if ncpus < 0:
        ncpus = nCPUs() + ncpus + 1
    walkers = []
        
    if args.cont!="" and os.path.exists ( args.cont ) and \
                   os.stat( args.cont ).st_size > 100:
        f=open( args.cont, "rb" )
        hiscores = pickle.load ( f )
        f.close()
        for ctr,(k,v) in enumerate(hiscores.items()):
            if ctr >= ncpus:
                break
            walkers.append ( RandomWalker.fromModel ( v ) )
            walkers[-1].walkerid = ctr
    else:
        for w in range(ncpus):
            walkers.append ( RandomWalker( w, args.nsteps, args.strategy ) )

    hiscore = Hiscore ( 0, True )
    for w in walkers:
        w.supplyHiscoreList ( hiscore )
            
    if len ( walkers ) == 1:
        walkers[0].walk() ## just one, start directly
    else:
        p = multiprocessing.Pool ( ncpus )
        p.map ( _run, walkers ) 
