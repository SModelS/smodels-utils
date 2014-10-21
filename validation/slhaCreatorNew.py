#!/usr/bin/env python


"""
.. module:: slhaCreatorNew
   :synopsis: An iterator object returning slha-files for validation plots

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""
import setPath 
from smodels_tools.tools.databaseBrowser import Browser
import logging
import sys
import os

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.WARNING)




class MassPlane(object):

    def __init__(self, browser, topo, extendetTopoName):
        
        self._browser = browser
        self.upperLimitdictionarys = self._getUpperLimitDictionarys(topo,extendetTopoName)
        self.xMin, self.xMax, self.yMin, self.yMax = self._getMinMaxValues(self.upperLimitdictionarys)
        self._xStep, self._yStep = self._getSteps(self.upperLimitdictionarys)
        self.xStepLimit = 25.
        self.yStepLimit = 25.
        
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
        
    def _getUpperLimitDictionarys(self, topo, extendetTopoName):
        
        analyses = topo.analyses
        dictionarys = []
        for anaName in analyses:
            resultName = anaName + '-' + extendetTopoName
            resultSet = self._browser.expResultSet(anaName,topo.name)
            if resultName in resultSet.hasUpperLimitDicts():
                dictionarySet = resultSet.upperLimitDicts()
                dictionary = dictionarySet[resultName]
                if dictionary: dictionarys.append(dictionarySet[resultName])
                
        if not dictionarys:
            logger.warning('There are no UpperlimitDictionarys for %s' %extendetTopoName)
        return dictionarys
        
    def _getMinMaxValues(self, upperLimitdictionarys):
        
        xMin = 99999.
        xMax = 0.
        yMin = 99999.
        yMax = 0.
        for dictionary in upperLimitdictionarys:
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
        return [xMin, xMax, yMin, yMax]
        
    def _getSteps(self, upperLimitdictionarys):
        
        xStepMin = 9999999.
        yStepMin = 9999999.
        for dictionary in upperLimitdictionarys:
            xValues = [x for x in dictionary]
            xValues.sort()
            print 'xValues: %s' %xValues
            if len(xValues) > 1: 
                xStep = xValues[1] - xValues[0]
                if xStep < xStepMin: xStepMin = xStep
            for y in dictionary[x]:
                yValues = [y for y in dictionary[x]]
                yValues.sort()
                print 'yValues: %s' %yValues
                if len(yValues) > 1:
                    yStep = yValues[1] - yValues[0]
                    if yStep < yStepMin: yStepMin = yStep
        return [xStepMin, yStepMin]
            
    def __nonzero__(self):
        
        if self.upperLimitdictionarys:
            return True
        return False

        
class SlhaFileSet(object):
    
    def __init__(self, browser, extendetTopoName, massParametrization,events = 1000, order = 'LO', \
    unlink = True,sqrts =8.0):
        
        self._browser = browser
        self._massPlane = MassPlane(browser, extendetTopoName)
        self.directory = self._createDirectory(extendetTopoName, events, order, sqrts)
        print extendetTopoName
        print len(massPlane.upperLimitdictionarys)
        print 'xmin: %s, xmax: %s, ymin: %s, ymax: %s' %(self._massPlane.xMin, self._massPlane.xMax, self._massPlane.yMin, self._massPlane.yMax)
        print 'xStep: %s, yStep %s' %(self._massPlane.xStep, self._massPlane.yStep)
        
    def _createDirectory(extendetTopoName, events, order, sqrts):
        
        directory = '../slha/%s_%s_%s_%sTeV_slhas' \
        %(extendetTopoName, events, order, sqrts)
        if os.path.exists(directory):
            print('Folder %s already exists!' %directory)
            while True:
                userInput = raw_input('Remove old files? [y/n]:  ')
                if userInput == 'n': return None
                if userInput == 'y': break
            os.system('rm -r %s' %directory)
        os.makedirs(directory)
        logger.info('Created new folder %s.' %directory)
        return directory
        
    def __nonzero__(self):
        
        if self._massPlane and self._directory:
            return True
        return False
        
    
    
    
    
    
    
    
def main():
    
    browser = Browser()
    extendetTopoName = 'T6ttWWx125'
    topo = browser.expTopology('T6bbWW')
    parametrizations = topo.massParametrizations
    for extendetTopoName,  massParametrization in parametrizations.iteritems():
        fileSet = SlhaFileSet(browser,extendetTopoName,massParametrization)
        print fileSet.directory
        
        
if __name__ == '__main__':
    main()
 