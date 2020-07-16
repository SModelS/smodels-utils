#import sys
#sys.path.append('../../../smodels/')
#sys.path.append('../../../smodels-utils/')

import os, torch, unum, random, copy
try:
	from system.readOrigData import *
except:
	from system.readOrigData import *
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import GeV, fb
from smodels.tools.stringTools import concatenateLines
from smodels.theory.auxiliaryFunctions import rescaleWidth
from torch.autograd import Variable
from torch.utils.data import Dataset, DataLoader
from torch import nn
import numpy as np
from random import shuffle


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
			# Draw random number between convex hull minima and maxima for each axis
			# If branches are symmetric, masses drawn for 1st branch are copied to 2nd
			
			### MANUALLY ADD ORIG GRID POINTS != 0 (USED FOR WIDTH MAPS)

			
			for n, e in enumerate(self.origData):

				m = [e[0]*GeV, (e[1]*GeV, e[2]*GeV)]
				masses = [m, m]

				#print("input:")
				#print(masses)
				#print("data -> coordinates:")
				#zguz = tx.txnameData.dataToCoordinates(masses)
				#print(zguz)
				#print("coordinates -> data:")
				#zguz = tx.txnameData.coordinatesToData(zguz)
				#print(zguz)		

				#val = self.txNameData.getValueFor(masses)
				val = self.origValues[n]
				if val > 0.:
					new = [np.log(e[0]), rescaleWidth(e[1]), np.log(e[0]), rescaleWidth(e[1])]
					#new = [np.log(e[0]), np.log(e[1]), rescaleWidth(e[2]), np.log(e[0]), np.log(e[1]), rescaleWidth(e[2])]
					new.append(val+1e-5)
					dataset.append(new)
			
			###############################################
			
			self.convexHullMax[1] = 1e-14
			self.convexHullMax[3] = 1e-14
			self.axesDependancies[0][1]["dependancy"] = None
			self.axesDependancies[0][1]["constant"] = False
			self.axesDependancies[0][1]["offset"] = 0

			while(samplesLeft>0):

				print("sleft:", samplesLeft)

				if self.symmetric:
					for n in range(self.inputDimensionHalf):
						particles[n] = random.uniform(self.convexHullMin[n], self.convexHullMax[n])
					for n in range(self.inputDimensionHalf):
						particles[self.inputDimensionHalf+n] = particles[n]
				else:
					for n in range(self.inputDimension):
						particles[n] = random.uniform(self.convexHullMin[n], self.convexHullMax[n])

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

						#if n == 2:
						#	particles[n] = 10**(random.uniform(-22,2))
					
				'''REMOVE'''
				
				#masses = [[(particles[0]*GeV, particles[1]*GeV)], [(particles[0]*GeV, particles[1]*GeV)]]
				#mx = [particles[0]*GeV, (particles[1]*GeV, particles[2]*GeV)] 
				mx = [(particles[0]*GeV, particles[1]*GeV)] 
				#mx = [[p*GeV for p in particles[0:self.inputDimensionHalf]], [p*GeV for p in particles[self.inputDimensionHalf:self.inputDimension]]]
				masses = [mx, mx] # [[x,(y,w)], [x,(y,w)]]		


				val = self.txNameData.getValueFor(masses)

				if type(val) != type(None) and val < 1e-6: val = 0
				if type(val) != type(None) and ( val != 0 or random.random() < 0.05 ): #val != 0.0:
			
					if type(val) != float and type(val) != int: val = val.asNumber(fb) # IMPLEMENT FB AND PB

					#new = [p for p in particles]
					#new = [np.log(particles[0]), np.log(particles[1]), rescaleWidth(particles[2]), np.log(particles[0]), np.log(particles[1]), rescaleWidth(particles[2])]
					new = [np.log(particles[0]), rescaleWidth(particles[1]), np.log(particles[0]), rescaleWidth(particles[1])]

					#new.append(0.1 + rescaleWidth(eff))
					#new.append(( eff + 1e-5 ) * 1e3) #LLP OFFSET
					new.append(val + 1e-5)

					dataset.append(new)
					samplesLeft -= 1
					
						
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

			#print("sleft:", samplesLeft)

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

		#import matplotlib.pyplot as plt
		#plt.figure(99)
		#plt_dots = plt.scatter([m[0] for m in expresData],[m[1] for m in expresData], color = 'gray', alpha=0.5)
		#plt_dots = plt.scatter([m[0] for m in massesHull[0]],[m[1] for m in massesHull[0]], color = 'green')
		#plt_dots = plt.scatter([m[0] for m in massesHull[1]],[m[1] for m in massesHull[1]], color = 'blue')
		#plt.show()

		if shuffleData: shuffle(dataset)
		dataSet = Data(dataset, self.inputDimension, self.device)
		return dataSet

