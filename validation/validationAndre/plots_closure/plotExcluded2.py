#!/usr/bin/env python

import argparse
import os, sys

argparser = argparse.ArgumentParser(description='plots the exclusion region and envelope')
argparser.add_argument( 'input', help='input data file (mother_mass,LSP_mass,R)')
args=argparser.parse_args()

from ROOT import *
import AuxPlot

#Define metadata tags:
tags = ['title','Root file','Out file','Kfactor','Root tag']
#Get metadata:
if not os.path.isfile(args.input):
  print 'Input file not found'
  sys.exit()
metadata = AuxPlot.getMetadata(args.input,tags)
Rmax = 1.
if metadata['Kfactor']:
  Rmax = Rmax/eval(metadata['Kfactor'][0])
  metadata['title'][0] += '*'+metadata['Kfactor'][0]

#Get data:
results = AuxPlot.getData(args.input,Rmax)
exc = results['exc']
xv = results['xv']
yv = results['yv']
zv = results['limv']
#Get exclusion envelope:
exc_curve = AuxPlot.getEnvelope(exc)
#Get root plots
rootPlots = AuxPlot.getRootPlots(metadata)
  
xvS = sorted(set(xv))    
yvS = sorted(set(yv))
zvS = sorted(set(zv))

xmax,ymax,zmax = max(xvS),max(yvS),max(zvS)
xmin,ymin,zmin = min(xvS),min(yvS),min(zvS)
dxmin = min([abs(xvS[i]-xvS[i+1]) for i in range(len(xvS)-1)])*1.1
dymin = min([abs(yvS[i]-yvS[i+1]) for i in range(len(yvS)-1)])*1.1
exp_limit = TH2F("","",int((xmax-xmin)/dxmin),xmin,xmax,int((ymax-ymin)/dymin),ymin,ymax)
for ilim,lim in enumerate(zv):
  if exp_limit.GetBinContent(exp_limit.FindBin(xv[ilim],yv[ilim])) < lim:
    exp_limit.SetBinContent(exp_limit.FindBin(xv[ilim],yv[ilim]),lim)


#Canvas
AuxPlot.set_palette(gStyle)
plane = TCanvas("c1", "c1",0,0,800,500)
AuxPlot.Default(plane,"TCanvas")
plane.SetRightMargin(0.15700422)
plane.SetTopMargin(0.05296053)
plane.SetBottomMargin(0.16796053)

exp_limit.Draw('COLZ')
for plot in rootPlots.keys(): rootPlots[plot].Draw("SAMEL")
exc_curve.Draw("SAMEL")
#Set options
exp_limit.SetStats(kFALSE)
AuxPlot.Default(exp_limit,'TH2')
plane.SetLogz()
exp_limit.GetXaxis().SetTitle("M (GeV)")
exp_limit.GetYaxis().SetTitle("m_{LSP} (GeV)")
exp_limit.GetYaxis().SetTitleOffset(0.75)
exp_limit.GetZaxis().SetTitle("Upper Limit (fb)")
exp_limit.GetZaxis().SetTitleOffset(0.75)
exp_limit.GetZaxis().SetRangeUser(zmin,zmax)
exc_curve.SetLineColor(kRed)
exc_curve.SetLineStyle(9)
exc_curve.SetLineWidth(3)
for iplot,plot in enumerate(rootPlots.keys()):
  rootPlots[plot].SetLineStyle(iplot+1)
  rootPlots[plot].SetLineWidth(3)
  rootPlots[plot].SetLineColor(kBlack)  
  rootPlots[plot].SetMarkerStyle(20)
  rootPlots[plot].SetMarkerSize(0.9) 
gPad.RedrawAxis()

#Legend
leg = TLegend(0.6934673,0.8051392,0.9886935,0.99)
AuxPlot.Default(leg,"Legend")  
leg.AddEntry(exc_curve,'SModelS',"L")
for plot in rootPlots.keys(): leg.AddEntry(rootPlots[plot],plot,"L")
leg.Draw()

#Title
if metadata['title']:
  title = metadata['title'][0]
  tit = TPaveLabel(0.01005025,0.8672377,0.5850754,0.9807281,title,"brNDC")
  tit.SetBorderSize(4)
  tit.SetFillColor(0)
  tit.SetTextFont(42)
  tit.SetTextSize(0.3127273)
  tit.Draw()

gPad.Update()
if metadata['Out file']: c1.Print('2D-'+metadata['Out file'][0])
ans = raw_input("Hit any key to close\n")

  
