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
        t = self._parseMetaInfo('private').lower()
        return t in [ "1", "yes", "true" ]
    
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
        if len(cats) == 0:
            logger.error('Could not get any category information for %s.' % \
                    self._name )
            return None
        if len(cats) == 1:
            return cats[0]
        
        logger.error('Unable to get consistent category for topology %s: %s' % \
                      (self._name,cats) )
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

            

