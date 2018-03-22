#!/usr/bin/python

""" draw comparison between profiling, marginalizing and Nicks """

from __future__ import print_function
import matplotlib.pyplot as plt
import sys
n=20

if len(sys.argv)>1:
    n=int(sys.argv[1])

D=__import__("results%d" % n )
data=D.d
#from results20 import d as data

x,ym,yp=[],[],[]

skip=[]
for row in data:
    ulnick=row["ul_nick"] 
    ulm=row["ul_marg"]
    ulp=row["ul_prof"]
    if type(ulm)!=float or type(ulp)!=float or type(ulnick)!=float or abs ( ulm/ulnick - 1 ) > .3:
        skip.append( row["#"] )
        continue
    x.append ( len(row["bins"]) )
    ym.append ( ulm/ulnick )
    yp.append ( ulp/ulnick )

print ( "skipped points %s" % skip )
plt.scatter ( [ i - .1 for i in x ], ym )
plt.scatter ( [ i + .1 for i in x ], yp )
plt.legend ( [ "marginalizing", "profiling" ] )
plt.savefig ( "comp.png" )
