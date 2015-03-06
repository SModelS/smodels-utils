#!/usr/bin/env python

"""
.. module:: plotRanges
   :synopsis: Given a TGraph object, returns a simple list of points to probe for validation.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import ROOT
import numpy

def getPoints ( tgraph ):
    """ given a TGraph object, returns list of points to probe """
    minx, miny = float("inf"), float("inf")
    maxx, maxy = 0., 0.
    for i in range(tgraph.GetN()):
        x, y = ROOT.Double(), ROOT.Double()
        tgraph.GetPoint(i,x,y) 
        if x<minx: minx=x
        if y<miny: miny=y
        if x>maxx: maxx=x
        if y>maxy: maxy=y
    minx=0.8*minx
    miny=0.9*miny
    maxx=1.2*maxx
    maxy=1.2*maxy
    dx=(maxx-minx)/30.
    dy=(maxy-miny)/20.
    points=[]
    for i in numpy.arange ( minx, maxx+dx/2., dx ):
        for j in numpy.arange ( miny, maxy+dy/2., dy ):
            points.append ( [i,j] )
    return points

def draw ( graph, points ):
    # container=[]
    t=ROOT.TGraph()
    for ctr,point in enumerate(points):
        print "draw",point
        # t=ROOT.TMarker ( point[0], point[1], 23 )
        # t.Draw()
        # container.append(t)
        t.SetPoint(ctr,point[0],point[1])
    t.Draw("AP")
    graph.Draw("same")
    ROOT.c1.Print("save.png")

if __name__ == "__main__":
    filename="/home/walten/git/smodels-database/8TeV/ATLAS/ATLAS-SUSY-2013-19/sms.root"
    f=ROOT.TFile(filename)
    graph=f.Get("T2tt/exclusion_2*Eq(mother,x)_Eq(lsp,y)")
    pts = getPoints ( graph )
    draw ( graph, pts )
