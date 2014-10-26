#!/usr/bin/env python


"""
.. module:: massPlaneComputer.py
   :synopsis: Class MassPlane, returning objects of type MassPoint for each masspoint in the massPlain of gifen extendetTopology. 

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""
from __future__ import print_function
import setPath 
from smodels_tools.tools.databaseBrowser import Browser
from smodels.tools.physicsUnits import GeV
from smodels.tools.slhaChecks import SlhaStatus
from unum import Unum
import logging
import sys
import os
import argparse
import types

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)




class MassPlane(object):

    def __init__(self, browser, topo, extendedTopoName, massParametrization):
        
        self._browser = browser
        self.upperLimitDictionaries = self._getUpperLimitDictionaries(topo,extendedTopoName)
        self.xMin, self.xMax, self.yMin, self.yMax = self._getMinMaxValues(self.upperLimitDictionaries)
        self._xStep, self._yStep = self._getSteps(self.upperLimitDictionaries)
        self.xStepLimit = 25.
        self.yStepLimit = 25.
        self._condition = self._checkCondition(massParametrization[0])
        self._value = self._setValue(massParametrization[1])
        self._massPoints = self._createMassPonits()
        #for p in self._massPoints:
        #    print 'motherMass: %s, intMass: %s, lspMass: %s, xMass: %s, yMass: %s' \
        #    %(p.motherMass, p.interMass, p.lspMass, p.xMass, p.yMass)
        
    @property
    def xStep(self):
        if self.xStepLimit:
            if self._xStep < self.xStepLimit and \
            (self.xMax - self.xMin)/self._xStep > 20.:
                return self.xStepLimit
        return self._xStep
        
    @property
    def yStep(self):
        if self.yStepLimit:
            if self._yStep < self.yStepLimit and \
            (self.yMax - self.yMin)/self._yStep > 20.:
                return self.yStepLimit
        return self._yStep
    
    def iterListsWithFixedMotherMasses(self):
        
        mothermassList = []
        for point in self._massPoints:
            if not mothermassList: 
                mothermassList.append(point)
                continue
            comparisonList = [p.motherMass for p in mothermassList]
            if not point.motherMass in comparisonList:
                returnList = mothermassList
                mothermassList = []
                yield returnList
            mothermassList.append(point)
            if len(mothermassList) == len(self._massPoints):
                yield mothermassList 
            
            
            
        
    def _createMassPonits(self):
        
        massPoints = []
        xMass = self.xMin
        while xMass <= self.xMax:
            yMass = self.yMin
            while yMass <= self.yMax:
                massPoint = self._massPointFactory(xMass,yMass)
                massPoints.append(massPoint)
                yMass = yMass + self.yStep    
            xMass = xMass + self.xStep
        massPoints = sorted(massPoints, key=lambda point: point.motherMass)
        return massPoints
            
    def _massPointFactory(self, xMass, yMass):
        
        massPoint = MassPoint()
        massPoint.xMass = xMass
        massPoint.yMass = yMass
        if not self._condition:
            massPoint.motherMass = xMass
            massPoint.lspMass = yMass 
        if self._condition == 'massSplitting':
            massPoint.motherMass = xMass
            massPoint.lspMass = yMass + 1
            massPoint.interMass = self._value * yMass + (1 - self._value) * xMass
        if self._condition == 'fixedM2':
            massPoint.motherMass = xMass
            massPoint.lspMass = yMass + 1
            massPoint.interMass = self._value
        if self._condition == 'fixedM1':
            massPoint.motherMass = self._value
            massPoint.lspMass = yMass
            massPoint.interMass = xMass
        if self._condition == 'M2-M1':
            massPoint.motherMass = xMass
            massPoint.lspMass = yMass
            massPoint.interMass = xMass - self._value #have to be fixed in expObjects
        if self._condition == 'M2-M0':
            massPoint.motherMass = xMass
            massPoint.lspMass = yMass
            massPoint.interMass = self._value + yMass
        if self._condition == 'fixedLSP':
            massPoint.motherMass = xMass
            massPoint.lspMass = self._value
            massPoint.interMass = yMass
        if self._condition == 'M2/M0':
            massPoint.motherMass = xMass
            massPoint.lspMass = yMass
            massPoint.interMass = self._value * yMass
        return massPoint
            
            
    def _setValue(self,value):
        
        #print '## %s' %value
        if isinstance(value,Unum):
            return float(value/GeV)
        if isinstance(value, int): 
            return float(value)
        return value
    
    
    def _checkCondition(self, condition):
        
        if condition in [None, 'massSplitting', 'fixedM2','fixedM1', 'M2-M1', 'M2-M0','fixedLSP', 'M2/M0']:
            return condition
        logger.warning('Unknown condition: %s' %condition)
        return 'unknown'
        
        
    def _getUpperLimitDictionaries(self, topo, extendedTopoName):
        
        analyses = topo.analyses
        dictionaries = []
        for anaName in analyses:
            resultName = anaName + '-' + extendedTopoName
            resultSet = self._browser.expResultSet(anaName,topo.name)
            if resultName in resultSet.hasUpperLimitDicts():
                #result = self._browser.expResult(anaName,extendedTopoName)
                result = resultSet.results[resultName]
                #print (result.axes)
                dictionary = result.upperLimitDict()
                if dictionary: dictionaries.append(dictionary)
                #dictionarySet = resultSet.upperLimitDicts()
                #dictionary = dictionarySet[resultName]
                #if dictionary:s dictionaries.append(dictionarySet[resultName])
                
        if not dictionaries:
            logger.warning('There are no UpperlimitDictionaries for %s' %extendedTopoName)
        return dictionaries
        
    def _getMinMaxValues(self, upperLimitDictionaries):
        
        xMin = 99999.
        xMax = 0.
        yMin = 99999.
        yMax = 0.
        for dictionary in upperLimitDictionaries:
            for x in dictionary:
                if x < xMin and x >= 0.:
                    xMin = x
                if x > xMax:
                    xMax = x
                for y in dictionary[x]:
                    if y < yMin and y >= 0.:
                        yMin = y
                    if y > yMax:
                        yMax = y
        xMin = round(xMin,0)
        xMax = round(xMax,0)
        yMin = round(yMin,0)
        yMax = round(yMax,0)
        return [xMin, xMax, yMin, yMax]
        
    def _getSteps(self, upperLimitDictionaries):
        
        xStepMin = 9999999.
        yStepMin = 9999999.
        for dictionary in upperLimitDictionaries:
            #print dictionary
            xValues = [x for x in dictionary]
            xValues.sort()
            #print 'xValues: %s' %xValues
            if len(xValues) > 1: 
                xStep = xValues[1] - xValues[0]
                if xStep < xStepMin: xStepMin = xStep
            for x in xValues:
                y = dictionary[x]
                yValues = [y for y in dictionary[x]]
                yValues.sort()
                # print 'yValues: %s' %yValues
                if len(yValues) > 1:
                    yStep = yValues[1] - yValues[0]
                    if yStep < yStepMin: yStepMin = yStep
        xStepMin = round(xStepMin,0)
        yStepMin = round(yStepMin,0)
        return [xStepMin, yStepMin]
            
    def __nonzero__(self):
        
        if self.upperLimitDictionaries or self._condition == 'unknown':
            return True
        return False

class MassPoint(object):
    
    def __init__(self):
        self.xMass = None # value on xaxes
        self.yMass = None # value on yaxes
        self.lsbMass = None
        self.interMass = None
        self.motherMass = None
        
        
def main():
    
    argparser = argparse.ArgumentParser(description = \
    'Produces the slha files for smodels validation plots')
    argparser.add_argument ('-b', '--Base', \
    help = 'set path to base-directory of smodels-database\n \
    - default: /afs/hephy.at/user/w/walten/public/sms/', \
    type = types.StringType, default = '/afs/hephy.at/user/w/walten/public/sms/')
    argparser.add_argument ('-t', '--topology', \
    help = 'topology that slha-files should be produced for - default: T1',\
    type = types.StringType, default = 'T1')
    args = argparser.parse_args()
    
    browser = Browser(args.Base)
    topo = browser.expTopology(args.topology)
    parametrizations = topo.massParametrizations
    slhaFileSets = []
    for extendedTopoName,  massParametrization in parametrizations.iteritems():
        massPlane = MassPlane(browser,topo, extendedTopoName,massParametrization)
        print('********%s************' %extendedTopoName)
        print('xMin: %s, xMax: %s, xStep: %s' \
        %(massPlane.xMin, massPlane.xMax, massPlane.xStep))
        print('yMin: %s, yMax: %s, yStep: %s' \
        %(massPlane.yMin, massPlane.yMax, massPlane.yStep)) 
            
        
        
if __name__ == '__main__':
    main()
        
 