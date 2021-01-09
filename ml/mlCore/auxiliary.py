import os, torch
from torch import nn
import numpy as np
from smodels.tools.stringTools import concatenateLines
from smodels.tools.physicsUnits import GeV, fb

def MSErel(predicted, label, reduction = "mean", denomOffset = 0.): #1e-4

	loss = ((predicted-label)/(label+denomOffset))**2
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


def getModelError(model, dataset, netType, returnMean = True):

	"""
	Quick hack to gain model performance over specific dataset.
	Useful to have a uniform error check regardless of loss function used
	during training.

	"""

	predictions = model(dataset.inputs)
	labels = dataset.labels
	
	error = []

	if netType == "regression":

		for n, label in enumerate(labels):

			l = label.item()
			p = predictions[n].item()

			if l > 0:
				e = np.sqrt((( p - l ) / l)**2)
			else:
				e = p


			error.append(e)

	else:

		modelState = model.training
		model.training = True

		for n, label in  enumerate(labels):

			l = label.item()
			p = predictions[n].item()

			if l == p: e = 1.
			else: e = 0.

			error.append(e)

		model.training = modelState

	error = np.array(error)

	if returnMean:
		mean = np.mean(error)
		std = np.std(error)
		return mean, std
	
	return error



def loadGridPoints(expres, txnameData, dataselector, signalRegion, singleLines = True, stripUnits = True):

	if dataselector == "upperLimit":
		whichTag = "upperLimits"
	else:
		whichTag = "efficiencyMap"

	for tx in expres.getTxNames():
		if tx.txnameData == txnameData:
			tx = str(tx)
			break


	if dataselector == "upperLimit":
		filePath = expres.path + '/data/' + tx + '.txt'
	else:
		filePath = expres.path + '/' + signalRegion + '/' + tx + '.txt'

	with open(filePath) as txtFile:
		txdata = txtFile.read()
	content = concatenateLines(txdata.split("\n"))
	tags = [line.split(":", 1)[0].strip() for line in content]

	for i,tag in enumerate(tags):
		if not tag: continue
		line = content[i]
		value = line.split(':',1)[1].strip()
		if ";" in value: value = value.split(";")

		if tag == whichTag:
			data = value
			break

	# endcopy #

	origData, values = [], []

	data = data.split("],[[[")

	if data[0] != data[0].replace('*fb',''): unitValues = "*fb"
	elif data[0] != data[0].replace('*pb',''): unitValues = "*pb"
	else: unitValues = 1.

	if stripUnits: units = [1., 1.]
	else: units = [GeV, unitValues]
	
	for line in data:
		line = line.replace('[[[[','')
		line = line.replace('],[',',')
		line = line.replace(']]','')
		line = line.replace('*GeV','')
		line = line.replace('(', '')
		line = line.replace(')', '')
		
		#if line != line.replace('*fb',''): UNITS = "*fb"
		#elif line != line.replace('*pb',''): UNITS = "*pb"
		#else: UNITS = None
			
		line = line.replace('*fb','')
		line = line.replace('*pb','')

		point = line.split(",")
		masses = [float(p)*units[0] for p in point[:-1]]
		dHalf = int(0.5*len(masses))

		if not singleLines:
			masses = [[m for m in masses[0:dHalf]],[m for m in masses[dHalf:]]]

		origData.append(masses)

		value = float(point[-1])*units[1]
		values.append(value)

	return origData, values, units



