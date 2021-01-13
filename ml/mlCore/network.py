
import torch
import torch.nn as nn
import numpy as np
import os
from pathlib import Path
from smodels.tools.smodelsLogging import logger

from scipy.special import inv_boxcox
#from sklearn.preprocessing import MinMaxScaler

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

	def __init__(self, winner):#, scaler, lmbda):
    	
		super(DatabaseNetwork, self).__init__()
		self["regression"] = winner["regression"]["model"]
		self["classification"] = winner["classification"]["model"]
		#self.scaler = scaler
		#self.lmbda = lmbda

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

	def forward(self, x, rescaleTarget = True):

		#x = self.scaler.inverse_transform(inputs)
		
		if self["classification"] == None:
			onHull = True
		else:
			onHull = True #self["classification"](x) == 1.

		if onHull:
			target = self["regression"](x)

			#if rescaleTarget:
			#	from scipy.special import inv_boxcox
			#	target = inv_boxcox(target, self.lmbda)

			return target
		return 0.

	def save(self, expres, txNameData):

		dbPath = expres.path
		for i in range(len(dbPath)):
			if dbPath[i:i+8] == 'database':
				dbPath = dbPath[i:]
				break
		path = os.getcwd() + "/" + dbPath + "/models"
		Path(path).mkdir(parents=True, exist_ok=True)
		path += "/" + str(txNameData) + ".pth"

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
 
	def __init__(self, netShape, activFunc):

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

		#self._rescaleParameter = rescaleParameter

	def setValidationLoss(self, meanError):
		self._validationLoss = meanError

	def getValidationLoss(self):
		return self._validationLoss

	def setRescaleParameter(self, parameter):
		self._rescaleParameter = parameter

	#def setScaler(self,scaler):
	#	self._scaler = scaler

	#@property
	#def scaler(self):
	#	return self._scaler

	def forward(self, x):#input_):

		#x = ( x - self._rescaleParameter["mean"] ) / self._rescaleParameter["std"]
		x = self.seq(x)
		
		if not self.training and self._delimiter != 0.:
			for n in range(len(x)):
				if self._delimiter < x[n]: x[n] = 1.
				else: x[n] = 0.
		
		return x


class Net_reg(nn.Module):

	def __init__(self, netShape, activFunc):
    	
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

	def setRescaleParameter(self, parameter):
		self._rescaleParameter = parameter



	def forward(self, x):

		if not self.training and "_rescaleParameter" in self.__dict__:
			if "masses" in self._rescaleParameter:
				if self._rescaleParameter["masses"]["method"] == "minmaxScaler":
					print("RESCALING INPUTS")

					scaler = self._rescaleParameter["masses"]["scaler"]
					x = scaler.transform(x)
					x = torch.tensor(x, dtype=torch.float64)


		#print(x)
		#x = ( x - self._rescaleParameter["mean"] ) / self._rescaleParameter["std"]
		x = self.seq(x)

		if not self.training and "_rescaleParameter" in self.__dict__:
			if "targets" in self._rescaleParameter:

				method = self._rescaleParameter["targets"]["method"]

				if method == "boxcox":
					print("RESCALING TARGETS BOXCOX")

					lmbda = self._rescaleParameter["targets"]["lambda"]
					print("LMBDA:", lmbda)
					x = x.detach().numpy()
					x = [inv_boxcox(t, lmbda)[0] for t in x]

				elif method == "log":

					print("RESCALING TARGETS LOG")

					x = x.detach().numpy()
					x = [(10**t)[0] for t in x]

				else:

					print("NO RESCALING TARGETS")

					x = x.detach().numpy()
					x = [t[0] for t in x]

		#x = x.detach().numpy()
		#x = [t[0] for t in x]
		return x
	


def createNet(hyper, rescaleParameter, full_dim, nettype):

	shape = hyper["shape"]
	nodes = hyper["nodes"]
	layer = hyper["layer"]
	activ = hyper["activationFunction"]

	netshape, nodesTotal = getNodesPerLayer(shape, nodes, layer, full_dim)

	if nettype == 'regression':
		model = Net_reg(netshape, activ)
	elif nettype == 'classification':
		model = Net_cla(netshape, activ)
	
	return model

