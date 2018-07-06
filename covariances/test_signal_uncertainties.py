#!/usr/bin/env python3

"""
.. module:: testSL
   :synopsis: Test the Simplified Likelihoods

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys
sys.path.insert(0,"../")
import unittest
from smodels.tools.simplifiedLikelihoods import Data, UpperLimitComputer, LikelihoodComputer
from numpy import sqrt, arange, array

class SLTest(unittest.TestCase):
    def createModel(self,n=3, ni=0, deltas_rel = .0 ):
        import model_90 as m9
        S=m9.third_moment.tolist()[ni:n]
        S=None
        D=m9.observed.tolist()[ni:n]
        B=m9.background.tolist()[ni:n]
        # sig=[ x/100. for x in m9.signal.tolist()[ni:n] ]
        sig=[ x for x in m9.signal.tolist()[ni:n] ]
        # S = sum(sig)
        # sig = [ x/S for x in sig ]
        C_=m9.covariance.tolist()
        ncov=int(sqrt(len(C_)))
        C=[]
        for i in range(ni,n):
            C.append ( C_[ni+ncov*i:ncov*i+n] )
        m = Data ( observed=D, backgrounds=B, covariance=C, third_moment=S, 
                    nsignal=sig, name="model%d" % n, deltas_rel=deltas_rel )
        return m

    def printDict ( self, d ):
        s=0.
        for k,v in d.items():
            s+=v
            print ( "%s: %s(%s)" % ( k, v, s ) )

    def testLLHDs(self):
        """ test the evolution of likelihoods """
        m = self.createModel ( 4, 2, 0. )
        m02 = self.createModel ( 4, 2, 0.2 )
        l = LikelihoodComputer ( m )
        ulComp = UpperLimitComputer(ntoys=10000, cl=.95 )
        l02 = LikelihoodComputer ( m02 )
        print ( "m obs=", m.observed )
        print ( "m bg=", m.backgrounds )
        print ( "m signal=", m.nsignal )
        print ( "m UL", ulComp.ulSigma ( m ) )
        print ( "m02 UL", ulComp.ulSigma ( m02 ) )
        print ( "m UL marg", ulComp.ulSigma ( m, marginalize=True ) )
        print ( "m02 UL marg", ulComp.ulSigma ( m02, marginalize=True ) )
        print ( "signals(1)=", m.signals(1) )
        print ( "mu, 0%  (left), 20% (right)" )
        lprof0,lprof2,lmarg0,lmarg2={},{},{},{}
        for mu in arange(0.0,120.,5.):
            lprof0[mu]=l.likelihood ( m.signals(mu) )
            lprof2[mu]=l02.likelihood ( m02.signals(mu) )
            lmarg0[mu]=l.likelihood ( m.signals(mu), marginalize=True )
            lmarg2[mu]=l.likelihood ( m02.signals(mu), marginalize=True )
        lprof0 = self.normalizeDict ( lprof0 )
        lprof2 = self.normalizeDict ( lprof2 )
        lmarg0 = self.normalizeDict ( lmarg0 )
        lmarg2 = self.normalizeDict ( lmarg2 )
        self.plotDicts ( { "prof0": lprof0, "prof2": lprof2, "marg0": lmarg0, "marg2": lmarg2 } )

    def plotDicts ( self, dicts ):
        """ plot the normalized likelihoods """
        import matplotlib.pyplot as plt
        plt.title("likelihoods, as function of $\\mu$" )
        for name,dct in dicts.items():
            style = "-"
            if "marg" in name:
                style = "-."
            col = "r"
            if "0" in name:
                col = "b"
            plt.plot ( dct.keys(), dct.values(), color=col, linestyle=style, label=name )
        plt.xlabel( "$\\mu$")
        plt.legend ()
        plt.savefig ( "signal_uncertainties.png" )
            

    def normalizeDict ( self, dct ):
        s = sum ( dct.values() )
        for k,v in dct.items():
            dct[k]=v/s
        return dct


    def festModel3(self):
        """ take first n SRs of model-90 """
        import time
        print ( "case 1: no signal uncertainty" )
        m = self.createModel ( 3, 1, 0. )
        print ( "model: %s" % m, m.observed, m.backgrounds )
        ulComp = UpperLimitComputer(ntoys=10000, cl=.95 )
        t0=time.time()
        ul = ulComp.ulSigma( m )
        ulm = None
        # ulm = ulComp.ulSigma( m, marginalize=True )
        t1=time.time()
        print ( "ul=%s,%s t=%s" % ( ul, ulm, t1-t0 ) )
        # self.assertAlmostEqual( ul/(2135.66*sum(m.nsignal)), 1.0, 1 )

        print ()
        print ( "case 2: 20 percent signal uncertainty" )
        m2 = self.createModel ( 3, 1, 0.2 )
        ul2 = ulComp.ulSigma( m2 )
        ulm2 = None
        # ulm2 = ulComp.ulSigma( m2, marginalize=True )
        t2=time.time()
        print ( "ul2=%s,%s t=%s" % ( ul2, ulm2, t2-t1 ) )
        #self.assertAlmostEqual( ulProf/(2135.66*sum(m.nsignal)), 1.0, 1 )


if __name__ == "__main__":
    unittest.main()
