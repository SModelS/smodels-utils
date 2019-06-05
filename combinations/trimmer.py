#!/usr/bin/env python3

""" Class that trims models down """

import time, colorama, copy
from model import Model
import helpers

class Trimmer:
    """ Class that trims models down, to decrease free parameters,
        *after* an MCMC walk.
    """
    def __init__ ( self, model, strategy="aggressive", maxloss=.001 ):
        self.model = model
        self.strategy = strategy
        self.maxloss = maxloss 

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        print ( "%s[trimmer:%d - %s] %s%s" % ( col, self.model.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)), colorama.Fore.RESET ) )

    def pprint ( self, *args ):
        """ logging """
        print ( "[trimmer:%d] %s" % (self.model.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        f=open( "walker%d.log" % self.model.walkerid, "a" )
        f.write ( "[model:%d - %s] %s\n" % ( self.model.walkerid, time.asctime(), " ".join(map(str,args)) ) )
        f.close()
        
    def trimParticles ( self ):
        unfrozen = self.model.unFrozenParticles( withLSP=False )
        ndiscarded,ndiscardedBR=0,0
        self.model.backup()
        oldZ = self.model.Z
        self.model.whatif = {} ## save the scores for the non-discarded particles.
        ## aka: what would happen to the score if I removed particle X?
        frozen = self.model.frozenParticles()
        for pid in frozen:
            ## remove ssmultipliers for frozen particles
            if pid in self.model.ssmultipliers:
                self.model.ssmultipliers.pop(pid)
        # unfrozen = [] ## FIXME was only needed for checking branching trimmer
        for cpid,pid in enumerate(unfrozen):
            self.highlight ( "info", "trying to freeze %d/%d: %s (%.1f)" % \
                   ( (cpid+1),len(unfrozen), helpers.getParticleName(pid), 
                     self.model.masses[pid] ) )
            oldmass = self.model.masses[pid]
            self.model.masses[pid]=1e6
            # self.createSLHAFile()
            self.model.predict ( self.strategy )
            self.pprint ( "when trying to remove %s, Z changed: %.3f -> %.3f" % ( helpers.getParticleName(pid), oldZ, self.model.Z ) )
            if self.model.Z > (1. - self.maxloss)*oldZ:
                ndiscarded+=1
                self.pprint ( "discarding #%d: %s" % ( ndiscarded, helpers.getParticleName(pid) ) )
                if pid in self.model.ssmultipliers:
                    #popping from multipliers also
                    self.model.ssmultipliers.pop(pid)
            else:
                self.model.whatif[pid]=self.model.Z
                self.pprint ( "not discarding %s" % helpers.getParticleName(pid) )
                self.model.masses[pid]=oldmass
                self.model.restore()

    def trim ( self, trimbranchings=False ):
        """ see if you can trim the model, accept losses smaller than maxloss
        on Z.
        :param trimbranchings: if true, also trim branchings
        """
        self.trimParticles ( )
        if trimbranchings:
            self.trimBranchings ( )
        self.model.clean()

    def trimBranchings ( ):
        """ now trim the branchings """
        unfrozen = self.model.unFrozenParticles( withLSP=False )
        self.pprint ( "now try to trim the branchings of %d particles" % len(unfrozen) )
        # unfrozen = [] ## turn it off
        for cpid,pid in enumerate(unfrozen):
            decays = self.model.decays[pid]
            self.highlight ( "info", "trying to trim %d/%d branchings of %s" % ( (cpid+1),len(unfrozen),helpers.getParticleName(pid) ) )
            for dpid,dbr in decays.items():
                if dbr < 1e-5: ## small values set automatically to zero
                    self.model.decays[pid][dpid]=0. ## correct for it.
                    S = sum ( self.model.decays[pid].values() )
                    for k,v in self.model.decays[pid].items():
                        self.model.decays[pid][k]=v/S
                    continue
                if dbr > 1e-5 and (dbr < .01 or self.model.masses[dpid]>self.model.masses[pid]):
                    self.pprint ( "decay %s -> %s (br=%.2f) has small branching or is offshell. Try to take out." % (helpers.getParticleName(pid),helpers.getParticleName(dpid),dbr) )
                    oldZ = self.model.Z
                    self.model.backup()
                    self.model.decays[pid][dpid]=0.
                    S = sum ( self.model.decays[pid].values() )
                    for k,v in self.model.decays[pid].items():
                        self.model.decays[pid][k]=v/S
                    self.model.predict ( self.strategy )
                    if self.model.Z > (1. - self.maxloss)*oldZ:
                        dbr = 0.
                        ndiscardedBR+=1
                        self.pprint ( "discarding small BR %s -> %s: %.2f: Z changed %.3f -> %.3f" % ( helpers.getParticleName(pid),helpers.getParticleName(dpid), dbr, oldZ, self.model.Z ) )
                    else:
                        self.pprint ( "not discarding small BR %s -> %s: %.2f Z changed %.3f -> %.3f" % ( helpers.getParticleName(pid), helpers.getParticleName(dpid), dbr, oldZ, self.model.Z ) )
                        self.model.restore()
                        
        self.pprint ( "froze %d particles. %d/%d particles are still unfrozen. discarded %d branchings." % ( ndiscarded, len(self.model.unFrozenParticles()),len(self.model.masses),ndiscardedBR )  )
