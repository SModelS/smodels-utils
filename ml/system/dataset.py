#import sys
#sys.path.append('../../../smodels/')
#sys.path.append('../../../smodels-utils/')

import os, torch, unum, random, copy
from time import time
from system.readOrigData import *
from system.auxiliaryFunctions import *
from smodels.experiment.databaseObj import Database
from smodels.tools import physicsUnits
from smodels.tools.physicsUnits import GeV, fb
from smodels.tools.stringTools import concatenateLines
from smodels.theory.auxiliaryFunctions import rescaleWidth, unscaleWidth, removeUnits
from torch.autograd import Variable
from torch.utils.data import Dataset, DataLoader
from torch import nn
import numpy as np
from random import shuffle
from sklearn.cluster import MeanShift






class HyperParameter():

	def __init__(self, parameterDict):

		self.parameter = parameterDict
		self.combinations = {}
		self.numOfCombinations = 0

		paramIndex = {}
		done = False
		firstKey = list(self.parameter.keys())[0]
		lastKey = list(self.parameter.keys())[-1]

		while not done:

			endOfDict = True
			for key in parameterDict:
				currentParamLen = len(self.parameter[key])

				if not key in self.combinations:
					self.combinations[key] = []

					if key != firstKey: paramIndex[key] = 0
					else: paramIndex[key] = -1

				if endOfDict:
					if paramIndex[key] + 1 < currentParamLen:
						paramIndex[key] += 1
						endOfDict = False
					else:
						paramIndex[key] = 0
						endOfDict = True
						if key == lastKey: done = True

			if not done:
				self.numOfCombinations += 1
				for key in self.combinations:
					self.combinations[key].append(paramIndex[key])

	def __len__(self):
		return self.numOfCombinations

	def __getitem__(self, index):
		configuration = {"index": index}
		for key in self.parameter:
			configuration[key] = self.parameter[key][self.combinations[key][index]]
		return configuration

	def __str__(self):
		return str(self.parameter)









class Data(Dataset):

	"""
	Holds the actual datasets in torch.tensor format for training and evaluation

	"""

	def __init__(self, dataset, inputDimension, device, rescaleInputs = False, rescaleLabels = False):

		self.inputs = torch.tensor(dataset, dtype=torch.float32).narrow(1, 0, inputDimension).double().to(device)
		self.labels = torch.tensor(dataset, dtype=torch.float32).narrow(1, inputDimension, 1).double().to(device)

		mean = torch.mean(self.inputs)	#[torch.mean(self.inputs), torch.mean(self.labels)]
		std = torch.std(self.inputs)	#[torch.std(self.inputs), torch.std(self.labels)]

		self.rescaleParameter = {"mean": mean, "std": std}
		self.inputDimension = inputDimension
		self.device = device


	def __len__(self):
		return self.inputs.size()[0]


	def split(self, sampleSplit):

		if sum(sampleSplit) != 1.:
			logger.error("Dataset splice ratios don't add up to 1")

		length = len(self)
		start = 0

		splitData = [[] for i in range(len(sampleSplit))]

		for i in range(len(sampleSplit)):
			if i > 0: start += int(length * sampleSplit[i-1])
			end = int(length * sampleSplit[i])

			splitData[i] = copy.deepcopy(self)
			splitData[i].inputs = self.inputs.narrow(0, start, end)
			splitData[i].labels = self.labels.narrow(0, start, end)

		return splitData
				
	def __getitem__(self, index):
		return (self.inputs[index], self.labels[index])






class DatasetBuilder():

	"""
	Outputs a Dataset class that is used for training and evaluation of neural networks
	Needs metainfo of analysis and training parameters (usually loaded from nn_parameters.info file) as well as a device to send Dataset class to
	(cpu or specific gpu)


	"""

	def __init__(self, logger, paramDatabase, paramDataset, device):

		self.paramDatabase = paramDatabase
		self.paramDataset = paramDataset
		self.device = device
		self.logger = logger

		self.txNameData = self.paramDatabase["txNameData"]

		self.origData, self.origValues, self.units	= self._getOrigData()
		self.origDataMean		= np.mean(self.origData, axis = 0)
		self.origDataStd		= np.std(self.origData, axis = 0)
		self.inputDimension 	= self.txNameData.full_dimensionality

		### TEMPORARY to remove 1e6 widths ###
		self._removeBigWidths()

		self.og_PCA = None
		self.m_c = None


	def _removeBigWidths(self):

		widthPos = self.txNameData.widthPosition[0][1] + 1
		n = 0
		while n < len(self.origData):

			width = self.origData[n][widthPos]
			if width > 1e4:
				self.origData.pop(n)
			else:
				n += 1

		


	def _getOrigData(self):
		return  getOrigExpresData(self.paramDatabase, stripUnits = True)


	def _PCA(self, data = None):

		"""
		Perform PCA on any given masspoints (default = original grid points)

		"""

		if data == None: data = self.origData

		tx = self.txNameData
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

		#self.og_PCA = np.array([tx.dataToCoordinates(m, rotMatrix = tx._V, transVector = tx.delta_x) for m in ogOrdered])
		data_PCA = np.array([tx.dataToCoordinates(m, rotMatrix = tx._V, transVector = tx.delta_x) for m in ogOrdered])

		return data_PCA


	def _clusterData(self, bw = 8):

		"""
		Perform meanshift analysis on PCA grid points

		"""

		clustering = MeanShift(bandwidth = bw).fit(self.og_PCA)
			
		m_c = [[] for _ in range(len(clustering.cluster_centers_))]
		#drawnPoints_PCA = []
		
		for n, label in enumerate(clustering.labels_):
			m_c[label].append(self.og_PCA[n])

		self.m_c = m_c


	def _addClusterBias(self, sampleSize):
	
		"""
		Adding a bias to draw more points from clusters with non-zero values

		"""

		tx = self.txNameData
		clusterMeanVals = []
		zeroClusters, nonZeroClusters = 0, 0
		for n, cluster in enumerate(self.m_c):

				mean = np.mean(cluster, axis = 0)

				x = tx.coordinatesToData(mean, rotMatrix = tx._V, transVector = tx.delta_x)
				val = tx.getValueFor(x)
				val = removeUnits(val,physicsUnits.standardUnits)

				clusterMeanVals.append(val)

				if val == 0: zeroClusters += len(cluster)
				else: nonZeroClusters += len(cluster)
						

		# If number of gridpoints is greater than sampleSize 'factor' could be a negative value
		factor = max((sampleSize - zeroClusters) / nonZeroClusters, 1)

		pointsToDraw = []
		for n, cluster in enumerate(self.m_c):

			if clusterMeanVals[n] > 0:
				pointsToDraw.append(int(factor*len(cluster))+1)
			else:
				pointsToDraw.append(len(cluster))

		return clusterMeanVals, pointsToDraw



	def _getHullPoints(self):

		"""
		Algorithm that finds hull edges from original datapoints

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


	def generateNewSet(self, netType, sampleSize = None, shuffleData = True):

		"""
		Generates datasets for training and evaluation and returns them as custom 'Data' class
		1. reads original grid points and PCA's them to reduce dimensionality
		2. mean-shift clusters PCA data to get points of high information density
		if classification:
			3. finds edges of original grid points
			4. draw points around edges
		5. draws points for each m-s cluster

		"""

		if sampleSize == None: sampleSize = self.paramDataset["sampleSize"]
		samplesLeft = sampleSize

		dataset = []
		particles = [0 for _ in range(self.inputDimension)]
		tx = self.txNameData

		width = tx.widthPosition
		rescaleInputs = width != []

		#print(width)

		if type(self.og_PCA) == type(None):
			t0 = time()
			self.logger.info("PCA on orig data..")
			self.og_PCA = self._PCA()
			self.logger.info("done. %ss" % round(time()-t0, 3))

		if type(self.m_c) == type(None):
			t0 = time()
			self.logger.info("clustering..")
			self._clusterData()
			self.logger.info("done. %ss" % round(time()-t0, 3))

		t0 = time()
		self.logger.info("drawing points..")

		if netType == 'regression':
		

			clusterMeanVals, pointsToDrawPerCluster = self._addClusterBias(sampleSize)
			
			zeroes = 0
			drawnPoints = []
			for n, cluster in enumerate(self.m_c):

				mean = np.mean(cluster, axis = 0)
				std = np.std(cluster, axis = 0)
				print("cluster %s/%s" % (n+1, len(self.m_c))) #self.logger.debug
				pointsLeft = pointsToDrawPerCluster[n]

				while pointsLeft > 0:

					rand = []
					for i in range(tx.dimensionality):
						rand.append(np.random.normal(mean[i], 250. + 4.*std[i]))

					x = tx.coordinatesToData(rand, rotMatrix = tx._V, transVector = tx.delta_x)
					val = tx.getValueFor(x)
					val = removeUnits(val,physicsUnits.standardUnits)

					# temporary test
					if val != None:
						if val < 1e-6: val = 0.

					if type(val) != type(None) and ( clusterMeanVals[n] == 0 or (val != 0. or random.random() < 0.1) ):
						
						pointsLeft -= 1
						
						if val == 0.:
							zeroes += 1

						#val += 1e-5
						
						strippedUnits = tx.dataToCoordinates(x)
						strippedUnits.append(val)

						drawnPoints.append(strippedUnits)

			print("%s%% are Zero." % round(100.*(zeroes/len(drawnPoints)), 3)) #self.logger.debug
						
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

			for n, cluster in enumerate(self.m_c):

				mean = np.mean(cluster, axis = 0)
				std = np.std(cluster, axis = 0)

				self.logger.debug("cluster %s/%s" % (n+1, len(self.m_c)))
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

		self.logger.info("done. %ss" % round(time()-t0, 3))

		"""
		from sklearn.preprocessing import MinMaxScaler
		scaler = MinMaxScaler(feature_range=(1, 40))

		### transform everything except values ###
		splitA, splitB = [], []
		for dP in drawnPoints:
			splitA.append(dP[0:-1])
			splitB.append(dP[-1])

		scaler = scaler.fit(splitA)
		splitA = scaler.transform(splitA)
		splitA = np.array(splitA)
		splitB = np.array(splitB)
		splitB = splitB[np.newaxis, :].T
		drawnPoints = np.concatenate((splitA, splitB), axis=1)
		### --- ###

		#scaler = scaler.fit(drawnPoints)
		#drawnPoints = scaler.transform(drawnPoints)
		"""

		#for dp in drawnPoints[0:20]:
		#	print(dp)
		if shuffleData: shuffle(drawnPoints)
		dataset = Data(drawnPoints, self.inputDimension, self.device)
		return dataset

