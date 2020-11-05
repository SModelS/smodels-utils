#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. module:: trainModel.py
   :synopsis: run gridsearch to train optimal neural networks for smodels-database maps
.. moduleauthor:: Philipp Neuhuber <ph.neuhuber@gmail.com>

"""

import torch
from copy import deepcopy
from system.initnet import createNet
from system.auxiliaryFunctions import loadLossFunction, loadOptimizer, getModelError
from torch.utils.data import DataLoader
from smodels.tools.smodelsLogging import logger

#import logging,sys,os
#import numpy,argparse
#import torch,random,copy
#from datetime import datetime
#from time import time


#from configparser import ConfigParser

#FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
#logging.basicConfig(format=FORMAT)
#logger = logging.getLogger(__name__)

#import subprocess
#plt.switch_backend('agg')
#torch.multiprocessing.set_start_method("spawn")


class ModelTrainer():

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


	def __init__(self, parameter, dataset):

		"""
		Example usage of neural network training methods.
		Reads the parameter file and trains networks for all
		maps it can find.

		:param parameter: Custom parameter dictionary holding all meta and hyper param informations
		:param dataset: dict of customized torch Dataset classes for training, testing and validation
		"""

		self.dataset = dataset
		self.type = parameter["nettype"]
		self.hyper = parameter[self.type]

		self.device = parameter["device"]
		self.cores = parameter["cores"]

		self.full_dim = parameter["txNameData"].full_dimensionality
		self.rescaleParameter = dataset["rescaleParameter"]
		self.scaler = dataset["scaler"]

		self.dataset 	= dataset["full"]
		self.training 	= dataset["training"]
		self.testing	= dataset["testing"]
		self.validation	= dataset["validation"]

		#self.paramDatabase = paramDatabase
		#self.hyperParameter = hyperParameter
		#self.currentHyperParamConfig = None
		#self.inputDimension = self.datasetFull.inputDimension
		#self.device = paramDevice["device"]
		#self.cores = paramDevice["cores"]
		

		self.logData = []
		self.winner = {"error": 1e10}

		#self.scaler = scaler
		

	def run(self):

		"""
		Loops over all hyperparameter configurations 
		and keeps track of the best current model.

		:return winner: result dict for best performing model, containing torch model, error and hyperparam config

		"""

		##logger.info("Starting grid search for %s: %s (%s)" % (self.paramDatabase["analysisID"], self.paramDatabase["txName"], self.netType))

		self.hyper.resetIndex
		while(self.hyper.incrIndex):

			#self.epochLoss = {'training':[],'testing':[]}

			logger.info("training with hyperparam config %d/%d .." %(self.hyper.index + 1, len(self.hyper)))

			self.runCurrentConfiguration()

			if self.winner["error"] > self.meanError:

				self.winner["model"]	= deepcopy(self.model)
				self.winner["error"]   	= self.meanError
				self.winner["config"]  	= self.hyper[-1]
				#self.winner["logData"] 	= self.logData
				#self.winner["plotData"]	= self.lossPerEpoch

				self.winner["model"].setValidationLoss(self.winner["error"])

		return self.winner



	def runCurrentConfiguration(self, secondRun = True):

		"""
		Parent method of actual training. Handles training differencies between
		regression and classification and keeps track of current model's error on
		the validation set.

		:param secondRun (optional): rerun model training with subset of inaccurate dataset predictions
		"""

		self.model = createNet(self.hyper[-1], self.rescaleParameter, self.scaler, self.full_dim, self.type).double().to(self.device)
		self.trainModel()

		if self.type == "regression" and secondRun:
			subset = self._getWrongPredictions()
			logger.debug("subset length: %s" %len(subset))
			self.trainModel(training = subset)
		
		self.meanError = getModelError(self.model, self.validation, self.type)[0]

		#if self.netType == "regression" and secondRun:
		#	subset = self._getWrongPredictionsSubset()
		#	logger.info("Rerunning training with new dataset: %s points" %len(subset))
		#	self._rerunWithWrongPredictionSubset(subset)

		#if self.netType == "classification":

		#	predictions, labels = self.model(self.validationSet.inputs).detach().numpy(), self.validationSet.labels.detach().numpy()
		#	self.model._delimiter = minimize(self._findDelimiter, 0.5, args=(predictions, labels), method="Powell").x.tolist()
		#	#lossFunction = loadLossFunction(self.currentHyperParamConfig["lossFunction"], self.device)
		#	#self.meanError = lossFunction(self.model(self.validationSet.inputs), self.validationSet.labels)

		
		
		#logger.info("Done! Mean error on validation set: %s" %round(self.meanError.item(), 3))
		#self.logData.append([round(self.meanError.item(), 3), self.currentHyperParamConfig])





	def trainModel(self, optimizer = None, lossFunction = None, batchSize = 0, epochNum = 0, training = None, testing = None):

		"""
		Core training method. Loads necessary torch classes and training parameters and
		updates the models' weights and biases via back propagation.
		Will save the model with the lowest error on the test set over all training epochs.

		"""

		if training == None:  	training	  = self.training
		if testing == None: 	 testing 	  = self.testing
		if batchSize == 0: 		 batchSize 	  = self.hyper["batchSize"] #self.currentHyperParamConfig
		if epochNum == 0: 		 epochNum 	  = self.hyper["epochNum"]  #self.currentHyperParamConfig
		if optimizer == None: 	 optimizer 	  = loadOptimizer(self.hyper["optimizer"], self.model, self.hyper["learnRate"])
		if lossFunction == None: lossFunction = loadLossFunction(self.hyper["lossFunction"], self.device)

		trainloader = DataLoader(training, batch_size = batchSize, shuffle = True, num_workers = self.cores)

		bestLossLocal, bestEpochLocal, bestModelLocal  = 1e5, 0, deepcopy(self.model)

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
			
				trainingLoss = lossFunction(self.model(training.inputs), training.labels)
				testingLoss = lossFunction(self.model(testing.inputs), testing.labels)
							
				#self.lossPerEpoch['training'].append(trainingLoss.item())
				#self.lossPerEpoch['testing'].append(testingLoss.item())
									
				if testingLoss < bestLossLocal:
					bestLossLocal  = testingLoss
					bestModelLocal = deepcopy(self.model)
					#bestEpochLocal = epoch
			

			#if logger.level <= 20:
			#	print("\repoch: %d/%d | testloss: %s" %(epoch+1,epochNum, round(testingLoss.item(), 5)), end = "" if epoch+1 < epochNum else "\n")
			print("\repoch: %d/%d | testloss: %s" %(epoch+1,epochNum, round(testingLoss.item(), 5)), end = "" if epoch+1 < epochNum else "\n")

		self.model = bestModelLocal



	def _getWrongPredictions(self):

		whichset = self.dataset #self.training

		from system.dataset import Data
		error = getModelError(self.model, whichset, self.type, returnMean = False)
		subset = []

		for n,e in enumerate(error):

			if e > 0.05:
				raw = [i.item() for i in whichset.inputs[n]]
				raw.append(whichset.labels[n].item())
				subset.append(raw)

		subset = Data(subset, self.full_dim, self.device)
		return subset

















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
	
					




