#!/usr/bin/env python3

from __future__ import print_function
import sys, os, time
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
from smodels.tools.physicsUnits import TeV
from smodels.tools.colors import colors
from smodels_utils.helper.various import hasLLHD
import analysisCombiner
import ROOT
import IPython
import ctypes

def sortOutDupes ( results ):
    """ If an analysis id appears more than once in the list,
    keep only the one with likelihoods. """
    isIn = set() ## mark result as being "in"
    ids = set() ## the analysis ids that are already in isIn
    ids_withoutLLHD = set()
    ret_withoutLLHD = {}
    for res in results:
        ID = res.globalInfo.id
        if ID in ids: ## already in
            continue
        hasllhd = hasLLHD ( res )
        if hasllhd and not ID in ids:
            ## not in and should be in: add!
            ids.add ( ID )
            isIn.add ( res.globalInfo.path )
            continue
        if not ID in ids and not hasllhd:
            ## not in but shouldnt be in: add to waiting list
            ids_withoutLLHD.add ( ID )
            ret_withoutLLHD[ID]= res.globalInfo.path
    for i in ids_withoutLLHD:
        if not i in ids: ## nothing with llhd is in, so add!
            isIn.add ( ret_withoutLLHD[i] )
            ids.add ( i )
    ## now sort them like in the original container!
    ret = []
    for res in results:
        if res.globalInfo.path in isIn:
            ret.append ( res )
    return ret

def draw( strategy, databasepath, trianglePlot=True ):
    """
    :param trianglePlot: if True, then only plot the upper triangle of this
                         symmetrical matrix
    """
    ROOT.gStyle.SetOptStat(0000)

    ROOT.gROOT.SetBatch()
    cols = [ ROOT.kRed, ROOT.kWhite, ROOT.kGreen, ROOT.kGray, ROOT.kBlack ]
    ROOT.gStyle.SetPalette(len(cols), (ctypes.c_int * len(cols))(*cols) )
    ROOT.gStyle.SetNumberContours(len(cols))

    ROOT.gStyle.SetPadLeftMargin(.25)

    colors.on = True
    setLogLevel ( "debug" )

    # dir = "/home/walten/git/smodels-database/"
    dir = databasepath
    d=Database( dir, discard_zeroes = True )
    print(d)
    results = d.getExpResults()
    results = sortOutDupes ( results )

    #results.sort()
    nres = len ( results )

    ROOT.c1=ROOT.TCanvas("c1","c1",1600,1500)
    #ROOT.c1.SetLeftMargin(0.17)
    #ROOT.c1.SetBottomMargin(0.17)
    ROOT.c1.SetLeftMargin(0.12)
    ROOT.c1.SetBottomMargin(0.15)
    ROOT.c1.SetTopMargin(0.09)
    ROOT.c1.SetRightMargin(0.015)

    h=ROOT.TH2F ( "Correlations", 
                  "Correlations between analyses, combination strategy: ,,%s''" % strategy, 
                  nres, 0., nres, nres, 0., nres )
    xaxis = h.GetXaxis()
    yaxis = h.GetYaxis()
    xaxis.SetLabelSize(.014)
    yaxis.SetLabelSize(.014)

    for x,e in enumerate(results):
        label = e.globalInfo.id
        hasLikelihood = hasLLHD ( e )
        ana = analysisCombiner.getExperimentName ( e.globalInfo )
        if not hasLikelihood:
            print ( "no likelihood: %s" % label )
        sqrts = e.globalInfo.sqrts.asNumber(TeV)
        color = ROOT.kCyan+2
        if ana == "ATLAS":
            color = ROOT.kBlue+1
        if sqrts > 10.:
            color += 2
        label = "#color[%d]{%s}" % (color, label )
        xaxis.SetBinLabel(x+1, label )
        yaxis.SetBinLabel(x+1, label )
        for y,f in enumerate(results):
            if trianglePlot and y<x:
                continue
            isUn = analysisCombiner.canCombine ( e.globalInfo, f.globalInfo, strategy )
            # isUn = e.isUncorrelatedWith ( f )
            if isUn:
                h.SetBinContent ( x+1, y+1, 1. )
            else:
                h.SetBinContent ( x+1, y+1, -1. )
            if not hasLikelihood or not hasLLHD ( f ): ## has no llhd? cannot be combined
                h.SetBinContent ( x+1, y+1, 2. )
            if y==x:
                h.SetBinContent ( x+1, y+1, 3. )

    h.Draw("col")
    ROOT.tl=ROOT.TLatex()
    ROOT.tl.SetNDC()
    ROOT.tl.SetTextSize(.02)
    ROOT.tl.DrawLatex(.1,.92,"green: uncorrelated, red: correlated, gray: no likelihood" )
    ROOT.gPad.SetGrid()
    print ( "Plotting to matrix_%s.png" % strategy )
    ROOT.c1.Print("matrix_%s.png" % strategy )
    ROOT.c1.Print("matrix_%s.pdf" % strategy )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description="correlation/combination matrix plotter")
    argparser.add_argument ( '-s', '--strategy', nargs='?', 
            help='combination strategy [aggressive]', type=str, default='aggressive' )
    argparser.add_argument ( '-d', '--database', nargs='?', 
            help='path to database [../../smodels-database]',
            type=str, default='../../smodels-database' )
    args=argparser.parse_args()
    draw( args.strategy, args.database )
