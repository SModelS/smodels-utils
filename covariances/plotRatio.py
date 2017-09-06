#!/usr/bin/python

""" Plot the ratio between the upper limit from the UL map, and our 
own upper limit computed from combining the efficiency maps. """

import CMS16050.T2tt_60 as FromEff
import CMS16050.T2tt_ul as FromUl

uls={}

def axisHash ( axes ):
    ret = 0
    axes.reverse()
    for ctr,a in enumerate(axes):
        ret += 10**(3*ctr)*int(a)
    return ret

for point in FromUl.validationData:
    axes = point["axes"]
    h = axisHash ( axes )
    uls[ h ] = point["UL" ]

for point in FromEff.validationData:
    axes = point["axes"]
    h = axisHash ( axes )
    ul = None
    if h in uls.keys():
        ul = uls[h]
    print "ul", axes, point["UL"], point["UL"] / point["efficiency"], ul
