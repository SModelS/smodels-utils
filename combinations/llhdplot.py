#!/usr/bin/env python3

""" the plotting script for the llhd scans """

import pickle
import IPython
import numpy as np
from matplotlib import pyplot as plt

def load ( picklefile ):
    """ load dictionary from picklefile """
    f = open ( picklefile, "rb" )
    llhds = pickle.load ( f )
    f.close()
    return llhds

def getAnaStats ( D ):
    """ given the likelihood dictionaries D, get
        stats of which analysis occurs how often """
    anas = {}
    for masspoint in D:
        m1,m2,llhds=masspoint[0],masspoint[1],masspoint[2]
        for k,v in llhds.items():
            if not k in anas.keys():
                anas[k]=0
            anas[k]=anas[k]+1
    return anas

def getHash ( m1, m2 ):
    return int(1e3*m1) + int(1e0*m2)

def plotOneAna ( masspoints, ana, interactive ):
    """ plot for one analysis """
    x,y=set(),set()
    L = {}
    minXY=0.,0.,float("inf")
    for masspoint in masspoints:
        m1,m2,llhds=masspoint[0],masspoint[1],masspoint[2]
        x.add ( m1 )
        y.add ( m2 )
        zt = 0.
        if ana in llhds:
            zt = - np.log(llhds[ana] )
            if zt < minXY[2]:
                minXY=(m1,m2,zt)
        h = getHash(m1,m2)
        L[h]=zt
    x,y=list(x),list(y)
    X, Y = np.meshgrid ( x, y )
    Z = 0.*X
    for irow,row in enumerate(Z):
        for icol,col in enumerate(row):
            h = getHash(x[icol],y[irow])
            Z[irow,icol]=L[h]
    cont = plt.contourf ( X, Y, Z )
    cbar = plt.colorbar( cont ) # , ticks=lvls, format="%.4f")
    ax = plt.axes()
    ax.scatter(X, Y, marker="+", s=1, color="black")
    print ( "minXY", minXY )
    ax.scatter( [ minXY[0] ], [ minXY[1] ], marker="*", s=6, color="red")
    plt.title ( "-ln L, %s" % ana )
    plt.xlabel ( "%s" % pid1 )
    plt.ylabel ( "%s" % pid2 )
    # plt.contour ( X, Y, Z )
    plt.savefig ( "plt%s.png" % ana )
    if interactive:
        IPython.embed()

def plot ( pid1, pid2, analysis, interactive ):
    """ do your plotting """
    picklefile = "mp%d%d.pcl" % ( pid1, pid2 )
    masspoints = load ( picklefile )
    stats = getAnaStats( masspoints )
    plotOneAna ( masspoints, analysis, interactive )


if __name__ == "__main__":
    pid1,pid2 = 1000021,1000022
    pid1,pid2 = 2000006,1000022
    import argparse
    argparser = argparse.ArgumentParser(
            description='plot likelihoods scans')
    argparser.add_argument ( '-1', '--pid1',
            help='pid1 [1000021]',
            type=int, default=1000021 )
    argparser.add_argument ( '-2', '--pid2',
            help='pid2 [1000022]',
            type=int, default=1000022 )
    argparser.add_argument ( '-a', '--analysis',
            help='analysis [ATLAS-SUSY-2015-02]',
            type=str, default="ATLAS-SUSY-2015-02" )
    argparser.add_argument ( '-i', '--interactive',
            help='interactive mode',
            action="store_true" )
    args = argparser.parse_args()
    interactive = True
    plot ( args.pid1, args.pid2, args.analysis, args.interactive )
