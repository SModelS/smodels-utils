#!/usr/bin/env python

"""
.. module:: sparticleNames
        :synopsis: assign sparticle names to pids ( 1000021 <-> ~g, ... ),
        pids to names, categorizes particles, etc.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function

class SParticleNames:
    """ a class that assigns names to sparticles """
    def __init__ ( self ):
        """ Defines the ids and the names """
        self.ids={
            1: "u", 2: "d", 3: "s", 4: "c", 5: "b", 6: "t", 11: "e-", 13: "mu-", 
            15: "tau-", 12: "nu", 14: "nu", 16:"nu", 21: "g", 22: "gamma", 
            24: "W", 23:"Z", 25:"h1", 35: "h2", 36: "a0", 37: "h+", 
            -15: "tau+", -13: "mu+", -11: "e:", -37: "h-", -24: "W-",
            -23: "Z", -25: "h1", -35: "h2", -36: "a0", -22: "gamma",
            -21: "g", -16: "nu", -14: "nu", -12: "nu", -1: "u",
            -2: "d", -3: "s", -4: "c", -5: "b", -6: "t",
            1000001: "~d_L", 2000001: "~d_R",
            1000002: "~u_L", 2000002: "~u_R",
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
            1000035: "~chi40",
            -1000001: "~d_L^*", -2000001: "~d_R^*",
            -1000002: "~u_L^*", -2000002: "~u_R^*",
            -1000003: "~s_L^*", -2000003: "~s_R^*",
            -1000004: "~c_L^*", -2000004: "~c_R^*",
            -1000005: "~b_1^*", -2000005: "~b_2^*",
            -1000006: "~t_1^*", -2000006: "~t_2^*",
            -1000011: "~e_L^*", -1000012: "~nu_eL",
            -1000013: "~mu_L^*", -1000014: "~nu_muL",
            -1000015: "~tau_L^*",- 1000016: "~nu_tauL",
            -2000011: "~e_R^*", -2000012: "~nu_eR",
            -2000013: "~mu_R^*", -2000014: "~nu_muR",
            -2000015: "~tau_R^*", -2000016: "~nu_tauR",
            -1000021: "~g^*", -1000022: "~chi10",
            -1000024: "~chi1-", -1000023: "~chi20",
            -1000037: "~chi2-",- 1000025: "~chi30",
        }
        self.names={}
        for (key,value) in self.ids.items():
                self.names[value]=key

    def name ( self, pid ):
        """ get the name for a particle id """
        if not pid in self.ids and not abs(pid) in self.ids:
            return str(pid)
        if not pid in self.ids:
            return self.ids[abs(pid)]
        return self.ids[pid]

    def pid ( self, name ):
        """ get the pid for a particle name """
        if not name in self.names:
            return 0
        return self.names[name]

    def has ( self, i ):
        """ do we have particle? can be pid or name """
        if i in self.names: return True
        if i in self.ids: return True
        return False

    def particleType ( self, pid ):
        """ categorizes sparticles """
        q=abs(pid)
        if q>1000000 and q<1000005:
            return "q"
        if q>2000000 and q<2000005:
            return "q"
        if q in [ 1000005, 2000005 ]:
            return "b"
        if q in [ 1000006, 2000006 ]:
            return "t"
        if q==1000021:
            return "g"
        if q in [ 1000022, 1000023, 1000025, 1000035, 1000024, 1000037 ]:
            return "n"
        if q in [ 1000011, 1000013, 1000015, 2000011, 2000013, 2000015 ]:
            return "l"
        if q in [ 1000012, 1000014, 1000016, 2000012, 2000014, 2000016 ]:
            return "l"
        return str(q)

    def shortName ( self, productiontuple ):
        """ assign a particle category to a tuple of two particle pids """
        p1,p2=abs( productiontuple[0] ),abs( productiontuple[1] )
        # p1,p2= productiontuple
        q1,q2=self.particleType ( p1 ), self.particleType ( p2 )
        if q1>q2: q1,q2=q2,q1 ## swap, give a canonical order
        return q1+q2

    def longName ( self, letter ):
        """ gives long names to particle categories """
        if letter=="l": return "slepton"
        if letter=="n": return "weakino"
        if letter=="q": return "squark"
        if letter=="t": return "stop"
        if letter=="b": return "sbottom"
        if letter=="g": return "gluino"
        return "?"

    def tilde ( self, text ):
        """ put a tilde over text """
        return "<math display='inline'><mover><mi>%s</mi><mo stretchy='true'>~</mo></mover></math>" % text

    def sub ( self, text ):
        return "<sub>"+text+"</sub>"

    def sup ( self, text ):
        return "<sup>"+text+"</sup>"

    def toHtml ( self, name ):
        """ translate particle names to html code """
        #if name=="~chi2+": 
        #    name=self.tilde("&chi;")+"xxx" ## sup("+")+"2"#+sub("2")
        #if name=="~chi1+": return self.tilde("&chi;")+"1+" ## sup("+")+"2"#+sub("2")
        #if name=="~chi30": return self.tilde("&chi;")+sup("0")#+sub("2")
        name=name.replace("_eL","<sub>eL</sub>")
        name=name.replace("_muL","<sub>muL</sub>")
        name=name.replace("_tauL","<sub>tauL</sub>")
        name=name.replace("chi10","chi<sub>1</sub><sup>0</sup>")
        name=name.replace("chi20","chi<sub>2</sub><sup>0</sup>")
        name=name.replace("chi30","chi<sub>3</sub><sup>0</sup>")
        name=name.replace("chi40","chi<sub>4</sub><sup>0</sup>")
        name=name.replace("chi50","chi<sub>5</sub><sup>0</sup>")
        name=name.replace("chi1+","chi<sub>1</sub><sup>+</sup>")
        name=name.replace("chi2+","chi<sub>2</sub><sup>+</sup>")
        name=name.replace("chi3+","chi<sub>3</sub><sup>+</sup>")
        name=name.replace("chi1-","chi<sub>1</sub><sup>-</sup>")
        name=name.replace("chi2-","chi<sub>2</sub><sup>-</sup>")
        name=name.replace("chi3-","chi<sub>3</sub><sup>-</sup>")
        name=name.replace("chi","&chi;")
        name=name.replace("nu","&nu;")
        name=name.replace("mu","&mu;")
        name=name.replace("tau","&tau;")
        name=name.replace("_L","<sub>L</sub>")
        name=name.replace("uL","u<sub>L</sub>")
        name=name.replace("dL","d<sub>L</sub>")
        name=name.replace("cL","c<sub>L</sub>")
        name=name.replace("sL","s<sub>L</sub>")
        name=name.replace("uR","u<sub>R</sub>")
        name=name.replace("dR","d<sub>R</sub>")
        name=name.replace("cR","c<sub>R</sub>")
        name=name.replace("sR","s<sub>R</sub>")
        name=name.replace("_R","<sub>R</sub>")
        name=name.replace("_1","<sub>1</sub>")
        name=name.replace("A0","A<sup>0</sup>")
        name=name.replace("H+","H<sup>+</sup>")
        name=name.replace("_2","<sub>2</sub>")
        name=name.replace("b1","b<sub>1</sub>")
        name=name.replace("b2","b<sub>2</sub>")
        name=name.replace("t1","t<sub>1</sub>")
        name=name.replace("t2","t<sub>2</sub>")
        name=name.replace("^*","<sup>*</sup>")
        #name=name.replace("+","<sup>+</sup>")
        if name.find("~")==0: 
            if name.find("<su")==-1: 
                name=self.tilde(name[1:])
            else:
                pos=name.find("<su")
                name=self.tilde(name[1:pos])+name[pos:]
        # print name,"<br>"
        return "<nobr>"+name+"</nobr>"


if __name__ == "__main__":
    """ as a script, we simply print out the paths """
    print ( "sparticle names" )
    namer = SParticleNames()
    ctr=0
    for (key,value) in namer.ids.items():
       ctr+=1
       print ( "%8d %8s   |" % (key,value), end="" )
       if ctr==3:
         print
         ctr=0
