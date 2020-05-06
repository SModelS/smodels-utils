#import sys
#sys.path.append('../../../smodels/')
#sys.path.append('../../../smodels-utils/')

import os, torch, unum, random, copy
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import GeV, fb
from torch.autograd import Variable
from torch.utils.data import Dataset, DataLoader
from torch import nn
import numpy as np
from random import shuffle


def MSErel(input, label, reduction = "mean"):
	#loss = torch.abs((input-label)/label)
	#if reduction == "mean": loss = torch.mean(loss)
	loss = ((input-label)/label)**2
	if reduction == "mean": loss = torch.sqrt(torch.mean(loss))
	return loss

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




#quick hack to load datapoints from data/txName.txt file
def getExpresData(expres, txName):

	path = expres.path + '/data/' + txName + '.txt'
		
	with open(path, "r") as file:
		data = file.readlines()

	for n in range(len(data)):
		if data[n][0:11] == "upperLimits":
			data[n] = data[n].replace("upperLimits:","")
			data = data[n:len(data)]
			break

	expresData = []
	for line in data:
		line = line.replace(',','')
		line = line.replace('[[[','')
		line = line.replace('][','')
		line = line.replace(']]','')
		line = line.replace('[','')
		line = line.replace(']','')
		line = line.replace('\n','')
		line = line.replace(' ','')
		values = line.split('*GeV')
		new = []
		for v in values[:-1]:
			new.append(float(v))

		expresData.append(new)

	expresData = np.array(expresData)
	return expresData



def generateDataset(expres, topo, massRange, sampleSize, dataType, device, shuffleData=True):

	analysis = expres.getDataset(None)

	for tx in analysis.txnameList: 
		if tx == topo or tx.txName == topo:

			#gather information for topology we are training on
			#so we can create an efficient dataset

			expresData 			= getExpresData(expres, topo)
			expresDataMean		= np.mean(expresData, axis = 0)
			expresDataStd		= np.std(expresData, axis = 0)
			inputDimension 		= tx.txnameData.full_dimensionality
			inputDimensionHalf 	= int(0.5*inputDimension)
			convexHullMin 		= np.min(expresData, axis=0)
			convexHullMax 		= np.max(expresData, axis=0)

			isSymmetric = True
			for entry in expresData:
				if not all(entry[0:inputDimensionHalf] == entry[inputDimensionHalf:inputDimension]):
					isSymmetric = False
					break
			break

	samplesLeft = sampleSize
	dataset = []
	particles = [0 for _ in range(inputDimension)]

	if dataType == 'regression':

		#create dataset for our regression network
		#draw random number between convex hull minima and maxima for each axis
		#if branches are symmetric, masses drawn for 1st branch are copied to 2nd
		
		while(samplesLeft>0):

			if isSymmetric:
				for n in range(inputDimensionHalf):
					particles[n] = random.uniform(convexHullMin[n], convexHullMax[n])
				for n in range(inputDimensionHalf):
					particles[inputDimensionHalf+n] = particles[n]
			else:
				for n in range(inputDimension):
					particles[n] = random.uniform(convexHullMin[n], convexHullMax[n])

			masses = [[p*GeV for p in particles[0:inputDimensionHalf]], [p*GeV for p in particles[inputDimensionHalf:inputDimension]]]
			ul	   = expres.getUpperLimitFor(txname=topo, mass=masses)

			if type(ul) != type(None):
				new = [p for p in particles]
				new.append(ul.asNumber(fb))
				dataset.append(new)
				samplesLeft -= 1

	else:

		#create dataset for our classification network
		#first we generate a rough estimate of our convex hull with "massesHull"
		#then we draw points around the hull and finish populating our dataset with
		#random points drawn around the center of our hull

		massesSorted = [sorted(expresData,key=lambda l:l[n]) for n in range(len(expresData[0]))]
		massesHull = []

		for k in range(len(massesSorted)):

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
		samplesPerHullPoint = int(( sampleSize / numOfHullPoints ) * 0.75)
			
		for currentMassHull in massesHull:
			for point in currentMassHull:
				samplesPerHullPointLeft = samplesPerHullPoint
				while(samplesPerHullPointLeft > 0):
					for n in range(inputDimension):

						if ( isSymmetric and n == inputDimensionHalf - 1 ) or ( not isSymmetric and n == inputDimension - 1 ):
							std = 25. #45.
						else:
							std = 25. #abs(point[n] - point[n+1]) * 0.15 #0.25
						mean = point[n]

						particles[n] = abs(np.random.normal(mean, std, 1)[0])

						if isSymmetric and n == inputDimensionHalf - 1:
							for k in range(inputDimensionHalf):
								particles[inputDimensionHalf+k] = particles[k]
							break

					masses = [[p*GeV for p in particles[0:inputDimensionHalf]], [p*GeV for p in particles[inputDimensionHalf:inputDimension]]]
					ul	   = expres.getUpperLimitFor(txname=topo, mass=masses)

					new = [p for p in particles]
					if type(ul) != type(None): new.append(1.)
					else: new.append(0.)
				
					dataset.append(new)
					samplesLeft -= 1
					samplesPerHullPointLeft -= 1

	while(samplesLeft>0):

		if isSymmetric:
			for n in range(inputDimensionHalf):
				particles[n] = abs(np.random.normal(expresDataMean[n], expresDataStd[n], 1)[0])
			for n in range(inputDimensionHalf):
				particles[inputDimensionHalf+n] = particles[n]
		else:
			for n in range(inputDimension):
				particles[n] = abs(np.random.normal(expresDataMean[n], expresDataStd[n], 1)[0])

		masses = [[p*GeV for p in particles[0:inputDimensionHalf]], [p*GeV for p in particles[inputDimensionHalf:inputDimension]]]
		ul	   = expres.getUpperLimitFor(txname=topo, mass=masses)

		new = [p for p in particles]
		if type(ul) != type(None): new.append(1.)
		else: new.append(0.)
				
		dataset.append(new)
		samplesLeft -= 1
		

	#import matplotlib.pyplot as plt
	#plt.figure(99)
	#plt_dots = plt.scatter([m[0] for m in expresData],[m[1] for m in expresData], color = 'gray', alpha=0.5)
	#plt_dots = plt.scatter([m[0] for m in massesHull[0]],[m[1] for m in massesHull[0]], color = 'green')
	#plt_dots = plt.scatter([m[0] for m in massesHull[1]],[m[1] for m in massesHull[1]], color = 'blue')
	#plt.show()

	if shuffleData: shuffle(dataset)
	dataSet = Data(dataset, inputDimension, device)
	return dataSet

