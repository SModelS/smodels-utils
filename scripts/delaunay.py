#!/usr/bin/python

import os
import IPython
import numpy as np
import IPython
from matplotlib import rc
import matplotlib.pyplot as plt
from smodels.tools.physicsUnits import GeV, pb
from smodels.experiment.databaseObj import Database
from smodels.experiment.txnameObj import TxNameData
from smodels.tools.smodelsLogging import setLogLevel, logger
from scipy.spatial import ConvexHull
import pickle
# setLogLevel ( "debug" )

TxNameData._keep_values = True

anaid = "CMS-PAS-SUS-15-002"
topo = "T1ttttoff"
# topo = "T1hacked"
#anaid = "ATLAS-SUSY-2013-23"
#topo = "TChiWH"
#anaid = "CMS-SUS-13-013"
#topo = "T6ttWW"

def getData():
    home=os.environ["HOME"]
    db = "./tinydb/"
    d=Database ( db )
    results = d.getExpResults ( analysisIDs=[ anaid ] )
    res=results[0]
    ds=res.datasets[0]
    tx = ds.getTxName ( topo )
    data=tx.txnameData
    return data


fig=plt.figure ( figsize=(340/72.,340/72.) )


rc('text',usetex=True)

# print len ( results )
# IPython.embed()

data = getData()
values = eval ( data.value )

ptsunits = [ x[0] for x in values ]
xsecs = [ x[1].asNumber(pb) for x in values ]

"""
RemovePoints = [ 11 ]
for r in RemovePoints:
    xsecs.pop ( r )
    ptsunits.pop ( r )
"""

Points = []
for p in ptsunits:
    t=[]
    for v in p:
        for v2 in v:
            t.append ( v2.asNumber(GeV) )
    Points.append ( t[:2] )
points = np.array ( Points )
# points = np.array([[0, 0], [0, 1.1], [1, 0], [1, 1]])
from scipy.spatial import Delaunay
#tri = Delaunay(points)
tri=data.tri
hull = tri.convex_hull

zeroes = [] ## all indices with zero xsecs
zero_Points = [] ## points with zero xsec
for i,x in enumerate (xsecs ):
    if x < 1e-9:
        zeroes.append ( i )
        zero_Points.append ( Points[i] )

# print ( "hull: %s" % hull.simplices )

def allZeroSimplex ( simplex, zeroes ):
    """ does a simplex have only zeroes? """
    for idx in simplex:
        if idx not in zeroes:
            return False
    return True
    
for s in tri.simplices:
    if allZeroSimplex ( s, zeroes ):
        print ( "simplex %s is all zeroes." % s )

for i in zeroes:
#for i in [ 11 ]:
    inHull = i in hull
    ct = 0
    allSimplicesZero=True
    for s in tri.simplices:
        if i in s:
            ct+=1
            if not allZeroSimplex ( s, zeroes ):
                allSimplicesZero = False
    if allSimplicesZero:
        print ( "we can remove point %d!!!" % i )

    print ( "point %d: inHull: %d. in %d simplices." % ( i, inHull, ct ) )

zero_points = np.array  ( zero_Points )
# IPython.embed()

plt.triplot(points[:,0], points[:,1], tri.simplices.copy(), linewidth=.4 )
plt.plot(points[:,0], points[:,1], 'bo', markeredgecolor='#0000aa', ms=2.0 )
plt.plot(zero_points[:,0], zero_points[:,1], 'bo', markeredgecolor='#00aa00', ms=3.0 )

for simplex in hull:
    plt.plot(points[simplex, 0], points[simplex, 1], 'r--')

plt.title("Delaunay triangulation, %s (%s)" % (anaid,topo) )
plt.xlabel ( "m$_\mathrm{mother}$ [GeV]" )
plt.ylabel ( "m$_\mathrm{lsp}$ [GeV]" )
#plt.show()
for i,(point,xsec) in enumerate ( zip ( points,xsecs ) ):
    ## add the xsecs to the points, as text
    col = "k"
    if i in zeroes:
        col="g"
    if i in hull:
        col="r"
    plt.text ( point[0], point[1], "%.2f" % xsec, fontdict = { "color": col} )
plt.savefig ( "delaunay.pdf" )
