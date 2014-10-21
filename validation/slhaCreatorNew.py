#!/usr/bin/env python


"""
.. module:: slhaCreatorNew
   :synopsis: An iterator object returning slha-files for validation plots

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""
import setPath 
from smodels_tools.tools.databaseBrowser import Browser
from smodels.tools.physicsUnits import GeV
from unum import Unum
import logging
import sys
import os

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)




class MassPlane(object):

    def __init__(self, browser, topo, extendetTopoName, massParametrization):
        
        self._browser = browser
        self.upperLimitdictionarys = self._getUpperLimitDictionarys(topo,extendetTopoName)
        self.xMin, self.xMax, self.yMin, self.yMax = self._getMinMaxValues(self.upperLimitdictionarys)
        self._xStep, self._yStep = self._getSteps(self.upperLimitdictionarys)
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
        if not self.xStepLimit: return self._xStep
        if self._xStep < self.xStepLimit: return self.xStepLimit
        return self._xStep
        
    @property
    def yStep(self):
        if not self.yStepLimit: return self._yStep
        if self._yStep < self.yStepLimit: return self.yStepLimit
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
            calculateXsecs = True
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
            massPoint.lspMass = yMass
            massPoint.interMass = self._value * yMass + (1 - self._value) * xMass
        if self._condition == 'fixedM2':
            massPoint.motherMass = xMass
            massPoint.lspMass = yMass
            massPoint.interMass = self._value
        if self._condition == 'fixedM1':
            massPoint.motherMass = self._value
            massPoint.lspMass = yMass
            massPoint.interMass = xMass
        if self._condition == 'M2-M1':
            massPoint.motherMass = xMass
            massPoint.lspMass = yMass
            massPoint.interMass = self._value + xMass
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
        
        
    def _getUpperLimitDictionarys(self, topo, extendetTopoName):
        
        analyses = topo.analyses
        dictionarys = []
        for anaName in analyses:
            resultName = anaName + '-' + extendetTopoName
            resultSet = self._browser.expResultSet(anaName,topo.name)
            if resultName in resultSet.hasUpperLimitDicts():
                result = self._browser.expResult(anaName,extendetTopoName)
                print result.axes
                dictionary = result.upperLimitDict()
                if dictionary: dictionarys.append(dictionary)
                #dictionarySet = resultSet.upperLimitDicts()
                #dictionary = dictionarySet[resultName]
                #if dictionary: dictionarys.append(dictionarySet[resultName])
                
        if not dictionarys:
            logger.warning('There are no UpperlimitDictionarys for %s' %extendetTopoName)
        return dictionarys
        
    def _getMinMaxValues(self, upperLimitdictionarys):
        
        xMin = 99999.
        xMax = 0.
        yMin = 99999.
        yMax = 0.
        for dictionary in upperLimitdictionarys:
            for y in dictionary:
                if y < yMin and y >= 0.:
                    yMin = y
                if y > yMax:
                    yMax = y
                for x in dictionary[y]:
                    if x < xMin and x >= 0.:
                        xMin = x
                    if x > xMax:
                        xMax = x
        return [xMin, xMax, yMin, yMax]
        
    def _getSteps(self, upperLimitdictionarys):
        
        xStepMin = 9999999.
        yStepMin = 9999999.
        for dictionary in upperLimitdictionarys:
            #print dictionary
            yValues = [y for y in dictionary]
            yValues.sort()
            #print 'xValues: %s' %xValues
            if len(yValues) > 1: 
                yStep = yValues[1] - yValues[0]
                if yStep < yStepMin: yStepMin = yStep
            for y in yValues:
                x = dictionary[y]
                xValues = [x for x in dictionary[y]]
                xValues.sort()
                # print 'yValues: %s' %yValues
                if len(xValues) > 1:
                    xStep = xValues[1] - xValues[0]
                    if xStep < xStepMin: xStepMin = xStep
        return [xStepMin, yStepMin]
            
    def __nonzero__(self):
        
        if self.upperLimitdictionarys or self._condition == 'unknown':
            return True
        return False

class MassPoint(object):
    
    def __init__(self):
        xMass = None # value on xaxes
        yMass = None # value on yaxes
        lsbMass = None
        interMass = None
        motherMass = None
        
        
        
class SlhaFileSet(object):
    
    def __init__(self, browser, topo, extendetTopoName, massParametrization, events = 10, order = 'NLL', \
    unlink = True, sqrts =8.0):
        
        self._browser = browser
        self._massPlane = MassPlane(browser, topo, extendetTopoName, massParametrization)
        self.directory = self._createDirectory(extendetTopoName, events, order, sqrts)
        
    def create(self):
        for l in self._massPlane.iterListsWithFixedMotherMasses():
            print '*******************************************'
            for p in l:
                print 'motherMass: %s, intMass: %s, lspMass: %s, xMass: %s, yMass: %s' \
                %(p.motherMass, p.interMass, p.lspMass, p.xMass, p.yMass)
    
    def _createDirectory(self, extendetTopoName, events, order, sqrts):
        
        directory = '../slha/%s_%s_%s_%sTeV_slhas' \
        %(extendetTopoName, events, order, int(sqrts))
        if os.path.exists(directory):
            print'Folder %s already exists!' %directory
            while True:
                userInput = raw_input('Remove old files? [y/n]:  ')
                if userInput == 'n': return None
                if userInput == 'y': break
            os.system('rm -r %s' %directory)
        if os.path.exists(directory +'.tar'):
            print'tarball %s already exists!' %(directory + '.tar')
            while True:
                userInput = raw_input('Remove tarball? [y/n]:  ')
                if userInput == 'n': return None
                if userInput == 'y': break
            os.system('rm %s' %(directory + '.tar'))
        os.makedirs(directory)
        logger.info('Created new folder %s.' %directory)
        return directory
        
    def __nonzero__(self):
        
        if self._massPlane and self.directory:
            return True
        return False
        
    
    
    
    
    
    
    
def main():
    
    browser = Browser()
    extendetTopoName = 'T6ttWWx125'
    topo = browser.expTopology('T6bbWW')
    #topo = browser.expTopology('T1')
    parametrizations = topo.massParametrizations
    for extendetTopoName,  massParametrization in parametrizations.iteritems():
        fileSet = SlhaFileSet(browser,topo, extendetTopoName,massParametrization)
        print fileSet.directory
        if fileSet: fileSet.create()
        
        
if __name__ == '__main__':
    main()
 