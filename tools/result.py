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
		

Base = '/afs/hephy.at/user/w/walten/public/sms/'
#Base = '../../smodels-database/'


allruns = ["8TeV", "ATLAS8TeV", "RPV8", "2012", "RPV7", "2011"]
artifacts = ['old', 'bad', 'missing', 'TODO', 'readme'] 
currentRun = '8TeV'

# ### FIX ME: should I use these? Improves performance? 
#allTopologies = []
#allAnalyses = []
#allPairs = []

class Analysis(object):
	
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
		logger.error('Cannot build Analysis %s for run %s.' %(analysis, run))
		
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
		
	def getLumi(self):
		return self._parsInfo('lumi')
		
	def getSqrts(self):
		return self._parsInfo('sqrts')
		
	def getPAS(self):
		return self._parsInfo('pas')
		
	def getURL(self):
		return self._parsInfo('URL')
		
	def getExperiment(self):
		return self._parsInfo('experiment')	
		
	def getComment(self):
		return self._parsInfo('comment')	
	
	def getPrettyName(self):
		return self._parsInfo('prettyname')
		
	def checkConstraints(self):
		"""Checks if there are any constraints for this Analysis.
		
		"""
		if self._parsInfo('constraint'): return True
		return False
		
	def checkPublic(self):
		if self._parsInfo('public'): return True
		return False
	
	def getPublic(self):
		if self._parsInfo('public'): return self._parsInfo('public')
		return None
	
	def getPrivate(self):
		return self._parsInfo('private')
	
	def checkArxiv(self):
		if self._parsInfo('arxiv'): return True
		return False
		
	def getArxiv(self):
		if self._parsInfo('arxiv'): return self._parsInfo('arxiv')
		return None
		
	def checkJournal(self):
		if self._parsInfo('journal'): return True
		return False
		
	def getJournal(self):
		if self._parsInfo('journal'): return self._parsInfo('journal')
		return None
		
	def checkPublication(self):
		if self._parsInfo('publication'): return True
		return False
	
	def getPublication(self):
		if self._parsInfo('publication'): return self._parsInfo('publication')
		return None	
		
	def checkAxes(self):
		if self._parsInfo('axes'): return True
		return False
		
	def getAxes(self):
		if self.checkAxes() == True:
			return preprocessAxes(getInfo(self._run, self._name, 'axes'))
		return None
	
	def checkChecked(self):
		if self._parsInfo('checked'): return True
		return False
		
	def getChecked(self):
		if self.checkChecked() == True:
			infoLine = getInfo(self._run, self._name, 'checked')
			infoLine = infoLine[0].split(',')
			infoLine[0] = infoLine[0].replace('checked: ','')
			infoLine = [ch.strip() for ch in infoLine]
			return infoLine
		return None
		
	def getName(self):
		return self._name
	
	def getRun(self):
		return self._run
	
	def getTopologyNames(self):
		return getAllTopologies(self._name, self._run)
		
	def getTopologies(self):
		if self.getTopologyNames():
			topos = [Topology(t) for t in self.getTopologyNames()]
			return topos
		return None
		
	def getExtendedTopologyNames(self):
		return getExtendedTopologies(self._name, self._run)
		
	#def getRestOfInfo => contact, arxiv, publisheddata ### check something missing?

class Topology(object):
	"""contains all topology-specific information (e.g. particles resp. productionmode, ...)
	### masssplitting? => move to pair object
	
	"""
	
	def __new__(self, topology):
		alltopos = getAllTopologies()
		if topology in alltopos:
			logger.info('found topology %s' %topology)
			return object.__new__(self)
		logger.error('Cannot build Topology %s' %topology)
		
	def __init__ (self, topology):
		self._name = topology
		self._runs = getAllRuns()
	
	def getName(self):
		return self._name
		
	def getAnalyses(self):
		if self.getAnalysisNames():
			anas = [Analysis(a) for a in self.getAnalysisNames()]
			return anas
		return None
	
	def getAnalysisNames(self, run = None):
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
	
	def _slackTopologyName(self):
		"""Bypassing case sensitivity
		
		"""
		return self._name.replace("W","w").replace("Z","z" )

	def getDecay(self):
		if dictionaries.decay.has_key(self._name):
			logger.info('found decay for topology %s' %self._name)
			return dictionaries.decay[self._name]
		if dictionaries.decay.has_key(self._slackTopologyName()):
			logger.info('found decay for topology %s with slack name %s' %(self._name, self._slackTopologyName()))
			return dictionaries.decay[self._slackTopologyName()]
		logger.warning('no decay found for topology %s' %self._name)
		return None
		
	#def getPrettyName       # particles resp. productionmode
	#def treatMasssplitting
	#def setAnalyses
	#def refreshAnalyses
	
class Pair (object):
	"""Contains all pair-specific informations and objects (e.g. exclusionlines, histograms, ...).
	    use ExtendedResult-objects to handle different mass assumptions for given topology and analysis
	"""
	# Best to call through function linkPairs()!
	
	def __init__ (self, pair): # should get objects
	"""set all needed private variables, especially self._extendedResults as list containing all available 
	"extended results" as ExtendedResults objects call self._setDefaultExResult
	
	"""
		self._topo = pair[2]
		self._ana = Analysis(pair[1],pair[0])
		self.extendedTopos = getExtendedTopologies(self._ana.getName(), self._ana.getRun(), self._topo) # getExtendedtopo should build and return extendedTopo-objects 
		self._extendedResults = [ExtendedResult(extTopo,self._ana) for extTopo in self.extendedTopos]
		logger.info('creating pair-object for %s-%s!' %(self._ana.getName(), self._topo))
		self._setDefaultExResult()
		
	def _setDefaultExResult(self):
	"""if there is only one extended Result this will be the default result if there more then one extended result,
	the one with mass value = 050 is set to default
	### FIX ME: rework defaultsettings 
	"""
		if self.numberOfExtendedReults == 1: 
			self._DefaultExResult = self._extendedResults[0]
			return
		self._DefaultExResult = [ExResult for ExResult in self._extendedResults if ExResult.Name()[:3] == '050']
		self._DefaultExResult = self._DefaultExResult[0]
		
	def getAnalysis(self):
		'''returns the Analysis-object linked to this Pair-object'''
		return self._ana
		
	def getTopology(self):
		'''returns the topologie-object linked to this pair-object'''
		return Topology(self._topo)
		
	@property
	def listOfextendedResults(self):
		'''returns a list containing all available extended Results as ExtendedResults-object'''
		return self._extendedResults
	    
	@property
	def numberOfExtendedReults(self):
		'''count all available extendet Results and returns the number'''
		return len(self._extendedResults)
		
	def listOfexclusionLines(self,expected = False, sigma = 0):
		'''return a list containing the exclusionlines for all extended results, available for this pair as Root.TGraph-object
		    if expected is set to False, the observed exclusionline will be returend, else the expected exclusionline will be returned
		    possible values for keywordargument "sigma" are: -1,0,1. depending on this value the exclusionlines for sigma =-1,0,1 will be returend '''
		return [ExResult.exclusionline(expected, sigma) for ExResult in self._extendedResults]
		
	def listOfexclusions(self,expected = False, typ = 0):
		'''return a list containing all exclusionValues for all extended results, available for this pair 
		    if expected is set to False, the observed values will be returend, else the expected values will be returned
		    possible values for keywordargument "typ" are: 'limit','min','max'. '''
		return [ExResult.exclusion(expected, typ) for ExResult in self._extendedResults]
	    
	def exclusionLine(self, extendetTopoName = 'default', expected = False, sigma = 0):
		'''return one exclusionline as Root.TGraph-object
		    if extendetTopoName is set to 'default', the exclusionline linked to the default extendetResult is returend
		    if exclusionline for outher extendetResult is needed, the name of the linkt extendetTopo is requested
		    if expected is set to False, the observed exclusionline will be returend, else the expected exclusionline will be returned
		    possible values for keywordargument "sigma" are: -1,0,1. depending on this value the exclusionlines for sigma =-1,0,1 will be returend '''
		return self._getSingleAttribute(extendetTopoName, expected, sigma, 'exclusionLine')
	    
	def exclusion(self, extendetTopoName = 'default',expected = False, typ ='max'):
		'''return one exclusion value 
		    if extendetTopoName is set to 'default', the value linked to the default extendetResult is returend
		    if values for outher extendetResult is needed, the name of the linkt extendetTopo is requested
		    if expected is set to False, the observed values will be returend, else the expected values will be returned
		    possible values for keywordargument "type" are: 'limit','min','max'. '''
		return self._getSingleAttribute(extendetTopoName, expected, typ, 'exclusion')
		
	def _getSingleAttribute(self, extendetTopoName, expected, argument, attribute):
		'''private methode used by the methodes "exclusionline" and "exclusion"'''
		if extendetTopoName == 'default':
			return getattr(self._DefaultExResult, attribute)(expected, argument)
		extendetResults = [ExResult for ExResult in self._extendedResults if extendetTopoName == ExResult.name]
		return getattr(extendetResults[0],attribute)(expected, argument)
		
	def checkedBy(self):
		"""Retrieves checked_by entry from info.txt.
		
		"""
		infoLine = self._ana.getChecked()
		logger.debug('got infoLine from Analysis-object: %s' %infoLine)
		if not infoLine: return None
		if 'AL' in infoLine: # ### FIX ME: this if will be obsolet when the checked flag is fixed in every info.txt
			logger.warning('there is no information about singel topologies')
			return infoLine[0]
		infoLine = [ch for ch in infoLine if self._topo in ch]
		logger.debug('first preprocessed infoLine: %s' %infoLine)
		if not infoLine:
			logger.warning('This Pair is not checked!')
			return None
		infoLine = [ch.split(':') for ch in infoLine]
		logger.debug('second preprocessed infoLine: %s' %infoLine)
		infoLine = infoLine[0]
		logger.debug('return value of infoLine: %s' %infoLine)
		return infoLine[1].strip()
		
	def selectExclusionLine(self, expected = False, sigma = 0, condition = 'xvalue', value = 050):
		"""Selects one exclusionline (out of all exclusionLines for this topology) corresponding to a specified case of mass proportions (e.g. x-value = 050, mass of LSP = 50 GeV, ...)
		### FIX ME: maybe define a standard configuration for other conditions as xvalues
		
		"""
		return self.exclusionLine(extendetTopoName = 'default', expected = expected, sigma = sigma)
		#exLines = self.selectTypeOfExclusionLine(expected, sigma)
		#if not exLines: return None
		#if len(exLines) == 1:
			#logger.info('there is just one exclusionline of this type!')
			#return exLines[0]
			
		#if not condition in ['D', 'x', 'LSP', 'C', 'M', 'xvalue']:
			#logger.error('%s is no valid type of condition for intermediate masses' %condition)
			#return None
			
		#if condition == 'xvalue': topoextention = str(value)
		#else:
			#topoextention = condition + str(value)
			
		#for line in exLines:
			#if topoextension in line.GetName(): return line

class ExtendedResult(object):
	'''Contains all specific informations linked to one extendet Result
	    a extended result is linked to one specific mass-assumption'''
	def __init__(self, name, Analysis):
		'''set all needed private variables
		    initiates the dictionaries for exclusionLines and exclusions'''
		self._name = name
		self._exclusionLines = {}
		self._exclusions = {}
		self._ana = Analysis
		
	@property
	def name(self):
	    '''return the name of the extended topology e.g.: "T.... ### Fixme'''
	    return self._name
		
	@property
	def dictOfExclusionLines(self):
		'''return a nested dictionary, containing all available exclusionlines
		{'observed':{1:Root.TGraph-object,0:Root.TGraph-object,-1:Root.TGraph-object}
		'expected':{1:Root.TGraph-object,0:Root.TGraph-object,-1:Root.TGraph-object}}'''
		if not self._exclusionLines: self._setExclusionLines
		return self._exclusionlines
		
	@property
	def dictOfExclusions(self):
		'''return a nested dictionary, containing all available exclusion-values
		{'observed':{'limit':value,'min':value,'max':value}
		'expected':{'limit':value,'min':value,'max':value}}'''
		if not self._exclusions: self._setExclusions
		return self._exclusions

	def exclusionLine(self, expected = False, sigma = 0):
		'''return the exclusionline as Root.TGraph-object
		    if expected is set to False, the observed exclusionline will be returend, else the expected exclusionline will be returned
		    possible values for keywordargument "sigma" are: -1,0,1. depending on this value the exclusionlines for sigma =-1,0,1 will be returend '''
		if not self._exclusionLines: self._setExclusionLines()
		sigmaDict = self._exclusionlines['observed']
		if expected: sigmaDict = self._exclusionLines['expected']
		return sigmaDict[sigma]
	    
	def exclusion(self,expected = False,typ ='max'):
		'''return one exclusion value 
		    if expected is set to False, the observed values will be returend, else the expected values will be returned
		    possible values for keywordargument "type" are: 'limit','min','max'. '''
		if not self._exclusions: self._setExclusions()
		typeDict = self._exclusionlines['observed']
		if expected: typeDict = self._exclusionlines['expected']
		return typeDict[typ]
	    
	def _setExclusionLines(self):
		''' private methode used by the methodes "exclusionLines" and "dictOfExclusionLines"
		    search for the exclusionlines in the sms.root-file linked to the corresponding Analysis
		    and build the a nested dictionary including all the exclusionlines'''
		path = checkResults(self._ana.getRun(), self._ana.getName(), 'sms.root')
		if not path: return None
		rootFile = ROOT.TFile(path)
		self._exclusionlines = {'observed':'exclusion','expected':'expectedexclusion'}
		for key, value in self._exclusionlines.items(): 
			sigmaDict = {1:'p1',0:'',-1:'m1'}
			for sigmaKey, sigmaValue in sigmaDict.items():
				sigmaDict[sigmaKey] = rootFile.Get(value + sigmaValue + '_' + self.name)
			self._exclusionlines[key] = sigmaDict
				
	def _setExclusions(self): #if we change the read steps provided by readInfo and get info, we can do this in a better way
		''' private methode used by the methodes "exclusion" and "dictOfExclusions"
		    serch for for the exclusionValues in the info.txt-file linked to the corresponding Analysis
		    and build the nested dictionary including all the exclusion values'''
		self._exclusions = {'observed':'exclusion','expected':'expectedexclusion'}
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
			    
			
	#def getLimitHi1stograms
	
#def loadAnalysis

#def loadTopology

def getDatabase():
	"""Creates a dictionary containing all runs as keys and all subdirectories resp. analyses as entries.
	
	"""
	
	data = {}
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
	logger.warning('requested keyword %s could not be found for %s-%s!' %(requested, run, analysis))
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
			content = getInfo(r, a)
			if not content: continue
			for c in content:
				if topos.count(c.split(' ')[1]) == 0:
					topos.append(c.split(' ')[1])
				
	if topos == []:
		logger.warning('for runs %s and analyses %s no topology could be found' %(runs, analyses))
		return None
		
	return topos
		
def getExtendedTopologies(analysis, run, topology = None):
	"""Checks if the topologies for one given analysis-run are tainted with any kind of mass requirements and returns dictionary with extended topologies. Can be reduced to given topology (returns list).
	### FIX ME: maybe use in class Pair only?
	
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
	print massdic
	return massdic
	
def linkPair(analysis, topology, current = True):
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
	

