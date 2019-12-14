#!/usr/bin/env python3

""" Class that encapsulates the manipulations we perform on the protomodels,
    so that the protomodel class is a data-centric class, and this one 
    an algorithm-centric class """

import protomodel
import copy

class Manipulator:
    """ contains the protomodel manipulation algorithms. """
    def __init__ ( self, protomodel ):
        self.M = copy.copy ( protomodel  ) # shallow copy

    def checkForOffshell ( self ):
        """ check for offshell decays
        :returns: a list of tuples (motherpid, daughterpid) """
        offshell = []
        for pid,decays in self.M.decays.items():
            mmother = self.M.masses[pid]
            if mmother > 9e5:
                continue
            for dpid,dbr in decays.items():
                mdaughter = 1e+6
                if dpid in self.M.masses:
                    mdaughter = self.M.masses[dpid]
                if mdaughter > mmother and dbr > 1e-5:
                    self.log ( "decay %d -> %s is offshell (%.3f)" % \
                               ( pid, dpid, dbr ) )
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
            if self.M.masses[pids[1]] > 9e4:
                # we dont check for frozen particles
                continue
            #if self.M.masses[pids[0]] > 9e4:
                # we dont check for frozen particles
            #    continue
            if self.M.masses[pids[0]] > self.M.masses[pids[1]]:
                self.pprint ( "particle swap %d <-> %d" % ( pids[0], pids[1] ) )
                self.swapParticles ( pids[0],pids[1] )

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
            self.highlight ( "red", "error, i was asked to swap %d and %d. but one of them isnt in the mass tuple" % ( pid1, pid2 ) )
            return
        ## swap mothers in the decays dictionary
        if pid1 in self.M.decays and pid2 in self.M.decays:
            s = self.M.decays[pid1]
            self.M.decays[pid1] = self.M.decays[pid2]
            self.M.decays[pid2] = s
        else:
            self.highlight ( "red", "error, i was asked to swap %d and %d. but one of them isnt in the decays tuple" % ( pid1, pid2 ) )
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
        self.M.ssmultipliers = newSSMultipliers

    def removeAllOffshell ( self ):
        """ remove all offshell decays, renormalize all branchings """
        offshell = self.checkForOffshell()
        for (mpid,dpid) in offshell:
            assert ( mpid in self.M.decays )
            assert ( dpid in self.M.decays[mpid] )
            self.M.decays[mpid][dpid]=0.
            # self.M.decays[mpid].pop ( dpid ) dont pop, we need it!
        self.normalizeAllBranchings()


    def normalizeBranchings ( self, pid ):
        """ normalize branchings of a particle, after freezing and unfreezing
            particles. while we are at it, remove zero branchings also. """
        # unfrozen = self.unFrozenParticles( withLSP = False )
        S=0.
        if pid in self.M.decays:
            for dpid,br in self.M.decays[pid].items():
                S+=br
        if S == 0.:
            nitems = len ( self.M.decays[pid].items() )
            for dpid,br in self.M.decays[pid].items():
                br = random.gauss ( 1. / nitems, numpy.sqrt ( .5 / nitems )  )
                br = min ( 0., br )
                self.M.decays[pid][dpid]=br
                S+=br
            self.M.pprint ( "total sum of branchings for %d is %.2f!! Number of decay channels in dictionary %d" % (pid,S,len(self.M.decays[pid])) )
        for dpid,br in self.M.decays[pid].items():
                tmp = self.M.decays[pid][dpid]
                self.M.decays[pid][dpid] = tmp / S

        # while we are at, remove also the zeroes
        if False: # nah dont, we need the zeroes for bookkeeping!
            for mpid,decays in self.M.decays.items():
                newdecays = {}
                for dpid,dbr in decays.items():
                    if dbr > 1e-10:
                        newdecays[dpid]=dbr
                self.M.decays[mpid] = newdecays

        ## remove also mothers with no decays at all
        newDecays = {}
        for mpid,decays in self.M.decays.items():
            if len(decays)>0:
                newDecays[mpid] = decays
        self.M.decays = newDecays

        ## adjust the signal strength multipliers to keep everything else
        ## as it was
        ## self.checkSSMultipliers()
        for pidpair,ssm in self.M.ssmultipliers.items():
            if (pid in pidpair) or (-pid in pidpair):
                if ssm == 0.:
                    self.pprint ( "huh, when normalizing we find ssmultipliers of 0? change to 1! S=%.4g" % S )
                    ssm=1.
                self.M.ssmultipliers[pidpair]=ssm*S
        self.M.checkSSMultipliers()

    def normalizeAllBranchings ( self ):
        """ normalize all branchings, after freezing or unfreezing particles """
        for pid in self.protomodel.masses.keys():
            if not pid == self.LSP:
                self.normalizeBranchings ( pid )

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
        self.M.masses[pid]=1e6
        self.normalizeAllBranchings() ## adjust everything
        self.log ( "Freezing most massive %s (%.1f)" % ( helpers.getParticleName(pid), minmass ) )
        return 1



if __name__ == "__main__":
    import hiscore
    p = ProtoModel( 0 )
    m = Manipulator ( p )
    m.normalizeAllBranchings()
