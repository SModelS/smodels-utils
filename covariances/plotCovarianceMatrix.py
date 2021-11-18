#!/usr/bin/env python3

""" some unfinished code that plots a covariance matrix as a 2d hist """

import sys
import numpy as np
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
import IPython
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LogNorm, Normalize
from matplotlib.colors import LogNorm, Normalize
import cov_helpers 

def plot():
    import argparse
    argparser = argparse.ArgumentParser(
            description = "plot of covariance matrix of an analysis" )
    argparser.add_argument ( "-d", "--dbpath",
            help="path to database [../../smodels-database/]",
            type=str, default="../../smodels-database/" )
    argparser.add_argument ( "-a", "--analysis",
            help="analysis name, like the directory name [CMS-SUS-19-006-ma5]",
            type=str, default="CMS-SUS-19-006-ma5" )
    argparser.add_argument ( "-o", "--outputfile",
            help="output file, replacing @a with the analysis name, @t is 'cov' or 'corr', depending on --correlations [@t_@a.png]",
            type=str, default="./@t_@a.png" )
    argparser.add_argument ( "-n", "--nmin",
            help="plot only starting with nmin-th row and column, for debugging [None]",
            type=int, default=None )
    argparser.add_argument ( "-N", "--nmax",
            help="plot only ending with nmax-th row and column, for debugging [None]",
            type=int, default=None )
    argparser.add_argument ( "-i", "--indices",
            help="plot only <indices> rows and columns, e.g '1 2 3' for debugging [None]",
            type=str, default=None )
    argparser.add_argument ( "-C", "--correlations", action="store_true",
            help="plot correlations matrix, not covariance matrix" )
    argparser.add_argument ( "-I", "--interactive", action="store_true",
            help="interactive mode" )
    argparser.add_argument ( "-c", "--copy", action="store_true",
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    argparser.add_argument ( "-p", "--push", action="store_true",
            help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    args = argparser.parse_args()

    database = Database( args.dbpath, discard_zeroes = False)
    res = database.getExpResults ( analysisIDs = [ args.analysis ] )
    er = res[0]
    n = len ( er.globalInfo.covariance)
    norig = n
    cov = er.globalInfo.covariance
    if args.correlations:
        cov = cov_helpers.computeCorrelationMatrix ( cov )
    if args.nmin == None:
        args.nmin = 0
    if args.nmax == None:
        args.nmax = n
    cov = cov_helpers.cutMatrix ( cov, args.nmin, args.nmax )
    n = len ( cov )
    print ( f"[plotCovarianceMatrix] we have an {norig}x{norig}->{n}x{n} matrix" )
    # fig, ax = plt.subplots()
    #grid_kws = {"hspace": .3, "vspace": 0.1 }
    #f, ax = plt.subplots(1, gridspec_kw=grid_kws)
    def fmtLabel ( s ):
        if s >= 1.:
            # return "%d" % s
            return "%.0f" % s
        if s < 1.:
            return ("%.1f" % s)[1:]
        return "%.1f" % s
    labels = [ [ fmtLabel(x) for x in y ] for y in cov ]
    if n > 25:
        labels = None
    cmap = "rocket"
    vmin, vmax = None, None
    if args.correlations:
        cmap = "RdBu_r"
        vmin, vmax = 1e-2, 1.
    annot_kws = { "fontsize": 10 }
    print ( "vmin", vmin )
    ax = sns.heatmap(cov, cmap=cmap, annot=labels, annot_kws=annot_kws, 
                     vmin = vmin, vmax = vmax, fmt='s', norm=LogNorm( vmin=vmin, vmax=vmax) )
    def fmtTick ( x ):
        x = x.replace( "Ewkino", "e" ).replace("stop","t")
        x = x.replace( "MET", "" )
        x = x.replace( "PT_", "" ).replace("M_","")
        p1 = x.find("to")
        if p1 > 0:
            x = x[:p1]
        return x
    ax.invert_yaxis()
    #ax.invert_xaxis()
    allticklabels = [ fmtTick(x) for x in er.globalInfo.datasetOrder ]
    ticks = list(map(int, ax.xaxis.get_majorticklocs()-.5 ))
    ticklabels = []
    for t in ticks:
        ticklabels.append ( allticklabels [ t + args.nmin ] )
    # print ( "ticklabels", ticklabels )
    title = f"covariance matrix, {args.analysis}" 
    if args.correlations:
        title = f"correlations matrix, {args.analysis}" 
    plt.title ( title )
    ax.set_yticklabels ( ticklabels )
    ax.set_xticklabels ( ticklabels, rotation=75 )
    #b, t = plt.ylim()
    #print ( "bt", b, t )
    #plt.ylim ( b, t-5. )
    ax.figure.tight_layout()
    fname = args.outputfile.replace("@a",args.analysis )
    repl = "corr" if args.correlations else "cov"
    fname = fname.replace( "@t",repl)
    print ( f"[plotCovarianceMatrix] saving to {fname}" )
    plt.savefig ( fname )
    if args.interactive:
        import IPython
        IPython.embed ( colors = "neutral" )

if __name__ == "__main__":
    plot()
