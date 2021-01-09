#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import torch
from math import ceil, inf
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from parameterParser import Parameter
from sklearn.preprocessing import MinMaxScaler
from mlCore.network import DatabaseNetwork
from mlCore.dataset import DatasetBuilder
from mlCore.auxiliary import getModelError
from smodels.tools.physicsUnits import GeV, fb
from smodels.theory.auxiliaryFunctions import unscaleWidth
from smodels.tools.smodelsLogging import logger

class NetworkEvaluater():

	def __init__(self, parameter, dataset, builder, lmbda, model = None):

		"""


		"""

		self.expres = parameter["expres"]
		self.txnameData = parameter["txName"].txnameData
		self.nettype = parameter["nettype"]
		self.massColumns = parameter["massColumns"]

		if model != None:
			self.model = model
		else:
			self.model = DatabaseNetwork.load(self.expres, self.txnameData) #loadModel(expres, txName)[netType]#.double()

		dbPath = self.expres.path
		for i in range(len(dbPath)):
			if dbPath[i:i+8] == 'database':
				dbPath = dbPath[i:]
				break
		self.savePath = os.getcwd() + "/" + dbPath + "/performance/"
		Path(self.savePath).mkdir(parents=True, exist_ok=True)

		self.builder = builder
		self.dataset = dataset
		self.lmbda = lmbda
		#self.unscaleData()



	def unscaleData(self, showPlots = False):

		model = self.model["regression"]
		predictions = model(self.dataset.inputs).detach().numpy()
		scaler = model.scaler
		#s1, s2 = [], []

		self.inputsRaw = scaler["masses"].inverse_transform(self.dataset.inputs)
		#self.labelsRaw = scaler["targets"].inverse_transform(self.dataset.labels)
		#self.predicRaw = scaler["targets"].inverse_transform(predictions)#np.reshape(predictions, (-1, 1)))
		self.labelsRaw = self.dataset.labels.detach().numpy()
		self.predicRaw = predictions

		from scipy.special import inv_boxcox
		#lmbda = -0.02888445 #no 0
		#lmbda = 0.12332622

		self.labelsRaw = [inv_boxcox(-label[0], self.lmbda) for label in self.labelsRaw]
		self.predicRaw = [inv_boxcox(-predic[0], self.lmbda) for predic in self.predicRaw]

		"""
		for n in range(len(predictions)):
			if self.dataset.inputs[n][0] == 1 and self.dataset.inputs[n][2] < 73.841:
				print(self.dataset.labels[n], predictions[n])
				print(self.labelsRaw[n], self.predicRaw[n])
				print("---")
		"""
		
		
		#self.labelsRaw = inv_boxcox(self.labelsRaw, lmbda)
		#self.predicRaw = inv_boxcox(self.predicRaw, lmbda)


		#self.labelsRaw = [0. if label > 70. else unscaleWidth(label[0]).asNumber(GeV) for label in self.labelsRaw]
		#self.predicRaw = [0. if predic > 70. else unscaleWidth(predic[0]).asNumber(GeV) for predic in self.predicRaw]

		## old
		##self.labelsRaw = [10**-label[0] for label in self.labelsRaw]
		##self.predicRaw = [10**-predic[0] for predic in self.predicRaw]


	def binError(self, whichData, showPlots = False):

		nettype = "regression"
		error = getModelError(self.model[nettype], self.dataset, nettype, returnMean = False)

		if whichData == "labels":
			data = self.labelsRaw
			units = ""
		elif whichData == "widths":
			data = []
			units = "GeV"
			for iR in self.inputsRaw:
				data.append(unscaleWidth(iR[2]).asNumber(GeV)) #widthPos]

		log = []
		for d in data:
			try: d = d.item()
			except: d = d
			if d != 0. and np.log10(d) != inf:
			#if d != 0.:
				log.append(np.log10(d))


		binMin = min(log)
		binMax = max(log)

		binNum = ceil(max(abs(binMin),abs(binMax))) + 1

		bins = [[] for _ in range(binNum)]
		mean = [_ for _ in range(binNum)]
		std  = [_ for _ in range(binNum)]

		for n,e in enumerate(error):
			try: d = data[n].item()
			except: d = data[n]
			if d == 0.: index = 0
			elif d == inf: index = 0 # WHAT IS GOING ON
			else: index = ceil(abs(np.log10(d)))
			
			bins[index].append(e)

		bins = np.array(bins)

		for n,b in enumerate(bins):

			if len(b) > 0:
				mean[n] = np.mean(b)
				std[n] = np.std(b)
			else:
				mean[n] = 0
				std[n] = 0

		labels = [_ for _ in range(binNum)]

		for n in range(binNum):
			
			if n == 0.:
				labels[n] = "0 " + units

			elif n == 1:
				labels[n] = ">1e-1 " + units

			else:
				labels[n] = "1e-" + str(n-1) + " - 1e-" + str(n) + " " + units

			labels[n] += " (n = {})".format(str(len(bins[n])))


		x = np.arange(len(bins))  # the label locations
		width = 0.5

		fig, ax = plt.subplots()
		rects = ax.bar(x, mean, width, yerr=std)


		ax.set_ylabel('mean relative error')
		ax.set_title('mean error binned by %s (n = %s)' % (whichData, len(self.dataset)))
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
		if showPlots: plt.show()
		


	def regression(self, showPlots = False):

		"""


		"""

		model = self.model["regression"]
		predictions = model(self.dataset.inputs)#.detach().numpy()

		zeroError = 0
		bigErr = 0
		E = []

		from scipy.stats import boxcox
		L = 0.16450906276299462

		for n in range(len(self.dataset.labels)):

			#l = self.dataset.labels[n][0].detach().item()
			#p = predictions[n][0]

			l = self.dataset.labels[n].detach().item()
			p = predictions[n]

			#l = 10**l
			#p = 10**p
			l = boxcox(l, L)
			p = boxcox(p, L)

			#if l > 80.:
			#	print(l,p)
			
			#print(l,p)
			#print(np.sqrt((( p - l ) / l)**2))

			

			#l = self.labelsRaw[n]
			#p = self.predicRaw[n]

			if False:#self.builder.refXsecs != None:
				#m0 = self.inputsRaw[n][0]

				m0 = self.dataset.inputs[n][0]

				xsec = self.builder._getRefXsec(m0)
				
				if self.builder.luminosity * xsec * l < 1e-2:
					l = 0
				if self.builder.luminosity * xsec * p < 1e-2:
					p = 0

			#print(l,p)
			"""
			if l == 0. and p != 0.:
				print(self.dataset.labels[n][0].detach().item(), predictions[n][0])
				print(l,p)
				print("\n")
			"""
			
			
			"""
			if l != 0:
				print(np.sqrt((( p - l ) / l)**2))
			else: print(p)
			print("\n")
			"""

			

			#if l < 1e-5: l = 0
			#if p < 1e-5: p = 0

			if l != 0:
				e = np.sqrt((( p - l ) / l)**2)


				if e == np.nan:
					print(e)
				#else: e = p	\t
				#e = np.sqrt((l - p)**2) \t

				#if e < 0.05: print(l,p)

				m0 = self.dataset.inputs[n][0]
				if e > 0.025 and m0 < 250.: 
					#logger.debug("[%s,\t%s]\tI: %s\tP: %s" %(int(self.inputsRaw[n][0]),unscaleWidth(self.inputsRaw[n][2]).asNumber(GeV), round(l,10), round(p,10) ))
					print(m0, l,p)
					#l = boxcox(l, L)
					#p = boxcox(p, L)
					#print(l,p,"\n")
					bigErr += 1
					#print(l, p)
				E.append(e) # \t
			else:
				if p != 0: zeroError += 1
				E.append(p)



		#meanError = 100.*s / len(E)
		#maxError = 100. * max(E)

	
		for n, e in enumerate(E):
			if not e < 100: 
				E[n] = 0

		#s = sum(E)
		#meanError = 100.*s / len(E)
		#maxError = 100. * max(E)

		meanError = np.mean(np.array(E)) * 100.
		maxError = np.max(np.array(E)) * 100.

		#print(sorted(E))

		logger.debug("total: %s" %len(self.dataset.labels))
		logger.debug("big: %s" %bigErr)
		logger.debug("zero: %s" %zeroError)
		logger.debug("mean error: %f%%" %round(meanError,2))
		logger.debug("max error: %f%%" %round(maxError,2))


		self.inputsRaw = self.dataset.inputs
		self.labelsRaw = self.dataset.labels



		#yaxis, waxis = 1, 2 # M1b
		#yaxis, waxis = 2, 6 # M5
		#yaxis, waxis = 1, 4 # M8

		if self.massColumns != None: # no txnamedata exists aka gridpoints read from external file

			xaxis = 0

			yaxis = self.massColumns.index(max(self.massColumns[:-1]))
			lspPlot = yaxis > xaxis

			w = min(self.massColumns)
			widthPlot = w < 0
			waxis = self.massColumns.index(w)


		argsort = np.argsort(E)
		E = np.array(E)[argsort]

		thingsToPlot = {}

		M0_GeV = np.array([inputs[0] for inputs in self.inputsRaw])[argsort]

		if yaxis != xaxis:
			LSP_GeV = np.array([inputs[yaxis] for inputs in self.inputsRaw])[argsort]
			thingsToPlot["mass0_lsp"] = {"xaxis": M0_GeV, "xlabel": r"$m_{HSCP}$ (GeV)", "yaxis": LSP_GeV, "ylabel":  r"$m_{LSP}$ (GeV)", "error": E}


		if widthPlot:
			widths = [unscaleWidth(inputs[waxis].item()).asNumber(GeV) for inputs in self.inputsRaw]
			WIDTH_LOG = np.array([-40. if width == 0. else np.log10(width) for width in widths])[argsort] #0.
			thingsToPlot["mass0_width"] = {"xaxis": M0_GeV, "xlabel": r"$m_{HSCP}$ (GeV)", "yaxis": WIDTH_LOG, "ylabel":  "width (log10)", "error": E}

		effs = [labels for labels in self.labelsRaw]
		EFF = np.array([0. if eff == 0. else np.log10(eff) for eff in effs])[argsort]
		#EFF = np.array([np.log10(labels) for labels in self.labelsRaw])[argsort]
		thingsToPlot["mass0_eff"] = {"xaxis": M0_GeV, "xlabel": r"$m_{HSCP}$ (GeV)", "yaxis": EFF, "ylabel":  "efficiencies (log)", "error": E}

		# bundle all values of constant m0 mass #
		targetMass = [140., 160., 240., 1000., 1200., 1400., 1600., 2000.]
		for tmass in targetMass:

			spliceWID = []
			spliceEFF = []
			spliceERR = []

			for n,mass in enumerate(M0_GeV):
				if mass == tmass:
					spliceWID.append(WIDTH_LOG[n])
					spliceEFF.append(EFF[n])
					spliceERR.append(E[n])

			if len(spliceERR) > 0:
				key = "m0=" + str(int(tmass))
				#thingsToPlot[key] = {"yaxis": spliceEFF, "ylabel": "efficiencies (log)", "xaxis": spliceWID, "xlabel":  "widths (log)", "error": spliceERR, "affix": r"$m_{HSCP}$ = " + str(int(tmass)) + " GeV "}
				
		#plt.figure(10)
		
		#plt.title("eff distribution boxcox")
		#plt.hist(self.dataset.labels.detach().numpy(), bins=25, density=True)
		#plt.hist([np.log10(l) for l in self.dataset.labels.detach().numpy()], bins=25, density=True)
		#plt.hist([np.log10(l) for l in self.labelsRaw], bins=25, density=True)

		
		index = 5
		for key, value in thingsToPlot.items():

			maxError = np.max(value["error"]) * 100.
			meanError = np.mean(value["error"]) * 100.

			vMax = min(1., 0.01*maxError)

			if not "affix" in value:
				affix = " "
			else: affix = value["affix"]

			plt.figure(index)
			plt.title("{} (regression)\n{}mean error: {:4.2f}% max error: {:4.2f}%".format(str(self.txnameData), affix, meanError, maxError), fontsize=14)
			plt.xlabel(value["xlabel"])
			plt.xlim([120.,300.])
			plt.ylim([-42,-14])
			plt.ylabel(value["ylabel"])
			plt.scatter(value["xaxis"], value["yaxis"], c=value["error"], cmap='rainbow', vmin=0, vmax=vMax)
			cbar = plt.colorbar()
			cbar.set_label('relative error', rotation=90)
			plt.tight_layout()
			fileName = str(self.txnameData) + "_regression_scatterPlot_" + key + ".png" #eps
			plt.savefig(self.savePath + fileName)
			index += 1

		if showPlots: plt.show()

		

		



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


		plt_cor_on = plt.scatter([np.exp(oH[x].item()) for oH in onHull_correct], [np.exp(oH[y].item()) for oH in onHull_correct], color = 'green')
		plt_cor_off = plt.scatter([np.exp(oH[x].item()) for oH in offHull_correct], [np.exp(oH[y].item()) for oH in offHull_correct], color = 'blue')
		plt_wrg_on = plt.scatter([np.exp(oH[x].item()) for oH in onHull_wrong], [np.exp(oH[y].item()) for oH in onHull_wrong], color = 'red')
		plt_wrg_off = plt.scatter([np.exp(oH[x].item()) for oH in offHull_wrong], [np.exp(oH[y].item()) for oH in offHull_wrong], color = 'orange')
		plt.legend((plt_cor_on, plt_cor_off, plt_wrg_on, plt_wrg_off), ('on hull correct', 'off hull correct', 'should be on hull', 'should be off hull'), scatterpoints=1, loc='upper right', ncol=1, fontsize=8)

		fileName = self.txName + "_classification_scatterPlot.eps"
		plt.show()


def main(parameter, nettypes):

	# ----------------------------------------------------------------------------------- #
	# custom dictionary class that automatically permutates all possible map combinations #
	# ----------------------------------------------------------------------------------- #

	thingsToEvaluate = parameter["database"]

	# -------------------------------------------------------------------------------- #
	# loop over all analysis map combinations of the parameter file [database] section #
	# -------------------------------------------------------------------------------- #

	while(thingsToEvaluate.incrIndex):

		parameter.loadExpres
		builder = DatasetBuilder(parameter)
		#lda = 0.12328563
		lda = 0.23636879

		for nettype in nettypes: #,"classification"]:
			parameter.set("nettype", nettype)

			#dataset = builder.run(nettype, lmbda = lda, sampleSize = 10000, splitData = False)["full"]

			builder.run(nettype, loadFromFile = True)
			builder.shuffle()
			#builder.rescaleMasses()
			#builder.rescaleTargets()
			#rescaleDict = builder.rescale

			dataset = builder.getDataset(fullSet = True, splitSet = False, rescaleParams = False)

			#print(dataset["full"].labels)
			#dataset["full"].labels = -dataset["full"].labels
			#print(dataset["full"].labels)


			validater = NetworkEvaluater(parameter, dataset["full"], builder, lda)

			#validater.binError("labels", showPlots = True)
			#validater.binError("widths", showPlots = True)
			validater.regression(showPlots = True)

if __name__=='__main__':

	ap = argparse.ArgumentParser(description="Evaluates performance of generated neural networks")
	ap.add_argument('-p', '--parfile', 
			help='parameter file', default='nn_parameters.ini')
	ap.add_argument('-l', '--log', 
			help='specifying the level of verbosity (error, warning, info, debug)',
			default = 'info', type = str)
	ap.add_argument('-n', '--nettype', 
			help="which neural network to test ('regression', 'classification' or 'all')",
			default = 'regression', type = str)     
	args = ap.parse_args()

	if args.nettype == "all": nettypes = ["regression, classification"]
	else: nettypes = [args.nettype]

	parameter = Parameter(args.parfile, args.log)

	main(parameter, nettypes)

