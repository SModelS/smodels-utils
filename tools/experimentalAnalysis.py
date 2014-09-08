#!/usr/bin/env python

"""
.. module:: experimentalAnalysis
   :synopsis: Holds the ExpAnalysis object retrieved from smodels-database 
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
        
    def __init__(self, analysis, infotxt, run, smsroot, smspy):
        self._name = analysis
        self._infotxt = infotxt
        self._run = run
        self._smsroot = smsroot
        self._smspy = smspy
        self._verbosity = 'error'

    def __str__(self ):
        ret = "%s [%s, %s] <<%s>>" % \
             (self.name, self.experiment, self.run, ", ".join(self.topologies))
        return ret
     
    @property
    def verbosity(self):
        """Tells the level the logger is set to.
        
        """
        return self._verbosity
        
    @verbosity.setter
    def verbosity(self, level):
        """Set the logger to specified level.
        
        """
        level = self._validateLevel(level)
        self._verbosity = level
        self._setLogLevel(level)
    
    @property
    def lumi(self):
        return self._parseMetaInfo('lumi')

    @property
    def publishedData(self):
        return self._parseMetaInfo('publisheddata')
    
    @property
    def extendedTopologies(self):
        return self._extendedTopologies
    
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
        """Checks if there are any constraints for this analysis.
        
        """
        
        if self._parseInfo('constraint'): return True
        return False
        
    @property
    def constraints(self):
        """Retrieves all the constraints stored in the info.txt file.
        
        """
        return self._parseInfo('constraint')
     
    @property
    def hasConditions(self):
        """Checks is there are any conditions for this analysis.
        
        """
        if self._parseInfo('condition'): return True
        return False
        
        
    @property
    def conditions(self):
        """Retrieves all the conditions stored in the info.txt file.
        
        """
        return self._parseInfo('condition')
        
    @property    
    def private(self):
        """States if the analysis is private (True) or public (False).

        """
        t = self._parseMetaInfo('private')
        if t == None: 
            return False
        t=t.lower()
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
        """Retrieves the axes information stored in the axes-labeled line of 
        info.txt.
        :return: {'topology': [{'mx': 'x-axis', 'my': 'y-axis', 
        'mz': ('mass condition', value)}]}
       
    
        """
        if self.hasAxes:
            return self._axes
        return None
    
    @property    
    def isChecked(self):
        if self._parseMetaInfo('checked'): return True
        return False
        
    @property        
    def checked(self):
        return self._parseMetaInfo('checked')
        
    @property        
    def supersedes(self):
        return self._parseMetaInfo('supersedes')
        
    @property        
    def superseded(self):
        return self._parseMetaInfo('superseded_by')
    
    @property
    def isPublished(self):
        if self._parseMetaInfo('arxiv') or self._parseMetaInfo('publication'):
            return True
        return False
    
    @property    
    def name(self):
        return self._name
    
    @property    
    def sqrts(self):
        return self._sqrts
    
    @property    
    def run(self):
        return self._run
        
    @property
    def topologies(self):
        """Retrieves all the topologies this analysis has results for as strings.
        
        """
        return self._getInfoProperty('topologies')
    
    @property
    def expTopologies(self):
        """Retrieves all the experimental topology objects this analysis has 
        results for.
        
        """
        if self.topologies:
            topos = [ExpTopology(t) for t in self.topologies]
            return topos
        return None
        
    @property    
    def extendedTopologies(self):
        """Retrieves all the topologies with their particular extensions 
        (referring to possible mass conditions) this analysis has results 
        for as strings.
        
        """
        return self._extendedTopologies
        
    @property
    def exclusions(self):
        """Retrieves all the exclusion values stored in the info.txt file.
        
        """
        return self._getInfoProperty('exclusions')
    
    @property    
    def hasROOT(self):
        if self._smsroot: return True
        return False
    
    @property    
    def hasPY(self):
        if self._smspy: return True
        return False
    
    @property    
    def ROOT(self):
        return self._smsroot
        
    @property    
    def PY(self):
        return self._smspy
    
    def _validateLevel(self, level):
        """Validates given level for pythons logger module.
        
        """
        if not level.lower() in ['debug', 'info', 'warning', 'error']:
            logger.error('No valid level for verbosity: %s! Browser will \
            use default setting!' %level)
            return 'error'
        return level.lower()
            
    def _setLogLevel(self, level = 'error'):
        if level == 'debug':
            logger.setLevel(level=logging.DEBUG)
        if level == 'info':
            logger.setLevel(level=logging.INFO)
        if level == 'warning':
            logger.setLevel(level=logging.WARNING)
        if level == 'error':
            pass
    
    def _getInfoProperty(self, requested):
        """Retrieves the requested property of the given info.txt object.
        
        """
        return getattr(self._infotxt, requested)
    
    def _parseMetaInfo(self, requested):
        metaInf = self._getInfoProperty('metaInfo')
        if not requested in metaInf:
            logger.warning('Requested keyword %s could not be found for %s!' \
            %(requested, self._name))
            return None
        return metaInf[requested]
        
    def _parseInfo(self, requested):
        inf = self._getInfoProperty('info')
        content = [line for line in inf if requested in line]
        if not content:
            logger.warning('Requested lines %s could not be found for %s!' \
            %(requested, self._name))
            return None
        content = [line.split(':')[1].strip() for line in content]
        return content
    
    @property
    def _axes(self):
        """
        Creates the axes dictionary from the infotxt object's axes method.
        
        """
        axesDict = {}
        axes = self._getInfoProperty('axes')
        for topo in axes:
            axesDict[topo] = []
            for a in axes[topo]:
                axe = {key: a[key] for key in a if key != 'extension'} 
                axesDict[topo].append(axe)
        return axesDict        
    
    @property
    def _extendedTopologies(self):
        """Creates all the extended topologies by concatenating the name of
        the topology and possible extensions and feeds them into a dictionary.
        
        """
        extTopos = {}
        extensions = self._getInfoProperty('extensions')
        for topo in self.topologies:
            extTopos[topo] = []
            if not extensions[topo]:
                extTopos[topo].append(topo)
                continue
            for ext in extensions[topo]:
                extTopos[topo].append(topo + ext)
        return extTopos        
    
    @property
    def _sqrts(self):
        s = self._parseMetaInfo('sqrts')
        try:
            return float(s)
        except ValueError:
            try:
                return float(s.split()[0])
            except TypeError:
                if '8' in s: return 8.0
                if '7' in s: return 7.0
                if not s: return None
        
    
        
    #def getRestOfInfo => contact, arxiv, publisheddata ### check something missing?
