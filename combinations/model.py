#!/usr/bin/env python3

""" Class that encapsulates a BSM model. """

import random, numpy, tempfile, os, copy, time, sys, colorama
from smodels.tools.xsecComputer import XSecComputer, LO
from combiner import Combiner
from predictor import Predictor
import helpers
from pympler.asizeof import asizeof

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
        self.rvalues = [] ## store the r values of the exclusion attempt
        self.llhd=0.
        self.Z = 0.
        self.letters = ""
        self.description = ""
        self.prior = 0.
        self.bestCombo = None

        with open ( self.templateSLHA ) as slhaf:
            tmp = slhaf.readlines()
            slhalines = []
            for line in tmp:
                p = line.find("#" )
                if p > -1:
                    line = line[:p]
                if "D" in line and not "DECAY" in line:
                    slhalines.append ( line.strip().split(" ")[0] )

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
        self.masses[Model.LSP]=random.uniform(250,500)
        if True: # cheat, to get a head start
            self.masses[1000006]=random.uniform(700,900)
            self.masses[1000005]=random.uniform(500,700)
            self.masses[1000002]=random.uniform(800,1200)
            # self.masses[1000024]=random.uniform(500,1000)
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
        with open( "walker%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[model:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def frozenParticles ( self ):
        """ returns a list of all particles that can be regarded as frozen
            (ie mass greater than 1e5 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)>1e5:
                ret.append(m)
        return ret

    def clean ( self, all=False ):
        """ remove unneeded stuff before storing """
        combiner = Combiner( self.walkerid )
        if hasattr ( self, "bestCombo" ) and self.bestCombo != None:
            self.bestCombo = combiner.removeDataFromBestCombo ( self.bestCombo )
        if all and hasattr ( self, "_backup" ):
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
        predictions = self.predictor.predict ( self.currentSLHA, allpreds=False,
                                               llhdonly=True )
        combiner = Combiner( self.walkerid )
        self.log ( "now find highest significance for %d predictions" % len(predictions) )
        bestCombo,Z,llhd = combiner.findHighestSignificance ( predictions, strategy )
        self.bestCombo = combiner.removeDataFromBestCombo ( bestCombo )
        self.Z = Z
        self.llhd = llhd
        self.letters = combiner.getLetterCode(self.bestCombo)
        self.description = combiner.getComboDescription(self.bestCombo)
        self.log ( "done with prediction. best Z=%.2f." % self.Z )
        self.clean()

    def checkForExcluded ( self, predictions ):
        """ check if any of the predictions excludes the point """
        self.rvalues=[]
        combiner = Combiner( self.walkerid )
        for theorypred in predictions:
            r = theorypred.getRValue(expected=False)
            rexp = theorypred.getRValue(expected=True)
            self.rvalues.append ( (r, rexp, combiner.removeDataFromTheoryPred ( theorypred ) ) )
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
                        "bestCombo": self.bestCombo, "masses": self.masses, 
                        "rvalues": self.rvalues }
        self.pprint ( "backing up state" )

    def restore ( self ):
        """ restore from the backup """
        if not hasattr ( self, "_backup" ):
            raise Exception ( "no backup available" )
        for k,v in self._backup.items():
            setattr ( self, k, v )

    def oldPriorTimesLlhd( self ):
        if not hasattr ( self, "_backup" ):
            self.pprint ( "asked for old prior times llhd, but no backup available" )
            sys.exit()
        return self._backup["llhd"]*self._backup["prior"]

    def oldZ( self ):
        if not hasattr ( self, "_backup" ):
            self.pprint ( "asked for old Z, but no backup available" )
            sys.exit()
        return self._backup["Z"]

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

    def createNewSLHAFileName ( self ):
        """ create a new SLHA file name. Needed when e.g. unpickling """
        self.currentSLHA = tempfile.mktemp(prefix=".cur",suffix=".slha",dir="./")

    def createSLHAFile ( self, outputSLHA=None ):
        """ from the template.slha file, create the slha file of the current
            model.
        :param outputSLHA: if not None, write into that file. else, write into
            currentSLHA file.
        """
        with open( self.templateSLHA ) as f:
            lines=f.readlines()
        if not hasattr ( self, "currentSLHA" ):
            self.createNewSLHAFileName()
        if outputSLHA == None:
            outputSLHA = self.currentSLHA
        self.pprint ( "create %s from %s" % (outputSLHA, self.templateSLHA ) )
        with open(outputSLHA,"w") as f:
            for line in lines:
                for m,v in self.masses.items():
                    line=line.replace("M%d" % m,"%.1f" % v )
                    if not m in self.decays:
                        self.highlight ( "error: could not find %s in decays" % m )
                        ## FIXME what is this???
                        self.decays[m]={ self.LSP: 1.0 }
                    for dpid,dbr in self.decays[m].items():
                        line=line.replace("D%d_%d" % ( m, dpid), "%.5f" % dbr )
                    D_ = "D%d_" % m
                    if D_ in line and not line[0]=="#":
                        p1= line.find(D_)
                        p2 = line[p1+1:].find(" ")
                        print ( "remaining token: %s: set to zero." % \
                                line[p1:p1+p2+1] )
                        line=line.replace( line[p1:p1+p2+1], "0." )
                f.write ( line )
        self.computeXSecs( )

    def computeXSecs ( self, nevents=2000 ):
        """ compute xsecs for current.slha """
        self.log ( "computing xsecs" )
        # print ( "[walk] computing xsecs for %s" % self.currentSLHA )
        computer = XSecComputer ( LO, nevents, 6 )
        computer.computeForOneFile ( [8,13], self.currentSLHA,
                unlink=True, lOfromSLHA=False, tofile=True,
                ssmultipliers  = self.ssmultipliers )
        self.log ( "done computing xsecs, size of computer %d" % asizeof(computer) )

    def computePrior ( self ):
        """ compute the prior for the current model.
        """
        self.prior = 1. / ( len(self.unFrozenParticles()))

