#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import math, time

def main():
    with open("scores.csv") as f:
        lines=f.readlines()
    x,y=[],[]
    epoch = 0
    dlta = 0.
    for l in lines:
        t = list ( map ( float, l.split(",") ) )
        x.append(t[1])
        y.append(t[2])
        dlta += ( t[1]-t[2] )**2
        epoch = t[0]
    dlta = math.sqrt( dlta/len(x) )
    plt.scatter ( x, y, s=.1 )
    plt.plot ( [0,2.8], [0,2.8], 'r--' )
    plt.title ( "true versus predicted Z scores, epoch %d" % epoch )
    plt.xlabel ( "predicted" )
    plt.ylabel ( "true" )
    plt.text ( 2.4, 0.2, "$\\Delta=%.2f$" % dlta ) 
    plt.text ( 2.0, 0.0, "%s" % time.asctime() ) 
    plt.savefig ( "scatter%d.png" % epoch )
    plt.savefig ( "scatter.png" )


main()
