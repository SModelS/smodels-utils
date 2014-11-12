#!/usr/bin/env python

"""
.. module:: xsecComparator
   :synopsis: Will check the tendency of the xsections and compare to official 
   data or to other order.
   

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

from __future__ import print_function
import setPath  # # set to python path for smodels
from smodels_utils.tools.databaseBrowser import Browser
import logging
import os
import types
import ROOT
import logging
import validationPlotsHelper
import referenceXSections
import argparse
import sys
from smodels.tools.physicsUnits import rmvunit

logger = logging.getLogger(__name__)

def main():
    """Handles all command line options, as:
    topology, analysis, directory, particle, ...
    Produces the root plot.
    
    """
    argparser = argparse.ArgumentParser(description = \
    'Checks the tendency of xsec for smodels validation plots')
    argparser.add_argument ('-t', '--topology', \
    help = 'topology that should be validated - default: T1',\
    type = types.StringType, default = 'T1')
    argparser.add_argument ('-a', '--analysis', \
    help = 'analysis that should be validated - default: SUS12028',\
    type = types.StringType, default = 'SUS12028')
    argparser.add_argument ('-o', '--order', \
    help = 'perturbation order (LO, NLO, NLL) - default: NLL', \
    type = types.StringType, default = 'NLL')
    argparser.add_argument ('-d', '--directory', \
    help = 'directory the data file should be taken from - default: ./gridData', \
    type = types.StringType, default = './gridData')
    argparser.add_argument ('-n', '--events',\
    help = 'set number of events - default: 10000', \
    type = types.IntType, default = 10000)
    argparser.add_argument ('-p', '--particle',\
    help = 'mass of mother/LSP vs. cross section - default: mother', \
    type = types.StringType, default = 'mother')
    argparser.add_argument ('-c', '--comparison',\
    help = 'mass of mother vs. cross section compared to:\
    reference x-sections or to LO if order is NLL - default: ref', \
    type = types.StringType, default = 'ref')
    argparser.print_help()
    args = argparser.parse_args()

    topology = args.topology
    analysis = args.analysis
    targetPath = getTarget(args.directory)
    events = args.events
    order = args.order
    particle = args.particle
    comparison = args.comparison
    
    blocks = [0, 1, 12, 25]
    col = [ROOT.kRed, ROOT.kYellow+1, ROOT.kGreen+1, ROOT.kGray+2,\
    ROOT.kOrange+7, ROOT.kMagenta+3, ROOT.kSpring-7, ROOT.kCyan+2, \
    ROOT.kBlue, ROOT.kRed+1, ROOT.kOrange-3,ROOT.kGreen-4]
    
    print ("========================================================")
    print('Producing the tendency plot')
    print('Topology: ', topology)
    print('Analysis: ', analysis)
    print('Order: ', order)
    print('Events: ', events)
    print('Particle: ', particle)
    print('Compare to: ', comparison)
    print ("========================================================")
    
    
    fileName = '%s-%s-%s-%s.dat' %(topology, analysis, events, order)
    motherM = readGrid(fileName, targetPath)[0]
    lspM = readGrid(fileName, targetPath)[1]
    xsections = readGrid(fileName, targetPath)[2]
    
    canvas = ROOT.TCanvas("c1", "c1", 0, 0, 900, 600)
    if particle == 'mother':
        canvas.SetLogy()
    legend = ROOT.TLegend(0.4, 0.15, 0.16, 0.3)
    legend.SetBorderSize(0)
    legend.SetMargin(0.2)
    legend.SetFillColor(ROOT.kWhite)
    legend.SetTextSize(0.0235)
    
    multi = ROOT.TMultiGraph()

    if particle == 'mother':
        mother = motherTendency(motherM, xsections)
        mother.SetLineColor(col[0])
        if comparison == 'ref':
            reference = referenceTendency('8TeV', topology)
            if reference:
                reference.SetLineColor(col[3])
        if comparison == 'LO':
            if not 'NLL' in fileName:
                logger.error('Can not compare %s to LO' %order)
                sys.exit()
            checkFile(targetPath + '/' + fileName.replace('NLL', 'LO'))
            fileRefName = fileName.replace('NLL', 'LO')
            motherRefM = readGrid(fileRefName, targetPath)[0]
            lspRefM = readGrid(fileRefName, targetPath)[1]
            xsectionsRef = readGrid(fileRefName, targetPath)[2]
            reference = motherTendency(motherRefM, xsectionsRef)
            if reference:
                reference.SetLineColor(col[7])
        if reference:        
            multi.Add(reference, 'l')
        multi.Add(mother, 'l')
        multi.Draw('ALP')
        multi.GetXaxis().SetTitle(" mother mass [GeV]")
        multi.GetYaxis().SetTitle(" log (xsection [fb])")
        multi.SetTitle('mother-mass vs xsection')
        legend.AddEntry(mother, 'smodels - %s' %order, 'L')
        if reference:
            if comparison == 'LO':
                legend.AddEntry(reference, 'smodels - LO', 'L')
            else:
                legend.AddEntry(reference, 'reference', 'L')
        legend.Draw('SAME')
        canvas.Update()
        
    if particle == 'LSP':
        count = 0
        for block in blocks:
            lsp = lspTendency(motherM, lspM, xsections, block)
            lsp[0].SetLineColor(col[count])
            count += 1
            multi.Add(lsp[0], 'L')
            legend.AddEntry(lsp[0], 'mother %s [GeV]' %lsp[1], 'L')
        multi.Draw('ALP')
        multi.GetXaxis().SetTitle("LSP mass [GeV]")
        multi.GetYaxis().SetTitle("xsection [fb]")
        multi.SetTitle('LSP-mass vs xsection')
        legend.Draw('SAME')
        canvas.Update()

    name = '%s-%s-%s.png' %(fileName.replace('.dat', ''), particle, comparison)
    logger.debug('Name of the output file: %s' %name)

    canvas.Print("./plots/xsecComparator/%s" %name)
    
def motherTendency(masses, xsections):
    """Produces a root TGraph with mother particle mass on x-axis 
    and xsec on y-axis.
    
    """
    graph = ROOT.TGraph()
    if not len(masses) == len(xsections):
        logger.error('Something is very wrong! Check the grid data!')
        return None
    m = float(masses[0])
    graph.SetPoint(0, m, float(xsections[0]))    
    for i in range(len(masses)):
        if m == float(masses[i]): continue
        if float(xsections[i]) > 4000.: continue
        m = float(masses[i])
        n = graph.GetN()
        #print('Fill in: ', n, m, float(xsections[i]))
        graph.SetPoint(n, m, float(xsections[i]))
    graph.SetName('mother')
    graph.SetTitle('mother-mass vs xsection')
    graph.SetLineWidth(4)
    #print ('mother graph', graph)
    return graph

def readGrid(fileName, targetPath):
    """Reads the given grid data file and creates python lists.
    
    """
    
    f = checkFile(targetPath + '/' + fileName)
    motherM = []
    lspM = []
    xsections = []
    outFile = open(f, 'r')
    for line in outFile.readlines():
        line = line.split()
        if line[0] == '#END': break
        if not eval(line[2].strip()):
            continue
        motherM.append(line[0].strip())
        lspM.append(line[1].strip())
        xsections.append(line[2].strip())
    return [motherM, lspM, xsections]
            

def lspTendency(motherMasses, lspMasses, xsections, block):
    """Produces a root TGraph with LSP mass on x-axis and xsec 
    on y-axis, for several masses of the mother particle.
    
    """
    graph = ROOT.TGraph()
    if not len(motherMasses) == len(xsections):
        logger.error('Something is very wrong!')
        return None
    m = float(motherMasses[0])
    mm = None
    count = 0
    for i in range(len(motherMasses)):
        if m != float(motherMasses[i]):
            count += 1
            m = float(motherMasses[i])
        if count == block:
            logger.debug('block %s and count %s' %(block, count))
            n = graph.GetN()
            logger.debug('Fill in: mother: %s, index: %s, lsp: %s and xsec: %s'\
            %(m,  n, float(lspMasses[i]), float(xsections[i])))
            graph.SetPoint(n, float(lspMasses[i]), float(xsections[i]))
            mm = m
        else: continue
    graph.SetName('LSP')
    graph.SetLineWidth(4)
    return [graph, mm]

def referenceTendency(sqrt, topology):
    """Produces a root TGraph with mother particle mass on x-axis and xsec 
    on y-axis using the reference cross sections.
    
    """
    values = referenceXSections.xSecs(sqrt, topology)
    if not values: return None
    graph = ROOT.TGraph()
    for point in values:
        mass = rmvunit(point[0], 'GeV')
        xsec = rmvunit(point[1], 'fb')
        graph.SetPoint(graph.GetN(), mass, xsec)
    graph.SetName('reference')
    graph.SetLineWidth(4)
    #print ('reference graph', graph)
    return graph    

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
