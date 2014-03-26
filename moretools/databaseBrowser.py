#!/usr/bin/env python

"""
.. module:: databaseBrowser
   :synopsis: Centralized facility to access smodels-database in order to produce summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Wolfgang Magerl <wolfgang.magerl@gmail.com>

"""

import ROOT
import logging, os, types
import dictionaries
from Tools import PhysicsUnits
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)

log.setLevel(level=logging.ERROR)

def setLogLevel(level = 'error'):
	if level == 'debug':
		log.setLevel(level=logging.DEBUG)
	if level == 'info':
		log.setLevel(level=logging.INFO)
	if level == 'error':
		pass
		

Base = '/afs/hephy.at/user/w/walten/public/sms/'
#Base = '/home/vroni/Documents/Diplomarbeit/smodels-database/'
allruns = ["8TeV", "ATLAS8TeV", "RPV8", "2012", "RPV7", "2011"]
artifacts = ['old', 'bad', 'missing', 'TODO', 'readme'] 
currentRun = '8TeV'

# ### FIX ME: should I use these? Improves performance? 
#allTopologies = []
#allAnalyses = []
#allPairs = []

class Analysis(object):
	
	"""contains all analysis-specific information (e.g. PAS, lumi, publication-url, ...)
		can handle specified run
		
	"""
	def __new__(self, analysis, run = currentRun):
		info = readInfo(run, analysis)
		if info:
			log.info('found info.txt in %s-%s.' %(run, analysis))
			return object.__new__(self)
		log.error('Cannot build Analysis %s for run %s.' %(analysis, run))
		
	def __init__(self, analysis, run = currentRun):
		self._name = analysis
		self._info = readInfo(run, self._name)
		self._run = run
		
	def _parsInfo(self, requested):
		content = [string for string in self._info if requested in string]
		if content:
			log.info('found %s: %s' %(requested,content[0].split(' ')[1]))
			return content[0].split(' ')[1].strip()
		
	def getLumi(self):
		return self._parsInfo('lumi')
		
	def getPAS(self):
		return self._parsInfo('pas')
		
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
			return getInfo(self._run, self._name, 'checked')
		return None
		
	def getName(self):
		return self._name
		
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
			log.info('found topology %s' %topology)
			return object.__new__(self)
		log.error('Cannot build Topology %s' %topology)
		
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
			log.warning('no run was given, therefore trying all available runs %s and returning dictionary!' %self._runs)
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
			log.info('found decay for topology %s' %self._name)
			return dictionaries.decay[self._name]
		if dictionaries.decay.has_key(self._slackTopologyName()):
			log.info('found decay for topology %s with slack name %s' %(self._name, self._slackTopologyName()))
			return dictionaries.decay[self._slackTopologyName()]
		log.warning('no decay found for topology %s' %self._name)
		return None
		
	#def getPrettyName       # particles resp. productionmode
	#def treatMasssplitting
	#def setAnalyses
	#def refreshAnalyses
	
class Pair (object):
	"""Contains all pair-specific informations and objects (e.g. exclusionlines, histograms, ...).

	"""
	# Best to call through function linkPairs()!
	
	def __init__ (self, pair):
		self._topo = pair[2]
		self._ana = pair[1]
		self._run = pair[0]
		log.info('creating pair-object for %s-%s!' %(self._ana, self._topo))
		
	def getAnalysis(self):
		return Analysis(self._ana, self._run)
		
	def getTopology(self):
		return Topology(self._topo)
		
	def getExclusionLines(self):
		"""Retrieves all the exclusionlines stored in sms.root as a python dictionary.
		
		"""
		if not checkResults(self._run, self._ana, 'sms.root'): return None
		rootFile = ROOT.TFile(checkResults(self._run, self._ana, 'sms.root'))
		exclusionLines = {}
		expected = []
		observed = []
		if not getExtendedTopologies(self._ana, self._run, self._topo): return None
		for t in getExtendedTopologies(self._ana, self._run, self._topo): 
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
		if not allLines: return None
		keys = allLines.keys()
		
		if expected == True:
			keys = [k for k in keys if 'expected' in k]
		if expected == False:
			keys = [k for k in keys if 'observed' in k]
			
		exLines = allLines[keys[0]]
		if sigma == 0: exLines = [l for l in exLines if not 'p1' in l.GetName() and not 'm1' in l.GetName()]
		elif sigma == 1: exLines = [l for l in exLines if 'p1' in l.GetName()]
		elif sigma == -1: exLines = [l for l in exLines if 'm1' in l.GetName()]
		else:
			log.error('no exclusionlines available for sigma = %s' % sigma)
			return None
		return exLines
		
	def selectExclusionLine(self, expected = False, sigma = 0, condition = 'xvalue', value = 050):
		"""Selects one exclusionline (out of all exclusionLines for this topology) corresponding to a specified case of mass proportions (e.g. x-value = 050, mass of LSP = 50 GeV, ...)
		### FIX ME: maybe define a standard configuration for other conditions as xvalues
		
		"""
		exLines = self.selectTypeOfExclusionLine(expected, sigma)
		if not exLines: return None
		if len(exLines) == 1:
			log.info('there is just one exclusionline of this type!')
			return exLines[0]
			
		if not condition in ['D', 'x', 'LSP', 'C', 'M', 'xvalue']:
			log.error('%s is no valid type of condition for intermediate masses' %condition)
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
		
		if not getExtendedTopologies(self._ana, self._run, self._topo): return None
		for t in getExtendedTopologies(self._ana, self._run, self._topo):
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
	for r in allruns:
		data[r] = os.listdir("%s/%s" % (Base, r))
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
		log.error('no results without analysis!')
		return None
		
	if not run:
		run = getAllRuns(analysis)
		
	path = Base + run + '/' + analysis + '/' + requested
	log.debug('check path: %s' %path)
	if not os.path.exists(path):
		log.error('for run %s and analyses %s no %s was found' %(run, analysis, requested))
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
		log.debug('found info.txt for run %s and analysis %s' %(run, analysis))
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
	log.info('requested keyword %s could not be found for %s-%s!' %(requested, run, analysis))
	return None
	
def preprocessAxes(infoLine):
	"""To handle the information stored in the axes-labeled line of info.txt, this line has to be preprocessed.
	
	"""
	infoLine = infoLine[0].split(',')
	infoLine[0] = infoLine[0].replace('axes: ','')
	infoLine = [ax.strip() for ax in infoLine]
	log.debug('axes- information: %s' %infoLine)
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
		log.error('no valid analysis %s' %analysis)
		return None
	
	if current == True:
		log.info('for %s collected runs: %s' %(analysis,runs))
		log.info('returning: %s' %runs[0])
		return runs[0]
		
	if current == False:
		return runs
		
def checkRun(run):
	"""Verifies if given run is valid. Returns True if run is found in database.
	
	"""
	if not run in getDatabase().keys():
		log.error('no valid run %s' %run)
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
		log.info('found %s analyses for %s' %(len(database[run]), run))
		return database[run]

	for a in database[run]:
		topologies = getAllTopologies(a, run)
		if topologies and topology in topologies:
			log.info('found %s in %s-%s' %(topology,run,a))
			analyses.append(a)
		
	if analyses == []:
		log.error('%s is no valid topology for given run %s' %(topology, run))
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
					
	log.debug('searching topologies for runs %s and analyses %s' %(runs,analyses))
	for r in runs:
		if nono == True:
			analyses = getAllAnalyses(r)
			log.info('no analysis was given, therefore took all analyses for run %s: %s' %(r, analyses))
		for a in analyses:
			content = getInfo(r, a)
			if not content: continue
			for c in content:
				if topos.count(c.split(' ')[1]) == 0:
					topos.append(c.split(' ')[1])
				
	if topos == []:
		log.error('for runs %s and analyses %s no topology could be found' %(runs, analyses))
		return None
		
	return topos
		
def getExtendedTopologies(analysis, run, topology = None):
	"""Checks if the topologies for one given analysis-run are tainted with any kind of mass requirements and returns dictionary with extended topologies. Can be reduced to given topology (returns list).
	### FIX ME: maybe use in class Pair only?
	
	"""
	topos = {}
	log.debug('got analysis: %s and run %s!' %(analysis, run))
	if not getInfo(run, analysis, 'axes'):
		log.info('No additional information about axes was found for %s-%s!' %(run, analysis))
		if not getAllTopologies(analysis, run): return None
		for t in getAllTopologies(analysis, run):
			topos[t]=[t]
		if not topology: return topos
		if topos.has_key(topology): return topos[topology]
		log.error('for %s-%s there is no topology %s' %(run, analysis, topology))
		return None
	
	infoLine = getInfo(run, analysis, 'axes')
	axes = preprocessAxes(infoLine)
	log.info('for %s-%s there is additional mass information!' %(run, analysis)) 
	
	for ax in axes:
		log.debug('axesline is:%s' %ax)
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
				log.info('topology is: %s => more then one additional condition is too much at the moment' %topo)
				continue
	
	if topos == {'':[]}:
		log.error('Something is wrong with the axes line in the info.txt for %s-%s!' %(run, analysis))
		return None
	if not topology: return topos
	if topos.has_key(topology): return topos[topology]
	log.error('for %s-%s there is no topology %s' %(run, analysis, topology))
	return None
	
def massProportions(axesLine):
	"""Reads out all the conditions for intermediate masses (e.g. masssplitting-xvalues 025, 050, 075) implicitly stored in axes-lines of info.txt and returns the information as dictionary.
	
	"""
	massdic = {}
	topo = axesLine.split(' ')[0].replace(':', '').strip()
	massdic[topo] = axesLine.replace(topo + ':', '').split('-')
	massdic[topo] = [c.strip() for c in massdic[topo]]
	log.info('for %s there are %s different cases of mass proportions' %(topo, len(massdic[topo])))
	massdic[topo]=[c.split(' ') for c in massdic[topo]]
	return massdic
	
def linkPair(analysis, topology, current = True):
	"""Inter couples analysis and topology creating a specified pair. Either for all runs (returns dictionary) or for first run the given analysis appears for in the database (returns list)
	
	"""
	if current == False:
		runs = getAllRuns(analysis, current = False)
		pair = {}
		if not runs: return None
		log.debug('try to link pair %s-%s for all available runs!' %(analysis, topology))
		for r in runs:
			topologies = getAllTopologies(analysis, run)
			if topologies and topology in topologies:
				pair[r]=[analysis, topology]
				log.debug('found pair %s-%s for run %s!' %(analysis, topology, run))
		return pair
	
	run = getAllRuns(analysis)
	if not run: return None
	topologies = getAllTopologies(analysis, run)
	if not topologies:
		log.info('there are no topologies for %s-%s' %(run, analysis))
		return None
		
	log.debug('try to link pair %s-%s for run %s!' %(analysis, topology, run))
	if topologies and topology in topologies:
		return [run, analysis, topology]
	

