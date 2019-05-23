#!/usr/bin/env python3

""" a first start at the random walk idea """

import random, subprocess, copy, pickle, sys, numpy, os, tempfile
from predictor import predict
from combiner import Combiner
from smodels.tools.xsecComputer import XSecComputer, LO
from smodels.tools.runtime import nCPUs
from scipy import stats

class RandomWalker:
    LSP = 1000022
    def __init__ ( self, nsteps=500, strategy="aggressive", hiscore=False ):
        """ initialise the walker
        :param nsteps: maximum number of steps to perform
        """
        self.particles = [ 1000001, 2000001, 1000002, 2000002, 1000003, 2000003,
                  1000004, 2000004, 1000005, 2000005, 1000006, 2000006, 1000011,
                  2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015,
                  1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024,
                  1000037 ]
        self.save_hiscore = hiscore
        self.currentSLHA = tempfile.mktemp(prefix="cur",suffix=".slha",dir="./")
        self.strategy = strategy
        self.names = { 1000001: "~q", 2000001: "~q", 1000002: "~q",
                       2000002: "~qR", 1000003: "~q", 2000003: "~qR",
                       1000004: "~c", 2000004: "~cR", 1000005: "~b",
                       2000005: "~bR", 1000006: "~t", 2000006: "~tR",
                       1000011: "~e", 2000011: "~eR", 1000012: "~nu",
                       1000013: "~mu", 2000013: "~muR", 1000014: "~nu",
                       1000015: "~tau", 2000015: "~tauR", 1000016: "~nu",
                       1000021: "~g", 1000022: "~chi10", 1000023: "~chi20",
                       1000025: "~chi30", 1000035: "~chi40", 1000024: "~chi1+",
                       1000037: "~chi2+" }
        self.highestZ = -1. ## keep track of hiscore!
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
        self.computePrior()
        self.llhd=0.
        self.Z = 0.
        self.takeStep() ## the first step should be considered as "taken"

    def removeDataFromBestCombo ( self, bestCombo ):
        """ remove the data from all theory predictions, we dont need them. """
        for combo in bestCombo:
            eR = combo.expResult
            for ds in eR.datasets:
                for tx in ds.txnameList:
                    del tx.txnameData
        return bestCombo

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
        if len(frozen)==0:
            return 0
        p = random.choice ( frozen )
        self.masses[p]=random.uniform ( self.masses[self.LSP], 3000. )
        print ( "[walk] Unfreezing %s: m=%f" % ( self.getParticleName(p), self.masses[p] ) )
        return 1

    def getParticleName ( self, p ):
        sp = str(p)
        if p in self.names:
            sp = self.names[p]
        return sp

    def freezeRandomParticle ( self ):
        """ freezes a random unfrozen particle """
        unfrozen = self.unFrozenParticles()
        if len(unfrozen)<3:
            return 0 ## freeze only if at least 3 unfrozen particles exist
        unfrozen.remove ( self.LSP )
        p = random.choice ( unfrozen )
        self.masses[p]=1e6
        print ( "[walk] Freezing %s." % ( self.getParticleName(p) ) )
        return 1

    def randomlyChangeBranchings ( self ):
        """ randomly change the branchings of a single particle """
        unfrozenparticles = self.unFrozenParticles()
        if len(unfrozenparticles)<2:
            print ( "[walk] not enough unfrozen particles to change random branching" )
            return 0
        unfrozenparticles.remove ( self.LSP )
        p = random.choice ( unfrozenparticles )
        openChannels = []
        for dpid,br in self.decays[p].items():
            if dpid in self.unFrozenParticles():
                openChannels.append ( dpid )
            # print ( "[walk] old `- pid,br", dpid, br, dpid in self.unFrozenParticles() )
        if len(openChannels) < 2:
            # not enough channels open to tamper with branchings!
            return 0
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

        self.pprint ( "changed branchings of %s." % self.getParticleName(p) )
        # print ( "[walk] we have %d open channels" % nChannels )
        for dpid,br in self.decays[p].items():
            if dpid in self.unFrozenParticles():
                openChannels.append ( dpid )
            # print ( "[walk] new `- pid,br", dpid, br, dpid in self.unFrozenParticles() )
        return 1

    def takeRandomMassStep ( self ):
        """ take a random step in mass space for all unfrozen particles """
        dx = 20. / numpy.sqrt ( len(self.unFrozenParticles() ) )
        for i in self.unFrozenParticles():
            self.masses[i]=self.masses[i]+random.uniform(-dx,dx)

    def createSLHAFile ( self ):
        """ from the template.slha file, create the slha file of the current
            model. """
        f=open( self.templateSLHA )
        lines=f.readlines()
        f.close()
        if not hasattr ( self, "currentSLHA" ):
            self.currentSLHA = tempfile.mktemp(prefix="cur",suffix=".slha",dir="./")
        f=open(self.currentSLHA,"w")
        for line in lines:
            for m,v in self.masses.items():
                line=line.replace("M%d" % m,"%.1f" % v )
                for dpid,dbr in self.decays[m].items():
                    line=line.replace("D%d_%d" % ( m, dpid), "%.1f" % dbr )
            f.write ( line )
        f.close()

    def computeXSecs ( self ):
        """ compute xsecs for current.slha """
        # print ( "[walk] computing xsecs for %s" % self.currentSLHA )
        computer = XSecComputer ( LO, 2000, 6 )
        computer.computeForOneFile ( [8,13], self.currentSLHA,
                unlink=True, lOfromSLHA=False, tofile=True )

    def computePrior ( self ):
        """ compute the prior for the current model.
        """
        self.prior = 1. / ( len(self.unFrozenParticles()))

    def getZFromPickle ( self ):
        """ get the high score Z from pickle file """
        if not os.path.exists ( "hiscore.pcl" ):
            return -1.
        if os.stat( "hiscore.pcl" ).st_size < 100:
            return -1.
        f=open("hiscore.pcl","rb")
        hi = pickle.load ( f )
        f.close()
        return hi.Z

    def pprint ( self, *args ):
        """ logging """
        print ( "[walk] %s" % (" ".join(map(str,args))) )

    def onestep ( self ):
        self.step+=1
        nUnfrozen = len ( self.unFrozenParticles() )
        nTotal = len ( self.masses.keys() )
        self.pprint ( "Step %d has %d/%d unfrozen particles: %s" % ( self.step, nUnfrozen, nTotal, ", ".join ( map ( self.getParticleName, self.unFrozenParticles() ) ) ) )
        # uUnfreeze = random.uniform(0,1)
        nChanges = 0
        uUnfreeze = random.gauss(.5,.5)
        if uUnfreeze > nUnfrozen/float(nTotal):
            # in about every tenth step unfreeze random particle
            nChanges += self.unfreezeRandomParticle()
        uBranch = random.uniform(0,1)
        if uBranch > .75:
            nChanges += self.randomlyChangeBranchings()
        # uFreeze = random.uniform(0,1)
        uFreeze = random.gauss(.5,.5)
        if uFreeze < nUnfrozen/float(nTotal):
            # in about every tenth step randomly change branchings of a particle
            nChanges+=self.freezeRandomParticle()
        if nChanges == 0:
            self.takeRandomMassStep()
        self.createSLHAFile()
        self.computeXSecs()
        predictions = predict ( self.currentSLHA )
        # self.pprint ( "I got %d predictions" % ( len(predictions) ) )
        combiner = Combiner()
        bestCombo,Z,llhd = combiner.findHighestSignificance ( predictions, self.strategy )
        self.bestCombo = self.removeDataFromBestCombo ( bestCombo )
        self.llhd = (1. - llhd ) ## we wish to minimize likelihood, find the most unexpected fluctuation
        self.Z = Z
        if self.Z > self.highestZ and self.save_hiscore:
            ## check also the pickle file
            hiZ = self.getZFromPickle ()
            if self.Z > hiZ: ## also higher than what is in the pickle file.
                self.pprint ( "new hiscore! save it to hiscore.pcl." )
                self.highestZ = Z
                if os.path.exists ( "hiscore.pcl" ):
                    subprocess.getoutput ("mv -f hiscore.pcl oldhiscore.pcl" )
                f=open("hiscore.pcl","wb")
                pickle.dump( self, f )
                f.close()
                subprocess.getoutput ( "cp hiscore.slha oldhiscore.slha" )
                subprocess.getoutput ( "cp %s.slha hiscore.slha" % self.currentSLHA )
        self.computePrior()
        self.pprint ( "best combo for strategy ``%s'' is %s: %s: [Z=%.2f]" % ( self.strategy, combiner.getLetterCode(bestCombo), combiner.getComboDescription(bestCombo), Z ) )

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
            self.pprint ( "prior times llhd, before versus after: %f -> %f" % ( self.oldPriorTimesLlhd(), self.priorTimesLlhd() ) )
            #ratio = 1.
            #if self.oldZ > 0.:
            #    ratio = self.Z / self.oldZ
            ratio = 1.
            if self.oldPriorTimesLlhd() > 0.:
                ratio = self.priorTimesLlhd() / self.oldPriorTimesLlhd()
            if self.oldZ > 0. and self.Z < 0.7 * self.oldZ:
                ## no big steps taken here.
                self.pprint ( "Z=%.2f -> 0. Revert." % self.oldZ )
                self.revert()
                continue

            if ratio >= 1.:
                self.pprint ( "Z: %.3f -> %.3f: take the step" % ( self.oldZ, self.Z ) )
                if self.Z < 0.7 * self.oldZ:
                    self.pprint ( " `- weird, though, Z decreases. Please check." )
                    self.pprint ( "oldllhd %f" % self.oldllhd )
                    self.pprint ( "oldprior", self.oldprior )
                    self.pprint ( "llhd", self.llhd )
                    self.pprint ( "prior", self.prior )
                    sys.exit()
                self.takeStep()
            else:
                u=random.uniform(0.,1.)
                if u > ratio:
                    print ( "[walk] u=%.2f > %.2f; Z: %.2f -> %.2f: revert." % (u,ratio,self.oldZ, self.Z) )
                    self.revert()
                else:
                    print ( "[walk] u=%.2f <= %.2f ; %.2f -> %.2f: take the step, even though old is better." % (u, ratio,self.oldZ,self.Z) )
                    self.takeStep()
        self.saveState()


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='model walker. builds BSM models of interest')
    argparser.add_argument ( '-s', '--strategy',
            help='combination strategy [aggressive]',
            type=str, default="aggressive" )
    argparser.add_argument ( '-n', '--nsteps',
            help='number of steps [500]',
            type=int, default=500 )
    argparser.add_argument ( '-p', '--ncpus',
            help='number of CPUs. -1 means all. [1]',
            type=int, default=1 )
    argparser.add_argument ( '-c', '--cont',
            help='continue with last save state [False]',
            action="store_true" )
    argparser.add_argument ( '-S', '--hiscore',
            help='save states with highest Zs [False]',
            action="store_true" )
    args = argparser.parse_args()
    ncpus = args.ncpus
    if ncpus < 0:
        ncpus = nCPUs() + ncpus + 1
    if args.cont and os.path.exists ( "state.pcl" ) and os.stat("state.pcl").st_size > 100:
        f=open("state.pcl","rb")
        walker = pickle.load ( f )
        f.close()
    else:
        walker = RandomWalker( args.nsteps, args.strategy, args.hiscore )
    walker.walk()
