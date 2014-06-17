#!/usr/bin/env python

	
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
		if self.numberOfExtendedResults == 1: 
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
	def numberOfExtendedResults(self):
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
	

