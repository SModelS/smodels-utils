#!/usr/bin/env python3

""" the plotting script for the llhd scans """

import pickle, sys
import IPython
import numpy as np
from matplotlib import pyplot as plt

def load ( picklefile ):
    """ load dictionary from picklefile """
    f = open ( picklefile, "rb" )
    llhds = pickle.load ( f )
    mx = pickle.load ( f )
    my = pickle.load ( f )
    f.close()
    return llhds,mx,my

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

def filterSmaller ( X, Y ):
    """ filter out whenever X < Y """
    Xs,Ys = [], []
    for irow,row in enumerate ( zip ( X, Y ) ):
        xt = []
        yt = []
        for icol,col in enumerate ( zip ( row[0], row[1] ) ):
            if col[0]>col[1]: ## all is good
                xt.append ( float(col[0]) )
                yt.append ( float(col[1]) )
            else:
                xt.append ( float("nan") )
                yt.append ( float("nan") )
        Xs.append ( xt )
        Ys.append ( yt )
    return np.array(Xs), np.array(Ys)

def plotOneAna ( masspoints, ana, interactive, pid1, pid2, mx, my ):
    """ plot for one analysis """
    x,y=set(),set()
    L = {}
    minXY=0.,0.,float("inf")
    for masspoint in masspoints:
        m1,m2,llhds=masspoint[0],masspoint[1],masspoint[2]
        if m2 > m1:
            print ( "m2,m1 mass inversion?",m1,m2 )
        x.add ( m1 )
        y.add ( m2 )
        zt = float("nan")
        zt = 0.
        if ana in llhds:
            zt = - np.log(llhds[ana] )
            if zt < minXY[2]:
                minXY=(m1,m2,zt)
        h = getHash(m1,m2)
        L[h]=zt
    x,y=list(x),list(y)
    X, Y = np.meshgrid ( x, y )
    Z = float("nan")*X
    for irow,row in enumerate(Z):
        for icol,col in enumerate(row):
            h = getHash(x[icol],y[irow])
            if h in L:
                Z[irow,icol]=L[h]
    cont = plt.contourf ( X, Y, Z )
    ### the altitude of the alpha quantile is l(nuhat) - .5 chi^2_(1-alpha);ndf 
    ### so for alpha=0.05%, ndf=1 the dl is .5 * 3.841 = 1.9207
    ### for ndf=2 the dl is ln(alpha) = .5 * 5.99146 = 2.995732
    ### folien slide 317
    cbar = plt.colorbar( cont ) # , ticks=lvls, format="%.4f")
    ax = cont.ax
    Xs,Ys = filterSmaller ( X, Y )
    ax.scatter(Xs, Ys, marker="+", s=1, color="black" )
    print ( "minXY", minXY )
    ax.scatter( [ minXY[0] ], [ minXY[1] ], marker="*", s=12, color="red", label="$\hat{l}$ (ml estimate, %.2f)" % minXY[2] )
    s=""
    h = getHash(mx,my)
    if h in L:
        s=" (%.2f)" % L[h]
    ax.scatter( [ mx ], [ my ], marker="*", s=15, color="black", label="proto-model%s" % s )
    plt.title ( "-ln L, %s" % ana )
    plt.xlabel ( "%s" % pid1 )
    plt.ylabel ( "%s" % pid2 )
    plt.legend()
    # plt.contour ( X, Y, Z )
    figname = "plt%d%s.png" % ( pid1, ana )
    print ( "[llhdplot] saving to %s" % figname )
    plt.savefig ( figname )
    if interactive:
        IPython.embed()
    plt.close()

def plot ( pid1, pid2, analysis, interactive ):
    """ do your plotting """
    picklefile = "mp%d%d.pcl" % ( pid1, pid2 )
    masspoints,mx,my = load ( picklefile )
    stats = getAnaStats( masspoints )
    plotOneAna ( masspoints, analysis, interactive, pid1, pid2, mx, my )

def listAnalyses( pid1, pid2 ):
    picklefile = "mp%d%d.pcl" % ( pid1, pid2 )
    masspoints,mx,my = load ( picklefile )
    stats = getAnaStats( masspoints )
    for k,v in stats.items():
        print ( "%d: %s" % ( v, k ) )

if __name__ == "__main__":
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
    argparser.add_argument ( '-l', '--list_analyses',
            help='list all analyses for these pids',
            action="store_true" )
    argparser.add_argument ( '-i', '--interactive',
            help='interactive mode',
            action="store_true" )
    args = argparser.parse_args()
    if args.list_analyses:
        listAnalyses ( args.pid1, args.pid2 )
        sys.exit()
    plot ( args.pid1, args.pid2, args.analysis, args.interactive )
