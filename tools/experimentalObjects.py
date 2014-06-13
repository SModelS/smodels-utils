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
		
	def __init__(self, analysis, path):
		self._name = analysis
		self._info = self._readInfo()
		self._run = databaseBrowser.allRuns(analysis)
		self._path = path
	
	def _readInfo(self):
		"""Reads the whole info.txt file, returns a dictionary.
	
		"""
		infoFile = open(path)
		_content = infoFile.readlines()
		infoFile.close()
		logger.debug('Found info.txt for run %s and analysis %s.' %(run, analysis))
		_infoDict = {line.split(':', 1)[0].strip(): line.split(':', 1)[1].strip() for line in _content }
		return _infoDict
		
	def _parsInfo(self, requested):
		if not requested in self._info:
			logger.warning('Requested keyword %s could not be found for %s!' %(requested, self._name))
			return None
		return self._info[requested][0]
		
	@property
	def lumi(self):
		return self._parsInfo('lumi')
		
	@property
	def sqrts(self):
		return self._parsInfo('sqrts')
		
	@property	
	def pas(self):
		return self._parsInfo('pas')
		
	@property	
	def url(self):
		return self._parsInfo('URL')
		
	@property	
	def experiment(self):
		if 'ATALS' in self._run:
			return 'ATLAS'
		return 'CMS' 
		
	@property	
	def comment(self):
		return self._parsInfo('comment')
	
	@property
	def prettyName(self):
		return self._parsInfo('prettyname')
		
	@property	
	def hasConstraints(self):
		"""Checks if there are any constraints for this Analysis.
		
		"""
		if self._parsInfo('constraint'): return True
		return False

	@property	
	def private(self):
		"""States if the analysis is private (1) or public (0).
		### FIX ME: change to True and False?
		
		"""
		return self._parsInfo('private')
	
	@property	
	def hasArxiv(self):
		if self._parsInfo('arxiv'): return True
		return False
		
	@property		
	def arxiv(self):
		return self._parsInfo('arxiv')
	
	@property	
	def isPublication(self):
		if self._parsInfo('publication'): return True
		return False

	@property	
	def publication(self):
		return self._parsInfo('publication')
	
	@property
	def hasAxes(self):
		if self._parsInfo('axes'): return True
		return False
		
	@property
	def axes(self):
		"""Retrieves the information stored in the axes-labeled line of info.txt.
	
		"""
		return self._parsInfo('axes')
	
	@property	
	def isChecked(self):
		if self._parsInfo('checked'): return True
		return False
		
	@property		
	def checked(self):
		return self._parsInfo('checked')
	
	@property
	def isPublished(self):
		if self._parsInfo('arxiv') or self._parsInfo('publication'):
			return True
		return False
	
	@property	
	def name(self):
		return self._name
	
	@property	
	def run(self):
		return self._run
		
	
	
	# ### FIX ME: below
	def getTopologyNames(self):
		return getAllTopologies(self._name, self._run)
		
	def getExpTopologies(self):
		if self.getTopologyNames():
			topos = [ExpTopology(t) for t in self.getExpTopologyNames()]
			return topos
		return None
		
	def getExtendedTopologyNames(self):
		return getExtendedTopologies(self._name, self._run)
		
	#def getRestOfInfo => contact, arxiv, publisheddata ### check something missing?