#!/usr/bin/env python3

""" Class that encapsulates a BSM model. """

import random, numpy, tempfile, os, copy, time, sys, colorama
from smodels.tools.xsecComputer import XSecComputer, LO
from combiner import Combiner
from predictor import Predictor
import pyslha
import helpers
from pympler.asizeof import asizeof

## the thresholds for exclusion
rthresholds = (1.7,)

predictor = [ None ]

class ProtoModel:
    """ encodes one theoretical model, i.e. the particles, their masses, their
        branchings, their signal strength modifiers.
    """
    LSP = 1000022 ## the LSP is hard coded
    def hasAntiParticle ( self, pid ):
        """ for a given pid, do i also have to consider its antiparticle
            -pid in the signal strength multipliers? """
        if pid in [ 1000021, 1000022, 1000023, 1000025, 1000035, 1000012, 
                    1000014, 1000016, 2000012, 2000014, 2000016 ]:
            return False
        return True

    def toTuple ( self, pid1, pid2 ):
        """ turn pid1, pid2 into a sorted tuple """
        a=[pid1,pid2]
        a.sort()
        return tuple(a)

    def __init__ ( self, walkerid, cheat=0, dbpath="../../smodels-database/",
                   expected = False, select = "all", keep_meta = True ):
        """
        :param expected: if True, run with observations drawn from expected values 
        """
        self.walkerid = walkerid
        self.expected = expected
        self.select = select
        self.keep_meta = keep_meta ## keep all meta info? big!
        self.dbpath = dbpath
        self.version = 1 ## version of this class
        self.maxMass = 2400. ## maximum masses we consider
        self.initializePredictor()
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
            # self.templateSLHA = "template.slha"
            self.templateSLHA = "template_many.slha"
        self.templateSLHA = os.path.join ( os.path.dirname ( __file__ ), self.templateSLHA )
        self.possibledecays = {} ## list all possible decay channels
        self.decays = {} ## the actual branchings
        self.masses = {}
        self.ssmultipliers = {} ## signal strength multipliers
        self.rvalues = [] ## store the r values of the exclusion attempt
        self.llhd=0.
        self.muhat = 1.
        self.Z = 0.
        self.rmax = 0.
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
            for q in self.particles:
                self.ssmultipliers[ self.toTuple(p,q) ]=1. ## signal strength multipliers
                if self.hasAntiParticle ( q ):
                    self.ssmultipliers[ self.toTuple(p,-q) ]=1.
            if self.hasAntiParticle ( p ):
                for q in self.particles:
                    self.ssmultipliers[ self.toTuple(-p,q) ]=1. ## signal strength multipliers
                    if self.hasAntiParticle ( q ):
                        self.ssmultipliers[ self.toTuple ( -p, -q ) ]=1.
            decays = []
            self.decays[p]={}
            for line in slhalines:
                if "D%s" % p in line:
                    _ = line.find("_")+1
                    dpid = int ( line[_:] )
                    decays.append ( dpid )
                    self.decays[p][dpid]=0.
                    if dpid == ProtoModel.LSP:
                        self.decays[p][dpid]=1.
            self.possibledecays[p]=decays

        ## the LSP we need from the beginning
        self.masses[ProtoModel.LSP]=random.uniform(250,500)
        if cheat>0: # True: # cheat, to get a head start
            if cheat == 1:
                self.highlight ( "red", "cheat mode (1), start with stop, sbottom, sup." )
                self.masses[1000006]=random.uniform(700,900)
                self.masses[1000005]=random.uniform(500,700)
                self.masses[1000002]=random.uniform(800,1200)
                # self.masses[1000024]=random.uniform(500,1000)
            if cheat == 2:
                self.highlight ( "red", "cheat mode (2), start with Z=2.82 point (roughly)." )
                self.masses[1000005]=1100.
                self.masses[1000001]=1070.
                self.masses[1000002]=920.
                self.masses[1000006]=830.
                self.masses[1000004]=450.
                self.masses[1000022]=410.
                self.ssmultipliers[(1000005,1000005)]=1.
                # self.masses[1000024]=random.uniform(500,1000)
            if cheat == 3:
                self.highlight ( "red", "cheat mode (3), start with Z=3.25 point (roughly)." )
                self.masses[1000001]=1070.
                self.masses[1000002]=920.
                self.masses[1000006]=830.
                self.masses[1000005]=600.
                self.masses[1000004]=440.
                self.masses[1000022]=375.
                self.ssmultipliers[(1000001,1000001)]=1.0
        self.computePrior()

    def checkForOffshell ( self ):
        """ check for offshell decays
        :returns: a list of tuples (motherpid, daughterpid) """
        offshell = []
        for pid,decays in self.decays.items():
            mmother = self.masses[pid]
            if mmother > 9e5:
                continue
            for dpid,dbr in decays.items():
                mdaughter = 1e+6
                if dpid in self.masses:
                    mdaughter = self.masses[dpid]
                if mdaughter > mmother and dbr > 1e-5:
                    self.log ( "decay %d -> %d is offshell (%.3f)" % \
                               ( pid, dpid, dbr ) )
                    offshell.append ( ( pid, dpid ) )
        return offshell

    def removeAllOffshell ( self ):
        """ remove all offshell decays, renormalize all branchings """
        offshell = self.checkForOffshell()
        for (mpid,dpid) in offshell:
            assert ( mpid in self.decays )
            assert ( dpid in self.decays[mpid] )
            self.decays[mpid][dpid]=0.
            # self.decays[mpid].pop ( dpid ) dont pop, we need it!
        self.normalizeAllBranchings()

    def checkSwaps ( self ):
        """ check for the usual suspects for particle swaps """
        ## the pairs to check. I put 1000023, 1000025 twice, 
        ## so as to make it possible that chi40 eventually swaps with chi20
        pairs = [ ( 1000006, 2000006 ), ( 1000005, 2000005 ),
                  ( 1000023, 1000025 ), ( 1000024, 1000037 ),
                  ( 1000025, 1000035 ), ( 1000023, 1000025 ) ]
        for pids in pairs:
            if not pids[1] in self.masses or not pids[0] in self.masses:
                continue
            if self.masses[pids[1]] > 9e4:
                # we dont check for frozen particles
                continue
            #if self.masses[pids[0]] > 9e4:
                # we dont check for frozen particles
            #    continue
            if self.masses[pids[0]] > self.masses[pids[1]]:
                self.pprint ( "particle swap %d <-> %d" % ( pids[0], pids[1] ) )
                self.swapParticles ( pids[0],pids[1] )

    def swapParticles ( self, pid1, pid2 ):
        """ swaps the two particle ids. The idea being that e.g. ~b1 should be
            lighter than ~b2. If in the walk, ~b1 > ~b2, we just swap the roles 
            of the two particles. """
        ## swap in the masses dictionary
        if pid1 in self.masses and pid2 in self.masses:
            s = self.masses[pid1]
            self.masses[pid1] = self.masses[pid2]
            self.masses[pid2] = s
        else:
            self.highlight ( "red", "error, i was asked to swap %d and %d. but one of them isnt in the mass tuple" % ( pid1, pid2 ) )
            return
        ## swap mothers in the decays dictionary
        if pid1 in self.decays and pid2 in self.decays:
            s = self.decays[pid1]
            self.decays[pid1] = self.decays[pid2]
            self.decays[pid2] = s
        else:
            self.highlight ( "red", "error, i was asked to swap %d and %d. but one of them isnt in the decays tuple" % ( pid1, pid2 ) )
            return

        # swap the daughters in the decays dictionary
        for mpid,decays in self.decays.items():
            if pid1 in decays and pid2 in decays: ## a swap!
                s = self.decays[mpid][pid1]
                self.decays[mpid][pid1] = self.decays[mpid][pid2]
                self.decays[mpid][pid2] = s
                continue
            if pid1 in decays and not pid2 in decays: ## just a rename
                self.decays[mpid][pid2]=copy.deepcopy( self.decays[mpid][pid1] )
                self.decays[mpid].pop(pid1)
                continue
            if pid2 in decays and not pid1 in decays: ## just a rename
                self.decays[mpid][pid1]=copy.deepcopy( self.decays[mpid][pid2] )
                self.decays[mpid].pop(pid2)
        ## swap all provenances in the ss multiplier dictionary
        newSSMultipliers = {}
        for pids,ssm in self.ssmultipliers.items():
            apids = list ( map ( abs, pids ) )
            if not pid1 in apids and not pid2 in apids:
                newSSMultipliers[pids]=ssm ## our swapping pids are not part
                continue
            npids = list ( pids )
            for ctr,pid in enumerate(npids):
                if pid == pid1:
                    npids[ctr]=pid2
                if pid == -pid1:
                    npids[ctr]=-pid2
                if pid == pid2:
                    npids[ctr]=pid1
                if pid == -pid2:
                    npids[ctr]=-pid1
            npids.sort()
            newSSMultipliers[tuple(npids)]=ssm
        self.ssmultipliers = newSSMultipliers


        
                


    def initializePredictor ( self ):
        """ initialize the predictor """
        self.pprint ( "initializing predictor #%d with database at %s" % ( self.walkerid, self.dbpath ) )
        if predictor [ 0 ] == None:
            predictor[0] = Predictor( self.walkerid, dbpath=self.dbpath, 
                                    expected=self.expected, select=self.select )
        self.dbversion = predictor[0].database.databaseVersion

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        if msgType.lower() in [ "error", "red" ]:
            col = colorama.Fore.RED
        elif msgType.lower() in [ "warn", "warning", "yellow" ]:
            col = colorama.Fore.YELLOW
        else:
            self.highlight ( "red", "i think we called highlight without msg type" )
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
        if all and hasattr ( self, "_backup" ):
            del self._backup
        if hasattr ( self, "keep_meta" ) and self.keep_meta:
            return ## dont remove best combo
        combiner = Combiner( self.walkerid )
        if hasattr ( self, "bestCombo" ) and self.bestCombo != None:
            self.bestCombo = combiner.removeDataFromBestCombo ( self.bestCombo )
        #if hasattr ( self, "predictor" ):
        #    del self.predictor

    def predict ( self, strategy = "aggressive", nevents = 10000,
                  check_thresholds = True ):
        """ compute best combo, llhd, and significance 
        :param rthres 
        :returns: False, if not prediction (e.g. because the model is excluded), 
                  True if prediction was possible
        """
        if predictor[0] == None:
            self.initializePredictor()
        # if not os.path.exists ( self.currentSLHA ):
        self.createSLHAFile( nevents = nevents )
        # get the predictions that determine whether model is excluded:
        # best results only, also non-likelihood results
        #if not hasattr ( self, "predictor" ):
        #    self.predictor = Predictor ( self.walkerid, dbpath = self.dbpath )
        # bestpreds = self.predictor.predict ( self.currentSLHA, allpreds=False,
        bestpreds = predictor[0].predict ( self.currentSLHA, allpreds=False,
                                             llhdonly=False )
        rs = self.checkForExcluded ( bestpreds )
        srs = "%s" % ", ".join ( [ "%.2f" % x for x in rs[:3] ] )
        self.log ( "received r values %s" % srs )
        self.nevents = nevents
        self.rmax = 0.
        self.r2 = 0.
        if len(rs)>0:
            self.rmax = rs[0]
        if len(rs)>1:
            self.r2 = rs[1]
        excluded = self.rmax > rthresholds[0]
        self.log ( "model is excluded? %s" % str(excluded) )
        if check_thresholds and excluded:
            return False
        if not check_thresholds  and excluded:
            self.pprint ( "we dont check thresholds, but the model would actually be excluded with rmax=%.2f" % self.rmax )
        # now get the predictions that determine the Z of the model. allpreds,
        # but need llhd
        #predictions = self.predictor.predict ( self.currentSLHA, allpreds=False,
        predictions = predictor[0].predict ( self.currentSLHA, allpreds=False,
                                               llhdonly=True )
        combiner = Combiner( self.walkerid )
        self.log ( "now find highest significance for %d predictions" % len(predictions) )
        ## find highest observed significance
        mumax = float("inf")
        if self.rmax > 0.:
            mumax = rthresholds[0] / self.rmax
        bestCombo,Z,llhd,muhat = combiner.findHighestSignificance ( predictions, strategy, expected=False, mumax = mumax )
        if hasattr ( self, "keep_meta" ) and self.keep_meta:
            self.bestCombo = bestCombo
        else:
            self.bestCombo = combiner.removeDataFromBestCombo ( bestCombo )
        self.Z = Z
        self.llhd = llhd
        self.muhat = muhat
        self.letters = combiner.getLetterCode(self.bestCombo)
        self.description = combiner.getComboDescription(self.bestCombo)
        self.log ( "done with prediction. best Z=%.2f (muhat=%.2f)" % ( self.Z, muhat ) )
        self.clean()
        return True

    def resolveMuhat ( self ):
        """ multiply the signal strength multipliers with muhat, then set muhat to 1. """
        if not hasattr ( self, "muhat" ):
            return
        if self.muhat == 0.:
            self.pprint ( "muhat is exactly zero??? set to one." )
            self.muhat = 1.
        if abs ( self.muhat - 1.0 ) < 1e-5:
            return
        self.pprint ( "resolve the muhat of %.2f" % self.muhat )
        for k,v in self.ssmultipliers.items():
            v = v * self.muhat
        self.muhat = 1.


    def checkForExcluded ( self, predictions ):
        """ check if any of the predictions excludes the point """
        self.log ( "checking %d predictions for exlusion" % len(predictions) )
        self.rvalues=[]
        combiner = Combiner( self.walkerid )
        robs=[]
        for theorypred in predictions:
            r = theorypred.getRValue(expected=False)
            if r == None:
                self.pprint ( "I received %s as r. What do I do with this?" % r )
                r = 23.
            rexp = theorypred.getRValue(expected=True)
            robs.append ( r )
            self.rvalues.append ( (r, rexp, combiner.removeDataFromTheoryPred ( theorypred ) ) )
        self.rvalues.sort ( reverse = True )
        robs.sort(reverse=True)
        return robs

    def almostSameAs ( self, other ):
        """ check if a model is essentially the same as <other> """
        if len ( self.masses.keys() ) != len ( other.masses.keys() ):
            return False
        ## check the masses
        for pid,m in self.masses.items():
            om = other.masses[pid]
            if m == 0.:
                if om == 0.:
                    continue
                else:
                    return False
            if abs ( om - m ) / m > 1e-5:
                return False
        ## now check ssmultipliers
        pidpairs = set ( self.ssmultipliers.keys() )
        pidpairs = pidpairs.union ( set ( other.ssmultipliers.keys() ) )
        for pidpair in pidpairs:
            ss = 1.
            if pidpair in self.ssmultipliers.keys():
                ss = self.ssmultipliers[pidpair]
            os = 1.
            if pidpair in other.ssmultipliers.keys():
                os = other.ssmultipliers[pidpair]
            if ss == 0.:
                if os == 0.:
                    continue
                else:
                    return False
                if abs ( ss - os ) / ss > 1e-6:
                    return False
        ## now check decays
        pids = set ( self.decays.keys() )
        pids = pids.union ( set ( other.decays.keys() ) )
        for pid in pids:
            sdecays, odecays = {}, {}
            if pid in self.decays:
                sdecays = self.decays[pid]
            if pid in other.decays:
                odecays = other.decays[pid]
            dpids = set ( sdecays.keys() )
            dpid = dpids.union ( set ( odecays.keys() ) )
            for dpid in dpids:
                sbr, obr = 0., 0.
                if dpid in sdecays:
                    sbr = sdecays[dpid]
                if dpid in odecays:
                    obr = odecays[dpid]
                if sbr == 0.:
                    if obr < 1e-6:
                        continue
                    else:
                        return False
                if abs ( sbr - obr ) / sbr > 1e-6:
                    return False
        return True

    def backup ( self ):
        """ backup the current state """
        self._backup = { "llhd": self.llhd, "letters": self.letters, "Z": self.Z,
                        "prior": self.prior, "description": self.description,
                        "bestCombo": copy.deepcopy(self.bestCombo), 
                        "masses": copy.deepcopy(self.masses), 
                        "ssmultipliers": copy.deepcopy(self.ssmultipliers), 
                        "decays": copy.deepcopy(self.decays),
                        "rvalues": copy.deepcopy(self.rvalues) }
        if hasattr ( self, "muhat" ):
            self._backup["muhat"]=self.muhat
        if hasattr ( self, "rmax" ):
            self._backup["rmax"]=self.rmax
        # self.pprint ( "backing up state" )

    def restore ( self ):
        """ restore from the backup """
        if not hasattr ( self, "_backup" ):
            raise Exception ( "no backup available" )
        for k,v in self._backup.items():
            setattr ( self, k, v )

    def oldPriorTimesLlhd( self ):
        if not hasattr ( self, "_backup" ):
            self.pprint ( "asked for old prior times llhd, but no backup available" )
            sys.exit(-1)
        return self._backup["llhd"]*self._backup["prior"]

    def oldZ( self ):
        if not hasattr ( self, "_backup" ):
            self.pprint ( "asked for old Z, but no backup available" )
            sys.exit(-1)
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
        if not withLSP and self.LSP in ret:
            ret.remove(self.LSP)
        return ret

    def normalizeBranchings ( self, pid ):
        """ normalize branchings of a particle, after freezing and unfreezing
            particles. while we are at it, remove zero branchings also. """
        # unfrozen = self.unFrozenParticles( withLSP = False )
        S=0.
        if pid in self.decays:
            for dpid,br in self.decays[pid].items():
                S+=br
        if S == 0.:
            return ## happens when never been unfrozen, I think
            self.pprint ( "total sum of branchings for %d is %.2f!!" % (pid,S) )
        for dpid,br in self.decays[pid].items():
                tmp = self.decays[pid][dpid]
                self.decays[pid][dpid] = tmp / S

        # while we are at, remove also the zeroes
        if False: # nah dont, we need the zeroes for bookkeeping!
            for mpid,decays in self.decays.items():
                newdecays = {}
                for dpid,dbr in decays.items():
                    if dbr > 1e-10:
                        newdecays[dpid]=dbr
                self.decays[mpid] = newdecays

        ## remove also mothers with no decays at all
        newDecays = {}
        for mpid,decays in self.decays.items():
            if len(decays)>0:
                newDecays[mpid] = decays
        self.decays = newDecays

        ## adjust the signal strength multipliers to keep everything else
        ## as it was
        ## self.checkSSMultipliers()
        for pidpair,ssm in self.ssmultipliers.items():
            if (pid in pidpair) or (-pid in pidpair):
                if ssm == 0.:
                    self.pprint ( "huh, when normalizing we find ssmultipliers of 0? change to 1! S=%.4g" % S )
                    ssm=1.
                self.ssmultipliers[pidpair]=ssm*S
        self.checkSSMultipliers()

    def checkSSMultipliers ( self ):
        """ 
        remove 1.0s from ss multipliers, they are redundant
        in addition, and only for debugging, 
        try to find out why we have non-pairs as keys 
        """
        for k,v in self.ssmultipliers.items():
            if type(k) != tuple:
                print ( "error, we have %s(%s) as key" % ( k, type(k) ) )
                raise Exception ( "error, we have %s(%s) as key" % ( k, type(k) ) ) 
        newssmults = {}
        for pids,v in self.ssmultipliers.items():
            if abs(v-1.)>1e-10:
                newssmults[pids]=v
        self.ssmultipliers = newssmults

    def normalizeAllBranchings ( self ):
        """ normalize all branchings, after freezing or unfreezing particles """
        for pid in self.masses.keys():
            if not pid == self.LSP:
                self.normalizeBranchings ( pid )

    def createNewSLHAFileName ( self ):
        """ create a new SLHA file name. Needed when e.g. unpickling """
        self.currentSLHA = tempfile.mktemp(prefix=".cur",suffix=".slha",dir="./")

    def checkTemplateSLHA ( self ):
        if not os.path.exists ( self.templateSLHA ):
            if "/mnt/hephy/" in self.templateSLHA:
                trySLHA = self.templateSLHA.replace("/mnt/hephy/pheno/ww/git/smodels-utils/combinations/","./" )
                if os.path.exists ( trySLHA ):
                    self.templateSLHA = trySLHA
                    return

    def printMasses( self ):
        """ convenience function to print masses with particle names """
        particles = []
        for pid,m in self.masses.items():
            if m > 99000:
                continue
            particles.append ( "%s: %d" % (  helpers.getParticleName ( pid ), m ) )
        print ( ", ".join ( particles ) )

    def createSLHAFile ( self, outputSLHA=None, nevents=10000 ):
        """ from the template.slha file, create the slha file of the current
            model.
        :param outputSLHA: if not None, write into that file. else, write into
            currentSLHA file.
        """
        self.checkTemplateSLHA()
        with open( self.templateSLHA ) as f:
            lines=f.readlines()
        if not hasattr ( self, "currentSLHA" ):
            self.createNewSLHAFileName()
        if outputSLHA == None:
            outputSLHA = self.currentSLHA
        self.log ( "create SLHA file at %s" % outputSLHA )
        self.pprint ( "create %s from %s" % (outputSLHA, self.templateSLHA ) )
        with open(outputSLHA,"w") as f:
            for line in lines:
                for m,v in self.masses.items():
                    line=line.replace("M%d" % m,"%.1f" % v )
                    if not m in self.decays:
                        self.highlight ( "red", "could not find %s in decays" % m )
                        ## FIXME what is this???
                        self.decays[m]={ self.LSP: 1.0 }
                    for dpid,dbr in self.decays[m].items():
                        line=line.replace("D%d_%d" % ( m, dpid), "%.5f" % dbr )
                    D_ = "D%d_" % m
                    if D_ in line and not line[0]=="#":
                        p1= line.find(D_)
                        p2 = line[p1+1:].find(" ")
                        if not "D" in line[p1:p1+p2+1]:
                            self.pprint ( "remaining token %s set to zero." % \
                                    line[p1:p1+p2+1] )
                        line=line.replace( line[p1:p1+p2+1], "0." )
                f.write ( line )
        self.computeXSecs( nevents )
        return outputSLHA

    def dict ( self ):
        """ return the dictionary that can be written out """
        return { "masses": self.masses, "ssmultipliers": self.ssmultipliers,
                 "decays": self.decays }

    def computeXSecs ( self, nevents=10000 ):
        """ compute xsecs for current.slha """
        self.log ( "computing xsecs" )
        # print ( "[walk] computing xsecs for %s" % self.currentSLHA )
        computer = XSecComputer ( LO, nevents, 6 )
        try:
            f = pyslha.readSLHAFile ( self.currentSLHA )
            m = f.blocks["MASS"]
        except Exception as e:
            self.pprint ( "could not read SLHA file %s: %s" % ( self.currentSLHA, e ) )
            self.pprint ( "lets restore old state" )
            self.restore()

        try:
            self.checkSSMultipliers()
            computer.computeForOneFile ( [8,13], self.currentSLHA,
                    unlink=True, lOfromSLHA=False, tofile=True,
                    ssmultipliers  = self.ssmultipliers )
            self.log ( "done computing xsecs, size of computer %d" % asizeof(computer) )
        except Exception as e:
            self.pprint ( "could not compute xsecs %s: %s" % ( self.currentSLHA, e ) )
            self.pprint ( "lets restore old state" )
            self.restore()

    def computePrior ( self ):
        """ compute the prior for the current model.
        """
        nunfrozen = len(self.unFrozenParticles())
        if nunfrozen==0:
            self.pprint ( "weird. no unfrozen particles?? %s" % self.masses )
            nunfrozen = 1
        self.prior = 1. / nunfrozen


if __name__ == "__main__":
    p = ProtoModel( 0 )
    p.createSLHAFile()
