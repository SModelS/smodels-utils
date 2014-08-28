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
import ROOT
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
  
def getData(fileName, maxR = 1., maxCondition = 0.001):
    infile = open(fileName,'r')
    data = infile.read()
    points = data[:data.find('#END') - 1].split('\n')
    notTested = ROOT.TGraph()
    excluded = ROOT.TGraph()
    allowed = ROOT.TGraph()
    conditionViolated = ROOT.TGraph()
  
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
        if cond > maxCondition:
            conditionViolated.SetPoint(conditionViolated.GetN(),mM,mLSP)
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
    
  
def getEnvelope(region):

    envelop = ROOT.TGraph()
    curve = copy.deepcopy(region)
    curve.Sort()
    x1, y1 = ROOT.Double(), ROOT.Double()
    curve.GetPoint(0, x1, y1)
    yline = []
    for ipt in range(curve.GetN() + 1): 
        x, y = ROOT.Double(), ROOT.Double()
        dmin = 0.
        if ipt < curve.GetN(): curve.GetPoint(ipt, x, y)
        if ipt != curve.GetN() and x == x1: yline.append(y)
        else:
            yline = sorted(yline, reverse = True)
            dy = [abs(yline[i] - yline[i + 1]) for i in range(len(yline) - 1)]
            if len(yline) <= 3 or envelop.GetN() == 0:
                newy = max(yline)
                if len(dy) > 2: dmin = min([abs(yline[i] - yline[i + 1]) for i in range(len(yline) - 1)])
            else:
                newy = max(yline)     
        #        dmin = min(dy)
                dmin = sum(dy) / float(len(dy))
                for iD in range(len(dy) - 1):
                    if dy[iD] <= dmin and dy[iD + 1] <= dmin:
                        newy = yline[iD]
                        break
            envelop.SetPoint(envelop.GetN(), x1, newy + dmin/2.)
            x1 = x
            yline = [y]

    x2, y2 = ROOT.Double(), ROOT.Double()
    envelop.GetPoint(envelop.GetN() - 1, x2, y2)
    envelop.SetPoint(envelop.GetN(), x2, 0.)  #Close exclusion curve at zero
    return envelop
