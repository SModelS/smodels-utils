#!/usr/bin/python

import os
import numpy as np
import IPython
from matplotlib import rc
import matplotlib.pyplot as plt
from smodels.base.physicsUnits import GeV, pb
from mpl_toolkits.mplot3d import Axes3D

anaid = "CMS-SUS-PAS-15-002"
topo = "T1ttttoff"
anaid = "ATLAS-SUSY-2013-23"
topo = "TChiWH"
anaid = "ATLAS-CONF-2013-007"
topo = "T5tttt"

def getData():
    from smodels.base.smodelsLogging import setLogLevel
    setLogLevel ( "debug" )
    from smodels.experiment.databaseObj import Database
    home=os.environ["HOME"]
    db = f"{home}/git/smodels/test/tinydb/"
    # db = "%s/git/smodels-database//" % home
    d=Database ( db )
    results = d.getExpResults ( analysisIDs=[ anaid ], useSuperseded=True, useNonValidated=True )
    # print ( results )
    res=results[0]
    ds=res.datasets[0]
    tx = ds.getTxName ( topo )
    data=tx.txnameData
    return data


fig=plt.figure ( figsize=(340/72.,340/72.) )
ax = fig.gca( projection='3d')

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

#ax.plot_wireframe (points[:,0], points[:,1], points[:,2] ) ## tri.simplices.copy(), linewidth=.4 )
ax.plot_trisurf ( points[:,0], points[:,1], points[:,2], triangles=tri.simplices.copy(), color="#ffddff", \
                  shade=False, linewidth=.4, antialiased=True, edgecolors='r', alpha=0 )
ax.scatter(points[:,0], points[:,1], points[:,2], 'bo' )
ax.view_init ( 30, -113 )
corr_anaid = anaid.replace ( "CMS-SUS-PAS", "CMS-PAS-SUS-15-002" )
plt.title(f"Delaunay triangulation\n {anaid} ({topo})" )
plt.xlabel ( "m$_\mathrm{mother}$ [GeV]" )
plt.ylabel ( "m$_\mathrm{inter}$ [GeV]" )
ax.set_zlabel( "m$_\mathrm{lsp}$ [GeV]" )
#plt.show()
plt.savefig ( "delaunay3d.pdf" )
