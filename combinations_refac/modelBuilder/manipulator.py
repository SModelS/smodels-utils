#!/usr/bin/env python3

""" Class that encapsulates the manipulations we perform on the protomodels,
    so that the protomodel class is a data-centric class, and this one
    an algorithm-centric class. """

""" TODO:
    -) merger, heed the changed particle mass when computing ssm.
"""

from tools import helpers
import copy, random, numpy, time, math, os, sys
from smodels.tools.physicsUnits import fb, TeV
from smodels.theory.crossSection import LO

class Manipulator:
    """ contains the protomodel manipulation algorithms. """
    def __init__ ( self, protomodel, strategy: str = "aggressive",
                   verbose: bool = False ):
        self.M = copy.copy ( protomodel  ) # shallow copy
        self.strategy = strategy
        self.verbose = verbose

    def getClosestPair ( self, pids ):
        """ of <n> PIDs, identify the two that are closest in mass """
        if len(pids)<2:
            return None
        dmin = float("inf")
        pair = (0,0)
        for pid1 in pids:
            for pid2 in pids:
                if pid1 == pid2:
                    continue
                dm = abs ( self.M.masses[pid2] - self.M.masses[pid1] )
                if dm < dmin:
                    dmin = dm
                    pair = ( pid1, pid2 )
        return pair,dmin

    def teleportToHiscore ( self ):
        """ without further ado, discard your current model and start
            fresh with the hiscore model. """
        fname = "states.dict"
        if not os.path.exists ( fname ):
            from tools.csetup import setup
            rundir = setup()
            fname = rundir + "/states.dict"
            if not os.path.exists ( fname ):
                self.pprint ( "could not find states.dict!!" )
                return
        try:
            with open ( fname, "rt" ) as f:
                dicts = eval ( f.read() )
        except (EOFError,SyntaxError,NameError) as e:
            self.pprint ( "when trying to teleport, found %s. cancel teleportation." % e )
            # can happen if it is just being written. in this case dont teleport
            return
        ith = 0
        choices = []
        f = 1
        for i in range(len(dicts)-1,-1,-1):
            choices += [i]*f
            f=f*2
        ith = random.choice ( choices )
        self.pprint ( "teleporting, we have %d dicts" % len(dicts) )
        self.pprint ( "choosing the %dth entry, it has a K of %.2f" % \
                      ( ith, dicts[ith]["K"] ) )
        self.initFromDict ( dicts[ith] )

    def writeDictFile ( self, outfile = "pmodel.py", cleanOut=True,
                        comment = "", appendMode=False ):
        """ write out the dict file to outfile
        :param outfile: output file, but replacing %t with int(time.time())
        :param cleanOut: clean the dictionary from defaults
        :param comment: add a comment field
        :param appendMode: if true, append to file, and add comma after dictionary.
                           if false, overwrite, and no comma at the end.
        """
        if type(self.M) == type(None):
            ## there is nothing to write
            return
        D = copy.deepcopy ( self.M.dict() )
        frozen = self.M.frozenParticles()
        if cleanOut:
            origMasses = self.M.dict()["masses"]
            ## but with a bit of cleaning!
            for k,v in origMasses.items():
                if v > 5e5:
                    D["masses"].pop(k)
                    if k in D["decays"]:
                        D["decays"].pop(k)
                else:
                    D["masses"][k]=round(v,3)
            for k,decays in self.M.dict()["decays"].items():
                for i,v in decays.items():
                    if not k in D["decays"]:
                        continue
                    if not i  in D["decays"][k]:
                        continue
                    if v < 1e-7:
                        D["decays"][k].pop(i)
                    else:
                        D["decays"][k][i]=round(v,3)
            for k,v in self.M.dict()["ssmultipliers"].items():
                ## if any of the pids is frozen, we dont write out
                hasFrozenPid = False
                for pid in k:
                    if abs(pid) in frozen:
                        hasFrozenPid = True
                if hasFrozenPid: #  or abs ( v - 1.) < 1e-5:
                    D["ssmultipliers"].pop(k)
                else:
                    D["ssmultipliers"][k]=round(v,3)
        import time
        D["timestamp"]=time.asctime()
        D["Z"]=round(self.M.Z,3)
        D["K"]=round(self.M.K,3)
        D["step"]=self.M.step
        if len(comment)>0:
            D["comment"]=comment
        fname = outfile.replace("%t", str(int(time.time())) )
        if not appendMode:
            self.M.pprint ( "writing model to %s" % fname )
        mode,comma = "wt",""
        if appendMode:
            mode,comma = "at",","
        with open ( fname, mode ) as f:
            f.write ( "%s%s\n" % (D,comma) )
            f.close()

    def pidInList ( self, pid, lst, signed ):
        """ is pid in lst """
        if signed:
            return pid in lst
        return pid in lst or -pid in lst

    def initFromDict ( self, D, filename="" ):
        """ setup the protomodel from dictionary D.
        :param D: dictionary, as defined in pmodel*.py files.
        :param filename: name of origin. not necessary, only for logging.
        """
        scom = ""
        if "comment" in D:
                scom = ": " + D["comment"]
        self.M.highlight ( "green", "starting with %s/%s%s" % ( os.getcwd(), filename, scom ) )
        for k,v in D["masses"].items():
            self.M.masses[k]=v
        for k,v in D["ssmultipliers"].items():
            self.M.ssmultipliers[k]=v
        for mpid,decays in D["decays"].items():
            if not mpid in self.M.decays:
                self.M.decays[mpid]={}
            for dpid,v in decays.items():
                self.M.decays[mpid][dpid]=v
        if "step" in D: ## keep track of number of steps
            self.M.step = D["step"]
        ## add also the unused SSMs, set them to 1.
        self.M.initializeSSMs ( overwrite = False )
        self.M.delXSecs()

    def cheat ( self, mode = 0 ):
        ## cheating, i.e. starting with models that are known to work well
        if mode == 0: ## no cheating
            return
        filename = "pmodel%d.py" % mode
        if not os.path.exists ( filename ):
            self.M.highlight ( "red", "cheat mode %d started, but no %s/%s found" % ( mode, os.getcwd(), filename ) )
            sys.exit(-1)
        # scom = ""
        with open ( filename, "rt" ) as f:
            m = eval ( f.read() )
        self.initFromDict ( m, filename )

    def pprint ( self, *args ):
        """ logging """
        print ( "[manipulator:%d] %s" % (self.M.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        with open( "walker%d.log" % self.M.walkerid, "a" ) as f:
            f.write ( "[manipulator:%d - %s] %s\n" % ( self.M.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def checkForOffshell ( self ):
        """ check for offshell decays
        :returns: a list of tuples (motherpid, daughterpid) """
        offshell = []
        for pid,decays in self.M.decays.items():
            mmother = self.M.masses[pid]
            if mmother > 9e5:
                continue
            for dpid,dbr in decays.items():
                mdaughter = -1.
                if dpid in self.M.masses:
                    mdaughter = self.M.masses[dpid]
                if type(dpid) == tuple and dpid[0] in self.M.masses:
                    mdaughter = self.M.masses[dpid[0]]
                if mdaughter < 0.:
                    self.M.log ( "this is weird, cannot get mass for dpid %s?" % dpid )
                if mdaughter > mmother and dbr > 1e-5:
                    self.M.log ( "decay %s(%d) -> %s(%d) is offshell (%.3f)" % \
                               ( helpers.getParticleName( pid ), mmother,
                                 helpers.getParticleName ( dpid ), mdaughter, dbr ) )
                    offshell.append ( ( pid, dpid ) )
        return offshell

    def checkSwaps ( self, predictor ):
        """ check for the usual suspects for particle swaps """
        ## the pairs to check. I put 1000023, 1000025 twice,
        ## so as to make it possible that chi40 eventually swaps with chi20
        # self.pprint ( "checking for nan before swap" )
        # self.checkForNans()
        pairs = [ ( 1000006, 2000006 ), ( 1000005, 2000005 ),
                  ( 1000023, 1000025 ), ( 1000024, 1000037 ),
                  ( 1000025, 1000035 ), ( 1000023, 1000025 ) ]
        for pids in pairs:
            if not pids[1] in self.M.masses or not pids[0] in self.M.masses:
                continue
            if self.M.masses[pids[1]] > 5e5:
                # we dont check for frozen particles, if they are second
                continue
            if self.M.masses[pids[0]] > self.M.masses[pids[1]]:
                self.M.pprint ( "particle swap %d <-> %d" % ( pids[0], pids[1] ) )
                self.swapParticles ( pids[0],pids[1] )

        ## now the same with pairs that actually need checking, e.g.
        ## because the xsecs could be affected, or b/c charm
        if not hasattr ( self.M, "K" ):
            return
        #if True:
        #    return
        cpairs = [ ( 1000001, 1000003 ), ( 1000002, 1000004 ), ( 1000001, 1000002 ) ]
        for pids in cpairs:
            if not pids[1] in self.M.masses or not pids[0] in self.M.masses:
                continue
            if self.M.masses[pids[1]] > 5e5:
                # we dont check for frozen particles, if they are second
                continue
            if self.M.masses[pids[0]] < self.M.masses[pids[1]]:
                continue
            self.M.pprint ( "check if we can particle swap %d <-> %d" % ( pids[0], pids[1] ) )
            oldK, oldrmax = self.M.K, self.M.rmax
            self.M.backup()
            self.swapParticles ( pids[0],pids[1] )
            predictor.predict(protomodel=self.M)
            if self.M.K < oldK - 1e-3: ## score deteriorated?
                self.M.pprint ( "new K is %.2f, old was %.2f. restore!" % \
                                ( self.M.K, oldK ) )
                self.M.restore()
            ## score deteriorated?
            if self.M.excluded and self.M.rmax > oldrmax+.0001:
                self.M.pprint ( "new rmax is %.2f, old was %.2f. restore!" % \
                                ( self.M.rmax, oldrmax ) )
                self.M.restore()
        # self.pprint ( "checking for nan after swap" )
        #self.checkForNans()

    def checkForNans ( self ):
        """ check protomodel for NaNs, for debugging only """
        for pid,m in self.M.masses.items():
            if numpy.isnan ( m ):
                self.pprint ( "checking for nans: mass of %d is nan" % pid )

    def get ( self ):
        """ since the shallowcopy business does not work as expected,
        here is a trivial way to overwrite the original protomodel.
        use as: protomodel = manipulator.get()
        """
        return self.M

    def setWalkerId ( self, Id ):
        """ set the walker id of protomodel """
        self.M.walkerid = Id

    def swapParticles ( self, pid1, pid2 ):
        """ swaps the two particle ids. The idea being that e.g. ~b1 should be
            lighter than ~b2. If in the walk, ~b1 > ~b2, we just swap the roles
            of the two particles. Takes care of changing the pids in the ssms, decays,
            and bestCombo.
        """
        ## swap in the masses dictionary
        if pid1 in self.M.masses and pid2 in self.M.masses:
            s = self.M.masses[pid1]
            self.M.masses[pid1] = self.M.masses[pid2]
            self.M.masses[pid2] = s
        else:
            self.M.highlight ( "red", "error, i was asked to swap %d and %d. but one of them isnt in the mass tuple" % ( pid1, pid2 ) )
            return
        ## swap mothers in the decays dictionary
        if pid1 in self.M.decays and pid2 in self.M.decays:
            s = self.M.decays[pid1]
            self.M.decays[pid1] = self.M.decays[pid2]
            self.M.decays[pid2] = s
        else:
            self.M.highlight ( "red", "error, i was asked to swap %d and %d. but one of them isnt in the decays tuple" % ( pid1, pid2 ) )
            return

        # swap the daughters in the decays dictionary
        for mpid,decays in self.M.decays.items():
            if pid1 in decays and pid2 in decays: ## a swap!
                s = self.M.decays[mpid][pid1]
                self.M.decays[mpid][pid1] = self.M.decays[mpid][pid2]
                self.M.decays[mpid][pid2] = s
                continue
            if pid1 in decays and not pid2 in decays: ## just a rename
                self.M.decays[mpid][pid2]=copy.deepcopy( self.M.decays[mpid][pid1] )
                self.M.decays[mpid].pop(pid1)
                continue
            if pid2 in decays and not pid1 in decays: ## just a rename
                self.M.decays[mpid][pid1]=copy.deepcopy( self.M.decays[mpid][pid2] )
                self.M.decays[mpid].pop(pid2)
        ## swap all provenances in the ss multiplier dictionary
        newSSMultipliers = {}
        for pids,ssm in self.M.ssmultipliers.items():
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
        self.M.ssmultipliers = copy.deepcopy ( newSSMultipliers )

        ## finally swap in bestCombo
        self.swapPidsInBestCombo ( pid1, pid2 )
        self.M.delXSecs() ## I dont trust the xsecs anymore now

    def swapPidsInBestCombo ( self, pid1, pid2 ):
        """ swap pid1 with pid2 in best combo """
        if not hasattr ( self.M, "bestCombo" ):
            return
        if self.M.bestCombo == None:
            return

        for c,combo in enumerate(self.M.bestCombo):
            for i,prod in enumerate(combo.PIDs):
                for b,branch in enumerate(prod):
                    for p,pid in enumerate(branch):
                       if pid == pid1:
                            self.M.bestCombo[c].PIDs[i][b][p] = pid2
                       elif pid == -pid1:
                            self.M.bestCombo[c].PIDs[i][b][p] = -pid2
                       if pid == pid2:
                            self.M.bestCombo[c].PIDs[i][b][p] = pid1
                       elif pid == -pid2:
                            self.M.bestCombo[c].PIDs[i][b][p] = -pid1

    def printCombo ( self, combo=None ):
        """ pretty print prediction combos.
            If None, print best combo """
        print ( "best combo:" )
        if combo == None:
            combo = self.M.bestCombo
        for i in combo:
            print ( " `- %s:%s:%s %s" % \
              ( i.analysisId(), i.dataType(True), i.dataId(), "; ".join(map(str,i.PIDs))))

    def removeAllOffshell ( self ):
        """ remove all offshell decays, renormalize all branchings """
        offshell = self.checkForOffshell()
        for dpd in offshell:
            self.M.log ( "removing offshell decay %s" % helpers.getParticleName ( dpd ) )
        for (mpid,dpid) in offshell:
            assert ( mpid in self.M.decays )
            assert ( dpid in self.M.decays[mpid] )
            self.M.decays[mpid][dpid]=0.
            # self.M.decays[mpid].pop ( dpid ) dont pop, we need it!
        self.normalizeAllBranchings()

    def normalizeBranchings ( self, pid, fixSSMs=True ):
        """ normalize branchings of a particle, after freezing and unfreezing
            particles. while we are at it, remove zero branchings also.
        :param fixSSMs: if True, adapt also signal strength multipliers,
                        i.e. multiply them with S < 0. so that sigma x br of
                        the remaining channels stays the same.
        """
        if not pid in self.M.decays:
            self.M.pprint ( "when attempting to normalize: %d not in decays" % pid )
            return
        S=0.
        for dpid,br in self.M.decays[pid].items():
            S+=br
        nitems = len ( self.M.decays[pid].items() )
        while S <= 0.:
            self.M.pprint ( "sum of branchings of %d was found to be %s: randomize them, while normalizing." % ( pid, S ) )
            for dpid,br in self.M.decays[pid].items():
                br = random.gauss ( 1. / nitems, numpy.sqrt ( .5 / nitems )  )
                br = max ( 0., br )
                self.M.decays[pid][dpid]=br
                S+=br
        brs = []
        for dpid,br in self.M.decays[pid].items():
                tmp = self.M.decays[pid][dpid] / S
                self.M.decays[pid][dpid] = tmp
                if tmp < .99999:
                    brs.append ( tmp )
        if len(brs)>0 and numpy.std ( brs ) > 0.001:
            self.M.log( "normalize branchings of %s with=%.2f, they are at %.2f +/- %.2f" % ( helpers.getParticleName ( pid ), S, numpy.mean ( brs ), numpy.std ( brs )  ) )

        ## adjust the signal strength multipliers to keep everything else
        ## as it was
        if not fixSSMs:
            return
        for pidpair,ssm in self.M.ssmultipliers.items():
            if pidpair in [ (pid,pid),(-pid,-pid),(-pid,pid),(pid,-pid) ]:
                newssm = ssm*S*S
                if newssm > 10000.:
                    newssm = 10000.
                self.M.ssmultipliers[pidpair]= newssm
                continue
            if (pid in pidpair) or (-pid in pidpair):
                newssm = ssm*S
                if newssm > 10000.:
                    newssm = 10000.
                self.M.ssmultipliers[pidpair]=newssm

    def normalizeAllBranchings ( self ):
        """ normalize all branchings, after freezing or unfreezing particles """
        for pid in self.M.masses.keys():
            if not pid == self.M.LSP:
                self.normalizeBranchings ( pid )

    def resolveMuhat ( self ):
        """ multiply the signal strength multipliers with muhat, then set muhat to 1. """
        if not hasattr ( self.M, "muhat" ):
            return
        if self.M.muhat == 0.:
            self.M.pprint ( "muhat is exactly zero??? set to one." )
            self.M.muhat = 1.
        if abs ( self.M.muhat - 1.0 ) < 1e-5:
            return
        self.M.log ( "resolve a muhat of %.2f" % self.M.muhat )
        self.M.rmax = self.M.rmax * self.M.muhat
        self.M.r2 = self.M.r2 * self.M.muhat
        for k,v in self.M.ssmultipliers.items():
            self.M.ssmultipliers[k] = v * self.M.muhat
        self.M.muhat = 1.

    def isInPids ( self, p, dpid ):
        """ is p in dpid, or p equals to dpid? """
        if type(dpid) == tuple:
            return p in dpid
        return p == dpid

    def randomlyChangeModel(self,predictor,sigmaUnFreeze = 0.5, probBR = 0.2, probSS = 0.25,
                                probSSingle=0.8, ssmSigma=0.1,
                                probMerge = 0.05, sigmaFreeze = 0.5, probMassive = 0.3,
                                probMass = 0.05, dx =200):
        """Randomly modify the proto-model following the steps:
        1) A random particle can be unfrozen (the probability is controlled by sigmaFreeze)
        2) A random BR can be modified (with probability probBR)
        3) A random signal strenght can be modified (the probability is controlled by probSS, probSSingle and ssmSigma)
        4) Particles can be merged (with probability probMerge)
        5) A random particle can be frozen (the probability is controlled by sigmaFreeze and probMassive)
        6) A random mass can be changed by a maximum value of dx (with probability probMass)
        """

        nChanges = 0
        nChanges += self.randomlyUnfreezeParticle(sigma=sigmaUnFreeze)
        nChanges += self.randomlyChangeBranchings(prob=probBR)
        nChanges += self.randomlyChangeSignalStrengths(prob = probSS,
                                                probSingle = probSSingle, ssmSigma = ssmSigma)
        nChanges += self.randomlyAttemptAMerger(predictor, prob=probMerge)
        nChanges+=self.randomlyFreezeParticle(sigma= sigmaFreeze, probMassive = probMassive)
        if not nChanges: #If nothing has changed, force a random change of masses
            nChanges+=self.randomlyChangeMasses(predictor,prob=1.0, dx = dx)
        else: #Change masses with 5% probability
            nChanges+=self.randomlyChangeMasses(predictor,prob = probMass, dx = dx)

        #Update the SLHA file
        self.M.createSLHAFile(nevents = 20000)

    def randomlyUnfreezeParticle ( self, sigma=0.5, force = False ):
        """ Unfreezes a (random) frozen particle according to gaussian distribution with width sigma.

        :param sigma: Width of the gaussian distribution
        :param force: If True force the unfreezing.
        """

        #Decide whether to unfreeze according to the number of active particles
        if not force:
            nUnfrozen = len( self.M.unFrozenParticles() )
            nTotal = len ( self.M.masses.keys() )
            denom = self.M.Z+1.
            if denom < 1.:
                denom = 1.
            mu = 1. - .7 / denom ## make it more unlikely when Z is high
            uUnfreeze = random.gauss( mu ,sigma)
            if uUnfreeze < nUnfrozen/float(nTotal):
                return 0

        self.log ( "unfreeze random particle" )
        #Randomly select the pid:
        frozen = self.M.frozenParticles()
        if len(frozen)==0:
            return 0
        pid = random.choice ( frozen )

        #Randomly select mass of unfrozen particle:
        self.M.masses[pid] = random.uniform ( self.M.masses[self.M.LSP], self.M.maxMass )
        ## when unfreezing, nothing can go offshell, right?
        self.removeAllOffshell() ## remove all offshell stuff, normalize all branchings
        self.M.delXSecs() ## old xsecs dont count anymore
        self.M.log ( "Unfreezing %s: m=%f" % ( helpers.getParticleName(pid), self.M.masses[pid] ) )
        return 1

    def randomlyChangeBranchings ( self, prob=0.2 ):
        """ randomly change the branchings of a single particle

        :param prob: Probability for changing a branching ratio
        """

        uBranch = random.uniform(0,1)
        if uBranch > prob:
            return 0

        self.log ( "randomly change branchings" )
        unfrozenparticles = self.M.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.M.pprint ( "not enough unfrozen particles to change random branching" )
            return 0
        p = random.choice ( unfrozenparticles )
        if not p in self.M.decays.keys():
            self.M.highlight ( "error", "why is %d not in decays?? %s" % ( p, self.M.decays.keys() ) )
            # we dont know about this decay? we initialize with the default!
        return self.randomlyChangeBranchingOfPid ( p )

    def randomlyChangeBranchingOfPid ( self, pid ):
        """ randomly change the branching a particle pid """
        openChannels = set()
        for dpid,br in self.M.decays[pid].items():
            if not numpy.isfinite ( br ):
                self.M.highlight ( "error", "br of %s/%s is %s. set to zero." % ( pid, dpid, br ) )
                self.M.decays[pid][dpid]=0.
            if type(dpid) not in [ tuple, list] and dpid in self.M.unFrozenParticles():
                openChannels.add ( dpid )
            if type(dpid) in [ tuple, list ] and dpid[0] in self.M.unFrozenParticles():
                openChannels.add ( dpid )
        for dpid in self.M.possibledecays[pid]:
            openChannels.add ( dpid )
        # print ( "the open channels are", openChannels )
        if len(openChannels) < 2:
            self.M.pprint ( "number of open channels of %d is %d: cannot change branchings." % (pid, len(openChannels) ) )
            # not enough channels open to tamper with branchings!
            return 0
        dx =.1/numpy.sqrt(len(openChannels)) ## maximum change per channel
        S=0.
        for c_,i in enumerate(openChannels):
            oldbr = 0.
            if i in self.M.decays[pid]:
                oldbr = self.M.decays[pid][i]
            if not numpy.isfinite ( oldbr ):
                self.M.highlight ( "error", "br of %s/%s is %s. set to zero." % ( pid, i, oldbr ) )
                oldbr = 0.
            Min,Max = max(0.,oldbr-dx), min(oldbr+dx,1.)
            br = random.uniform ( Min, Max )
            ## with some small chance set it simply to zero
            a = random.uniform ( 0., 1. )
            if a > 0.95:
                br = 0.
            ## with some small chance set it to equal another random br
            if a < 0.05:
                c = random.choice(list(openChannels))
                if pid in self.M.decays and c in self.M.decays[pid]:
                    br = self.M.decays[pid][c]
            self.M.decays[pid][i]=br
            S+=br
        if S == 0.: ## all at zero?
            c = random.choice(list(openChannels))
            if pid in self.M.decays:
                self.M.decays[pid][c] = 1.
                S = 1.
        if S > 0.: ## correct for too large sums
            for i,v in self.M.decays[pid].items():
                self.M.decays[pid][i] = v / S
            S = 1.
        control = sum ( [  x for x in self.M.decays[pid].values() ] )
        if abs ( control - 1.0 ) > 1e-5 or not numpy.isfinite ( control ):
            self.M.pprint ( "ATTENTION control %s" % control )
        #    sys.exit(-5)
        brvec=[]
        for x in self.M.decays[pid].values():
            if x<1e-5:
                brvec.append("")
            else:
                brvec.append("%.2f" % x )
        self.M.log ( "changed branchings of %s: %s: s=%.2f" % (helpers.getParticleName(pid), ",".join( brvec  ), control ) )
        return 1

    def randomlyChangeSignalStrengths ( self, prob=0.25, probSingle=0.8, ssmSigma=0.1):
        """ randomly change one of the signal strengths according to a gaussian distribution centered around the original SSM.

        :param prob: Probability for changing the signal strengths
        :param probSingle: Probability for changing the signal strength of a single particle
        :param ssmSigma: Width for the gaussian
        """

        uSSM = random.uniform(0,1)
        if not (uSSM > 1-prob):
            return 0

        self.log ( "randomly change signal strengths" )
        if random.uniform(0,1) < probSingle:
            return self.randomlyChangeSSOfOneParticle()
        unfrozenparticles = self.M.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.M.pprint ( "not enough unfrozen particles to change random signal strength" )
            return 0
        #Randomly choose which process pids to change:
        p = random.choice ( unfrozenparticles )
        q = random.choice ( unfrozenparticles )
        #Half of the time select the anti-particle:
        if self.M.hasAntiParticle(p) and random.uniform(0,1)<.5:
            p = -p
        if self.M.hasAntiParticle(q) and random.uniform(0,1)<.5:
            q = -q
        pair = self.M.toTuple(p,q)
        if not pair in self.M.ssmultipliers:
            self.M.ssmultipliers[pair]=1.
        newSSM=self.M.ssmultipliers[pair]*random.gauss(1.,ssmSigma) + random.gauss(.1,.1)
        if newSSM < 0.:
            newSSM = 0.
        self.changeSSM(pair,newSSM)
        self.M.log ( "changing signal strength multiplier of %s,%s: %.2f." % (helpers.getParticleName(pair[0]), helpers.getParticleName(pair[1]), newSSM ) )
        return 1

    def randomlyChangeSSOfOneParticle ( self, pid = None ):
        """ randomly change the SS's consistently for one pid
        :param pid: change for this pid. If None, change of a random pid.
        """
        unfrozenparticles = self.M.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.M.pprint ( "not enough unfrozen particles to change random signal strength" )
            return 0
        p = random.choice ( unfrozenparticles )
        if pid != None:
            p = pid
        a = random.uniform ( 0., 1. )
        if a > .9: ## sometimes, just knock out a random SSM
            randomProd = random.choice ( list ( self.M.ssmultipliers.keys() ) )
            self.M.ssmultipliers[randomProd]=0.00001
            return 1
        if a < .1: ## sometimes, just try to set to 1.
            randomProd = random.choice ( list ( self.M.ssmultipliers.keys() ) )
            self.M.ssmultipliers[randomProd]=1.
            return 1
        if .1 < a < .2: ## sometimes, just try to set to ssm of differnt particle
            randomProd = random.choice ( list ( self.M.ssmultipliers.keys() ) )
            v = random.choice ( list ( self.M.ssmultipliers.values() ) )
            self.M.ssmultipliers[randomProd]=v
            return 1
        f = random.uniform ( .8, 1.2 )
        self.M.log ( "randomly changing ssms of %s by a factor of %.2f" % \
                     ( helpers.getParticleName ( p ), f ) )
        ssms = []
        for dpd,v in self.M.ssmultipliers.items():
            if p in dpd or -p in dpd:
                newssm = self.M.ssmultipliers[dpd]*f
                #if newssm > 10000.:
                #    newssm = 10000.
                # self.M.ssmultipliers[dpd]= newssm
                self.changeSSM ( dpd, newssm )
                ssms.append ( newssm )
        self.M.log ( " `- %s: ssms are now %.2f+/-%.2f" % ( helpers.getParticleName(p), numpy.mean ( ssms ), numpy.std ( ssms) ) )
        return 1

    def randomlyAttemptAMerger ( self, predictor, prob = 0.05 ):
        """ randomly try to merge a mergable pair of particles

        :param prob: Probability for merging
        :returns: False, if no mergable particle pair exists, else true
        """

        ## randomly try a merger
        uM = random.uniform(0,1)
        if uM > prob:
            return False

        self.log ( "randomly try merger" )
        possibles = self.checkForMergers ( predictor, mergeIfPossible = False )
        if len(possibles)==0:
            return False
        self.merge ( random.choice ( possibles ) )
        return True

    def checkForMergers ( self, predictor, mergeIfPossible = False ):
        """ compile a list of potential PID mergers, then check
        :param mergeIfPossible: if True, then perform possible mergers
        """
        candpairs = [ (1000001, 1000002, 1000003, 1000004 ), ( 1000005, 2000005 ),
                       (1000006, 2000006), ( 1000024, 1000037 ), ( 1000023, 1000025 )  ]
        unfrozen = self.M.unFrozenParticles( withLSP=False )
        ret = []
        for candidates in candpairs:
            pids = set()
            for cand in candidates:
                if cand in unfrozen:
                    pids.add ( cand )
            if len(pids)>1:
                r = self.checkForMergerOf ( predictor, pids, mergeIfPossible )
                if r:
                    ret.append ( pids )
        return ret

    def checkForMergerOf ( self, predictor, pids, mergeIfPossible = False ):
        """ check if PIDs can be merged """
        self.log ( "checking if %s can be merged" % str(pids) )
        #if not hasattr ( self.M, "stored_xsecs" ) or self.M.stored_xsecs == None:
        #    self.pprint ( "model has no stored xsecs?" )
        #    self.M.computeXSecs(  )
        #self.log ( "found %d stored xsecs" % len(self.M.stored_xsecs) )
        cpair,dmin = self.getClosestPair ( pids )
        self.log ( "closest pair is %s: dm=%.1f" % (str(cpair),dmin ) )
        max_dm = 200. ## maximum mass gap to consider a merger
        if dmin < max_dm:
            if mergeIfPossible:
                self.merge ( predictor, cpair )
            return True
        return False

    def merge ( self, predictor, pair, merge_strategy="default", force_merge=False ):
        """ merge two particles, pids given in pair
        :param merge_strategy: I introduced this so we can try a few strategies
                               and compare
        :param pair: pair of pids
        :param force_merge: if true, for the merger, even if Z gets much lower,
            or we run into an exclusion.
        """
        pair = list(pair)
        pair.sort()
        p1,p2 = pair[0], pair[1]
        self.pprint ( "attempt to merge %d and %d" % ( p1, p2 ) )
        self.log ( "masses before merger: %.2f, %.2f" % \
                   ( self.M.masses[p1], self.M.masses[p2] ) )
        avgM = self.computeAvgMass ( pair, merge_strategy )
        self.log ( "avg mass for %s is %.1f" % ( str(pair), avgM ) )
        self.M.backup() ## in case it doesnt work out!
        ## for the next step we need the cross sections
        self.log ( "now compute the xsecs (if not cached), *before* taking out particle. so we can compute ssms" )
        self.M.createSLHAFile ( recycle_xsecs = True )
        self.M.masses[ p1 ] = avgM ## set this one to the avg mass
        self.M.masses[ p2 ] = 1e6 ## freeze that one!

        ## add the decays from pid2 to pid1
        for pids,br in self.M.decays [ p2 ].items():
            if pids in self.M.decays[p1]:
                if br > 0.001:
                    self.log ( "add to decays %s/%s: %.2f" % ( p1, pids, br ) )
                self.M.decays[p1][pids] = self.M.decays[p1][pids] + br
            else:
                self.log ( "set decays of %s/%s to %.2f" % ( p1, pids, br ) )
                self.M.decays[p1][pids] = br
        # print ( "ssms1000006", self.M.ssmultipliers[(-1000006, 1000006)] )
        self.log ( "now normalize branchings of %d" % p1 )
        self.normalizeBranchings ( p1, fixSSMs = False )

        ## decays *into* pid2 need to be remapped to pid1
        olddecays = copy.deepcopy ( self.M.decays )
        for mpid,decays in olddecays.items():
            for dpids,br in decays.items():
                if self.isIn ( p2, dpids ) and type(dpids) in [ list, tuple ]:
                    newpids = []
                    for dpid in dpids:
                        if dpid == p2:
                            newpids.append ( p1 )
                        else:
                            newpids.append ( dpid )
                    if br > 0.0001:
                        self.log ( "redirecting decay of %d from %s to %s: br=%.2f" % \
                                   ( mpid, dpids, newpids, br ) )
                    self.M.decays[mpid].pop ( dpids )
                    self.M.decays[mpid][tuple(newpids)]=br
                if self.isIn ( p2, dpids ) and type(dpids) in [ int ]:
                    newpids = [ p1, dpids ]
                    if br > 0.0001:
                        self.log ( "redirecting decay of %d from %s to %s: br=%.2f" % \
                                   ( mpid, dpids, newpids, br ) )
                    self.M.decays[mpid].pop ( dpids )
                    self.M.decays[mpid][tuple(newpids)]=br

        ## clean up, remove all decays with pid2
        # self.M.decays.pop ( p2 )
        ## ssmultipliers get added up, too
        newssms = self.computeNewSSMs( pair )

        self.M.ssmultipliers = newssms

        self.log ( "now predict. old rmax is at %.2f" % self.M.rmax )
        oldZ = self.M.Z
        self.M.delXSecs()

        passed = predictor.predict (protomodel=self.M)
        if passed == False:
            self.pprint ( "after merging, did not pass. rmax=%.2f. scale and retry." % self.M.rmax )
            ## did not pass? Okay, we make it pass, by scaling the new ssms
            f_sc = .999 * rthresholds[0] / self.M.rmax  ## we multiply with this factor
            for pids,ssm in self.M.ssmultipliers.items():
                if p1 in pids or -p1 in pids:
                    self.M.ssmultipliers[pids] = self.M.ssmultipliers[pids] * f_sc
            passed = predictor.predict ( protomodel=self.M )
            self.pprint ( "after retrying we have: passed=%d, rmax=%.2f" % ( passed, self.M.rmax ) )

        if force_merge:
            self.pprint ( "forced merge, so not checking" )
            return
        if self.M.excluded:
            self.pprint ( "trying to merge %d and %d lead to an rmax of %.2f. reverting" % \
                          ( p1, p2, self.M.rmax ) )
            self.M.restore()
        if self.M.Z < oldZ *.999:
            self.pprint ( "trying to merge %d and %d lead to a Z of %.3f < %.3f. reverting" % \
                          ( p1, p2, self.M.Z, oldZ *.999 ) )
            self.M.restore()

    def randomlyFreezeParticle ( self, sigma= 0.5, probMassive = 0.3):
        """ freezes a random unfrozen particle according to gaussian distribution with width sigma.

        :param sigma: Width of the gaussian distribution
        :param probMassive: Probability for freezen the most massive particle
        """

        nUnfrozen = len( self.M.unFrozenParticles() )
        nTotal = len ( self.M.masses.keys() )
        denom = self.M.Z+1.
        if denom < 1.:
            denom = 1.
        mu = .4 / denom ## make it more unlikely when Z is high
        uFreeze = random.gauss(mu,sigma)
        if uFreeze > nUnfrozen/float(nTotal):
            return 0

        # in every nth step freeze random particle
        if random.uniform(0,1) < probMassive:
            self.log ( "freeze most massive particle" )
            return self.freezeMostMassiveParticle()

        self.log ( "freeze random particle" )
        unfrozen = self.M.unFrozenParticles( withLSP = False )
        if len(unfrozen)<2:
            self.M.log ( "only two particles are unfrozen, so dont freeze anything" )
            return 0 ## freeze only if at least 3 unfrozen particles exist
        p = random.choice ( unfrozen )
        self.M.log ( "Freezing %s (but keep its branchings)." % ( helpers.getParticleName(p) ) )
        self.freezeParticle ( p )
        return 1

    def freezeMostMassiveParticle ( self ):
        """ freezes the most massive unfrozen particle """
        unfrozen = self.M.unFrozenParticles( withLSP=False )
        if len(unfrozen)<2:
            return 0 ## freeze only if at least 3 unfrozen particles exist
        pid,minmass=0,0
        for i in unfrozen:
            if self.M.masses[i]>minmass:
                minmass = self.M.masses[i]
                pid = i
        # p = random.choice ( unfrozen )
        self.M.log ( "Freezing most massive %s (%.1f)" % ( helpers.getParticleName(pid), minmass ) )
        self.freezeParticle ( pid )
        return 1

    def freezeParticle ( self, pid ):
        """ freeze particle pid, take care of offshell removal, and
            branching normalization """
        self.M.masses[pid]=1e6
        self.normalizeAllBranchings()
        self.removeAllOffshell()
        self.M.delXSecs()

    def randomlyChangeMasses ( self, predictor, prob = 0.05, dx = 200.0 ):
        """ take a random step in mass space for a single unfrozen particle

        :param prob: Probability for changing the mass
        :param dx: Defines the interval for selecting the delta m (-dx,dx) """

        uMass = random.uniform ( 0., 1. )
        if uMass < (1-prob):
            return 0

        self.log ( "take random mass step" )
        unfrozen = self.M.unFrozenParticles()
        if len(unfrozen)==0:
            return 0
        pid = random.choice ( unfrozen )

        ret = self.randomlyChangeMassOf ( pid, dx=dx )
        #for i in unfrozen:
        #    ret = self.randomlyChangeMassOf ( i )
        self.checkSwaps(predictor) ## should we really do this here?
        ## now remove all offshell decays, and normalize all branchings
        self.removeAllOffshell()
        return ret

    def computeNewSSMs ( self, pair ):
        """ compute the new ssms after the merger """
        newssms = copy.deepcopy ( self.M.ssmultipliers )
        p1, p2 = pair[0], pair[1]

        ## dont add for the frozen particles
        frozen = self.M.frozenParticles()

        #for pids, ssm in self.M.ssmultipliers.items():
        for sxsecs in self.M.stored_xsecs[0]:
            if sxsecs.info.sqrts < 10.*TeV or sxsecs.info.order > 0:
                continue
            pids = sxsecs.pid
            ssm = 1.0
            if pids in self.M.ssmultipliers:
                ssm = self.M.ssmultipliers[pids]
            if not p2 in pids and not -p2 in pids:
                continue
            addxsec = 0. * fb
            for xsec in self.M.stored_xsecs[0]:
                if pids == xsec.pid:
                    addxsec = xsec.value
            self.log ( "xsecs of dissolving production %s: %s (ssm %s)" % \
                       ( pids, addxsec, ssm ) )
            if addxsec < 0.001 * fb:
                continue
            newpids = []
            for pid in pids:
                if pid in [ p2, -p2 ]:
                    newpids.append ( int ( math.copysign ( p1, pid ) ) )
                else:
                    newpids.append ( pid )
            newpids = tuple(newpids)
            # self.pprint ( "adding", ssm, "for",pids,"to",newpids )
            if newpids in self.M.ssmultipliers:
                hasFrozenPid=False
                for pid in newpids: ## skip the frozen stuff
                    if abs(pid) in frozen:
                        hasFrozenPid=True
                if hasFrozenPid:
                    continue
                if ssm > 0.:
                    toxsec = 0. * fb
                    for xsec in self.M.stored_xsecs[0]:
                        if newpids == xsec.pid:
                            toxsec = xsec.value
                    oldssm = newssms[newpids]
                    self.log ( "xsec of to-be-kept production %s: %s, ssm=%s" % ( newpids, toxsec, oldssm ) )
                    newxsec = addxsec + toxsec
                    if toxsec > 0.*fb:
                        newssm = oldssm * newxsec.asNumber(fb)/toxsec.asNumber(fb)
                        self.log ( "adding ssm from %s to %s: ssm of addition is %.2f, ssm of keeper is %.2f, xsec of addition %s, xsec of keeper is %s. newssm is %.2f" % ( pids, newpids, ssm, oldssm, addxsec, toxsec, newssm ) )
                    ## FIXME what I didnt take into account here, is that the
                    ## xsec of the "to" particle is changing, also!
                        newssms[newpids]=newssm
            else:
                self.log ( "setting ssm of %s to %.2f" % ( newpids, ssm ) )
                newssms[newpids]=ssm
        ## clean up, remove all pid2 ssms
        newms={}
        for pids,ssm in newssms.items(): # self.M.ssmultipliers.items():
            if not p2 in pids and not -p2 in pids:
                newms[pids]=ssm
        return newms

    def computeAvgMass ( self, pids, merge_strategy ):
        """ compute the average mass
        :param merge_strategy: allow for different ways to merge
        :returns: mass, as scalar, in GeV
        """
        ret=0.
        for pid in pids:
            ret+=self.M.masses[pid]
        return ret / len(pids)

    def isIn ( self, pid, pids ):
        """ is pid in pids (in case pids is tuple),
            is pid equal to pids (in case pids is int) """
        if type(pids) in [ int, float ]:
            return pid == pids
        return pid in pids

    def simplifyMasses ( self ):
        """ return the masses only of the unfrozen particles """
        ret ={}
        unfrozen = self.M.unFrozenParticles()
        for pid in unfrozen:
            ret[pid]=self.M.masses[pid]
        return ret

    def simplifyXSecs ( self, fbmin=.001*fb ):
        """ return the xsecs above a threshold only """
        self.assertXSecs()
        xsecs={ 8:{}, 13:{} }
        for xsec in self.M.stored_xsecs[0]:
            if xsec.value < fbmin:
                continue
            sqrts = xsec.info.sqrts.asNumber(TeV)
            if not xsec.pid in xsecs[sqrts]:
                xsecs[sqrts][xsec.pid]=xsec
            else:
                if xsecs[sqrts][xsec.pid].info.order < xsec.info.order:
                    xsecs[sqrts][xsec.pid]=xsec

        return xsecs

    def printXSecs ( self, fbmin=.001*fb ):
        """ print the cross sections in a human-readable way """
        xsecs = self.simplifyXSecs( fbmin )
        for sqrts in xsecs.keys():
            print ( "%d TeV:" % sqrts )
            for pid,xsec in xsecs[sqrts].items():
                print ( " %22s: %s" % \
                        ( pid, xsec.value ) )

    def simplifyDecays ( self ):
        """ return the decays only of the unfrozen particles,
            only != 0 """
        ret ={}
        unfrozen = self.M.unFrozenParticles()
        for mpid,decays in self.M.decays.items():
            if mpid not in unfrozen:
                continue
            d = {}
            for dpid,dbr in decays.items():
                if dbr > 1e-5:
                    d[dpid]=dbr
            ret[mpid]=d
        return ret

    def allXSecsAbove ( self, threshold=.01*fb, sqrts=13*TeV, order=LO ):
        """ return list of all cross sections above threshold.
        :returns: list of tuples of pids, cross sections (that had the SSM applied),
                          and SSMs that *were* applied.
        """
        if type(threshold)==float and threshold>0.:
            self.pprint ( "note: interpreting threshold as fb" )
            threshold = threshold * fb
        self.assertXSecs()
        ret = []
        for xsec in self.M.stored_xsecs[0]:
            if xsec.info.order != order:
                continue
            if abs (( xsec.info.sqrts - sqrts ).asNumber(TeV)) > .1:
                continue
            xs = xsec.value
            ssm = 1.
            if xsec.pid in self.M.ssmultipliers:
                ssm = self.M.ssmultipliers[xsec.pid]
            ret.append ( (xsec.pid, xs, ssm) )
        ret.sort( key = lambda x: x[1], reverse = True )
        return ret

    def xsecsFor ( self, pids, sqrts=13*TeV, order=LO ):
        """ return the cross sections for pids.
        :param pids: tuple of two pids
        :returns: cross section (that had the SSM applied),
                  and SSM that *was* applied.
        """
        self.assertXSecs()
        ssm = 1.
        if pids[1] < pids[0]:
            pids = ( pids[1], pids[0] )
        if pids in self.M.ssmultipliers:
            ssm = self.M.ssmultipliers[pids]
        xs = 0. * fb
        for xsec in self.M.stored_xsecs[0]:
            if xsec.info.order != order:
                continue
            if abs ( ( xsec.info.sqrts - sqrts ).asNumber(TeV) ) > .1:
                continue
            if xsec.pid != pids:
                continue
            xs = xsec.value
        return xs,ssm

    def assertXSecs ( self ):
        """ make sure we have xsecs """
        if hasattr ( self.M, "stored_xsecs" ):
            return
        self.pprint ( "did not find cross sections, compute now." )
        self.M.computeXSecs (recycle = True )

    def simplifySSMs ( self, removeOnes=False, removeZeroes=False,
                       threshold=0.001*fb, store = False ):
        """ return only SSMs for unfrozen particles
        :param removeOnes: if True, remove ssms == 1.
        :param removeZeroes: if True, remove ssms == 0.
        :param threshold: remove the SSMs for cross sections smaller
                                          than the given threshold (13TeV, LO).
        :param store: if True, overwrite original ssms with ours
        :returns: dictionary of SSMs
        """
        if type(threshold)==float and threshold>0.:
            self.pprint ( "note: interpreting threshold as fb" )
            threshold = threshold * fb
        ret = {}
        frozen = self.M.frozenParticles()
        for pids,v in self.M.ssmultipliers.items():
            if removeOnes and abs(v-1.)<1e-5:
                continue
            if removeZeroes and v<1e-7:
                continue
            xsecBigEnough = False
            if threshold > 0.*fb:
                self.assertXSecs()
                for xsec in self.M.stored_xsecs[0]:
                    if xsec.info.sqrts.asNumber(TeV)<10:
                        continue
                    if pids == xsec.pid: # they are always sorted
                        sigma = xsec.value
                        if sigma > threshold:
                            xsecBigEnough = True
            if not xsecBigEnough:
                continue
            isFrozen = False
            for pid in pids:
                if pid in frozen or -pid in frozen:
                    isFrozen = True
            if isFrozen:
                continue
            ret[pids]=v
        if store:
            self.M.ssmultipliers = ret
        return ret

    def changeSSM ( self, pids, newssm ):
        """ change the signal strength multiplier of pids to newssm,
            if we have stored xsecs, we correct them, also """
        if type(pids) != tuple:
            self.M.highlight ( "error", "when changing SSMs, need to supply PIDs as a tuple!" )
            return
        if len(pids)!= 2:
            self.M.highlight ( "error", "when changing SSMs, need to supply PIDs as a tuple of two pids!" )
            return
        if pids[1] < pids[0]:
            self.M.highlight ( "warn", "when changing SSMs, pids are wrongly ordered. Reverting them." )
            pids = ( pids[1], pids[0] )

        if not pids in self.M.ssmultipliers:
            self.M.highlight ( "warn", "when changing SSMs, cannot find %s. not changing anything." % str(pids) )
            return
        oldssm = self.M.ssmultipliers[pids]
        if newssm > 10000.:
            newssm = 10000.
        self.M.ssmultipliers[pids]=newssm
        self.M.highlight ( "info", "changing ssm of %s from %.2f to %.2f" % \
                                   ( str(pids), oldssm, newssm ) )
        if oldssm == 0.:
            self.M.highlight ( "info could not find ssms for %s. recompute xsecs." % str(pids) )
            self.M.delXSecs()
            return

        r = newssm / oldssm
        if not hasattr ( self.M, "stored_xsecs" ):
            self.M.highlight ( "info", "when changing SSMs, no stored xsecs found. not rescaling %s." % str(pids) )
            return
        for ctr,xsec in enumerate(self.M.stored_xsecs[0]):
            if pids == xsec.pid: ## ok, lets go!
               self.M.stored_xsecs[0][ctr].value = xsec.value * r

    def randomlyChangeMassOf ( self, pid, dx=None ):
        """ randomly change the mass of pid
        :param dx: the delta x to change. If none, then use a model-dependent
                   default
        """
        if dx == None:
            denom = self.M.Z + 1.
            if denom < 1.:
                denom = 1.
            dx = 40. / numpy.sqrt ( len(self.M.unFrozenParticles() ) ) / denom
        tmpmass = self.M.masses[pid]+random.uniform(-dx,dx)
        if tmpmass > self.M.maxMass:
            tmpmass = self.M.maxMass
        if tmpmass < self.M.masses[self.M.LSP]: ## the LSP is the LSP.
            tmpmass = self.M.masses[self.M.LSP]+1.
        self.M.masses[pid]=tmpmass
        ### if we changed the mass of the LSP, we need to make sure it remains
        ### the lightest particle
        if pid == self.M.LSP:
            for pid2,mass in self.M.masses.items():
                if pid2 == pid:
                    continue
                if mass < tmpmass:
                    self.M.masses[pid2] = tmpmass + 1.
        self.M.delXSecs() ## delete xsecs
        return 1

    def getAllPidsOfBestCombo ( self ):
        """ get all pids that appear in the best combo """
        ret = set()
        if type(self.M.bestCombo)==type(None):
            return ret
        for tp in self.M.bestCombo:
            for prod in tp.PIDs:
                for branch in prod:
                    for pid in branch:
                        if type(pid) == int:
                            ret.add ( abs(pid) )
                        if type(pid) in [ tuple, list ] and len(pid)>0:
                            ret.add ( abs(pid[0]) )

        return ret

    def freezePidsNotInBestCombo ( self ):
        """ all pids that arent in best combo but have
            unfrozen masses -- freeze them """
        okPids = self.getAllPidsOfBestCombo()
        unfrozen = self.M.unFrozenParticles( withLSP=False )
        for pid in unfrozen:
            if not pid in okPids:
                self.freezeParticle ( pid )

if __name__ == "__main__":
    import pickle
    f=open("hiscore.pcl","rb" )
    protomodels = pickle.load(f)
    f.close()
    ma = Manipulator ( protomodels[0], verbose=True )
    print ( ma.getAllPidsOfBestCombo() )
    #ma.merge ( ( 1000001, 1000003 ), force_merge = True )
    #import IPython
    #IPython.embed()
