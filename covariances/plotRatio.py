#!/usr/bin/python

""" Plot the ratio between the upper limit from the UL map, and our 
own upper limit computed from combining the efficiency maps. """

import math, os, numpy
import matplotlib.pyplot as plt

def main():
    # import CMS16050.T2tt_all as FromEff
    # import CMS16050.T2tt_ul as FromUl
    analysis, topo, srs = "CMS16052", "T4bbffff", "44"
    # analysis, topo, srs = "CMS16050", "T2tt", "all"
    FromUl = __import__ ( "%s.%s_ul" % ( analysis, topo), fromlist="%s_ul" % topo )
    FromEff = __import__ ( "%s.%s_%s" % ( analysis, topo, srs ), 
                           fromlist="%s_%s" % ( topo, srs ) )
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
        uls[ h ] = point["UL" ] / point["signal"]


    x,y,col=[],[],[]

    for point in FromEff.validationData:
        axes = point["axes"]
        h = axisHash ( axes )
        ul = None
        if h in uls.keys():
            ul = uls[h]
        # print "ul", axes, point["UL"], point["UL"] / point["efficiency"], ul
        if ul:
            ul_eff = point["UL"] / point["signal"] ##  point["efficiency"]
            ratio = ul_eff / ul
            # ratio = math.log10 ( ul )
            x.append ( axes[1] )
            y.append ( axes[0] )
            col.append ( ratio )

    cm = plt.cm.get_cmap('RdYlBu')
    scatter = plt.scatter ( x, y, c=col, cmap=cm )
    plt.rc('text', usetex=True)
    slhafile=FromEff.validationData[0]["slhafile"]
    Dir=os.path.dirname ( FromEff.__file__ )
    analysis=Dir[ Dir.rfind("/")+1: ]
    topo=slhafile[:slhafile.find("_")]

    plt.title ( "Ratio UL(eff) / UL(official), %s, %s" % ( analysis, topo) )
    plt.xlabel ( "m$_{mother}$ [GeV]" )
    plt.ylabel ( "m$_{LSP}$ [GeV]" )
    plt.colorbar()
    plt.savefig ( "ratio.png" )

    print ( "ratio=%s +/- %s" % ( numpy.mean(col), numpy.std(col) ) )
    # plt.show()

main()
