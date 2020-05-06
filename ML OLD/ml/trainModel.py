#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#import sys
#sys.path.append('../../smodels/')

import logging,sys,os
import subprocess
import copy
from time import time
import matplotlib.pyplot as plt
#plt.switch_backend('agg')
import torch
from torch.utils.data import DataLoader as DataLoader
from math import sqrt as sqrt
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
import random, string

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)


def findDelimiter(delimiter, predictions, labels):

	wrong = 0
	right = 0

	for i in range(len(predictions)):

		if ( labels[i] == 0. and predictions[i] < delimiter ) or ( labels[i] == 1. and predictions[i] > delimiter ):
			right += 1
		else:
			wrong += 1

	return float(wrong)/float(right+wrong)


def createLossPlot(expres, txName, netType, lossPerEpoch):

	savePath = expres.path + "/performance/"
	fileName = txName + "_" + netType + "_lossPlot.eps"

	#replace databasePath TEMPORARY
	for i in range(len(savePath)):
		if savePath[i:i+8] == 'database':
			savePath = savePath[:i] + 'database-ml' + savePath[i+8:]

	#pointless when merged with real database
	if not os.path.exists(savePath):
		os.makedirs(savePath)

	plt.figure(5)
	plt.title('Loss Function', fontsize=20)
	plt.xlabel('Epochs')
	plt.ylabel('Error')
	plt.plot([e for e in range(len(lossPerEpoch['training']))], lossPerEpoch['training'], label = 'Train Loss')
	plt.plot([e for e in range(len(lossPerEpoch['testing']))], lossPerEpoch['testing'], label = 'Test Loss')
	plt.legend()
	plt.savefig(savePath + fileName)
	#plt.savefig( + "/loss{}.eps".format(j), format = 'eps')



def saveResultsToLog(model, expres, txName, netType, hyperParameter, relativeValidationError, logData, done):

	date = datetime.now()
	logData.append([round(relativeValidationError.item(), 3), hyperParameter])

	if not done:
		return logData

	logData = sorted(logData, key=lambda lD: lD[0])
	#logData = sorted(logData)

	savePath = expres.path + "/logs/"
	fileName = txName + "_" + netType + "_" + date.strftime("%d.%m.%Y-%H:%M:%S")

	#replace databasePath TEMPORARY
	for i in range(len(savePath)):
		if savePath[i:i+8] == 'database':
			savePath = savePath[:i] + 'database-ml' + savePath[i+8:]

	#pointless when merged with real database
	if not os.path.exists(savePath):
		os.makedirs(savePath)

	with open(savePath + fileName, "a+") as file:
		for lD in logData:
			file.write("loss: %s\t%s\n" %(lD[0], str(lD[1])))

	logger.info("All done! Results stored in %s" %(savePath + fileName))

	return logData



def saveModelInfo(model, expres, txName, netType, hyperParameter, relativeValidationError):

	savePath = expres.path + "/"
	fileName = txName + "_" + netType + ".info"

	#replace databasePath TEMPORARY
	for i in range(len(savePath)):
		if savePath[i:i+8] == 'database':
			savePath = savePath[:i] + 'database-ml' + savePath[i+8:]

	with open(savePath + fileName, "w+") as file:

		date = datetime.now()
		file.write("created on:\t%s\n" %(date.strftime("%d.%m.%Y-%H:%M:%S")))
		file.write("implemented by:\t%s\n" %("Philipp Neuhuber")) # NYI
		file.write("relative error:\t%s%%\n\n" %(round(relativeValidationError.item()*100., 3)))
		file.write("%s\n\n" % str(model))
		file.write("hyperParameters:\n---\n")
		for key in hyperParameter: file.write("%s: %s\n" %(key, hyperParameter[key]))
		file.write("---")
			





def trainModel(model, optimizer, lossFunction, batchSize, epochNum, trainingSet, testSet, lossPlot = True):

	trainloader = DataLoader(trainingSet, batch_size = batchSize, shuffle = True, num_workers = 6)

	bestLoss, bestEpoch, bestModel  = 1e5, 0, copy.deepcopy(model)
	lossPerEpoch = {'training':[],'testing':[]}

	for epoch in range(epochNum):

		model.train()

		for i, data in enumerate(trainloader):  

			inputs, labels = data[0], data[1]
			loss = lossFunction(model(inputs), labels)
			optimizer.zero_grad()
			loss.backward()
			optimizer.step()

		model.eval()

		with torch.no_grad():
		
			trainingLoss = lossFunction(model(trainingSet.inputs), trainingSet.labels)
			testLoss = lossFunction(model(testSet.inputs), testSet.labels)
						
			if lossPlot:
				lossPerEpoch['training'].append(trainingLoss)
				lossPerEpoch['testing'].append(testLoss)
								
			if testLoss < bestLoss:
				bestLoss  = testLoss
				bestModel = copy.deepcopy(model)
				#bestEpoch = epoch+1

		print("\repoch: %d/%d | testloss: %s" %(epoch+1,epochNum, round(testLoss.item(), 3)), end = "", flush = True)

	return [bestModel, lossPerEpoch]




def main(expres, txName, netType, overwrite, hyperParameter, sampleSize, massRange, sampleSplit, device, logFile, lossPlot, runPerformance):

	analysis = expres.globalInfo.getInfo('id')
	print("\n\n\tStarting new grid search\n\t________________\n\tanalysis: {}\n\ttopology: {}\n\tnettype:  {}\n\n".format(analysis, txName, netType))

	logger.info("Generating dataset")
	dataset = generateDataset(expres, txName, massRange, sampleSize, netType, device)
	inputDimension = dataset.inputDimension
	trainingSet, testSet, validationSet = dataset.split(sampleSplit)

	currentParameterSetNum = 0
	logData = []
	bestError = 1e5
	bestModel = None

	for i in range(len(hyperParameter)):

		currentHyperParamConfig = hyperParameter[i]
		optimizer = currentHyperParamConfig["optimizer"]
		learnRate = currentHyperParamConfig["learnRate"]
		lossFunction = currentHyperParamConfig["lossFunction"]
		batchSize = currentHyperParamConfig["batchSize"]
		epochNum = currentHyperParamConfig["epochNum"]
		rescaleMethod = currentHyperParamConfig["rescaleMethod"]

		if rescaleMethod == "standardScore":
			parameter = {"mean": dataset.mean[0], "std": dataset.std[0]}
		else: parameter = None	

		rescaleParameter = {"method": rescaleMethod, "parameter": parameter}

		currentParameterSetNum += 1
		logger.info("Training model %d/%d .." %(currentParameterSetNum,len(hyperParameter)))

		model = createNet(currentHyperParamConfig, inputDimension, netType, rescaleParameter).to(device)
		optimizer = loadOptimizer(optimizer, model, learnRate)
		lossFunction = loadLossFunction(lossFunction, device)

		model, lossPerEpoch = trainModel(model, optimizer, lossFunction, batchSize, epochNum, trainingSet, testSet, lossPlot)

		if netType == "regression":

			meanError = MSErel(model(validationSet.inputs), validationSet.labels)
			print("\rDone! Total relative error on validation set: %s" %round(meanError.item(), 3))

			relError = MSErel(model(validationSet.inputs), validationSet.labels, reduction = None)
			updatedDataSet = []
			for n in range(len(relError)):
				if relError[n].item() > 0.05:
					newData = [inputs.item() for inputs in validationSet.inputs[n]]
					newData.append(validationSet.labels[n].item())
					#updatedDataSet.append([validationSet.inputs[n][0].item(), validationSet.inputs[n][1].item(), validationSet.labels[n].item()])
					updatedDataSet.append(newData)

			updatedDataSet = Data(updatedDataSet, inputDimension, device)
			logger.info("Rerunning training with new dataset: %s" %len(updatedDataSet))
			trainingNew, testNew = updatedDataSet.split([0.8,0.2])
			optimizer = loadOptimizer(currentHyperParamConfig["optimizer"], model, learnRate*0.1)
			model, lossPerEpochNew = trainModel(model, optimizer, MSErel, batchSize, int(epochNum*0.5), trainingNew, testNew, lossPlot)

			lossPerEpoch['training'] += lossPerEpochNew['training']
			lossPerEpoch['testing'] += lossPerEpochNew['testing']
			
			meanError = MSErel(model(validationSet.inputs), validationSet.labels)
			print("\rSecond run: Done! Total relative error on validation set: %s" %round(meanError.item(), 3))

		else:

			model._delimiter = minimize(findDelimiter, 0.5, args=(model(validationSet.inputs).detach().numpy(), validationSet.labels.detach().numpy()), method="Powell").x.tolist()
			meanError = lossFunction(model(validationSet.inputs), validationSet.labels)
			print("\rDone! Mean error on validation set: %s" %round(meanError.item(), 3))

		if logFile:
			logData = saveResultsToLog(model, expres, txName, netType, currentHyperParamConfig, meanError, logData, done = (i == len(hyperParameter) - 1))

		if meanError < bestError:
			bestError  = meanError
			bestModel  = copy.deepcopy(model)
			bestConfig = currentHyperParamConfig
		
	if lossPlot:
		createLossPlot(expres, txName, netType, lossPerEpoch)

	if runPerformance:
		validateModel(model, expres, txName, massRange, sampleSize, netType, validationSet)

	if overwrite == "always": saveNewModel = True
	elif overwrite == "outperforming":
		savedModel = loadModel(expres, txName, netType)
		if savedModel == None: saveNewModel = True
		else: saveNewModel = MSErel(savedModel(validationSet.inputs), validationSet.labels) > meanError
	else: saveNewModel = False

	if saveNewModel:
		saveModel(bestModel, expres, txName, netType)
		saveModelInfo(bestModel, expres, txName, netType, bestConfig, meanError)
					

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
	logFile = parser.getboolean("analysis", "logFile")
	lossPlot = parser.getboolean("analysis", "lossPlot")
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
		logger.info(netType + ": total of %d hyperparameter combinations have been found." %len(hyperParameter))

		for txName in txNames:
			if GetModel(expres, txName, netType) == None or overwrite != 'never':
				main(expres, txName, netType, overwrite, hyperParameter, sampleSize, massRange, sampleSplit, device, logFile, lossPlot, runPerformance)

			#else: print("Ignoring id: {}, tx: {} [{}] -> overwrite set to 'False'.".format(analysisId, tx, nt))
	


