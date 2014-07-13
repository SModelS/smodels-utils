 #!/usr/bin/env python

"""
.. module:: experimentalResults
   :synopsis: Holds all the experimental objects retrieved from smodels-database\ 
   in order to produce summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""    

import ROOT
import logging, os, types
import prettyDescriptions
import setPath
import sys
import databaseBrowser
from experimentalObjects import expAnalysis, expTopology

   
class ExpResult (object):
    """Contains all result-specific information and objects (e.g. 
    exclusion lines, histograms, ...). Uses the extended result objects to 
    handle different mass assumptions for given topology and analysis.
    """
    
    def __init__ (self, run, expAnalysis, expTopology):
        """Sets all private variables, especially self._extendedResults 
        as list containing all available extended results as objects.
    
        """
        self._expTopo = expTopology
        self._expAna = expAnalysis
        self._topo = expTopology.name
        self._ana = expAnalysis.name
        self._run = run
        self.extendedTopos = self._expAna.extendedTopologies[self._topo]
        self._extendedResults = self._getExtendedResults
        logger.info('Creating experimental result object for %s-%s!' \
        %(self._ana, self._topo))
        self._setExtendedResultsDefault
        
    @property
    def _getExtendedResults(self):
        """Retrieves a list of all extended results we have for this 
        analysis topology pair.
        
        """
        exRes = [ExtendedResult(extop, self._ana, self.ROOT) for extop in \
        self.extendedTopos]
        return exRes
        
    @property    
    def _setExtendedResultsDefault(self):
        """Defines which mass assumptions for this result will be the default 
        for the extended results. If there are no further assumptions, the 
         only one there will be the default, else the one with 
         mass splitting = 050.
    
        """
        # ### FIX ME: rework default settings and docstrings 
        if len(self._extendedResults) == 1: 
            self._extendedResultsDefault = self._extendedResults[0]
            return
        self._extendedResultsDefault = [exRes for exRes in self._extendedResults\
        if exRes.topoName()[:3] == '050']
        self._extendedResultsDefault = self._extendedResultsDefault[0]
    
    @property    
    def expAnalysis(self):
        """Returns the analysis-object linked to this result-object.
        
        """
        return self._expAna
    
    @property    
    def expTopology(self):
        """Returns the topology-object linked to this result-object.
        
        """
        return self._expTopo
    
    # ### FIX ME: does this belong in here?
    @property    
    def hasROOT(self):
        if databaseBrowser.Browser._checkResults(self._ana, \
        requested = 'sms.root'): return True
        return False
    
    @property    
    def hasPY(self):
        if databaseBrowser.Browser._checkResults(self._name, \
        requested = 'sms.py'): return True
        return False
    
    @property    
    def ROOT(self):
        return databaseBrowser.Browser._checkResults(self._ana, \
        requested = 'sms.root')
        
    @property    
    def PY(self):
        return databaseBrowser.Browser._checkResults(self._name, \
        requested = 'sms.py')
    
    @property    
    def checkedBy(self):
        """Retrieves checked_by entry from info.txt.
        
        """
        infoLine = self._expAna.checked
        logger.debug('Got infoLine from Analysis-object: %s.' %infoLine)
        if not infoLine: return None
        # ### FIX ME: the IF below will be obsolet when 
        #the checked flag is fixed in every info.txt
        if 'AL' in infoLine: 
            logger.warning('There is no information about single topologies.')
            return infoLine[0]
        infoLine = [ch for ch in infoLine if self._topo in ch]
        logger.debug('First preprocessed infoLine: %s.' %infoLine)
        if not infoLine:
            logger.warning('This Result is not checked!')
            return None
        infoLine = [ch.split(':') for ch in infoLine]
        logger.debug('Second preprocessed infoLine: %s.' %infoLine)
        infoLine = infoLine[0]
        logger.debug('Return value of infoLine: %s.' %infoLine)
        return infoLine[1].strip()
    
    @property
    def extendedResults(self):
        """Returns a list containing all available extended 
        results as objects.
        
        """
        return self._extendedResults
        
    def exclusionLines(self,expected = False, sigma = 0):
        """Returns a list containing the exclusion lines for all mass 
        assumptions available for this result as Root.TGraph-objects. 
        If expected is set to False, the observed exclusion lines will 
        be returned, else the expected ones. 
        Possible values for keyword argument 'sigma' are: -1,0,1.
        
        """
        return [exRes.exclusionline(expected, sigma) for exRes in \
        self._extendedResults]
        
    def exclusions(self,expected = False, typ = 0):
        """Returns a list containing all exclusion values for all mass 
        assumptions available for this result. If expected is set to False, 
        the observed values will be returned, else the expected ones. 
        Possible values for keyword argument 'typ' are: 'limit', 'min', 'max'.
        
        """
        return [exRes.exclusion(expected, sigma) for exRes in \
        self._extendedResults]
        
    def exclusionLine(self, extendedTopoName = 'default', expected = False, \
    sigma = 0):
        """Returns one exclusion line as Root.TGraph-object if extendedTopoName 
        is set to 'default', the exclusion line linked to the default 
        extendedResult is returned if exclusionline for other extendedResult 
        is needed, the name of the linked extendedTopo is requested. 
        If expected is set to False, the observed exclusionline will be returned, 
        else the expected exclusionline will be returned. Possible values for 
        keywordargument "sigma" are: -1,0,1. depending on this value the 
        exclusionlines for sigma = -1,0,1 will be returned.
        
        """
        # ### FIX ME: improve docstring!
        return self._getSingleAttribute(extendedTopoName, expected, \
        sigma, 'exclusionLine')
        
    def exclusion(self, extendedTopoName = 'default',expected = False, typ = 'max'):
        """Returns one exclusion value if extendedTopoName is set to 'default', 
        the value linked to the default extendedResult is returned if values 
        for other extendedResult is needed, the name of the linked extendedTopo 
        is requested. If expected is set to False, the observed values will be 
        returned, else the expected values will be returned. Possible values 
        for keywordargument "type" are: 'limit', 'min', 'max'.
        
        """
        # ### FIX ME: improve docstring!
        return self._getSingleAttribute(extendedTopoName, expected, typ, '\
        exclusion')
        
    def _getSingleAttribute(self, extendedTopoName, expected, argument, \
    attribute):
        """Private method used by the methods 'exclusionLine' and 'exclusion'.
        
        """
        if extendedTopoName == 'default':
            return getattr(self._extendedResultsDefault, attribute)(expected, argument)
        extendedResults = [exRes for exRes in self._extendedResults if \
        extendedTopoName == exRes.topoName]
        return getattr(extendedResults[0], attribute)(expected, argument)
    
    
        
    def selectExclusionLine(self, expected = False, sigma = 0, \
    condition = 'xvalue', value = 050):
        """Selects one exclusion line (out of all exclusionLines for this 
        topology) corresponding to a specified case of mass proportions 
        (e.g. x-value = 050, mass of LSP = 50 GeV, ...)
        
        """
        # ### FIX ME: maybe define a standard configuration for other 
        #conditions as xvalues
        
        return self.exclusionLine(extendedTopoName = 'default', \
        expected = expected, sigma = sigma)

class ExtendedResult(object):
    """Contains all specific informations linked to one extended result,
    where an extended result denotes a pair of analysis and topology
    when a specified case of mass proportions is assumed (e.g. x-value = 050, 
    mass of LSP = 50 GeV, ...).
    
    """
    
    def __init__(self, extendedTopologyName, expAnalysis, path):
        """Sets all private variables and initiates the dictionaries for 
        exclusion lines and exclusions.
        
        """
        self._topoName = extendedTopologyName
        self._expAna = expAnalysis
        self._path = path
        self._exclusionLines = {}
        self._exclusions = {}
        
        
    @property
    def topoName(self):
        """Returns the name of the extended topology e.g.: 'TChiChipmSlepL050'.

        """
        return self._topoName
        
    @property
    def dictOfExclusionLines(self):
        """Returns a nested dictionary, containing all available 
        exclusion lines: {'observed': {1: Root.TGraph-object, 
        0: Root.TGraph-object, -1: Root.TGraph-object}, 'expected': 
        {1: Root.TGraph-object, 0: Root.TGraph-object, 
        -1: Root.TGraph-object}}
        
        """
        if not self._exclusionLines: self._setExclusionLines
        return self._exclusionlines
        
    @property
    def dictOfExclusions(self):
        """Returns a nested dictionary, containing all available 
        exclusion values: {'observed': {'limit': value, 'min':value, 
        'max': value}, 'expected': {'limit': value, 'min': value, 
        'max': value}}
        
        """
        if not self._exclusions: self._setExclusions
        return self._exclusions

    def exclusionLine(self, expected = False, sigma = 0):
        """Retrieves one specified exclusion line (out of all exclusion lines  
        available for this topology) as root TGraph. If expected is set 
        to False, the observed exclusion line will be returned, else the 
        expected one. Possible values for keyword argument "sigma" are: -1, 0, 1.
        
        """
        if not self._exclusionLines: self._setExclusionLines()
        sigmaDict = self._exclusionlines['observed']
        if expected: sigmaDict = self._exclusionLines['expected']
        return sigmaDict[sigma]
        
    def exclusion(self, expected = False, typ ='max'):
        """Retrieves one specified exclusion value (out of all exclusion   
        values available for this topology). If expected is set to False, the 
        observed value will be returned, else the expected one. 
        Possible values for keyword argument "type" are: 
        'limit', 'min', 'max'.
        
        """
        if not self._exclusions: self._setExclusions()
        typeDict = self._exclusionlines['observed']
        if expected: typeDict = self._exclusionlines['expected']
        return typeDict[typ]
        
    def _setExclusionLines(self):
        """Private method used by the methods 'exclusionLines' and 
        'dictOfExclusionLines'. Retrieves the exclusion lines from the 
        sms.root-file linked to the corresponding analysis and builds a nested 
        dictionary including all the exclusion lines.
        
        """
        path = checkResults(self._ana.getRun(), self._ana.getName(), 'sms.root')
        if not path: return None
        rootFile = ROOT.TFile(path)
        self._exclusionlines = {'observed':'exclusion','expected':'expectedexclusion'}
        for key, value in self._exclusionlines.items(): 
            sigmaDict = {1:'p1',0:'',-1:'m1'}
            for sigmaKey, sigmaValue in sigmaDict.items():
                sigmaDict[sigmaKey] = rootFile.Get(value + sigmaValue + '_' + self.name)
            self._exclusionlines[key] = sigmaDict
                
    #if we change the read steps provided by readInfo and get info, we can do this in a better way            
    def _setExclusions(self):
        """Private method used by the methods 'exclusions' and 
        'dictOfExclusions'. Retrieves the exclusion values from the 
        info.txt-file linked to the corresponding analysis and builds a nested 
        dictionary including all the exclusion values of form:
        self._exclusions = {'observed': 'exclusion', 
        'expected': 'expectedExclusion'}
        
        """
        
        for key, value in self._exclusions.items():
            info = getInfo(self._ana.getRun(), self._ana.getName(), value)
            try:
                info = [line.split() for line in info]
                info = [line for line in info if line[1] == self.name]
                info = info[0]
            except: 
                del self._exclusions[key]
                continue            
            typeDict = {'limit':2,'min':3,'max':4}
            for typeKey,typeValue in typeDict.items():
                typeDict[typeKey] = info[typeValue]
                