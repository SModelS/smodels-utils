#!/usr/bin/python3

from __future__ import print_function
import sys, os, time
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
from smodels.tools.physicsUnits import TeV
from smodels.tools.colors import colors
import ROOT
import IPython
import ctypes

ROOT.gStyle.SetOptStat(0000)
cols = [ ROOT.kRed, ROOT.kWhite, ROOT.kGreen ]
ROOT.gStyle.SetPalette(len(cols), (ctypes.c_int * len(cols))(*cols) )
ROOT.gStyle.SetNumberContours(len(cols))

ROOT.gStyle.SetPadLeftMargin(.25)

colors.on = True
setLogLevel ( "debug" )

#dir = "/home/walten/git/smodels/test/database/"
dir = "/home/walten/git/smodels-database/"
d=Database( dir, discard_zeroes = True )
print(d)
results = d.getExpResults()
#results.sort()
nres = len ( results )

ROOT.c1=ROOT.TCanvas("c1","c1",1600,1500)
ROOT.c1.SetLeftMargin(0.17)
ROOT.c1.SetBottomMargin(0.17)

h=ROOT.TH2F ( "Correlations", "Correlations between analyses (green is uncorrelated)", nres, 0., nres, nres, 0., nres )
xaxis = h.GetXaxis()
yaxis = h.GetYaxis()
xaxis.SetLabelSize(.02)
yaxis.SetLabelSize(.02)

for x,e in enumerate(results):
    label = e.globalInfo.id
    if e.globalInfo.sqrts.asNumber(TeV) > 10.:
        label = "#color[12]{%s}" % e.globalInfo.id#+ "[%d]" % e.globalInfo.sqrts.asNumber(TeV)
    xaxis.SetBinLabel(x+1, label )
    yaxis.SetBinLabel(x+1, label )
    for y,f in enumerate(results):
        isUn = e.isUncorrelatedWith ( f )
        if isUn:
            h.SetBinContent ( x+1, y+1, 1. )
        else:
            h.SetBinContent ( x+1, y+1, -1. )
        if y==x:
            h.SetBinContent ( x+1, y+1, 0. )
        print ( e.globalInfo.id, f.globalInfo.id, isUn )

h.Draw("col")
ROOT.gPad.SetGrid()
ROOT.c1.Print("matrix.png" )
ROOT.c1.Print("matrix.pdf" )
#IPython.embed()
