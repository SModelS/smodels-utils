#!/usr/bin/env python3

""" Class that trims models down """

import time, colorama, copy, sys
from smodels.tools import runtime
runtime._experimental = True
from combiner import Combiner
from protomodel import ProtoModel, rthresholds
import helpers

class Trimmer:
    """ Class that trims models down, to decrease free parameters,
        *after* an MCMC walk.
    """
    def __init__ ( self, protomodel, strategy="aggressive", maxloss=.005,
                   nevents = 10000 ):
        """
        :param maxloss: maximum loss that we allow, in relative numbers
        """
        self.protomodel = copy.deepcopy ( protomodel )
        self.strategy = strategy
        self.maxloss = maxloss
        self.nevents = nevents

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[trimmer:%d - %s] %s%s" % ( col, self.protomodel.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)), colorama.Fore.RESET ) )

    def pprint ( self, *args ):
        """ logging """
        print ( "[trimmer:%d] %s" % (self.protomodel.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        with open( "walker%d.log" % self.protomodel.walkerid, "a" ) as f:
            f.write ( "[trimmer:%d - %s] %s\n" % ( self.protomodel.walkerid, time.asctime(), " ".join(map(str,args)) ) )

    def checkZ ( self ):
        print ( "[trimmer] Check significance Z ... " )
        origZ = self.protomodel.Z # to be sure
        self.protomodel.Z = -23.
        self.protomodel.predict( strategy=self.strategy, nevents=self.nevents ) # , keep_meta = True )
        print ( "[trimmer] Z=%.2f, old=%.2f, %d predictions, experimental=%d" % ( self.protomodel.Z, origZ, len(self.protomodel.bestCombo), runtime._experimental ) )
        return abs ( (origZ - self.protomodel.Z) / ( origZ +1e-10 ) ) < 1e-7

    def computeAnalysisContributions ( self ):
        """ compute the contributions to Z of the individual analyses """
        print ( "[trimmer] now computing analysis contributions" )
        print ( "[trimmer] step 1: recompute the full Z. Old one at %.2f." % self.protomodel.Z )
        origZ = self.protomodel.Z # to be sure
        self.protomodel.Z = -23.
        hasPred = self.protomodel.predict( strategy=self.strategy, nevents=self.nevents,
                                           check_thresholds = False )
        if not hasPred:
            print ( "[trimmer] I dont understand, why do I not get a pred anymore? r=%.2f" % ( self.protomodel.rmax ) )
        print ( "[trimmer] Z=%.2f, old=%.2f, %d predictions, has a pred? %d, experimental=%d" % ( self.protomodel.Z, origZ, len(self.protomodel.bestCombo), hasPred, runtime._experimental ) )
        if origZ > 0. and abs ( origZ - self.protomodel.Z ) / origZ > 0.001:
            print  ( "[trimmer] error!! Zs do not match! Should not save" )
        contributions = {}
        combiner = Combiner()
        dZtot = 0.
        bestCombo = copy.deepcopy ( self.protomodel.bestCombo )
        for ctr,pred in enumerate(bestCombo):
            combo = copy.deepcopy ( bestCombo )[:ctr]+copy.deepcopy ( bestCombo)[ctr+1:] 
            Z, muhat_ = combiner.getSignificance ( combo )
            dZ = origZ - Z
            dZtot += dZ
            contributions[ ctr ] = Z
            # contributions[ ctr ] = Z
        for k,v in contributions.items():
            perc = (origZ-v) / dZtot
            print ( "[trimmer] without %s(%s) we get %.3f (%d%s)" % ( self.protomodel.bestCombo[k].analysisId(), self.protomodel.bestCombo[k].dataType(short=True), v, 100.*perc,"%" ) )
            contributions[ k ] = perc
        contrsWithNames = {}
        for k,v in contributions.items():
            contrsWithNames [ self.protomodel.bestCombo[k].analysisId() ] = v
        self.protomodel.contributions = contrsWithNames
        print ( "[trimmer] stored %d contributions" % len(contributions) )
        return self.protomodel

    def pidsOfBestCombo ( self ):
        """ obtain all pids that are relevant for best combo """
        ret = set()
        for theoryPred in self.protomodel.bestCombo:
            for pids in theoryPred.PIDs:
                for pidbranch in pids:
                    for pid in pidbranch:
                        ret.add ( abs(pid) )
        return ret

    def removeUnusedParticles ( self ):
        """ particles that dont make it into the best combo
            can safely be removed """
        ## FIXME still have to check for decays!
        return
        # print ( "bestcombo", self.protomodel.bestCombo )
        bestComboPids = self.pidsOfBestCombo()
        dontRemove = copy.deepcopy ( bestComboPids )
        unfrozen = self.protomodel.unFrozenParticles( withLSP=False )
        for pid in unfrozen: # bestComboPids:
            if pid in self.protomodel.decays:
                # dont remove particles that appear in decay chains of any unfrozen particle
                for dpid in self.protomodel.decays[pid].keys():
                    dontRemove.add ( abs(dpid) )
        print ( "dont removes", dontRemove )
        removed = []
        for pid in unfrozen: ## of all unfrozen particles
            if pid not in dontRemove:
                removed.append ( pid )
                self.protomodel.masses[pid]=1e6
                ## FIXME now remove also from decays!
        return removed

    def removeUnusedSSMultipliers ( self ):
        frozen = self.protomodel.frozenParticles( )
        removed = []
        for pids,v in self.protomodel.ssmultipliers.items():
            for pid in pids:
                if abs(pid) in frozen: ## ssmultiplier for a frozen particle?
                    if abs(v-1.)>1e-5:
                        removed.append ( pids )
                        self.protomodel.ssmultipliers[pids]=1. # set to 1!
        return removed

    def trimParticles ( self ):
        """ this function checks if a particle can be taken out without
            significantly worsening Z """
        from smodels.tools import runtime
        runtime._experimental = True
        unfrozen = self.protomodel.unFrozenParticles( withLSP=False )
        ndiscarded=0
        oldZ = self.protomodel.Z
        self.protomodel.whatif = {} ## save the scores for the non-discarded particles.
        ## aka: what would happen to the score if I removed particle X?
        frozen = self.protomodel.frozenParticles()
        for pid in frozen:
            ## remove ssmultipliers for frozen particles
            if pid in self.protomodel.ssmultipliers:
                self.protomodel.ssmultipliers.pop(pid)
            self.protomodel.masses[pid]=1e6 ## renormalize
        # unfrozen = [] ## FIXME was only needed for checking branching trimmer
        pidsnmasses = [ (x,self.protomodel.masses[x]) for x in unfrozen ]
        pidsnmasses.sort ( key=lambda x: x[1], reverse=True )
        for cpid,(pid,mass) in enumerate(pidsnmasses):
            self.protomodel.backup()
            self.highlight ( "info", "trying to freeze %s (%.1f): [%d/%d]" % \
                   ( helpers.getParticleName(pid,addSign=False),
                     self.protomodel.masses[pid],(cpid+1),len(unfrozen) ) )
            oldmass = self.protomodel.masses[pid]
            self.protomodel.masses[pid]=1e6
            ## also branchings need to be taken out.
            olddecays = copy.deepcopy ( self.protomodel.decays ) ## keep a copy of all, is easier
            for dpid,decays in self.protomodel.decays.items():
                if pid in decays.keys():
                    br = 1. - decays[pid] ## need to correct for what we loose
                    self.protomodel.decays[dpid].pop(pid)
                    for dp_,dbr_ in self.protomodel.decays[dpid].items():
                        self.protomodel.decays[dpid][dp_] = self.protomodel.decays[dpid][dp_] / br
            ## and signal strength multipliers, take them out also
            for dpd,v in self.protomodel.ssmultipliers.items():
                if dpid in dpd or -dpid in dpd:
                    self.protomodel.ssmultipliers[dpd]=1. ## setting to 1 is taking out
            # self.createSLHAFile()
            ## when trimming we want to increase statistics
            self.protomodel.predict ( self.strategy, nevents = self.nevents )
            self.pprint ( "when trying to remove %s, Z changed: %.3f -> %.3f" % ( helpers.getParticleName(pid), oldZ, self.protomodel.Z ) )
            if self.protomodel.Z > (1. - self.maxloss)*oldZ:
                ## the Z is still good enough? discard!
                ndiscarded+=1
                self.pprint ( "discarding #%d: %s" % ( ndiscarded, helpers.getParticleName(pid) ) )
                if pid in self.protomodel.ssmultipliers:
                    #popping from multipliers also
                    self.protomodel.ssmultipliers.pop(pid)
            else:
                self.protomodel.whatif[pid]=self.protomodel.Z
                self.pprint ( "keeping %s" % helpers.getParticleName(pid) )
                self.protomodel.masses[pid]=oldmass
                self.protomodel.decays = olddecays
                self.protomodel.restore()
        self.pprint ( "discarded %d/%d particles." % ( ndiscarded, len(pidsnmasses) ) )

    def trim ( self, trimbranchings=False ):
        """ see if you can trim the model, accept losses smaller than maxloss
        on Z.
        :param trimbranchings: if true, also trim branchings
        """
        self.trimParticles ( )
        if trimbranchings:
            self.trimBranchings ( )
        self.protomodel.trimmedBranchings = trimbranchings
        if hasattr ( self.protomodel, "checkSwaps" ):
            self.pprint ( "Check if we should swap certain particles (eg ~b2 <-> ~b1)" )
            self.protomodel.checkSwaps() ## check if e.g. N3 is lighter than N2
        self.removeUnusedSSMultipliers() ## discard unneeded ss multipliers
        self.protomodel.trimloss = self.maxloss ## store the trim loss
        self.protomodel.clean()

    def trimBranchingsOf ( self, pid ):
        """ trim the branchings of pid """
        decays = self.protomodel.decays[pid]
        ndiscardedBR = 0
        for dpid,dbr in decays.items():
            dpid1 = dpid
            if type(dpid)==tuple:
                dpid1 = dpid[0]
            if not dpid1 in self.protomodel.masses:
                self.protomodel.masses[dpid1]=1e6
            if not pid in self.protomodel.masses:
                self.protomodel.masses[pid]=1e6
            self.log ( "look at %s(%.1f) -> %s(%.1f) [br %.3f]" % (pid,self.protomodel.masses[pid],dpid1,self.protomodel.masses[dpid1],dbr) )
            if dbr < 1e-5: ## small values set automatically to zero
                self.protomodel.decays[pid][dpid]=0. ## correct for it.
                S = sum ( self.protomodel.decays[pid].values() )
                if S > 0.:
                    for k,v in self.protomodel.decays[pid].items():
                        self.protomodel.decays[pid][k]=v/S
                continue
            if dbr > 1e-5 and (dbr < .15 or self.protomodel.masses[dpid1]>self.protomodel.masses[pid]):
                self.pprint ( "decay %s -> %s (br=%.2f) has small branching or is offshell. Try to take out." % (helpers.getParticleName(pid),helpers.getParticleName(dpid1),dbr) )
                oldZ = self.protomodel.Z
                self.protomodel.backup()
                self.protomodel.decays[pid][dpid]=0.
                S = sum ( self.protomodel.decays[pid].values() )
                for k,v in self.protomodel.decays[pid].items():
                    self.protomodel.decays[pid][k]=v/S
                self.protomodel.decays[pid][dpid]=0.
                self.protomodel.predict ( self.strategy, nevents=self.nevents )
                if self.protomodel.rmax > rthresholds[0]:
                    self.pprint ( "running into exclusion if I try to take it out (rmax=%.1f). Leave in." % self.protomodel.rmax )
                    self.protomodel.restore()
                    continue

                if self.protomodel.Z > (1. - self.maxloss)*oldZ:
                    dbr = 0.
                    ndiscardedBR+=1
                    self.pprint ( "discarding small BR %s -> %s: %.2f: Z changed %.3f -> %.3f" % ( helpers.getParticleName(pid),helpers.getParticleName(dpid), dbr, oldZ, self.protomodel.Z ) )
                else:
                    self.pprint ( "not discarding small BR %s -> %s: %.2f Z changed %.3f -> %.3f" % ( helpers.getParticleName(pid), helpers.getParticleName(dpid), dbr, oldZ, self.protomodel.Z ) )
                    self.protomodel.restore()
        return ndiscardedBR


    def trimBranchings ( self ):
        """ now trim the branchings """
        from smodels.tools import runtime
        runtime._experimental = True
        unfrozen = self.protomodel.unFrozenParticles( withLSP=False )
        ndiscardedBR=0
        self.pprint ( "now try to trim the branchings of %d particles" % len(unfrozen) )
        # unfrozen = [] ## turn it off
        for cpid,pid in enumerate(unfrozen):
            ndiscardedBR += self.trimBranchingsOf ( pid )
            self.highlight ( "info", "trying to trim branchings of %s [%d/%d]" % ( helpers.getParticleName(pid),(cpid+1),len(unfrozen) ) )
        self.pprint ( "%d/%d particles are still unfrozen. discarded %d branchings." % ( len(self.protomodel.unFrozenParticles()),len(self.protomodel.masses),ndiscardedBR )  )
