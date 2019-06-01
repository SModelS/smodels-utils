#!/usr/bin/env python3

""" Class that encapsulates a BSM model. """

import random, numpy, tempfile, os, copy, time, sys, colorama
from smodels.tools.xsecComputer import XSecComputer, LO
from combiner import Combiner
from predictor import predict

class Model:
    """ encodes one theoretical model, i.e. the particles, their masses, their
        branchings, their signal strength modifiers.
    """
    LSP = 1000022 ## the LSP is hard coded
    def __init__ ( self, walkerid ):
        self.walkerid = walkerid
        self.version = 1 ## version of this class
        self.maxMass = 2400. ## maximum masses we consider
        self.step = 0 ## count the steps
        self.particles = [ 1000001, 2000001, 1000002, 2000002, 1000003, 2000003,
                  1000004, 2000004, 1000005, 2000005, 1000006, 2000006, 1000011,
                  2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015,
                  1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024,
                  1000037 ]
        self.names = { 1000001: "~dL", 2000001: "~dR", 1000002: "~uL",
                       2000002: "~uR", 1000003: "~sL", 2000003: "~sR",
                       1000004: "~cL", 2000004: "~cR", 1000005: "~b1",
                       2000005: "~b2", 1000006: "~t1", 2000006: "~t2",
                       1000011: "~eL", 2000011: "~eR", 1000012: "~nu",
                       1000013: "~muL", 2000013: "~muR", 1000014: "~nu",
                       1000015: "~tauL", 2000015: "~tauR", 1000016: "~nu",
                       1000021: "~g", 1000022: "~chi10", 1000023: "~chi20",
                       1000025: "~chi30", 1000035: "~chi40", 1000024: "~chi1+",
                       1000037: "~chi2+" }
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
        ## for now we start with a stop1 at around 700 --
        ## we know this works well.
        self.masses[1000006]=random.uniform(500,900)
        self.masses[1000002]=random.uniform(800,1200)
        self.masses[1000024]=random.uniform(500,1000)
        self.computePrior()

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[model:%d - %s] %s%s" % ( col, self.walkerid, time.asctime(), " ".join(map(str,args)), colorama.Fore.RESET ) )

    def pprint ( self, *args ):
        """ logging """
        print ( "[model:%d] %s" % (self.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        f=open( "walker%d.log" % self.walkerid, "a" )
        f.write ( "[model:%d - %s] %s\n" % ( self.walkerid, time.asctime(), " ".join(map(str,args)) ) )
        f.close()

    def frozenParticles ( self ):
        """ returns a list of all particles that can be regarded as frozen
            (ie mass greater than 1e5 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)>1e5:
                ret.append(m)
        return ret

    def predict ( self, strategy ):
        """ compute best combo, llhd, and significance """
        # if not os.path.exists ( self.currentSLHA ):
        self.createSLHAFile()
        predictions = predict ( self.currentSLHA )
        excluded = self.checkForExcluded ( predictions )
        if excluded:
            return 
        combiner = Combiner( self.walkerid )
        bestCombo,Z,llhd = combiner.findHighestSignificance ( predictions, strategy )
        self.bestCombo = bestCombo # combiner.removeDataFromBestCombo ( bestCombo )
        self.Z = Z
        self.llhd = 1. - llhd
        self.letters = combiner.getLetterCode(self.bestCombo)
        self.description = combiner.getComboDescription(self.bestCombo)
        # return (bestCombo,Z,llhd)

    def checkForExcluded ( self, predictions ):
        """ check if any of the predictions excludes the point """
        for theorypred in predictions:
            r = theorypred.getRValue(expected=False)
            if r > 1.:
                self.pprint ( "analysis %s excludes the model. r=%.1f" % ( theorypred.expResult.globalInfo.id, r ) )
                self.Z = 0.
                self.llhd = 0.
                self.letters = "?"
                self.description = "?"
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
        self.pprint ( "Unfreezing %s: m=%f" % ( self.getParticleName(p), self.masses[p] ) )
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

    def getParticleName ( self, p ):
        sp = str(p)
        if p in self.names:
            sp = self.names[p]
        return sp

    def freezeRandomParticle ( self ):
        """ freezes a random unfrozen particle """
        unfrozen = self.unFrozenParticles( withLSP = False )
        if len(unfrozen)<2:
            return 0 ## freeze only if at least 3 unfrozen particles exist
        p = random.choice ( unfrozen )
        self.masses[p]=1e6
        self.normalizeAllBranchings() ## adjust everything
        self.pprint ( "Freezing %s (keep branchings)." % ( self.getParticleName(p) ) )
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
        self.pprint ( "Freezing most massive %s (%.1f)" % ( self.getParticleName(pid), minmass ) )
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
        self.pprint ( "changed signal strength multiplier of %s: %.2f." % (self.getParticleName(p), newSSM ) )
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
        if S > 1.: ## correct for too large sums
            for i in self.decays[p].keys():
                self.decays[p][i] = self.decays[p][i] / S
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
        self.pprint ( "changed branchings of %s: %s: s=%.2f" % (self.getParticleName(p), ",".join( brvec  ), control ) )
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
                    # print ( "m,d = br", m, dpid, dbr )
                    line=line.replace("D%d_%d" % ( m, dpid), "%.5f" % dbr )
            f.write ( line )
        f.close()
        self.computeXSecs()

    def trim ( self, strategy="aggressive", maxloss=.001 ):
        """ see if you can trim the model, accept losses smaller than maxloss
        on Z.
        """
        unfrozen = self.unFrozenParticles( withLSP=False )
        ndiscarded,ndiscardedBR=0,0
        self.backup()
        oldZ = self.Z
        self.whatif = {} ## save the scores for the non-discarded particles.
        ## aka: what would happen to the score if I removed particle X?
        frozen = self.frozenParticles()
        for pid in frozen:
            ## remove ssmultipliers for frozen particles
            if pid in self.ssmultipliers:
                self.ssmultipliers.pop(pid)
        # unfrozen = [] ## FIXME was only needed for checking branching trimmer
        for cpid,pid in enumerate(unfrozen):
            self.highlight ( "info", "trying to freeze %d/%d: %s (%.1f)" % \
                   ( (cpid+1),len(unfrozen), self.getParticleName(pid), self.masses[pid] ) )
            oldmass = self.masses[pid]
            self.masses[pid]=1e6
            # self.createSLHAFile()
            self.predict ( strategy )
            self.pprint ( "when trying to remove %s, Z changed: %.3f -> %.3f" % ( self.getParticleName(pid), oldZ, self.Z ) )
            if self.Z > (1. - maxloss)*oldZ:
                ndiscarded+=1
                self.pprint ( "discarding #%d: %s" % ( ndiscarded, self.getParticleName(pid) ) )
                if pid in self.ssmultipliers:
                    #popping from multipliers also
                    self.ssmultipliers.pop(pid)
            else:
                self.whatif[pid]=self.Z
                self.pprint ( "not discarding %s" % self.getParticleName(pid) )
                self.masses[pid]=oldmass
                self.restore()
        unfrozen = self.unFrozenParticles( withLSP=False )
        self.pprint ( "now try to trim the branchings of %d particles" % len(unfrozen) )
        # unfrozen = [] ## turn it off
        for cpid,pid in enumerate(unfrozen):
            decays = self.decays[pid]
            self.highlight ( "info", "trying to trim %d/%d branchings of %s" % ( (cpid+1),len(unfrozen),self.getParticleName(pid) ) )
            for dpid,dbr in decays.items():
                if dbr < 1e-5: ## small values set automatically to zero
                    self.decays[pid][dpid]=0. ## correct for it.
                    S = sum ( self.decays[pid].values() )
                    for k,v in self.decays[pid].items():
                        self.decays[pid][k]=v/S
                    continue
                if dbr > 1e-5 and (dbr < .01 or self.masses[dpid]>self.masses[pid]):
                    self.pprint ( "decay %s -> %s (br=%.2f) has small branching or is offshell. Try to take out." % (self.getParticleName(pid),self.getParticleName(dpid),dbr) )
                    oldZ = self.Z
                    self.backup()
                    self.decays[pid][dpid]=0.
                    S = sum ( self.decays[pid].values() )
                    for k,v in self.decays[pid].items():
                        self.decays[pid][k]=v/S
                    # self.createSLHAFile()
                    self.predict ( strategy )
                    if self.Z > (1. - maxloss)*oldZ:
                        dbr = 0.
                        ndiscardedBR+=1
                        self.pprint ( "discarding small BR %s -> %s: %.2f: Z changed %.3f -> %.3f" % ( self.getParticleName(pid),self.getParticleName(dpid), dbr, oldZ, self.Z ) )
                    else:
                        self.pprint ( "not discarding small BR %s -> %s: %.2f Z changed %.3f -> %.3f" % ( self.getParticleName(pid), self.getParticleName(dpid), dbr, oldZ, self.Z ) )
                        self.restore()
                        
        self.pprint ( "froze %d particles. %d/%d particles are still unfrozen. discarded %d branchings." % ( ndiscarded, len(self.unFrozenParticles()),len(self.masses),ndiscardedBR )  )
        if hasattr ( self, "_backup" ):
            del self._backup

    def computeXSecs ( self ):
        """ compute xsecs for current.slha """
        # print ( "[walk] computing xsecs for %s" % self.currentSLHA )
        computer = XSecComputer ( LO, 2000, 6 )
        computer.computeForOneFile ( [8,13], self.currentSLHA,
                unlink=True, lOfromSLHA=False, tofile=True,
                ssmultipliers  = self.ssmultipliers )

    def computePrior ( self ):
        """ compute the prior for the current model.
        """
        self.prior = 1. / ( len(self.unFrozenParticles()))

