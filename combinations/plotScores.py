#!/usr/bin/env python3

import matplotlib.pyplot as plt

def main():
    with open("scores.csv") as f:
        lines=f.readlines()
    x,y=[],[]
    for l in lines:
        t = list ( map ( float, l.split(",") ) )
        x.append(t[1])
        y.append(t[2])
    plt.scatter ( x, y )
    plt.xlabel ( "predicted" )
    plt.ylabel ( "true" )
    plt.savefig ( "scatter.png" )


main()
