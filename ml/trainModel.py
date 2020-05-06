#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging,sys,os
#import subprocess
import copy
from time import time
import matplotlib.pyplot as plt
#plt.switch_backend('agg')
import torch
from torch.utils.data import DataLoader as DataLoader
#from math import sqrt as sqrt
#from system.analysis import *
from system.dataset import *
from system.initnet import *
from getPerformance import *
from scipy.optimize import minimize
#torch.multiprocessing.set_start_method("spawn")
import numpy
import argparse
from configparser import ConfigParser
from datetime import datetime
#import string
#import random

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)


class Trainer():

	def __init__(self, expres, txName, netType, hyperParameter, sampleSize, massRange, sampleSplit, device, saveLogfile, saveLossPlot, replaceExistingModel):

		"""



		"""

		# global information
		self.expres = expres
		self.txName = txName
		self.netType = netType
		self.device = device
		#self.savePath = expres.path

		# TEMPORARY replace databasePath
		dbPath = expres.path
		for i in range(len(dbPath)):
			if dbPath[i:i+8] == 'database':
				dbPath = dbPath[i:]
				break
		self.savePath = os.getcwd() + "/" + dbPath
		# ---

		# generate datasets
		timestamp = time()
		logger.info("Building Trainer - generating dataset..")
		self.fullDataset = generateDataset(expres, txName, massRange, sampleSize, netType, device)
		splitData = self.fullDataset.split(sampleSplit)
		self.inputDimension = self.fullDataset.inputDimension
		self.trainingSet = splitData[0]
		self.testSet = splitData[1]
		self.validationSet = splitData[2]
		logger.info("Done. (%ss)" % (round(time() - timestamp, 3)))

		self.hyperParameter = hyperParameter
		# current hyperparam configuration for each training run
		self.currentHyperParamConfig = None
		self.totalHyperParamCombinations = len(self.hyperParameter)
		logger.info("%s Hyperparameter combinations have been loaded." % (self.totalHyperParamCombinations) )

		self.saveLogfile  = saveLogFile
		self.saveLossPlot = saveLossPlot
		self.replaceExistingModel = replaceExistingModel

		# current best model over all parameter configurations
		self.bestModelGlobal = None
		self.bestLossGlobal = 1e5
		self.bestHyperParamConfig = None

		# list of mean losses and hyperparam configurations for each model
		self.logData = []


	def findBestModel(self):

		"""



		"""

		logger.info("Starting grid search for %s: %s (%s)" % (self.expres.globalInfo.getInfo('id'), self.txName, self.netType) )

		for n in range(len(self.hyperParameter)):
			self.currentHyperParamConfig = self.hyperParameter[n]
			self.runCurrentConfiguration()

			if self.saveLossPlot:
				self.createLossPlot()

		if self.saveLogfile:
			self.saveResultsToLog()

		if self.replaceExistingModel == "outperforming":
			oldModel = loadModel(self.expres, self.txName, self.netType)
			if oldModel == None: 
				saveNewModel = True
			else: 
				saveNewModel = MSErel(oldModel(self.validationSet.inputs), self.validationSet.labels) > self.bestLossGlobal
		else: saveNewModel = self.replaceExistingModel == "always"

		if saveNewModel:
			self.saveModel()


	def runCurrentConfiguration(self):

		"""



		"""

		if self.currentHyperParamConfig == None:
			logger.error("No hyperparameter configuration specified for training.")
			return


		logger.info("Training model %d/%d .." %(self.currentHyperParamConfig["index"]+1, self.totalHyperParamCombinations))

		if self.saveLossPlot:
			self.lossPerEpoch = {'training':[],'testing':[]}


		self.model = createNet(self.currentHyperParamConfig, self.fullDataset, self.netType).to(device)
		self.trainModel()

		if netType == "regression":

			meanError = MSErel(self.model(self.validationSet.inputs), self.validationSet.labels)
			logger.info("\rDone! Total relative error on validation set: %s" %round(meanError.item(), 3))

			if False:
				newDataset = self._getWrongPredictionsSubset()		

				logger.info("Rerunning training with new dataset: %s points" %len(newDataset))
				trainingNew, testNew = newDataset.split([0.8,0.2])
				optimizer = loadOptimizer(self.currentHyperParamConfig["optimizer"], self.model, self.currentHyperParamConfig["learnRate"]*0.1)
				self.trainModel(optimizer, MSErel, epochNum = int(self.currentHyperParamConfig["epochNum"]*0.5), trainingSet = trainingNew, testSet = testNew)

				meanError = MSErel(self.model(self.validationSet.inputs), self.validationSet.labels)
				logger.info("\rSecond run: Done! Total relative error on validation set: %s" %round(meanError.item(), 3))

		else:

			self.model._delimiter = minimize(self._findDelimiter, 0.5, args=(self.model(self.validationSet.inputs).detach().numpy(), self.validationSet.labels.detach().numpy()), method="Powell").x.tolist()
			lossFunction = loadLossFunction(self.currentHyperParamConfig["lossFunction"], self.device)
			meanError = lossFunction(self.model(self.validationSet.inputs), self.validationSet.labels)
			logger.info("\rDone! Mean error on validation set: %s" %round(meanError.item(), 3))



		if meanError < self.bestLossGlobal:
			self.bestLossGlobal  = meanError
			self.bestModelGlobal = copy.deepcopy(self.model)
			self.bestHyperParamConfig = self.currentHyperParamConfig

		if self.saveLogfile:
			self.logData.append([round(meanError.item(), 3), self.currentHyperParamConfig])


	def _getWrongPredictionsSubset(self, tolerance = 0.05):

		"""



		"""

		relError = MSErel(self.model(self.fullDataset.inputs), self.fullDataset.labels, reduction = None)

		subset = []
		for n in range(len(relError)):
			if relError[n].item() > tolerance:
				newPoint = [inputs.item() for inputs in self.fullDataset.inputs[n]]
				newPoint.append(self.fullDataset.labels[n].item())
				subset.append(newPoint)

		newDataset = Data(subset, self.inputDimension, self.device)
		return newDataset


	def trainModel(self, optimizer = None, lossFunction = None, batchSize = 0, epochNum = 0, trainingSet = None, testSet = None):

		"""



		"""

		if trainingSet == None:  trainingSet  = self.trainingSet
		if testSet == None: 	 testSet 	  = self.testSet
		if batchSize == 0: 		 batchSize 	  = self.currentHyperParamConfig["batchSize"]
		if epochNum == 0: 		 epochNum 	  = self.currentHyperParamConfig["epochNum"]
		if optimizer == None: 	 optimizer 	  = loadOptimizer(self.currentHyperParamConfig["optimizer"], self.model, self.currentHyperParamConfig["learnRate"])
		if lossFunction == None: lossFunction = loadLossFunction(self.currentHyperParamConfig["lossFunction"], self.device)

		trainloader = DataLoader(trainingSet, batch_size = batchSize, shuffle = True, num_workers = 6)

		bestLossLocal, bestEpochLocal, bestModelLocal  = 1e5, 0, copy.deepcopy(self.model)

		for epoch in range(epochNum):

			self.model.train()

			for i, data in enumerate(trainloader):  

				optimizer.zero_grad()
				inputs, labels = data[0], data[1]
				loss = lossFunction(self.model(inputs), labels)
				loss.backward()
				optimizer.step()

			self.model.eval()

			with torch.no_grad():
			
				trainingLoss = lossFunction(self.model(trainingSet.inputs), trainingSet.labels)
				testLoss = lossFunction(self.model(testSet.inputs), testSet.labels)
							
				if self.saveLossPlot:
					self.lossPerEpoch['training'].append(trainingLoss)
					self.lossPerEpoch['testing'].append(testLoss)
									
				if testLoss < bestLossLocal:
					bestLossLocal  = testLoss
					bestModelLocal = copy.deepcopy(self.model)
					#bestEpochLocal = epoch
			

			print("\repoch: %d/%d | testloss: %s" %(epoch+1,epochNum, round(testLoss.item(), 3)), end = "", flush = True)

		self.model = bestModelLocal



	def createLossPlot(self):

		"""



		"""

		savePath = self.savePath + "/performance/"
		if not os.path.exists(savePath): os.makedirs(savePath)
			
		fileName = txName + "_" + netType + "_lossPlot.eps"

		plt.figure(5)
		plt.title('Loss Function', fontsize=20)
		plt.xlabel('Epochs')
		plt.ylabel('Error')
		plt.plot([e for e in range(len(self.lossPerEpoch['training']))], self.lossPerEpoch['training'], label = 'Train Loss')
		plt.plot([e for e in range(len(self.lossPerEpoch['testing']))], self.lossPerEpoch['testing'], label = 'Test Loss')
		plt.legend()
		plt.savefig(savePath + fileName)
		logger.info("Lossplot has been created. (%s)" %(savePath + fileName))


	def saveResultsToLog(self):

		"""



		"""

		date = datetime.now()

		self.logData = sorted(self.logData, key=lambda lD: lD[0])

		savePath = self.savePath + "/logs/"
		if not os.path.exists(savePath): os.makedirs(savePath)

		fileName = self.txName + "_" + self.netType + "_" + date.strftime("%d.%m.%Y-%H:%M:%S")

		with open(savePath + fileName, "a+") as file:
			for lD in self.logData:
				file.write("loss: %s\t%s\n" %(lD[0], str(lD[1])))

		logger.info("Logfile has been created. (%s)" %(savePath + fileName))



	def _findDelimiter(self, delimiter, predictions, labels):

		"""



		"""

		right, wrong = 0, 0

		for i in range(len(predictions)):

			if ( labels[i] == 0. and predictions[i] < delimiter ) or ( labels[i] == 1. and predictions[i] > delimiter ):
				right += 1
			else:
				wrong += 1

		return float(wrong)/float(right+wrong)





	def saveModel(self):

		"""



		"""

		savePathModel = self.savePath + "/models/"
		fileNameModel = self.txName + '_' + self.netType + '.pth'
		if not os.path.exists(savePathModel): os.makedirs(savePathModel)

		#torch.save(self.bestModelGlobal.state_dict(), savePathModel + fileNameModel)
		torch.save(self.bestModelGlobal, savePathModel + fileNameModel)
		logger.info("Best performing model has been saved. (%s)" %(savePathModel + fileNameModel))

		savePathInfo = self.savePath + "/"
		fileNameInfo = self.txName + "_" + self.netType + ".info"
		if not os.path.exists(savePathInfo): os.makedirs(savePathInfo)

		with open(savePathInfo + fileNameInfo, "w+") as file:

			date = datetime.now()
			file.write("created on:\t%s\n" %(date.strftime("%d.%m.%Y-%H:%M:%S")))
			file.write("implemented by:\t%s\n" %("Philipp Neuhuber")) # NYI
			file.write("relative error:\t%s%%\n\n" %(round(self.bestLossGlobal.item()*100., 3)))
			file.write("%s\n\n" % str(self.bestModelGlobal))
			file.write("hyperParameters:\n---\n")
			for key in self.bestHyperParamConfig: file.write("%s: %s\n" %(key, self.bestHyperParamConfig[key]))
			file.write("---")
			
		logger.info("Model.info file has been created. (%s)" %(savePathInfo + fileNameInfo))
	
	
					

if __name__=='__main__':

	ap = argparse.ArgumentParser(description="Trains and finds best performing neural networks for database analyses via hyperparameter search")
	ap.add_argument('-p', '--parfile', 
			help='parameter file specifying the plots to be checked', default='nn_parameters.ini')
	ap.add_argument('-l', '--log', 
			help='specifying the level of verbosity (error, warning, info, debug)',
			default = 'info', type = str)
           
	args = ap.parse_args()
    
	if not os.path.isfile(args.parfile):
		logger.error("Parameters file %s not found" %args.parfile)
	else:
		logger.info("Reading validation parameters from %s" %args.parfile)


	parser = ConfigParser( inline_comment_prefixes=( ';', ) )
	parser.read(args.parfile)


	#Control output level:
	numeric_level = getattr(logging,args.log.upper(), None)
	logger.setLevel(level=numeric_level)
    
	#Add smodels and smodels-database to path
	smodelsPath = parser.get("path", "smodelsPath")
	databasePath = parser.get("path", "databasePath")
	sys.path.append(smodelsPath)
	sys.path.append(databasePath)
	from smodels.experiment.databaseObj import Database
	

	#Select analysis and topologies for training
	analysisID = parser.get("database", "analysis")
	txNames = parser.get("database", "txNames").split(",")


	#Configure dataset generated for training
	sampleSize = float(parser.get("dataset", "sampleSize"))
	massRange = parser.get("dataset", "massRange").split(",")
	massRange = [float(mR) for mR in massRange]
	sampleSplit = parser.get("dataset", "sampleSplit").split(",")
	sampleSplit = [float(sS) for sS in sampleSplit]


	#Choose wether to run on CPU or GPU
	whichDevice = float(parser.get("options", "device"))
	deviceCount = torch.cuda.device_count()
	if torch.cuda.is_available() and int(whichDevice) >= 0 and whichDevice <= deviceCount:
		device = torch.device('cuda:' + str(whichDevice))
		logger.info("Running on GPU:%d" %deviceCount)
	else:
		device = torch.device('cpu')
		logger.info("Running on CPU")

	#Select which NNs to train
	whichNN = parser.get("options", "whichNN")
	if whichNN == "both": whichNN = ["regression", "classification"]
	elif whichNN == "regression" or whichNN == "classification":
		whichNN = [whichNN]
	else:
		logger.error("Invalid NN type selected. Allowed options: 'regression'  'classification' and 'both'")


	#Check wether you want to override old NN with new results
	overwrite = parser.get("options", "overwrite")
	if not (overwrite == "always" or overwrite == "never" or overwrite == "outperforming"):
		logger.error("Invalid overwrite parameter. Allowed options: 'always' 'never' and 'outperforming'")


	#Check analysis options
	saveLogFile = parser.getboolean("analysis", "logFile")
	saveLossPlot = parser.getboolean("analysis", "lossPlot")
	runPerformance = parser.getboolean("analysis", "runPerformance")
	
	expres = Database(databasePath)
	expres = expres.getExpResults(analysisIDs = analysisID, useSuperseded = True, useNonValidated = True)[0]

	for netType in whichNN:

		optimizers = parser.get(netType, "optimizer").split(",")
		lossFunctions = parser.get(netType, "lossFunc").split(",")
		batchSizes = parser.get(netType, "batchSize").split(",")
		batchSizes = [int(bS) for bS in batchSizes]
		activationFunctions = parser.get(netType, "activFunc").split(",")
		epochNums = parser.get(netType, "epochs").split(",")
		epochNums = [int(eN) for eN in epochNums]
		learnRates = parser.get(netType, "learnRate").split(",")
		learnRates = [float(lN) for lN in learnRates]
		layers = parser.get(netType, "layer").split(",")
		layers = [int(l) for l in layers]
		nodes = parser.get(netType, "nodes").split(",")
		nodes = [int(n) for n in nodes]
		shapes = parser.get(netType, "shape").split(",")
		try: rescaleMethods = parser.get(netType, "rescaleData").split(",")
		except: rescaleMethods = [None]

		hyperParameter = {}
		hyperParameter["optimizer"] = optimizers
		hyperParameter["lossFunction"] = lossFunctions
		hyperParameter["batchSize"] = batchSizes
		hyperParameter["activationFunction"] = activationFunctions
		hyperParameter["epochNum"] = epochNums
		hyperParameter["learnRate"] = learnRates
		hyperParameter["layer"] = layers
		hyperParameter["nodes"] = nodes
		hyperParameter["shape"] = shapes
		hyperParameter["rescaleMethod"] = rescaleMethods
		hyperParameter = HyperParameter(hyperParameter)

		for txName in txNames:
			if GetModel(expres, txName, netType) == None or overwrite != 'never':

				modelTrainer = Trainer(expres, txName, netType, hyperParameter, sampleSize, massRange, sampleSplit, device, saveLogFile, saveLossPlot, overwrite)
				modelTrainer.findBestModel()

				#if runPerformance:
					#validateModel(model, expres, txName, massRange, sampleSize, netType, validationSet)
							#getPerformanceOfModel()
				
				
	

