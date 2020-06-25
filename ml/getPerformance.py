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


class Performance():

	def __init__(self, expres, txName, SR, sampleSize, massRange, netType, showPlots = True, savePlots = True):

		"""


		"""

		self.expres = expres
		self.txName = txName
		#self.dataselector = dataselector
		self.SR = SR
		self.showPlots = showPlots
		self.savePlots = savePlots
		self.netType = netType
		self.model = loadModel(expres, txName)[netType]

		print(loadModel(expres, txName)["regression"])
		print(loadModel(expres, txName)["classification"])

		# TEMPORARY replace databasePath
		dbPath = expres.path
		for i in range(len(dbPath)):
			if dbPath[i:i+8] == 'database':
				dbPath = dbPath[i:]
				break
		self.savePath = os.getcwd() + "/" + dbPath + "/performance/"
		if not os.path.exists(self.savePath): os.makedirs(self.savePath)
		# ---

		self.validationSet = generateDataset(expres, txName, SR, massRange, sampleSize, netType, "cpu")


	def evaluate(self):

		"""


		"""

		if self.netType == "regression":

			self.error = torch.sqrt(MSErel(self.model(self.validationSet.inputs), self.validationSet.labels, reduction = None))
			self.meanError = torch.mean(self.error).item()
			self.getBins()
			self.validateRegression()

		else:

			lossFunction = torch.nn.BCELoss(reduction = 'none')
			self.meanError = lossFunction(self.model(self.validationSet.inputs), self.validationSet.labels)
			self.validateClassification()

		if self.showPlots: plt.show()
		

	def getBins(self, binNum = 15):

		#correctBin = [0 for n in range(binNum)]
		#wrongBin = [0 for n in range(binNum)]
		#errorBin = [0. for n in range(binNum)]
		#scatterCorrect = []
		#scatterWrong = []

		binRange = 250.
		#binRange = max(self.validationSet.labels).item() / binNum
		#errorBin = [0. for i in range(binNum)]
		errorBin = [[] for i in range(binNum)]
		errorBinNum = [0 for i in range(binNum)]

		for i in range(len(self.error)):

			for n in range(binNum):
				if self.validationSet.labels[i] < binRange * (n+1) or n == binNum - 1:
					#errorBin[n] += self.error[i].item()
					errorBin[n].append(self.error[i].item())
					#errorBinNum[n] += 1
					break

		#print(errorBin[:-1])
		mean = []
		std = []
		for i in range(binNum):
			if len(errorBin[i]) != 0:
				mean.append(np.mean(errorBin[i]))
				std.append(np.std(errorBin[i]))
			else:
				mean.append(0)
				std.append(0)

		#print(mean)
		#print(std)
		#for i in range(binNum):
		#	if errorBinNum[i] != 0:
		#		relE = errorBin[i] / errorBinNum[i]
		#	else: relE = 0
		#	errorBin[i] = relE

		labels = []
		for n in range(binNum):
			if n == binNum - 1: r = ">" + str(int(n*binRange)) + " fb"
			else: r = str(int(n*binRange)) + "-" + str(int((n+1)*binRange)) + " fb"
			labels.append("(" + r + ")" + " n=" + str(len(errorBin[n])))

		#labels = ["n=" + str(round(s, 3)) for s in sumBin]
		x = np.arange(len(errorBin))  # the label locations
		width = 0.5

		fig, ax = plt.subplots()
		rects = ax.bar(x, mean, width, yerr=std)

		ax.set_ylabel('mean error')
		ax.set_title('mean error sorted by xsecs (n = %s)' % len(self.validationSet))
		ax.set_xticks(x)
		ax.set_xticklabels(labels, rotation=45, rotation_mode="anchor", ha="right")
		#ax.legend()

		for rect in rects:
			height = round(rect.get_height(), 3)
			ax.annotate('{}'.format(height),
				xy=(rect.get_x() + rect.get_width() / 2, height), 
				xytext=(0, 3),  # 3 points vertical offset
				textcoords="offset points",
				ha='center', va='bottom')

		fig.tight_layout()
		if self.showPlots: plt.show()
		


	def validateRegression(self):

		"""


		"""

		predictions = self.model(self.validationSet.inputs)#.detach().tolist()
		labels = self.validationSet.labels#.detach().tolist()

		yaxis = 1
		if self.validationSet.inputDimension > 4:
			if max(self.validationSet.inputs[2]) - min(self.validationSet.inputs[2]) > 20:
				yaxis = 2

		X = [inputs[0].item() for inputs in self.validationSet.inputs]
		Y = [inputs[yaxis].item() for inputs in self.validationSet.inputs]
		E = [e.item() for e in self.error]

		plt.figure(2)
		plt.title('id: {}, tx: {}, relError: {:4.2f}%  (regression)'.format(self.expres.globalInfo.getInfo('id'), self.txName, self.meanError*100.), fontsize=14)
		plt.xlabel('mass mother [GeV]')
		plt.ylabel('mass daughter [GeV]')
		plt.scatter(X,Y, c=E, cmap='rainbow', vmin=0, vmax=1)
		plt.colorbar()
		plt.tight_layout()

		fileName = self.txName + "_regression_scatterPlot.eps"
		if self.savePlots:plt.savefig(self.savePath + fileName)
	
		origPoints = getExpresData(self.expres, self.txName, self.SR)
		
		X0 = [oP[0] for oP in origPoints]
		Y0 = [oP[1] for oP in origPoints]
		#plt.scatter(X0,Y0, marker="x", c="black", s=32)


	def validateClassification(self):

		"""


		"""

		delimiter = 0.5
		onHull_correct = []
		onHull_wrong = []
		offHull_correct = []
		offHull_wrong = []

		for i in range(len(self.validationSet)):

			inputs = self.validationSet.inputs[i]
			predi = self.model(inputs)
			label = self.validationSet.labels[i]

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

		error = round(100.*(1. - (onHull_correct_total + offHull_correct_total)/samples_total), 3)
		delim = round(self.model._delimiter, 3)

		onShell  = "%s / %s (%s%%)" % (onHull_correct_total, onHull_total, round(100.*onHull_correct_total/onHull_total, 3))
		offShell = "%s / %s (%s%%)" % (offHull_correct_total, offHull_total, round(100.*offHull_correct_total/offHull_total, 3))
		total    = "%s / %s (%s%%)" % (onHull_correct_total + offHull_correct_total, samples_total, error)

		print("onShell:   %s" %onShell)
		print("offShell:  %s" %offShell)
		print("total:     %s" %total)
		print("delimiter: %s" %delim)


		plt.figure(0)
		plt.title('id: {}, tx: {} error: {}% (delimiter: {})'.format(self.expres.globalInfo.getInfo('id'),self.txName, error, delim), fontsize=14)
		plt.xlabel('mass mother [GeV]')
		plt.ylabel('mass daughter [GeV]')
		plt_cor_on = plt.scatter([oH[0].item() for oH in onHull_correct], [oH[1].item() for oH in onHull_correct], color = 'green')
		plt_cor_off = plt.scatter([oH[0].item() for oH in offHull_correct], [oH[1].item() for oH in offHull_correct], color = 'blue')
		plt_wrg_on = plt.scatter([oH[0].item() for oH in onHull_wrong], [oH[1].item() for oH in onHull_wrong], color = 'red')
		plt_wrg_off = plt.scatter([oH[0].item() for oH in offHull_wrong], [oH[1].item() for oH in offHull_wrong], color = 'orange')
		plt.legend((plt_cor_on, plt_cor_off, plt_wrg_on, plt_wrg_off), ('on hull correct', 'off hull correct', 'should be on hull', 'should be off hull'), scatterpoints=1, loc='upper right', ncol=1, fontsize=8)


		origPoints = getExpresData(self.expres, self.txName)
		
		X0 = [oP[0] for oP in origPoints]
		Y0 = [oP[1] for oP in origPoints]
		#plt.scatter(X0,Y0, marker="x", c="black", s=32)

		fileName = txName + "_classification_scatterPlot.eps"
		if self.savePlots:plt.savefig(self.savePath + fileName)
		plt.show()



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
	txNames = parser.get("database", "txNames").split(",")[0]
	dataselector = parser.get("database", "dataselector")

	#Configure dataset generated for training
	sampleSize = 4000 #int(parser.get("dataset", "sampleSize"))
	massRange = parser.get("dataset", "massRange").split(",")
	massRange = [float(mR) for mR in massRange]

	"""
	#Choose wether to run on CPU or GPU
	whichDevice = float(parser.get("options", "device"))
	deviceCount = torch.cuda.device_count()
	if torch.cuda.is_available() and int(whichDevice) >= 0 and whichDevice <= deviceCount:
		device = torch.device('cuda:' + str(whichDevice))
		logger.info("Running on GPU:%d" %deviceCount)
	else:
		device = torch.device('cpu')
		logger.info("Running on CPU")
	"""
	

	#Select which NNs to train
	netType = parser.get("options", "whichNN")
	if not ( netType == "regression" or netType == "classification"):
		logger.error("Parameter nettype: for performance, only 'regression' or 'classification' allowed")
		netType = "regression" #"classification"

	#expres = Database(databasePath, progressbar = True)
	#expres = expres.getExpResults(analysisIDs = analysisID, useSuperseded = True, useNonValidated = True)[0]

	db = Database(databasePath)
	expres = db.getExpResults(analysisIDs = analysisID, txnames = txNames, dataTypes = dataselector, useSuperseded = True, useNonValidated = True)[0]

	SR = None
	if dataselector == "efficiencyMap":
		IDS = [d.getID() for d in expres.datasets]
		while SR not in IDS:
			SR = input("available SR: %s\nselect which to train: " %expres.datasets)


	validater = Performance(expres, txNames, SR, sampleSize, massRange, netType)
	validater.evaluate()

