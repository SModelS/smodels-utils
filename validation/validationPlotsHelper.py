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

def getTarget(path):
    """Checks if the target directory already exists and creates it if not.
    
    """
    
    if os.path.exists(path):
        logger.info('Target %s already exists.' %path)
        return path
    
    os.mkdir(path)
    logger.info('Created new directory: %s' %path) 
    return path 

def checkFile(path):
    """Checks if the data file already exists.
    If the file already exists, the user can decide whether to remove it, 
    or to exit the script.
    
    """
    if os.path.exists(path):
        print('File %s already exists!' %path)
        while True:
            userInput = raw_input('Replace old file? [y/n]:  ')
            if userInput == 'n':
                sys.exit()
            if userInput == 'y':
                os.remove(path)
                return path
    return path    
    
def getExtension(expResSet, param, val, valStr):
    """Produces possible extensions for the topology name via comparison
    to database known cases.
    
    """
    setMembers = expResSet.members
    extendedTopology = ''
    for exTop in setMembers:
        if setMembers[exTop] == (param, val):
            extendedTopology = exTop
    if not extendedTopology:
        if setMembers[exTop][0] == param:
            if param == 'massSplitting':
                extendedTopology = expResSet.expTopology.name + valStr
            elif param == 'M2/M0':
                extendedTopology = exTop.replace('%s' %(exTop[1]*100.), '%s'%(val*100.))
            else:
                extendedTopology = exTop.replace('%s' %exTop[1], '%s'%val)
    return extendedTopology        

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
    
def correctGraph(line):
    """Adds a new first point (given xm, ym) to the TGraph. For cases that the region doesn't allow for proper shading.
    
    """
    minX = ROOT.TMath.MinElement(line.GetN(),line.GetX())
    num = line.GetN()  
    gr = ROOT.TGraph()
    gr.SetName(line.GetName())
    gr.SetTitle(line.GetTitle())
    gr.SetPoint(0, minX, 0.)
    x = ROOT.Double(0.)
    y = ROOT.Double(0.)
    for ind in range(0, num):
        line.GetPoint(ind, x, y)
        logger.debug('Got point n=%s | x=%s | y=%s.' %(ind, x, y))
        gr.SetPoint(ind + 1, x, y)
        logger.debug('Add point n=%s | x=%s | y=%s to new line.' %(ind + 1, x, y))
    return(gr)
    
def cutGraph (graph, n, before = True, after = False):
    """Deletes all points from the TGraph before/after given number. For cases that region of plots doesn't match.
    
    """
    num = graph.GetN()
    logger.info('Got TGraph %s with %s points. Try to delet before(%s)/after(%s) n=%s.' %(graph.GetName(), num,  before, after, n))  
    gr = ROOT.TGraph()
    gr.SetName(graph.GetName())
    gr.SetTitle(graph.GetTitle())
    x = ROOT.Double(0.)
    y = ROOT.Double(0.)
    for ind in range(0,num):
        graph.GetPoint(ind, x, y)
        if before:
            if ind > n:
                logger.debug('Add point n=%s | x=%s | y=%s to new graph on n=%s.' %(ind, x, y, ind - n - 1))
                gr.SetPoint(ind - n - 1, x, y)
            else:
                logger.debug('Deleted point n=%s | x=%s | y=%s from new graph.' %(ind - n - 1, x, y))
        if after:
            if ind < n:
                logger.debug('Add point n=%s | x=%s | y=%s to new graph.' %(ind, x, y))
                gr.SetPoint(ind, x, y)
            else:
                logger.debug('Deleted point n=%s | x=%s | y=%s from new graph.' %(ind, x, y))
                continue
    return(gr)
    
def addPoint(graph, xm, ym):
    """Adds a new last point (given xm, ym) to the TGraph. For cases that the region doesn't allow for proper shading.
    
    """
    num = graph.GetN()
    logger.info('Got TGraph %s with %s points. Try to add last point xm=%s/ym=%s' %(graph.GetName(), num,  xm, ym))  
    gr = ROOT.TGraph()
    gr.SetName(graph.GetName())
    gr.SetTitle(graph.GetTitle())
    x = ROOT.Double(0.)
    y = ROOT.Double(0.)
    for ind in range(0, num):
        graph.GetPoint(ind, x, y)
        gr.SetPoint(ind, x, y)
        logger.debug('Add point n=%s | x=%s | y=%s to new graph.' %(ind, x, y))
    gr.SetPoint(num, xm, ym)
    logger.info('Added last point n=%s | x=%s | y=%s.' %(num, xm, ym))
    return(gr)    