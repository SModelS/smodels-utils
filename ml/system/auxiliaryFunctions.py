import os, torch
from torch import nn
import numpy as np

def MSErel(predicted, label, reduction = "mean", denomOffset = 0.): #1e-4

	loss = ((predicted-label)/(label+denomOffset))**2
	if reduction == "mean": loss = torch.sqrt(torch.mean(loss))
	return loss


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

