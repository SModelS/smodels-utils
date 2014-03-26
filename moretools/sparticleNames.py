#!/usr/bin/env python

"""
.. module:: sparticleNames
        :synopsis: assign sparticle names to pids ( 1000021 <-> ~g, ... )

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

class SParticleNames:
    """ a class that assigns names to sparticles """
    def __init__ ( self ):
        """ Defines the ids and the names """
        self.ids={
            1: "u", 2: "d", 3: "s", 4: "c", 5: "b", 6: "t", 11: "e", 13: "mu", 
            15: "tau", 12: "nu", 14: "nu", 16:"nu", 21: "g", 22: "gamma", 
            24: "W", 23:"Z", 25:"h1", 35: "h2", 36: "a0", 37: "h+", 
            1000001: "~d_L", 2000001: "~d_R",
            1000002: "~d_L", 2000002: "~u_R",
            1000003: "~s_L", 2000003: "~s_R",
            1000004: "~c_L", 2000004: "~c_R",
            1000005: "~b_1", 2000005: "~b_2",
            1000006: "~t_1", 2000006: "~t_2",
            1000011: "~e_L", 1000012: "~nu_eL",
            1000013: "~mu_L", 1000014: "~nu_muL",
            1000015: "~tau_L", 1000016: "~nu_tauL",
            2000011: "~e_R", 2000012: "~nu_eR",
            2000013: "~mu_R", 2000014: "~nu_muR",
            2000015: "~tau_R", 2000016: "~nu_tauR",
            1000021: "~g", 1000022: "~chi10",
            1000024: "~chi1+", 1000023: "~chi20",
            1000037: "~chi2+", 1000025: "~chi30",
            1000035: "~chi40"
        }
        self.names={}
        for (key,value) in self.ids.items():
                self.names[value]=key

    def name ( self, pid ):
        """ get the name for a particle id """
        if not pid in self.ids:
            return "?"
        return self.ids[pid]

    def pid ( self, name ):
        """ get the pid for a particle name """
        if not name in self.names:
            return 0
        return self.names[name]

if __name__ == "__main__":
    """ as a script, we simply print out the paths """
    print "sparticle names"
    namer = SParticleNames()
    ctr=0
    for (key,value) in namer.ids.items():
       ctr+=1
       print "%7d %8s   |" % (key,value),
       if ctr==3:
         print
         ctr=0
