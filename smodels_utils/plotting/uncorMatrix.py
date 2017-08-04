#!/usr/bin/python3

from __future__ import print_function
import sys, os, time
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
from smodels.tools.colors import colors
import ROOT
import IPython

ROOT.gStyle.SetOptStat(0000)
ROOT.gStyle.SetPalette(1)
ROOT.gStyle.SetNumberContours(2)
ROOT.gStyle.SetPadLeftMargin(.25)

colors.on = True
setLogLevel ( "debug" )

dir = "/home/walten/git/smodels/test/database/"
d=Database( dir, discard_zeroes = True )
print(d)
results = d.getExpResults()
nres = len ( results )

ROOT.c1=ROOT.TCanvas("c1","c1",640,480)
ROOT.c1.SetLeftMargin(0.19)

h=ROOT.TH2F ( "Correlations", "Correlations between analyses", nres, 0., nres, nres, 0., nres )
xaxis = h.GetXaxis()
yaxis = h.GetYaxis()

for x,e in enumerate(results):
    xaxis.SetBinLabel(x+1,e.globalInfo.id )
    yaxis.SetBinLabel(x+1,e.globalInfo.id )
    for y,f in enumerate(results):
        isUn = e.isUncorrelatedWith ( f )
        if isUn:
            h.SetBinContent ( x+1, y+1, 1e-5 )
        else:
            h.SetBinContent ( x+1, y+1, 1. )
        print ( e.globalInfo.id, f.globalInfo.id, isUn )

h.Draw("col")
ROOT.gPad.SetGrid()
ROOT.c1.Print("matrix.png" )
ROOT.c1.Print("matrix.pdf" )
#IPython.embed()
