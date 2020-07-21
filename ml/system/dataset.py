#import sys
#sys.path.append('../../../smodels/')
#sys.path.append('../../../smodels-utils/')

import os, torch, unum, random, copy
try:
	from system.readOrigData import *
except:
	from system.readOrigData import *
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


def MSErel(predicted, label, reduction = "mean"):
	#loss = torch.abs((input-label)/label)
	#if reduction == "mean": loss = torch.mean(loss)
	#if label != 0.:
	#	loss = ((input-label)/label)**2
	#else: loss = input**2
	#print(predicted)
	#print(label)
	#print("---")
	loss = ((predicted-label)/label)**2
	if reduction == "mean": loss = torch.sqrt(torch.mean(loss))
	return loss
"""

def MSErel(predicted, label, reduction = "mean"):
	loss = torch.abs(torch.log(predicted/label))
	#print(predicted)
	#print(label)
	#print("---")
	if reduction == "mean": loss = torch.mean(loss)
	return loss


def MSErel(predicted, label, reduction = "mean"):

	loss = ( (predicted-label)/(predicted+label) )**2
	if reduction == "mean": loss = torch.sqrt(torch.mean(loss))
	return loss
"""

def loadOptimizer(optimizerName, model, learnRate):
	if optimizerName == "Adam":
		optimizer = torch.optim.Adam(model.parameters(), lr=learnRate)
	else:
		optimizer = torch.optim.Adam(model.parameters(), lr=learnRate)
		logger.warning("Invalid optimizer selected. Only Adam is supported currently. Continuing on Adam" %args.parfile)

	return optimizer

def loadLossFunction(lossFunctionName, device):
	if lossFunctionName == "MSE": lossFunction = nn.MSELoss(reduction = 'mean').to(device)
	elif lossFunctionName == "MSErel": lossFunction = MSErel
	elif lossFunctionName == "BCE": lossFunction = nn.BCELoss(reduction = 'mean').to(device)

	return lossFunction



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





def GetModel(expres, topo, netType):

	savedir = expres.path + '/data/'
		
	#temporary relocation
	for i in range(len(savedir)):
		if savedir[i:i+8] == 'database':
			savedir = savedir[:i] + 'utils/ml/storage' + savedir[i+8:]

	pth = savedir + str(topo) + '_' + netType + '.pth'

	if os.path.exists(pth):

		model = torch.load(pth)
		model.eval()

	else: model = None

	return model



class Data(Dataset):

	def __init__(self, dataset, inputDimension, device, rescaleInputs = False, rescaleLabels = False):

		self.inputs = torch.tensor(dataset, dtype=torch.float32).narrow(1, 0, inputDimension).to(device)
		self.labels = torch.tensor(dataset, dtype=torch.float32).narrow(1, inputDimension, 1).to(device)

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



	"""

	def __init__(self, logger, paramDatabase, paramDataset, device):

		self.paramDatabase = paramDatabase
		self.paramDataset = paramDataset
		self.device = device
		self.logger = logger

		self.txNameData = self.paramDatabase["txNameData"]

		self.axesDependancies	= self._getAxes()
		self.origData, self.origValues, self.units	= self._getOrigData()
		self.origDataMean		= np.mean(self.origData, axis = 0)
		self.origDataStd		= np.std(self.origData, axis = 0)
		self.inputDimension 	= self.txNameData.full_dimensionality
		self.inputDimensionHalf = int(0.5*self.inputDimension)
		self.convexHullMin 		= np.min(self.origData, axis=0)
		self.convexHullMax 		= np.max(self.origData, axis=0)

		isSymmetric = True
		for line in self.origData:
			if not line[0:self.inputDimensionHalf] == line[self.inputDimensionHalf:self.inputDimension]:
				isSymmetric = False
				break
		self.symmetric = isSymmetric


	def _getOrigData(self):
		return getOrigExpresData(self.paramDatabase, stripUnits = True)


	def _getAxes(self):
		return getAxesData(self.logger, self.paramDatabase)


	def generateNewSet(self, netType, sampleSize = None, shuffleData = True):

		if sampleSize == None: sampleSize = self.paramDataset["sampleSize"]

		dataset = []
		particles = [0 for _ in range(self.inputDimension)]

		samplesLeft = sampleSize


		if netType == 'regression':

			# Create dataset for our regression network
			# Perform PCA and mean shift on original grid points
			# Draw dataset points around each cluster
			
			tx = self.txNameData

			#print("full dim: %s" % tx.full_dimensionality)
			#print("dim: %s" % tx.dimensionality)
			#print("widthpos:",tx.widthPosition)
			#print("\n")

			ogOrdered = []
			if tx.widthPosition != []:
				for og in self.origData:
					temp, mw = [], []
					for n, m in enumerate(og):
						if n == tx.widthPosition[int(n/tx.dimensionality)][1] + 1 + int(n/tx.dimensionality) * tx.dimensionality:
							mw.append(rescaleWidth(m))
						else:
							temp.append(m)
					for w in mw: temp.append(w)
					ogOrdered.append(tx.coordinatesToData(temp))
			else: 
				for og in self.origData:			
					ogOrdered.append(tx.coordinatesToData(og))

			og_PCA = np.array([tx.dataToCoordinates(m, rotMatrix = tx._V, transVector = tx.delta_x) for m in ogOrdered])

			clustering = MeanShift(bandwidth=8).fit(og_PCA)

			m_c = [[] for _ in range(len(clustering.cluster_centers_))]
			drawnPoints_PCA = []
			drawnPoints = []
			zeroes = 0

			for n, label in enumerate(clustering.labels_):
				m_c[label].append(og_PCA[n])

			singleClusters = 0
			for n, cluster in enumerate(m_c):
				mean = np.mean(cluster, axis = 0)
				std = np.std(cluster, axis = 0)

				#if len(cluster) == 1: singleClusters += 1
			
				pointsToDraw = int(len(cluster)*sampleSize/len(self.origData)) + 1

				while pointsToDraw > 0:

					rand = []
					for i in range(tx.dimensionality):
						rand.append(np.random.normal(mean[i], 180. + 2.*std[i]))

					x = tx.coordinatesToData(rand, rotMatrix = tx._V, transVector = tx.delta_x)
					val = tx.getValueFor(x)
					val = removeUnits(val,physicsUnits.standardUnits)

					if type(val) != type(None) and (val != 0. or random.random() < 0.1):
						
						pointsToDraw -= 1

						#if val == 0.:
						#	zeroes += 1

						val += 1e-5
						
						strippedUnits = tx.dataToCoordinates(x)
						strippedUnits.append(val)

						#drawnPoints_PCA.append(rand)
						drawnPoints.append(strippedUnits)

			#drawnPoints_PCA = np.array(drawnPoints_PCA)
			dataset = drawnPoints

			drawnPoints = np.array(drawnPoints)

			for n in range(10):
				print(dataset[n])

			#print("%s%% are Zero." % round(100.*(zeroes/sampleSize), 3))
			#print("min num of drawn points = %s" % int(10000/len(self.origData)))
			#print("detected %s clusters in %s datapoints" % (len(m_c), len(self.origData)))
			#print("%s of those are 1dim\n" % singleClusters)

			#import matplotlib.pyplot as plt
			#plt.figure(0)
			#plt.scatter(drawnPoints[:,0], drawnPoints[:,1])
			#plt.tight_layout()
			#plt.show()
						
		else:

			
			# Particle widths (at least for 2016-32-eff) range from 1e-22 - 1e+6 and thus will always be on shell
			#widthPos = 2
			#self.axesDependancies[0][widthPos]["dependancy"] = None
			#self.axesDependancies[0][widthPos]["constant"] = True
			#self.axesDependancies[0][widthPos]["offset"] = 0

			# Create dataset for our classification network
			# First we generate a rough estimate of our convex hull with "massesHull"
			# Then we draw points around the hull and finish populating our dataset with
			# random points drawn around the center of our hull
			
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


			numOfHullPoints = 0
			for axisPoints in massesHull:
				numOfHullPoints += len(axisPoints)
			samplesPerHullPoint = int(( sampleSize / numOfHullPoints ) * 0.15) #0.75)
				
			for currentMassHull in massesHull:

				for point in currentMassHull:

					samplesPerHullPointLeft = samplesPerHullPoint

					#isMin = point[0] == self.convexHullMin[0] or point[1] == self.convexHullMin[1]
					#isMax = point[0] == self.convexHullMax[0] or point[1] == self.convexHullMax[1]

					#if isMin or isMax:
					#	samplesPerHullPointLeft *= 5

					while(samplesPerHullPointLeft > 0):

						for n in range(self.inputDimension):

							if ( self.symmetric and n == self.inputDimensionHalf - 1 ) or ( not self.symmetric and n == self.inputDimension - 1 ):
								std = 25. #45.
							else:
								std = 25. #abs(point[n] - point[n+1]) * 0.15 #0.25
							mean = point[n]

							particles[n] = abs(np.random.normal(mean, std, 1)[0])

						if self.symmetric:
							for n in range(self.inputDimensionHalf):

								dep = self.axesDependancies[0][n]["dependancy"]
								con = self.axesDependancies[0][n]["constant"]
								off = self.axesDependancies[0][n]["offset"]

								if type(dep) == list:
									particles[n] = 0.5 * ( particles[dep[0]] + particles[dep[1]] )
								elif dep != None:
									particles[n] = particles[dep] + off
								elif con:
									particles[n] = off

								particles[self.inputDimensionHalf+n] = particles[n]


						'''REMOVE'''
						#masses = [[p*GeV for p in particles[0:inputDimensionHalf]], [p*GeV for p in particles[inputDimensionHalf:inputDimension]]]
						#masses = [[(particles[0]*GeV, particles[1]*GeV)], [(particles[0]*GeV, particles[1]*GeV)]] # [[(x,w)], [(x,w)]]
						mx = [(particles[0]*GeV, particles[1]*GeV)] 
						#mx = [particles[0]*GeV, (particles[1]*GeV, particles[2]*GeV)] 
						masses = [mx, mx] # [[x,(y,w)], [x,(y,w)]]

						res = self.txNameData.getValueFor(masses)

						#if SR == None:
						#	res = expres.getUpperLimitFor(txname=topo, mass=masses)
						#else:
						#	res = expres.getEfficiencyFor(txname=topo, mass=masses, dataset=SR)

						'''REMOVE'''
						# 2dim
						#new = [np.log(particles[0]), np.log(particles[1]), rescaleWidth(particles[2]), np.log(particles[0]), np.log(particles[1]), rescaleWidth(particles[2])]
						new = [np.log(particles[0]), np.log(particles[1]), 0, np.log(particles[0]), np.log(particles[1]), 0]

						# 1dim
						#new = [np.log(particles[0]), rescaleWidth(particles[1]), np.log(particles[0]), rescaleWidth(particles[1])]
						#new = [np.log(particles[0]), 0, np.log(particles[0]), 0]

						#new = [np.log(p) if p != 0 else p for p in particles] 
						if type(res) != type(None): new.append(1.)
						else: new.append(0.)
					
						dataset.append(new)
						samplesLeft -= 1
						samplesPerHullPointLeft -= 1


						#masses = [[p*GeV for p in particles[0:inputDimensionHalf]], [p*GeV for p in particles[inputDimensionHalf:inputDimension]]]
						#ul	   = expres.getUpperLimitFor(txname=topo, mass=masses)

						#new = [p for p in particles]
						#if type(ul) != type(None): new.append(1.)
						#else: new.append(0.)
					
						#dataset.append(new)
						#samplesLeft -= 1
						#samplesPerHullPointLeft -= 1

		

			while(samplesLeft>0):

				print("sleft:", samplesLeft)

				if self.symmetric:
					for n in range(self.inputDimensionHalf):
						particles[n] = abs(np.random.normal(self.origDataMean[n], self.origDataStd[n]*2., 1)[0])


					for n in range(self.inputDimensionHalf):

						dep = self.axesDependancies[0][n]["dependancy"]
						con = self.axesDependancies[0][n]["constant"]
						off = self.axesDependancies[0][n]["offset"]

						if type(dep) == list:
							particles[n] = 0.5 * ( particles[dep[0]] + particles[dep[1]] )
						elif dep != None:
							particles[n] = particles[dep] + off
						elif con:
							particles[n] = off

						particles[self.inputDimensionHalf+n] = particles[n]

				else:
					for n in range(self.inputDimension):
						particles[n] = abs(np.random.normal(self.origDataMean[n], self.origDataStd[n], 1)[0])
					

				'''REMOVE'''
				#masses = [[p*GeV for p in particles[0:inputDimensionHalf]], [p*GeV for p in particles[inputDimensionHalf:inputDimension]]]
				#masses = [[(particles[0]*GeV, particles[1]*GeV)], [(particles[0]*GeV, particles[1]*GeV)]]

				#mx = [particles[0]*GeV, (particles[1]*GeV, particles[2]*GeV)] 
				mx = [(particles[0]*GeV, particles[1]*GeV)] 
				masses = [mx, mx] # [[x,(y,w)], [x,(y,w)]]		

				res = self.txNameData.getValueFor(masses)

				'''REMOVE'''
				# 2dim
				#new = [np.log(particles[0]), np.log(particles[1]), rescaleWidth(particles[2]), np.log(particles[0]), np.log(particles[1]), rescaleWidth(particles[2])]
				#new = [np.log(particles[0]), np.log(particles[1]), 0, np.log(particles[0]), np.log(particles[1]), 0]

				# 1dim
				#new = [np.log(particles[0]), rescaleWidth(particles[1]), np.log(particles[0]), rescaleWidth(particles[1])]
				new = [np.log(particles[0]), 0, np.log(particles[0]), 0]

				#new = [np.log(p) if p != 0 else p for p in particles] 
				if type(res) != type(None): new.append(1.)
				else: new.append(0.)
				
				#if type(res) == type(None) or random.random() < 0.25:
				dataset.append(new)
				samplesLeft -= 1
					#print(samplesLeft)


		if shuffleData: shuffle(dataset)
		dataSet = Data(dataset, self.inputDimension, self.device)
		return dataSet

