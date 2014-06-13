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
		can handle specified run ### FIX ME: handeling of runs is not very elegant at the moment => think of a better way!

	"""
		
	def __init__(self, analysis):
		self._name = analysis
		self._info = self._readInfo(run, self._name)
		self._run = databaseBrowser.allRuns(analysis)
		
	def _parsInfo(self, requested):
		content = [string for string in self._info if requested in string]
		if content:
			logger.info('found %s: %s' %(requested,content[0].split(' ')[1]))
			return content[0].split(' ')[1].strip()
	
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
		''' ### FIX ME: this is not very nice
		
		'''
		if getInfo(run = self._run, analysis = self._name, requested = 'comment'):
			com = getInfo(run = self._run, analysis = self._name, requested = 'comment')[0].split(':')[1]
			return com.strip() 
	
	@property
	def prettyName(self):
		return self._parsInfo('prettyname')
		
	def checkConstraints(self):
		"""Checks if there are any constraints for this Analysis.
		
		"""
		if self._parsInfo('constraint'): return True
		return False

	@property	
	def private(self):
		"""States if the analysis is private (1) or public (0).
		### FIX ME: chenge to True and False?
		
		"""
		_priv = self._parsInfo('private')
			if _priv:
				_priv = _priv[0].split()[-1].strip()
		return _priv
	
	@property	
	def checkArxiv(self):
		if self._parsInfo('arxiv'): return True
		return False
		
	@property		
	def arxiv(self):
		if self._parsInfo('arxiv'): return self._parsInfo('arxiv')
		return None
	
	@property	
	def checkPublication(self):
		if self._parsInfo('publication'): return True
		return False

	@property	
	def publication(self):
		if self._parsInfo('publication'): return self._parsInfo('publication')
		return None	
		
	def checkAxes(self):
		if self._parsInfo('axes'): return True
		return False
		
	def getAxes(self):
		if self.checkAxes() == True:
			return preprocessAxes(getInfo(self._run, self._name, 'axes'))
		return None
	
	@property	
	def checkChecked(self):
		if self._parsInfo('checked'): return True
		return False
		
	@property		
	def checked(self):
		if self.checkChecked() == True:
			infoLine = getInfo(self._run, self._name, 'checked')
			infoLine = infoLine[0].split(',')
			infoLine[0] = infoLine[0].replace('checked: ','')
			infoLine = [ch.strip() for ch in infoLine]
			return infoLine
		return None
	
	@property	
	def name(self):
		return self._name
	
	@property	
	def run(self):
		return self._run
	
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