#!/usr/bin/env python3

""" the plotting script for the llhd scans """

import pickle, sys, copy
import IPython
import numpy as np
from csetup import setup
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt

def load ( picklefile ):
    """ load dictionary from picklefile """
    topo, timestamp = "?", "?"
    with open ( picklefile, "rb" ) as f:
        try:
            allhds = pickle.load ( f )
            mx = pickle.load ( f )
            my = pickle.load ( f )
            nevents = pickle.load ( f )
            topo = pickle.load ( f )
            timestamp = pickle.load ( f )
        except EOFError as e:
            pass
        f.close()
    llhds=[]
    mu = 1.
    def getMu1 ( L ):
        for k,v in L.items():
            if abs(k-mu)<1e-9:
                return v
        print ( "couldnt find anything" )
        return None
    for llhd in allhds:
        llhds.append ( (llhd[0],llhd[1],getMu1(llhd[2])) )
    return llhds,mx,my,nevents,topo,timestamp

def integrateLlhds ( Z ):
    """ compute the integral of the likelihood over all points """
    I = 0.
    for row in Z:
        for nll in row:
            if not np.isnan(nll):
                I += np.exp ( - nll )
    return I


def findMin ( Z ):
    """ find the minimum in Z """
    x,y,m = 0., 0, float("inf")
    for x_,row in enumerate(Z):
        for y_,v in enumerate(row):
            if v < m:
                m,x,y = v,x_,y_
    return x,y,m

def computeHLD ( Z, alpha = .9 ):
    """ compute the regions of highest likelihood density to the alpha quantile 
    """
    I = integrateLlhds ( Z )
    S = 0.
    points = []
    oldZ = copy.deepcopy ( Z )
    newZ = copy.deepcopy ( Z )
    n = 0
    for x,row in enumerate(newZ):
        for y,_ in enumerate(row):
            n += 1
            newZ[x][y] = 0.
    ctr = 0
    while S < alpha: ## as long as we dont have enough area
        x,y,m = findMin(oldZ)
        ctr+= 1
        S += np.exp ( -m)/I ## add up
        oldZ[x][y]=float("nan") ## kill this one
        newZ[x][y]=1 +1./ctr
    print ( "%d/%d points in %d%s HLD" % ( sum(sum(newZ)), n, int(alpha*100), "%" ) )
    return newZ

def getAnaStats ( D, topo, integrateSRs=True, integrateTopos=True ):
    """ given the likelihood dictionaries D, get
        stats of which analysis occurs how often """
    anas = {}
    for masspoint in D:
        m1,m2,llhds=masspoint[0],masspoint[1],masspoint[2]
        for k,v in llhds.items():
            tokens = k.split(":")
            if not integrateTopos and topo not in tokens[2]:
                continue
            name = tokens[0]
            if not integrateTopos:
                name = tokens[0]+tokens[1]
            if not name in anas.keys():
                anas[name]=0
            anas[name]=anas[name]+1
    return anas

def getHash ( m1, m2 ):
    return int(1e3*m1) + int(1e0*m2)

def filterSmaller ( X, Y ):
    """ filter out whenever X < Y """
    Xs,Ys = [], []
    for irow,row in enumerate ( zip ( X, Y ) ):
        xt = []
        yt = []
        if irow % 3 == 1:
            continue
        if irow % 3 == 2:
            continue
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

def resultFor ( ana, topo, llhds ):
    """ return result for ana/topo pair """
    ret,sr = None,None
    for k,v in llhds.items():
        tokens = k.split(":")
        if ana != tokens[0]:
            continue
        if topo not in tokens[2]:
            continue
        if ret == None or v > ret:
            ret = v
            sr = tokens[1]
    return ret,sr

def plotOneAna ( masspoints, ana, pid1, pid2, mx, my, 
                 topo, nevents, timestamp ):
    """ plot for one analysis """
    print ( "[plotLlhds] now plotting %s" % ana )
    x,y=set(),set()
    L = {}
    minXY=0.,0.,float("inf")
    s=""
    r,sr = resultFor ( ana, topo, masspoints[0][2] )
    if r:
        s="(%.2f)" % (-np.log(r))
    cresults = 0
    for masspoint in masspoints[1:]:
        m1,m2,llhds=masspoint[0],masspoint[1],masspoint[2]
        if m2 > m1:
            print ( "m2,m1 mass inversion?",m1,m2 )
        x.add ( m1 )
        y.add ( m2 )
        zt = float("nan")
        # zt = 0.
        result,sr = resultFor ( ana, topo, llhds )
        if result:
            zt = - np.log( result )
            cresults += 1
            if zt < minXY[2]:
                minXY=(m1,m2,zt)
        h = getHash(m1,m2)
        L[h]=zt
    if cresults == 0:
        print ( "[plotLlhds] warning: found no results for %s. skip" % ana )
        return
    x,y=list(x),list(y)
    x.sort(); y.sort()
    X, Y = np.meshgrid ( x, y )
    Z = float("nan")*X
    # print ( "x", x )
    for irow,row in enumerate(Z):
        for icol,col in enumerate(row):
            h = getHash(x[icol],y[irow])
            if h in L:
                Z[irow,icol]=L[h]
    contf = plt.contourf ( X, Y, Z, levels=100 )
    hldZ95 = computeHLD ( Z, .95 )
    cont95 = plt.contour ( X, Y, hldZ95, levels=[0.5], colors = [ "orange" ] )
    plt.clabel ( cont95, fmt="95%.0s" )
    hldZ50 = computeHLD ( Z, .5 )
    cont50 = plt.contour ( X, Y, hldZ50, levels=[1.0], colors = [ "red" ] )
    plt.clabel ( cont50, fmt="50%.0s" )
    # print ( "timestamp:", timestamp, topo, max(x) )
    plt.text( max(x)-300,min(y)-350,timestamp, c="gray" )
    ### the altitude of the alpha quantile is l(nuhat) - .5 chi^2_(1-alpha);ndf 
    ### so for alpha=0.05%, ndf=1 the dl is .5 * 3.841 = 1.9207
    ### for ndf=2 the dl is ln(alpha) = .5 * 5.99146 = 2.995732
    ### folien slide 317
    cbar = plt.colorbar( contf, format="%.2f" )
    cbar.set_label ( "-ln L" )
    ax = contf.ax
    # Xs,Ys=X,Y
    Xs,Ys = filterSmaller ( X, Y )
    ax.scatter(Xs, Ys, marker=".", s=.2, color="gray", label="points probed" )
    ax.scatter( [ minXY[0] ], [ minXY[1] ], marker="*", s=60, color="black" ) 
    ax.scatter( [ minXY[0] ], [ minXY[1] ], marker="*", s=35, color="red", label="$\hat{l}$ (ml estimate, %.2f)" % minXY[2] )
    h = getHash(mx,my)
    if h in L:
        s=" (%.2f)" % L[h]
    ax.scatter( [ mx ], [ my ], marker="*", s=60, color="white" )
    ax.scatter( [ mx ], [ my ], marker="*", s=35, color="black", label="proto-model%s" % s )
    if sr == None:
        sr = "UL"
    plt.title ( "$-\ln L(m_i)$, %s: %s,%s [%d events]" % ( ana, topo, sr, nevents ) )
    plt.xlabel ( "%s" % pid1 )
    plt.ylabel ( "%s" % pid2 )
    plt.legend()
    # plt.contour ( X, Y, Z )
    figname = "plt%d%s.png" % ( pid1, ana )
    print ( "[plotLlhds] saving to %s" % figname )
    plt.savefig ( figname )
    plt.close()

def plot ( pid1, pid2, analysis ):
    """ do your plotting """
    masspoints,mx,my,nevents,topo,timestamp = load ( getPickleFile ( pid1, pid2 ) )
    stats = getAnaStats( masspoints, topo )
    plotOneAna ( masspoints, analysis, pid1, pid2, mx, my, topo,
                 nevents,timestamp )

def getPickleFile ( pid1, pid2 ):
    rundir = setup()
    picklefile = "%smp%d%d.pcl" % ( rundir, pid1, pid2 )
    return picklefile

def listAnalyses( pid1, pid2, topo ):
    masspoints,mx,my,nevents,ntopo,timestamp = load ( getPickleFile(pid1,pid2) )
    if topo == "?":
        topo = ntopo
    stats = getAnaStats( masspoints, topo )
    print ( "%d masspoints with %s" % ( len(masspoints), topo ) )
    for k,v in stats.items():
        print ( "%d: %s" % ( v, k ) )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='plot likelihoods scans')
    argparser.add_argument ( '-t', '--topo',
            help='topo [?]',
            type=str, default="?" )
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
    argparser.add_argument ( '-A', '--all',
            help='plot for all analyses',
            action="store_true" )
    argparser.add_argument ( '-I', '--interactive',
            help='interactive mode',
            action="store_true" )
    args = argparser.parse_args()
    if args.all:
        masspoints,mx,my,nevents,topo,timestamp = load ( getPickleFile ( args.pid1, args.pid2 ) )
        stats = getAnaStats( masspoints, topo )
        for ana,v in stats.items():
            plot ( args.pid1, args.pid2, ana )
        sys.exit()
            
    if args.list_analyses:
        listAnalyses ( args.pid1, args.pid2, args.topo )
    else:
        plot ( args.pid1, args.pid2, args.analysis )
    if args.interactive:
        masspoints,mx,my,nevents,topo,timestamp = load ( getPickleFile ( args.pid1, args.pid2 ) )
        import IPython
        IPython.embed()
