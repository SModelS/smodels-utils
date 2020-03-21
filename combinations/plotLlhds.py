#!/usr/bin/env python3

""" the plotting script for the llhd scans """

import pickle, sys, copy, subprocess
import IPython
import numpy as np
from csetup import setup
import matplotlib
from helpers import getParticleName, toLatex
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

def computeHLD ( Z, alpha = .9, verbose = True ):
    """ compute the regions of highest likelihood density to the alpha quantile
    """
    newZ = copy.deepcopy ( Z )
    if alpha > .999999: # give all points with likelihoods
        for x,row in enumerate(newZ):
            for y,_ in enumerate(row):
                if _ > 0.:
                    newZ[x][y]=1.
                else:
                    newZ[x][y]=0.
        return newZ
    I = integrateLlhds ( Z )
    S = 0.
    points = []
    oldZ = copy.deepcopy ( Z )
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
    if verbose:
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
                 topo, nevents, timestamp, copy ):
    """ plot for one analysis
    :param copy: copy plot to ../../smodels.github.io/protomodels/latest
    """
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

def getAlpha ( color ):
    """ different alpha for different colors """
    return .3
    if color == "red":
        return .6
    return .4

def plotSummary ( pid1, pid2, copy ):
    """ a summary plot, overlaying all contributing analyses 
    :param copy: copy plot to ../../smodels.github.io/protomodels/latest
    """
    masspoints,mx,my,nevents,topo,timestamp = load ( getPickleFile ( pid1, pid2 ) )
    resultsForPIDs = {}
    from plotHiscore import getPIDsOfTPred, obtain
    picklefile = "hiscore.pcl"
    protomodel, trimmed = obtain ( 0, picklefile )
    for tpred in protomodel.bestCombo:
        resultsForPIDs = getPIDsOfTPred ( tpred, resultsForPIDs )
    # print ( "results", resultsForPIDs )
    stats = getAnaStats( masspoints, topo )
    anas = list(stats.keys())
    if pid1 in resultsForPIDs:
        anas = list ( resultsForPIDs[pid1] )
    anas.sort()
    print ( "[plotLlhds] summary plot: %s" % ",".join ( anas ) )
    # print ( stats.keys() )
    colors = [ "red", "green", "blue", "orange", "cyan", "magenta", "grey", "brown",
               "pink", "indigo", "olive", "orchid", "darkseagreen", "teal" ]
    xmin,xmax,ymin,ymax=9000,0,9000,0
    for m in masspoints:
        if m[0] < xmin:
            xmin = m[0]
        if m[0] > xmax:
            xmax = m[0]
        if m[1] < ymin:
            ymin = m[1]
        if m[1] > ymax:
            ymax = m[1]
    print ( "[plotLlhds] range x [%d,%d] y [%d,%d]" % ( xmin, xmax, ymin, ymax ) )
    for ctr,ana in enumerate ( anas ): ## loop over the analyses
        if ctr > 2:
            break
        color = colors[ctr]
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
        x.add ( xmax*1.03 )
        x.add ( xmin*.93 )
        y.add ( ymax+50. )
        y.add ( 0. )
        x,y=list(x),list(y)
        x.sort(); y.sort()
        X, Y = np.meshgrid ( x, y )
        Z = float("nan")*X
        for irow,row in enumerate(Z):
            for icol,col in enumerate(row):
                h = getHash(x[icol],y[irow])
                if h in L:
                    Z[irow,icol]=L[h]
        # contf = plt.contourf ( X, Y, Z, levels=100 )
        hldZ100 = computeHLD ( Z, 1., False )
        cont100 = plt.contour ( X, Y, hldZ100, levels=[0.25], colors = [ color ], linestyles = [ "dotted" ] )
        #hldZ95 = computeHLD ( Z, .95, False )
        #cont95 = plt.contour ( X, Y, hldZ95, levels=[0.5], colors = [ color ], linestyles = [ "dashed" ] )
        #plt.clabel ( cont95, fmt="95%.0s" )
        hldZ50 = computeHLD ( Z, .68, False )
        cont50c = plt.contour ( X, Y, hldZ50, levels=[1.0], colors = [ color ] )
        cont50 = plt.contourf ( X, Y, hldZ50, levels=[1.,10.], colors = [ color, color ], alpha=getAlpha( color ) )
        plt.clabel ( cont50c, fmt="68%.0s" )
        ax = cont50.ax
        # print ( "[plotLlhds] ana, min", ana, minXY )
        ax.scatter( [ minXY[0] ], [ minXY[1] ], marker="*", s=180, color="black" )
        ax.scatter( [ minXY[0] ], [ minXY[1] ], marker="*", s=110, color=color, label=ana, alpha=1. )

    # print ( "timestamp:", timestamp, topo, max(x) )
    plt.text( max(x)-300,min(y)-350,timestamp, c="gray" )
    ### the altitude of the alpha quantile is l(nuhat) - .5 chi^2_(1-alpha);ndf
    ### so for alpha=0.05%, ndf=1 the dl is .5 * 3.841 = 1.9207
    ### for ndf=2 the dl is ln(alpha) = .5 * 5.99146 = 2.995732
    ### folien slide 317
    ax = cont50.ax
    # Xs,Ys=X,Y
    Xs,Ys = filterSmaller ( X, Y )
    h = getHash(mx,my)
    if h in L:
        s=" (%.2f)" % L[h]
    ax.scatter( [ mx ], [ my ], marker="*", s=200, color="white" )
    ax.scatter( [ mx ], [ my ], marker="*", s=160, color="black", label="proto-model%s" % s )
    if sr == None:
        sr = "UL"
    plt.title ( "HPD intervals, %s [%s]" % ( toLatex(pid1,True), topo ) )
    # plt.title ( "$-\ln L(m_i)$, %s" % ( topo ) )
    plt.xlabel ( "m(%s) [GeV]" % toLatex(pid1,True) )
    plt.ylabel ( "m(%s) [GeV]" % toLatex(pid2,True) )
    plt.legend( loc="upper left" )
    figname = "llhd%d.png" % ( pid1 )
    print ( "[plotLlhds] saving to %s" % figname )
    plt.savefig ( figname )
    plt.close()
    if copy:
        cmd = "cp %s ../../smodels.github.io/protomodels/latest/" % figname
        subprocess.getoutput ( cmd )
    return

def plot ( pid1, pid2, analysis, copy ):
    """ do your plotting 
    :param copy: copy plot to ../../smodels.github.io/protomodels/latest
    """
    if analysis in [ "*", "all", "summary" ]:
        plotSummary ( pid1, pid2, copy )
        return
    masspoints,mx,my,nevents,topo,timestamp = load ( getPickleFile ( pid1, pid2 ) )
    stats = getAnaStats( masspoints, topo )
    plotOneAna ( masspoints, analysis, pid1, pid2, mx, my, topo,
                 nevents,timestamp, copy )

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
            help='pid1, if 0 then do predefined list [0]',
            type=int, default=0 )
    argparser.add_argument ( '-2', '--pid2',
            help='pid2 [1000022]',
            type=int, default=1000022 )
    argparser.add_argument ( '-a', '--analysis',
            help="analysis. '*' means, overlay all analyses to a summary plot [*]",
            type=str, default="*" )
    argparser.add_argument ( '-l', '--list_analyses',
            help='list all analyses for these pids',
            action="store_true" )
    argparser.add_argument ( '-c', '--copy',
            help='copy plots to ../../smodels.github.io/protomodels/latest',
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
            plot ( args.pid1, args.pid2, ana, args.copy )
        sys.exit()

    pids1 = [ args.pid1 ]
    if pids1[0]==0:
        pids1 = [ 1000006, 1000021, 2000006, 1000002 ]

    if args.list_analyses:
        for pid1 in pids1:
            listAnalyses ( pid1, args.pid2, args.topo )
    else:
        for pid1 in pids1:
            try:
                plot ( pid1, args.pid2, args.analysis, args.copy )
            except FileNotFoundError:
                pass

    if args.interactive:
        masspoints,mx,my,nevents,topo,timestamp = load ( getPickleFile ( pids1[0], args.pid2 ) )
        import IPython
        IPython.embed()
