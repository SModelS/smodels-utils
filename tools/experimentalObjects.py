#!/usr/bin/env python

"""
.. module:: experimentalObjects
   :synopsis: Holds all the experimental objects retrieved from smodels-database 
   in order to produce summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Wolfgang Magerl <wolfgang.magerl@gmail.com>

"""	

import ROOT
import logging, os, types
import dictionaries
import setPath
import sys
import databaseBrowser

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

def setLogLevel(level = 'error'):
	if level == 'debug':
		logger.setLevel(level=logging.DEBUG)
	if level == 'info':
		logger.setLevel(level=logging.INFO)
	if level == 'warning':
		logger.setLevel(level=logging.WARNING)
	if level == 'error':
		pass
	
class ExpAnalysis(object):
	
	"""contains all analysis-specific information (e.g. PAS, lumi, publication-url, ...)
	
	"""
		
	def __init__(self, analysis, infotxt, run):
		self._name = analysis
		self._info = infotxt.info
		self._metaInfo = infotxt.metaInfo
		self._run = run
		
	def _parsMetaInfo(self, requested):
		if not requested in self._metaInfo:
			logger.warning('Requested keyword %s could not be found for %s!' %(requested, self._name))
			return None
		return self._metaInfo[requested][0]
		
	def _parsInfo(self, requested):
		content = [line for line in self._info if requested in line]
		if not content:
			logger.warning('Requested lines %s could not be found for %s!' %(requested, self._name))
			return None
		content = [line.split(':')[1].strip() for line in content]
		return content
	
	@property
	def lumi(self):
		return self._parsMetaInfo('lumi')
		
	@property
	def sqrts(self):
		return self._parsMetaInfo('sqrts')
		
	@property
	def pas(self):
		return self._parsMetaInfo('pas')
		
	@property	
	def url(self):
		return self._parsMetaInfo('URL')
		
	@property	
	def experiment(self):
		if 'ATALS' in self._run:
			return 'ATLAS'
		return 'CMS' 
		
	@property	
	def comment(self):
		return self._parsMetaInfo('comment')
	
	@property
	def prettyName(self):
		return self._parsMetaInfo('prettyname')
		
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
		"""States if the analysis is private (1) or public (0).
		### FIX ME: change to True and False?
		
		"""
		return self._parsMetaInfo('private')
	
	@property	
	def hasArxiv(self):
		if self._parsMetaInfo('arxiv'): return True
		return False
		
	@property		
	def arxiv(self):
		return self._parsMetaInfo('arxiv')
	
	@property	
	def hasPublication(self):
		if self._parsMetaInfo('publication'): return True
		return False

	@property	
	def publication(self):
		return self._parsMetaInfo('publication')
	
	@property
	def hasAxes(self):
		if self._parsMetaInfo('axes'): return True
		return False
		
	@property
	def axes(self):
		"""Retrieves the information stored in the axes-labeled line of info.txt.
	
		"""
		return self._parsMetaInfo('axes')
	
	@property	
	def isChecked(self):
		if self._parsMetaInfo('checked'): return True
		return False
		
	@property		
	def checked(self):
		return self._parsMetaInfo('checked')
	
	@property
	def isPublished(self):
		if self._parsMetaInfo('arxiv') or self._parsMetaInfo('publication'):
			return True
		return False
	
	@property	
	def name(self):
		return self._name
	
	@property	
	def run(self):
		return self._run
		
	@property
	def allTopologyNames(self):
		"""Retrieves all the topologies this analysis has results for as strings.
		
		"""
		return databaseBrowser.Browser.allTopologies(self._run, self._name)
		
	def getExpTopologies(self):
		if self.getTopologyNames():
			topos = [ExpTopology(t) for t in self.getExpTopologyNames()]
			return topos
		return None
		
	def getExtendedTopologyNames(self):
		return getExtendedTopologies(self._name, self._run)
		
	#def getRestOfInfo => contact, arxiv, publisheddata ### check something missing?
# ### FIX ME ExpTopoObject ###
class ExpTopology(object):
	"""contains all topology-specific information (e.g. particles resp. productionmode, ...)
	### masssplitting? => move to pair object
	
	"""
	
	def __new__(self, topology):
		alltopos = getAllTopologies()
		if topology in alltopos:
			logger.info('found topology %s' %topology)
			return object.__new__(self)
		logger.error('Cannot build ExpTopology %s' %topology)
		
	def __init__ (self, topology):
		self._name = topology
		self._runs = getAllRuns()
	
	@property	
	def name(self):
		return self._name
		
	def getAnalyses(self):
		if self.getExpAnalysisNames():
			anas = [ExpAnalysis(a) for a in self.getExpAnalysisNames()]
			return anas
		return None
	@property
	def analysesNames(self, run = None):
		"""Retrieves the names (as strings) of all analyses existing for this topology. Returns a list of names for one given run, or a dictionary with runs as keys.
		
		"""
		if not run:
			anas = {}
			logger.warning('no run was given, therefore trying all available runs %s and returning dictionary!' %self._runs)
			for r in self._runs:
				if getAllAnalyses(run = r, topology = self._name):
					anas[r] = [a for a in getAllAnalyses(run = r, topology = self._name)]
			return anas
		return getAllAnalyses(run = run, topology = self._name)
	
	def _slackExpTopologyName(self):
		"""Bypassing case sensitivity
		
		"""
		return self._name.replace("W","w").replace("Z","z" )

	def getDecay(self):
		if dictionaries.decay.has_key(self._name):
			logger.info('found decay for topology %s' %self._name)
			return dictionaries.decay[self._name]
		if dictionaries.decay.has_key(self._slackExpTopologyName()):
			logger.info('found decay for topology %s with slack name %s' %(self._name, self._slackExpTopologyName()))
			return dictionaries.decay[self._slackExpTopologyName()]
		logger.warning('no decay found for topology %s' %self._name)
		return None
		
	#def getPrettyName       # particles resp. productionmode
	#def treatMasssplitting
	#def setAnalyses
	#def refreshAnalyses
	
class ExpResult (object):
	"""Contains all result-specific informations and objects (e.g. exclusionlines, histograms, ...). A result denotes a specified pair of topology and analysis.

	"""
	def __init__ (self, run, analysis, topology):
		self._topo = topology
		self._ana = analysis
		self._run = run
		
		# ### FIX ME: maybe implement Michis getExclusions - functions? Adapt to exp-objects!
		self._extendedTopos = getExtendedTopologies(self._ana, self._run, self._topo) 
		logger.info('creating pair-object for %s-%s!' %(self._ana, self._topo))
		
	def getExpAnalysis(self):
		return ExpAnalysis(self._ana, self._run)
		
	def getExpTopology(self):
		return ExpTopology(self._topo)
		
	@property
	def extendedTopologies(self):
	    return self._extendedTopos
		
	@property
	def checkedBy(self):
		"""Retrieves checked_by entry from info.txt.
		
		"""
		infoLine = self.getExpAnalysis().getChecked()
		logger.debug('got infoLine from ExpAnalysis-object: %s' %infoLine)
		if not infoLine: return None
		if 'AL' in infoLine: # ### FIX ME: this if will be obsolet when the checked flag is fixed in every info.txt
			logger.warning('there is no information about singel topologies')
			return infoLine[0]
		infoLine = [ch for ch in infoLine if self._topo in ch]
		logger.debug('first preprocessed infoLine: %s' %infoLine)
		if not infoLine:
			logger.warning('This Result is not checked!')
			return None
		infoLine = [ch.split(':') for ch in infoLine]
		logger.debug('second preprocessed infoLine: %s' %infoLine)
		infoLine = infoLine[0]
		logger.debug('return value of infoLine: %s' %infoLine)
		return infoLine[1].strip()
		
	def getExclusionLines(self):
		"""Retrieves all the exclusionlines stored in sms.root as a python dictionary.
		
		"""
		if not checkResults(self._run, self._ana, 'sms.root'): return None
		rootFile = ROOT.TFile(checkResults(self._run, self._ana, 'sms.root'))
		exclusionLines = {}
		expected = []
		observed = []
		if not self._extendedTopos: return None
		for t in self._extendedTopos:
			for sigma in ['p1', '', 'm1']:
				expected.append(rootFile.Get('expectedexclusion' + sigma + '_' + t))
				observed.append(rootFile.Get('exclusion' + sigma + '_' + t))
			exclusionLines[t + '_expected'] = expected
			exclusionLines[t + '_observed'] = observed
		return exclusionLines
	
	def selectTypeOfExclusionLine(self, expected = False, sigma = 0):
		"""Picks one specified type of exclusionline as ROOT.TGraph.
		
		"""
		allLines = self.getExclusionLines()
		logger.debug('all exclusionlines: %s' %allLines)
		if not allLines: return None
		keys = allLines.keys()
		
		if expected == True:
			keys = [k for k in keys if 'expected' in k]
		if expected == False:
			keys = [k for k in keys if 'observed' in k]
			
		exLines = allLines[keys[0]]
		exLines = [l for l in exLines if l]
		logger.debug('selected exclusionlines: %s' %exLines)
		if sigma == 0: exLines = [l for l in exLines if not 'p1' in l.GetName() and not 'm1' in l.GetName()]
		elif sigma == 1: exLines = [l for l in exLines if 'p1' in l.GetName()]
		elif sigma == -1: exLines = [l for l in exLines if 'm1' in l.GetName()]
		else:
			logger.error('no exclusionlines available for sigma = %s' % sigma)
			return None
		return exLines
		
	def selectExclusionLine(self, expected = False, sigma = 0, condition = 'xvalue', value = 050):
		"""Selects one exclusionline (out of all exclusionLines for this topology) corresponding to a specified case of mass proportions (e.g. x-value = 050, mass of LSP = 50 GeV, ...)
		### FIX ME: maybe define a standard configuration for other conditions as xvalues
		
		"""
		exLines = self.selectTypeOfExclusionLine(expected, sigma)
		if not exLines: return None
		if len(exLines) == 1:
			logger.info('there is just one exclusionline of this type!')
			return exLines[0]
			
		if not condition in ['D', 'x', 'LSP', 'C', 'M', 'xvalue']:
			logger.error('%s is no valid type of condition for intermediate masses' %condition)
			return None
			
		if condition == 'xvalue': topoextention = str(value)
		else:
			topoextention = condition + str(value)
			
		for line in exLines:
			if topoextension in line.GetName(): return line
		
	def getExclusions(self):
		"""Retrieves all exclusions stored in info.txt.
		### FIX ME maybe it's better not to do it the same way it is done for exclusionlines!
		
		"""
		exclusions = {}
		info = getInfo(self._run, self._ana, 'exclusions')
		if not info: return None
		expected = [line for line in info if 'expected' in line] 
		observed = [line for line in info if not 'expected' in line]
		if not self._extendedTopos: return None 
		for t in self._extendedTopos: 
			expected = [line.split() for line in expected]
			observed = [line.split() for line in observed]
			expected = [line for line in expected if line[1] == t]
			observed = [line for line in observed if line[1] == t]
			
			print expected
			print observed
			exclusions[t + '_expected'] = expected
			exclusions[t + '_observed'] = observed
		return exclusions
	#def getLimitHistograms
