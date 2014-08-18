#!/usr/bin/env python

"""
.. module:: xsecTester
     :synopsis: Module to create a histogram to check the values of the cross sections. 

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


"""
from __future__ import print_function
import argparse
import os, sys
import ROOT
import validationPlotsHelper
import logging
import types

logger = logging.getLogger(__name__)

def main():
    """Handles all command line options, as:
    topology, analysis, directory, base, loglevel, ...
    Produces the grid data file and adds some meta data.
    
    """
    argparser = argparse.ArgumentParser(description = \
    'Produces a root plot to test the xsections')
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
    help = 'directory the data file should be taken from - default: ./gridData', \
    type = types.StringType, default = './gridData')
    argparser.add_argument ('-n', '--events',\
    help = 'set number of events - default: 10000', \
    type = types.IntType, default = 10000)
    args = argparser.parse_args()

    topology = args.topology
    analysis = args.analysis
    targetPath = getTarget(args.directory)
    events = args.events
    order = args.order

    print ("========================================================")
    print('Producing the test plot')
    print('Topology: ', topology)
    print('Analysis: ', analysis)
    print('Take grid from: ', targetPath)
    print ("========================================================")
    
    fileName = '%s-%s-%s-%s.dat' %(topology, analysis, events, order)
    f = checkFile(targetPath + '/' + fileName)
    
    #Define metadata tags:
    tags = ['decay', 'analysis', 'outFile','Kfactor','rootTag']
    metadata = validationPlotsHelper.getMetadata(f, tags)
    description = metadata['analysis'][0].split(',')
    results = validationPlotsHelper.getData(f, Rmax = 1.)
    motherM = results['massMother']
    lspM = results['massLSP']
    tUL = results['theoreticalUpperLimit']
    eUL = results['experimentalUpperLimit']
    logger.debug('lengths of mother: %s, lsp: %s and  tUL: %s '\
    %(len(motherM), len(lspM), len(tUL) ))
    motherBins = []
    lspBins = []
    lB = []
    for i in range(len(motherM)):
        if motherM[i] < 800 or motherM[i] > 1000: continue
        lB.append(lspM[i])
        if not motherM[i] in motherBins:
            logger.debug('lB %s' %lB)
            motherBins.append(motherM[i])
            lspBins.append(len(lB))
            lB = []
    logger.debug('lspBins %s' %lspBins) 
    logger.debug('motherBins %s' %motherBins)

    ROOT.gROOT.SetBatch()
    ROOT.gROOT.ProcessLine(".L tdrstyle_SUSY.C")
    ROOT.setTDRStyle()

    ROOT.gStyle.SetPadLeftMargin(0.125)
    ROOT.gStyle.SetPadRightMargin(0.07)
    ROOT.gStyle.SetPadBottomMargin(0.1)
    ROOT.gStyle.SetPadTopMargin(0.1)

    #Dimensions of the ROOT-histogram:   

    #motherMin = min(motherM)
    motherMin = 800.
    #motherMax = max(motherM)
    motherMax = 1000.
    motherN = len(motherBins)
    lspMin = min(lspM)
    lspMax = max(lspM)
    lspN = max(lspBins)
    logger.debug('lspN %s' %lspN)
    logger.debug('motherN %s' %motherN)

    c = ROOT.TCanvas()
    c.SetFillColor(ROOT.kWhite)
    
    h = ROOT.TH2F('h', '', motherN, motherMin, motherMax, lspN, lspMin, lspMax)


    for i in range(len(motherM)):
        if motherM[i] < 800 or motherM[i] > 1000: continue
        logger.debug('Fill the TH2F %s-%s-%s-%s: ' %(i, motherM[i], lspM[i], eUL[i]))
        if h.GetBinContent(h.FindBin(motherM[i], lspM[i])) < eUL[i]:
            h.SetBinContent(h.FindBin(motherM[i], lspM[i]), eUL[i])
        
        #h.Fill(motherM[i], lspM[i], int(eUL[i]))
        
    h.SetXTitle("mother mass [GeV]")
    h.SetYTitle("LSP mass [GeV]")
    h.SetTitleSize(0.034, "X")
    h.SetLabelSize(0.034, "X")
    h.SetTitleSize(0.034, "Y")
    h.SetLabelSize(0.034, "Y")
    h.SetTitleOffset(1.3, "X")
    h.SetTitleOffset(1.6, "Y")

    c.cd()
    #h.Draw('textsame')
    h.Draw('colz')

    title = ROOT.TLatex(motherMin + 20, lspMax + 70, '%s: %s' %(topology, metadata['decay'][0]))
    title.SetTextSize(0.05)
    title.Draw()
    if 'ATLAS' in analysis:
        
        title2 = ROOT.TLatex(motherMin + 20, lspMax + 50, '%s %s' \
        %(description[0], description[1].replace('\\', '#')))
        title2.SetTextSize(0.03)
        title2.Draw()
        title3 = ROOT.TLatex(motherMin + 20, lspMax + 30, \
        '#sqrt{s} = %s, order = %s' %(description[2], description[3]))
        title3.SetTextSize(0.03)
        title3.Draw()
    else:
        title2 = ROOT.TLatex(motherMin + 20, lspMax + 10, \
        '%s %s, #sqrt{s} = %s, order = %s' %(description[0], \
        description[1].replace('\\', '#'), description[2], description[3]))
        title2.SetTextSize(0.03)
        title2.Draw()
    name = '2D-expUL-%s.png' %fileName.replace('.dat', '')    
    c.Print("./plots/xsecTester/%s" %name)
    
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