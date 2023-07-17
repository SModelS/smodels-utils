#!/usr/bin/python

import os

anaid = "CMS-SUS-PAS-15-002"
topo = "T1ttttoff"
home=os.environ["HOME"]
db = "%s/git/smodels/test/tinydb/" % home


from smodels.base.physicsUnits import GeV, pb
from smodels.experiment.databaseObj import Database
import numpy as np
import IPython
from matplotlib import rc
import matplotlib.pyplot as plt

rc('text',usetex=True)

d=Database ( db )
results = d.getExpResults ( analysisIDs=[ anaid ] )
res=results[0]
ds=res.datasets[0]
tx = ds.getTxName ( topo )
data=tx.txnameData
# print len ( results )
# IPython.embed()

values = eval ( data.value )
ptsunits = [ x[0] for x in values ]
Points = []
for p in ptsunits:
    t=[]
    for v in p:
        for v2 in v:
            t.append ( v2.asNumber(GeV) )
    Points.append ( t )
points = np.array ( Points )
# points = np.array([[0, 0], [0, 1.1], [1, 0], [1, 1]])
from scipy.spatial import Delaunay
#tri = Delaunay(points)
tri=data.tri

delta_x = [ data.delta_x.tolist()[0][x] for x in [ 0, 2 ] ]

#print "dx=",delta_x
print "V=",data._V
# print "points",type(points),points

pts = {}
for i in points:
    tpl = (i[0], i[2]) 
    if not tpl in pts:
        pts [ tpl ] = 0
    pts[tpl]+=1
    # pts.append ( (i[0], i[2]) )

k=500.
# pt2 = ( delta_x[0] + k * data._V[0][0], delta_x[0] + k * data._V[2][0] )

fig=plt.figure ( figsize=(340/72.,340/72.) )

# plt.triplot(points[:,0], points[:,1], tri.simplices.copy(), linewidth=.1 )
# plt.plot( (delta_x[0],pt2[0]), (delta_x[1],pt2[1]) , 'r-', ms=2.5 )
for t,s in pts.items():
    plt.plot( t[0], t[1], 'bo', markeredgecolor="white", alpha=.5, ms=s*1.1)
# plt.plot(points[:,0], points[:,2], 'o', ms=2.5 )
plt.plot( delta_x[0], delta_x[1], 'rp', ms=6.5 )
ax=plt.axes()
ax.arrow( delta_x[0],delta_x[1], k * data._V[0][0], k * data._V[2][0]  , head_width=35., head_length=30., width=5., fc='r', ec='r' )
ax.arrow( delta_x[0],delta_x[1], -.3*k * data._V[0][2], -.3* k * data._V[2][2]  , head_width=35., head_length=30., width=5., fc='g', ec='g' )
corr_anaid = anaid.replace ( "CMS-SUS-PAS", "CMS-PAS-SUS-15-002" )
plt.title("Principal component analysis, %s (%s)" % (anaid,topo) )
plt.xlabel ( "m$_1$ (first mother) [GeV]" )
plt.ylabel ( "M$_1$ (second mother) [GeV]" )
# plt.ylabel ( "m$_\mathrm{lsp}$ [GeV]" )
#plt.show()
plt.savefig ( "Pca.pdf" )
