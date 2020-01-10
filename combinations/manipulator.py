#!/usr/bin/env python3

""" Class that encapsulates the manipulations we perform on the protomodels,
    so that the protomodel class is a data-centric class, and this one 
    an algorithm-centric class """

import protomodel
import helpers
import copy, random, numpy

class Manipulator:
    """ contains the protomodel manipulation algorithms. """
    def __init__ ( self, protomodel, strategy = "aggressive" ):
        self.M = copy.copy ( protomodel  ) # shallow copy
        self.strategy = strategy

    def predict ( self ):
        nevents = 20000
        if self.M.Z > 2.5:
            nevents = 50000
        if self.M.Z > 2.8:
            nevents = 100000
        self.M.log ( "now create slha file via predict with %d events" % nevents )
        self.M.predict ( self.strategy, nevents = nevents )
        if self.M.Z > 2.7 and nevents < 55000:
            # redo in extreme cases
            nevents = 100000
            self.M.predict ( self.strategy, nevents = nevents )

    def writeDictFile ( self, outfile = "mymodel.py", cleanOut=True ):
        """ write out the dict file to outfile
        :param cleanOut: clean the dictionary from defaults
        """
        D = copy.deepcopy ( self.M.dict() )
        if cleanOut:
            origMasses = self.M.dict()["masses"]
            ## but with a bit of cleaning!
            for k,v in origMasses.items():
                if v > 5e5:
                    D["masses"].pop(k)
            for k,decays in self.M.dict()["decays"].items():
                for i,v in decays.items():
                    if v < 1e-7:
                        D["decays"][k].pop(i)
            for k,v in self.M.dict()["ssmultipliers"].items():
                if abs ( v - 1.) < 1e-5:
                    D["ssmultipliers"].pop(k)
        with open ( outfile, "wt" ) as f:
            f.write ( "%s\n" % D )
            f.close()

    def pidInList ( self, pid, lst, signed ):
        """ is pid in lst """
        if signed:
            return pid in lst
        return pid in lst or -pid in lst

    def cheat ( self, mode = 0 ):
        ## cheating, i.e. starting with models that are known to work well
        if mode > 0:
            self.M.highlight ( "red", "cheat mode: %d" % mode )
        if mode == 1:
            self.M.highlight ( "red", "stops, light but ss-suppressed gluino and sbottoms" )
            self.M.masses[self.M.LSP]=343.
            self.M.masses[1000001]=780.
            self.M.masses[1000021]=520.
            self.M.masses[1000024]=566.
            self.M.masses[1000006]=640.
            self.M.masses[1000005]=830.
            self.M.masses[2000006]=900.
            self.M.masses[2000005]=1306.

            self.M.decays[1000021][(1000022,1)]=1.
            self.M.decays[1000021][(1000022,21)]=0.

            for dpd,v in self.M.ssmultipliers.items():
                ssm = self.M.ssmultipliers[dpd]
                if self.pidInList ( 1000006, dpd, signed=False ):
                    ssm=.1
                if self.pidInList ( 2000005, dpd, signed=False ):
                    ssm=.2
                if self.pidInList ( 1000005, dpd, signed=False ):
                    ssm=.2
                if self.pidInList ( 2000006, dpd, signed=False ):
                    ssm=.4
                if self.pidInList ( 1000001, dpd, signed=False ):
                    ssm=.4
                if self.pidInList ( 1000024, dpd, signed=False ):
                    ssm=.7
                if self.pidInList ( 1000021, dpd, signed=False ):
                    ssm=.03
                if dpd == ( 1000021, 1000021 ):
                    ssm = .11
                if dpd in [ ( 1000006, 1000006 ), ( -1000006, 1000006 ) ]:
                    ssm = .3
                self.M.ssmultipliers[dpd]=ssm
            return
        if mode == 2:
            self.M.highlight ( "red", "stops, light but ss-suppressed gluino and sbottoms" )
            self.M.masses[self.M.LSP]=343.
            self.M.masses[1000001]=780.
            self.M.masses[1000021]=520.
            self.M.masses[1000024]=566.
            self.M.masses[1000006]=640.
            self.M.masses[1000005]=830.
            self.M.masses[2000006]=900.
            self.M.masses[2000005]=1306.

            self.M.decays[1000021][(1000022,1)]=1.
            self.M.decays[1000021][(1000022,21)]=0.

            for dpd,v in self.M.ssmultipliers.items():
                ssm = self.M.ssmultipliers[dpd]
                if self.pidInList ( 1000006, dpd, signed=False ):
                    ssm=.1
                if self.pidInList ( 2000005, dpd, signed=False ):
                    ssm=.2
                if self.pidInList ( 1000005, dpd, signed=False ):
                    ssm=.2
                if self.pidInList ( 2000006, dpd, signed=False ):
                    ssm=.4
                if self.pidInList ( 1000001, dpd, signed=False ):
                    ssm=.4
                if self.pidInList ( 1000024, dpd, signed=False ):
                    ssm=.7
                if self.pidInList ( 1000021, dpd, signed=False ):
                    ssm=.03
                if dpd == ( 1000021, 1000021 ):
                    ssm = .1
                if dpd in [ ( 1000006, 1000006 ), ( -1000006, 1000006 ) ]:
                    ssm = .3
                self.M.ssmultipliers[dpd]=ssm
            return
        if mode >= 3:
            import os, sys
            filename = "model%d.py" % mode
            if not os.path.exists ( filename ):
                self.M.highlight ( "red", "cheat mode %d started, but no %s/%s found" % ( mode, os.getcwd(), filename ) )
                sys.exit(-1)
            self.M.highlight ( "green", "starting with %s/%s" % ( os.getcwd(), filename ) )
            with open ( filename, "rt" ) as f:
                m = eval ( f.read() )
            for k,v in m["masses"].items():
                self.M.masses[k]=v
            for k,v in m["ssmultipliers"].items():
                self.M.ssmultipliers[k]=v
            for mpid,decays in m["decays"].items():
                if not mpid in self.M.decays:
                    self.M.decays[mpid]={}
                for dpid,v in decays.items():
                    self.M.decays[mpid][dpid]=v
            return
        self.M.highlight ( "red", "cheat mode %d, not yet implemented" % mode )

    def unfreezeRandomParticle ( self ):
        """ unfreezes a random frozen particle """
        frozen = self.M.frozenParticles()
        if len(frozen)==0:
            return 0
        p = random.choice ( frozen )
        self.M.masses[p]=random.uniform ( self.M.masses[self.M.LSP], self.M.maxMass )
        ## when unfreezing, nothing can go offshell, right?
        self.removeAllOffshell() ## remove all offshell stuff, normalize all branchings
        # self.M.normalizeAllBranchings() ## adjust everything
        self.M.log ( "Unfreezing %s: m=%f" % ( helpers.getParticleName(p), self.M.masses[p] ) )
        return 1

    def pprint ( self, args ):
        return self.M.pprint ( args )

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

    def checkSwaps ( self ):
        """ check for the usual suspects for particle swaps """
        ## the pairs to check. I put 1000023, 1000025 twice, 
        ## so as to make it possible that chi40 eventually swaps with chi20
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

    def get ( self ):
        """ since the shallowcopy business does not work as expected,
        here is a trivial way to overwrite the original protomodel. 
        use as: protomodel = manipulator.get() 
        """
        return self.M

    #def randomlyTamperWithTheseParticles ( self, pids, r ):
    #    # the critic gave us feedback, the culprits are the given
    #    #    pids. So tamper only with these. r is our usual theoryprediction/ul
    #    #    ratio, and can help us guide how strong a change we have to make.
    #    #
    #    ## we can tamper with the masses, the signal strengths, or
    #    ## the decays, so which is it gonna be? 
    #    u = uniform.random ( 0., 1. )
    #    if u <= 0.333:
    #        ### so we change some masses
    #        pass
    #    if u > 0.333 and u <= 0.666:
    #        #### so we tamper with some ss multipliers
    #        pass
    #    if u > 0.666:
    #        #### ok, its the decays
    #        pass
    #    return

    def setWalkerId ( self, Id ):
        """ set the walker id of protomodel """
        self.M.walkerid = Id

    def swapParticles ( self, pid1, pid2 ):
        """ swaps the two particle ids. The idea being that e.g. ~b1 should be
            lighter than ~b2. If in the walk, ~b1 > ~b2, we just swap the roles 
            of the two particles. """
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
        if not hasattr ( self.M, "bestCombo" ):
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

    #def logBranchings ( self, pid ):
    #    """ discuss the decay channels of pid in log file """
    #    brs = []
    #    for dpid,br in self.M.decays[pid].items():
    #            tmp = self.M.decays[pid][dpid] / S
    #            self.M.decays[pid][dpid] = tmp
    #            if tmp < .99999:
    #                brs.append ( tmp )
    #    if numpy.std ( brs ) > 0.001:
    #        self.M.log( "branchings of %s are at %.2f +/- %.2f" % \
    #                    ( helpers.getParticleName ( pid ), numpy.mean ( brs ), numpy.std ( brs )  ) )


    def normalizeBranchings ( self, pid ):
        """ normalize branchings of a particle, after freezing and unfreezing
            particles. while we are at it, remove zero branchings also. """
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
            self.M.log( "normalize branchings of %s, they are at %.2f +/- %.2f" % ( helpers.getParticleName ( pid ), numpy.mean ( brs ), numpy.std ( brs )  ) )

        ## adjust the signal strength multipliers to keep everything else
        ## as it was
        for pidpair,ssm in self.M.ssmultipliers.items():
            if ssm == 0.:
                self.M.pprint ( "huh, when normalizing we find ssmultipliers of 0? change to 1! S=%.4g" % S )
                ssm=1.
            if pidpair in [ (pid,pid),(-pid,-pid),(-pid,pid),(pid,-pid) ]:
                self.M.ssmultipliers[pidpair]=ssm*S*S
                continue
            if (pid in pidpair) or (-pid in pidpair):
                self.M.ssmultipliers[pidpair]=ssm*S

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
        for k,v in self.M.ssmultipliers.items():
            v = v * self.M.muhat
        self.M.muhat = 1.

    def isInPids ( self, p, dpid ):
        """ is p in dpid, or p equals to dpid? """
        if type(dpid) == tuple:
            return p in dpid
        return p == dpid

    def freezeRandomParticle ( self ):
        """ freezes a random unfrozen particle """
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

    def randomlyChangeSSOfOneParticle ( self ):
        """ randomly change the SS consistently for one pid """
        unfrozenparticles = self.M.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.M.pprint ( "not enough unfrozen particles to change random signal strength" )
            return 0
        p = random.choice ( unfrozenparticles )
        f = random.uniform ( .8, 1.2 )
        self.M.log ( "randomly changing ssms of %s by a factor of %.2f" % \
                     ( helpers.getParticleName ( p ), f ) )
        ssms = []
        for dpd,v in self.M.ssmultipliers.items():
            if p in dpd or -p in dpd:
                newssm = self.M.ssmultipliers[dpd]*f
                self.M.ssmultipliers[dpd]= newssm
                ssms.append ( newssm )
        self.M.log ( " `- %s: ssms are now %.2f+/-%.2f" % ( helpers.getParticleName(p), numpy.mean ( ssms ), numpy.std ( ssms) ) )
        return 1

    def randomlyChangeSignalStrengths ( self ):
        """ randomly change one of the signal strengths """
        if random.uniform(0.,1.)<.8:
            return self.randomlyChangeSSOfOneParticle()
        unfrozenparticles = self.M.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.M.pprint ( "not enough unfrozen particles to change random signal strength" )
            return 0
        p = random.choice ( unfrozenparticles )
        q = random.choice ( unfrozenparticles )
        if self.M.hasAntiParticle(p) and random.uniform(0,1)<.5:
            p = -p
        if self.M.hasAntiParticle(q) and random.uniform(0,1)<.5:
            q = -q
        pair = self.M.toTuple(p,q)
        if not pair in self.M.ssmultipliers:
            self.M.ssmultipliers[pair]=1.
        newSSM=self.M.ssmultipliers[pair]*random.gauss(1.,.1)
        if newSSM == 0.:
            self.M.pprint ( "Huh? ssmultiplier is 0?? Change to 1." )
            newSSM = 1.
        self.M.ssmultipliers[pair]=newSSM
        self.M.log ( "changing signal strength multiplier of %s,%s: %.2f." % (helpers.getParticleName(pair[0]), helpers.getParticleName(pair[1]), newSSM ) )
        return 1

    def randomlyChangeBranchingOfPid ( self, pid ):
        """ randomly change the branching a particle pid """
        openChannels = []
        for dpid,br in self.M.decays[pid].items():
            if not numpy.isfinite ( br ):
                self.M.highlight ( "error", "br of %s/%s is %s. set to zero." % ( pid, dpid, br ) )
                self.M.decays[p][dpid]=0.
            if type(dpid) not in [ tuple, list] and dpid in self.M.unFrozenParticles():
                openChannels.append ( dpid )
            if type(dpid) in [ tuple, list ] and dpid[0] in self.M.unFrozenParticles():
                openChannels.append ( dpid )
        if len(openChannels) < 2:
            self.M.pprint ( "number of open channels of %d is %d: cannot change branchings." % (pid, len(openChannels) ) )
            # not enough channels open to tamper with branchings!
            return 0
        dx =.1/numpy.sqrt(len(openChannels)) ## maximum change per channel
        S=0.
        for i in self.M.decays[pid].keys(): ## openChannels[:-1]:
            oldbr = self.M.decays[pid][i]
            if not numpy.isfinite ( oldbr ):
                self.M.highlight ( "error", "br of %s/%s is %s. set to zero." % ( pid, i, oldbr ) )
                oldbr = 0.
            Min,Max = max(0.,oldbr-dx), min(oldbr+dx,1.)
            br = random.uniform ( Min, Max )
            self.M.decays[pid][i]=br
            S+=br
        if True: # S > 1.: ## correct for too large sums
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

    def randomlyChangeBranchings ( self ):
        """ randomly change the branchings of a single particle """
        unfrozenparticles = self.M.unFrozenParticles( withLSP=False )
        if len(unfrozenparticles)<2:
            self.M.pprint ( "not enough unfrozen particles to change random branching" )
            return 0
        p = random.choice ( unfrozenparticles )
        if not p in self.M.decays.keys():
            self.M.highlight ( "error", "why is %d not in decays?? %s" % ( p, self.M.decays.keys() ) )
            # we dont know about this decay? we initialize with the default!
        return self.randomlyChangeBranchingOfPid ( p )

    def takeRandomMassStep ( self ):
        """ take a random step in mass space for all unfrozen particles """
        dx = 40. / numpy.sqrt ( len(self.M.unFrozenParticles() ) ) / ( self.M.Z + 1. )
        for i in self.M.unFrozenParticles():
            tmp = self.M.masses[i]+random.uniform(-dx,dx)
            if tmp > self.M.maxMass:
                tmp = self.M.maxMass
            if tmp < self.M.masses[self.M.LSP]: ## the LSP is the LSP.
                tmp = self.M.masses[self.M.LSP]
            self.M.masses[i]=tmp
        self.checkSwaps() ## should we really do this here?
        ## now remove all offshell decays, and normalize all branchings
        self.removeAllOffshell() 

if __name__ == "__main__":
    import hiscore
    p = protomodel.ProtoModel( 0 )
    m = Manipulator ( p )
    cheatcode = 1
    m.cheat ( cheatcode )
    m.M.predict( nevents = 20000 )
    print ( "[manipulator] cheat model %d: Z=%2f, rmax=%2f" % ( cheatcode, m.M.Z, m.M.rmax ) )
    print ( "              `- %s" % m.M.description )
