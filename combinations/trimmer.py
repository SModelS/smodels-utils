#!/usr/bin/env python3

""" Class that trims models down """

import time, colorama, copy, sys, math
from smodels.tools import runtime
from smodels.tools.physicsUnits import fb
runtime._experimental = True
from combiner import Combiner
from protomodel import ProtoModel, rthresholds
from manipulator import Manipulator
import helpers

class Trimmer:
    """ Class that trims models down, to decrease free parameters,
        *after* an MCMC walk.
    """
    def __init__ ( self, protomodel, strategy="aggressive", maxloss=.005,
                   nevents = 100000 ):
        """
        :param maxloss: maximum loss that we allow, in relative numbers
        """
        self.M = copy.deepcopy ( protomodel )
        self.M.createNewSLHAFileName ( prefix="tri" )
        self.manipulator = Manipulator ( self.M )
        self.strategy = strategy
        self.maxloss = maxloss
        self.nevents = nevents

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[trimmer:%d - %s] %s%s" % ( col, self.M.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)), colorama.Fore.RESET ) )

    def pprint ( self, *args ):
        """ logging """
        print ( "[trimmer:%d] %s" % (self.M.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        # logfile = "walker%d.log" % self.M.walkerid
        logfile = "hiscore.log"
        with open( logfile, "a" ) as f:
            f.write ( "[trimmer:%d - %s] %s\n" % ( self.M.walkerid, time.asctime(), " ".join(map(str,args)) ) )

    def checkZ ( self ):
        print ( "[trimmer] Check significance Z ... " )
        origZ = self.M.Z # to be sure
        self.M.Z = -23.
        self.M.predict( strategy=self.strategy, nevents=self.nevents ) # , keep_meta = True )
        print ( "[trimmer] Z=%.2f, old=%.2f, %d predictions, experimental=%d" % ( self.M.Z, origZ, len(self.M.bestCombo), runtime._experimental ) )
        return abs ( (origZ - self.M.Z) / ( origZ +1e-10 ) ) < 1e-7

    def computeAnalysisContributions ( self ):
        """ compute the contributions to Z of the individual analyses """
        print ( "[trimmer] now computing analysis contributions" )
        print ( "[trimmer] step 1: recompute the full Z. Old one at %.2f." % self.M.Z )
        origZ = self.M.Z # to be sure
        self.M.Z = -23.
        hasPred = self.M.predict( strategy=self.strategy, nevents=self.nevents,
                                           check_thresholds = False )
        if not hasPred:
            print ( "[trimmer] I dont understand, why do I not get a pred anymore? r=%.2f" % ( self.M.rmax ) )
        print ( "[trimmer] Z=%.2f, old=%.2f, %d predictions, has a pred? %d, experimental=%d" % ( self.M.Z, origZ, len(self.M.bestCombo), hasPred, runtime._experimental ) )
        if origZ > 0. and abs ( origZ - self.M.Z ) / origZ > 0.001:
            print  ( "[trimmer] error!! Zs do not match! Should not save" )
        contributions = {}
        combiner = Combiner()
        dZtot = 0.
        bestCombo = copy.deepcopy ( self.M.bestCombo )
        for ctr,pred in enumerate(bestCombo):
            combo = copy.deepcopy ( bestCombo )[:ctr]+copy.deepcopy ( bestCombo)[ctr+1:] 
            Z, muhat_ = combiner.getSignificance ( combo )
            dZ = origZ - Z
            dZtot += dZ
            contributions[ ctr ] = Z
            # contributions[ ctr ] = Z
        for k,v in contributions.items():
            perc = (origZ-v) / dZtot
            print ( "[trimmer] without %s(%s) we get %.3f (%d%s)" % ( self.M.bestCombo[k].analysisId(), self.M.bestCombo[k].dataType(short=True), v, 100.*perc,"%" ) )
            contributions[ k ] = perc
        contrsWithNames = {}
        for k,v in contributions.items():
            contrsWithNames [ self.M.bestCombo[k].analysisId() ] = v
        self.M.contributions = contrsWithNames
        print ( "[trimmer] stored %d contributions" % len(contributions) )
        return self.M

    def pidsOfBestCombo ( self ):
        """ obtain all pids that are relevant for best combo """
        ret = set()
        for theoryPred in self.M.bestCombo:
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
        # print ( "bestcombo", self.M.bestCombo )
        bestComboPids = self.pidsOfBestCombo()
        dontRemove = copy.deepcopy ( bestComboPids )
        unfrozen = self.M.unFrozenParticles( withLSP=False )
        for pid in unfrozen: # bestComboPids:
            if pid in self.M.decays:
                # dont remove particles that appear in decay chains of any unfrozen particle
                for dpid in self.M.decays[pid].keys():
                    dontRemove.add ( abs(dpid) )
        print ( "dont removes", dontRemove )
        removed = []
        for pid in unfrozen: ## of all unfrozen particles
            if pid not in dontRemove:
                removed.append ( pid )
                self.M.masses[pid]=1e6
                ## FIXME now remove also from decays!
        return removed

    def removeFrozenSSMs( self ):
        """ discard ss multipliers for frozen particles """
        self.log ( "remove frozen SSMs" )
        removed = []
        ssms = copy.deepcopy ( self.M.ssmultipliers )
        for pids,v in ssms.items():
            removeIt = False
            for pid in pids:
                if self.M.masses[abs(pid)]>5e5:
                    removeIt = True
            if removeIt:
                removed.append ( pids )
                self.M.ssmultipliers.pop ( pids )
        return removed

    def removeSSM1s( self ):
        """ discard ss multipliers that are at 1.0 """
        self.log ( "try to discard ss multipliers that are 1" )
        removed = []
        ssms = copy.deepcopy ( self.M.ssmultipliers )
        for pids,v in ssms.items():
            if abs(v-1.)<1e-5:
                removed.append ( pids )
                self.M.ssmultipliers.pop ( pids )
        return removed

    def trimParticles ( self ):
        """ this function checks if a particle can be taken out without
            significantly worsening Z """
        from smodels.tools import runtime
        runtime._experimental = True
        unfrozen = self.M.unFrozenParticles( withLSP=False )
        ndiscarded=0
        oldZ = self.M.Z
        self.M.whatif = {} ## save the scores for the non-discarded particles.
        ## aka: what would happen to the score if I removed particle X?
        frozen = self.M.frozenParticles()
        for pid in frozen:
            ## remove ssmultipliers for frozen particles
            if pid in self.M.ssmultipliers:
                self.M.ssmultipliers.pop(pid)
            self.M.masses[pid]=1e6 ## renormalize
        # unfrozen = [] ## FIXME was only needed for checking branching trimmer
        pidsnmasses = [ (x,self.M.masses[x]) for x in unfrozen ]
        pidsnmasses.sort ( key=lambda x: x[1], reverse=True )
        for cpid,(pid,mass) in enumerate(pidsnmasses):
            self.M.backup()
            self.highlight ( "info", "trying to freeze %s (%.1f): [%d/%d]" % \
                   ( helpers.getParticleName(pid,addSign=False),
                     self.M.masses[pid],(cpid+1),len(unfrozen) ) )
            oldmass = self.M.masses[pid]
            self.M.masses[pid]=1e6
            ## also branchings need to be taken out.
            olddecays = copy.deepcopy ( self.M.decays ) ## keep a copy of all, is easier
            for dpid,decays in self.M.decays.items():
                if pid in decays.keys():
                    br = 1. - decays[pid] ## need to correct for what we loose
                    if br > 0.: # if the branching is only to this guy, we cannot take it out
                        self.M.decays[dpid].pop(pid)
                        for dp_,dbr_ in self.M.decays[dpid].items():
                            self.M.decays[dpid][dp_] = self.M.decays[dpid][dp_] / br
            ## and signal strength multipliers, take them out also
            for dpd,v in self.M.ssmultipliers.items():
                if dpid in dpd or -dpid in dpd:
                    self.M.ssmultipliers[dpd]=1. ## setting to 1 is taking out
            # self.createSLHAFile()
            ## when trimming we want to increase statistics
            self.M.predict ( self.strategy, nevents = self.nevents )
            perc = 0.
            if oldZ > 0.:
                perc = ( self.M.Z - oldZ ) / oldZ
            self.pprint ( "when trying to remove %s, Z changed: %.3f -> %.3f (%d evts, %.1f%s)" % \
                    ( helpers.getParticleName(pid), oldZ, self.M.Z, self.nevents, 100.*perc, "%" ) )
            if self.M.Z > (1. - self.maxloss)*oldZ:
                ## the Z is still good enough? discard!
                ndiscarded+=1
                self.pprint ( "discarding #%d: %s" % ( ndiscarded, helpers.getParticleName(pid) ) )
                if pid in self.M.ssmultipliers:
                    #popping from multipliers also
                    self.M.ssmultipliers.pop(pid)
                oldZ = self.M.Z
            else:
                self.M.whatif[pid]=self.M.Z
                self.pprint ( "keeping %s" % helpers.getParticleName(pid) )
                self.M.masses[pid]=oldmass
                self.M.decays = olddecays
                self.M.restore()
        self.pprint ( "discarded %d/%d particles." % ( ndiscarded, len(pidsnmasses) ) )

    def removeZeroDecays ( self ):
        """ remove zero entries in all decays """
        for pid,decay in self.M.decays.items():
            newdecay = {}
            for dpd,br in decay.items():
                if br > 0.:
                    newdecay[dpd]=br
            self.M.decays[pid]=newdecay

    def trim ( self, trimbranchings=False ):
        """ see if you can trim the model, accept losses smaller than maxloss
        on Z.
        :param trimbranchings: if true, also trim branchings
        """
        oldZ = self.M.Z
        self.manipulator.removeAllOffshell() ## just to be sure!
        self.manipulator.checkSwaps() ## check if e.g. N3 is lighter than N2
        self.M = self.manipulator.get() ## to be sure
        self.M.predict ( nevents = self.nevents ) ## a final predict!
        newZ = self.M.Z
        dZ = abs(newZ - oldZ )
        err = "error!!!!"
        if dZ < .1:
            err = "ok!"
        self.pprint ( "before trimming we check again: from %.3f to %.3f (%d evts): %s" % \
                      ( oldZ, newZ, self.nevents, err ) )
        self.pprint ( "Check if we should swap certain particles (eg ~b2 <-> ~b1)" )
        self.trimParticles ( )
        if trimbranchings:
            self.trimBranchings ( )
        self.M.trimmedBranchings = trimbranchings
        self.removeSSM1s() ## discard ss multipliers that are at 1.0
        self.M.predict ( nevents = self.nevents ) ## a final predict!
        self.pprint ( "after removeSSM1s it moved from %.2f to %.2f" % ( oldZ, self.M.Z ) )
        self.removeFrozenSSMs() ## discard ss multipliers for frozen particles
        self.removeZeroDecays() ## remove decays with br of zero
        self.M.predict ( nevents = self.nevents ) ## a final predict!
        self.pprint ( "before trimSSMs we are at %.2f" % ( self.M.Z ) )
        self.trimSSMs() ## now also remove all the ssms that dont do nothing
        self.M.trimloss = self.maxloss ## store the trim loss
        self.M.predict ( nevents = self.nevents ) ## a final predict!
        self.pprint ( "SSM trimming changed the score from %.2f to %.2f" % ( oldZ, self.M.Z ) )
        self.M.clean()

    def getAllPidsOfXsecs ( self ):
        if not hasattr ( self.M, "stored_xsecs" ):
            self.pprint ( "couldnt find any xsecs, recompute!" )
            self.M.backup()
            self.M.computeXSecs ( nevents=self.nevents, 
                                  recycle = True )
        pids = set()
        self.log ( "getAllPidsOfXsecs: we have %d stored xsecs" % ( len(self.M.stored_xsecs[0]) ) )
        for xsec in self.M.stored_xsecs[0]:
            pids.add ( xsec.pid )
        return pids

    def trimSSMs ( self ):
        """ try to take out the signal strength multipliers 
        """
        xsecpids = self.getAllPidsOfXsecs()
        nbefore = len(self.M.ssmultipliers)
        self.log ( "trimSSMs: xsecpids: %s" % str(xsecpids) )
        self.log ( "trimSSMs: ssms before: %s" % str(self.M.ssmultipliers) )
        for i,(pids,ssm) in enumerate(self.M.ssmultipliers.items()):
            if not pids in xsecpids:
                self.log ( "taking out ssm(%.2f) for %s" % (ssm,str(pids) ) )
                self.M.ssmultipliers[pids]=1.
        self.removeSSM1s() ## discard ss multipliers that are at 1.0
        nafter = len(self.M.ssmultipliers)
        self.pprint ( "kept %d of %d ss multipliers" % ( nafter, nbefore ) )

    def _trimSSMsEvenMore_ ( self, trimTo=1. ):
        """ try to take out the signal strength multipliers 
        :param trimTo: parameter to try to trim ssm to, 1 or 0 makes sense. If 0,
                       you must make sure that the ones havent been taken out yet!
        """
        self.trimSSMs()
        if abs(trimTo)<1e-5:
            self.pprint ( "FIXME need to make sure the ssms=1. are still in!!" )
        oldZ = self.M.Z
        n = len(self.M.ssmultipliers)
        for i,(pids,ssm) in enumerate(self.M.ssmultipliers.items()):
            self.pprint ( "trying to take out [%d/%d] ssm(%.2f) for %s" % (i+1,n,ssm,str(pids) ) )
            self.M.ssmultipliers[pids]=trimTo ## try!
            self.M.predict ( nevents = self.nevents )
            if self.M.Z > (1. - self.maxloss)*oldZ:
                self.pprint ( "Z changed from %.2f to %.2f. discarding %s" % ( oldZ, self.M.Z, str(pids) ) )
            else:
                self.pprint ( "Z changed from %.2f to %.2f. keeping %s" % ( oldZ, self.M.Z, str(pids) ) )
                self.M.ssmultipliers[pids]=ssm
        self.removeSSM1s() ## discard ss multipliers that are at 1.0


    def trimBranchingsOf ( self, pid ):
        """ trim the branchings of pid """
        decays = self.M.decays[pid]
        ndiscardedBR = 0
        for dpid,dbr in decays.items():
            dpid1 = dpid
            if type(dpid)==tuple:
                dpid1 = dpid[0]
            if not dpid1 in self.M.masses:
                self.M.masses[dpid1]=1e6
            if not pid in self.M.masses:
                self.M.masses[pid]=1e6
            self.log ( "look at %s(%.1f) -> %s(%.1f) [br %.3f]" % (pid,self.M.masses[pid],dpid1,self.M.masses[dpid1],dbr) )
            if dbr < 1e-5: ## small values set automatically to zero
                self.M.decays[pid][dpid]=0. ## correct for it.
                S = sum ( self.M.decays[pid].values() )
                if S > 0.:
                    for k,v in self.M.decays[pid].items():
                        self.M.decays[pid][k]=v/S
                continue
            if dbr > 1e-5 and (dbr < .15 or self.M.masses[dpid1]>self.M.masses[pid]):
                self.pprint ( "decay %s -> %s (br=%.2f) has small branching or is offshell. Try to take out." % (helpers.getParticleName(pid),helpers.getParticleName(dpid1),dbr) )
                oldZ = self.M.Z
                self.M.backup()
                self.M.decays[pid][dpid]=0.
                S = sum ( self.M.decays[pid].values() )
                for k,v in self.M.decays[pid].items():
                    self.M.decays[pid][k]=v/S
                self.M.decays[pid][dpid]=0.
                self.M.predict ( self.strategy, nevents=self.nevents, recycle_xsecs = True )
                if self.M.rmax > rthresholds[0]:
                    self.pprint ( "running into exclusion if I try to take it out (rmax=%.1f). Leave in." % self.M.rmax )
                    self.M.restore()
                    continue

                if self.M.Z > (1. - self.maxloss)*oldZ:
                    dbr = 0.
                    ndiscardedBR+=1
                    self.pprint ( "discarding small BR %s -> %s: %.2f: Z changed %.3f -> %.3f" % ( helpers.getParticleName(pid),helpers.getParticleName(dpid), dbr, oldZ, self.M.Z ) )
                else:
                    self.pprint ( "not discarding small BR %s -> %s: %.2f Z changed %.3f -> %.3f" % ( helpers.getParticleName(pid), helpers.getParticleName(dpid), dbr, oldZ, self.M.Z ) )
                    self.M.restore()
        return ndiscardedBR

    def checkForMergers ( self ): 
        """ compile a list of potential PID mergers, then check """
        candpairs = [ (1000001, 1000002, 1000003, 1000004 ), ( 1000005, 2000005 ),
                       (1000006, 2000006), ( 1000024, 1000037 ), ( 1000023, 1000025 )  ]
        unfrozen = self.M.unFrozenParticles( withLSP=False )
        for candidates in candpairs:
            pids = set()
            for cand in candidates:
                if cand in unfrozen:
                    pids.add ( cand )
            if len(pids)>1:
                self.checkForMergerOf ( pids )

    def checkForMergerOf ( self, pids ):
        """ check if PIDs can be merged """
        self.log ( "checking if %s can be merged" % str(pids) )
        if not hasattr ( self.M, "stored_xsecs" ) or self.M.stored_xsecs == None:
            self.pprint ( "model has no stored xsecs?" )
            self.M.computeXSecs( nevents = 100000 )
        self.log ( "found %d stored xsecs" % len(self.M.stored_xsecs) )
        cpair,dmin = self.getClosestPair ( pids )
        self.log ( "closest pair is %s: dm=%.1f" % (str(cpair),dmin ) )
        if dmin < 100.:
            self.merge ( cpair )

    def isIn ( self, pid, pids ):
        """ is pid in pids (in case pids is tuple),
            is pid equal to pids (in case pids is int) """
        if type(pids) in [ int, float ]:
            return pid == pids
        return pid in pids

    def merge ( self, pair ):
        """ merge two particles, pids given in pair """
        pair = list(pair)
        pair.sort()
        p1,p2 = pair[0], pair[1]
        self.pprint ( "attempt to merge %d and %d" % ( p1, p2 ) )
        avgM = self.computeAvgMass ( pair )
        self.log ( "avg mass for %s is %.1f" % ( str(pair), avgM ) )
        self.M.backup() ## in case it doesnt work out!
        self.M.masses[ p2 ] = 1e6 ## freeze that one!

        ## add the decays from pid2 to pid1
        for pids,br in self.M.decays [ p2 ].items():
            if pids in self.M.decays[p1]:
                self.M.decays[p1][pids] = self.M.decays[p1][pids] + br
            else:
                self.M.decays[p1][pids] = br
        # print ( "ssms1000006", self.M.ssmultipliers[(-1000006, 1000006)] )
        self.manipulator.normalizeBranchings ( p1, fixSSMs = False )

        ## decays *into* pid2 need to be remapped to pid1
        for mpid,decays in self.M.decays.items():
            for dpids,br in decays.items():
                if self.isIn ( p2, dpids ):
                    newpids = []
                    for dpid in dpids:
                        if dpid == p2:
                            newpids.append ( p1 )
                        else:
                            newpids.append ( dpid )
                    self.M.decays[mpid].pop ( dpids )
                    self.M.decays[mpid][tuple(newpids)]=br

        ## clean up, remove all decays with pid2
        # self.M.decays.pop ( p2 )

        # print ( "ssms1000006", self.M.ssmultipliers[(-1000006, 1000006)] )
        ## ssmultipliers get added up, too
        newssms = copy.deepcopy ( self.M.ssmultipliers )
        for pids, ssm in self.M.ssmultipliers.items():
            if not p2 in pids and not -p2 in pids:
                continue
            newpids = []
            for pid in pids:
                if pid in [ p2, -p2 ]:
                    newpids.append ( int ( math.copysign ( p1, pid ) ) )
                else:
                    newpids.append ( pid )
            newpids = tuple(newpids)
            # print ( "adding", ssm, "for",pids,"to",newpids )
            if newpids in self.M.ssmultipliers:
                newssms[newpids]=newssms[newpids]+ssm
            else:
                newssms[newpids]=ssm
        # self.M.ssmultipliers = newssms

        ## clean up, remove all pid2 ssms
        newms={}
        for pids,ssm in self.M.ssmultipliers.items():
            if not p2 in pids and not -p2 in pids:
                newms[pids]=ssm
        self.M.ssmultipliers = newms

        oldZ,oldrmax = self.M.Z, self.M.rmax
        self.M.predict ( nevents = 100000, recycle_xsecs = False )
        if self.M.rmax > rthresholds[0]:
            self.pprint ( "trying to merge %d and %d lead to an rmax of %.2f. reverting" % \
                          ( p1, p2, self.M.rmax ) ) 
            self.M.restore()
        if self.M.Z < oldZ *.999:
            self.pprint ( "trying to merge %d and %d lead to a Z of %.3f < %.3f. reverting" % \
                          ( p1, p2, self.M.Z, oldZ *.999 ) ) 
            self.M.restore()

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

    def computeAvgMass ( self, pids ):
        """ compute the average mass """
        ret=0.
        for pid in pids:
            ret+=self.M.masses[pid]
        return ret / len(pids)

    def trimBranchings ( self ):
        """ now trim the branchings """
        from smodels.tools import runtime
        runtime._experimental = True
        unfrozen = self.M.unFrozenParticles( withLSP=False )
        ndiscardedBR=0
        self.pprint ( "now try to trim the branchings of %d particles" % len(unfrozen) )
        # unfrozen = [] ## turn it off
        for cpid,pid in enumerate(unfrozen):
            ndiscardedBR += self.trimBranchingsOf ( pid )
            self.highlight ( "info", "trying to trim branchings of %s [%d/%d]" % ( helpers.getParticleName(pid),(cpid+1),len(unfrozen) ) )
        self.pprint ( "%d/%d particles are still unfrozen. discarded %d branchings." % ( len(self.M.unFrozenParticles()),len(self.M.masses),ndiscardedBR )  )
