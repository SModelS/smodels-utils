import torch
import torch.nn as nn
import numpy as np
import os

def loadModel(expres, txName, netType):

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







def getNodesPerLayer(shape, nodes, layer, inputNum):

	net = []
	nodes_total = 0
	
	for lay in range(layer):

		n = [0, 0]
		n_count = 0

		if shape == "lin":

			n[0] = nodes
			n[1] = nodes
			n_count += nodes

		elif shape == "trap":

			k = 2 * nodes / layer
			m = layer*0.5
			
			for i in range(2):

				cl = float(lay + i)
			
				if cl > m:
					cl = m - (cl%m)
				
				n[i] = round(cl*k)

			n_count += n[i]

		elif shape == "ramp":
			
			k = nodes / layer
	
			for i in range(2):
	
				cl = float(lay + i - 1)
				n[i] = round(nodes - k * cl)
	
			if lay == 0:
				n[1] = nodes
			elif lay == 1:
				n[0] = nodes

			n_count += n[i]				

		if lay == 0:
			n[0] = inputNum
		if lay == layer - 1:
			n[1] = 1
			n_count = 0

		nodes_total += n_count
		net.append(n)

	return [net, nodes_total]


class Net_cla(nn.Module):
 
	def __init__(self, netShape, activFunc, rescaleParameter):

		super(Net_cla, self).__init__()
		self.seq = nn.Sequential()
		self._delimiter = 0.
		lastLayer = len(netShape) - 1

		for i in range(len(netShape)):

			nin, nout = netShape[i][0], netShape[i][1]

			self.seq.add_module('lin{}'.format(i), nn.Linear(nin,nout))

			if activFunc == "rel" and i != lastLayer:
				self.seq.add_module('rel{}'.format(i), nn.ReLU()) #nn.BatchNorm1d(nout))

			if activFunc == "prel" and i != lastLayer:
				self.seq.add_module('prel{}'.format(i), nn.PReLU())

			if activFunc == "sel" and i != lastLayer:
				self.seq.add_module('sel{}'.format(i), nn.SELU())

			if activFunc == "lrel" and i != lastLayer:
				self.seq.add_module('lrel{}'.format(i), nn.LeakyReLU())

			if i == lastLayer:
				self.seq.add_module('sgm{}'.format(i), nn.Sigmoid())
			#elif i == 0:
				#self.seq.add_module('drp{}'.format(i), nn.Dropout(0.2))			

		self.rescaleParameter = rescaleParameter

	def forward(self, x):#input_):

		x = ( x - self.rescaleParameter["mean"] ) / self.rescaleParameter["std"]
		x = self.seq(x)
		
		if not self.training and self._delimiter != 0.:
			for n in range(len(x)):
				if self._delimiter < x[n]: x[n] = 1.
				else: x[n] = 0.
		
		return x


class Net_reg(nn.Module):

	def __init__(self, netShape, activFunc, rescaleParameter):
    	
		super(Net_reg, self).__init__()
		self.seq = nn.Sequential()

		lastLayer = len(netShape) - 1

		for i in range(len(netShape)):

			nin, nout = netShape[i][0], netShape[i][1]

			self.seq.add_module('lin{}'.format(i), nn.Linear(nin,nout))

			if activFunc == "rel" and i != lastLayer:
				self.seq.add_module('rel{}'.format(i), nn.PReLU()) #nn.SELU() nn.BatchNorm1d(nout))
                    
			if activFunc == "tah" and i != lastLayer:
				self.seq.add_module('tah{}'.format(i), nn.Tanh())

			if activFunc == "sig" and i != lastLayer:
				self.seq.add_module('sig{}'.format(i), nn.Sigmoid())   
    	
		self.rescaleParameter = rescaleParameter

		for m in self.modules():
			if isinstance(m, nn.Linear):
				nn.init.xavier_normal_(m.weight)

				#nn.init.xavier_uniform(m.weight)
				#nn.init.normal(m.weight, mean=0, std=0.01)
				#nn.init.constant(m.bias, 0)
    

	def forward(self, x):

		#if self.rescaleParameter["method"] == "standardScore":
		#	mean = self.rescaleParameter["parameter"]["mean"]
		#	std = self.rescaleParameter["parameter"]["std"]
		#	x = ( x - mean ) / std

		x = ( x - self.rescaleParameter["mean"] ) / self.rescaleParameter["std"]
		x = self.seq(x)
		return x
	


def createNet(hyperParameter, fullDataset, netType):

	shape = hyperParameter["shape"]
	nodes = hyperParameter["nodes"]
	layer = hyperParameter["layer"]
	activationFunction = hyperParameter["activationFunction"]

	netshape, nodesTotal = getNodesPerLayer(shape, nodes, layer, fullDataset.inputDimension)

	if netType == 'regression':
		model = Net_reg(netshape, activationFunction, fullDataset.rescaleParameter)
	elif netType == 'classification':
		model = Net_cla(netshape, activationFunction, fullDataset.rescaleParameter)
	
	return model

