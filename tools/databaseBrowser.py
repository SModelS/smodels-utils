#!/usr/bin/env python

"""
.. module:: databaseBrowser
   :synopsis: Centralized facility to access smodels-database 
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

allruns = ["8TeV", "ATLAS8TeV", "RPV8", "2012", "RPV7", "2011"]
artifacts = ['old', 'bad', 'missing', 'TODO', 'readme'] 
currentRun = '8TeV'

base = '/afs/hephy.at/user/w/walten/public/sms/'

def validateBase(Base):
	"""Validates the base directory to locate the database. Exits the script if something is wrong with the path
	
	"""
	#if not Base: Base = "/afs/hephy.at/user/w/walten/public/sms/"
	logger.debug('Try to set the path for the database to: %s' %Base)
	if not os.path.exists(Base):
		logger.error('%s is no valid Path!' %Base)
		sys.exit()
	if not [run for run in os.listdir(Base) if run in allruns]:
		logger.error('There is no valid database at %s' %Base)
		sys.exit()
	logger.info('Set base to %s' %Base)
	return Base

# ### FIX ME: should I use these? Improves performance? 
#allTopologies = []
#allAnalyses = []
#allPairs = []

class ExpAnalysis(object):
	
	"""contains all analysis-specific information (e.g. PAS, lumi, publication-url, ...)
		can handle specified run ### FIX ME: handeling of runs is not very elegant at the moment => think of a better way!

	"""
	def __new__(self, analysis, run = None):
		if not run:
			run = getAllRuns(analysis)
		info = readInfo(run, analysis)
		if info:
			logger.info('found info.txt in %s-%s.' %(run, analysis))
			return object.__new__(self)
		logger.error('Cannot build ExpAnalysis %s for run %s.' %(analysis, run))
		
	def __init__(self, analysis, run = None):
		self._name = analysis
		self._info = readInfo(run, self._name)
		if not run:
			run = getAllRuns(analysis)
		self._run = run
		
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
	
class Result (object):
	"""Contains all pair-specific informations and objects (e.g. exclusionlines, histograms, ...).

	"""
	# Best to call through function linkResults()!
	
	def __init__ (self, pair):
		self._topo = pair[2]
		self._ana = pair[1]
		self._run = pair[0]
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
	
#def loadAnalysis

#def loadTopology

def getDatabase():
	"""Creates a dictionary containing all runs as keys and all subdirectories resp. analyses as entries.
	
	"""
	
	data = {}
	Base = validateBase(base)
	for r in allruns:
		if not os.path.exists('%s/%s' % (Base, r)):
			logger.warning('Using an uncomplete version of the database!')
			continue
		data[r] = os.listdir('%s/%s' % (Base, r))
		data[r] = [directory for directory in data[r] if not '.' in directory]
		# exclude all files (e.g. create.sh) from list of directories 
		data[r] = [directory for directory in data[r] if not directory in artifacts]
		# exclude every file and directory specified by list of artifacts
	return data
	
def checkResults(run = None, analysis = None, requested = 'info.txt'):
	"""Checks if results are available in form of info.txt, sms.root and sms.py.
	
	"""
	Base = validateBase(base)
	
	if run and checkRun(run) == False:
		return None
		
	if not analysis:
		logger.error('no results without analysis!')
		return None
		
	if not run:
		run = getAllRuns(analysis)
		
	path = Base + run + '/' + analysis + '/' + requested
	logger.debug('check path: %s' %path)
	if not os.path.exists(path):
		logger.warning('for run %s and analyses %s no %s was found' %(run, analysis, requested))
		return None
		
	return path
	
def readInfo(run = None, analysis = None):
	"""Reads the whole info.txt file (if existing) for given run-analysis-pair
	
	"""
	
	if run and checkRun(run) == False:
		return None

	if not analysis: return None
	
	if not run: run = getAllRuns(analysis)
	
	path = checkResults(run, analysis)
	if path:
		infoFile = open(path)
		content = infoFile.readlines()
		infoFile.close()
		logger.debug('found info.txt for run %s and analysis %s' %(run, analysis))
		return content 
		
def getInfo(run = None, analysis = None, requested = 'constraint'):
	"""Extracts information from info.txt file, returns a list containing all lines the requested information is stored in.
	
	"""
	# to get all topologies without any additional information like mass-splitting, the best way is to read the constraint-lines!
	
	if analysis and not run: run = getAllRuns(analysis)
	
	if not checkResults(run, analysis): return None
	
	content = readInfo(run, analysis)
	content = [string.strip() for string in content if requested in string]
	if not content == []: return content
	logger.info('requested keyword %s could not be found for %s-%s!' %(requested, run, analysis))
	return None
	
def preprocessAxes(infoLine):
	"""To handle the information stored in the axes-labeled line of info.txt, this line has to be preprocessed.
	
	"""
	infoLine = infoLine[0].split(',')
	infoLine[0] = infoLine[0].replace('axes: ','')
	infoLine = [ax.strip() for ax in infoLine]
	logger.debug('axes- information: %s' %infoLine)
	return infoLine

def getAllRuns(analysis = None, topology = None, current = True):
	"""Retrieves all runs a given analysis or topology or analysis-topology pair is available for. Returns a list containing all runs or just a string when current = True 
	### FIX ME check if current still works resp. do I have to sort hits??!!!  ### FIX ME: maybe drop the topology-option?
	
	"""
	database = getDatabase()
	
	if not analysis:
		return database.keys()
		
	runs = [key for key in database if analysis in database[key]]
				
	if runs == []:
		logger.error('no valid analysis %s' %analysis)
		return None
	
	if current == True:
		logger.info('for %s collected runs: %s' %(analysis,runs))
		logger.info('returning: %s' %runs[0])
		return runs[0]
		
	if current == False:
		return runs
		
def checkRun(run):
	"""Verifies if given run is valid. Returns True if run is found in database.
	
	"""
	if not run in getDatabase().keys():
		logger.error('no valid run %s' %run)
		return False
		
	return True
	
def getAllAnalyses(run = None, topology = None):
	"""Retrieves all analyses existing for given run or run-topology-pair
	
	"""
	database = getDatabase()
	analyses = []
	
	if run and checkRun(run) == False:
		return None
		
	if not run:
		analyses.append(database[key] for key in getAllRuns(current = False))
		analyses = [ana for anas in analyses for ana in anas]
		
	if not topology:
		logger.info('found %s analyses for %s' %(len(database[run]), run))
		return database[run]

	for a in database[run]:
		topologies = getAllTopologies(a, run)
		if topologies and topology in topologies:
			logger.info('found %s in %s-%s' %(topology,run,a))
			analyses.append(a)
		
	if analyses == []:
		logger.error('%s is no valid topology for given run %s' %(topology, run))
		return None
		
	return analyses

def getAllTopologies(analysis = None, run = None):
	"""Retrieves all topologies existing for given run or analysis-run-pair
	### FIX ME: maybe all topologies with given characteristics like existing exclusionlines?
	
	"""
	topos = []
	runs = []
	analyses = []
	nono = False
	
	if run and checkRun(run) == False:
		return None
		
	if analysis and not run:
		analyses.append(analysis)
		runs.append(getAllRuns(analysis))

	if run and not analysis:
		runs.append(run)
		analyses = getAllAnalyses(run)
			
	if run and analysis:
		runs.append(run)
		analyses.append(analysis)
		
	if not run and not analysis:
		runs = getAllRuns()
		nono = True
					
	logger.debug('searching topologies for runs %s and analyses %s' %(runs,analyses))
	for r in runs:
		if nono == True:
			analyses = getAllAnalyses(r)
			logger.info('no analysis was given, therefore took all analyses for run %s: %s' %(r, analyses))
		for a in analyses:
			const = getInfo(r, a)
			unconst = getInfo(r, a, requested = 'unconstraint')
			if not const: content = unconst
			if not unconst: content = const
			if const and unconst: content = const + unconst
			if not content: continue
			for c in content:
				if topos.count(c.split(' ')[1]) == 0:
					topos.append(c.split(' ')[1])
				
	if topos == []:
		logger.info('for runs %s and analyses %s no topology could be found' %(runs, analyses))
		return None
		
	return topos
		
def getExtendedTopologies(analysis, run, topology = None):
	"""Checks if the topologies for one given analysis-run are tainted with any kind of mass requirements and returns dictionary with extended topologies. Can be reduced to given topology (returns list).
	### FIX ME: maybe use in class Result only?
	
	"""
	topos = {}
	logger.debug('got analysis: %s and run %s!' %(analysis, run))
	if not getInfo(run, analysis, 'axes'):
		logger.info('No additional information about axes was found for %s-%s!' %(run, analysis))
		if not getAllTopologies(analysis, run): return None
		for t in getAllTopologies(analysis, run):
			topos[t]=[t]
		if not topology: return topos
		if topos.has_key(topology): return topos[topology]
		logger.warning('for %s-%s there is no topology %s' %(run, analysis, topology))
		return None
	
	infoLine = getInfo(run, analysis, 'axes')
	axes = preprocessAxes(infoLine)
	logger.info('for %s-%s there is additional mass information!' %(run, analysis)) 
	
	for ax in axes:
		logger.debug('axesline is:%s' %ax)
		massdic = massProportions(ax)
		topo = massdic.keys()[0]
		topos[topo] = []

		for case in massdic[topo]:
			if len(case) == 2: topos[topo].append(topo)
			if len(case) == 3:
				try:
					x = int(case[2])
					topos[topo].append(topo + case[2])
				except ValueError:
					if 'D' in case[2]:
						D = case[2].split('=')[-1].strip()
						topos[topo].append(topo + 'D' + D)
					elif 'LSP' or 'x' or 'C' or 'M' in case[2]: topos[topo].append(topo + case[2])
			if len(case) > 3:
				logger.info('topology is: %s => more then one additional condition is too much at the moment' %topo)
				continue
	
	if topos == {'':[]}:
		logger.warning('Something is wrong with the axes line in the info.txt for %s-%s!' %(run, analysis))
		return None
	if not topology: return topos
	if topos.has_key(topology): return topos[topology]
	logger.warning('for %s-%s there is no topology %s' %(run, analysis, topology))
	return None
	
def massProportions(axesLine):
	"""Reads out all the conditions for intermediate masses (e.g. masssplitting-xvalues 025, 050, 075) implicitly stored in axes-lines of info.txt and returns the information as dictionary.
	
	"""
	massdic = {}
	topo = axesLine.split(' ')[0].replace(':', '').strip()
	massdic[topo] = axesLine.replace(topo + ':', '').split('-')
	massdic[topo] = [c.strip() for c in massdic[topo]]
	logger.info('for %s there are %s different cases of mass proportions' %(topo, len(massdic[topo])))
	massdic[topo]=[c.split(' ') for c in massdic[topo]]
	return massdic
	
def linkResult(analysis, topology, current = True):
	"""Inter couples analysis and topology creating a specified pair. Either for all runs (returns dictionary) or for first run the given analysis appears for in the database (returns list)
	
	"""
	if current == False:
		runs = getAllRuns(analysis, current = False)
		pair = {}
		if not runs: return None
		logger.debug('try to link pair %s-%s for all available runs!' %(analysis, topology))
		for r in runs:
			topologies = getAllTopologies(analysis, run)
			if topologies and topology in topologies:
				pair[r]=[analysis, topology]
				logger.debug('found pair %s-%s for run %s!' %(analysis, topology, run))
		return pair
	
	run = getAllRuns(analysis)
	if not run: return None
	topologies = getAllTopologies(analysis, run)
	if not topologies:
		logger.info('there are no topologies for %s-%s' %(run, analysis))
		return None
		
	logger.debug('try to link pair %s-%s for run %s!' %(analysis, topology, run))
	if topologies and topology in topologies:
		return [run, analysis, topology]

		
	# ### Do the rest below!!! ### 
	
class databaseBrowser(object):
	
	"""Browses the database, exits if given path does not point to a valid smodels-database. Browser can be restricted to specified run or experiment.
	### FIX ME: docstring???
	### FIX ME: maybe drop the set run option?
	### FIX ME: be aware of using some functions from the outside with specified runs or analysis, when inside these remain unset!
	
	"""
	def __init__(self, base = '/afs/hephy.at/user/w/walten/public/sms/'):
		self._base = self._validateBase(base)
		self._allruns = ["8TeV", "ATLAS8TeV", "RPV8", "2012", "RPV7", "2011"]
		self._artifacts = ['old', 'bad', 'missing', 'TODO', 'readme']
		self._experiment = None
		self._database = self.getDatabase()
		self._run = None
		#self._analysis = None
		#self._topology = None
		
	@property
	def base(self):
		"""This is the path to the base directory where to find the database.
		
		"""
		return self._base
		
	def _validateBase(self, path):
		"""Validates the base directory to locate the database. Exits the script if something is wrong with the path.
	
		"""
		logger.debug('Try to set the path for the database to: %s' %path)
		if not os.path.exists(path):
			logger.error('%s is no valid path!' %path)
			sys.exit()
		if not [run for run in os.listdir(path) if run in self.allruns]:
			logger.error('There is no valid database at %s' %path)
			sys.exit()
		logger.info('Set base to %s' %path)
		return path
		
	@property
	def experiment(self):
		"""Restricts the browser to either CMS or ATLAS.
		
		"""
		return self._experiment
		
	@experiment.setter
	def experiment(self, detector):
		self._experiment = self._validateExperiment(detector)
		
	def _validateExperiment(self, detector):
		"""Validates the given experiment. Exits the script if the given experiment is unknown.
		### FIX ME: maybe better not exit the script, but set experiment to default?
		
		"""
		if not detector in ['CMS', 'ATLAS']:
			logger.error('%s is no valid experiment!' %detector)
			sys.exit()
		logger.info('Focusing on experiment %s.' %detector)
		return detector

	def getDatabase(self):
		"""Creates a dictionary containing all runs as keys and all subdirectories resp. analyses as entries.
	
		"""
		data = {}
		_allruns = self.allruns
		if self._experiment == 'ATLAS':
			_allruns = [r for r in _allruns if 'ATLAS' in r]
		if self._experiment == 'CMS':
			_allruns = [r for r in _allruns if not 'ATLAS' in r]
		for r in _allruns:
			if not os.path.exists('%s/%s' % (self._base, r)):
				logger.warning('Using an incomplete version of the database! Run %s is missing' %r)
				continue
			data[r] = os.listdir('%s/%s' % (self._base, r))
			data[r] = [directory for directory in data[r] if not '.' in directory]
			# exclude all files (e.g. create.sh) from list of directories 
			data[r] = [directory for directory in data[r] if not directory in self.artifacts]
			# exclude every file and directory specified by list of artifacts
		return data
		
	@property
	def run(self):
		"""Restricts the Browser to one specified run.
		
		"""
		return self._run
		
	@run.setter
	def run(self, consideredRun):
		self._run = self._validateRun(consideredRun)
		
	def _validateRun(self, consideredRun):
		"""Validates the given run. Exits the script if the given run is unknown.
		### FIX ME: maybe better not exit the script, but set run to default?
		
		"""
		if not consideredRun in self._database.keys():
			logger.error('%s is no valid run!' %consideredRun)
			sys.exit()
		logger.info('Restricted to run %s.' %consideredRun)
		return consideredRun
		
	#@property
	#def analysis(self):
		#"""Restricts the Browser to one specified analysis.
		
		#"""
		#return self._analysis
		
	#@analysis.setter
	#def analysis(self, consideredAnalysis):
		#self._analysis = self._validateAnalysis(consideredAnalysis)
		
	def _validateAnalysis(self, consideredAnalysis):
		"""Validates the given analysis. Exits the script if the given analysis is unknown. Builds the Analysis-object if value given is just a string.
		### FIX ME: maybe better not exit the script, but set analysis to default?
		
		"""
		if isinstance(consideredAnalysis, ExpAnalysis):
			return consideredAnalysis
			
		runs = [key for key in self._database if consideredAnalysis in database[key]]
		if not runs:
			logger.error('%s is no valid analysis!' %consideredAnalysis)
			sys.exit()
		logger.info('Restricted to analysis %s.' %consideredAnalysis)
		return ExpAnalysis(consideredAnalysis)
		
	#@property
	#def topology(self):
		#"""Restricts the Browser to one specified topology.
		
		#"""
		#return self._topology
		
	#@topology.setter
	#def topology(self, consideredTopology):
		#self._topology = self._validateTopology(consideredTopology)
		
	def _validateTopology(self, consideredTopology):
		"""Validates the given topology. Exits the script if the given topology is unknown. Builds the Topology-object if value given is just a string.
		### FIX ME: maybe better not exit the script, but set topology to default?
		
		"""
		if isinstance(consideredTopology, ExpTopology):
			return consideredTopology
			
		runs = [key for key in self._database if consideredTopology in database[key]]
		if not runs:
			logger.error('%s is no valid topology!' %consideredTopology)
			sys.exit()
		logger.info('Restricted to topology %s.' %consideredTopology)
		return ExpTopology(consideredTopology)
	
	@property
	def allRuns(self, analysis = None, topology = None):
	"""Retrieves all runs a given analysis or topology or analysis-topology pair is available for. Returns a list containing all runs or just a string when analysis is given 
	### FIX ME: maybe return only list?
	
	"""
	
	if not analysis and not topology:
		return self._database.keys()
	
	if self._run:
		logger.warning('Cannot get all runs because browser is restricted to %s!' %self._run)
		return self._run
	
	if self._experiment:
		logger.warning('Browser is restricted to experiment %s' %self._experiment)
		
	if analysis:
		return _validateAnalysis(analysis).run
		
	if topology and not analysis:
		runs = [key for key in self._database if _validateTopology(topology).analysesNames in self._database[key]]
	return runs
	
	# ### FIX ME: obsolete by now?
	#if current == True:
		#logger.debug('for %s collected runs: %s' %(self._analysis, runs))
		#logger.debug('returning: %s' %runs[0])
		#return runs[0]
		
	#if current == False:
		#return runs
	@property
	def allAnalyses(self, run = None, topology = None):
	"""Retrieves all analyses or all analyses existing for given run or run-topology-pair
	
	"""
	
	_analyses = []
		
	if self._run:
		logger.warnig('Browser is restricted to run %s!' %self._run)
		
	if not self._run and not run:
		_analyses.append(self._database[key] for key in self.allRuns())
		_analyses = [ana for anas in _analyses for ana in anas]
		
	if not topology and self._run and not run:
		logger.info('found %s analyses for %s' %(len(self._database[self._run]), self._run))
		return self._database[self._run]
		
	if not topology and not self._run and run:
		logger.info('found %s analyses for %s' %(len(self._database[run]), run))
		return self._database[self._run]

		
	for a in self._database[self._run]:
		_topologies = self.allTopologies(a)
		if _topologies and self._topology in _topologies:
			logger.debug('found %s in %s-%s' %(self._topology, self._run, a))
			_analyses.append(a)
		
	if not _analyses:
		logger.warning('%s is no valid topology for given run %s' %(self._topology, self._run))
		return None
		
	return _analyses
	
#	@property
	def allTopologies(self):
		"""Retrieves all topologies existing for given run or analysis-run-pair
	### FIX ME: maybe all topologies with given characteristics like existing exclusionlines?
	
		"""
	_topos = []
	_runs = []
	_analyses = []
	nono = False
	
	if self._analysis and not self._run:
		analyses.append(analysis)
		runs.append(self.allRuns())

	if run and not analysis:
		runs.append(run)
		analyses = getAllAnalyses(run)
			
	if run and analysis:
		runs.append(run)
		analyses.append(analysis)
		
	if not run and not analysis:
		runs = getAllRuns()
		nono = True
					
	logger.debug('searching topologies for runs %s and analyses %s' %(runs,analyses))
	for r in runs:
		if nono == True:
			analyses = getAllAnalyses(r)
			logger.info('no analysis was given, therefore took all analyses for run %s: %s' %(r, analyses))
		for a in analyses:
			const = getInfo(r, a)
			unconst = getInfo(r, a, requested = 'unconstraint')
			if not const: content = unconst
			if not unconst: content = const
			if const and unconst: content = const + unconst
			if not content: continue
			for c in content:
				if topos.count(c.split(' ')[1]) == 0:
					topos.append(c.split(' ')[1])
				
	if topos == []:
		logger.info('for runs %s and analyses %s no topology could be found' %(runs, analyses))
		return None
		
	return topos