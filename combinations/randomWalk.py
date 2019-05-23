#!/usr/bin/env python3

""" a first start at the random walk idea """

import random, subprocess, copy, pickle, sys, numpy
from predictor import predict
from combiner import Combiner
from smodels.tools.xsecComputer import XSecComputer, LO
from scipy import stats

class RandomWalker:
    LSP = 1000022
    def __init__ ( self, nsteps=500 ):
        """ initialise the walker 
        :param nsteps: maximum number of steps to perform
        """
        self.particles = [ 1000001, 2000001, 1000002, 2000002, 1000003, 2000003, 
                  1000004, 2000004, 1000005, 2000005, 1000006, 2000006, 1000011, 
                  2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015, 
                  1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024, 
                  1000037 ]
        self.names = { 1000001: "~q", 2000001: "~q", 1000002: "~q", 
                       2000002: "~q", 1000003: "~q", 2000003: "~q", 
                       1000004: "~q", 2000004: "~q", 1000005: "~b", 
                       2000005: "~b", 1000006: "~t", 2000006: "~t", 
                       1000011: "~e", 2000011: "~e", 1000012: "~nu", 
                       1000013: "~mu", 2000013: "~mu", 1000014: "~nu", 
                       1000015: "~tau", 2000015: "~tau", 1000016: "~nu", 
                       1000021: "~g", 1000022: "~chi10", 1000023: "~chi20", 
                       1000025: "~chi30", 1000035: "~chi40", 1000024: "~chi1+", 
                  1000037: "~chi2+" }
        self.maxsteps = nsteps
        self.templateSLHA = "template.slha"
        self.onesquark = True ## only one light squark
        if self.onesquark:
            self.particles = [ 1000001, 1000005, 1000006, 1000011, 1000012, 
                      1000013, 1000014, 1000015,  1000016, 1000021, 1000022, 
                      1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "template_1q.slha"
        self.possibledecays = {} ## list all possible decay channels
        self.decays = {} ## the actual branchings
        self.masses = {}
        self.step = 0 ## count the steps
        slhaf = open ( self.templateSLHA )
        tmp = slhaf.readlines()
        slhalines = []
        for line in tmp:
            p = line.find("#" )
            if p > -1:
                line = line[:p]
            if "D" in line and not "DECAY" in line:
                slhalines.append ( line.strip().split(" ")[0] )
        slhaf.close()

        for p in self.particles:
            self.masses[p]=1e6
            decays = []
            self.decays[p]={}
            for line in slhalines:
                if "D%s" % p in line:
                    _ = line.find("_")+1
                    dpid = int ( line[_:] )
                    decays.append ( dpid )
                    self.decays[p][dpid]=0.
                    if dpid == self.LSP:
                        self.decays[p][dpid]=1.
            self.possibledecays[p]=decays

        ## the LSP we need from the beginning
        self.masses[self.LSP]=random.uniform(50,500)
        self.oldmasses = copy.deepcopy (self.masses ) ## the state of the previous step
        self.oldZ = 0. ## Z of the previous step
        self.oldllhd = stats.norm.pdf( self.oldZ ) ## llhd of previous step
        self.olddecays = copy.deepcopy ( self.decays )
        self.oldpossibledecays = copy.deepcopy ( self.possibledecays )
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

    def freezeRandomParticle ( self ):
        """ freezes a random unfrozen particle """
        unfrozen = self.unFrozenParticles()
        if len(unfrozen)<3:
            return ## freeze only if at least 3 unfrozen particles exist
        unfrozen.remove ( self.LSP )
        p = random.choice ( unfrozen )
        self.masses[p]=1e6
        print ( "[walk] Freezing %d: m=%f" % ( p, self.masses[p] ) )

    def randomlyChangeBranchings ( self ):
        """ randomly change the branchings of a single particle """
        unfrozenparticles = self.unFrozenParticles()
        if len(unfrozenparticles)<2:
            print ( "[walk] not enough unfrozen particles to change random branching" )
            return
        unfrozenparticles.remove ( self.LSP )
        p = random.choice ( unfrozenparticles )
        openChannels = []
        for dpid,br in self.decays[p].items():
            if dpid in self.unFrozenParticles():
                openChannels.append ( dpid )
            # print ( "[walk] old `- pid,br", dpid, br, dpid in self.unFrozenParticles() )
        if len(openChannels) < 2:
            # not enough channels open to tamper with branchings!
            return
        dx =.1/numpy.sqrt(len(openChannels)) ## maximum change per channel
        S=0.
        for i in openChannels[:-1]:
            oldbr = self.decays[p][i]
            br = oldbr+random.uniform(-dx,dx)
            if br < 0.: br = 0.
            if br > 1.: br = 1.
            self.decays[p][i]=br
            S+=br
        self.decays[p][ openChannels[-1] ] = 1. - S
            
        print ( "[walk] changed branchings of ", p )
        # print ( "[walk] we have %d open channels" % nChannels )
        for dpid,br in self.decays[p].items():
            if dpid in self.unFrozenParticles():
                openChannels.append ( dpid )
            # print ( "[walk] new `- pid,br", dpid, br, dpid in self.unFrozenParticles() )

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
                for dpid,dbr in self.decays[m].items():
                    line=line.replace("D%d_%d" % ( m, dpid), "%.1f" % dbr )
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

    def pprint ( self, *args ):
        """ logging """
        print ( "[walk] %s" % args )

    def onestep ( self ):
        self.step+=1
        u = random.uniform(0,1)
        if u > .9:
            # in about every tenth step unfreeze random particle
            self.unfreezeRandomParticle()
        elif .8 < u < .9:
            # in about every tenth step randomly change branchings of a particle
            self.randomlyChangeBranchings()
        elif .7 < u < .8:
            # in about every tenth step randomly change branchings of a particle
            self.freezeRandomParticle()
        else:
            self.takeRandomStep()
        self.createSLHAFile()
        self.computeXSecs()
        predictions = predict ( "current.slha" )
        self.pprint ( "I got %d predictions" % ( len(predictions) ) )
        combiner = Combiner()
        strategy = "aggressive"
        bestCombo,Z,llhd = combiner.findHighestSignificance ( predictions, strategy )
        self.bestCombo = bestCombo
        self.llhd = (1. - llhd ) ## we wish to minimize likelihood, find the most unexpected fluctuation
        self.Z = Z
        self.computePrior()
        print ( "[walk] best combo for strategy ``%s'' is %s: %s: [Z=%.2f]" % ( strategy, combiner.getLetterCode(bestCombo), combiner.getComboDescription(bestCombo), Z ) )

    def revert ( self ):
        """ revert the last step. go back. """
        self.masses = copy.deepcopy ( self.oldmasses )
        self.prior = self.oldprior
        self.llhd = self.oldllhd
        self.Z = self.oldZ
        self.decays = copy.deepcopy ( self.olddecays )
        self.possibledecays = copy.deepcopy ( self.oldpossibledecays )

    def takeStep ( self ):
        """ take the step, save it as last step """
        self.oldmasses = copy.deepcopy ( self.masses )
        self.oldprior = self.prior
        self.oldllhd = self.llhd
        self.oldZ = self.Z
        self.olddecays = copy.deepcopy ( self.decays )
        self.oldpossibledecays = copy.deepcopy ( self.possibledecays )
        
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
        while self.step<self.maxsteps:
            self.onestep()
            self.computePrior()
            print ( "[walk] prior times llhd, before versus after: %f -> %f" % ( self.oldPriorTimesLlhd(), self.priorTimesLlhd() ) )
            ratio = self.priorTimesLlhd() / self.oldPriorTimesLlhd()

            if ratio >= 1.:
                print ( "[walk] Z: %.2f -> %.2f: take the step" % ( self.oldZ, self.Z ) )
                if self.Z < self.oldZ:
                    print ( " `- weird, though, Z decreases. Please check." )
                    print ( "oldllhd", self.oldllhd )
                    print ( "oldprior", self.oldprior )
                    print ( "llhd", self.llhd )
                    print ( "prior", self.prior )
                    sys.exit()
                self.takeStep()
            else:
                u=random.uniform(0.,1.)
                if u > ratio:
                    print ( "[walk] u=%.2f > %.2f; Z: %.2f -> %.2f: go back" % (u,ratio,self.oldZ, self.Z) )
                    self.revert()
                else:
                    print ( "[walk] u=%.2f <= %.2f ; %.2f -> %.2f: take the step, even though old is better." % (u, ratio,self.oldZ,self.Z) )
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
