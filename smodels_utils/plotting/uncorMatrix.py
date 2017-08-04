#!/usr/bin/python3

from __future__ import print_function
import sys, os, time
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.experiment.exceptions import SModelSExperimentError
from smodels.tools.smodelsLogging import setLogLevel
from smodels.tools.colors import colors
from smodels.tools.physicsUnits import pb, fb, GeV
from smodels.theory import slhaDecomposer
import ROOT

ROOT.gStyle.SetOptStat(0000)

colors.on = True
setLogLevel ( "debug" )

dir = "/home/walten/git/smodels/test/database/"
d=Database( dir, discard_zeroes = True )
print(d)
results = d.getExpResults()
nres = len ( results )

h=ROOT.TH2F ( "Correlations", "Correlations", nres, 0., nres, nres, 0., nres )
xaxis = h.GetXaxis()
yaxis = h.GetYaxis()

for x,e in enumerate(results):
    xaxis.SetBinLabel(x+1,e.globalInfo.id )
    yaxis.SetBinLabel(x+1,e.globalInfo.id )
    for y,f in enumerate(results):
        isUn = e.isUncorrelatedWith ( f )
        if isUn:
            h.SetBinContent ( x+1, y+1, 1 )
        print ( e.globalInfo.id, f.globalInfo.id, isUn )

h.Draw("colz")
ROOT.c1.Print("matrix.png" )
