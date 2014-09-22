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

def main(arguments = None):
    """Handles all command line options.
    Produces the validation plot.
    :param None: if set to None script uses the argparser, else takes list of arguments
    :param Base: sets the path to the smodels-database
    :param analysis: analysis the validation plot should be preoduced for
    :param topology: topology the validation plot should be preoduced for
    :param order: order of perturbation theory as string ('LO', 'NLO', 'NLL')
    :param directory: 'directory the grid data file should be taken from
    :param events: number of events for pythia simulation 
    :param intermediate: comma separated condition and value (e.g. LSP,300); condition for mass of intermediate particle (e.g xvalue), value for the mass condition (e.g. 025)
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
    argparser.add_argument ('-n', '--events',\
    help = 'set number of events - default: 10000', \
    type = types.IntType, default = 10000)
    argparser.add_argument ('-i', '--intermediate', \
    help = 'condition and value for intermediate particle - default: xvalue,050', \
    type = types.StringType, default = 'xvalue,050')
    args = argparser.parse_args()

    if not arguments:
        base = args.Base
        topology = args.topology
        intermediate = args.intermediate.split(',')
    else:
        base = arguments['base']
        topology = arguments['topology']
        intermediate = arguments['intermediate'].split(',')
    browser = Browser(base)    
    intermediate = [i.strip() for i in intermediate]
    if intermediate[0] == 'xvalue':
        condition = ''
    else:
        condition = intermediate[0]
    if intermediate[1] == '050' and not condition:
        value = ''
    else:
        value = intermediate[1]
    if topology[-2:] == 'on':
        topologyName = topology[:-2]
    elif topology[-3:] == 'off':
        topologyName = topology[:-3]
    else: topologyName = topology
    extendedTopology = topology + condition + value
    if not arguments:
        analysis = args.analysis
        targetPath = getTarget(args.directory)
        events = args.events
        order = args.order
    else:
        analysis = arguments['analysis']
        targetPath = getTarget(arguments['directory'])
        events = arguments['events']
        order = arguments['order']
        
    expRes = browser.expResult(analysis, topology)
    if not expRes:
        expRes = browser.expResult(analysis, topologyName)
    expAna = expRes.expAnalysis
    expTopo = expRes.expTopology
    
    #Define metadata tags:
    tags = ['decay', 'analysis', 'outFile','factor','rootTag', 'intermediate']
    
    #Get the grid data file:
    fileName = '%s-%s-%s-%s.dat' %(extendedTopology, analysis, events, order)
    f = checkFile(targetPath + '/' + fileName)
    
    print ("========================================================")
    print('Producing the validation plot')
    print('Topology: ', topology)
    print('Analysis: ', analysis)
    print('Using database: ', base)
    print('Use grid file: ', f)
    print ("========================================================")
    
    #Get all the values and TGraphs:
    metadata = validationPlotsHelper.getMetadata(f, tags)
    description = metadata['analysis'][0].split(',')
    factor = ''
    if metadata['factor']:
        factor = ' * %s' %metadata['factor'][0]
  
    for i, des in enumerate(description):
        if i == 3:
            logger.info('Index %s holds %s%s.' %(i, des, factor))
        else:
            logger.info('Index %s holds %s.' %(i, des))

    maxR = 1.0
    if factor:
        maxR = 1.0/eval(metadata['factor'][0])
    results = validationPlotsHelper.getData(f, maxR = maxR)
    motherM = results['massMother']
    lspM = results['massLSP']
    tUL = results['theoreticalUpperLimit']
    eUL = results['experimentalUpperLimit']
    excluded = results['excluded']
    allowed = results['allowed']
    notTested = results['notTested']
    exclusionLine = validationPlotsHelper.getEnvelope(excluded)
    valueAbove = ''
    valueBelow = ''
    if extendedTopology == 'T6ttWWLSP050':
        exclusionLine = validationPlotsHelper.cutGraph(exclusionLine, 19, before = False, after = True)
    if extendedTopology == 'T6ttWWx166':
        exclusionLine = validationPlotsHelper.cutGraph(exclusionLine, 16, before = False, after = True)    
        exclusionLine = validationPlotsHelper.addPoint(exclusionLine, 587., 100.)
    if not condition and not value:
        officialExclusionLine = expRes.exclusionLine()
    else:
        if not extendedTopology in expRes.extendedTopologies:
            logger.info('There is no official exclusion line for %s!\n \
            Search for adjacent lines.' %extendedTopology)
            if not condition or condition == 'x':
                values = []
                for extTopo in expRes.axes:
                    values.append(expRes.axes[extTopo]['mz'].replace(condition, ''))
                values.append(value)
                values.sort()
                valueIndex = values.index(value)
                if not valueIndex + 1 > len(values):
                    valueAbove = values[valueIndex + 1]
                    logger.info('Found adjacent line above for %s%s'\
                    %(condition, valueAbove))
                else:
                    valueAbove = ''
                    logger.info('No adjacent line above could be found!')
                if not valueIndex - 1 < 0:
                    valueBelow = values[valueIndex - 1]
                    logger.info('Found adjacent line below for %s%s'\
                    %(condition, valueBelow))
                else:
                    valueBelow = ''
                    logger.info('No adjacent line below could be found!')
                
            if valueAbove:        
                officialExclusionLineAbove = expRes.selectExclusionLine\
                (condition = intermediate[0], value = valueAbove)
                if extendedTopology == 'T6ttWWx166':
                    officialExclusionLineAbove = validationPlotsHelper.cutGraph(officialExclusionLineAbove, 35, before = False, after = True)    
                    officialExclusionLineAbove = validationPlotsHelper.cutGraph(officialExclusionLineAbove, 5)    
                
            if valueBelow:
                officialExclusionLineBelow = expRes.selectExclusionLine\
                (condition = intermediate[0], value = valueBelow)
                if extendedTopology == 'T6ttWWx166':
                    officialExclusionLineBelow = validationPlotsHelper.cutGraph(officialExclusionLineBelow, 55, before = False, after = True)
                    officialExclusionLineBelow = validationPlotsHelper.cutGraph(officialExclusionLineBelow, 5)    
        else:
            officialExclusionLine = expRes.exclusionLine(extendedTopology)
            valueAbove = ''
            valueBelow = ''
            
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
    if not value and not condition:
        try: 
            officialExclusionLine.SetLineColor(ROOT.kBlack)
        except AttributeError:
            logger.warning('No official line could be found!')
    else:
        if valueAbove:
            officialExclusionLineAbove.SetLineColor(ROOT.kGray+1)
            officialExclusionLineAbove.SetLineWidth(3)
        if valueBelow:
            officialExclusionLineBelow.SetLineColor(ROOT.kGray+1)
            officialExclusionLineBelow.SetLineStyle(7)
            officialExclusionLineBelow.SetLineWidth(3)
        if not valueAbove and not valueBelow:
            try:
                officialExclusionLine.SetLineColor(ROOT.kBlack)
            except AttributeError: pass
    #Create TMutiGraph-object:
    multi = ROOT.TMultiGraph()
    multi.Add(excluded, 'P')
    multi.Add(allowed, 'P')
    if notTested.GetN():
        multi.Add(notTested, 'P')
    #multi.Add(exclusionLine, 'L')
    multi.Add(exclusionLine, 'LSAME')
    if not value and not condition:
        try:
            multi.Add(officialExclusionLine, 'L')
        except TypeError: pass
    else:
        if valueAbove:
            #multi.Add(officialExclusionLineAbove, 'L')
            multi.Add(officialExclusionLineAbove, 'LSAME')
        if valueBelow:
            #multi.Add(officialExclusionLineBelow, 'L')
            multi.Add(officialExclusionLineBelow, 'LSAME')
        if not valueAbove and not valueBelow:
            multi.Add(officialExclusionLine, 'L')
    
    #Legend:
    if extendedTopology == 'T6ttWWLSP050':
        legend = ROOT.TLegend(0.57, 0.7, 0.9, 0.9)
    else:
        legend = ROOT.TLegend(0.57, 0.55, 0.9, 0.89)
    legend.SetBorderSize(1)
    legend.SetMargin(0.2)
    legend.SetFillColor(ROOT.kWhite)
    legend.SetTextSize(0.03)
    legend.AddEntry(excluded, 'excluded', 'P')
    legend.AddEntry(allowed, 'allowed', 'P')
    legend.AddEntry(notTested, 'not tested', 'P')
    legend.AddEntry(exclusionLine, 'SmodelS %s' %(intermediate[0] + '='\
    + intermediate[1]), 'L')
    if not value and not condition and officialExclusionLine:
        legend.AddEntry(officialExclusionLine, '%s' %metadata['rootTag'][0][1], 'L')
    else:
        if valueAbove:
            legend.AddEntry(officialExclusionLineAbove, '%s, %s=%s' \
            %(metadata['rootTag'][0][1], intermediate[0], valueAbove), 'L')
        if valueBelow:
            legend.AddEntry(officialExclusionLineBelow, '%s, %s=%s' \
            %(metadata['rootTag'][0][1], intermediate[0], valueBelow), 'L')
        if not valueAbove and not valueBelow and officialExclusionLine:
            if not value: val = '050'
            else: val = value
            legend.AddEntry(officialExclusionLine, '%s, %s=%s' \
            %(metadata['rootTag'][0][1], intermediate[0], val), 'L')
    #Canvas:
    c = ROOT.TCanvas("c1", "c1", 0, 0, 800, 500)
    c.SetFillColor(ROOT.kWhite)
    
    multi.Draw('APL')
    multi.GetXaxis().SetTitle("m_{mother} (GeV)")
    if condition == 'LSP':
        multi.GetYaxis().SetTitle("m_{intermediate} (GeV)")
    else:
        multi.GetYaxis().SetTitle("m_{LSP} (GeV)")
    multi.GetYaxis().SetTitleOffset(1.0)
    ROOT.gPad.RedrawAxis()
    legend.Draw('L')

    # compute the position of the title:
    
    motherMinExcluded = ROOT.TMath.MinElement(excluded.GetN(), excluded.GetX())
    print(notTested.GetN(), notTested.GetX())
    try:
        motherMinNotTested = ROOT.TMath.MinElement(notTested.GetN(), notTested.GetX())
    except TypeError:
       motherMinNotTested =  motherMinExcluded
    motherMinAllowed = ROOT.TMath.MinElement(allowed.GetN(), allowed.GetX())
    
    xPosition = min([motherMinExcluded, motherMinAllowed, motherMinNotTested])
    
    lspMaxExcluded = ROOT.TMath.MaxElement(excluded.GetN(), excluded.GetY())
    try:
        lspMaxNotTested = ROOT.TMath.MaxElement(notTested.GetN(), notTested.GetY())
    except TypeError:
        lspMaxNotTested = lspMaxExcluded
    lspMaxAllowed = ROOT.TMath.MaxElement(allowed.GetN(), allowed.GetY())
    
    yPosition = max([lspMaxExcluded, lspMaxAllowed, lspMaxNotTested])
    
    if yPosition > 1100.:
        offset = 100
        offset2 = 200
        offset3 = 300
        offset4 = 400
    elif yPosition < 500:
        offset = 10
        offset2 = 40
        offset3 = 70
        offset4 = 100
    else:
        offset = 50
        offset2 = 100
        offset3 = 150
        offset4 = 200
        
    if 'off' in topology:
        offset = 10
        offset2 = 25
        offset3 = 40
        offset4 = 55
    
    if topology in ['T6bbWW'] and value:
        xOffset = 30
    #elif 'T6ttWWx' in extendedTopology:
        #xOffset = 110
    elif extendedTopology == 'T6ttWWLSP050':
        xOffset = 90
    
    else:
        xOffset = 0
        
    if topology in ['TChiChipmSlepL', 'TChiChipmSlepStau']:
            title1 = ROOT.TLatex(xPosition - xOffset, yPosition - offset, '%s:' %topology)
            title1.SetTextSize(0.05)
            title1.Draw()
            title4 = ROOT.TLatex(xPosition - xOffset, yPosition - offset4, '%s' %metadata['decay'][0])
            title4.SetTextSize(0.03)
            title4.Draw()
    else:
        title1 = ROOT.TLatex(xPosition - xOffset, yPosition - offset, '%s: %s' %(topology, metadata['decay'][0]))
        title1.SetTextSize(0.05)
        title1.Draw()
        
    if 'ATLAS' in analysis:
        
        title2 = ROOT.TLatex(xPosition - xOffset, yPosition - offset2, '%s %s' \
        %(description[0], description[1].replace('\\', '#')))
        title2.SetTextSize(0.03)
        title2.Draw()
        title3 = ROOT.TLatex(xPosition - xOffset, yPosition - offset3, \
        '#sqrt{s} = %s, order = %s%s' %(description[2], description[3], factor))
        title3.SetTextSize(0.03)
        title3.Draw()
    else:
        title2 = ROOT.TLatex(xPosition - xOffset, yPosition - offset2, \
        '%s %s, #sqrt{s} = %s, order = %s%s' %(description[0], \
        description[1].replace('\\', '#'), description[2], description[3], \
        factor))
        title2.SetTextSize(0.03)
        title2.Draw()
    
    #ans = raw_input("Hit any key to close\n")
    c.Print("./plots/%s/%s" %(topology, metadata['outFile'][0].strip()))

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
