#!/usr/bin/env python

"""
.. module:: validationPlot
     :synopsis: Module to create a validation plot for given grid data file. 

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


"""
import argparse
import os, sys
import ROOT
import validationPlotsHelper
import logging

logger = logging.getLogger(__name__)

argparser = argparse.ArgumentParser(description='plots the exclusion region and envelope')
argparser.add_argument( 'input', help = 'input data file')
args=argparser.parse_args()

#Define metadata tags:
tags = ['title','Root file','Out file','Kfactor','Root tag']
metadata = validationPlotsHelper.getMetadata(args.input,tags)
description = metadata['title'][0].split(',')
results = validationPlotsHelper.getData(args.input, Rmax = 1.)
motherM = results['massMother']
lspM = results['massLSP']
tUL = results['theoreticalUpperLimit']
eUL = results['experimentalUpperLimit']
print 'len of mother ', len(motherM), ' lsp ', len(lspM), ' tUL ', len(tUL) 
motherBins = []
lspBins = []
lB = []
for i in range(len(motherM)):
    if motherM[i] < 800 or motherM[i] > 1000: continue
    lB.append(lspM[i])
    if not motherM[i] in motherBins:
        print 'lB', lB
        motherBins.append(motherM[i])
        lspBins.append(len(lB))
        lB = []
print 'lspBins', lspBins 
print 'motherBins', motherBins

#Dimensions of the ROOT-histogram:   

#motherMin = min(motherM)
motherMin = 800.
#motherMax = max(motherM)
motherMax = 1000.
motherN = len(motherBins)
lspMin = min(lspM)
lspMax = max(lspM)
lspN = max(lspBins)
print 'lspN', lspN
print 'motherN', motherN

c = ROOT.TCanvas()
c.SetFillColor(ROOT.kWhite)

h = ROOT.TH2F('h', '', motherN, motherMin, motherMax, lspN, lspMin, lspMax)


for i in range(len(motherM)):
    if motherM[i] < 800 or motherM[i] > 1000: continue
    #print i, motherM[i], lspM[i], eUL[i]
    h.Fill(motherM[i], lspM[i], int(eUL[i]))
    
h.SetXTitle("mother mass [GeV]")
h.SetYTitle("LSP mass [GeV]")
h.SetTitleSize(0.034, "X")
h.SetLabelSize(0.034, "X")
h.SetTitleSize(0.034, "Y")
h.SetLabelSize(0.034, "Y")
h.SetTitleOffset(1.3, "X")
h.SetTitleOffset(1.6, "Y")

c.cd()
h.Draw('textsame')

title = ROOT.TLatex(390, 1100, "#splitline{%s}{#splitline{analysis = %s,  #sqrt{s} = %s}{order = %s}}" %(description[0], description[1], description[2], description[3]))
title.SetTextSize(0.02)
title.Draw("SAME")

name = metadata['Out file'][0].strip()
print name

c.Print("%s" %name)