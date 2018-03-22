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

xv,ym,yp,ym10,ymn=[],[],[],[],[]
Tn,Tm,Tp,Tnn,Tm10={},{},{},{},{}
for i in range(20):
    Tn[i]=[]
    Tm[i]=[]
    Tp[i]=[]
    Tnn[i]=[]
    Tm10[i]=[]

skip=[]
for row in data:
    ulnick=row["ul_nick"] 
    ulnickn=row["ul_nickn"] 
    ulm=row["ul_marg"]
    ulm10=row["ul_marg10"]
    ulp=row["ul_prof"]
    if type(ulm)!=float or type(ulp)!=float or type(ulnick)!=float or abs ( ulm/ulnick - 1 ) > .3:
        skip.append( row["#"] )
        continue
    nbins =  len(row["bins"]) 
    xv.append ( nbins )
    ym.append ( ulm/ulnick )
    yp.append ( ulp/ulnick )
    ym10.append ( ulm10/ulnick )
    ymn.append ( ulnickn/ulnick )
    Tn[nbins].append ( row["t_nick"] )
    Tnn[nbins].append ( row["t_nickn"] )
    Tm10[nbins].append ( row["t_marg10"] )
    Tm[nbins].append ( row["t_marg"] )
    Tp[nbins].append ( row["t_prof"] )

print ( "skipped points %s" % skip )
print ( "marginalizing", numpy.mean ( ym ), numpy.std ( ym ) )
print ( "profiling    ", numpy.mean ( yp ), numpy.std ( yp ) )
print ( "marginalizing 10K", numpy.mean ( ym10 ), numpy.std ( ym10 ) )
print ( "Nick narrow ", numpy.mean ( ymn ), numpy.std ( ymn ) )
plt.scatter ( [ i - .1 for i in xv ], ym )
plt.scatter ( [ i + .1 for i in xv ], yp )
plt.scatter ( [ i + .1 for i in xv ], ym10 )
plt.legend ( [ "marginalizing", "profiling", "marginalizing 10K" ] )
plt.savefig ( "comp.png" )
plt.xlabel ( "number of signal regions" )
plt.ylabel ( "ul / ul(nick)" )
plt.clf()
fig,ax=plt.subplots()
print ( "Tn values",len(Tn.values()) )
print ( "Tn keys",len(Tn.keys()) )
print ( "Tn keys",len( [ numpy.mean(x) for x in Tn.values() ] ) )
M = max([numpy.mean(x+[0]) for x in Tm10.values()]) 
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

addLine ( Tn,  'k', "Nick" )
addLine ( Tnn, 'k', "Nick Narrow", '-.' )
addLine ( Tp, 'r', "Profiling" )
addLine ( Tm, 'g', "Marginalizing" )
addLine ( Tm10, 'cyan', "Marginal 10k" )
plt.xlabel ( "number of signal regions" )
plt.ylabel ( "time per point [s]" )
plt.legend (  )
fig.savefig ( "t.png" )

