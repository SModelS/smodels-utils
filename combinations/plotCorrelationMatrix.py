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
    gray = 42 ## thats gold
    gray = 17
    cols = [ ROOT.kRed+1, ROOT.kWhite, ROOT.kGreen+1, gray, ROOT.kBlack ]
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

    h=ROOT.TH2F ( "Correlations", "",
                  nres, 0., nres, nres, 0., nres )
    xaxis = h.GetXaxis()
    yaxis = h.GetYaxis()
    xaxis.SetLabelSize(.014)
    yaxis.SetLabelSize(.014)

    bins= { "CMS": { 8: [999,0], 13:[999,0] }, 
            "ATLAS": { 8: [999,0], 13: [999,0] } }

    for x,e in enumerate(results):
        label = e.globalInfo.id
        hasLikelihood = hasLLHD ( e )
        ana = analysisCombiner.getExperimentName ( e.globalInfo )
        #if not hasLikelihood:
        #    print ( "no likelihood: %s" % label )
        sqrts = int(e.globalInfo.sqrts.asNumber(TeV))
        color = ROOT.kCyan+2
        ymax=0
        if ana == "ATLAS":
            color = ROOT.kBlue+1
        if sqrts > 10.:
            color += 2
        if x < bins[ana][sqrts][0]:
            bins[ana][sqrts][0]=x
        if x > bins[ana][sqrts][1]:
            bins[ana][sqrts][1]=x
            ymax=x
        color = ROOT.kGray+2
        n = len(results )
        label = "#color[%d]{%s}" % (color, label )
        xaxis.SetBinLabel(n-x, label )
        yaxis.SetBinLabel(x+1, label )
        for y,f in enumerate(results):
            if trianglePlot and y>x:
                continue
            isUn = analysisCombiner.canCombine ( e.globalInfo, f.globalInfo, strategy )
            # isUn = e.isUncorrelatedWith ( f )
            if isUn:
                h.SetBinContent ( n-x, y+1, 1. )
            else:
                h.SetBinContent ( n-x, y+1, -1. )
            if not hasLikelihood or not hasLLHD ( f ): ## has no llhd? cannot be combined
                h.SetBinContent ( n-x, y+1, 2. )
            if y==x:
                h.SetBinContent ( n-x, y+1, 3. )

    h.Draw("col")
    ROOT.bins, ROOT.xbins, ROOT.lines = {}, {}, []
    for ana in [ "CMS", "ATLAS" ]:
        for sqrts in [ 8, 13 ]:
            name= "%s%d" % ( ana, sqrts )
            ROOT.bins[name] = ROOT.TLatex()
            ROOT.bins[name].SetTextColorAlpha(ROOT.kBlack,.7)
            ROOT.bins[name].SetTextSize(.025)
            ROOT.bins[name].SetTextAngle(90.)
            ROOT.xbins[name] = ROOT.TLatex()
            ROOT.xbins[name].SetTextColorAlpha(ROOT.kBlack,.7)
            ROOT.xbins[name].SetTextSize(.025)
            xcoord = .5 * ( bins[ana][sqrts][0] + bins[ana][sqrts][1] ) 
            ycoord = n- .5 * ( bins[ana][sqrts][0] + bins[ana][sqrts][1] )
            ycoord = ycoord - .7 * ( bins[ana][sqrts][1] - bins[ana][sqrts][0] ) + 6
            ycoord = n - bins[ana][sqrts][1]
            if ycoord < 3:
                ycoord=3
            ROOT.bins[name].DrawLatex(-4,xcoord-3,"#splitline{%s}{%d TeV}" % ( ana, sqrts ) )
            ROOT.xbins[name].DrawLatex(ycoord,-5,"#splitline{%s}{%d TeV}" % ( ana, sqrts ) )
            yt = bins[ana][sqrts][1] +1 
            line = ROOT.TLine ( -1, yt, n-yt, yt )
            line.SetLineWidth(2)
            line.Draw()
            xline = ROOT.TLine ( yt, n-yt, yt, -1 )
            xline.SetLineWidth(2)
            xline.Draw()
            ROOT.lines.append ( line )
            ROOT.lines.append ( xline )
    for i in range(n+1):
        wline = ROOT.TLine ( n, i, n-i, i )
        wline.SetLineColor ( ROOT.kWhite )
        wline.Draw ()
        ROOT.lines.append ( wline )
        vline = ROOT.TLine ( i, n-i, i, n )
        vline.SetLineColor ( ROOT.kWhite )
        vline.Draw ()
        ROOT.lines.append ( vline )
    ROOT.title = ROOT.TLatex()
    ROOT.title.SetNDC()
    ROOT.title.SetTextSize(.025 )
    ROOT.title.DrawLatex(.30,.89, "#font[0]{Correlations between analyses, combination strategy: ,,%s''}" % strategy )
    ROOT.tl=ROOT.TLatex()
    ROOT.tl.SetNDC()
    ROOT.tl.SetTextSize(.022)
    ROOT.tl.DrawLatex(.82,.82,"#splitline{#splitline{#color[417]{#bullet uncorrelated}}{#color[633]{#bullet correlated}}}{#color[16]{#bullet no likelihood}}" )
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
