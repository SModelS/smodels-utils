#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. module:: readParameterFile.py
   :synopsis: load parameters for various ML related scripts
.. moduleauthor:: Philipp Neuhuber <ph.neuhuber@gmail.com>

"""

import logging,sys
import argparse
import torch
from configparser import ConfigParser


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)


def readParameterFile(logger, parameterFile):

	parser = ConfigParser( inline_comment_prefixes=( ';', ) )
	parser.allow_no_value = True
	parser.read(parameterFile)

	############################################
	# Add smodels and smodels-database to path #
	############################################

	sct = "path"
	if parser.has_section(sct):
		
		smodelsPath = parser.get(sct, "smodelsPath")
		databasePath = parser.get(sct, "databasePath")
		sys.path.append(smodelsPath)
		sys.path.append(databasePath)
		import smodels
		from smodels.experiment.databaseObj import Database

		outputPath = parser.get(sct, "outputPath")
		if outputPath == "": outputPath = None

		paramPath = {"smodels": smodelsPath, "database": databasePath, "outputPath": outputPath}

	else:
		logger.info("No '{}' section found. Skipping Database import.".format(sct))
		paramPath = None


	###############################################
	# Select analysis and topologies for training #
	###############################################

	sct = "database"
	if parser.has_section(sct):

		analysisID = parser.get(sct, "analysis").split(",")
		txName = parser.get(sct, "txName").split(",")
		dataselector = parser.get(sct, "dataselector").split(",")
		signalRegion = parser.get(sct, "signalRegion").split(",")
		for n, sr in enumerate(signalRegion):
			if sr == "None": 
				signalRegion[n] = None

		paramDatabase = {"analysisID": analysisID, "txName": txName, "dataselector": dataselector, "signalRegion": signalRegion}

		# Check wether you want to override old NN with new results		
		
		overwrite = parser.get(sct, "overwrite")
		if not (overwrite == "always" or overwrite == "never" or overwrite == "outperforming"):
			logger.info("Invalid overwrite parameter. Allowed options: 'always' 'never' and 'outperforming'. Setting parameter to 'never'")
			overwrite = "never"

	else:
		logger.info("No '{}' section found. Skipping map selection".format(sct))
		paramDatabase = None

	##############################################################
	# Dataset settings used for training, testing and validation #
	##############################################################

	sct = "dataset"
	
	if parser.has_section(sct):

		sampleSize = int(parser.get(sct, "sampleSize"))
		#massRange = parser.get(sct, "massRange").split(",")
		#massRange = [float(mR) for mR in massRange]
		sampleSplit = parser.get(sct, "sampleSplit").split(",")
		sampleSplit = [float(sS) for sS in sampleSplit]


		paramDataset = {"sampleSize": sampleSize, "sampleSplit": sampleSplit}

	else:
		logger.info("No '{}' section found. Skipping dataset specifications".format(sct))
		paramDataset = None

	######################################
	# Choose wether to run on CPU or GPU #
	######################################

	sct = "device"
	if parser.has_section(sct):

		whichDevice = int(parser.get(sct, "device"))
		deviceCount = torch.cuda.device_count()
		if torch.cuda.is_available() and whichDevice >= 0 and whichDevice <= deviceCount:
			device = torch.device("cuda:" + str(whichDevice))
			logger.info("Running on GPU:%d" %deviceCount)
		else:
			device = torch.device("cpu")
			logger.info("Running on CPU")

		cores = int(parser.get(sct, "cores"))

		paramDevice = {"device": device, "cores": cores}
		
	else:
		logger.info("No '{}' section found. Default set to single-core CPU".format(sct))
		device = torch.device("cpu")
		paramDevice = {"device": "cpu", "cores": 1}


	
	"""
	#Select which NNs to train
	whichNN = parser.get("options", "whichNN")
	if whichNN == "both": whichNN = ["regression", "classification"]
	elif whichNN == "regression" or whichNN == "classification":
		whichNN = [whichNN]
	else:
		logger.error("Invalid NN type selected. Allowed options: 'regression'  'classification' and 'both'")
	"""

	##########################
	# Load analysis options #
	##########################

	sct = "analysis"
	if parser.has_section(sct):

		logFile = parser.getboolean(sct, "logFile")
		lossPlot = parser.getboolean(sct, "lossPlot")
		runPerformance = parser.getboolean(sct, "runPerformance")

		paramAnalysis = {"logFile": logFile, "lossPlot": lossPlot, "runPerformance": runPerformance}

	else:
		logger.info("No '{}' section found. Not going to produce any logfiles or performance outputs".format(sct))
		paramAnalysis = None


	#######################
	# Load Hyperparameter #
	#######################

	hyperParameter = {}

	params = [("optimizer", str), ("lossFunction", str), ("batchSize", int),
			("activationFunction", str), ("epochNum", int), ("learnRate", float),
			("layer", int), ("nodes", int), ("shape", str), ("rescaleMethod", str)]

	for netType in ["regression", "classification"]:

		if parser.has_section(netType):

			hP = {}

			for param in params:

				key = param[0]
				form = param[1]

				try:
					p = parser.get(netType, key).split(",")

					if form != str:
						p = [form(x) for x in p]
				except: p = [None]

				hP[key] = p
			
			#hP = HyperParameter(hp)

		else:
			logger.info("No '{}' section found. No hyperparameters loaded".format(netType))
			hP = None

		hyperParameter[netType] = hP
		
	
	parameters = {"path": paramPath, 
			"database": paramDatabase, 
			"dataset": paramDataset, 
			"device": paramDevice, 
			"analysis": paramAnalysis, 
			"hyperParameter": hyperParameter}

	return parameters
	


if __name__=='__main__':

	ap = argparse.ArgumentParser(description = "Reads parameter file for neural network training")
	ap.add_argument('-p', '--parfile', 
			help='parameter file specifying the plots to be checked', default = 'nn_parameters.ini')
	ap.add_argument('-l', '--log', 
			help='specifying the level of verbosity (error, warning, info, debug)',
			default = 'info', type = str)
           
	args = ap.parse_args()
    
	if not os.path.isfile(args.parfile):
		logger.error("Parameters file %s not found" %args.parfile)
	else:
		logger.info("Reading validation parameters from %s" %args.parfile)


	# Control output level

	numeric_level = getattr(logging,args.log.upper(), None)
	logger.setLevel(level=numeric_level)

	readParameterFile(logger, args.parfile)



