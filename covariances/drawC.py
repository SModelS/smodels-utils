#!/usr/bin/python3

""" draw comparison between profiling, marginalizing and Nicks """

from __future__ import print_function
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import glob
import sys
import random
import numpy

def addLine ( ax, X, c, legend, style='-', ul=False ):
    l =Line2D ( list(X.keys()), [ numpy.mean(X[x]) for x in X.keys() ], c=c, linestyle=style, label=legend )
    ax.add_line(l)
    alpha=.5
    if ul:
        lp =Line2D ( list(X.keys()), [ numpy.mean(X[x])+numpy.std(X[x]) for x in X.keys() ], c=c, 
                     linestyle=':', alpha=alpha )
        ax.add_line(lp)
        lm =Line2D ( list(X.keys()), [ numpy.mean(X[x])-numpy.std(X[x]) for x in X.keys() ], c=c, 
                     linestyle=':', alpha=alpha )
        ax.add_line(lm)

def checkN ( n ):
    fname="results%d" % n
    files = glob.glob(fname+"_*.py")
    lines=[]
    for fil in files:
        f = open ( fil, "r" )
        for L in f.readlines():
            lines.append ( L )
        f.close()
    g=open(fname+"tmp.py","w")
    g.write ( "d=[" )
    for line in lines:
        g.write ( line )
    g.write("]\n" )
    g.close()
    return fname+"tmp"

def run ( n, selected, denominator, plot ):
    """ run for results<n>.py, drawing <selected> algos. """
    fname=checkN( n )
    D=__import__( fname )
    data=D.d
    print ( f"I have a total of {len(data)} points." )

    #max number of bins
    bmax = max( [ x["nbins"] for x in data ] )

    xv=[]

    algos={ "nick": "k", "nickl": "k", "marg": "b", "marg10": "cyan", "prof": "r", 
            "marg100": "g", "margl": "magenta", "profl": "orange", "nickn": "k" }
    descs={ "nick": "Nick", "nickl": "Linear Nick", "prof": "Profile", 
            "marg": "Margin", "marg10": "Margin 10K", "marg100": "Margin 100", 
            "margl": "Linear Margin", "profl": "Linear Profile", 
            "nickn": "Nick Narrow" }
    if "all" in selected:
        selected=algos.keys()

    R,T={},{}
    for a in algos.keys():
        R[a],T[a]={},{}
        for i in range(2,bmax+1):
            T[a][i]=[]
            R[a][i]=[]

    skip=[]
    for row in data:
        nbins =  len(row["bins"]) 
        xv.append ( nbins )

        denom=row["ul_nick"]
        if denominator=="mean":
            denom=numpy.mean ( [row["ul_nick"],row["ul_prof"],row["ul_marg10"] ] )
        else:
            denom= row[f"ul_{denominator}" ]

        for a in algos.keys():
            T[a][nbins].append( row[f"t_{a}" ] )
            r = row[f"ul_{a}" ]
            if type(r)==float:
                R[a][nbins].append( row[f"ul_{a}" ] / denom )
            else:
                print ( f"skipping ul: {r}" )

    def mean ( Rx ):
        x=[]
        for k,v in Rx.items():
            for i in v:
                x.append ( i )
        return numpy.mean(x), numpy.std(x)

    fig,ax=plt.subplots()
    #print ( "skipped points %s" % skip )
    plt.scatter ( xv, [ random.uniform(.8,1.2) for x in xv ], c='w' )
    for a,c in algos.items():
        print ( descs[a], mean ( R[a] ) )
        if a in selected: 
            addLine( ax, R[a], c, descs[a], ul=True )
    plt.legend (  )
    plt.xlabel ( "number of signal regions" )
    plt.ylabel ( "ul / ul(nick)" )
    if plot in [ "all", "comp" ]:
        plt.savefig ( "comp.png" )
    plt.clf()
    fig,ax=plt.subplots()
    M = max([numpy.mean(x+[0]) for x in T["marg10"].values()]) 
    print ( "max", M )
    plt.scatter ( [ i - .1 for i in xv ], [ random.uniform(0,M) for x in xv ], c='w' )

    for a,c in algos.items():
        if a in selected: 
            addLine( ax, T[a], c, descs[a] )
    plt.xlabel ( "number of signal regions" )
    plt.ylabel ( "time per point [s]" )
    plt.legend (  )
    if plot in [ "all", "t" ]:
        fig.savefig ( "t.png" )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser( description="Draw various validation plots" )
    ap.add_argument('-N', '--nruns', type=int, default=1000, 
                    help="which result file to access (result<nruns>.py)" )
    ap.add_argument('-a', '--algos', type=str, default="all",
                    help="which algos to plot (comma separated, or all)" )
    ap.add_argument('-p', '--plots', type=str, default="all",
                    help="which plots (comp,t,all)" )
    ap.add_argument('-d', '--denominator', type=str, default="nick",
                    help="which algo is the denominator" )
    args=ap.parse_args()
    run ( args.nruns, [ x.strip() for x in args.algos.split(",") ], 
          args.denominator, args.plots )
