#!/usr/bin/env python

"""
.. module:: validationPlotsHelper
   :synopsis: Some functions needed for producing the validation plots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

from __future__ import print_function
import setPath  # # set to python path for smodels
from smodels.tools.physicsUnits import fb, GeV, addunit, rmvunit
from smodels_tools.tools.databaseBrowser import Browser
import logging
import os
from ROOT import TTree,TColor,TCanvas,TF1,TGraph,Double,TFile,gDirectory
import copy

logger = logging.getLogger(__name__)

def getMetadata(filename,tags):
    infile = open(filename,'r')
    data = infile.read()
    info = data[data.find('#END'):].split('\n')
    metadata = {}
    for tag in tags: metadata[tag] = None
    if len(info) > 0:
      for line in info:
        for tag in tags:
          if tag in line:
            if not metadata[tag]: metadata[tag] = []
            entry = line.lstrip(tag + ' :').rstrip()
            if ':' in entry: entry = entry.split(':')
            metadata[tag].append(entry)

    infile.close()
    return metadata
  
def getData(fileName, maxR = 1., condmax = 0.001):
    infile = open(fileName,'r')
    data = infile.read()
    points = data[:data.find('#END') - 1].split('\n')
    notTested = TGraph()
    excluded = TGraph()
    allowed = TGraph()
    conditionViolated = TGraph()
  
    massMother = []
    massLSP = []
    experimentalUpperLimit = []
    condition = []
    theoreticalUpperLimit = []
    for pt in points:
        values = [p.strip() for p in pt.split()]
        mM, mLSP, tUL, eUL, cond = values
        #print('point: ', mM, mLSP, tUL, eUL, cond)
        if not eval(tUL) or not eval(eUL):
            #print('no tUL')
            mM = float(eval(mM))
            mLSP = float(eval(mLSP))
            notTested.SetPoint(notTested.GetN(),mM,mLSP)
            continue
        r = float(eval(tUL)) / float(eval(eUL))
        if eval(tUL) < 0.: continue
        if cond == 'None': cond = '0.'
        mM = eval(mM)
        mLSP = eval(mLSP)
        eUL = eval(eUL)
        tUL = eval(tUL)
        cond = eval(cond)
        massMother.append(mM)
        massLSP.append(mLSP)
        experimentalUpperLimit.append(eUL)
        theoreticalUpperLimit.append(tUL)
        condition.append(cond)
        if cond > condmax: conditionViolated.SetPoint(conditionViolated.GetN(),mM,mLSP)
        if r < 0.:
            notTested.SetPoint(notTested.GetN(),mM,mLSP)
        elif r >= maxR:
            excluded.SetPoint(excluded.GetN(),mM,mLSP)
        elif r < maxR:
            allowed.SetPoint(allowed.GetN(),mM,mLSP)
        else:
            logger.error('Unknown r value: %s' %r)
            sys.exit()
      
    infile.close()
    graphs = {'excluded' : excluded,
    'notTested' : notTested,
    'conditionViolated' : conditionViolated,
    'allowed' : allowed,
    'massMother' : massMother,
    'massLSP' : massLSP,
    'theoreticalUpperLimit' : theoreticalUpperLimit,
    'experimentalUpperLimit' : experimentalUpperLimit,
    'condition' : condition}
    return graphs
  
def getRootPlots(metadata):  
    plots = {}
    if metadata['Root file'] and os.path.isfile(metadata['Root file'][0]):
        rootfile = TFile(metadata['Root file'][0],"read")
        objs =  gDirectory.GetListOfKeys()
        for ob in objs:
            add = False
            Tob = ob.ReadObj()
            if type(Tob) != type(TGraph()): continue
            if metadata['Root tag']:
                for rootTag in metadata['Root tag']:
                    Tag = rootTag
                    if type(Tag) == type([]) and len(Tag) > 1: Tag = Tag[0]
                    if Tag == ob.GetName():  add = rootTag
            else:
                add = 'Official Exclusion'
            if add:
                if type(add) == type([]): add = add[1]
                plots[add] = copy.deepcopy(Tob)
        
    return plots
    
  
def getEnvelope(excluded,consecutive_bins=3):

    exc_curve = TGraph()
    exc = copy.deepcopy(excluded)
    exc.Sort()
    x1,y1 = Double(), Double()
    exc.GetPoint(0,x1,y1)
    yline = []
    for ipt in range(exc.GetN()+1): 
        x,y = Double(), Double()
        dmin = 0.
        if ipt < exc.GetN(): exc.GetPoint(ipt,x,y)
        if ipt != exc.GetN() and x == x1: yline.append(y)
        else:
            yline = sorted(yline,reverse=True)
            dy = [abs(yline[i]-yline[i+1]) for i in range(len(yline)-1)]
            if len(yline) <= 3 or exc_curve.GetN() == 0:
                newy = max(yline)
                if len(dy) > 2: dmin = min([abs(yline[i]-yline[i+1]) for i in range(len(yline)-1)])
            else:
                newy = max(yline)     
        #        dmin = min(dy)
                dmin = sum(dy)/float(len(dy))
                for iD in range(len(dy)-1):
                    if dy[iD] <= dmin and dy[iD+1] <= dmin:
                        newy = yline[iD]
                        break
            exc_curve.SetPoint(exc_curve.GetN(),x1,newy+dmin/2.)
            x1 = x
            yline = [y]

    x2,y2 = Double(), Double()
    exc_curve.GetPoint(exc_curve.GetN()-1,x2,y2)
    exc_curve.SetPoint(exc_curve.GetN(),x2,0.)  #Close exclusion curve at zero
    return exc_curve
  
def Default(obj,Type):
  
    if Type == "TCanvas":
        obj.SetLeftMargin(0.1097891)
        obj.SetRightMargin(0.02700422)
        obj.SetTopMargin(0.02796053)
        obj.SetBottomMargin(0.14796053)
        obj.SetFillColor(0)
        obj.SetBorderSize(0)
        obj.SetFrameBorderMode(0)
    elif "TGraph" in Type or "TH" in Type:
        obj.GetYaxis().SetTitleFont(132)
        obj.GetYaxis().SetTitleSize(0.065)
        obj.GetYaxis().CenterTitle(True)
        obj.GetYaxis().SetTitleOffset(0.9)
        obj.GetXaxis().SetTitleFont(52)
        obj.GetXaxis().SetTitleSize(0.065)
        obj.GetXaxis().CenterTitle(True)
        obj.GetXaxis().SetTitleOffset(1.0)
        obj.GetYaxis().SetLabelFont(132)
        obj.GetXaxis().SetLabelFont(132)
        obj.GetYaxis().SetLabelSize(0.05)
        obj.GetXaxis().SetLabelSize(0.05)
        if "TGraph2D" in Type or "TH2" in Type:
            obj.GetZaxis().SetTitleFont(132)
            obj.GetZaxis().SetTitleSize(0.06)
            obj.GetZaxis().CenterTitle(True)
            obj.GetZaxis().SetTitleOffset(0.7)
            obj.GetZaxis().SetLabelFont(132)
            obj.GetZaxis().SetLabelSize(0.05)
    elif "Leg" in Type:
        obj.SetBorderSize(1)
        obj.SetTextFont(132)
        obj.SetTextSize(0.05)
        obj.SetLineColor(1)
        obj.SetLineStyle(1)
        obj.SetLineWidth(1)
        obj.SetFillColor(0)
        obj.SetFillStyle(1001)

   
   