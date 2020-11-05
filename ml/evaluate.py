#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, os, sys, torch
import numpy as np
import matplotlib.pyplot as plt
from parameter import Parameter
from sklearn.preprocessing import MinMaxScaler
from system.initnet import DatabaseNetwork
from system.dataset import DatasetBuilder
from smodels.tools.smodelsLogging import logger

#from system.dataset import *

#from system.auxiliaryFunctions import *
#from configparser import ConfigParser

from smodels.tools.physicsUnits import GeV, fb
from smodels.theory.auxiliaryFunctions import unscaleWidth
#from smodels.experiment.databaseObj import Database

#FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
#logger = logging.getLogger(__name__)


class NetworkEvaluater():

	def __init__(self, parameter, model = None, dataset = None):

		"""


		"""

		#self.paramPath = parameters["path"]
		#self.paramDatabase = parameters["database"]
		#self.paramDataset = parameters["dataset"]
		#self.paramDevice = parameters["device"]
		#self.paramAnalysis = parameters["analysis"]

		#analysis 		= self.paramDatabase["analysisID"]
		#txName 			= self.paramDatabase["txName"]
		#dataSelector 	= self.paramDatabase["dataSelector"]

		self.expres = parameter["expres"]
		self.txNameData = parameter["txNameData"]
		self.nettype = parameter["nettype"]

		#self.expres = expres
		#self.txName = txName
		
		#self.dataselector = dataselector
		#self.SR = parameter["database"]["signalRegion"]
		#self.showPlots = True
		#self.savePlots = True

		if model != None:
			self.model = model
		else:
			self.model = DatabaseNetwork.load(self.expres, self.txNameData) #loadModel(expres, txName)[netType]#.double()

		#self.scaler = self.model.getScaler()

		dbPath = self.expres.path
		for i in range(len(dbPath)):
			if dbPath[i:i+8] == 'database':
				dbPath = dbPath[i:]
				break
		self.savePath = os.getcwd() + "/" + dbPath + "/performance/"
		if not os.path.exists(self.savePath): os.makedirs(self.savePath)

		if dataset == None:
			builder = DatasetBuilder(parameter)
			dataset = builder.run(self.nettype, sampleSize = 10000, splitData = False)
			self.dataset = dataset["full"]
		else: 
			self.dataset = dataset


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

		#if self.showPlots: plt.show()
		

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


	def binData(self, binNum = 15):

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
		


	def regression(self):

		"""


		"""

		model = self.model["regression"]

		predictions = model(self.dataset.inputs)
		labels = self.dataset.labels
		scaler = model.scaler

		s1, s2 = [], []

		for n in range(len(self.dataset)):
			i = self.dataset.inputs[n].detach().numpy()
			l = self.dataset.labels[n].detach().numpy()
			p = predictions[n].detach().numpy()

			L = np.concatenate((i,l))
			P = np.concatenate((i,p))

			s1.append(L)
			s2.append(P)

		inputsNew = scaler.inverse_transform(s1)

		labels1 = scaler.inverse_transform(s1)[:, [-1]]
		predic1 = scaler.inverse_transform(s2)[:, [-1]]

		# clear up as much memory as we possibly can
		#del(s1)
		#del(s2)

		#yaxis = 1
		#if self.validationSet.inputDimension > 4:
		#	if max(self.validationSet.inputs[2]) - min(self.validationSet.inputs[2]) > 20:
		#		yaxis = 2


		zeroError = 0
		bigErr = 0
		E2 = []
		LL = 0
		PP = 0

		for n in range(len(labels)):

			#l = labels[n].item()
			#p = predictions[n].item()

			l = labels1[n][0]
			p = predic1[n][0]

			if l < 1e-7:
				l = 0
				LL +=1
				if p < 1e-7: 
					p = 0
					PP += 1

			if l != 0:
				e = np.sqrt((( p - l ) / l)**2)
				#else: e = p	\t
				#e = np.sqrt((l - p)**2) \t

				if e > 0.25: 
					print("[%s,\t%s]\tI: %s\tP: %s" %(int(inputsNew[n][0]),unscaleWidth(inputsNew[n][2]).asNumber(GeV), round(l,10), round(p,10) ))
					#print("[%s,\t%s]\tI: %s\tP: %s" %(round(inputsNew[n][0],5),round(inputsNew[n][2],5),round(l,5),round(p,5)))
					bigErr += 1
				E2.append(e) # \t
			else:
				if p != 0: zeroError += 1
				E2.append(p)

		meanError2 = np.mean(E2) * 100.

		print("total: %s" %len(labels))
		print("big: %s" %bigErr)
		print("zero: %s" %zeroError)
		print("error: %s%%" %round(meanError2, 2))
		#print("squished L's: %s\tP's: %s" %(LL,PP))

		print(self.dataset.inputs[0])
		
		yaxis, waxis = 1, 2 # M1b
		#yaxis, waxis = 2, 6	# M5
		#yaxis, waxis = 1, 4 # M8

		#E = [e.item() for e in self.error]

		"""
		#M0_scaled = [inputs[0].item() for inputs in self.validationSet.inputs]
		#M1_scaled = [inputs[yaxis].item() for inputs in self.validationSet.inputs]

		plt.figure(2)
		plt.title('id: {}, tx: {}, sr: {}, relError: {:4.2f}% (regression)'.format(self.expres.globalInfo.getInfo('id'), self.txName, self.SR, meanError2), fontsize=14)
		plt.xlabel("squark mass [scaled]")
		plt.ylabel("stau [scaled]")
		#plt.ylabel("relative error")
		plt.scatter(M0_scaled,M1_scaled, c=E2, cmap='rainbow', vmin=0, vmax=1)
		cbar = plt.colorbar()
		cbar.set_label('relative error', rotation=90)
		plt.tight_layout()
		"""

		M0_GeV = [inputs[0] for inputs in inputsNew]
		M1_GeV = [inputs[yaxis] for inputs in inputsNew]
		EFF = [labels for labels in labels1]
		W_Log = [inputs[waxis].item() for inputs in inputsNew]

		plt.figure(3)
		#plt.title('id: {}, tx: {}, sr: {}, relError: {:4.2f}% (regression)'.format(self.expres.globalInfo.getInfo('id'), self.txName, self.SR, meanError2), fontsize=14)
		plt.title('{} relError: {:4.2f}% (regression)'.format(str(self.txNameData), meanError2), fontsize=14)
		plt.xlabel(r"$m_{squark}$ (GeV)")
		plt.ylabel(r"$m_{stau}$ (GeV)")
		#plt.ylabel("relative error")
		plt.scatter(M0_GeV, M1_GeV, c=E2, cmap='rainbow', vmin=0, vmax=1)
		cbar = plt.colorbar()
		cbar.set_label('relative error', rotation=90)
		plt.tight_layout()
		fileName = str(self.txNameData) + "_regression_scatterPlot_stau.png" #eps
		plt.savefig(self.savePath + fileName)

		#W_Log = [np.log10(unscaleWidth(inputs[waxis].item()).asNumber(GeV)) for inputs in self.validationSet.inputs]
		#W_Log = [inputs[waxis].item() for inputs in self.validationSet.inputs]
		
		
		plt.figure(4)
		plt.title('{} relError: {:4.2f}% (regression)'.format(str(self.txNameData), meanError2), fontsize=14)
		plt.xlabel(r"$m_{squark}$ (GeV)")
		plt.ylabel("width log + 1 scale")
		plt.scatter(M0_GeV, W_Log, c=E2, cmap='rainbow', vmin=0, vmax=1)
		cbar = plt.colorbar()
		cbar.set_label('relative error', rotation=90)
		plt.tight_layout()
		fileName = str(self.txNameData) + "_regression_scatterPlot_width.png" #eps
		plt.savefig(self.savePath + fileName)

		#EFF = [labels.item() for labels in self.validationSet.labels]
		

		plt.figure(5)
		plt.title('{} relError: {:4.2f}% (regression)'.format(str(self.txNameData), meanError2), fontsize=14)
		plt.xlabel(r"$m_{squark}$ (GeV)")
		plt.ylabel("efficiencies")
		plt.scatter(M0_GeV, EFF, c=E2, cmap='rainbow', vmin=0, vmax=1)
		cbar = plt.colorbar()
		cbar.set_label('relative error', rotation=90)
		plt.tight_layout()
		fileName = str(self.txNameData) + "_regression_scatterPlot_eff.png" #eps
		plt.savefig(self.savePath + fileName)

		#if self.savePlots:plt.savefig(self.savePath + fileName)
		# ^^^^^^^^^^^^

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
		#if self.savePlots:plt.savefig(self.savePath + fileName)
		# ^^^^^^^^^^^^
		plt.show()


def main(parameter):

	# ----------------------------------------------------------------------------------- #
	# custom dictionary class that automatically permutates all possible map combinations #
	# ----------------------------------------------------------------------------------- #

	thingsToEvaluate = parameter["database"]

	# -------------------------------------------------------------------------------- #
	# loop over all analysis map combinations of the parameter file [database] section #
	# -------------------------------------------------------------------------------- #

	while(thingsToEvaluate.incrIndex):

		parameter.loadExpres

		for nettype in ["regression","classification"]:
			parameter.set("nettype", nettype)

			validater = NetworkEvaluater(parameter)
			#validater.evaluate()

			validater.regression()
			exit()


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

	parameter = Parameter(args.parfile, args.log)

	main(parameter)

