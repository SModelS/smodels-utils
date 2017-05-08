#!/usr/bin/python

import os
import numpy as np
import IPython
from matplotlib import rc
import matplotlib.pyplot as plt
from smodels.tools.physicsUnits import GeV, pb

anaid = "CMS-SUS-PAS-15-002"
topo = "T1ttttoff"
anaid = "ATLAS-SUSY-2013-23"
topo = "TChiWH"
#anaid = "CMS-SUS-13-013"
#topo = "T6ttWW"

def getData():
    from smodels.experiment.databaseObj import Database
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

plt.triplot(points[:,0], points[:,1], tri.simplices.copy(), linewidth=.4 )
plt.plot(points[:,0], points[:,1], 'bo', markeredgecolor='#0000aa', ms=2.0 )
corr_anaid = anaid.replace ( "CMS-SUS-PAS", "CMS-PAS-SUS-15-002" )
plt.title("Delaunay triangulation, %s (%s)" % (anaid,topo) )
plt.xlabel ( "m$_\mathrm{mother}$ [GeV]" )
plt.ylabel ( "m$_\mathrm{lsp}$ [GeV]" )
#plt.show()
plt.savefig ( "delaunay.pdf" )
