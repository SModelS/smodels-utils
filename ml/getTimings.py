#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from system.dataset import *
from system.initnet import *
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import GeV, fb
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



def predict(masses, model_reg, model_cla):
	if model_cla(masses).item() == 1:
		return model_reg(masses).item()
	else:
		return None

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

		
def getTimings(expres, topo):

	model_reg = loadModel(expres, txName, "regression")
	model_cla = loadModel(expres, txName, "classification")

	#m1 = 300.
	#m2 = 0.

	masses_int = []
	masses_pre = []
	masses_int2 = []
	masses_pre2 = []

	for n in range(300,1300):
		m = random.random() * 0.5 * n
		#r = random.random()
		#q = random.random()
		#mi = [[m1*r*GeV, m2*q*GeV], [m1*r*GeV, m2*q*GeV]]
		mi = [[n*GeV, m*GeV], [n*GeV, m*GeV]]
		mp = torch.tensor([n, m, n, m])
		masses_int.append(mi)
		masses_pre.append(mp)

	for n in range(len(masses_int)):
		if type(expres.getUpperLimitFor(txname=topo, mass=masses_int[n])) == type(None):
			masses_int2.append(masses_int[n])
			masses_pre2.append(masses_pre[n])


	plt.figure(5)
	plt.scatter([m[0].item() for m in masses_pre2], [m[1].item() for m in masses_pre2])
	plt.show()

	t0 = time()
	for m in masses_int2:
		expres.getUpperLimitFor(txname=topo, mass=m)
	print(time()-t0)

	nx = 0
	t0 = time()
	for m in masses_pre2:
		if model_cla(m) == 1.: model_reg(m)
		else: nx += 1
	print(time()-t0)

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


	expres = Database(databasePath, progressbar = True)
	expres = expres.getExpResults(analysisIDs = analysisID, useSuperseded = True, useNonValidated = True)[0]

	getTimings(expres, txName)
