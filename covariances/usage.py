#!/usr/bin/python

from __future__ import print_function
from smodels.tools.SimplifiedLikelihoods import Model, UpperLimitComputer, fb, LikelihoodComputer
# from SimplifiedLikelihoods import Model, UpperLimitComputer

C=[ 18774.2, -2866.97, -5807.3, -4460.52, -2777.25, -1572.97, -846.653, -442.531,
   -2866.97, 496.273, 900.195, 667.591, 403.92, 222.614, 116.779, 59.5958,
   -5807.3, 900.195, 1799.56, 1376.77, 854.448, 482.435, 258.92, 134.975,
   -4460.52, 667.591, 1376.77, 1063.03, 664.527, 377.714, 203.967, 106.926,
   -2777.25, 403.92, 854.448, 664.527, 417.837, 238.76, 129.55, 68.2075,
   -1572.97, 222.614, 482.435, 377.714, 238.76, 137.151, 74.7665, 39.5247,
   -846.653, 116.779, 258.92, 203.967, 129.55, 74.7665, 40.9423, 21.7285,
   -442.531, 59.5958, 134.975, 106.926, 68.2075, 39.5247, 21.7285, 11.5732]
data=[1964,877,354,182,82,36,15,11]
backgrounds=[2006.4,836.4,350.,147.1,62.0,26.2,11.1,4.7]
signals=[47,29.4,21.1,14.3,9.4,7.1,4.7,4.3 ]
efficiencies=[.47,.29,.21,.14,.094,.071,.047,.043 ]

m=Model ( data=data,
          backgrounds=backgrounds,
          covariance= C,
          skewness = None,
          efficiencies=efficiencies,
          name="CMS-NOTE-2017-001 model" )

LC = LikelihoodComputer ( m )

print ( "likelihood for no signal, marginalizing:", LC.likelihood([0.]*m.n, marginalize=True ) )
signal = [ 10.*x for x in efficiencies ]
print ( "likelihood for given signal, profiling:", LC.likelihood(signal, marginalize=False ) )

ulComp = UpperLimitComputer ( lumi = 1. / fb, cl=.95 )

## compute upper limit on production cross section with profiled nuisances
ulProf = ulComp.ulSigma ( m, marginalize=False )
print ( "Profiled UL=", ulProf )

## compute upper limit on production cross section with marginalized nuisances,
## 5000 toys
ulMarg = ulComp.ulSigma ( m, marginalize=True, toys=5000 )
print ( "Marginalized UL=", ulMarg )
