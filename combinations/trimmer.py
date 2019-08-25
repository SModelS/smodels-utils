#!/usr/bin/env python3

""" Class that trims models down """

import time, colorama, copy, sys
from smodels.tools import runtime
runtime._experimental = True
from combiner import Combiner
from model import Model
import helpers

class Trimmer:
    """ Class that trims models down, to decrease free parameters,
        *after* an MCMC walk.
    """
    def __init__ ( self, model, strategy="aggressive", maxloss=.001 ):
        self.model = copy.deepcopy ( model )
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
        with open( "walker%d.log" % self.model.walkerid, "a" ) as f:
            f.write ( "[model:%d - %s] %s\n" % ( self.model.walkerid, time.asctime(), " ".join(map(str,args)) ) )

    def computeAnalysisContributions ( self ):
        """ compute the contributions to Z of the individual analyses """
        print ( "[trimmer] now computing analysis contributions" )
        print ( "[trimmer] step 1: recompute the full Z. Old one at %.2f." % self.model.Z )
        #anas = set()
        #for pred in self.model.bestCombo:
        #    anas.add ( pred.analysisId() )
        #from smodels.theory.theoryPrediction import theoryPredictionsFor
        #db = Database ( "../../smodels-database" )
        #results = db.getExpResults ( analysisIDs = anas )
        #print ( "[trimmer] got %d results" % len(results))
        origZ = self.model.Z # to be sure
        self.model.Z = -23.
        self.model.predict( strategy=self.strategy, keep_meta = True )
        print ( "[trimmer] Z=%.2f, old=%.2f, %d predictions, experimental=%d" % ( self.model.Z, origZ, len(self.model.bestCombo), runtime._experimental ) )
        if origZ > 0. and abs ( origZ - self.model.Z ) / origZ > 0.001:
            print  ( "[trimmer] error!! Zs do not match! Should not save" )
        contributions = {}
        combiner = Combiner()
        dZtot = 0.
        bestCombo = copy.deepcopy ( self.model.bestCombo )
        for ctr,pred in enumerate(bestCombo):
            combo = copy.deepcopy ( bestCombo )[:ctr]+copy.deepcopy ( bestCombo)[ctr+1:] 
            Z = combiner.getSignificance ( combo )
            dZ = origZ - Z
            dZtot += dZ
            contributions[ ctr ] = Z
        for k,v in contributions.items():
            perc = (origZ-v) / dZtot
            print ( "[trimmer] without %s(%s) we get %.2f (%d%s)" % ( self.model.bestCombo[k].analysisId(), self.model.bestCombo[k].dataType(short=True), v, 100.*perc,"%" ) )
            contributions[ k ] = perc
        self.model.contributions = contributions
        print ( "[trimmer] stored %d contributions" % len(contributions) )
        return self.model

    def trimParticles ( self ):
        """ this function checks if particle can be taken out without
            significantly worsening Z """
        from smodels.tools import runtime
        runtime._experimental = True
        unfrozen = self.model.unFrozenParticles( withLSP=False )
        ndiscarded=0
        oldZ = self.model.Z
        self.model.whatif = {} ## save the scores for the non-discarded particles.
        ## aka: what would happen to the score if I removed particle X?
        frozen = self.model.frozenParticles()
        for pid in frozen:
            ## remove ssmultipliers for frozen particles
            if pid in self.model.ssmultipliers:
                self.model.ssmultipliers.pop(pid)
            self.model.masses[pid]=1e6 ## renormalize
        # unfrozen = [] ## FIXME was only needed for checking branching trimmer
        pidsnmasses = [ (x,self.model.masses[x]) for x in unfrozen ]
        pidsnmasses.sort ( key=lambda x: x[1], reverse=True )
        for cpid,(pid,mass) in enumerate(pidsnmasses):
            self.model.backup()
            self.highlight ( "info", "trying to freeze %s (%.1f): [%d/%d]" % \
                   ( helpers.getParticleName(pid),
                     self.model.masses[pid],(cpid+1),len(unfrozen) ) )
            oldmass = self.model.masses[pid]
            self.model.masses[pid]=1e6
            # self.createSLHAFile()
            self.model.predict ( self.strategy )
            self.pprint ( "when trying to remove %s, Z changed: %.3f -> %.3f" % ( helpers.getParticleName(pid), oldZ, self.model.Z ) )
            if self.model.Z > (1. - self.maxloss)*oldZ:
                ## the Z is still good enough? discard!
                ndiscarded+=1
                self.pprint ( "discarding #%d: %s" % ( ndiscarded, helpers.getParticleName(pid) ) )
                if pid in self.model.ssmultipliers:
                    #popping from multipliers also
                    self.model.ssmultipliers.pop(pid)
            else:
                self.model.whatif[pid]=self.model.Z
                self.pprint ( "keeping %s" % helpers.getParticleName(pid) )
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
        self.model.trimmedBranchings = trimbranchings
        self.model.clean()

    def trimBranchings ( self ):
        """ now trim the branchings """
        from smodels.tools import runtime
        runtime._experimental = True
        unfrozen = self.model.unFrozenParticles( withLSP=False )
        ndiscardedBR=0
        self.pprint ( "now try to trim the branchings of %d particles" % len(unfrozen) )
        # unfrozen = [] ## turn it off
        for cpid,pid in enumerate(unfrozen):
            decays = self.model.decays[pid]
            self.highlight ( "info", "trying to trim branchings of %s [%d/%d]" % ( helpers.getParticleName(pid),(cpid+1),len(unfrozen) ) )
            for dpid,dbr in decays.items():
                if not dpid in self.model.masses:
                    self.model.masses[dpid]=1e6
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
                    if self.model.rmax > 1.5:
                        self.pprint ( "running into exclusion if I try to take it out (rmax=%.1f). Leave in." % self.model.rmax )
                        self.model.restore()
                        continue

                    if self.model.Z > (1. - self.maxloss)*oldZ:
                        dbr = 0.
                        ndiscardedBR+=1
                        self.pprint ( "discarding small BR %s -> %s: %.2f: Z changed %.3f -> %.3f" % ( helpers.getParticleName(pid),helpers.getParticleName(dpid), dbr, oldZ, self.model.Z ) )
                    else:
                        self.pprint ( "not discarding small BR %s -> %s: %.2f Z changed %.3f -> %.3f" % ( helpers.getParticleName(pid), helpers.getParticleName(dpid), dbr, oldZ, self.model.Z ) )
                        self.model.restore()

        self.pprint ( "%d/%d particles are still unfrozen. discarded %d branchings." % ( len(self.model.unFrozenParticles()),len(self.model.masses),ndiscardedBR )  )

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='trimmer. if called from commandline, it currently computes the analysis contributions (yes, this is quite confusing)' )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file with hiscores [hiscore.pcl]',
            type=str, default="hiscore.pcl" )
    argparser.add_argument ( '-s', '--save',
            help='save the analysis contributed result', action='store_true' )
    args = argparser.parse_args()
    from hiscore import Hiscore
    h = Hiscore ( 0, False, args.picklefile )
    model = h.hiscores[0]
    useTrimmed = False
    if len ( h.trimmed ) > 0:
        print ( "[trimmer] trimmed models available." )
        model = h.trimmed[0]
        useTrimmed = True
    else:
        print ( "[trimmer] no trimmed models available, falling back to untrimmed." )
    print ( "model: %s" % model.description )
    tr = Trimmer ( model )
    model = tr.computeAnalysisContributions ()
    if useTrimmed:
        h.trimmed[0] = model
    else:
        h.hiscores[0] = model
    if args.save:
        h.save()

if __name__ == "__main__":
    main()

