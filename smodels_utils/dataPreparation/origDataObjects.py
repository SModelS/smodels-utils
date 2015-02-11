#!/usr/bin/env python

"""
.. module:: origDataObjects
   :synopsis: Holds objects for reading of data given by experimentalists 

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""

import sys
import os
import ROOT
from smodels_utils.dataPreparation.helper import Locker

class Orig(Locker):
    
    infoAttr = []
    internalAttr = ['name','path', 'fileType', 'objectName',\
    'dataUrl', 'index']
    
    def __init__(self,name):
        
        self.name = name
        self.path = None
        self.fileType = None
        self.objectName = None
        self.dataUrl = None
        self.index = None

    def setSource(self, path, fileType, objectName = None, index = None):
        
        self.path = path
        self.fileType = fileType
        self.objectName = objectName
        self.index = index
        
    def txt(self):
        
        txtFile = open(self.path,'r')
        content = txtFile.readlines()
        txtFile.close
        for line in content:
            #print(line)
            try:
                values = line.split()
            except:
                Errors().txtFormat(self.path, 'Orig')
            values = [value.strip() for value in values] 
            try:
                values = [float(value) for value in values]
            except:
               Errors().value(self.path) 
            yield values  
    
    def root(self):
        
        if not isinstance(self.objectName, str):
            Errors().rootObject(self.objectName,self.path)
        rootFile = ROOT.TFile(self.path)
        obj = rootFile.Get(self.objectName)
        if not isinstance(obj,ROOT.TGraph):
            obj.SetDirectory(0)
        rootFile.Close()
        return obj
        
    def cMacro(self):
        
        if not isinstance(self.objectName, str):
            Errors().rootObject(self.objectName,self.path)
        ROOT.gROOT.SetBatch()
        ROOT.gROOT.ProcessLine(".x %s" %self.path)
        try:
            return eval("ROOT.%s" %self.objectName)
        except:
            Errors().noRootObject(self.objectName,self.path)

    def canvas(self):
        
        if not isinstance(self.objectName, str):
            Errors().rootObject(self.objectName, self.path)
        if not isinstance(self.index, int):
            Errors().index(self.index, self.path)
        rootFile = ROOT.TFile(self.path, 'r')
        canvas = rootFile.Get(self.objectName)
        return canvas.GetListOfPrimitives()[self.index]
    
    def __nonzero__(self):
        
        if self.path and self.fileType:
            return True
        return False            
 
 
class OrigLimit(Orig):
    
    plotableAttr = [] + Orig.infoAttr
    internalAttr = ['_unit', 'unit', ] + Orig.internalAttr
    
    def __init__(self,name):
        
        Orig.__init__(self,name)
        self._unit = 'pb'
        
    @property
    def unit(self):
        
        return self._unit
        
    @unit.setter
    def unit(self, unitString):
        
        units = ['fb','pb']
        if not unitString in units: Errors().unit(unitString)
        self._unit = unitString
        
    def __iter__(self):
        
        for point in getattr(self,self.fileType)():
            if self.unit == 'fb': point[-1] = point[-1]/1000.
            yield point
            
    def txt(self):
        
        for point in Orig.txt(self):
            if not len(point) == 3:
                Errors().txtFormat(self.path, 'OrigLimit', 3)
            yield point
    
    def root(self):
        
        limit = Orig.root(self)
        for point in self._getPoints(limit):
            yield point
                
    def cMacro(self):
       
        limit = Orig.cMacro(self)
        for point in self._getPoints(limit):
            yield point
            
    def canvas(self):
        
        limit = Orig.canvas(self)
        for point in self._getPoints(limit):
            yield point
                
    def _getPoints(self,limit):
        
        xAxis = limit.GetXaxis()
        yAxis = limit.GetYaxis()
        xRange = range(1,xAxis.GetNbins() + 1)
        yRange = range(1,yAxis.GetNbins() + 1)
        for xBin in xRange:
            x = xAxis.GetBinCenter(xBin)
            for yBin in yRange:
                y = yAxis.GetBinCenter(yBin)
                ul = limit.GetBinContent(xBin, yBin)
                if ul == 0.: continue
                yield [x, y, ul]
        
        
        
class OrigExclusion(Orig):
    
    infoAttr = [] + Orig.infoAttr
    internalAttr = ['sort', 'reverse'] + Orig.internalAttr
    
    def __init__(self,name):
        
        Orig.__init__(self,name)
        self.sort = False
        self.reverse = False
        
    def __iter__(self):
        
        points = []
        for point in getattr(self,self.fileType)():
            points.append(point)
        if self.reverse:
            points = reversed(points)
        if self.sort:
            points = sorted(points, key = lambda x: x[0])
        for point in points:
            yield point

    def txt(self):
        
        for point in Orig.txt(self):
            if not len(point) == 2:
                Errors().txtFormat(self.path, 'OrigExclusion', 2)
            yield point
            
    def svg(self):
        """ returns a TGraph from a txt file with coorinates in svg format
            first line in txt file needs scaling information"""
        f = open(self.path, 'r')
        lines = f.readlines()
        f.close()
        n = len(lines)
        xorig = 0
        yorig = 0
        if 'm' in lines[0].split()[0]:
            relative = True
        elif 'M' in lines[0].split()[0]:
            relative = False
        else:
            Errors().unknownSvg(self, self.path, lines[0].split()[0])
        ticks = lines[0].split()
        xticks = []
        yticks = []
        for tick in ticks[1:]:
            if tick.split(':')[0][:1] == 'x':
                xticks.append([float(tick.split(':')[0][1:-3]),float(tick.split(':')[1])])
                if tick.split(':')[0][-3:] != 'GeV':
                    Errors().unknownMassUnit(self.path, tick.split(':')[0][-3:])
            elif tick.split(':')[0][:1] == 'y':
                yticks.append([float(tick.split(':')[0][1:-3]),float(tick.split(':')[1])])
                if tick.split(':')[0][-3:] != 'GeV':
                    Errors().unknownMassUnit(self.path, tick.split(':')[0][-3:])
            else:
                Errors().unknownAxis(self, self.path, tick.split(':')[0][:1])
        if len(xticks) != 2:
            Errors().axesInformation(self, self.path)
        if len(yticks) != 2:
            Errors().axesInformation(self, self.path)    
        xGeV = (xticks[1][1]-xticks[0][1])/(xticks[1][0]-xticks[0][0])
        yGeV = (yticks[1][1]-yticks[0][1])/(yticks[1][0]-yticks[0][0])
        x0 = xticks[0][1] - xticks[0][0]*xGeV
        y0 = yticks[0][1] - yticks[0][0]*yGeV
        if relative:
            for l in lines[1:]:
                v = l.split(' ')
                xorig += float(v[0])
                yorig += float(v[1])
                x = (xorig-x0)/xGeV
                y = (yorig-y0)/yGeV
                yield [x,y]
        else:
            for l in lines[1:]:
                v = l.split(' ')
                xorig = float(v[0])
                yorig = float(v[1])
                x = (xorig-x0)/xGeV
                y = (yorig-y0)/yGeV
                yield [x,y]

                
    def root(self):
        
        limit = Orig.root(self)
        for point in self._getPoints(limit):
            yield point
                
    def cMacro(self):
       
        limit = Orig.cMacro(self)
        for point in self._getPoints(limit):
            yield point
    
    def canvas(self):
        
        limit = Orig.canvas(self)
        for point in self._getPoints(limit):
            yield point
    
    def _getPoints(self, graph):
        
        x, y = ROOT.Double(0.),ROOT.Double(0.)
        for i in range(0, graph.GetN()):
            graph.GetPoint(i, x, y)
            yield [float(x), float(y)]
        
        
class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def txtFormat(self,filePath, className, columns = ''):
        
        m = self._starLine
        m = m + 'wrong content in file: %s!!\n'  %filePath
        m = m + 'file content for a txt file readable by %s shuold be:\n' %className
        m = m + '%s columns with numbers diveded by a split() sign' %columns
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def value(self, filePath):
        
        m = self._starLine#
        m = m + 'valueError in file: %s\n' %filePath
        m = m + 'cant convert value to float'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def rootObject(self, objectName, filePath):
        
        m = self._starLine#
        m = m + 'objectError in file: %s\n' %filePath
        m = m + 'objectName for root file should be of string type\n'
        m = m + 'got %s' %objectName
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def noRootObject(self, objectName, filePath):
        
        m = self._starLine#
        m = m + 'objectError in file: %s\n' %filePath
        m = m + 'file contain no root object called %s\n' %objectName
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def index(self, index, filePath):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'index for listOfPrimitives should be of integer type\n'
        m = m + 'got %s' %objectName
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def unit(self, unitString):
        
        m = self._starLine#
        m = m + "unit for limits must be 'fb' or 'pb'\n"
        m = m + 'got %s' %unitString
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def unknownSvg(self, filePath, svg):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'unknown %s (svg)' %svg
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def unknownMassUnit(self, filePath, massUnit):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'unknown mass unit: %s\n' %massUnit
        m = m + 'mass unit have to be: GeV' 
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def unknownAxis(self, filePath, axis):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'unknown axis: %s\n' %axis
        m = m + 'mass unit have to be: x or y'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def axesInformation(self, filePath):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'too much/less information about one of the axes!'
        m = m + self._starLine
        print(m)
        sys.exit()


        

        
