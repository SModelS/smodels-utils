#!/usr/bin/env python

"""
.. module:: validationPlot
     :synopsis: Module to create a validation plot for given grid data file. 

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


"""

from __future__ import print_function
import setPath  # # set to python path for smodels
import argparse
import os
import sys
import ROOT
import validationPlotsHelper
import logging
import types
from smodels_tools.tools.databaseBrowser import Browser

logger = logging.getLogger(__name__)

def main():
    """Handles all command line options, as:
    topology, analysis, directory, base, loglevel, ...
    Produces the validation plot.
    
    """
    argparser = argparse.ArgumentParser(description = \
    'Produces the validation plots')
    argparser.add_argument ('-b', '--Base', \
    help = 'set path to base-directory of smodels-database \n \
    - default: /afs/hephy.at/user/w/walten/public/sms/', \
    type = types.StringType, default = '/afs/hephy.at/user/w/walten/public/sms/')
    argparser.add_argument ('-a', '--analysis', \
    help = 'analysis that should be validated - default: SUS12028',\
    type = types.StringType, default = 'SUS12028')
    argparser.add_argument ('-t', '--topology', \
    help = 'topology that should be validated - default: T1',\
    type = types.StringType, default = 'T1')
    argparser.add_argument ('-o', '--order', \
    help = 'perturbation order (LO, NLO, NLL) - default: NLL', \
    type = types.StringType, default = 'NLL')
    argparser.add_argument ('-d', '--directory', \
    help = 'directory the grid data file should be taken from - default: ./gridData', \
    type = types.StringType, default = './gridData')
    argparser.add_argument ('-blog', '--browserVerbosity',\
    help = 'set browser-verbosity - default: ERROR', \
    type = types.StringType, default = 'error')
    argparser.add_argument ('-n', '--events',\
    help = 'set number of events - default: 10000', \
    type = types.IntType, default = 10000)
    argparser.add_argument ('-R', '--maxR',\
    help = 'set value for maximal R \
    (quotient of theoretical to experimental upper limit) - default: 1.0', \
    type = types.FloatType, default = 1.)
    args = argparser.parse_args()

    browser = Browser(args.Base)
    browser.verbosity = args.browserVerbosity
    topology = args.topology
    analysis = args.analysis
    targetPath = getTarget(args.directory)
    events = args.events
    order = args.order
    expRes = browser.expResult(analysis, topology)
    expAna = expRes.expAnalysis
    expTopo = expRes.expTopology
    
    #Define metadata tags:
    tags = ['decay', 'analysis', 'outFile','Kfactor','rootTag']
    
    #Get the grid data file:
    fileName = '%s-%s-%s-%s.dat' %(topology, analysis, events, order)
    f = checkFile(targetPath + '/' + fileName)
    
    print ("========================================================")
    print('Producing the validation plot')
    print('Topology: ', topology)
    print('Analysis: ', analysis)
    print('Using database: ', args.Base)
    print('Use grid file: ', f)
    print ("========================================================")
    
    #Get all the values and TGraphs:
    metadata = validationPlotsHelper.getMetadata(f, tags)
    description = metadata['analysis'][0].split(',')
    for i, des in enumerate(description): 
        print(i, des)
    results = validationPlotsHelper.getData(f, Rmax = args.maxR)
    motherM = results['massMother']
    lspM = results['massLSP']
    tUL = results['theoreticalUpperLimit']
    eUL = results['experimentalUpperLimit']
    excluded = results['excluded']
    allowed = results['allowed']
    notTested = results['notTested']
    exclusionLine = validationPlotsHelper.getEnvelope(excluded)
    officialExclusionLine = expRes.exclusionLine()
    
    #Set the options for the TGraphs:
    excluded.SetMarkerStyle(10)
    excluded.SetMarkerColor(ROOT.kMagenta+3)
    allowed.SetMarkerStyle(10)
    allowed.SetMarkerColor(ROOT.kGreen+2)
    notTested.SetMarkerStyle(10)
    notTested.SetMarkerColor(ROOT.kOrange-2)
    exclusionLine.SetLineStyle(2)
    exclusionLine.SetLineWidth(4)
    exclusionLine.SetLineColor(ROOT.kBlack-2)
    officialExclusionLine.SetLineColor(ROOT.kBlack)
    
    #Create TMutiGraph-object:
    multi = ROOT.TMultiGraph()
    multi.Add(excluded, 'P')
    multi.Add(allowed, 'P')
    multi.Add(notTested, 'P')
    multi.Add(exclusionLine, 'L')
    multi.Add(officialExclusionLine, 'L')
    
    #Legend:
    legend = ROOT.TLegend(0.6, 0.55, 0.9, 0.89)
    legend.SetBorderSize(0)
    legend.SetMargin(0.2)
    legend.SetFillColor(ROOT.kWhite)
    legend.SetTextSize(0.03)
    legend.AddEntry(excluded, 'excluded', 'P')
    legend.AddEntry(allowed, 'allowed', 'P')
    legend.AddEntry(notTested, 'not tested', 'P')
    legend.AddEntry(exclusionLine, 'derived exclusion contour', 'L')
    legend.AddEntry(officialExclusionLine, '%s' %metadata['rootTag'][0][1], 'L')
    
    #Canvas:
    c = ROOT.TCanvas("c1", "c1", 0, 0, 800, 500)
    c.SetFillColor(ROOT.kWhite)
    
    multi.Draw('APL')
    multi.GetXaxis().SetTitle("m_{mother} (GeV)")
    multi.GetYaxis().SetTitle("m_{LSP} (GeV)")
    multi.GetYaxis().SetTitleOffset(1.0)
    ROOT.gPad.RedrawAxis()
    legend.Draw('L')

    #title = ROOT.TLatex(0, 1100, "#splitline{%s}{#splitline{analysis = %s,  #sqrt{s} = %s}{order = %s}}" %(description[0], description[1], description[2], description[3]))
    #title.SetTextSize(0.03)
    motherMinExcluded = ROOT.TMath.MinElement(excluded.GetN(), excluded.GetX())
    motherMinNotTested = ROOT.TMath.MinElement(notTested.GetN(), notTested.GetX())
    motherMinAllowed = ROOT.TMath.MinElement(allowed.GetN(), allowed.GetX())
    
    xPosition = min([motherMinExcluded, motherMinAllowed, motherMinNotTested])
    
    lspMaxExcluded = ROOT.TMath.MaxElement(excluded.GetN(), excluded.GetY())
    lspMaxNotTested = ROOT.TMath.MaxElement(notTested.GetN(), notTested.GetY())
    lspMaxAllowed = ROOT.TMath.MaxElement(allowed.GetN(), allowed.GetY())
    
    yPosition = max([lspMaxExcluded, lspMaxAllowed, lspMaxNotTested])
    
    title = ROOT.TLatex(xPosition, yPosition-50, '%s: %s' %(topology, metadata['decay'][0]))
    title.SetTextSize(0.05)
    title.Draw()
    if 'ATLAS' in analysis:
        
        title2 = ROOT.TLatex(xPosition, yPosition-130, '%s %s' \
        %(description[0], description[1].replace('\\', '#')))
        title2.SetTextSize(0.03)
        title2.Draw()
        title3 = ROOT.TLatex(xPosition, yPosition-155, \
        '#sqrt{s} = %s, order = %s' %(description[2], description[3]))
        title3.SetTextSize(0.03)
        title3.Draw()
    else:
        title2 = ROOT.TLatex(xPosition, yPosition-130, \
        '%s %s, #sqrt{s} = %s, order = %s' %(description[0], \
        description[1].replace('\\', '#'), description[2], description[3]))
        title2.SetTextSize(0.03)
        title2.Draw()
    
    c.Print("./plots/%s" %metadata['outFile'][0].strip())

def getTarget(path):
    """Checks if the target directory already exists and raises an error if not.
    
    """
    
    if not os.path.exists(path):
        logger.error('Could not find directory %s!' %path)
        sys.exit()
    return path

def checkFile(path):
    """Checks if the data file already exists, raises an error if not. 
    
    """
    if not os.path.exists(path):
        logger.error('Could not find file %s!' %path)
        sys.exit()
    return path
    
if __name__ == '__main__':
    main()  
#--------------------------------------------------------------------------------

    
    ##Dimensions of the ROOT-histogram:   

    #motherMin = min(motherM)
    #motherMax = max(motherM)
    #motherN = len(motherM))
    #lspMin = min(lspM)
    #lspMax = max(lspM)
    #lspN = len(lspM))

    
    #h = ROOT.TH2F('h', '', motherN, motherMin, motherMax, lspN, lspMin, lspMax)

    #h.SetXTitle("mother mass [GeV]")
    #h.SetYTitle("LSP mass [GeV]")
    #h.SetTitleSize(0.034, "X")
    #h.SetLabelSize(0.034, "X")
    #h.SetTitleSize(0.034, "Y")
    #h.SetLabelSize(0.034, "Y")
    #h.SetTitleOffset(1.3, "X")
    #h.SetTitleOffset(1.6, "Y")

    #c.cd()
    #h.Draw()

