#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from system.dataset import *
from system.initnet import *
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import GeV, fb
from readParameter import readParameterFile
import os, sys, torch
import matplotlib.pyplot as plt
import numpy as np
import argparse, logging
from configparser import ConfigParser
from time import time
import matplotlib.pyplot as plt
import random

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)




def interpolate(masses, topo):
	ul = expres.getUpperLimitFor(txname=topo, mass=masses)
	if type(ul) == type(None): return None
	else: return ul.asNumber(fb)


def getError(expres, topo):

	model_reg = loadModel(expres, txName, "regression")
	model_cla = loadModel(expres, txName, "classification")

	for n in range(100):
		r = random.random()
		m1 = 450.*r*r
		m2 = 150.*r*r

		mass0 = [[m1*GeV, m2*GeV], [m1*GeV, m2*GeV]]
		ip = interpolate(mass0, topo)
		mass0 = masses = torch.tensor([m1, m2, m1, m2])
		pd = predict(mass0, model_reg, model_cla)

		if ip == None and pd == None: print(None)
		elif ip != None and pd != None: print(round(abs(ip-pd)/ip, 3))
		else: print("WRONG CLA")


def getInterpolTimeOnly(expres, topo):

	T = []
	for i in range(5):

		sampleSize = 2000
		dataset = generateDataset(expres, topo, None, 0., sampleSize, "regression", "cpu")
		sampleSize = len(dataset)

		inputs = dataset.inputs.numpy()
		dim = int(0.5*dataset.inputDimension)
		masses = []

		for i in inputs:
			m = [[x*GeV for x in i[0:dim]], [x*GeV for x in i[dim:]]]
			masses.append(m)
	
	
		t0 = time()
		for m in masses:
			expres.getUpperLimitFor(txname=topo, mass=m)
		t = time() - t0

		T.append(1000.*t/sampleSize)

	return np.mean(T), np.std(T)


def getSpeed(model, expres, topo, dataset):

	dsp = dataset.inputs[0:5000]
	dsnp = dsp.numpy()
	dsnpi = []

	dim = int(0.5*len(dsnp[0]))

	for d in dsnp:
		i = [[x*GeV for x in d[0:dim]], [x*GeV for x in d[dim:]]]
		dsnpi.append(i)


	t0 = time()
	for m in dsnpi:
		expres.getUpperLimitFor(txname=topo, mass=m)
	timei = time() - t0

	t0 = time()
	for m in dsp:
		model(m)
	timep = time() - t0

	deltaT = timep / timei

	return deltaT

	


def getTimings(model, txNameData, data):

	

	data_i = []
	data_p = []
	for d in data:

		print(d)

		#m = [[d[0][0].item()*GeV, d[0][1].item()*GeV, d[0][2].item()*GeV], [d[0][3].item()*GeV, d[0][4].item()*GeV, d[0][5].item()*GeV]]
		#m= [[d[0][0].item()*GeV, d[0][1].item()*GeV], [d[0][2].item()*GeV, d[0][3].item()*GeV]]
		m = [[d[0], (d[1], d[2])], [d[3], (d[4], d[5])]]

		n = d[0]
		data_i.append(m)
		data_p.append(n)

	#plt.figure(5)
	#plt.scatter([m[0].item() for m in masses_pre2], [m[1].item() for m in masses_pre2])
	#plt.show()

	T = []
	for n in range(5):
		t0 = time()
		for m in data_i:
			#interpolate_GETTIMINGS(m, topo, expres)
			txNameData.getValueFor(m)
		T.append(time()-t0)
	print("interpolation: %s +/- %sms" % (round(1000*np.mean(T)/len(data), 5), round(1000*np.std(T)/len(data), 5)))
	
	T = []
	for n in range(5):
		t0 = time()
		for m in data_p:
			predict_GETTIMINGS(m, model)
			model(m)
		T.append(time()-t0)
	print("prediction: %s +/- %sms" % (round(1000*np.mean(T)/len(data), 5), round(1000*np.std(T)/len(data), 5)))
	

def getPlot():
	
	hid_lay = [1, 2, 3, 4, 5, 6, 7]
	P_mean = [0.05295, 0.07822, 0.1046, 0.13177, 0.16682, 0.18376, 0.22011]
	P_std = [0.00285, 0.00442, 0.00285, 0.00265, 0.00813, 0.00432, 0.00519]
	"""
	plt.figure(44)
	plt.title('prediction times for single mass points', fontsize=20) #comparison of interpolation vs model prediction times
	plt.xlabel('number of hidden layers', fontsize=16)
	plt.ylabel('average time [ms]', fontsize=16)
	plt.errorbar(hid_lay, P_mean, yerr=P_std)
	plt.show()
	"""

	N = ["ATLAS-SUSY-2017-02 TChiH\n26 gridpoints", "CMS-SUS-17-009 TSmuSmu\n452 gridpoints", "CMS-SUS-19-006 T1ttttoff\n976 gridpoints", "CMS-SUS-16-009 T1tttt\n7685 gridpoints", "CMS-SUS-19-006 T1\n15425 gridpoints"]
	I_mean = [0.1378, 0.13572, 0.13862, 0.15623, 0.18318]
	I_std = [0.00893, 0.00309, 0.00184, 0.01052, 0.00651]
	#P_mean = [0.05295, 0.05352, 0.0556]
	#P_std = [0.00285, 0.00274, 0.00632]

	x = np.arange(len(N))  # the label locations
	width = 0.7  # the width of the bars

	fig, ax = plt.subplots()
	rects1 = ax.bar(x, I_mean, width, yerr=I_std) # label='interpolation'
	#rects2 = ax.bar(x + width/2, P_mean, width, label='prediction', yerr= P_std)

	# Add some text for labels, title and custom x-axis tick labels, etc.
	ax.set_ylabel('average time [ms]', fontsize=16)
	ax.set_title('interpolation times for single mass points', fontsize=20)
	ax.set_xticks(x)
	ax.set_xticklabels(N)
	ax.legend()


	def autolabel(rects):
		"""Attach a text label above each bar in *rects*, displaying its height."""
		for rect in rects:
		    height = rect.get_height()
		    ax.annotate('{}'.format(height),
		                xy=(rect.get_x() + rect.get_width() / 2, height),
		                xytext=(0, 15),  # 15 points vertical offset
		                textcoords="offset points",
		                ha='center', va='bottom')


	autolabel(rects1)
	#autolabel(rects2)

	fig.tight_layout()

	plt.show()

	"""
	plt.figure(32)
	plt.title('computation time regression model', fontsize=20) #comparison of interpolation vs model prediction times
	plt.xlabel('number of UL predictions') #calculations
	plt.ylabel('computation time (ms)')
	plt.plot(X, [tp*1000 for tp in TP], label = 'model prediction')
	#plt.plot(X, [ti*1000 for ti in TI], label = 'interpolation')
	plt.legend()
	plt.show()
	"""
	

if __name__=='__main__':


	ap = argparse.ArgumentParser(description="Trains and finds best performing neural networks for database analyses via hyperparameter search")
	ap.add_argument('-p', '--parfile', 
			help='parameter file specifying the plots to be checked', default='nn_parameters.ini')
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

	netType = "regression"

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

					db = Database(parameters["path"]["database"])
					expres = db.getExpResults(analysisIDs = analysisID, txnames = txName, dataTypes = daSel, useSuperseded = True, useNonValidated = True)[0]

					txList = expres.getDataset(signalRegion).txnameList
					for tx in txList:
						if str(tx) == txName:
							txNameData = tx.txnameData
							break

					parameters["database"]["expres"] = expres
					parameters["database"]["txNameData"] = txNameData

					datasetbuilder = DatasetBuilder(logger, parameters["database"], parameters["dataset"], parameters["device"])
					validationSet = datasetbuilder.generateNewSet(netType, sampleSize = 10000)

					model = loadModel(expres, txName)[netType]
					model.eval()

					getTimings(model, txNameData, validationSet)
	#getPlot()
