
import os, torch
from torch import nn
import numpy as np

def MSErel(predicted, label, reduction = "mean", denomOffset = 1e-4): #1e-4

	loss = ((predicted-label)/(label+denomOffset))**2
	if reduction == "mean": loss = torch.sqrt(torch.mean(loss))
	return loss


def getModelError(model, dataset, netType):

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
	mean = np.mean(error)
	std = np.std(error)

	return mean, std
		

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


def getModel(expres, topo, netType):

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




def loadModel(expres, txName):
	
	# TEMPORARY replace databasePath
	dbPath = expres.path
	for i in range(len(dbPath)):
		if dbPath[i:i+8] == 'database':
			dbPath = dbPath[i:]
			break
	savePath = os.getcwd() + "/" + dbPath + "/models/"
	# ---

	fileName = txName + '.pth'

	try: 
		#model = Net_reg()
		#model.load_state_dict(torch.load(savePath + fileName))

		model = torch.load(savePath + fileName)
		model.eval()
	except:
		model = None

	return model


"""

def loadModelX(expres, txName, netType):

	#savePath = expres.path + "/models/"
	
	# TEMPORARY replace databasePath
	dbPath = expres.path
	for i in range(len(dbPath)):
		if dbPath[i:i+8] == 'database':
			dbPath = dbPath[i:]
			break
	savePath = os.getcwd() + "/" + dbPath + "/models/"
	# ---

	fileName = txName + '_' + netType + '.pth'

	try: 
		#model = Net_reg()
		#model.load_state_dict(torch.load(savePath + fileName))

		model = torch.load(savePath + fileName)
		model.eval()
	except:
		model = None

	return model



def MSErel(predicted, label, reduction = "mean"):

	#loss = torch.abs((input-label)/label)
	#if reduction == "mean": loss = torch.mean(loss)
	#if label != 0.:
	#	loss = ((input-label)/label)**2
	#else: loss = input**2

	loss = torch.abs(torch.log(predicted/label))
	#print(predicted)
	#print(label)
	#print("---")
	if reduction == "mean": loss = torch.mean(loss)
	return loss

"""
