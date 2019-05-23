#!/usr/bin/env python3

""" a first start at the random walk idea """

import random, subprocess, copy, pickle
from predictor import predict
from combiner import Combiner
from smodels.tools.xsecComputer import XSecComputer, LO
from scipy import stats

class RandomWalker:
    LSP = 1000022
    def __init__ ( self ):
        """ initialise the walker """
        self.particles = [ 1000001, 2000001, 1000002, 2000002, 1000003, 2000003, 
                  1000004, 2000004, 1000005, 2000005, 1000006, 2000006, 1000011, 
                  2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015, 
                  1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024, 
                  1000037 ]
        self.templateSLHA = "template.slha"
        self.onesquark = True ## only one light squark
        if self.onesquark:
            self.particles = [ 1000001, 1000005, 1000006, 1000011, 
                      2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015, 
                      1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024, 
                      1000037 ]
            self.templateSLHA = "template_1q.slha"
        self.masses = {}
        self.step = 0 ## count the steps
        for p in self.particles:
            self.masses[p]=1e6
        ## the LSP we need from the beginning
        self.masses[self.LSP]=random.uniform(50,500)
        self.oldmasses = copy.deepcopy (self.masses ) ## the state of the previous step
        self.oldZ = 0. ## Z of the previous step
        self.oldllhd = stats.norm.pdf( self.oldZ ) ## llhd of previous step
        self.oldprior = 1. ## prior of previous step (we start with one free param)

    def frozenParticles ( self ):
        """ returns a list of all particles that can be regarded as frozen
            (ie mass greater than 1e5 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)>1e5:
                ret.append(m)
        return ret

    def unFrozenParticles ( self ):
        """ returns a list of all particles that can be regarded as unfrozen
            (ie mass less than 5e3 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)<5e3:
                ret.append(m)
        return ret

    def unfreezeRandomParticle ( self ):
        """ unfreezes a random frozen particle """
        frozen = self.frozenParticles()
        p = random.choice ( frozen )
        self.masses[p]=random.uniform ( self.masses[self.LSP], 3000. )
        print ( "[walk] Unfreezing %d: m=%f" % ( p, self.masses[p] ) )

    def takeRandomStep ( self ):
        """ take a random step for all unfrozen particles """
        dx = 20. / numpy.sqrt ( len(self.unFrozenParticles() ) )
        for i in self.unFrozenParticles():
            self.masses[i]=self.masses[i]+random.uniform(-dx,dx)

    def createSLHAFile ( self ):
        """ from the template.slha file, create the slha file of the current
            model. """
        f=open( self.templateSLHA )
        lines=f.readlines()
        f.close()
        f=open("current.slha","w")
        for line in lines:
            for m,v in self.masses.items():
                line=line.replace("M%d" % m,"%.1f" % v )
            f.write ( line )
        f.close()

    def computeXSecs ( self ):
        """ compute xsecs for current.slha """
        print ( "[walk] computing xsecs for current.slha" )
        computer = XSecComputer ( LO, 2000, 6 )
        computer.computeForOneFile ( [8,13], "current.slha", 
                unlink=True, lOfromSLHA=False, tofile=True )

    def computePrior ( self ):
        """ compute the prior for the current model.
        """
        self.prior = 1. / ( len(self.unFrozenParticles()))

    def onestep ( self ):
        self.step+=1
        u = random.uniform(0,1)
        if u > .9:
            # about every tenth step unfreeze random particle
            self.unfreezeRandomParticle()
        else:
            self.takeRandomStep()
        self.createSLHAFile()
        self.computeXSecs()
        predictions = predict ( "current.slha" )
        print ( "[walk] I got %d predictions" % ( len(predictions) ) )
        combiner = Combiner()
        strategy = "aggressive"
        bestCombo,Z,llhd = combiner.findHighestSignificance ( predictions, strategy )
        self.bestCombo = bestCombo
        self.llhd = (1. - llhd ) ## we wish to minimize likelihood, find the most unexpected fluctuation
        self.computePrior()
        print ( "[walk] best combo for strategy ``%s'' is %s: %s: [Z=%.2f]" % ( strategy, combiner.getLetterCode(bestCombo), combiner.getComboDescription(bestCombo), Z ) )

    def revert ( self ):
        """ revert the last step. go back. """
        self.masses = copy.deepcopy ( self.oldmasses )
        self.prior = self.oldprior
        self.llhd = self.oldllhd

    def takeStep ( self ):
        """ take the step, save it as last step """
        self.oldmasses = copy.deepcopy ( self.masses )
        self.oldprior = self.prior
        self.oldllhd = self.llhd
        
    def priorTimesLlhd( self ):
        return self.prior * self.llhd

    def oldPriorTimesLlhd ( self ):
        return self.oldprior * self.oldllhd

    def saveState ( self ):
        """ write out current state, for later retrieval """
        f=open("state.pcl","wb")
        pickle.dump ( self, f )
        f.close()

    def walk ( self ):
        """ Now perform the random walk """
        self.unfreezeRandomParticle() ## start with unfreezing a random particle
        while self.step<50:
            self.onestep()
            self.computePrior()
            print ( "[walk] prior times llhd, before versus after: %f -> %f" % ( self.oldPriorTimesLlhd(), self.priorTimesLlhd() ) )
            ratio = self.priorTimesLlhd() / self.oldPriorTimesLlhd()

            if ratio >= 1.:
                print ( "[walk] take the step" )
                self.takeStep()
            else:
                u=random.uniform(0.,1.)
                if u > ratio:
                    print ( "[walk] u=%.2f > %.2f; go back" % (u,ratio) )
                    self.revert()
                else:
                    print ( "[walk] u=%.2f <= %.2f ; take the step, even though old is better." % (u, ratio) )
                    self.takeStep()
        self.saveState()


if __name__ == "__main__":
    continueOld = False
    if continueOld and os.path.exists ( "state.pcl" ):
        f=open("state.pcl","rb")
        walker = pickle.load ( self, f )
        f.close()
    else:
        walker = RandomWalker()
    walker.walk()
