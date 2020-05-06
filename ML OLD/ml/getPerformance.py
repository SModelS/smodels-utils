#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from system.dataset import *
from system.initnet import *
import os, sys, torch
import matplotlib.pyplot as plt
import numpy as np
import argparse, logging
from configparser import ConfigParser

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)


def validateRegression(model, expres, txName, massRange, sampleSize, validationSet, showPlots, savePlots):

	relError = MSErel(model(validationSet.inputs), validationSet.labels, reduction = None)
	meanRelError = torch.mean(relError).item()

	numBins = 15
	targetError = 0.05
	correctBin = [0 for n in range(numBins)]
	wrongBin = [0 for n in range(numBins)]
	errorBin = [0. for n in range(numBins)]
	scatterCorrect = []
	scatterWrong = []

	binRange = max(validationSet.labels) / numBins

	for i in range(len(relError)):
		
		if relError[i] < targetError:
			
			scatterCorrect.append(validationSet[i][0:-1])
			for n in range(numBins):
				if validationSet.labels[i] < binRange * (n+1) or n == numBins-1:
					correctBin[n] += 1
					break

		else:

			scatterWrong.append(validationSet[i][0:-1])
			for n in range(numBins):
				if validationSet.labels[i] < binRange * (n+1) or n == numBins-1:
					wrongBin[n] += 1
					break

	
	for i in range(numBins):
		sumBin = correctBin[i] + wrongBin[i]
		if sumBin > 0: errorBin[i] = float(correctBin[i]) / float(sumBin)
		
	savePath = expres.path + "/performance/"

	#replace databasePath TEMPORARY
	for i in range(len(savePath)):
		if savePath[i:i+8] == 'database':
			savePath = savePath[:i] + 'database-ml' + savePath[i+8:]

	#pointless when merged with real database
	if not os.path.exists(savePath):
		os.makedirs(savePath)
	
	plt.figure(5)
	plt.title('id: {}, tx: {}, relError: {:4.2f}%  (regression)'.format(expres.globalInfo.getInfo('id'),txName, meanRelError*100.), fontsize=14)
	plt.bar([binRange*n for n in range(numBins)], errorBin, width=int(binRange*0.9))
	#for n in range(numBins): plt.bar(width=int(binRange*0.9)*len(correctBin[n])/len(relError)))
	plt.xlabel('xsec [fb]')
	plt.ylabel('correct/total predicted')
	fileName = txName + "_regression_bins.eps"
	if savePlots: plt.savefig(savePath + fileName)
	

	plt.figure(1)
	plt.title('id: {}, tx: {}, relError: {:4.2f}%  (regression)'.format(expres.globalInfo.getInfo('id'),txName, meanRelError*100.), fontsize=14)
	plt.xlabel('mass mother [GeV]')
	plt.ylabel('mass daughter [GeV]')
	pltcor = plt.scatter([sC[0][0].item() for sC in scatterCorrect], [sC[0][1].item() for sC in scatterCorrect], color = 'green')
	pltwrg = plt.scatter([sC[0][0].item() for sC in scatterWrong], [sC[0][1].item() for sC in scatterWrong], color = 'red')
	plt.legend((pltcor, pltwrg), ('correct', 'wrong'), scatterpoints=1, loc='upper right', ncol=1, fontsize=8)
	fileName = txName + "_regression_scatterPlot.eps"
	if savePlots:plt.savefig(savePath + fileName)
	if showPlots: plt.show()




def validateClassification(model, expres, txName, massRange, sampleSize, validationSet, showPlots, savePlots):

	delimiter = 0.5
	onHull_correct = []
	onHull_wrong = []
	offHull_correct = []
	offHull_wrong = []

	lossFunction = torch.nn.BCELoss(reduction = 'none')
	error = lossFunction(model(validationSet.inputs), validationSet.labels)

	for i in range(len(validationSet)):

		inputs = validationSet.inputs[i]
		predi = model(inputs)
		label = validationSet.labels[i]

		if label == 0.:
			if predi == 0.:
				offHull_correct.append(inputs)
			else:
				offHull_wrong.append(inputs)
		elif label == 1.:
			if predi == 1.:
				onHull_correct.append(inputs)
			else:
				onHull_wrong.append(inputs)

	onHull_correct_total = len(onHull_correct)
	onHull_wrong_total = len(onHull_wrong)
	offHull_correct_total = len(offHull_correct)
	offHull_wrong_total = len(offHull_wrong)
	onHull_total = onHull_correct_total + onHull_wrong_total
	offHull_total = offHull_correct_total + offHull_wrong_total
	samples_total = onHull_total + offHull_total

	onShell  = "%s / %s (%s%%)" % (onHull_correct_total, onHull_total, round(100.*onHull_correct_total/onHull_total, 3))
	offShell = "%s / %s (%s%%)" % (offHull_correct_total, offHull_total, round(100.*offHull_correct_total/offHull_total, 3))
	total    = "%s / %s (%s%%)" % (onHull_correct_total + offHull_correct_total, samples_total, round(100.*(onHull_correct_total + offHull_correct_total)/samples_total, 3))

	print("onShell:   %s" %onShell)
	print("offShell:  %s" %offShell)
	print("total:     %s" %total)
	print("delimiter: %s" % (round(model._delimiter, 3)))


	savePath = expres.path + "/performance/"

	#replace databasePath TEMPORARY
	for i in range(len(savePath)):
		if savePath[i:i+8] == 'database':
			savePath = savePath[:i] + 'database-ml' + savePath[i+8:]

	#pointless when merged with real database
	if not os.path.exists(savePath):
		os.makedirs(savePath)

	plt.figure(0)
	plt.title('id: {}, tx: {}  (classification) correct predictions: {}'.format(expres.globalInfo.getInfo('id'),txName, total), fontsize=14)
	plt.xlabel('mass mother [GeV]')
	plt.ylabel('mass daughter [GeV]')
	plt_cor_on = plt.scatter([oH[0].item() for oH in onHull_correct], [oH[1].item() for oH in onHull_correct], color = 'green')
	plt_cor_off = plt.scatter([oH[0].item() for oH in offHull_correct], [oH[1].item() for oH in offHull_correct], color = 'blue')
	plt_wrg_on = plt.scatter([oH[0].item() for oH in onHull_wrong], [oH[1].item() for oH in onHull_wrong], color = 'red')
	plt_wrg_off = plt.scatter([oH[0].item() for oH in offHull_wrong], [oH[1].item() for oH in offHull_wrong], color = 'orange')
	plt.legend((plt_cor_on, plt_cor_off, plt_wrg_on, plt_wrg_off), ('on hull correct', 'off hull correct', 'should be on hull', 'should be off hull'), scatterpoints=1, loc='upper right', ncol=1, fontsize=8)
	fileName = txName + "_classification_scatterPlot.eps"
	if savePlots:plt.savefig(savePath + fileName)
	plt.show()





def validateModel(model, expres, txName, massRange, sampleSize, netType, validationSet, showPlots = False, savePlots = True):

	if netType == "regression":
		validateRegression(model, expres, txName, massRange, sampleSize, validationSet, showPlots, savePlots)
	else:
		validateClassification(model, expres, txName, massRange, sampleSize, validationSet, showPlots, savePlots)


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
	txName = parser.get("database", "txNames").split(",")[0]

	#Configure dataset generated for training
	sampleSize = float(parser.get("dataset", "sampleSize"))
	massRange = parser.get("dataset", "massRange").split(",")
	massRange = [float(mR) for mR in massRange]

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
	netType = parser.get("options", "whichNN")
	if not ( netType == "regression" or netType == "classification"):
		logger.error("Parameter nettype: for performance, only 'regression' or 'classification' allowed")

	expres = Database(databasePath, progressbar = True)
	expres = expres.getExpResults(analysisIDs = analysisID, useSuperseded = True, useNonValidated = True)[0]
	validationSet = generateDataset(expres, txName, massRange, sampleSize, netType, device)
	model = loadModel(expres, txName, netType)

	validateModel(model, expres, txName, massRange, sampleSize, netType, validationSet, showPlots = True, savePlots = False)
