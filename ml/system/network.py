
import torch
import torch.nn as nn
import numpy as np
import os
from pathlib import Path
from smodels.tools.smodelsLogging import logger

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


class DatabaseNetwork(nn.Module):

	def __init__(self, winner):
    	
		super(DatabaseNetwork, self).__init__()
		self["regression"] = winner["regression"]["model"]
		self["classification"] = winner["classification"]["model"]

	def __setitem__(self, netType, model):
		self.__dict__[netType] = model

	def __getitem__(self, netType):
		return self.__dict__[netType]

	def __repr__(self):
		return repr(self.__dict__)

	def __len__(self):
		return len(self.__dict__)

	def getValidationLoss(self, netType):
		return self[netType].getValidationLoss()

	def setSpeedFactor(self, factor):
		self._speedFactor = factor

	def getSpeedFactor(self):
		return self._speedFactor

	def forward(self, x):

		onHull = self["classification"](x) == 1.
		if onHull: return self["regression"](x)
		return 0.

	def save(self, expres, txNameData):

		dbPath = expres.path
		for i in range(len(dbPath)):
			if dbPath[i:i+8] == 'database':
				dbPath = dbPath[i:]
				break
		path = os.getcwd() + "/" + dbPath + "/models/" + str(txNameData) + ".pth"

		Path(path).mkdir(parents=True, exist_ok=True)

		torch.save(self, path)
		logger.info("model saved at '%s'" % path)


	def load(expres, txNameData):
	
		dbPath = expres.path
		for i in range(len(dbPath)):
			if dbPath[i:i+8] == 'database':
				dbPath = dbPath[i:]
				break
		path = os.getcwd() + "/" + dbPath + "/models/" + str(txNameData) + ".pth"

		try:
			model = torch.load(path)
			model.eval()
		except: model = None

		return model


class Net_cla(nn.Module):
 
	def __init__(self, netShape, activFunc, rescaleParameter, scaler):

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

		self._rescaleParameter = rescaleParameter
		self._scaler = scaler

	def setValidationLoss(self, meanError):
		self._validationLoss = meanError

	def getValidationLoss(self):
		return self._validationLoss

	def setScaler(self,scaler):
		self._scaler = scaler

	@property
	def scaler(self):
		return self._scaler

	def forward(self, x):#input_):

		#x = ( x - self._rescaleParameter["mean"] ) / self._rescaleParameter["std"]
		x = self.seq(x)
		
		if not self.training and self._delimiter != 0.:
			for n in range(len(x)):
				if self._delimiter < x[n]: x[n] = 1.
				else: x[n] = 0.
		
		return x


class Net_reg(nn.Module):

	def __init__(self, netShape, activFunc, rescaleParameter, scaler):
    	
		super(Net_reg, self).__init__()
		self.seq = nn.Sequential()

		lastLayer = len(netShape) - 1

		for i in range(len(netShape)):

			nin, nout = netShape[i][0], netShape[i][1]

			self.seq.add_module('lin{}'.format(i), nn.Linear(nin,nout))

			if activFunc == "rel" and i != lastLayer:
				self.seq.add_module('rel{}'.format(i), nn.ReLU())
                    
			if activFunc == "prel" and i != lastLayer:
				self.seq.add_module('prel{}'.format(i), nn.PReLU())

			if activFunc == "sel" and i != lastLayer:
				self.seq.add_module('sel{}'.format(i), nn.SELU())

			if activFunc == "lrel" and i != lastLayer:
				self.seq.add_module('lrel{}'.format(i), nn.LeakyReLU()) 

    	
		self._rescaleParameter = rescaleParameter
		self._scaler = scaler

		for m in self.modules():
			if isinstance(m, nn.Linear):
				nn.init.xavier_normal_(m.weight)

				#nn.init.xavier_uniform(m.weight)
				#nn.init.normal(m.weight, mean=0, std=0.01)
				#nn.init.constant(m.bias, 0)

	def setValidationLoss(self, meanError):
		self._validationLoss = meanError

	def getValidationLoss(self):
		return self._validationLoss

	def setScaler(self,scaler):
		self._scaler = scaler

	@property
	def scaler(self):
		return self._scaler

	def forward(self, x):

		x = ( x - self._rescaleParameter["mean"] ) / self._rescaleParameter["std"]
		x = self.seq(x)

		return x
	


def createNet(hyper, rescaleParameter, scaler, full_dim, nettype):

	shape = hyper["shape"]
	nodes = hyper["nodes"]
	layer = hyper["layer"]
	activ = hyper["activationFunction"]

	netshape, nodesTotal = getNodesPerLayer(shape, nodes, layer, full_dim)

	if nettype == 'regression':
		model = Net_reg(netshape, activ, rescaleParameter, scaler)
	elif nettype == 'classification':
		model = Net_cla(netshape, activ, rescaleParameter, scaler)
	
	return model

