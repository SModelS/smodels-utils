#!/usr/bin/env python3

import matplotlib.pyplot as plt

def main():
    with open("scores.csv") as f:
        lines=f.readlines()
    x,y=[],[]
    epoch = 0
    for l in lines:
        t = list ( map ( float, l.split(",") ) )
        x.append(t[1])
        y.append(t[2])
        epoch = t[0]
    plt.scatter ( x, y, s=.1 )
    plt.plot ( [0,2.8], [0,2.8], 'r--' )
    plt.title ( "true versus predicted Z scores, epoch %d" % epoch )
    plt.xlabel ( "predicted" )
    plt.ylabel ( "true" )
    plt.savefig ( "scatter%d.png" % epoch )
    plt.savefig ( "scatter.png" )


main()
