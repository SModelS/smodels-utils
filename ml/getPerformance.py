#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from system.dataset import *
from system.initnet import *
import os, sys, torch
import matplotlib.pyplot as plt
import numpy as np
import argparse, logging
from configparser import ConfigParser
from readParameter import readParameterFile
from smodels.tools.physicsUnits import GeV, fb
from smodels.theory.auxiliaryFunctions import unscaleWidth

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)


class Performance():

	def __init__(self, parameters, netType, validationSet = None, showPlots = True, savePlots = True):

		"""


		"""

		self.paramPath = parameters["path"]
		self.paramDatabase = parameters["database"]
		self.paramDataset = parameters["dataset"]
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

		self.expres = expres
		self.txName = txName
		#self.dataselector = dataselector
		self.SR = parameters["database"]["signalRegion"]
		self.showPlots = True
		self.savePlots = True
		self.netType = netType
		self.model = loadModel(expres, txName)[netType].double()

		# TEMPORARY replace databasePath
		dbPath = expres.path
		for i in range(len(dbPath)):
			if dbPath[i:i+8] == 'database':
				dbPath = dbPath[i:]
				break
		self.savePath = os.getcwd() + "/" + dbPath + "/performance/"
		if not os.path.exists(self.savePath): os.makedirs(self.savePath)
		# ---

		if validationSet == None:
			datasetbuilder = DatasetBuilder(logger, self.paramDatabase, self.paramDataset, self.paramDevice["device"])
			self.validationSet = datasetbuilder.generateNewSet(netType, sampleSize = 10000)
		else: self.validationSet = validationSet


	def evaluate(self):

		"""


		"""

		if self.netType == "regression":

			self.error = torch.sqrt(MSErel(self.model(self.validationSet.inputs), self.validationSet.labels, reduction = None))
			self.meanError = torch.mean(self.error).item()
			#self.getBins()
			self.getEffBins()
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


	def getEffBins(self, binNum = 15):

		#binRange = max(self.validationSet.labels).item() / binNum  #250.
		binRange = [10**(n-10) for n in range(binNum)]

		errorBin = [[] for i in range(binNum)]
		errorBinNum = [0 for i in range(binNum)]

		for i in range(len(self.error)):

			for n in range(binNum):
				if self.validationSet.labels[i] < binRange[n] or n == binNum - 1:
					errorBin[n].append(self.error[i].item())
					break

		mean, std = [], []
		for i in range(binNum):
			if len(errorBin[i]) != 0:
				mean.append(np.mean(errorBin[i]))
				std.append(np.std(errorBin[i]))
			else:
				mean.append(0)
				std.append(0)

		#for i, m in enumerate(mean):
		#	if m < 1:
		#		print(i,"\n---")
		#		for e in errorBin[i]: print(e)


		labels = []
		for n in range(binNum):
			if n == binNum - 1: r = ">" + str(binRange[n]) + " fb"
			elif n == 0: r = "0 - " + str(binRange[n]) + " fb"
			else: r = str(binRange[n-1]) + "-" + str(binRange[n]) + " fb"
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


		for inputs in self.validationSet.inputs[0:20]:
			print(inputs)

		yaxis = 1
		if self.validationSet.inputDimension > 4:
			if max(self.validationSet.inputs[2]) - min(self.validationSet.inputs[2]) > 20:
				yaxis = 2

		#yaxis = 4 #1
		#'''REMOVE'''

		X = [inputs[0].item() for inputs in self.validationSet.inputs]
		Y = [inputs[4].item() for inputs in self.validationSet.inputs] #yaxis

		#Y = [l.item() for l in self.validationSet.labels]

		zeroError = 0
		bigErr = 0
		E2 = []
		for n in range(len(labels)):
			l = labels[n].item()
			p = predictions[n].item()
			#l = unscaleWidth(l - 0.1).asNumber(GeV)
			#p = unscaleWidth(p - 0.1).asNumber(GeV)

			#if l == 1e-5:
			#	l -= 1e-5
			#	p -= 1e-5
			if l < 1e-6: l = 0
			if p < 1e-6: p = 0

			if l > 0:
				e = np.sqrt((( p - l ) / l)**2)
				#else: e = p	\t
				#e = np.sqrt((l - p)**2) \t

				if e < 0.05: 
					print(l,p)
					bigErr += 1
				E2.append(e) # \t
			else:
				if p != 0: zeroError += 1
				E2.append(p)

		meanError2 = np.mean(E2) * 100.
		
		#X = [inputs[0].item() for inputs in self.validationSet.inputs]
		#Y = [inputs[yaxis].item() for inputs in self.validationSet.inputs]
		E = [e.item() for e in self.error]

		
		#Xd,Yd,Ed = [],[],[]
		#for n, width in enumerate(Y):
		#	if width < 1e-6:
		#for n, err in enumerate(E2):
		#	if err > 0.1:

		#for n, label in enumerate(self.validationSet.labels):
		#	if label < 1e-4:
		#		Xd.append(X[n])
		#		Yd.append(Y[n])
		#		Ed.append(E2[n])

		#meanEd = np.mean(Ed) * 100.
		
		print("SMOL ERROR: %s" %bigErr)
		print("ZERO ERROR: %s" %zeroError)

		plt.figure(2)
		#plt.title('id: {}, tx: {}, sr: {}, relError: {:4.2f}% (regression)'.format(self.expres.globalInfo.getInfo('id'), self.txName, self.SR, self.meanError*100.), fontsize=14)
		plt.title('id: {}, tx: {}, sr: {}, relError: {:4.2f}% (regression)'.format(self.expres.globalInfo.getInfo('id'), self.txName, self.SR, meanError2), fontsize=14)
		plt.xlabel("mass mother [GeV]")
		plt.ylabel("mass daughter [GeV]")
		#plt.ylabel("relative error")
		#plt.scatter(X,E2)
		plt.scatter(X,Y, c=E2, cmap='rainbow', vmin=0, vmax=1)
		#plt.scatter(Xd,Yd, c=Ed, cmap='rainbow', vmin=0, vmax=1)
		plt.colorbar()
		plt.tight_layout()

		fileName = self.txName + "_regression_scatterPlot.eps"
		if self.savePlots:plt.savefig(self.savePath + fileName)
	
		#origPoints = getExpresData(self.expres, self.txName, self.SR)
		#origPoints = getOrigExpresData(self.paramDatabase, stripUnits = True)
		
		#X0 = [oP[0] for oP in origPoints]
		#Y0 = [oP[1] for oP in origPoints]
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
		plt.title('id: {}, tx: {}, sr: {},  error: {}% (delimiter: {})'.format(self.expres.globalInfo.getInfo('id'),self.txName, self.SR, error, delim), fontsize=14)
		plt.xlabel('mass mother [GeV]')
		plt.ylabel('mass daughter [GeV]')

		x = 0
		y = 1

		#plt_cor_on = plt.scatter([oH[0].item() for oH in onHull_correct], [oH[1].item() for oH in onHull_correct], color = 'green')
		#plt_cor_off = plt.scatter([oH[0].item() for oH in offHull_correct], [oH[1].item() for oH in offHull_correct], color = 'blue')
		#plt_wrg_on = plt.scatter([oH[0].item() for oH in onHull_wrong], [oH[1].item() for oH in onHull_wrong], color = 'red')
		#plt_wrg_off = plt.scatter([oH[0].item() for oH in offHull_wrong], [oH[1].item() for oH in offHull_wrong], color = 'orange')


		#plt_cor_on = plt.scatter([np.exp(oH[x].item()) for oH in onHull_correct], [unscaleWidth(oH[y].item()).asNumber(GeV) for oH in onHull_correct], color = 'green')
		#plt_cor_off = plt.scatter([np.exp(oH[x].item()) for oH in offHull_correct], [unscaleWidth(oH[y].item()).asNumber(GeV) for oH in offHull_correct], color = 'blue')
		#plt_wrg_on = plt.scatter([np.exp(oH[x].item()) for oH in onHull_wrong], [unscaleWidth(oH[y].item()).asNumber(GeV) for oH in onHull_wrong], color = 'red')
		#plt_wrg_off = plt.scatter([np.exp(oH[x].item()) for oH in offHull_wrong], [unscaleWidth(oH[y].item()).asNumber(GeV) for oH in offHull_wrong], color = 'orange')


		plt_cor_on = plt.scatter([np.exp(oH[x].item()) for oH in onHull_correct], [np.exp(oH[y].item()) for oH in onHull_correct], color = 'green')
		plt_cor_off = plt.scatter([np.exp(oH[x].item()) for oH in offHull_correct], [np.exp(oH[y].item()) for oH in offHull_correct], color = 'blue')
		plt_wrg_on = plt.scatter([np.exp(oH[x].item()) for oH in onHull_wrong], [np.exp(oH[y].item()) for oH in onHull_wrong], color = 'red')
		plt_wrg_off = plt.scatter([np.exp(oH[x].item()) for oH in offHull_wrong], [np.exp(oH[y].item()) for oH in offHull_wrong], color = 'orange')
		plt.legend((plt_cor_on, plt_cor_off, plt_wrg_on, plt_wrg_off), ('on hull correct', 'off hull correct', 'should be on hull', 'should be off hull'), scatterpoints=1, loc='upper right', ncol=1, fontsize=8)

		#origPoints = getExpresData(self.expres, self.txName, self.SR)
		
		#X0 = [oP[x] for oP in origPoints]
		#Y0 = [oP[y] for oP in origPoints]
		#plt.scatter(X0,Y0, marker="x", c="black", s=32)

		fileName = self.txName + "_classification_scatterPlot.eps"
		if self.savePlots:plt.savefig(self.savePath + fileName)
		plt.show()



if __name__=='__main__':

	ap = argparse.ArgumentParser(description="Evaluates performance of generated neural networks")
	ap.add_argument('-p', '--parfile', 
			help='parameter file', default='nn_parameters.ini')
	ap.add_argument('-l', '--log', 
			help='specifying the level of verbosity (error, warning, info, debug)',
			default = 'info', type = str)
	ap.add_argument('-n', '--netType', 
			help='which neural network to test (regression or classification)',
			default = 'regression', type = str)
           
	args = ap.parse_args()
	numeric_level = getattr(logging,args.log.upper(), None)
	logger.setLevel(level=numeric_level)
    
	if not os.path.isfile(args.parfile):
		logger.error("Parameters file %s not found" %args.parfile)
	else:
		logger.info("Reading validation parameters from %s" %args.parfile)

	fileParameters = readParameterFile(logger, args.parfile)

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

					validater = Performance(parameters, args.netType)
					validater.evaluate()


