#!/usr/bin/python3

from __future__ import print_function
import sys, os, time
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
from smodels.base.smodelsLogging import setLogLevel
from smodels.base.physicsUnits import TeV
from smodels.tools.colors import colors
import ROOT
import IPython
import ctypes

ROOT.gStyle.SetOptStat(0000)

ROOT.gROOT.SetBatch()
cols = [ ROOT.kRed, ROOT.kWhite, ROOT.kGreen ]
ROOT.gStyle.SetPalette(len(cols), (ctypes.c_int * len(cols))(*cols) )
ROOT.gStyle.SetNumberContours(len(cols))

ROOT.gStyle.SetPadLeftMargin(.25)

colors.on = True
setLogLevel ( "debug" )

#dir = "/home/walten/git/smodels/test/database/"
dir = "/home/walten/git/smodels-database/"
d=Database( dir )
print(d)
results = d.getExpResults()
#results.sort()
nres = len ( results )

ROOT.c1=ROOT.TCanvas("c1","c1",1600,1500)
ROOT.c1.SetLeftMargin(0.17)
ROOT.c1.SetBottomMargin(0.17)

h=ROOT.TH2F ( "Correlations", 
              "Correlations between analyses (green is uncorrelated)", 
              nres, 0., nres, nres, 0., nres )
xaxis = h.GetXaxis()
yaxis = h.GetYaxis()
xaxis.SetLabelSize(.02)
yaxis.SetLabelSize(.02)

def hasLLHD ( analysis ) : 
    """ can one create likelihoods from analyses?
        true for efficiency maps and upper limits with expected values. """
    if len ( analysis.datasets)>1:
        return True

    ds=analysis.datasets[0]
    if ds.dataInfo.dataType=="efficiencyMap":
        return True
    for tx in ds.txnameList:
        if tx.hasLikelihood():
            return True
    return False


for x,e in enumerate(results):
    label = e.globalInfo.id
    hasLikelihood = hasLLHD ( e )
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
        if not hasLikelihood or not hasLLHD ( f ): ## has no llhd? cannot be combined
            h.SetBinContent ( x+1, y+1, 0. )

h.Draw("col")
ROOT.gPad.SetGrid()
ROOT.c1.Print("matrix.png" )
ROOT.c1.Print("matrix.pdf" )
#IPython.embed()
