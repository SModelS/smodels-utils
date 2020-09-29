#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. module:: trainModel.py
   :synopsis: run gridsearch to train optimal neural networks for smodels-database maps
.. moduleauthor:: Philipp Neuhuber <ph.neuhuber@gmail.com>

"""

import logging,sys,os
import numpy,argparse
import torch,random,copy

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
#logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

#import subprocess
#plt.switch_backend('agg')
#torch.multiprocessing.set_start_method("spawn")




def makeHeuristicPredictions(hyperParameter, netType):

	hyperParamPredicted = copy.deepcopy(hyperParameter)

	for key, value in hyperParameter.items():
		if value == None or value == [None]:

			if key == "optimizer":
				newValue = "Adam"

			if key == "batchSize":
				newValue = 16
			
			elif key == "lossFunction":

				if netType == "regression":
					newValue = "MSErel"
				else:
					newValue = "BCE"

			elif key == "rescaleMethod":
				if netType == "regression":
					newValue = "standardScore"
				else: newValue = None

			elif key == "learnRate":
				newValue = 1e-3

			elif key == "epochNum":

				lr = hyperParameter["learnRate"]
				if lr == None:
					lr = 1e-3
					hyperParamPredicted["learnRate"] = [lr]

				newValue = 20 - int(20 * np.log10(lr))

			hyperParamPredicted[key] = [newValue]

	return hyperParamPredicted


class TrainerWrapper():

	"""
	Wrapper for regression and classification trainer.
	Handles heuristics, dataset generation and combines finished networks for a single analysis map.

	:ivar parameters: (vtype: dict >> string/int/f32)
	:ivar modelTrainer: Holds Trainer classes for individual network types (vtype: dict >> Trainer)

	"""


	def __init__(self, parameters): #, dataset = None):

		"""



		"""

		self.parameters = parameters
		self.paramPath = parameters["path"]
		self.paramDatabase = parameters["database"]
		self.paramDataset = parameters["dataset"]
		self.hyperParameterRaw = copy.deepcopy(parameters["hyperParameter"])
		self.paramDevice = parameters["device"]
		self.paramAnalysis = parameters["analysis"]

		analysis 		= self.paramDatabase["analysisID"]
		txName 			= self.paramDatabase["txName"]
		dataSelector 	= self.paramDatabase["dataSelector"]

		db = Database(self.paramPath["database"])
		expres = db.getExpResults(analysisIDs = analysis, txnames = txName, dataTypes = dataSelector, useSuperseded = True, useNonValidated = True)[0]
		txList = expres.getDataset(self.paramDatabase["signalRegion"]).txnameList

		for tx in txList:
			if str(tx) == self.paramDatabase["txName"]:
				txNameData = tx.txnameData
				break

		self.paramDatabase["expres"] = expres
		self.paramDatabase["txNameData"] = txNameData

		self.modelTrainer = {}
		self.hyperParameter = {}
		self.outputDir = {}

		self._setOutputPaths()

	
	def _setOutputPaths(self):

		"""
		Set directories for any training outputs including the final model.
		If 'outputPath' in parameter file was left blank, default expres database location
		will be used as root folder.

		"""

		###################################################
		#		  Storage location for output 			  #
		###################################################
		self.outputDir["model"]		  = "/models/"		  #
		self.outputDir["log"]		  = "/logs/"		  #
		self.outputDir["loss"] 		  = "/performance/"	  #
		self.outputDir["performance"] = "/performance/"   #
		###################################################

		if self.paramPath["outputPath"] != None:
			dbPath = self.paramDatabase["expres"].path
			for i in range(len(dbPath)):
				if dbPath[i:i+8] == "database":
					dbPath = dbPath[i+8:]
					break
			outputDir = os.path.join(os.path.abspath(self.paramPath["outputPath"]) + dbPath)
		else: outputDir = expres.path

		for key, value in self.outputDir.items():
			self.outputDir[key] = os.path.join(outputDir + value)
			if not os.path.exists(self.outputDir[key]):
				try: os.makedirs(self.outputDir[key])
				except: logger.error("Insufficient user rights! Failed to create output directory.")


	def _makeHeuristicPredictions(self):

		"""
		If some hyper-parameters in the parameter config file have been set to 'None' a script
		will now try and predict fitting parameters for the given analysis map.
		Ideally this will circumvent a hyper-parameter search with multiple combinations and instead give a targeted
		prediction about optimal hyper-parameters to use.
		Note that this method is still a WIP and unfathomably slow for large orig datafiles.
		See the actual prediction method for more information.

		"""

		heuristicParameters = {}
		missingParameters = False

		for netType in ["regression", "classification"]:
			for key, value in self.hyperParameterRaw[netType].items():
				if value == None or value == [None]:
					missingParameters = True
					break

			if missingParameters:
				timestamp = time()
				logger.info("Missing hyperparameters found. Predicting optimal model architectures..")
				heuristicParameters = makeHeuristicPredictions(self.hyperParameterRaw[netType], netType)
				logger.info("Done. (%ss)" % (round(time() - timestamp, 3)))

			for key, value in heuristicParameters.items():
				missingValue = self.hyperParameterRaw[netType][key]
				if missingValue == None or missingValue == [None]:
					self.hyperParameterRaw[netType][key] = value


	def _formatHyperParameter(self, netType):
		self.hyperParameter[netType] = HyperParameter(self.hyperParameterRaw[netType])


	def _loadDatasetBuilder(self):
		self.datasetBuilder = DatasetBuilder(logger, self.paramDatabase, self.paramDataset, self.paramDevice["device"])


	def _generateDataset(self, netType):

		self.dataset = {}

		if netType == "classification":
			datasetFull = self.datasetBuilder.generateNewSet(netType, sampleSize = 100)
		else:
			datasetFull = self.datasetBuilder.generateNewSet(netType)
		splitSet = datasetFull.split(self.paramDataset["sampleSplit"])
		
		self.dataset["full"] 		= datasetFull
		self.dataset["training"] 	= splitSet[0]
		self.dataset["testing"] 	= splitSet[1]
		self.dataset["validation"] 	= splitSet[2]


	def generateNeuralNetwork(self):

		"""


		"""

		t0 = time()
		
		self._loadDatasetBuilder()
		self._makeHeuristicPredictions()

		### QUICK FIX TO FOCUS ON ONE MODEL ONLY ###
		for netType in ["regression", "classification"]:

			self._formatHyperParameter(netType)
			logger.info("%s hyperparameter combination(s) loaded.." % len(self.hyperParameter[netType]))

			timestamp = time()
			logger.info("Generating %s dataset with %s samples.." % (netType, self.paramDataset["sampleSize"]))
			self._generateDataset(netType)
			logger.info("Done. (%ss)" % (round(time() - timestamp, 3)))

			self.modelTrainer[netType] = Trainer(self.paramDatabase, self.hyperParameter[netType], self.dataset, self.paramDevice, netType)
			timestamp = time()

			self.modelTrainer[netType].findBestModel()

			if self.paramAnalysis["logFile"]:
				self.saveResultsToLog(netType)
			if self.paramAnalysis["lossPlot"]:
				self.createLossPlot(netType)



		self.combinedModel = NN_combined(self.modelTrainer["regression"].winner["model"], None) #self.modelTrainer["classification"].winner["model"])

		logger.info("All done! Final network generated after %ss." % round(time()-t0, 3))

		self.saveModel()

		if True: #runPerformance:
			validater = Performance(self.parameters, "regression", validationSet = self.dataset["validation"])
			validater.evaluate()

		existingModel = None # LoadModel(...)

		#speedFactor = getSpeed(bestModel, expres, txName, trainerRegression.fullDataset)
		#bestModel.setSpeedFactor(speedFactor)

		
			#validateModel(model, expres, txName, massRange, sampleSize, netType, validationSet)


	
	def createLossPlot(self, netType):

		"""



		"""
		print("LOSSPLOT")

		fullPath = self.outputDir["loss"] + self.paramDatabase["txName"] + "_" + netType + "_lossPlot.png" #.eps

		x = [e+1 for e in range(len(self.modelTrainer[netType].winner["plotData"]["training"]))]
		y = self.modelTrainer[netType].winner["plotData"]["training"]
		z = self.modelTrainer[netType].winner["plotData"]["testing"]

		ID = self.paramDatabase["analysisID"]
		tx = self.paramDatabase["txName"]
		sr = self.paramDatabase["signalRegion"]
		loss = self.modelTrainer[netType].winner["config"]["lossFunction"]
		title = title = "Loss Per Epoch (loss func = %s) (%s) \nid = %s, tx = %s" % (loss, netType, ID, tx)

		if sr != None:
			title += ", sr = %s" % sr

		if netType == "regression": figId = 55
		else: figId = 54

		plt.figure(figId)
		plt.title(title, fontsize=20)
		plt.xlabel("Epochs")
		plt.ylabel("Loss")
		plt.plot(x, y, label = "training set")
		plt.plot(x, z, label = "testing set")
		plt.legend()
		plt.savefig(fullPath)
		logger.info("Lossplot saved in %s." % fullPath)


	def saveResultsToLog(self, netType):

		"""



		"""

		date = datetime.now()

		logData = sorted(self.modelTrainer[netType].logData, key=lambda lD: lD[0])

		fullPath = self.outputDir["log"] + self.paramDatabase["txName"] + "_" + netType + "_" + date.strftime("%d.%m.%Y-%H:%M:%S") + ".info"

		with open(fullPath, "a+") as file:
			for lD in logData:
				file.write("loss: %s\t%s\n" %(lD[0], str(lD[1])))

		logger.info("Logfile has been created. (%s)" % fullPath)


	def saveModel(self):

		fullPath = self.outputDir["model"] + self.paramDatabase["txName"] + ".pth"

		torch.save(self.combinedModel, fullPath)
		logger.info("Best performing model has been saved. (%s)" % fullPath)





class Trainer():

	"""
	Trainer object. Holds all information used during gridsearch for one specific map.

	:ivar expres: current experiment result
	:ivar txName: current topology
	:ivar netType: current network architecture: regression or classification (string)
	:ivar device: tells torch on which CPU or GPU to run (string)
	:ivar savePath: main directory where all output will be stored (string)
	:ivar inputDimension: number of SUSY particles of current topology (int)
	:ivar fullDataset: main dataset used for training, split into training, testing and validation (Dataset object)
					inputs and labels inside dataset are stored as torch tensors
	:ivar hyperParameter: dict class that holds all permuations of gridsearch parameters (Hyperparameter object)

	"""


	def __init__(self, paramDatabase, hyperParameter, dataset, paramDevice, netType):

		"""



		"""

		self.paramDatabase = paramDatabase

		self.hyperParameter = hyperParameter
		self.currentHyperParamConfig = None

		self.datasetFull 	= dataset["full"]
		self.trainingSet 	= dataset["training"]
		self.testSet 		= dataset["testing"]
		self.validationSet 	= dataset["validation"]
		self.inputDimension = self.datasetFull.inputDimension

		self.device = paramDevice["device"]
		self.cores = paramDevice["cores"]
		self.netType = netType

		self.logData = []
		self.winner = {"error": 1e10}
		

	def findBestModel(self):

		"""
		Loops over all hyperparameter configurations 
		and keeps track of the best current model.
		"""

		logger.info("Starting grid search for %s: %s (%s)" % (self.paramDatabase["analysisID"], self.paramDatabase["txName"], self.netType))

		for n in range(len(self.hyperParameter)):

			self.lossPerEpoch = {'training':[],'testing':[]}

			self.currentHyperParamConfig = self.hyperParameter[n]
			logger.info("Training model %d/%d .." %(self.currentHyperParamConfig["index"] + 1, len(self.hyperParameter)))
			self.runCurrentConfiguration()

			if self.winner["error"] > self.meanError:

				self.winner["model"]	= copy.deepcopy(self.model)
				self.winner["error"]   	= self.meanError
				self.winner["config"]  	= self.currentHyperParamConfig
				self.winner["logData"] 	= self.logData
				self.winner["plotData"]	= self.lossPerEpoch

				self.winner["model"].setValidationLoss(self.winner["error"])



	def _rerunWithWrongPredictionSubset(self, subset):

		"""
		Second training run with with 'subset' dataset. Mainly used for regression

		"""

		training, testing = subset.split([0.8,0.2])
		#self.trainModel(trainingSet = training, testSet = testing)

		#optimizer = loadOptimizer(self.currentHyperParamConfig["optimizer"], self.model, self.currentHyperParamConfig["learnRate"]) #*0.1
		self.trainModel(epochNum = int(self.currentHyperParamConfig["epochNum"]*0.5), trainingSet = training, testSet = testing) #MSErel


	def _getWrongPredictionsSubset(self, tolerance = 0.05):

		"""
		If model performance is weak after training a subset of training data can be built consisting
		of wrongly predicted points for a second training run.

		:param tolerance: relative error threshold for which a given point is considered as wrongly predicted

		"""

		if self.netType == "classification":

			subset = []

			for n in range(len(self.datasetFull.labels)):

				l = self.datasetFull.labels[n].item()
				p = self.model(self.datasetFull.inputs[n]).item()

				if not ((p < 0.5 and l == 0) or (p >= 0.5 and l == 1)):

					newPoint = [inputs.item() for inputs in self.datasetFull.inputs[n]]
					newPoint.append(self.datasetFull.labels[n].item())
					subset.append(newPoint)

			newDataset = Data(subset, self.inputDimension, self.device)
			return newDataset
			

		### TEMPORARY LLP FIX FOR RESCALED LABELS
	
		subset = []
		
		for n in range(len(self.datasetFull.labels)):

			#l = unscaleWidth(self.fullDataset.labels[n].item() - 0.1).asNumber(GeV)
			#p = unscaleWidth(self.model(self.fullDataset.inputs[n]).item() - 0.1).asNumber(GeV)
			l = self.datasetFull.labels[n].item()
			p = self.model(self.datasetFull.inputs[n]).item()
			if l < 1e-5: l = 0
			if p < 1e-5: p = 0
			if l > 0: e = np.sqrt((( p - l ) / l)**2)
			else: e = p


			if e > 0.05 or random.random() < 0.1:
				newPoint = [inputs.item() for inputs in self.datasetFull.inputs[n]]
				newPoint.append(self.datasetFull.labels[n].item())
				subset.append(newPoint)

		newDataset = Data(subset, self.inputDimension, self.device)
		return newDataset
	
		###

		relError = MSErel(self.model(self.fullDataset.inputs), self.fullDataset.labels, reduction = None)

		subset = []
		for n in range(len(relError)):
			if relError[n].item() > tolerance:
				newPoint = [inputs.item() for inputs in self.fullDataset.inputs[n]]
				newPoint.append(self.fullDataset.labels[n].item())
				subset.append(newPoint)

		newDataset = Data(subset, self.inputDimension, self.device)
		return newDataset


	def runCurrentConfiguration(self, secondRun = True):

		"""
		Parent method of actual training. Handles training differencies between
		regression and classification and keeps track of current model's error on
		the validation set.

		"""

		if self.currentHyperParamConfig == None:
			logger.error("No hyperparameter configuration specified for training.")
			return

		self.model = createNet(self.currentHyperParamConfig, self.datasetFull, self.netType).double().to(self.device)
		self.trainModel()

		if self.netType == "regression" and secondRun:
			subset = self._getWrongPredictionsSubset()
			logger.info("Rerunning training with new dataset: %s points" %len(subset))
			self._rerunWithWrongPredictionSubset(subset)

		if self.netType == "classification":

			predictions, labels = self.model(self.validationSet.inputs).detach().numpy(), self.validationSet.labels.detach().numpy()
			self.model._delimiter = minimize(self._findDelimiter, 0.5, args=(predictions, labels), method="Powell").x.tolist()
			#lossFunction = loadLossFunction(self.currentHyperParamConfig["lossFunction"], self.device)
			#self.meanError = lossFunction(self.model(self.validationSet.inputs), self.validationSet.labels)

		self.meanError = getModelError(self.model, self.validationSet, self.netType)[0]
		
		logger.info("Done! Mean error on validation set: %s" %round(self.meanError.item(), 3))
		self.logData.append([round(self.meanError.item(), 3), self.currentHyperParamConfig])





	def trainModel(self, optimizer = None, lossFunction = None, batchSize = 0, epochNum = 0, trainingSet = None, testSet = None):

		"""
		Core training method. Loads necessary torch classes and training parameters and
		updates the models' weights and biases via back propagation.
		Will save the model with the lowest error on the test set over all training epochs.

		"""

		if trainingSet == None:  trainingSet  = self.trainingSet
		if testSet == None: 	 testSet 	  = self.testSet
		if batchSize == 0: 		 batchSize 	  = self.currentHyperParamConfig["batchSize"]
		if epochNum == 0: 		 epochNum 	  = self.currentHyperParamConfig["epochNum"]
		if optimizer == None: 	 optimizer 	  = loadOptimizer(self.currentHyperParamConfig["optimizer"], self.model, self.currentHyperParamConfig["learnRate"])
		if lossFunction == None: lossFunction = loadLossFunction(self.currentHyperParamConfig["lossFunction"], self.device)

		trainloader = DataLoader(trainingSet, batch_size = batchSize, shuffle = True, num_workers = self.cores)

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
							
				self.lossPerEpoch['training'].append(trainingLoss.item())
				self.lossPerEpoch['testing'].append(testLoss.item())
									
				if testLoss < bestLossLocal:
					bestLossLocal  = testLoss
					bestModelLocal = copy.deepcopy(self.model)
					#bestEpochLocal = epoch
			

			if logger.level <= 20:
				print("\repoch: %d/%d | testloss: %s" %(epoch+1,epochNum, round(testLoss.item(), 5)), end = "" if epoch+1 < epochNum else "\n")

		self.model = bestModelLocal


	def _findDelimiter(self, delimiter, predictions, labels):

		"""
		Method that converts float output of classification predictions into binary 0,1 values and
		assigns an error value to the given dataset. Should not be used outside of the optimization process of
		classification networks after training (therefore semi private).

		:param delimiter: cutoff value to split float model predictions into 0s and 1s

		"""

		right, wrong = 0, 0

		for i in range(len(predictions)):

			if ( labels[i] == 0. and predictions[i] < delimiter ) or ( labels[i] == 1. and predictions[i] > delimiter ):
				right += 1
			else:
				wrong += 1

		return float(wrong)/float(right+wrong)
	
					

if __name__=='__main__':

	from readParameter import readParameterFile
	from configparser import ConfigParser
	from datetime import datetime
	from time import time

	ap = argparse.ArgumentParser(description="Trains and finds best performing neural networks for database analyses via hyperparameter search")
	ap.add_argument('-p', '--parfile', 
			help='parameter file', default='nn_parameters.ini')
	ap.add_argument('-l', '--log', 
			help='specifying the level of verbosity (error, warning, info, debug)',
			default = 'info', type = str)
           
	args = ap.parse_args()


	numeric_level = getattr(logging,args.log.upper(), None)
	logger.setLevel(level=numeric_level)
	
    
	if not os.path.isfile(args.parfile):
		logger.error("Parameters file %s not found" %args.parfile)
	else:
		logger.info("Reading validation parameters from %s" %args.parfile)

	fileParameters = readParameterFile(logger, args.parfile)

	#import matplotlib.pyplot as plt
	from system.dataset import *
	from system.initnet import *
	from system.auxiliaryFunctions import *
	from getPerformance import *
	from system.getTimings import *
	from system.getInterpolationError import *
	from scipy.optimize import minimize
	from smodels.theory.auxiliaryFunctions import unscaleWidth
	from torch.utils.data import DataLoader as DataLoader

	parameters = {}
	parameters["database"] 		 = {}
	parameters["path"] 			 = fileParameters["path"]
	parameters["dataset"] 		 = fileParameters["dataset"]
	parameters["device"] 		 = fileParameters["device"]
	parameters["analysis"] 		 = fileParameters["analysis"]
	parameters["hyperParameter"] = fileParameters["hyperParameter"]

	for analysisID in fileParameters["database"]["analysisID"]:
		for txName in fileParameters["database"]["txName"]:
			for daSel in fileParameters["database"]["dataselector"]:
				for signalRegion in fileParameters["database"]["signalRegion"]:

					parameters["database"]["analysisID"]   = analysisID
					parameters["database"]["txName"]	   = txName
					parameters["database"]["dataSelector"] = daSel
					parameters["database"]["signalRegion"] = signalRegion
					
					modelTrainer = TrainerWrapper(parameters)
					modelTrainer.generateNeuralNetwork()

	

