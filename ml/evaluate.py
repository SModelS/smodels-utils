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
from parameter import Parameter
from sklearn.preprocessing import MinMaxScaler
from system.network import DatabaseNetwork
from system.dataset import DatasetBuilder
from smodels.tools.physicsUnits import GeV, fb
from smodels.theory.auxiliaryFunctions import unscaleWidth
from system.auxiliary import getModelError
from smodels.tools.smodelsLogging import logger

class NetworkEvaluater():

	def __init__(self, parameter, dataset, model = None):

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

		self.dataset = dataset
		self.unscaleData()



	def unscaleData(self, showPlots = False):

		model = self.model["regression"]
		predictions = model(self.dataset.inputs)
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
		#print(np.shape(np.array(s1)))
		self.inputsRaw = scaler.inverse_transform(s1)
		self.labelsRaw = scaler.inverse_transform(s1)[:, [-1]]
		self.predicRaw = scaler.inverse_transform(s2)[:, [-1]]
		

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


		ax.set_ylabel('mean error')
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

		zeroError = 0
		bigErr = 0
		E = []
		LL = 0
		PP = 0

		for n in range(len(self.dataset.labels)):

			l = self.labelsRaw[n][0]
			p = self.predicRaw[n][0]

			if l < 1e-7:
				l = 0
				LL +=1
				if p < 1e-7: 
					p = 0
					PP += 1

			#if l < 1e-5: l = 0
			#if p < 1e-5: p = 0

			if l != 0:
				e = np.sqrt((( p - l ) / l)**2)
				#else: e = p	\t
				#e = np.sqrt((l - p)**2) \t

				if e > 0.25: 
					#logger.debug("[%s,\t%s]\tI: %s\tP: %s" %(int(self.inputsRaw[n][0]),unscaleWidth(self.inputsRaw[n][2]).asNumber(GeV), round(l,10), round(p,10) ))
					bigErr += 1
				E.append(e) # \t
			else:
				if p != 0: zeroError += 1
				E.append(p)


		meanError2 = np.mean(E) * 100.

		logger.debug("total: %s" %len(self.dataset.labels))
		logger.debug("big: %s" %bigErr)
		logger.debug("zero: %s" %zeroError)
		logger.debug("error: %s%%" %round(meanError2, 2))
		#logger.debug("squished L's: %s\tP's: %s" %(LL,PP))


		if self.massColumns != None: # no txnamedata exists aka gridpoints read from external file

			xaxis = 0

			yaxis = self.massColumns.index(max(self.massColumns[:-1]))
			lspPlot = yaxis > xaxis

			w = min(self.massColumns)
			widthPlot = w < 0
			waxis = self.massColumns.index(w)

			#yaxis, waxis = 1, 2 # M1b
			#yaxis, waxis = 2, 6 # M5
			#yaxis, waxis = 1, 4 # M8

		M0_GeV = [inputs[0] for inputs in self.inputsRaw]
		EFF = [labels for labels in self.labelsRaw]
		#EFF = [labels.item() for labels in self.validationSet.labels]

		plt.figure(5)
		plt.title('{} relError: {:4.2f}% (regression)'.format(str(self.txnameData), meanError2), fontsize=14)
		plt.xlabel(r"$m_{squark}$ (GeV)")
		plt.ylabel("efficiencies")
		plt.scatter(M0_GeV, EFF, c=E, cmap='rainbow', vmin=0, vmax=1)
		cbar = plt.colorbar()
		cbar.set_label('relative error', rotation=90)
		plt.tight_layout()
		fileName = str(self.txnameData) + "_regression_scatterPlot_eff.png" #eps
		plt.savefig(self.savePath + fileName)

		if lspPlot:
		
			M1_GeV = [inputs[yaxis] for inputs in self.inputsRaw]

			plt.figure(3)
			plt.title('{} relError: {:4.2f}% (regression)'.format(str(self.txnameData), meanError2), fontsize=14)
			plt.xlabel(r"$m_{squark}$ (GeV)")
			plt.ylabel(r"$m_{stau}$ (GeV)")
			plt.scatter(M0_GeV, M1_GeV, c=E, cmap='rainbow', vmin=0, vmax=1)
			cbar = plt.colorbar()
			cbar.set_label('relative error', rotation=90)
			plt.tight_layout()
			fileName = str(self.txnameData) + "_regression_scatterPlot_lsp.png" #eps
			plt.savefig(self.savePath + fileName)

		if widthPlot:
		
			W_Log = [inputs[waxis].item() for inputs in self.inputsRaw]
			#W_Log = [np.log10(unscaleWidth(inputs[waxis].item()).asNumber(GeV)) for inputs in self.validationSet.inputs]
			#W_Log = [inputs[waxis].item() for inputs in self.validationSet.inputs]

			plt.figure(4)
			plt.title('{} relError: {:4.2f}% (regression)'.format(str(self.txnameData), meanError2), fontsize=14)
			plt.xlabel(r"$m_{squark}$ (GeV)")
			plt.ylabel("width log + 1 scale")
			plt.scatter(M0_GeV, W_Log, c=E, cmap='rainbow', vmin=0, vmax=1)
			cbar = plt.colorbar()
			cbar.set_label('relative error', rotation=90)
			plt.tight_layout()
			fileName = str(self.txnameData) + "_regression_scatterPlot_width.png" #eps
			plt.savefig(self.savePath + fileName)

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

		for nettype in nettypes: #,"classification"]:
			parameter.set("nettype", nettype)

			dataset = builder.run(nettype, sampleSize = 10000, splitData = False)["full"]

			validater = NetworkEvaluater(parameter, dataset)

			validater.binError("labels", showPlots = True)
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

