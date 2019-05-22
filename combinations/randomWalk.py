#!/usr/bin/env python3

""" a first start at the random walk idea """

import random, subprocess

class RandomWalker:
    LSP = 1000022
    def __init__ ( self ):
        """ initialise the walker """
        self.particles = [ 1000001, 2000001, 1000002, 2000002, 1000003, 2000003, 
                  1000004, 2000004, 1000005, 2000005, 1000006, 2000006, 1000011, 
                  2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015, 
                  1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024, 
                  1000037 ]
        self.masses = {}
        for p in self.particles:
            self.masses[p]=1e6
        ## the LSP we need from the beginning
        self.masses[self.LSP]=random.uniform(50,500)

    def frozenParticles ( self ):
        """ returns a list of all particles that can be regarded as frozen
            (ie mass greater than 1e5 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)>1e5:
                ret.append(m)
        return ret

    def unfreezeRandomParticle ( self ):
        """ unfreezes a random frozen particle """
        frozen = self.frozenParticles()
        p = random.choice ( frozen )
        self.masses[p]=random.uniform ( self.masses[self.LSP], 3000. )
        print ( "Unfreezing %d: m=%f" % ( p, self.masses[p] ) )

    def createSLHAFile ( self ):
        """ from the template.slha file, create the slha file of the current
            model. """
        f=open("template.slha")
        lines=f.readlines()
        f.close()
        f=open("current.slha","w")
        for line in lines:
            for m,v in self.masses.items():
                line=line.replace("M%d" % m,"%.1f" % v )
            f.write ( line )
        f.close()

    def walk ( self ):
        self.unfreezeRandomParticle()
        self.createSLHAFile()

if __name__ == "__main__":
    walker = RandomWalker()
    walker.walk()
