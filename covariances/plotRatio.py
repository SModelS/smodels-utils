#!/usr/bin/python

""" Plot the ratio between the upper limit from the UL map, and our 
own upper limit computed from combining the efficiency maps. """

import CMS16050.T2tt_5 as FromEff
import CMS16050.T2tt_ul as FromUl
import math
import matplotlib.pyplot as plt

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


x,y,col=[],[],[]

for point in FromEff.validationData:
    axes = point["axes"]
    h = axisHash ( axes )
    ul = None
    if h in uls.keys():
        ul = uls[h]
    # print "ul", axes, point["UL"], point["UL"] / point["efficiency"], ul
    if ul:
        ul_eff = point["UL"] / point["efficiency"]
        ratio = ul_eff / ul
        # ratio = math.log10 ( ul )
        x.append ( axes[1] )
        y.append ( axes[0] )
        col.append ( ratio )

cm = plt.cm.get_cmap('RdYlBu')
scatter = plt.scatter ( x, y, c=col, cmap=cm )
plt.rc('text', usetex=True)
plt.title ( "Ratio UL(eff) / UL(official), CMS-SUS-16-050, T2tt" )
plt.xlabel ( "m$_{mother}$ [GeV]" )
plt.ylabel ( "m$_{LSP}$ [GeV]" )
plt.colorbar()
plt.savefig ( "ratio.png" )
# plt.show()
