#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import torch
import numpy as np
from time import time
from copy import deepcopy
from random import random, shuffle
from scipy.spatial import ConvexHull#, convex_hull_plot_2d
from scipy.spatial import Delaunay
from sklearn.cluster import MeanShift
from mlCore.auxiliary import loadGridPoints
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

		if isinstance(dataset, tuple):
			self.inputs = torch.tensor(dataset[0], dtype=torch.float64).to(device)
			self.labels = torch.tensor(dataset[1], dtype=torch.float64).to(device)
		else:
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




	def _loadGridPoints(self, loadFromFile, includeExtremata = False, targetMinimum = 1e-14):

		"""
		Load grid points from either txnameData orig points or an external file and store them in self._gridPoints and self._gridTargets
		This method is still under construction and subject of constant change, so code is not very pretty at the moment.
		If masses or targets are rescaled - depending on the rescaling method - it is advised to include minima and maxima of each parameter axis in the dataset

		:param loadFromFile: flag if loading from external file string stored in self.loadFile (boolean)
		:param includeExtremata: flag to make sure we include minima and maxima of each axis in the dataset (boolean)
		:param targetMinimum: target values (effs/ULs) below this threshold will be set to this number instead to avoid having 0s or really small targets in the dataset

		"""

		if not loadFromFile:
			self._gridPoints = loadGridPoints(self.expres, self.txnameData, self.dataselector, self.signalRegion, stripUnits = True)[0]
			return


		logger.info("loading dataset (%s)" % self.nettype)
		
		with open(self.loadFile) as txtFile:
			raw = txtFile.read()

		lines = raw.split("\n")[1:]

		dataset_masses = []
		dataset_targets = []
		count = [0 for n in range(20)]
		squished = 0
		totalLen = len(lines) - 1

		minimum = [[[1e4 for _ in range(self.full_dim)], [0]] for _ in range(self.full_dim)]
		maximum = [[[0. for _ in range(self.full_dim)], [0]] for _ in range(self.full_dim)]

		#X = []
		#Y = []
		tmax = 0

		for line in lines[:-1]:
			values = line.split()
			masses = []

			width = 0

			for x in self.massColumns[:-1]:
				if x < 0:
					x = -x
					
					width = float(values[x])

					### set 0 width to 1e-30
					#if values[x] == 0.:
					#	masses.append(rescaleWidth(1e-30))
					#else:
					###

					masses.append(rescaleWidth(float(values[x])))
				else:
					masses.append(float(values[x]))

			target = float(values[self.massColumns[-1]])
			
			
			if self.refXsecs != None:
				m0 = masses[0]
				xsec = self._getRefXsec(m0)

				if self.luminosity * xsec * target < 1e-2:
					
					if target > 0.: squished += 1
					target = 0.
			

			#if target < targetMinimum: target = targetMinimum

			for n,mass in enumerate(masses):
				if minimum[n][0][n] > mass:
					minimum[n] = [masses, target]
				elif maximum[n][0][n] < mass:
					maximum[n] = [masses, target]
					

			#if target > 1e-14:# and m0 > 250. and width < 1e-17:
			#if target > targetMinimum:# or random() > 0.9:
			if target != 0.:
				dataset_masses.append(masses)
				dataset_targets.append(target)

				#if m0 == 140.:
					#print("%s\t%s"%(width, target))

				#	X.append(np.log10(width))
				#	Y.append(np.log10(target))

			

			if target == 0.: x = 0
			else:
				x = int(-np.log10(target)) + 1
			count[x] += 1

		"""
		import matplotlib.pyplot as plt
		plt.figure(55)
		plt.title(r"SR1FULL_175, THSCPM1b, $m_{HSCP}$ = 140 GeV", fontsize=14)
		plt.xlabel("widths [log10]")
		plt.ylabel("effs [log10]")
		plt.plot(X,Y)
		plt.show()

		"""
		
		if includeExtremata:

			for mini in minimum:
				if not mini[0] in dataset_masses:
					target = max(targetMinimum,mini[1])
					print("t:", target)
					dataset_masses.append(mini[0])
					dataset_targets.append(target)
			for maxi in maximum:
				if not maxi[0] in dataset_masses:
					target = max(targetMinimum,maxi[1])
					dataset_masses.append(maxi[0])
					dataset_targets.append(target)
		
		for n,c in enumerate(count[:10]):
			if n == 0: p = 0
			else: p = 10**-n
			logger.debug("# effs at ~%s: %s" % (p, c))

		
		self._gridPoints = dataset_masses
		self._gridTargets = dataset_targets

		logger.debug("length of dataset: %s" %len(dataset_masses))
		logger.debug("number of eff squished to 0: %s (%s%%)" % (squished, 100*round(squished/totalLen,2)))
		logger.debug("percentage of 0 efficiencies: %s%%" %(round(100*count[0]/totalLen, 2)))
		logger.debug("taget minimum: %s" % min(self._gridTargets))
		logger.debug("taget maximum: %s" % max(self._gridTargets))

		

		


	def _PCA(self, data = None):

		"""
		Perform PCA on any given masspoints (default = original grid points)

		:param data: alternative datapoints, default are original gridpoints of current map

		"""

		if data == None: data = self._gridPoints

		tx = self.txnameData
		ogOrdered = []
		if tx.widthPosition != []:
			for og in data:
				temp, mw = [], []
				for n, m in enumerate(og):	# OG DATA LOADED FROM SMODELS RIGHT NOW DOESNT HAVE EFFS, LOADED FROM FILES HAS THOUGH
					if n == tx.widthPosition[int(n/tx.dimensionality)][1] + 1 + int(n/tx.dimensionality) * tx.dimensionality:
						mw.append(rescaleWidth(m))
					else:
						temp.append(m)
				for w in mw: temp.append(w)
				ogOrdered.append(tx.coordinatesToData(temp))
		else: 
			for og in data:			
				ogOrdered.append(tx.coordinatesToData(og))


		pca = np.array([tx.dataToCoordinates(m, rotMatrix = tx._V, transVector = tx.delta_x) for m in ogOrdered])

		if data == self._gridPoints:
			self._origPCA = pca

		return pca


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

				print(cluster)
				mean = np.mean(cluster, axis = 0)
				print(mean)
				x = tx.coordinatesToData(mean, rotMatrix = tx._V, transVector = tx.delta_x)
				print(x)
				val = tx.getValueFor(x)
				val = removeUnits(val,physicsUnits.standardUnits)

				print("VAL: %s" %val)

				clusterMeanVals.append(val)

				if val == 0: zeroClusters += len(cluster)
				else: nonZeroClusters += len(cluster)
						

		# If number of gridpoints is greater than sampleSize, 'factor' could be a negative value
		factor = max((sampleSize - zeroClusters) / nonZeroClusters, 1)

		pointsToDraw = []
		for n, cluster in enumerate(self._origCluster):

			#print("cluster[%s] = %s"%(n, cluster))

			print("meanval: %s" %clusterMeanVals[n])
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

		massesSorted = [sorted(self._gridPoints,key=lambda l:l[n]) for n in range(len(self._gridPoints[0]))]
		#massesHull = []

		massesHull = [[] for _ in range(len(massesSorted))]

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

				massesSortedReduced.append(np.max(subset, axis=0).tolist())
				#massesSortedReduced.append(max(subset, key=lambda x:x[k])) this should work but doesnt for some reason?

			massesHull[k] = massesSortedReduced

			#if "massesHull" in locals():
			#	massesHull = np.append(massesHull, massesSortedReduced, axis=0)
			#else:
			#	massesHull = massesSortedReduced
			#	#print(massesHull)

			#massesHull.append(massesSortedReduced)


		# getting rid of duplicate axes

		n = 0
		while n < len(massesHull)-1:
			n += 1
			for m in massesHull[:n]:
				if massesHull[n] == m:
					massesHull.pop(n)
					n -= 1
					continue


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

		


	def _isOnHull(self, point):

		"""
		:param point: massPoint eg [m0,m1,w]
		returns boolean if within convex hull of grid points

		"""
		return self._delauney.find_simplex(point)>=0


	def _getHullDelauney(self):

		"""
		first calculates convex hull of self._gridPoints
		then performs delauney triangulation of vertices for easy determination
		if drawn mass points are within convex hull


		"""

		axis, dupl = [], []
		for n,c in enumerate(self.massColumns[:-1]):
			if not c in dupl:
				dupl.append(c)
				axis.append(n)
			

		splicedData = np.array([np.array(self._gridPoints)[:, a] for a in axis]).T
		hull = ConvexHull(splicedData)

		hullPoints = []
		for vert in hull.vertices:
			hullPoints.append(splicedData[vert])

		self._delauney = Delaunay(hullPoints)

		"""
		### get some visual confirmation ###
		import matplotlib.pyplot as plt
		plt.plot(splicedData[:,0], splicedData[:,1], 'o')
		for simplex in hull.simplices:
			plt.plot(splicedData[simplex, 0], splicedData[simplex, 1], 'k-')


		plt.plot(splicedData[hull.vertices,0], splicedData[hull.vertices,1], 'r--', lw=2)
		plt.plot(splicedData[hull.vertices[0],0], splicedData[hull.vertices[0],1], 'ro')
		plt.show()
		### --- ###
		"""


	def _drawRandomPoints(self, sampleSize = None):

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


		particles = [0 for _ in range(self.full_dim)]
		tx = self.txnameData

		width = tx.widthPosition
		rescaleInputs = width != []

		drawnMasses = []
		drawnTargets = []


		if not hasattr(self, "_origPCA"):
			self._PCA()

		if not hasattr(self, "_origCluster"):
			self._clusterData()

		t0 = time()
		logger.info("drawing points..")

		if self.nettype == 'regression':

			clusterMeanVals, pointsToDrawPerCluster = self._addClusterBias(sampleSize)
			
			zeroes = 0

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
						drawnMasses.append(strippedUnits)
						drawnTargets.append(val)

			logger.debug("%s%% are Zero." % round(100.*(zeroes/len(drawnMasses)), 3))
						
		else:

			hullPoints = self._getHullPoints()


			"""
			X = [p[0] for p in hullPoints[0]]
			Y = [p[2] for p in hullPoints[0]]
			import matplotlib.pyplot as plt
			plt.figure(55)
			plt.title(r"SR1FULL_175, THSCPM1b, $m_{HSCP}$ = 140 GeV", fontsize=14)
			plt.xlabel("m0 [GeV]")
			plt.ylabel("widths [log10(w+1)]")
			plt.plot(X,Y)
			plt.show()
			"""

			hP_PCA = []
			numOfHullPoints = 0
			for axisPoints in hullPoints:
				numOfHullPoints += len(axisPoints)

				temp = self._PCA(axisPoints)
				hP_PCA.append(temp)

			samplesPerHullPoint = max(1,int(( sampleSize / numOfHullPoints ) * 0.75)) #0.15)


			for currentMassHull in hP_PCA:

				#mean = np.mean(currentMassHull, axis = 0)
				std = np.std(currentMassHull, axis = 0)

				for point in currentMassHull:

					samplesPerHullPointLeft = samplesPerHullPoint

					while(samplesPerHullPointLeft > 0):

						rand = []
						for i in range(tx.dimensionality):
							rand.append(np.random.normal(point[i], 0))#1.25*std[i]))

						x = tx.coordinatesToData(rand, rotMatrix = tx._V, transVector = tx.delta_x)
						val = tx.getValueFor(x)
						val = removeUnits(val,physicsUnits.standardUnits)

						if type(val) != type(None): val = 0.
						else: val = 1.

						strippedUnits = tx.dataToCoordinates(x)
						drawnMasses.append(strippedUnits)
						drawnTargets.append(val)

						samplesLeft -= 1
						samplesPerHullPointLeft -= 1

						logger.debug("points drawn: %s" % len(drawnMasses))

			"""
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

					drawnMasses.append(strippedUnits)
					drawnTargets.append(val)
					logger.debug("points drawn: %s" % len(drawnMasses))
			"""

		self.masses = drawnMasses
		self.targets = drawnTargets



		X = [m[0] for m in self.masses]
		Y = [m[2] for m in self.masses]
		import matplotlib.pyplot as plt
		plt.figure(55)
		plt.title(r"SR1FULL_175, THSCPM1b", fontsize=14)
		plt.xlabel("m0 [GeV]")
		plt.ylabel("widths [log10(w+1)]")
		plt.scatter(X,Y)
		plt.show()
		

		logger.info("done. %ss" % round(time()-t0, 3))




	def run(self, nettype, loadFromFile = None, sampleSize = None):

		"""
		Generate self.masses and self.targets for the dataset. Points will either be drawn randomly from the txnamedata interpolation
		or read from an external file.

		:param nettype: (string) 'regression' or 'classification' type dataset will be generated.
		:param loadFromFile: (optional) (boolean) Specify drawing points via interpolation method or read an external file.
		:param sampleSize: (optional) (float) Override the number of points drawn. Only used when using interpolation, default = self.sampleSize.

		"""

		self.nettype = nettype

		if loadFromFile == None:
			loadFromFile = self.loadFile != None

		if not hasattr(self, "_gridPoints"):
			self._loadGridPoints(loadFromFile)

		
		if self.nettype == "regression":

			if loadFromFile:
				self.masses = np.array(self._gridPoints)
				self.targets = np.array(self._gridTargets)

			else:
				self._drawRandomPoints()



		elif self.nettype == "classification":

			self.masses = np.array(self._gridPoints)
			self.targets = np.array(self._gridTargets)

			"""

			if loadFromFile:
				print("get hull")
				if not hasattr(self, "_delauney"):
					self._getHullDelauney()

				print("draw points")
				self._drawRandomPoints()

			else:
				#self._getHullPoints()
				#self._addClusterBias()
				self._drawRandomPoints()

			"""

			#self.masses, self.targets = np.array(self._gridPoints), np.array(self._gridTargets)
			#masses, targets = self._gridPoints, self._gridTargets = self._gridPoints #self._createDataset(sampleSize)
	
	


	def rescaleMasses(self, method = "minmaxScaler"):

		"""
		Rescale masses either via minmax scaler or standard score.

		:param method: (optional) (string) Specify which method to use. Currently available: 'minmaxScaler' and 'standardScore'.

		"""

		if method == "minmaxScaler":
			scaler = MinMaxScaler(feature_range=(1, 100))
			scaler = scaler.fit(self.masses)
			self.masses = scaler.transform(self.masses)

			if not "rescale" in self.__dict__:
				self.rescale = {}

			self.rescale["masses"] = {"method": method, "scaler": scaler}

		elif method == "standardScore":

			if not "rescale" in self.__dict__:
				self.rescale = {}

			# TBD
		else:
			logger.error("%s: unrecognized rescale method." % method)



	def rescaleTargets(self, method = "log", lmbda = None):

		"""
		Rescale targets via boxcox method. Mainly used for LLP maps with very low and lots of 0 efficiencies.

		:param method: (optional) (string) Method used for rescaling. Options: log, boxcox.
		:param lmbda: (optional) (float) Used for a fixed boxcox transformation. If set to 'None' boxcox will find an optimal lmbda automatically. Default = None

		"""

		if method == "boxcox":

			from scipy.stats import boxcox

			if lmbda == None:
				self.targets, lmbda = boxcox(self.targets)
			else:
				self.targets = boxcox(self.targets, lmbda)

			logger.debug("lambda: %f" % lmbda)

			
			#self.targets = np.array(self.targets)[np.newaxis]
			#self.targets = self.targets.T

			#self.targets = -self.targets

		elif method == "log":

			self.targets = np.log10(self.targets)


		self.targets = np.array(self.targets)[np.newaxis]
		self.targets = self.targets.T

		if not "rescale" in self.__dict__:
				self.rescale = {}

		self.rescale["targets"] = {"method": method, "lambda": lmbda}



	def shuffle(self):

		"""
		Shuffle masses and targets if necessary.
		"""

		indices = np.arange(self.targets.shape[0])
		np.random.shuffle(indices)

		self.masses = self.masses[indices]
		self.targets = self.targets[indices]


	def getDataset(self, fullSet = True, splitSet = True, rescaleParams = True):

		"""
		Generate output dictionary.

		:param fullSet: (boolean) Return the full dataset.
		:param splitSet: (optional) (boolean) Split and return full set into subsets specified via self.sampleSplit list.
		:param rescaleParams: (optional) (boolean) Return used rescale parameters of 'self.rescaleMasses' and 'self.rescaleTargets' method.

		:return output: (dict) May contain keys 'full', 'training', 'testing', 'validation' and 'rescaleParams'.
		"""

		output = {}

		if rescaleParams:
			if hasattr(self, "rescale"):
				output["rescaleParams"] = self.rescale

				keys = ["masses", "targets"]
				for key in keys:
					if not key in output["rescaleParams"]:
						output["rescaleParams"][key] = {"method": None}

			else:
				output["rescaleParams"] = {"masses": {"method": None}, "targets": {"method": None}}

		if fullSet or splitSet:
			full = Data((self.masses, self.targets), self.full_dim, self.device)

		if fullSet:
			output["full"] = full

		if splitSet:
			splitset = full.split(self.sampleSplit)
			output["training"]   = splitset[0]
			output["testing"]    = splitset[1]
			output["validation"] = splitset[2]

		return output
	
