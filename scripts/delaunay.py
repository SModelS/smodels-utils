#!/usr/bin/python

import os

anaid = "CMS-SUS-PAS-15-002"
topo = "T1ttttoff"
home=os.environ["HOME"]
db = "%s/git/smodels/test/tinydb/" % home


from smodels.tools.physicsUnits import GeV, pb
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

plt.triplot(points[:,0], points[:,1], tri.simplices.copy(), linewidth=.1 )
plt.plot(points[:,0], points[:,1], 'o', ms=.1 )
corr_anaid = anaid.replace ( "CMS-SUS-PAS", "CMS-PAS-SUS-15-002" )
plt.title("Delaunay triangulation, %s (%s)" % (anaid,topo) )
plt.xlabel ( "m$_\mathrm{mother}$ [GeV]" )
plt.ylabel ( "m$_\mathrm{lsp}$ [GeV]" )
#plt.show()
plt.savefig ( "delaunay.pdf" )
