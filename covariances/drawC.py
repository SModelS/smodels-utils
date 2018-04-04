#!/usr/bin/python

""" draw comparison between profiling, marginalizing and Nicks """

from __future__ import print_function
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import sys
import random
import numpy
n=1000

if len(sys.argv)>1:
    n=int(sys.argv[1])

def addLine ( X, c, legend, style='-', ul=False ):
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

def checkN ( fname ):
    f=open(fname+".py")
    l=f.readlines()[-1]
    f.close()
    if not "]" in l[-2:]:
        f=open(fname+".py","a")
        f.write("]\n" )
        f.close()

fname="results%d" % n
checkN(fname )
D=__import__( fname )
data=D.d

#max number of bins
bmax = max( [ x["nbins"] for x in data ] )

xv=[]

algos={ "nick": "k", "nickl": "k", "marg": "b", "marg10": "cyan", "prof": "r", 
        "marg100": "g", "margl": "magenta", "profl": "orange" }
descs={ "nick": "Nick", "nickl": "Linear Nick", "prof": "Profile", "marg": "Margin", 
        "marg10": "Margin 10K", "marg100": "Margin 100", "margl": "Linear Margin",
        "profl": "Linear Profile" }

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
    for a in algos.keys():
        T[a][nbins].append( row["t_%s" % a ] )
        r = row["ul_%s" % a ]
        if type(r)==float:
            R[a][nbins].append( row["ul_%s" % a ] / denom )
        else:
            print ( "skipping ul: %s" % r )

def mean ( Rx ):
    x=[]
    for k,v in Rx.items():
        for i in v:
            x.append ( i )
    return numpy.mean(x), numpy.std(x)

fig,ax=plt.subplots()
#print ( "skipped points %s" % skip )
plt.scatter ( [ i - .1 for i in xv ], [ random.uniform(.8,1.2) for x in xv ], c='w' )
for a,c in algos.items():
    print ( descs[a], mean ( R[a] ) )
    if a not in [ "marg100" ]: ##  [ "nickl", "marg100" ]:
        addLine( R[a], c, descs[a], ul=True )
plt.legend (  )
plt.xlabel ( "number of signal regions" )
plt.ylabel ( "ul / ul(nick)" )
plt.savefig ( "comp.png" )
plt.clf()
fig,ax=plt.subplots()
M = max([numpy.mean(x+[0]) for x in T["marg10"].values()]) 
print ( "max", M )
plt.scatter ( [ i - .1 for i in xv ], [ random.uniform(0,M) for x in xv ], c='w' )

for a,c in algos.items():
    addLine( T[a], c, descs[a] )
plt.xlabel ( "number of signal regions" )
plt.ylabel ( "time per point [s]" )
plt.legend (  )
fig.savefig ( "t.png" )

