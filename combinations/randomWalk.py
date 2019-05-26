#!/usr/bin/env python3

""" a first start at the random walk idea """

import random, subprocess, copy, pickle, sys, numpy, os, tempfile, fcntl, time
import multiprocessing
from predictor import predict
from combiner import Combiner
from smodels.tools.xsecComputer import XSecComputer, LO
from smodels.tools.runtime import nCPUs
from scipy import stats

class Hiscore:
    """ encapsulates the hiscore list. """
    def __init__ ( self, save_hiscores ):
        self.save_hiscores = save_hiscores
        self.nkeep = 20 ## how many do we keep.
        self.hiscores = {}
        self.fileAttempts = 0 ## unsucessful attempts at reading or writing
        self.updateListFromPickle ( )

    def currentMinZ ( self ):
        """ the current minimum Z to make it into the list. """
        if len(self.hiscores)==0:
            return 0.
        return min ( self.hiscores.keys() )

    def addResult ( self, model ):
        """ add a result to the list """
        while model.Z in self.hiscores.keys():
            model.Z = model.Z-1e-20
        self.hiscores[model.Z]=copy.deepcopy(model)
        self.trimList()

    def trimList ( self ):
        keys = list ( self.hiscores.keys() )
        if len(keys)<= self.nkeep:
            return
        keys.sort( reverse=True )
        tmp = {}
        for k in keys[:self.nkeep]:
            tmp[k]=copy.deepcopy ( self.hiscores[k] )
        self.hiscores = tmp

    def updateListFromPickle ( self ):
        """ fetch the list from the pickle file """
        if not os.path.exists ( "hiscore.pcl" ):
            return
        try:
            f=open("hiscore.pcl","rb")
            fcntl.lockf( f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.hiscores = pickle.load ( f )
            fcntl.lockf( f, fcntl.LOCK_UN)
            f.close()
            self.fileAttempts=0
        except OSError or BlockingIOError:
            self.fileAttempts+=1
            if self.fileAttempts<5: # try again
                time.sleep (.01 )
                self.updateListFromPickle()

    def writeListToPickle ( self ):
        """ dump the list to the pickle file """
        self.pprint ( "saving new hiscore list." )
        try:
            f=open("hiscore.pcl","wb" )
            fcntl.lockf( f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            pickle.dump ( self.hiscores, f )
            fcntl.lockf( f, fcntl.LOCK_UN )
            f.close()
            self.fileAttempts=0
        except OSError or BlockingIOError:
            self.fileAttempts+=1
            if self.fileAttempts<5: # try again
                time.sleep (.01 )
                self.writeListToPickle()

    def newResult ( self, model ):
        """ see if new result makes it into hiscore list. If yes, then add.
        """
        # self.pprint ( "New result with Z=%.2f, %s" % (model.Z, self.save_hiscores ) )
        if not self.save_hiscores:
            return
        if model.Z <= 0.: ## we ignore models with Z==0.
            return
        if len ( self.hiscores.keys() ) > 0 and \
            model.Z < self.currentMinZ():
                return ## clearly out

        self.addResult ( model )
        self.writeListToPickle()

    def pprint ( self, *args ):
        """ logging """
        print ( "[hiscore] %s" % (" ".join(map(str,args))) )

class Model:
    """ encodes on theoretical model, i.e. the particles, their masses, their branchings.
    """
    LSP = 1000022
    def __init__ ( self ):
        self.maxMass = 2400. ## maximum masses we consider
        self.step = 0 ## count the steps
        self.particles = [ 1000001, 2000001, 1000002, 2000002, 1000003, 2000003,
                  1000004, 2000004, 1000005, 2000005, 1000006, 2000006, 1000011,
                  2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015,
                  1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024,
                  1000037 ]
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
        self.onesquark = True ## only one light squark
        if self.onesquark:
            self.particles = [ 1000001, 1000005, 1000006, 1000011, 1000012,
                      1000013, 1000014, 1000015,  1000016, 1000021, 1000022,
                      1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "template_1q.slha"
        self.possibledecays = {} ## list all possible decay channels
        self.decays = {} ## the actual branchings
        self.masses = {}
        self.llhd=0.
        self.Z = 0.

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
                    if dpid == Model.LSP:
                        self.decays[p][dpid]=1.
            self.possibledecays[p]=decays

        ## the LSP we need from the beginning
        self.masses[Model.LSP]=random.uniform(50,500)
        self.computePrior()

    def pprint ( self, *args ):
        """ logging """
        print ( "[model] %s" % (" ".join(map(str,args))) )

    def frozenParticles ( self ):
        """ returns a list of all particles that can be regarded as frozen
            (ie mass greater than 1e5 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)>1e5:
                ret.append(m)
        return ret

    def priorTimesLlhd( self ):
        return self.prior * self.llhd

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
        self.masses[p]=random.uniform ( self.masses[Model.LSP], self.maxMass )
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
        unfrozen.remove ( Model.LSP )
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
        unfrozenparticles.remove ( Model.LSP )
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
            tmp = self.masses[i]+random.uniform(-dx,dx)
            if tmp > self.maxMass:
                tmp = self.maxMass
            if tmp < 10.:
                tmp = 10.
            self.masses[i]=tmp

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

class RandomWalker:
    def __init__ ( self, nsteps=500, strategy="aggressive", hiscore=False ):
        """ initialise the walker
        :param nsteps: maximum number of steps to perform
        """
        self.model = Model()
        self.strategy = strategy
        self.hiscoreList = Hiscore( hiscore )
        self.maxsteps = nsteps
        self.takeStep() ## the first step should be considered as "taken"

    def removeDataFromBestCombo ( self, bestCombo ):
        """ remove the data from all theory predictions, we dont need them. """
        for combo in bestCombo:
            eR = combo.expResult
            for ds in eR.datasets:
                for tx in ds.txnameList:
                    del tx.txnameData
        return bestCombo


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
        self.model.step+=1
        nUnfrozen = len ( self.model.unFrozenParticles() )
        nTotal = len ( self.model.masses.keys() )
        self.pprint ( "Step %d has %d/%d unfrozen particles: %s" % ( self.model.step, nUnfrozen, nTotal, ", ".join ( map ( self.model.getParticleName, self.model.unFrozenParticles() ) ) ) )
        # uUnfreeze = random.uniform(0,1)
        nChanges = 0
        uUnfreeze = random.gauss(.5,.5)
        if uUnfreeze > nUnfrozen/float(nTotal):
            # in about every tenth step unfreeze random particle
            nChanges += self.model.unfreezeRandomParticle()
        uBranch = random.uniform(0,1)
        if uBranch > .75:
            nChanges += self.model.randomlyChangeBranchings()
        # uFreeze = random.uniform(0,1)
        uFreeze = random.gauss(.5,.5)
        if uFreeze < nUnfrozen/float(nTotal):
            # in about every tenth step randomly change branchings of a particle
            nChanges+=self.model.freezeRandomParticle()
        if nChanges == 0:
            self.model.takeRandomMassStep()
        self.model.createSLHAFile()
        self.model.computeXSecs()
        predictions = predict ( self.model.currentSLHA )
        # self.pprint ( "I got %d predictions" % ( len(predictions) ) )
        combiner = Combiner()
        bestCombo,Z,llhd = combiner.findHighestSignificance ( predictions, self.strategy )
        self.model.bestCombo = self.removeDataFromBestCombo ( bestCombo )
        self.model.llhd = (1. - llhd ) ## we wish to minimize likelihood, find the most unexpected fluctuation
        self.model.Z = Z
        self.hiscoreList.newResult ( self.model ) ## add to high score list
        self.model.computePrior()
        self.pprint ( "best combo for strategy ``%s'' is %s: %s: [Z=%.2f]" % ( self.strategy, combiner.getLetterCode(bestCombo), combiner.getComboDescription(bestCombo), Z ) )

    def revert ( self ):
        """ revert the last step. go back. """
        self.model = copy.deepcopy ( self.oldmodel )

    def takeStep ( self ):
        """ take the step, save it as last step """
        self.oldmodel = copy.deepcopy ( self.model )

    def saveState ( self ):
        """ write out current state, for later retrieval """
        f=open("state.pcl","wb")
        pickle.dump ( self, f )
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
                self.pprint ( "Z=%.2f -> 0. Revert." % self.oldmodel.Z )
                self.revert()
                continue

            if ratio >= 1.:
                self.pprint ( "Z: %.3f -> %.3f: take the step" % ( self.oldmodel.Z, self.model.Z ) )
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
            help='number of steps [500]',
            type=int, default=500 )
    argparser.add_argument ( '-p', '--ncpus',
            help='number of CPUs. -1 means all. [1]',
            type=int, default=1 )
    argparser.add_argument ( '-c', '--cont',
            help='continue with last save state [False]',
            action="store_true" )
    #argparser.add_argument ( '-S', '--hiscore',
    #        help='save states with highest Zs [False]',
    #        action="store_true" )
    args = argparser.parse_args()
    ncpus = args.ncpus
    if ncpus < 0:
        ncpus = nCPUs() + ncpus + 1
    if args.cont and os.path.exists ( "state.pcl" ) and os.stat("state.pcl").st_size > 100:
        f=open("state.pcl","rb")
        walker = pickle.load ( f )
        f.close()
    else:
        walker = RandomWalker( args.nsteps, args.strategy, True )
    if ncpus == 1:
        walker.walk()
    else:
        walkers = []
        for w in range(ncpus):
            walkers.append ( copy.deepcopy ( walker ) )
        p = multiprocessing.Pool ( ncpus )

        p.map ( _run, walkers ) 
