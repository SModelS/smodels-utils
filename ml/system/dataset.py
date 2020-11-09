#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import torch
import numpy as np
from time import time
from copy import deepcopy
from random import random, shuffle
from sklearn.cluster import MeanShift
from system.auxiliary import loadGridPoints
from torch.utils.data import Dataset # better import?
from sklearn.preprocessing import MinMaxScaler
from smodels.theory.auxiliaryFunctions import rescaleWidth, removeUnits#, unscaleWidth
from smodels.tools import physicsUnits
from smodels.tools.smodelsLogging import logger
from smodels.tools.physicsUnits import GeV, fb, pb

class Data(Dataset):

	"""
	Holds the actual datasets in torch.tensor format for training and evaluation

	"""

	def __init__(self, dataset, inputDimension, device, rescaleInputs = False, rescaleLabels = False):

		self.inputs = torch.tensor(dataset, dtype=torch.float64).narrow(1, 0, inputDimension).to(device) #.double().to(device)
		self.labels = torch.tensor(dataset, dtype=torch.float64).narrow(1, inputDimension, 1).to(device) #.double().to(device)

		mean = torch.mean(self.inputs)	#[torch.mean(self.inputs), torch.mean(self.labels)]
		std = torch.std(self.inputs)	#[torch.std(self.inputs), torch.std(self.labels)]

		self.rescaleParameter = {"mean": mean, "std": std}
		self.inputDimension = inputDimension
		self.device = device


	def __len__(self):
		return self.inputs.size()[0]


	def split(self, sampleSplit):

		"""
		Method to split dataset into different parts. Mainly training, testing and validation.

		:param sampleSplit: dict of floats that ideally add up to 1.

		"""

		if sum(sampleSplit) != 1.:
			logger.error("Dataset splice ratios don't add up to 1")

		length = len(self)
		start = 0

		splitData = [[] for i in range(len(sampleSplit))]

		for i in range(len(sampleSplit)):
			if i > 0: start += int(length * sampleSplit[i-1])
			end = int(length * sampleSplit[i])

			splitData[i] = deepcopy(self)
			splitData[i].inputs = self.inputs.narrow(0, start, end)
			splitData[i].labels = self.labels.narrow(0, start, end)

		return splitData
				
	def __getitem__(self, index):
		return (self.inputs[index], self.labels[index])



class DatasetBuilder():

	"""
	Outputs a Dataset class that is used for training and evaluation of neural networks
	Needs metainfo of analysis and training parameters (usually loaded from nn_parameters.info file) as well as a device to send 'Dataset' class to
	(cpu or specific gpu)

	"""

	def __init__(self, parameter):

		"""
		Sets up the dataset generation for a specific map
		:param parameter: Holds all neccessary information to create or load datasets. Can be a simple dict, or the custom class introduced in 'readParameter.py'

		""" 

		self.smodelsPath = parameter["smodelsPath"]
		self.utilsPath = parameter["utilsPath"]

		self.expres = parameter["expres"]
		self.txnameData = parameter["txName"].txnameData
		self.dataselector = parameter["dataselector"]
		self.signalRegion = parameter["signalRegion"]
		self.full_dim = self.txnameData.full_dimensionality
		self.luminosity = parameter["txName"].globalInfo.getInfo("lumi").asNumber(1/fb)

		self.sampleSize 	= parameter["sampleSize"]
		self.sampleSplit 	= parameter["sampleSplit"]
		self.device 		= parameter["device"]

		self.refXsecFile = parameter["refXsecFile"]
		if self.refXsecFile != None:
			self.refXsecColumns = parameter["refXsecColumns"]
			self._readRefXsecs()
		else: self.refXsecs = None

		self.loadFile = parameter["loadFile"]
		if self.loadFile != None:
			self.massColumns = parameter["massColumns"]

		logger.info("builder completed for %s" % self.txnameData)


	def _removeBigWidths(self):

		"""
		Some analyses had big widths in the range 1e6 in the original grid, which dampened final performance significantly.
		Use with caution, more of a troubleshooting method.

		"""

		width = self.txnameData.widthPosition
		if width == []:
			return

		widthPos = width[0][1] + 1
		n = 0
		while n < len(self.origData):

			width = self.origData[n][widthPos]
			if width > 1e4:
				self.origData.pop(n)
			else:
				n += 1


	def _loadOrigData(self): #, removeBigWidths = False

		"""
		Load grid points from databse/../analysis/sr/Tx.txt
		Function loadGridPoints returns (masspoints, values, units),
		but we are only interested in mass points

		"""

		self._origData = loadGridPoints(self.expres, self.txnameData, self.dataselector, self.signalRegion, stripUnits = True)[0]
		#if removeBigWidths: self._removeBigWidths()

		#self.origData, self.origValues, self.units	= self._getOrigData()
		#self.origDataMean		= np.mean(self.origData, axis = 0)
		#self.origDataStd		= np.std(self.origData, axis = 0)


	def _PCA(self, data = None):

		"""
		Perform PCA on any given masspoints (default = original grid points)

		:param data: alternative datapoints, default are original gridpoints of current map

		"""

		if data == None: data = self._origData

		tx = self.txnameData
		ogOrdered = []

		if tx.widthPosition != []:
			for og in data:
				temp, mw = [], []
				for n, m in enumerate(og):
					if n == tx.widthPosition[int(n/tx.dimensionality)][1] + 1 + int(n/tx.dimensionality) * tx.dimensionality:
						mw.append(rescaleWidth(m))
					else:
						temp.append(m)
				for w in mw: temp.append(w)
				ogOrdered.append(tx.coordinatesToData(temp))
		else: 
			for og in data:			
				ogOrdered.append(tx.coordinatesToData(og))

		self._origPCA = np.array([tx.dataToCoordinates(m, rotMatrix = tx._V, transVector = tx.delta_x) for m in ogOrdered])


	def _clusterData(self, bandWidth = 8):

		"""
		Perform meanshift analysis on PCA grid points

		:param bandWidth: bandwidth for the sklearn.cluster.Meanshift method

		"""

		clustering = MeanShift(bandwidth = bandWidth).fit(self._origPCA)
			
		cluster = [[] for _ in range(len(clustering.cluster_centers_))]
		
		for n, label in enumerate(clustering.labels_):
			cluster[label].append(self._origPCA[n])

		self._origCluster = cluster


	def _addClusterBias(self, sampleSize):
	
		"""
		Adding a bias to draw more points from clusters with non-zero values

		"""

		tx = self.txnameData
		clusterMeanVals = []
		zeroClusters, nonZeroClusters = 0, 0
		for n, cluster in enumerate(self._origCluster):

				mean = np.mean(cluster, axis = 0)

				x = tx.coordinatesToData(mean, rotMatrix = tx._V, transVector = tx.delta_x)
				val = tx.getValueFor(x)
				val = removeUnits(val,physicsUnits.standardUnits)

				clusterMeanVals.append(val)

				if val == 0: zeroClusters += len(cluster)
				else: nonZeroClusters += len(cluster)
						

		# If number of gridpoints is greater than sampleSize, 'factor' could be a negative value
		factor = max((sampleSize - zeroClusters) / nonZeroClusters, 1)

		pointsToDraw = []
		for n, cluster in enumerate(self._origCluster):

			if clusterMeanVals[n] > 0:
				pointsToDraw.append(int(factor*len(cluster))+1)
			else:
				pointsToDraw.append(len(cluster))

		return clusterMeanVals, pointsToDraw



	def _getHullPoints(self):

		"""
		Algorithm that finds hull edges from original datapoints
		Used to generate convex hull dataset for classifaction network

		"""

		massesSorted = [sorted(self.origData,key=lambda l:l[n]) for n in range(len(self.origData[0]))]
		massesHull = []

		for k in range(len(massesSorted)):

			#if k == widthPos:
			#	continue

			massesSortedReduced = []
			lastMass = 0.
			totalMasses = len(massesSorted[k])

			for n in range(totalMasses):
				subset = []
				currentMass = massesSorted[k][n][k]
				if lastMass == currentMass:
					continue
				lastMass = currentMass
				for i in range(n, totalMasses):
					if massesSorted[k][i][k] == currentMass:
						subset.append(massesSorted[k][i])
					else: break

				massesSortedReduced.append(np.max(subset, axis=0))
				#massesSortedReduced.append(max(subset, key=lambda x:x[k])) this should work but doesnt for some reason?

			massesHull.append(massesSortedReduced)

		return massesHull

	
	def _readRefXsecs(self):

		"""
		Load reference cross sections for an eff cutoff given by
		luminosity * eff * refXsec[m0] > 1e-2 to ignore irrelevent effs and improve model performance

		"""

		from slha.addRefXSecs import getXSecsFrom

		fiLe = self.refXsecFile
		col  = self.refXsecColumns

		if col != None:
			xsecs = getXSecsFrom(fiLe, columns={"mass":col[0],"xsec":col[1]})
		else:
			xsecs = getXSecsFrom(fiLe)
			
		dic = {"masses":[],"xsecs":[]}

		for key,value in xsecs.items():
			dic["masses"].append(key)
			dic["xsecs"].append(value*1e3) # pb -> fb

		self.refXsecs = dic
	

	def _getRefXsec(self, mother):

		for n, mass in enumerate(self.refXsecs["masses"]):
			if mass > mother:
				return self.refXsecs["xsecs"][n]

		return self.refXsecs["xsecs"][-1]



	def _loadDataset(self):

		logger.info("loading dataset (%s)" % self.nettype)
		
		with open(self.loadFile) as txtFile:
			raw = txtFile.read()

		lines = raw.split("\n")[1:]

		dataset = []
		count = [0 for n in range(20)]
		squished = 0
		totalLen = len(lines) - 1
		
		for line in lines[:-1]:
			values = line.split()
			datapoint = []
			for x in self.massColumns:
				if x < 0:
					x = -x
					datapoint.append(rescaleWidth(float(values[x])))
				else:
					datapoint.append(float(values[x]))


			
			if self.refXsecs != None:
				m0 = datapoint[0]
				eff = datapoint[-1]
				xsec = self._getRefXsec(m0)
				if self.luminosity * xsec * eff < 1e-4: #1e-2
					if eff > 0.: squished += 1
					eff = 0.
					datapoint[-1] = eff
					
			#if eff != 0.:
			dataset.append(datapoint)

			if eff == 0.: x = 0
			else:
				x = int(-np.log10(eff)) + 1
			count[x] += 1

		for n,c in enumerate(count[:10]):
			if n == 0: p = 0
			else: p = 10**-n
			logger.debug("# effs at/below %s: %s" % (p, c))

		logger.debug("length of dataset: %s" %len(dataset))
		logger.debug("number of eff squished to 0: %s (%s%%)" % (squished, 100*round(squished/totalLen,2)))
		logger.debug("percentage of 0 efficiencies: %s%%" %(100*round(count[0]/totalLen,2)))
		
		return dataset
		


	def _createDataset(self, sampleSize = None):

		"""
		Generates datasets for training and evaluation and returns them as custom 'Data' class
		1. reads original grid points and PCA's them to reduce dimensionality
		2. mean-shift clusters PCA data to get points of high information density
		if classification:
			3. finds edges of original grid points
			4. draw points around edges
		5. draws points for each m-s cluster

		"""

		if sampleSize == None: sampleSize = self.sampleSize
		samplesLeft = sampleSize

		dataset = []
		particles = [0 for _ in range(self.full_dim)]
		tx = self.txnameData

		width = tx.widthPosition
		rescaleInputs = width != []

		if not hasattr(self, "_origData"):
			self._loadOrigData()

		if not hasattr(self, "_origPCA"):
			self._PCA()

		if not hasattr(self, "_origCluster"):
			self._clusterData()

		t0 = time()
		logger.info("drawing points..")

		if self.nettype == 'regression':

			clusterMeanVals, pointsToDrawPerCluster = self._addClusterBias(sampleSize)
			
			zeroes = 0
			drawnPoints = []

			for n, cluster in enumerate(self._origCluster):

				mean = np.mean(cluster, axis = 0)
				std = np.std(cluster, axis = 0)
				logger.debug("cluster %s/%s" % (n+1, len(self._origCluster)))
				pointsLeft = pointsToDrawPerCluster[n]

				while pointsLeft > 0:

					rand = []
					for i in range(tx.dimensionality):
						rand.append(np.random.normal(mean[i], 250. + 4.*std[i]))

					x = tx.coordinatesToData(rand, rotMatrix = tx._V, transVector = tx.delta_x)
					val = tx.getValueFor(x)
					val = removeUnits(val,physicsUnits.standardUnits)

					if self.refXsecs != None and val != None:
						x0 = x
						while type(x0) == list or type(x0) == tuple: x0 = x0[0]
						x0 = x0.asNumber(GeV)
						xsec = self._getRefXsec(x0)

						thresh = self.luminosity * xsec * val

						if thresh < 1e-2:
							val = 0.

					if type(val) != type(None) and ( clusterMeanVals[n] == 0 or (val != 0. or random() < 0.15) ): #0.1
						
						pointsLeft -= 1
						
						if val == 0.:
							zeroes += 1

						strippedUnits = tx.dataToCoordinates(x)
						strippedUnits.append(val)

						drawnPoints.append(strippedUnits)

			logger.debug("%s%% are Zero." % round(100.*(zeroes/len(drawnPoints)), 3))
						
		else:

			hullPoints = self._getHullPoints()

			hP_PCA = []
			numOfHullPoints = 0
			for axisPoints in hullPoints:
				numOfHullPoints += len(axisPoints)

				temp = self._PCA(axisPoints)
				hP_PCA.append(temp)

			samplesPerHullPoint = int(( sampleSize / numOfHullPoints ) * 0.75) #0.15)

			drawnPoints = []

			for currentMassHull in hP_PCA:

				#mean = np.mean(currentMassHull, axis = 0)
				std = np.std(currentMassHull, axis = 0)

				for point in currentMassHull:

					samplesPerHullPointLeft = samplesPerHullPoint

					while(samplesPerHullPointLeft > 0):

						rand = []
						for i in range(tx.dimensionality):
							rand.append(np.random.normal(point[i], 1.25*std[i]))

						x = tx.coordinatesToData(rand, rotMatrix = tx._V, transVector = tx.delta_x)
						val = tx.getValueFor(x)
						val = removeUnits(val,physicsUnits.standardUnits)

						if type(val) != type(None): val = 0.
						else: val = 1.

						strippedUnits = tx.dataToCoordinates(x)
						strippedUnits.append(val)
						drawnPoints.append(strippedUnits)

						samplesLeft -= 1
						samplesPerHullPointLeft -= 1

	
			samplesLeft = 0
			clusterMeanVals, pointsToDrawPerCluster = self._addClusterBias(samplesLeft)

			for n, cluster in enumerate(self._origCluster):

				mean = np.mean(cluster, axis = 0)
				std = np.std(cluster, axis = 0)

				logger.debug("cluster %s/%s" % (n+1, len(self._origCluster)))
				pointsLeft = pointsToDrawPerCluster[n]

				while pointsLeft > 0:

					rand = []
					for i in range(tx.dimensionality):
						rand.append(np.random.normal(mean[i], 2.*std[i]))

					x = tx.coordinatesToData(rand, rotMatrix = tx._V, transVector = tx.delta_x)
					val = tx.getValueFor(x)
					val = removeUnits(val,physicsUnits.standardUnits)

					if type(val) != type(None): val = 0.
					else: val = 1.
						
					pointsLeft -= 1
	
					strippedUnits = tx.dataToCoordinates(x)
					strippedUnits.append(val)

					drawnPoints.append(strippedUnits)

		logger.info("done. %ss" % round(time()-t0, 3))

		return drawnPoints



	def run(self, nettype, sampleSize = None, splitData = True, loadFromFile = None):

		self.nettype = nettype

		if loadFromFile == None:
			loadFromFile = self.loadFile != None

		if loadFromFile:
			points = self._loadDataset()
		else:
			points = self._createDataset(sampleSize)

		scaler = MinMaxScaler(feature_range=(1, 100))

		scaler = scaler.fit(points)
		points = scaler.transform(points)

		shuffle(points)
		dataset = Data(points, self.full_dim, self.device)

		self.dataset = {"full": dataset, "scaler": scaler}
		self.dataset["rescaleParameter"] = dataset.rescaleParameter
		if splitData:
			splitset = dataset.split(self.sampleSplit)
			self.dataset["training"]   = splitset[0]
			self.dataset["testing"]    = splitset[1]
			self.dataset["validation"] = splitset[2]

		return self.dataset
	
