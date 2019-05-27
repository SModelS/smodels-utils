#!/usr/bin/env python3

""" Class that encapsulates a BSM model. """

import random, numpy, tempfile
from smodels.tools.xsecComputer import XSecComputer, LO

class Model:
    """ encodes on theoretical model, i.e. the particles, their masses, their
        branchings.
    """
    LSP = 1000022 ## the LSP is hard coded
    def __init__ ( self, walkerid ):
        self.walkerid = walkerid
        self.maxMass = 2400. ## maximum masses we consider
        self.step = 0 ## count the steps
        self.particles = [ 1000001, 2000001, 1000002, 2000002, 1000003, 2000003,
                  1000004, 2000004, 1000005, 2000005, 1000006, 2000006, 1000011,
                  2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015,
                  1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024,
                  1000037 ]
        self.names = { 1000001: "~q", 2000001: "~q", 1000002: "~q",
                       2000002: "~qR", 1000003: "~q", 2000003: "~qR",
                       1000004: "~c", 2000004: "~cR", 1000005: "~b",
                       2000005: "~bR", 1000006: "~t", 2000006: "~tR",
                       1000011: "~e", 2000011: "~eR", 1000012: "~nu",
                       1000013: "~mu", 2000013: "~muR", 1000014: "~nu",
                       1000015: "~tau", 2000015: "~tauR", 1000016: "~nu",
                       1000021: "~g", 1000022: "~chi10", 1000023: "~chi20",
                       1000025: "~chi30", 1000035: "~chi40", 1000024: "~chi1+",
                       1000037: "~chi2+" }
        self.onesquark = False ## only one light squark
        self.twosquark = True  ## a few squarks, but not all
        if self.onesquark:
            self.particles = [ 1000001, 1000005, 1000006, 1000011, 1000012,
                      1000013, 1000014, 1000015,  1000016, 1000021, 1000022,
                      1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "template_1q.slha"
        if self.twosquark:
            self.particles = [ 1000001, 1000002, 1000004, 1000005, 1000006, 1000011, 
                      1000012, 1000013, 1000014, 1000015, 1000016, 1000021, 1000022,
                      1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "template.slha"
        self.possibledecays = {} ## list all possible decay channels
        self.decays = {} ## the actual branchings
        self.masses = {}
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
        self.computePrior()

    def pprint ( self, *args ):
        """ logging """
        print ( "[model:%d] %s" % (self.walkerid, " ".join(map(str,args))) )

    def frozenParticles ( self ):
        """ returns a list of all particles that can be regarded as frozen
            (ie mass greater than 1e5 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)>1e5:
                ret.append(m)
        return ret

    def priorTimesLlhd( self ):
        return self.prior * self.llhd

    def unFrozenParticles ( self ):
        """ returns a list of all particles that can be regarded as unfrozen
            (ie mass less than 5e3 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)<5e3:
                ret.append(m)
        return ret

    def unfreezeRandomParticle ( self ):
        """ unfreezes a random frozen particle """
        frozen = self.frozenParticles()
        if len(frozen)==0:
            return 0
        p = random.choice ( frozen )
        self.masses[p]=random.uniform ( self.masses[Model.LSP], self.maxMass )
        self.pprint ( "Unfreezing %s: m=%f" % ( self.getParticleName(p), self.masses[p] ) )
        return 1

    def getParticleName ( self, p ):
        sp = str(p)
        if p in self.names:
            sp = self.names[p]
        return sp

    def freezeRandomParticle ( self ):
        """ freezes a random unfrozen particle """
        unfrozen = self.unFrozenParticles()
        if len(unfrozen)<3:
            return 0 ## freeze only if at least 3 unfrozen particles exist
        unfrozen.remove ( Model.LSP )
        p = random.choice ( unfrozen )
        self.masses[p]=1e6
        self.pprint ( "Freezing %s." % ( self.getParticleName(p) ) )
        return 1

    def freezeMostMassiveParticle ( self ):
        """ freezes the most massive unfrozen particle """
        unfrozen = self.unFrozenParticles()
        if len(unfrozen)<3:
            return 0 ## freeze only if at least 3 unfrozen particles exist
        unfrozen.remove ( self.LSP )
        p = random.choice ( unfrozen )
        self.masses[p]=1e6
        self.pprint ( "Freezing %s." % ( self.getParticleName(p) ) )
        return 1

    def randomlyChangeBranchings ( self ):
        """ randomly change the branchings of a single particle """
        unfrozenparticles = self.unFrozenParticles()
        if len(unfrozenparticles)<2:
            self.pprint ( "not enough unfrozen particles to change random branching" )
            return 0
        unfrozenparticles.remove ( Model.LSP )
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
        for i in openChannels[:-1]:
            oldbr = self.decays[p][i]
            br = oldbr+random.uniform(-dx,dx)
            if br < 0.: br = 0.
            if br > 1.: br = 1.
            self.decays[p][i]=br
            S+=br
        for i in self.frozenParticles(): ## frozen particles have 0 branchings
            self.decays[p][i]=0.
        self.decays[p][ openChannels[-1] ] = 1. - S

        self.pprint ( "changed branchings of %s." % self.getParticleName(p) )
        # print ( "[walk] we have %d open channels" % nChannels )
        for dpid,br in self.decays[p].items():
            if dpid in self.unFrozenParticles():
                openChannels.append ( dpid )
            # print ( "[walk] new `- pid,br", dpid, br, dpid in self.unFrozenParticles() )
        return 1

    def takeRandomMassStep ( self ):
        """ take a random step in mass space for all unfrozen particles """
        dx = 20. / numpy.sqrt ( len(self.unFrozenParticles() ) )
        for i in self.unFrozenParticles():
            tmp = self.masses[i]+random.uniform(-dx,dx)
            if tmp > self.maxMass:
                tmp = self.maxMass
            if tmp < 10.:
                tmp = 10.
            self.masses[i]=tmp

    def createSLHAFile ( self, outputSLHA=None ):
        """ from the template.slha file, create the slha file of the current
            model.
        :param outputSLHA: if not None, write into that file. else, write into
            currentSLHA file.
        """
        f=open( self.templateSLHA )
        lines=f.readlines()
        f.close()
        if outputSLHA == None:
            outputSLHA = self.currentSLHA
        if not hasattr ( self, "currentSLHA" ):
            self.currentSLHA = tempfile.mktemp(prefix=".cur",suffix=".slha",dir="./")
        f=open(outputSLHA,"w")
        for line in lines:
            for m,v in self.masses.items():
                line=line.replace("M%d" % m,"%.1f" % v )
                for dpid,dbr in self.decays[m].items():
                    line=line.replace("D%d_%d" % ( m, dpid), "%.1f" % dbr )
            f.write ( line )
        f.close()

    def computeXSecs ( self ):
        """ compute xsecs for current.slha """
        # print ( "[walk] computing xsecs for %s" % self.currentSLHA )
        computer = XSecComputer ( LO, 2000, 6 )
        computer.computeForOneFile ( [8,13], self.currentSLHA,
                unlink=True, lOfromSLHA=False, tofile=True )

    def computePrior ( self ):
        """ compute the prior for the current model.
        """
        self.prior = 1. / ( len(self.unFrozenParticles()))

