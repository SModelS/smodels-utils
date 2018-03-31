#!/usr/bin/python

""" draw comparison between profiling, marginalizing and Nicks """

from __future__ import print_function
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import sys
import random
import numpy
n=20

if len(sys.argv)>1:
    n=int(sys.argv[1])

D=__import__("results%d" % n )
data=D.d
#from results20 import d as data

#max number of bins
bmax = max( [ x["nbins"] for x in data ] )

xv,ym,yp,ym10,ymn=[],[],[],[],[]

algos={ "nick": "k", "nickn": "k", "marg": "b", "marg10": "g", "prof": "r" }
descs={ "nick": "Nick", "nickn": "Nick Lin", "prof": "Profile",
        "marg": "Margin", "marg10": "Margin 10K" }

T={}
for a in algos.keys():
    T[a]={}
    for i in range(2,bmax+1):
        T[a][i]=[]

skip=[]
for row in data:
    ulnick=row["ul_nick"] 
    ulnickn=row["ul_nickn"] 
    ulm=row["ul_marg"]
    ulm10=row["ul_marg10"]
    ulp=row["ul_prof"]
    if (ulp/ulnick-1)>.3:
        print ( "Outlier found. #%d, ul(nick)=%s, ul(prof)=%s, ul(marg)=%s, r=%s" % ( row["#"], ulnick, ulp, ulm, ulp/ulnick ) )
    if type(ulm)!=float or type(ulp)!=float or type(ulnick)!=float or abs ( ulm/ulnick - 1 ) > .3 or ulp<0.:
        skip.append( row["#"] )
        continue
    nbins =  len(row["bins"]) 
    xv.append ( nbins )
    ym.append ( ulm/ulnick )
    yp.append ( ulp/ulnick )
    ym10.append ( ulm10/ulnick )
    ymn.append ( ulnickn/ulnick )

    for a in algos.keys():
        T[a][nbins].append( row["t_%s" % a ] )

print ( "skipped points %s" % skip )
print ( descs["marg"], numpy.mean ( ym ), numpy.std ( ym ) )
print ( descs["prof"], numpy.mean ( yp ), numpy.std ( yp ) )
print ( descs["marg10"], numpy.mean ( ym10 ), numpy.std ( ym10 ) )
print ( descs["nickn"], numpy.mean ( ymn ), numpy.std ( ymn ) )
plt.scatter ( [ i - .1 for i in xv ], ym )
plt.scatter ( [ i + .1 for i in xv ], yp )
plt.scatter ( [ i + .1 for i in xv ], ym10 )
plt.legend ( [ descs["marg"], descs["prof"], descs["marg10"] ] )
plt.xlabel ( "number of signal regions" )
plt.ylabel ( "ul / ul(nick)" )
plt.savefig ( "comp.png" )
plt.clf()
fig,ax=plt.subplots()
M = max([numpy.mean(x+[0]) for x in T["marg10"].values()]) 
print ( "max", M )
plt.scatter ( [ i - .1 for i in xv ], [ random.uniform(0,M) for x in xv ], c='w' )

legends=[]

def addLine ( X, c, legend, style='-' ):
    l =Line2D ( list(X.keys()), [ numpy.mean(X[x]) for x in X.keys() ], c=c, linestyle=style, label=legend )
    ax.add_line(l)
    alpha=.2
    lp =Line2D ( list(X.keys()), [ numpy.mean(X[x])+numpy.std(X[x]) for x in X.keys() ], c=c, 
                 linestyle=':', alpha=alpha )
    ax.add_line(lp)
    lm =Line2D ( list(X.keys()), [ numpy.mean(X[x])-numpy.std(X[x]) for x in X.keys() ], c=c, 
                 linestyle=':', alpha=alpha )
    ax.add_line(lm)

for a,c in algos.items():
    addLine( T[a], c, descs[a] )
plt.xlabel ( "number of signal regions" )
plt.ylabel ( "time per point [s]" )
plt.legend (  )
fig.savefig ( "t.png" )

