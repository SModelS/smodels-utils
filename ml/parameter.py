#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. module:: readParameterFile.py
   :synopsis: load parameters for various ML related scripts
.. moduleauthor:: Philipp Neuhuber <ph.neuhuber@gmail.com>

"""

import sys, os, torch
from configparser import ConfigParser




TrainingParameter = {
	"pathing": 	[("databasePath", str), 
				("smodelsPath", str), 
				("utilsPath", str),
				("outputPath", str)],
	"database": [("analysis", str),
				("txName", str),
				("dataselector", str),
				("signalRegion", str),
				("overwrite", str)],
	"dataset": 	[("sampleSize", int), 
				("sampleSplit", float), 
				("loadFile", str),
				("massColumns", int), 
				("refXsecFile", str), 
				("refXsecColumns", int)],
	"computation": [("device", str),
				("cores", int)],
	"validation": [("logFile", bool),
				("lossPlot", bool),
				("runPerformance", bool)],
	"hyparam":	[("optimizer", str), 
				("lossFunction", str), 
				("batchSize", int),
				("activationFunction", str), 
				("epochNum", int), 
				("learnRate", float),
				("layer", int), 
				("nodes", int), 
				("shape", str), 
				("rescaleMethod", str)]
}



class PermutationDictionary():

	def __init__(self, parameterDict):

		self.parameter = parameterDict
		self.combinations = {}
		self.numOfCombinations = 0
		self._index = -1

		paramIndex = {}
		done = False
		firstKey = list(self.parameter.keys())[0]
		lastKey = list(self.parameter.keys())[-1]

		while not done:

			endOfDict = True
			for key in parameterDict:
				currentParamLen = len(self.parameter[key])

				if not key in self.combinations:
					self.combinations[key] = []

					if key != firstKey: paramIndex[key] = 0
					else: paramIndex[key] = -1

				if endOfDict:
					if paramIndex[key] + 1 < currentParamLen:
						paramIndex[key] += 1
						endOfDict = False
					else:
						paramIndex[key] = 0
						endOfDict = True
						done = key == lastKey
						#if key == lastKey: done = True

			if not done:
				self.numOfCombinations += 1
				for key in self.combinations:
					self.combinations[key].append(paramIndex[key])

	
	@property
	def incrIndex(self):
		self._index += 1
		return self._index < self.numOfCombinations

	@property
	def resetIndex(self):
		self._index = -1

	@property
	def index(self):
		return self._index

	def __len__(self):
		return self.numOfCombinations


	def __getitem__(self, index):

		if isinstance(index, str):
			target = self.parameter[index][self.combinations[index][self._index]]
			if isinstance(target, list): target = target[0]
			return target

		if index == -1: index = self._index
		configuration = {"index": index}
		for key in self.parameter:
			configuration[key] = self.parameter[key][self.combinations[key][index]]
		return configuration

	def __str__(self):
		return str(self.parameter)





class Parameter(dict):

	def __init__(self, fileName, logLevel):

		print("reading %s.." %fileName)

		parser = ConfigParser( inline_comment_prefixes=(';', ) )
		parser.allow_no_value = True
		parser.read(fileName)

		self._parameter = {}

		netTypes = ["regression","classification"]

		for net in netTypes:
			TrainingParameter[net] = TrainingParameter["hyparam"]
		del(TrainingParameter["hyparam"])

		for key,values in TrainingParameter.items():

			if parser.has_section(key):

				loadedValues = {}

				for line in values:

					keyword = line[0]
					fromat = line[1]

					try:
						param = parser.get(key, keyword).split(",")

						if fromat != str:
							param = [fromat(x) for x in param]
					except: param = [None]

					loadedValues[keyword] = param

			else:
				print("No '{}' section found. Skipping..".format(key)) #logger.info
				loadedValues = None


			self._parameter[key] = loadedValues


		if not self._parameter["database"]["overwrite"][0] in ["always","never","outperforming"]:
			self._parameter["database"]["overwrite"] = ["never"]
			#logger.warning("Invalid overwrite parameter. Allowed options: 'always' 'never' and 'outperforming'. Setting parameter to 'never'")

		self._parameter["database"] = PermutationDictionary(self._parameter["database"])
		hyperParameter = {}
		for net in netTypes:
			hyperParameter[net] = PermutationDictionary(self._parameter[net])
			del(self._parameter[net])
		self._parameter["hyperParameter"] = hyperParameter


		try: device = int(self["device"])
		except: device = self["device"]
		deviceCount = torch.cuda.device_count()
		if isinstance(device, int) and torch.cuda.is_available() and device < deviceCount:
			device = torch.device("cuda:" + str(device))
			#logger.info("Running on GPU:%d" %device)
		else:
			device = torch.device("cpu")
			#logger.info("Running on CPU")
		self._parameter["computation"]["device"] = device

		
		self._parameter["pathing"]["smodelsPath"] = os.path.abspath(self["smodelsPath"])
		self._parameter["pathing"]["utilsPath"] = os.path.abspath(self["utilsPath"])
		self._parameter["pathing"]["databasePath"] = os.path.abspath(self["databasePath"])

		sys.path.append(self["smodelsPath"])
		sys.path.append(self["utilsPath"])
		from smodels.experiment.databaseObj import Database
		self._parameter["smodels-db"] = Database(self["databasePath"])

		import smodels.tools.smodelsLogging as log
		log.setLogLevel(logLevel)


	@property
	def loadExpres(self):

		analysis 	 = self["analysis"]
		txName 		 = self["txName"]
		dataSelector = self["dataselector"]
		signalRegion = self["signalRegion"]

		expres = self["smodels-db"].getExpResults(analysisIDs = analysis, txnames = txName, dataTypes = dataSelector, useSuperseded = True, useNonValidated = True)[0]
		txList = expres.getDataset(signalRegion).txnameList #"SR1FULL_175"

		for tx in txList:
			if str(tx) == txName:
				#txNameData = tx.txnameData
				break

		self._parameter["expres"] = expres
		self._parameter["txName"] = tx
		#self._parameter["txNameData"] = txNameData

		
	def set(self, key, value):
		self._parameter[key] = value

	def __getitem__(self, targetKey):

		target = None

		if targetKey in self._parameter:
			target = self._parameter[targetKey]
		else:
			for subdict in self._parameter.values():

				if isinstance(subdict, PermutationDictionary):
					if targetKey in subdict.parameter:
						target = subdict[targetKey]
						break

				if isinstance(subdict, dict) and targetKey in subdict:
					target = subdict[targetKey]
					break
		
		if isinstance(target, list) and len(target) == 1: target = target[0]
		return target


	#def set(self, target, value, subKey = None):
	#def add(self, target, value, subKey = None):

	def __str__(self):
		for key, value in self._parameter.items():
			print(value)

			
"""	


def readParameterFile(logger, parameterFile):

	parser = ConfigParser( inline_comment_prefixes=(';', ) )
	parser.allow_no_value = True
	parser.read(parameterFile)

	############################################
	# Add smodels and smodels-database to path #
	############################################

	sct = "path"
	if parser.has_section(sct):
		
		smodelsPath = parser.get(sct, "smodelsPath")
		databasePath = parser.get(sct, "databasePath")
		utilsPath = parser.get(sct, "utilsPath")
		sys.path.append(smodelsPath)
		sys.path.append(databasePath)
		sys.path.append(utilsPath)
		import smodels
		from smodels.experiment.databaseObj import Database

		outputPath = parser.get(sct, "outputPath")
		if outputPath == "": outputPath = None

		paramPath = {"smodels": smodelsPath, "database": databasePath, "utils": utilsPath, "outputPath": outputPath}

	else:
		logger.info("No '{}' section found. Skipping Database import.".format(sct))
		paramPath = None


	###############################################
	# Select analysis and topologies for training #
	###############################################

	sct = "database"
	if parser.has_section(sct):

		analysisID = parser.get(sct, "analysis").split(",")
		txName = parser.get(sct, "txName").split(",")
		dataselector = parser.get(sct, "dataselector").split(",")
		signalRegion = parser.get(sct, "signalRegion").split(",")
		for n, sr in enumerate(signalRegion):
			if sr == "None": 
				signalRegion[n] = None

		paramDatabase = {"analysisID": analysisID, "txName": txName, "dataselector": dataselector, "signalRegion": signalRegion}

		# Check wether you want to override old NN with new results		
		
		overwrite = parser.get(sct, "overwrite")
		if not (overwrite == "always" or overwrite == "never" or overwrite == "outperforming"):
			logger.info("Invalid overwrite parameter. Allowed options: 'always' 'never' and 'outperforming'. Setting parameter to 'never'")
			overwrite = "never"

	else:
		logger.info("No '{}' section found. Skipping map selection".format(sct))
		paramDatabase = None

	##############################################################
	# Dataset settings used for training, testing and validation #
	##############################################################

	sct = "dataset"
	
	if parser.has_section(sct):

		params = [("sampleSize", int), ("sampleSplit", float), ("loadFile", str),
			("massColumns", int), ("refXsecFile", str), ("refXsecColumns", int)]

		paramDataset = {}

		for param in params:

			key = param[0]
			form = param[1]

			try:
				p = parser.get(sct, key).split(",")

				if form != str:
					p = [form(x) for x in p]
			except: p = [None]

			paramDataset[key] = p

		print(paramDataset)
		'''
		sampleSize 	= int(parser.get(sct, "sampleSize"))
		sampleSplit = parser.get(sct, "sampleSplit").split(",")
		sampleSplit = [float(x) for x in sampleSplit]
		loadFile 	= parser.get(sct, "loadFile")
		massColumns = parser.get(sct, "massColumns").split(",")
		massColumns = [float(x) for x in massColumns]
		refXsecFile	= parser.get(sct, "refXsecFile")
		refXsecColumns = parser.get(sct, "refXsecColumns").split(",")
		refXsecColumns = [float(x) for x in refXsecColumns]

		paramDataset = {"sampleSize": sampleSize, "sampleSplit": sampleSplit, "loadFile": loadFile, "massColumns": massColumns, "refXsecFile": refXsecFile, "refXsecColumns": refXsecColumns}
		'''
	else:
		logger.info("No '{}' section found. Skipping dataset specifications".format(sct))
		paramDataset = None

	######################################
	# Choose wether to run on CPU or GPU #
	######################################

	sct = "device"
	if parser.has_section(sct):

		whichDevice = int(parser.get(sct, "device"))
		deviceCount = torch.cuda.device_count()
		if torch.cuda.is_available() and whichDevice >= 0 and whichDevice <= deviceCount:
			device = torch.device("cuda:" + str(whichDevice))
			logger.info("Running on GPU:%d" %deviceCount)
		else:
			device = torch.device("cpu")
			logger.info("Running on CPU")

		cores = int(parser.get(sct, "cores"))

		paramDevice = {"device": device, "cores": cores}
		
	else:
		logger.info("No '{}' section found. Default set to single-core CPU".format(sct))
		device = torch.device("cpu")
		paramDevice = {"device": "cpu", "cores": 1}


	
	'''
	#Select which NNs to train
	whichNN = parser.get("options", "whichNN")
	if whichNN == "both": whichNN = ["regression", "classification"]
	elif whichNN == "regression" or whichNN == "classification":
		whichNN = [whichNN]
	else:
		logger.error("Invalid NN type selected. Allowed options: 'regression'  'classification' and 'both'")
	'''

	##########################
	# Load analysis options #
	##########################

	sct = "analysis"
	if parser.has_section(sct):

		logFile = parser.getboolean(sct, "logFile")
		lossPlot = parser.getboolean(sct, "lossPlot")
		runPerformance = parser.getboolean(sct, "runPerformance")

		paramAnalysis = {"logFile": logFile, "lossPlot": lossPlot, "runPerformance": runPerformance}

	else:
		logger.info("No '{}' section found. Not going to produce any logfiles or performance outputs".format(sct))
		paramAnalysis = None


	#######################
	# Load Hyperparameter #
	#######################

	hyperParameter = {}

	params = [("optimizer", str), ("lossFunction", str), ("batchSize", int),
			("activationFunction", str), ("epochNum", int), ("learnRate", float),
			("layer", int), ("nodes", int), ("shape", str), ("rescaleMethod", str)]

	for netType in ["regression", "classification"]:

		if parser.has_section(netType):

			hP = {}

			for param in params:

				key = param[0]
				form = param[1]

				try:
					p = parser.get(netType, key).split(",")

					if form != str:
						p = [form(x) for x in p]
				except: p = [None]

				hP[key] = p
			
			#hP = HyperParameter(hp)

		else:
			logger.info("No '{}' section found. No hyperparameters loaded".format(netType))
			hP = None

		hyperParameter[netType] = hP
		
	
	parameters = {"path": paramPath, 
			"database": paramDatabase, 
			"dataset": paramDataset, 
			"device": paramDevice, 
			"analysis": paramAnalysis, 
			"hyperParameter": hyperParameter}

	return parameters
	


if __name__=='__main__':

	ap = argparse.ArgumentParser(description = "Reads parameter file for neural network training")
	ap.add_argument('-p', '--parfile', 
			help='parameter file specifying the plots to be checked', default = 'nn_parameters.ini')
	ap.add_argument('-l', '--log', 
			help='specifying the level of verbosity (error, warning, info, debug)',
			default = 'info', type = str)
           
	args = ap.parse_args()
    
	if not os.path.isfile(args.parfile):
		logger.error("Parameters file %s not found" %args.parfile)
	else:
		logger.info("Reading validation parameters from %s" %args.parfile)


	# Control output level

	numeric_level = getattr(logging,args.log.upper(), None)
	logger.setLevel(level=numeric_level)

	readParameterFile(logger, args.parfile)

"""

