#!/usr/bin/python

import os
import numpy as np
import IPython
from matplotlib import rc
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import plotly.plotly as py
import plotly.offline as offline
import plotly.graph_objs as go
from smodels.tools.physicsUnits import GeV, pb
from mpl_toolkits.mplot3d import Axes3D

anaid = "CMS-SUS-13-013"
topo = "T6ttWW"

def map_z2color(zval, colormap, vmin, vmax):
    #map the normalized value zval to a corresponding color in the colormap
    
    if vmin>vmax:
        raise ValueError('incorrect relation between vmin and vmax')
    t=(zval-vmin)/float((vmax-vmin))#normalize val
    R, G, B, alpha=colormap(t)
    return 'rgb('+'{:d}'.format(int(R*255+0.5))+','+'{:d}'.format(int(G*255+0.5))+\
           ','+'{:d}'.format(int(B*255+0.5))+')'   

def tri_indices(simplices):
    #simplices is a numpy array defining the simplices of the triangularization
    #returns the lists of indices i, j, k
    
    return ([triplet[c] for triplet in simplices] for c in range(3))

def plotly_trisurf(x, y, z, simplices, colormap=cm.RdBu, plot_edges=None):
    #x, y, z are lists of coordinates of the triangle vertices 
    #simplices are the simplices that define the triangularization;
    #simplices  is a numpy array of shape (no_triangles, 3)
    #insert here the  type check for input data
    
    points3D=np.vstack((x,y,z)).T
    tri_vertices=map(lambda index: points3D[index], simplices)# vertices of the surface triangles     
    zmean=[np.mean(tri[:,2]) for tri in tri_vertices ]# mean values of z-coordinates of 
                                                      #triangle vertices
    min_zmean=np.min(zmean)
    max_zmean=np.max(zmean)  
    facecolor=[map_z2color(zz,  colormap, min_zmean, max_zmean) for zz in zmean] 
    I,J,K=tri_indices(simplices)
    
    triangles=go.Mesh3d( x=x, y=y, z=z, facecolor=facecolor, i=I, j=J, k=K, name='' )
    
    if plot_edges is None:# the triangle sides are not plotted 
        return go.Data([triangles])
    else:
        #define the lists Xe, Ye, Ze, of x, y, resp z coordinates of edge end points for each triangle
        #None separates data corresponding to two consecutive triangles
        lists_coord=[[[T[k%3][c] for k in range(4)]+[ None]   for T in tri_vertices]  for c in range(3)]
        Xe, Ye, Ze=[reduce(lambda x,y: x+y, lists_coord[k]) for k in range(3)]
        
        #define the lines to be plotted
        lines=go.Scatter3d(x=Xe, y=Ye, z=Ze, mode='lines',
                        line=go.Line(color= 'rgb(50,50,50)', width=2.5)
               )
        return go.Data([triangles, lines])


def getData():
    from smodels.tools.smodelsLogging import setLogLevel
    setLogLevel ( "debug" )
    from smodels.experiment.databaseObj import Database
    from smodels.experiment.txnameObj import TxNameData
    TxNameData._keep_values = True
    home=os.environ["HOME"]
    db = "./tinydb/" 
    #db = "%s/git/smodels-database//" % home
    d=Database ( db )
    results = d.getExpResults ( analysisIDs=[ anaid ], useSuperseded=True, useNonValidated=True )
    # print ( results )
    res=results[0]
    ds=res.datasets[0]
    tx = ds.getTxName ( topo )
    data=tx.txnameData
    return data

def cleanPoints( data ):
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
    return points

def initFig():
    fig=plt.figure ( figsize=(340/72.,340/72.) )
    ax = fig.gca( projection='3d')
    ax.view_init ( 30, -113 )
    plt.title("Delaunay triangulation\n %s (%s)" % (anaid,topo) )
    plt.xlabel ( "m$_\mathrm{mother}$ [GeV]" )
    plt.ylabel ( "m$_\mathrm{inter}$ [GeV]" )
    ax.set_zlabel( "m$_\mathrm{lsp}$ [GeV]" )
    return ax

rc('text',usetex=True)

# print len ( results )
# IPython.embed()

data = getData()
points = cleanPoints ( data )

from scipy.spatial import Delaunay
tri=data.tri

axis = dict(
showbackground=True,
backgroundcolor="rgb(240, 240, 240)",
gridcolor="rgb(255, 255, 255)",      
zerolinecolor="rgb(255, 255, 255)",  
title="$x^2$"
    )

layout = go.Layout(
         title="Delaunay triangulation<br> %s (%s)" % (anaid,topo),
         width=800,
         height=800,
         scene=go.Scene(  
         xaxis=go.XAxis(axis,title="m(mother) [GeV]" ),
         yaxis=go.YAxis(axis,title="$\\gamma$ [2]" ), 
         # zaxis=go.ZAxis(axis,title="m$$_{lsp}$$ [GeV]"), 
         zaxis=axis,
        aspectratio=dict(
            x=1,
            y=1,
            z=0.5
        ),
        )
        )

ts = plotly_trisurf ( points[:,0], points[:,1], points[:,2], tri.simplices.copy(), plot_edges=True ) 
fig = go.Figure(data=ts, layout=layout)

#py.sign_in('WolfgangWaltenberger', '5mBjlg7FEj1awizxm5cR')
#py.iplot(fig, filename='delaunay')

py.image.save_as(fig, filename='delaunay.png')
