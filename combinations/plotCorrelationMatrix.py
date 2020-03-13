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

def sortBySqrts ( results, sqrts ):
    ret = []
    for res in results:
        if abs (res.globalInfo.sqrts.asNumber(TeV) - sqrts ) < 0.1:
            ret.append ( res )
    return ret

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

def draw( strategy, databasepath, trianglePlot, miscol,
          diagcol, experiment, S ):
    """
    :param trianglePlot: if True, then only plot the upper triangle of this
                         symmetrical matrix
    :param miscol: color to use when likelihood is missing
    :param diagcol: color to use for diagonal
    :param experiment: draw only for specific experiment ("CMS", "ATLAS", "all" )
    :param S: draw only for specific sqrts ( "8", "13", "all" )
    """
    ROOT.gStyle.SetOptStat(0000)

    ROOT.gROOT.SetBatch()
    cols = [ ROOT.kRed+1, ROOT.kWhite, ROOT.kGreen+1, miscol, diagcol ]
    ROOT.gStyle.SetPalette(len(cols), (ctypes.c_int * len(cols))(*cols) )
    ROOT.gStyle.SetNumberContours(len(cols))

    ROOT.gStyle.SetPadLeftMargin(.25)

    sqrtses = [ 8, 13 ]
    if S not in [ "all" ]:
        sqrtses = [ int(S) ]

    colors.on = True
    setLogLevel ( "debug" )

    # dir = "/home/walten/git/smodels-database/"
    dir = databasepath
    d=Database( dir, discard_zeroes = True )
    print(d)
    analysisIds = [ "all" ]
    exps = [ "CMS", "ATLAS" ]
    if experiment in [ "CMS", "ATLAS" ]:
        analysisIds = [ experiment+"*" ]
        exps = [ experiment ]
    results = d.getExpResults( analysisIDs = analysisIds )
    results = sortOutDupes ( results )
    if S in [ "8", "13" ]:
        results = sortBySqrts ( results, int(S) )

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

    n = len(results )
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
    for ana in exps:
        for sqrts in sqrtses:
            name= "%s%d" % ( ana, sqrts )
            ROOT.bins[name] = ROOT.TLatex()
            ROOT.bins[name].SetTextColorAlpha(ROOT.kBlack,.7)
            ROOT.bins[name].SetTextSize(.025)
            ROOT.bins[name].SetTextAngle(90.)
            ROOT.xbins[name] = ROOT.TLatex()
            ROOT.xbins[name].SetTextColorAlpha(ROOT.kBlack,.7)
            ROOT.xbins[name].SetTextSize(.025)
            xcoord = .5 * ( bins[ana][sqrts][0] + bins[ana][sqrts][1] )
            ycoord = n- .5 * ( bins[ana][sqrts][0] + bins[ana][sqrts][1] ) -3
            ROOT.bins[name].DrawLatex(-4,xcoord-3,"#splitline{%s}{%d TeV}" % ( ana, sqrts ) )
            ROOT.xbins[name].DrawLatex(ycoord,-5,"#splitline{%s}{%d TeV}" % ( ana, sqrts ) )
            yt = bins[ana][sqrts][1] +1
            extrudes = 3 # how far does the line extrude into tick labels?
            xmax = n
            if trianglePlot:
                xmax = n-yt
            line = ROOT.TLine ( -extrudes, yt, xmax, yt )
            line.SetLineWidth(2)
            line.Draw()
            ymax = n
            if trianglePlot:
                ymax = yt
            xline = ROOT.TLine ( n-yt, ymax, n-yt, -extrudes )
            xline.SetLineWidth(2)
            xline.Draw()
            ROOT.lines.append ( line )
            ROOT.lines.append ( xline )
    line = ROOT.TLine ( -extrudes, 0, xmax, 0 )
    line.SetLineWidth(2)
    line.Draw()
    xline = ROOT.TLine ( n, ymax, n, -extrudes )
    xline.SetLineWidth(2)
    xline.Draw()
    ROOT.lines.append ( line )
    ROOT.lines.append ( xline )
    if trianglePlot:
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
        ROOT.title.DrawLatex(.28,.89, "#font[132]{Correlations between analyses, combination strategy: ,,%s''}" % strategy )
    ROOT.boxes = []
    if trianglePlot:
        for i,b in enumerate ( [ "pair is uncorrelated", "pair is correlated", "likelihood is missing" ] ):
            bx = 51
            by = 68 - 3*i
            box = ROOT.TBox(bx,by,bx+1,by+1)
            c = cols[i]
            if i > 0:
                c = cols[i+1]
            box.SetFillColor ( c )
            box.Draw()
            ROOT.boxes.append ( box )
            l = ROOT.TLatex()
            l.SetTextSize(.022)
            #if i == 2:
            #    c = 16
            l.SetTextColor ( c )
            b="#font[132]{%s}" % b ## add font
            l.DrawLatex ( bx+2, by, b )
            ROOT.boxes.append ( l )
    ROOT.gPad.SetGrid()
    print ( "Plotting to matrix_%s.png" % strategy )
    ROOT.c1.Print("matrix_%s.png" % strategy )
    ROOT.c1.Print("matrix_%s.pdf" % strategy )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description="correlation/combination matrix plotter")
    argparser.add_argument ( '-S', '--strategy', nargs='?',
            help='combination strategy [aggressive]', type=str, default='aggressive' )
    argparser.add_argument ( '-d', '--database', nargs='?',
            help='path to database [../../smodels-database]',
            type=str, default='../../smodels-database' )
    argparser.add_argument ( '-e', '--experiment', nargs='?',
            help='plot only specific experiment CMS,ATLAS,all [all]',
            type=str, default='all' )
    argparser.add_argument ( '-s', '--sqrts', nargs='?',
            help='plot only specific sqrts 8,13,all [all]',
            type=str, default='all' )
    argparser.add_argument ( '-t', '--triangular',
            help='plot as lower triangle matrix?',
            action="store_true" )
    args=argparser.parse_args()
    miscol = 42 ## missing likelihood color, golden
    miscol = ROOT.kWhite ## missing likelihood color, white
    diagcol = ROOT.kBlack
    diagcol = ROOT.kGray
    draw( args.strategy, args.database, args.triangular, miscol, diagcol,
          args.experiment, args.sqrts )
