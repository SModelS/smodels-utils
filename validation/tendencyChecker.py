#!/usr/bin/env python

"""
.. module:: gridDataCreator
   :synopsis: Will check the tendency of the xsections for the validation plots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

from __future__ import print_function
import setPath  # # set to python path for smodels
from smodels.tools.physicsUnits import fb, GeV, addunit, rmvunit
from smodels_tools.tools.databaseBrowser import Browser
import logging
import argparse
import os
import types
import ROOT
import logging
import validationPlotsHelper

logger = logging.getLogger(__name__)

def main():
    """Handles all command line options, as:
    topology, analysis, directory, base, loglevel, ...
    Produces the grid data file and adds some meta data.
    
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
    help = 'perturbation order (LO, NLO, NLL) - default: LO', \
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
    blocks = [0, 1, 12, 25]
    col = [ROOT.kRed, ROOT.kYellow+1, ROOT.kGreen+1, ROOT.kGray+2,\
    ROOT.kOrange+7, ROOT.kMagenta+3, ROOT.kSpring-7, ROOT.kCyan+2, \
    ROOT.kBlue, ROOT.kRed+1, ROOT.kOrange-3,ROOT.kGreen-4]
    
    print ("========================================================")
    print('Producing the tendency plot')
    print('Topology: ', topology)
    print('Analysis: ', analysis)
    print ("========================================================")
    
    fileName = '%s-%s-%s-%s.dat' %(topology, analysis, events, order)
    f = checkFile(targetPath + '/' + fileName)
    motherM = []
    lspM = []
    xsections = []
    outFile = open(f, 'r')
    for line in outFile.readlines():
        line = line.split()
        if line[0] == '#END': break
        motherM.append(line[0].strip())
        lspM.append(line[1].strip())
        xsections.append(line[2].strip())
    
    canvas = ROOT.TCanvas("c1", "c1", 0, 0, 900, 600)
    multi = None
    canvas.Divide(2, 1)
    mother = motherTendency(motherM, xsections)
    canvas.cd(1)
    mother.Draw()
    canvas.cd(2)
    
    multi = ROOT.TMultiGraph()
    leg = ROOT.TLegend(0.6325287,0.7408994,0.9827586,1)
    validationPlotsHelper.Default(leg,"Legend")
    count = 0
    for block in blocks:
        lsp = lspTendency(motherM, lspM, xsections, block)[0]
        lsp.SetLineColor(col[count])
        count += 1
        multi.Add(lsp, 'L')
        leg.AddEntry(lsp, 'mother %s' %lspTendency(motherM, lspM, xsections, block)[1], 'L')
    #leg.Draw()
    multi.Draw('AL')
    multi.GetXaxis().SetTitle("LSP mass")
    multi.GetYaxis().SetTitle("xsection")
    multi.SetTitle('LSP-mass vs xsection')
    
    canvas.Update()
    ans = raw_input("Hit any key to close\n")

def motherTendency(masses, xsections):
    """Produces a root TGraph with mother particle mass on x-axis and xsec on y-axis.
    
    """
    graph = ROOT.TGraph()
    if not len(masses) == len(xsections):
        logger.error('Something is very wrong!')
        return None
    m = float(masses[0])
    graph.SetPoint(0, m, float(xsections[0]))    
    for i in range(len(masses)):
        if m == float(masses[i]): continue
        #if float(xsections[i]) > 4000.: continue
        m = float(masses[i])
        n = graph.GetN()
        print('Fill in: ', n, m, float(xsections[i]))
        graph.SetPoint(n, m, float(xsections[i]))
    graph.SetName('mother')
    graph.SetTitle('mother-mass vs xsection')
    graph.SetLineWidth(4)
    graph.GetXaxis().SetTitle("mother mass")
    graph.GetYaxis().SetTitle("xsection")
    
    return graph
 
def lspTendency(motherMasses, lspMasses, xsections, block):
    """Produces a root TGraph with LSP particle mass on x-axis and xsec on y-axis.
    
    """
    graph = ROOT.TGraph()
    if not len(motherMasses) == len(xsections):
        logger.error('Something is very wrong!')
        return None
    m = float(motherMasses[0])
    count = 0
    #graph.SetPoint(0, float(lspMasses[block]), float(xsections[block]))    
    for i in range(len(motherMasses)):
        if m != float(motherMasses[i]):
            count += 1
            m = float(motherMasses[i])
        if count == block:
            print('block' , block, 'count', count)
            n = graph.GetN()
            print('Fill in: ',m,  n, float(lspMasses[i]), float(xsections[i]))
            graph.SetPoint(n, float(lspMasses[i]), float(xsections[i]))
        else: continue
    graph.SetName('LSP')
    graph.SetLineWidth(4)
    return [graph, m]
    
def getColor():
    col = [ROOT.kRed, ROOT.kYellow+1, ROOT.kGreen+1, ROOT.kGray+2,\
    ROOT.kOrange+7, ROOT.kMagenta+3, ROOT.kSpring-7, ROOT.kCyan+2, \
    ROOT.kBlue, ROOT.kRed+1, ROOT.kOrange-3,ROOT.kGreen-4]
    for c in col:
        yield c 

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