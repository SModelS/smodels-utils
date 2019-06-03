#!/usr/bin/env python3

""" Class that encapsulates a BSM model. """

import random, numpy, tempfile, os, copy, time, sys, colorama
from smodels.tools.xsecComputer import XSecComputer, LO
from combiner import Combiner
from predictor import Predictor
import helpers

class Model:
    """ encodes one theoretical model, i.e. the particles, their masses, their
        branchings, their signal strength modifiers.
    """
    LSP = 1000022 ## the LSP is hard coded
    def __init__ ( self, walkerid ):
        self.walkerid = walkerid
        self.version = 1 ## version of this class
        self.maxMass = 2400. ## maximum masses we consider
        self.predictor = Predictor( walkerid )
        self.step = 0 ## count the steps
        self.particles = [ 1000001, 2000001, 1000002, 2000002, 1000003, 2000003,
                  1000004, 2000004, 1000005, 2000005, 1000006, 2000006, 1000011,
                  2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015,
                  1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024,
                  1000037 ]
        self.onesquark = False ## only one light squark
        self.twosquark = False  ## a few squarks, but not all
        self.manysquark = True ## many squarks
        if self.onesquark:
            self.particles = [ 1000001, 1000005, 1000006, 1000011, 1000012,
                      1000013, 1000014, 1000015,  1000016, 1000021, 1000022,
                      1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "template_1q.slha"
        if self.twosquark:
            self.particles = [ 1000001, 1000002, 1000004, 1000005, 1000006, 1000011, 
                      1000012, 1000013, 1000014, 1000015, 1000016, 1000021, 1000022,
                      1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "template_2q.slha"
        if self.manysquark:
            self.particles = [ 1000001, 1000002, 1000003, 1000004, 1000005, 1000006, 
                      2000005, 2000006, 1000011, 1000012, 1000013, 1000014, 1000015, 
                      1000016, 1000021, 1000022, 1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "template_many.slha"
        self.possibledecays = {} ## list all possible decay channels
        self.decays = {} ## the actual branchings
        self.masses = {}
        self.ssmultipliers = {} ## signal strength multipliers
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
            self.ssmultipliers[p]=1. ## signal strength multipliers
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
        if False: # cheat, to get a head start
            self.masses[1000006]=random.uniform(500,900)
            self.masses[1000002]=random.uniform(800,1200)
            self.masses[1000024]=random.uniform(500,1000)
        self.computePrior()

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[model:%d - %s] %s%s" % ( col, self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)), colorama.Fore.RESET ) )

    def pprint ( self, *args ):
        """ logging """
        print ( "[model:%d] %s" % (self.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        f=open( "walker%d.log" % self.walkerid, "a" )
        f.write ( "[model:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )
        f.close()

    def frozenParticles ( self ):
        """ returns a list of all particles that can be regarded as frozen
            (ie mass greater than 1e5 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)>1e5:
                ret.append(m)
        return ret

    def clean ( self ):
        """ remove unneeded stuff before storing """
        combiner = Combiner( self.walkerid )
        self.bestCombo = combiner.removeDataFromBestCombo ( self.bestCombo )
        if hasattr ( self, "_backup" ):
            del self._backup
        if hasattr ( self, "predictor" ):
            del self.predictor

    def predict ( self, strategy ):
        """ compute best combo, llhd, and significance """
        # if not os.path.exists ( self.currentSLHA ):
        self.createSLHAFile()
        # get the predictions that determine whether model is excluded:
        # best results only, also non-likelihood results
        self.log ( "check if excluded" )
        if not hasattr ( self, "predictor" ):
            self.predictor = Predictor ( self.walkerid )
        bestpreds = self.predictor.predict ( self.currentSLHA, allpreds=False, 
                                             llhdonly=False )
        self.log ( "received best preds" )
        excluded = self.checkForExcluded ( bestpreds )
        self.log ( "model is excluded? %s" % str(excluded) )
        if excluded:
            return
        # now get the predictions that determine the Z of the model. allpreds,
        # but need llhd
        predictions = self.predictor.predict ( self.currentSLHA, allpreds=True, llhdonly=True )
        combiner = Combiner( self.walkerid )
        self.log ( "now find highest significance for %d predictions" % len(predictions) )
        bestCombo,Z,llhd = combiner.findHighestSignificance ( predictions, strategy )
        self.bestCombo = bestCombo # combiner.removeDataFromBestCombo ( bestCombo )
        self.Z = Z
        self.llhd = llhd
        self.letters = combiner.getLetterCode(self.bestCombo)
        self.description = combiner.getComboDescription(self.bestCombo)
        self.log ( "done with prediction. best Z=%.2f." % self.Z )

    def checkForExcluded ( self, predictions ):
        """ check if any of the predictions excludes the point """
        for theorypred in predictions:
            r = theorypred.getRValue(expected=False)
            rexp = theorypred.getRValue(expected=True)
            if r == None:
                self.pprint ( "I received %s as r. What do I do with this?" % r )
                r = 2.
            if r > 1.5:
                self.pprint ( "analysis %s:%s excludes the model. r=%.1f (r_exp=%s)" % ( theorypred.analysisId(), theorypred.dataId(), r, rexp ) )
                self.Z = 0.
                self.llhd = 0.
                self.letters = "excluded"
                self.description = "excluded"
                return True
        self.pprint ( "check if excluded, %d predictions: no" % len(predictions) )
        return False

    def backup ( self ):
        """ backup the current state """
        self._backup = { "llhd": self.llhd, "letters": self.letters, "Z": self.Z,
                        "prior": self.prior, "description": self.description,
                        "bestCombo": self.bestCombo, "masses": self.masses }
        self.pprint ( "backing up state" )

    def restore ( self ):
        """ restore from the backup """
        if not hasattr ( self, "_backup" ):
            raise Exception ( "no backup available" )
        for k,v in self._backup.items():
            setattr ( self, k, v )

    def priorTimesLlhd( self ):
        return self.prior * self.llhd

    def unFrozenParticles ( self, withLSP=True ):
        """ returns a list of all particles that can be regarded as unfrozen
            (ie mass less than 5e3 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)<5e3:
                ret.append(m)
        if not withLSP:
            ret.remove(self.LSP)
        return ret

    def unfreezeRandomParticle ( self ):
        """ unfreezes a random frozen particle """
        frozen = self.frozenParticles()
        if len(frozen)==0:
            return 0
        p = random.choice ( frozen )
        self.masses[p]=random.uniform ( self.masses[Model.LSP], self.maxMass )
        self.normalizeAllBranchings() ## adjust everything
        self.pprint ( "Unfreezing %s: m=%f" % ( helpers.getParticleName(p), self.masses[p] ) )
        return 1

    def normalizeBranchings ( self, pid ):
        """ normalize branchings of a particle, after freezing and unfreezing
            particles """
        # unfrozen = self.unFrozenParticles( withLSP = False )
        S=0.
        for dpid,br in self.decays[pid].items():
            S+=br
            #if dpid in unfrozen:
            #    S+=br
            #else:
            #    self.decays[pid][dpid]=0.
        if S == 0.:
            return ## happens when never been unfrozen, I think
            self.pprint ( "total sum of branchings for %d is %.2f!!" % (pid,S) )
        for dpid,br in self.decays[pid].items():
                tmp = self.decays[pid][dpid]
                self.decays[pid][dpid] = tmp / S

        ## adjust the signal strength multipliers to keep everything else
        ## as it was
        if pid in self.ssmultipliers.keys():
            t = self.ssmultipliers[pid]
            if t == 0.:
                self.pprint ( "huh, when normalizing we find ssmultipliers of 0? change to 1! S=%.4g" % S )
                t=1.
            self.ssmultipliers[pid]=t*S

    def normalizeAllBranchings ( self ):
        """ normalize all branchings, after freezing or unfreezing particles """
        for pid in self.masses.keys():
            if not pid == self.LSP:
                self.normalizeBranchings ( pid )

    def freezeRandomParticle ( self ):
        """ freezes a random unfrozen particle """
        unfrozen = self.unFrozenParticles( withLSP = False )
        if len(unfrozen)<2:
            return 0 ## freeze only if at least 3 unfrozen particles exist
        p = random.choice ( unfrozen )
        self.masses[p]=1e6
        self.normalizeAllBranchings() ## adjust everything
        self.pprint ( "Freezing %s (keep branchings)." % ( helpers.getParticleName(p) ) )
        return 1

    def freezeMostMassiveParticle ( self ):
        """ freezes the most massive unfrozen particle """
        unfrozen = self.unFrozenParticles( withLSP=False )
        if len(unfrozen)<2:
            return 0 ## freeze only if at least 3 unfrozen particles exist
        pid,minmass=0,0
        for i in unfrozen:
            if self.masses[i]>minmass:
                minmass = self.masses[i]
                pid = i
        # p = random.choice ( unfrozen )
        self.masses[pid]=1e6
        self.normalizeAllBranchings() ## adjust everything
        self.pprint ( "Freezing most massive %s (%.1f)" % ( helpers.getParticleName(pid), minmass ) )
        return 1

    def randomlyChangeSignalStrengths ( self ):
        """ randomly change one of the signal strengths """
        unfrozenparticles = self.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.pprint ( "not enough unfrozen particles to change random signal strength" )
            return 0
        p = random.choice ( unfrozenparticles )
        newSSM=self.ssmultipliers[p]*random.gauss(1.,.1)
        if newSSM == 0.:
            self.pprint ( "Huh? ssmultiplier is 0?? Change to 1." )
            newSSM = 1.
        self.ssmultipliers[p]=newSSM
        self.pprint ( "changed signal strength multiplier of %s: %.2f." % (helpers.getParticleName(p), newSSM ) )
        return 1

    def randomlyChangeBranchings ( self ):
        """ randomly change the branchings of a single particle """
        unfrozenparticles = self.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.pprint ( "not enough unfrozen particles to change random branching" )
            return 0
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
        for i in self.decays[p].keys(): ## openChannels[:-1]:
            oldbr = self.decays[p][i]
            Min,Max = max(0.,oldbr-dx), min(oldbr+dx,1.)
            br = random.uniform ( Min, Max )
            #br = oldbr+random.uniform(-dx,dx)
            #if br < 0.: br = 0.
            #if br > 1.: br = 1.
            self.decays[p][i]=br
            S+=br
        if True: # S > 1.: ## correct for too large sums
            for i,v in self.decays[p].items():
                self.decays[p][i] = v / S
            S = 1.
        #for i in self.frozenParticles(): ## frozen particles have 0 branchings
        #    self.decays[p][i]=0.
        # self.decays[p][ self.decays[p][-1] ] = 1. - S
        #self.decays[p][ openChannels[-1] ] = 1. - S
        control = sum ( [  x for x in self.decays[p].values() ] )
        if abs ( control - 1.0 ) > 1e-5:
            self.pprint ( "control %s" % control )
        #    sys.exit()
        brvec=[]
        for x in self.decays[p].values():
            if x<1e-5:
                brvec.append("")
            else:
                brvec.append("%.2f" % x )
        self.pprint ( "changed branchings of %s: %s: s=%.2f" % (helpers.getParticleName(p), ",".join( brvec  ), control ) )
        return 1

    def takeRandomMassStep ( self ):
        """ take a random step in mass space for all unfrozen particles """
        dx = 40. / numpy.sqrt ( len(self.unFrozenParticles() ) ) / ( self.Z + 1. )
        for i in self.unFrozenParticles():
            tmp = self.masses[i]+random.uniform(-dx,dx)
            if tmp > self.maxMass:
                tmp = self.maxMass
            if tmp < self.masses[self.LSP]: ## the LSP is the LSP.
                tmp = self.masses[self.LSP]
            self.masses[i]=tmp
        for squark in [ 1, 2, 3, 4, 5, 6 ]:
            sq1,sq2=1000000+squark,2000000+squark
            if not sq1 in self.masses or not sq2 in self.masses:
                continue
            msq1,msq2 = self.masses[sq1], self.masses[sq2]
            if msq2 < msq1:
            ### sq1 should always be lighter than sq2
             self.masses[sq2]=msq1
             self.masses[sq1]=msq2
        if 1000023 in self.masses and 1000025 in self.masses:
            mchi20 = self.masses[1000023]
            mchi30 = self.masses[1000025]
            if mchi20 > mchi30:
                self.masses[1000023] = mchi30
                self.masses[1000025] = mchi20

    def createNewSLHAFileName ( self ):
        """ create a new SLHA file name. Needed when e.g. unpickling """
        self.currentSLHA = tempfile.mktemp(prefix=".cur",suffix=".slha",dir="./")

    def createSLHAFile ( self, outputSLHA=None ):
        """ from the template.slha file, create the slha file of the current
            model.
        :param outputSLHA: if not None, write into that file. else, write into
            currentSLHA file.
        """
        f=open( self.templateSLHA )
        lines=f.readlines()
        f.close()
        if not hasattr ( self, "currentSLHA" ):
            self.createNewSLHAFileName()
        if outputSLHA == None:
            outputSLHA = self.currentSLHA
        self.pprint ( "create %s from %s" % (outputSLHA, self.templateSLHA ) )
        f=open(outputSLHA,"w")
        for line in lines:
            for m,v in self.masses.items():
                line=line.replace("M%d" % m,"%.1f" % v )
                for dpid,dbr in self.decays[m].items():
                    line=line.replace("D%d_%d" % ( m, dpid), "%.5f" % dbr )
                D_ = "D%d_" % m 
                if D_ in line and not line[0]=="#":
                    p1= line.find(D_)
                    p2 = line[p1+1:].find(" ")
                    print ( "remaining token: %s: set to zero." % line[p1:p1+p2+1] )
                    line=line.replace( line[p1:p1+p2+1], "0." )
            f.write ( line )
        f.close()
        self.computeXSecs()

    def computeXSecs ( self ):
        """ compute xsecs for current.slha """
        self.log ( "computing xsecs" )
        # print ( "[walk] computing xsecs for %s" % self.currentSLHA )
        computer = XSecComputer ( LO, 2000, 6 )
        computer.computeForOneFile ( [8,13], self.currentSLHA,
                unlink=True, lOfromSLHA=False, tofile=True,
                ssmultipliers  = self.ssmultipliers )
        self.log ( "done computing xsecs" )

    def computePrior ( self ):
        """ compute the prior for the current model.
        """
        self.prior = 1. / ( len(self.unFrozenParticles()))

