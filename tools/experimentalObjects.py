#!/usr/bin/env python

"""
.. module:: experimentalObjects
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

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)
    
class ExpAnalysis(object):
    
    """Contains all analysis-specific information 
    (e.g. PAS, lumi, publication-url, ...)
    
    """
        
    def __init__(self, analysis, infotxt, run):
        self._name = analysis
        self._info = infotxt.info
        self._metaInfo = infotxt.metaInfo
        self._topologies = infotxt.topologies
        self._extendedTopologies = infotxt.extendedTopologies()
        self._run = run
        self._verbosity = 'error'
     
    @property
    def verbosity(self):
        """Tells the level the logger is set to.
        
        """
        return self._verbosity
        
    @verbosity.setter
    def verbosity(self, level):
        """Set the logger to specified level.
        
        """
        self._verbosity = level
        self._setLogLevel(level)
        
    def _setLogLevel(self, level = 'error'):
        if level == 'debug':
            logger.setLevel(level=logging.DEBUG)
        if level == 'info':
            logger.setLevel(level=logging.INFO)
        if level == 'warning':
            logger.setLevel(level=logging.WARNING)
        if level == 'error':
            pass

    def _parseMetaInfo(self, requested):
        if not requested in self._metaInfo:
            logger.warning('Requested keyword %s could not be found for %s!' \
            %(requested, self._name))
            return None
        return self._metaInfo[requested]
        
    def _parsInfo(self, requested):
        content = [line for line in self._info if requested in line]
        if not content:
            logger.warning('Requested lines %s could not be found for %s!' \
            %(requested, self._name))
            return None
        content = [line.split(':')[1].strip() for line in content]
        return content
    
    @property
    def lumi(self):
        return self._parseMetaInfo('lumi')

    @property
    def publishedData(self):
        return self._parseMetaInfo('publisheddata')
        
    @property
    def sqrts(self):
        return self._parseMetaInfo('sqrts')
        
    @property
    def pas(self):
        return self._parseMetaInfo('pas')
        
    @property    
    def url(self):
        return self._parseMetaInfo('url')
    
    @property    
    def hasUrl(self):
        if self._parseMetaInfo('url'): return True
        return False
    
    @property    
    def experiment(self):
        if 'ATLAS' in self._run:
            return 'ATLAS'
        return 'CMS' 
        
    @property    
    def comment(self):
        return self._parseMetaInfo('comment')
    
    @property
    def prettyName(self):
        return self._parseMetaInfo('prettyname')
        
    @property    
    def hasConstraints(self):
        """Checks if there are any constraints for this Analysis.
        
        """
        
        if self._parsInfo('constraint'): return True
        return False
        
    @property
    def constraints(self):
        return self._parsInfo('constraint')
        
    @property    
    def private(self):
        """States if the analysis is private (True) or public (False).

        """
        return self._parseMetaInfo('private')==1
    
    @property    
    def hasArxiv(self):
        if self._parseMetaInfo('arxiv'): return True
        return False
        
    @property        
    def arxiv(self):
        return self._parseMetaInfo('arxiv')
    
    @property    
    def hasPublication(self):
        if self._parseMetaInfo('publication'): return True
        return False

    @property    
    def publication(self):
        return self._parseMetaInfo('publication')
    
    @property
    def hasAxes(self):
        if self._parseMetaInfo('axes'): return True
        return False
        
    @property
    def axes(self):
        """Retrieves the information stored in the axes-labeled line of 
        info.txt as list.
    
        """
        if self.hasAxes:
            return self._parseMetaInfo('axes').split(',')
        return None
    
    @property    
    def isChecked(self):
        if self._parseMetaInfo('checked'): return True
        return False
        
    @property        
    def checked(self):
        return self._parseMetaInfo('checked')
    
    @property
    def isPublished(self):
        if self._parseMetaInfo('arxiv') or self._parseMetaInfo('publication'):
            return True
        return False
    
    @property    
    def name(self):
        return self._name
    
    @property    
    def run(self):
        return self._run
        
    @property
    def topologies(self):
        """Retrieves all the topologies this analysis has results for as strings.
        
        """
        return self._topologies
    
    @property
    def expTopologies(self):
        """Retrieves all the experimental topology objects this analysis has 
        results for.
        
        """
        if self.getTopologyNames():
            topos = [ExpTopology(t) for t in self.getExpTopologyNames()]
            return topos
        return None
        
    @property    
    def extendedTopologies(self):
        """Retrieves all the topologies with their particular extentions 
        (refering to possible mass conditions) this analysis has results 
        for as strings.
        
        """
        return self._extendedTopologies
        
    #def getRestOfInfo => contact, arxiv, publisheddata ### check something missing?

class ExpTopology(object):
    """Contains all topology-specific information (e.g. analyses and runs that 
    contain this topology, category, particles resp. productionmode, ...)
    
    """
    def __init__ (self, topology, topoDict):
        self._name = topology
        self._topoDict = topoDict
        self._runs = [key for key in self._topoDict]
        self._analyses = self._anas
        self._verbosity = 'error'
     
    @property
    def verbosity(self):
        """Tells the level the logger is set to.
        
        """
        return self._verbosity
        
    @verbosity.setter
    def verbosity(self, level):
        """Set the logger to specified level.
        
        """
        self._verbosity = level
        self._setLogLevel(level)
        
    def _setLogLevel(self, level = 'error'):
        if level == 'debug':
            logger.setLevel(level=logging.DEBUG)
        if level == 'info':
            logger.setLevel(level=logging.INFO)
        if level == 'warning':
            logger.setLevel(level=logging.WARNING)
        if level == 'error':
            pass
        
    @property    
    def _anas(self):
        """Extracts all the analyses given as inner keys of nested topoDict.
        
        """
        anas = []
        for r in self._runs:
            for a in self._topoDict[r]:
                anas.append(a)
        return anas
        
    @property    
    def _category(self):
        """Takes the category for this topology from every info.txt, 
        compairs them and returns the string if they are all the same. 
        Raises an ERROR and returns None if they are not!
        
        """
        
        cats = []
        for run in self._topoDict:
            for ana in self._topoDict[run]:
                try:
                    category = self._topoDict[run][ana][0][self._name]
                    if cats.count(category) == 0:
                        cats.append(category)
                    if cats and cats.count(category) == 0:
                        logger.error('There are different categories for topology %s! \
                        Please check the database entry %s-%s!' %(self._name, run, ana))
                except KeyError:
                    logger.warning('The category for %s is missing! Please \
                    check the database entry %s-%s!' %(self._name, run, ana))
        logger.debug('List of categories: %s.' %cats)
        if len(cats) == 1:
            return cats[0]
        
        logger.error('Unable to get category for topology %s!' %self._name)
        return None
    
    @property    
    def _constraints(self):
        """Takes the constraints for this topology from every info.txt, 
        returns a list containing all available constraints.
        
        """
        
        const = []
        for run in self._topoDict:
            for ana in self._topoDict[run]:
                try:
                    c = self._topoDict[run][ana][1][self._name]
                    if const.count(c) == 0:
                        const.append(c)
                except KeyError:
                    logger.warning('The constraint for %s is missing! \
                    Please check the database entry %s-%s!' %(self._name, run, ana))
        logger.debug('List of constraints: %s.' %const)
        return const
        
        logger.error('Unable to get category for topology %s!' %self._name)
        return None
        
    @property    
    def name(self):
        return self._name
    
    @property
    def analyses(self):
        return self._analyses
    
    @property
    def runs(self):
        return self._runs
        
    @property
    def category(self):
        return self._category
      
    @property
    def constraints(self):
        return self._constraints
        
    #@property
    #def analysesNames(self, run = None):
        #"""Retrieves the names (as strings) of all analyses existing for 
        #this topology. Returns a list of names for one given run, 
        #or a dictionary with runs as keys.
        
        #"""
        #if not run:
            #anas = {}
            #logger.warning('no run was given, therefore trying all available \
            #runs %s and returning dictionary!' %self._runs)
            #for r in self._runs:
                #if getAllAnalyses(run = r, topology = self._name):
                    #anas[r] = [a for a in getAllAnalyses(run = r, \
                    #topology = self._name)]
            #return anas
        #return getAllAnalyses(run = run, topology = self._name)
    
    def _slackExpTopologyName(self):
        """Bypassing case sensitivity
        
        """
        return self._name.replace("W","w").replace("Z","z" )
    
    @property
    def decay(self):
        """Retrieves the description of this decay as LaTex-strings.
        UNDER CONSTRUCTION!
        """
        # ### FIX ME: This is not done yet -> should use already existing code!  
        if prettyDescriptions.decay.has_key(self._name):
            logger.info('found decay for topology %s' %self._name)
            return prettyDescriptions.decay[self._name]
        if prettyDescriptions.decay.has_key(self._slackExpTopologyName()):
            logger.info('found decay for topology %s with \
            slack name %s' %(self._name, self._slackExpTopologyName()))
            return prettyDescriptions.decay[self._slackExpTopologyName()]
        logger.warning('no decay found for topology %s' %self._name)
        return None
        
    #def getPrettyName       # particles resp. productionmode
    #def treatMasssplitting
    #def setAnalyses
    #def refreshAnalyses
    
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
                
            

