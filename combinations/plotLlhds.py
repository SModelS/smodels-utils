#!/usr/bin/env python3

""" the plotting script for the llhd scans """

import pickle, sys, copy, subprocess, os, colorama, time
import IPython
import numpy as np
from csetup import setup
import matplotlib
from helpers import getParticleName, toLatex
matplotlib.use("Agg")
from matplotlib import pyplot as plt

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
    #x,y,m = 0., 0, float("inf")
    #for x_,row in enumerate(Z):
    #    for y_,v in enumerate(row):
    #        if v < m:
    #            m,x,y = v,x_,y_
    #print ( "findMin", Z.shape )
    # print ( "Z", Z )
    idx = np.nanargmin ( Z ) 
    y = idx % Z.shape[1] 
    x = int ( ( idx - y ) / Z.shape[1] )
    m = Z[x][y]
    #print ( "argmin", idx, x2 , y2, m2 )
    #print ( "found at x,y,m",x,y,m )
    #sys.exit()
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

def getAlpha ( color ):
    """ different alpha for different colors """
    return .3
    if color == "red":
        return .6
    return .4

class LlhdPlot:
    """ A simple class to make debugging the plots easier """
    def __init__ ( self, pid1, pid2, verbose, copy ):
        """
        :param copy: copy plot to ../../smodels.github.io/protomodels/latest
        """
        if pid1==0:
            pid1 = [ 1000006, 1000021, 2000006, 1000002 ]
        self.DEBUG, self.INFO = 40, 30
        self.pid1 = pid1
        self.pid2 = pid2
        self.copy = copy
        self.hiscorefile = "./hiscore.pcl"
        self.setVerbosity ( verbose )
        self.setup()
        masspoints,mx,my,nevents,topo,timestamp = self.loadPickleFile()
        self.masspoints = masspoints
        self.mx = mx
        self.my = my
        self.nevents = nevents
        self.topo = topo
        self.timestamp = timestamp
        self.massdict = {}
        for m in masspoints:
            self.massdict[ (m[0],m[1]) ] = m [2]

    def setVerbosity ( self, verbose ):
        self.verbose = verbose
        if type(verbose)==str:
            verbose = verbose.lower()
            if "deb" in verbose:
                self.verbose = 40
                return
            if "inf" in verbose:
                self.verbose = 30
                return
            if "warn" in verbose:
                self.verbose = 20
                return
            if "err" in verbose:
                self.verbose = 10
                return
            self.pprint ( "I dont understand verbosity ``%s''. Setting to debug." % verbose )
            self.verbose = 40

    def getHash ( self, m1=None, m2=None ):
        """ get hash for point. if None, get hash for self.mx, self.my """
        if m1 == None:
            m1 = self.mx
        if m2 == None:
            m2 = self.my
        return int(1e3*m1) + int(1e0*m2)

    def getResultFor ( self, ana, masspoint ):
        """ return result for ana/topo pair 
        :param ana: the analysis id. optionally a data type can be specificed, e.g.
                    as :em. Alternatively, a signal region can be specified.
        :param masspoint: a point from self.masspoints
        :returns: results for this analysis (possibly data type, possibly signal region) 
                  and topology
        """
        #self.pprint ( "asking for %s" % ana )
        ret,sr = None,None
        dType = "any"
        if ":" in ana:
            ana,dType = ana.split(":")
        for k,v in masspoint.items():
            tokens = k.split(":")
            if dType == "ul" and tokens[1] != "None":
                continue
            if dType == "em" and tokens[1] == "None":
                continue
            if ana != tokens[0]:
                continue
            # self.pprint ( "asking for %s, %s %s" % ( tokens[0], tokens[1], dType ) )
            if tokens[1] != None and dType not in [ "any", "ul", "None" ]:
                # if signal regions are given, they need to match
                if tokens[1] != dType:
                    continue
                self.debug ( "found a match for", tokens[0], tokens[1], v )
            if self.topo not in tokens[2]:
                continue
            if ret == None or v > ret:
                ret = v
                sr = tokens[1]
        return ret,sr

    def plotOneAna ( self, ana ):
        """ plot for one analysis
        :param copy: copy plot to ../../smodels.github.io/protomodels/latest
        """
        print ( "[plotLlhds] now plotting %s" % ana )
        x,y=set(),set()
        L = {}
        minXY=0.,0.,float("inf")
        s=""
        r,sr = self.getResultFor ( ana, self.masspoints[0][2] )
        if r:
            s="(%.2f)" % (-np.log(r))
        cresults = 0
        for masspoint in self.masspoints[1:]:
            m1,m2,llhds=masspoint[0],masspoint[1],masspoint[2]
            if m2 > m1:
                print ( "m2,m1 mass inversion?",m1,m2 )
            x.add ( m1 )
            y.add ( m2 )
            zt = float("nan")
            # zt = 0.
            result,sr = self.getResultFor ( ana, llhds )
            if result:
                zt = - np.log( result )
                cresults += 1
                if zt < minXY[2]:
                    minXY=(m1,m2,zt)
            h = self.getHash(m1,m2)
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
                h = self.getHash(x[icol],y[irow])
                if h in L:
                    Z[irow,icol]=L[h]
        print ( "now getting HLDs" )
        contf = plt.contourf ( X, Y, Z, levels=100 )
        hldZ95 = computeHLD ( Z, .95 )
        cont95 = plt.contour ( X, Y, hldZ95, levels=[0.5], colors = [ "orange" ] )
        plt.clabel ( cont95, fmt="95%.0s" )
        hldZ50 = computeHLD ( Z, .5 )
        cont50 = plt.contour ( X, Y, hldZ50, levels=[1.0], colors = [ "red" ] )
        plt.clabel ( cont50, fmt="50%.0s" )
        print ( "timestamp:", self.timestamp, self.topo, max(x) )
        plt.text( max(x)-300,min(y)-350,self.timestamp, c="gray" )
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
        h = self.getHash()
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

    def loadPickleFile ( self ):
        """ load dictionary from picklefile """
        topo, timestamp = "?", "?"
        with open ( self.picklefile, "rb" ) as f:
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

    def pprint ( self, *args ):
        print ( "[plotLlhds] %s" % " ".join(map(str,args)) )  

    def debug ( self, *args ):
        if self.verbose >= self.DEBUG:
            print ( "[plotLlhds] %s" % " ".join(map(str,args)) )  

    def setup ( self ):
        """ setup rundir, picklefile path and hiscore file path """
        self.rundir = setup()
        self.hiscorefile = self.rundir + "/hiscore.pcl"
        if not os.path.exists ( self.hiscorefile ):
            self.pprint ( "could not find hiscore file %s" % self.hiscorefile )

        self.picklefile = "%smp%d%d.pcl" % ( self.rundir, self.pid1, self.pid2 )
        if not os.path.exists ( self.picklefile ):
            self.pprint ( "could not find pickle file %s" % self.picklefile )

    def describe ( self ):
        """ describe the situation """
        print ( "%d masspoints obtained from %s, hiscore stored in %s" % \
                ( len ( self.masspoints), self.picklefile, self.hiscorefile ) )
        print ( "Data members: plot.masspoints, plot.massdict, plot.timestamp, plot.mx, plot.my" )
        print ( "              plot.pid1, plot.pid2, plot.topo" )
        print ( "Function members: plot.findClosestPoint()" )

    def plotSummary ( self, ulSeparately=True ):
        """ a summary plot, overlaying all contributing analyses 
        :param ulSeparately: if true, then plot UL results on their own
        """
        resultsForPIDs = {}
        from plotHiscore import getPIDsOfTPred, obtain
        protomodel, trimmed = obtain ( 0, self.hiscorefile )
        for tpred in protomodel.bestCombo:
            resultsForPIDs = getPIDsOfTPred ( tpred, resultsForPIDs, integrateSRs=False )
        stats = self.getAnaStats( integrateSRs=False )
        anas = list(stats.keys())
        if self.pid1 in resultsForPIDs:
            self.debug ( "results for PIDs %s" % ", ".join ( resultsForPIDs[self.pid1] ) )
            anas = list ( resultsForPIDs[self.pid1] )
        anas.sort()
        self.pprint ( "summary plot: %s" % ", ".join ( anas ) )
        # print ( stats.keys() )
        colors = [ "red", "green", "blue", "orange", "cyan", "magenta", "grey", "brown",
                   "pink", "indigo", "olive", "orchid", "darkseagreen", "teal" ]
        xmin,xmax,ymin,ymax=9000,0,9000,0
        for m in self.masspoints:
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
                print ( "[plotLlhds] too many analyses. skip it" )
                break
            color = colors[ctr]
            x,y=set(),set()
            L = {}
            minXY=( 0.,0., float("inf") )
            s=""
            r,sr = self.getResultFor ( ana, self.masspoints[0][2] )
            if r:
                s="(%.2f)" % (-np.log(r))
            cresults = 0
            for cm,masspoint in enumerate(self.masspoints[1:]):
                #if cm % 10 != 0:
                #    continue
                if cm % 1000 == 0:
                    print ( ".", end="", flush=True )
                m1,m2,llhds=masspoint[0],masspoint[1],masspoint[2]
                if m2 > m1:
                    print ( "m2,m1 mass inversion?",m1,m2 )
                x.add ( m1 )
                y.add ( m2 )
                zt = float("nan")
                result,sr = self.getResultFor ( ana, llhds )
                if result:
                    zt = - np.log( result )
                    cresults += 1
                    if zt < minXY[2]:
                        minXY=(m1,m2,zt)
                h = self.getHash(m1,m2)
                L[h]=zt
            print ( "\n[plotLlhds] min(xy) for %s is at m=(%d/%d): %.2f(%.2g)" % ( ana, minXY[0], minXY[1], minXY[2], np.exp(-minXY[2] ) ) )
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
                    h = self.getHash(x[icol],y[irow])
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
            ax.scatter( [ minXY[0] ], [ minXY[1] ], marker="*", s=110, color=color, label=ana+" (%.2f)" % (minXY[2]), alpha=1. )

        print()
        self.pprint ( "timestamp:", self.timestamp, self.topo, max(x) )
        dx,dy = max(x)-min(x),max(y)-min(y)
        plt.text( max(x)-.37*dx,min(y)-.11*dy,self.timestamp, c="gray" )
        ### the altitude of the alpha quantile is l(nuhat) - .5 chi^2_(1-alpha);ndf
        ### so for alpha=0.05%, ndf=1 the dl is .5 * 3.841 = 1.9207
        ### for ndf=2 the dl is ln(alpha) = .5 * 5.99146 = 2.995732
        ### folien slide 317
        ax = cont50.ax
        # Xs,Ys=X,Y
        Xs,Ys = filterSmaller ( X, Y )
        h = self.getHash()
        if h in L:
            s=" (%.2f)" % L[h]
        ax.scatter( [ self.mx ], [ self.my ], marker="*", s=200, color="white" )
        ax.scatter( [ self.mx ], [ self.my ], marker="*", s=160, color="black", 
                      label="proto-model%s" % s )
        if sr == None:
            sr = "UL"
        plt.title ( "HPD intervals, %s [%s]" % ( toLatex(self.pid1,True), self.topo ) )
        plt.xlabel ( "m(%s) [GeV]" % toLatex(self.pid1,True) )
        plt.ylabel ( "m(%s) [GeV]" % toLatex(self.pid2,True) )
        plt.legend( loc="upper left" )
        figname = "llhd%d.png" % ( self.pid1 )
        self.pprint ( "saving to %s" % figname )
        plt.savefig ( figname )
        plt.close()
        if self.copy:
            self.copyFile ( figname )
        return

    def copyFile ( self, filename ):
        """ copy filename to smodels.github.io/protomodels/latest/ """
        dest = os.path.expanduser ( "~/git/smodels.github.io" )
        cmd = "cp %s/%s %s/protomodels/latest/" % ( self.rundir, figname, dest )
        o = subprocess.getoutput ( cmd )
        pprint ( "%s: %s" % ( cmd, o ) )


    def getAnaStats ( self, integrateSRs=True, integrateTopos=True,
                      integrateDataType=True  ):
        """ given the likelihood dictionaries D, get
            stats of which analysis occurs how often 
        :param integrateTopos: sum over all topologies
        :param integrateSRs: sum over all signal regions
        :param integrateDataType: ignore data type
        """
        anas = {}
        for masspoint in self.masspoints:
            m1,m2,llhds=masspoint[0],masspoint[1],masspoint[2]
            for k,v in llhds.items():
                tokens = k.split(":")
                if not integrateTopos and self.topo not in tokens[2]:
                    continue
                dType = ":em"
                if tokens[1] in [ "None", None ]:
                    dType = ":ul"
                name = tokens[0]
                if not integrateDataType:
                    name = name + dType
                if not integrateTopos:
                    name = tokens[0]+tokens[1]
                if not name in anas.keys():
                    anas[name]=0
                anas[name]=anas[name]+1
        return anas

    def listAnalyses( self ):
        """
        :param verbose: verbosity: debug, info, warn, or error
        """
        stats = self.getAnaStats( integrateDataType=False )
        print ( "%6d masspoints with %s" % ( len(self.masspoints), self.topo ) )
        for k,v in stats.items():
            print ( "%6d: %s" % ( v, k ) )

    def findClosestPoint ( self, m1=None, m2=None, nll=False ):
        """ find the mass point closest to m1, m2. If not specified, 
            return the hiscore point.
        :param nll: if True, report nlls, else report likelihoods.
        """
        if m1 == None:
            m1 = self.mx
        if m2 == None:
            m2 = self.my
        dm,point = float("inf"),None
        def distance ( m ):
            return (m[0]-m1)**2 + (m[1]-m2)**2

        for m in self.masspoints:
            tmp = distance(m)
            if tmp < dm:
                dm = tmp
                point = m
        if not nll:
            return point
        # asked for NLLs
        D = {}
        for k,v in point[2].items():
            D[k]=-np.log(v)
        return ( point[0], point[1], D )

    def interact ( self ):
        import IPython
        varis = "plot.describe()"
        print ( "%s[plot] interactive session. Try: %s%s" % \
                ( colorama.Fore.GREEN, varis, colorama.Fore.RESET ) )
        IPython.embed()

    def plotAll ( self ):
        """ """
        stats = self.getAnaStats()
        for ana,v in stats.items():
            self.plot ( ana )
        pass


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='plot likelihoods scans')
    """
    argparser.add_argument ( '-t', '--topo',
            help='topo [?]',
            type=str, default="?" )
    """
    argparser.add_argument ( '-v', '--verbose',
            help='verbosity: debug, info, warn, or error [warn]',
            type=str, default="warn" )
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
            help='copy plots to ~/git/smodels.github.io/protomodels/latest',
            action="store_true" )
    argparser.add_argument ( '-A', '--all',
            help='plot for all analyses',
            action="store_true" )
    argparser.add_argument ( '-I', '--interactive',
            help='interactive mode',
            action="store_true" )
    args = argparser.parse_args()

    plot = LlhdPlot ( args.pid1, args.pid2, args.verbose, args.copy )

    if args.all:
        plot.plotAll ( )
    elif args.interactive:
        plot.interact()
    elif args.list_analyses:
        plot.listAnalyses ( )
    ## summary plot!
    elif args.analysis in [ "*", "all", "summary" ]:
        plot.plotSummary()
    else:
        ## plot one specific analysis
        plot.plotOneAna ( args.analysis )

