#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, unum, sys
import numpy as np
import matplotlib.pyplot as plt
from time import time
from smodels.experiment.databaseObj import Database
from smodels.experiment.txnameObj import TxNameData
from smodels.tools.physicsUnits import GeV, fb
from smodels.tools.stringTools import concatenateLines



def getExpresDataFormatted(data):

	MASSES, UL = [], []
	N = 0
	
	data = data.split("],[[[")
	for line in data:
		line = line.replace('[[[[','')
		line = line.replace('],[',',')
		line = line.replace(']]','')
		line = line.replace('*GeV','')
		
		if line != line.replace('*fb',''):
			UNITS = "*fb"
		elif line != line.replace('*pb',''):
			UNITS = "*pb"

		line = line.replace('*fb','')
		line = line.replace('*pb','')
		

		point = line.split(",")
		masses = [float(p)*GeV for p in point[:-1]]
		dHalf = int(0.5*len(masses))
		masses = [[m for m in masses[0:dHalf]],[m for m in masses[dHalf:]]]

		MASSES.append(masses)

		ul = float(point[-1]) #*fb
		UL.append(ul)

	return MASSES, UL, UNITS


def removeMassPoint(data, index, units):

	data = data.split(units)
	dataNew = ""

	for n in range(len(data)):
		if n != len(data) - 1:
			
			data[n] += "*fb"
			
		if n != index:
			dataNew += data[n]
	
	if index == 0:
		dataNew = "[" + dataNew[2:]

	return dataNew


def getInterpolationError(expres, topology, showPlot = False):

	txtFile = open(expres.path + '/data/' + topology + '.txt','r')
	txdata = txtFile.read()
	txtFile.close()
	content = concatenateLines(txdata.split("\n"))
	
	tags = [line.split(':', 1)[0].strip() for line in content]
	data = None
	dataType = None
	for i,tag in enumerate(tags):
		if not tag: continue
		line = content[i]
		value = line.split(':',1)[1].strip()
		if ';' in value: value = value.split(';')
		if tag == 'upperLimits':
			data = value
			dataType = 'upperLimit'
			masses, uls, units = getExpresDataFormatted(data)
			break
		#if tag == "axes":
		#	print("AXES:", value)
			
		#  --- maybe add efficiencyMap support? ---
		#elif tag == 'efficiencyMap':
		#	data = value
		#	dataType = 'efficiencyMap'
			

	t0 = time()
	error = []

	
	massesNum = len(masses)
	
	"""
	txes = expres.getTxNames()
	for tx in txes:
		if str(tx) == topology:
			txName = tx
			break

	delauNum = len(txName.txnameData.tri.points)
	print("num of delauney points: %s" % delauNum)
	print("num of mass points: %s" % massesNum)
	"""

	for currentSkip in range(massesNum):

		print("\rprogress: %s/%s" %(currentSkip+1, massesNum), end = "", flush = True)
		dataNew = removeMassPoint(data, currentSkip, units)


		txNameNew = TxNameData(dataNew, dataType, "tempID")

		newUl = txNameNew.getValueFor(masses[currentSkip])
		if type(newUl) != type(None):
			relError = round(abs(uls[currentSkip]-newUl.asNumber(fb)) / uls[currentSkip], 3)
		else:
			relError = -1

		error.append(relError)

	print(" -> done (%ss)" %(round(time()-t0, 3)))

	X = [m[0][0].asNumber(GeV) for m in masses]
	Y = [m[0][1].asNumber(GeV) for m in masses]
	E = error

	# get rid of extrapolations at edge points of convex hull
	# (we flagged them with an error of -1)
	n = 0
	edges = 0
	while n < len(E):
		if E[n] == -1:
			E.pop(n)
			X.pop(n)
			Y.pop(n)
			edges += 1
		else: n += 1

	relErrorMean = np.mean(E) #round(np.mean(E), 3)
	relErrorStd = np.std(E) #round(np.std(E), 3)

	#for e in E:
	#	print(round(e, 3))

	print("# of edges: %s" %edges)
	print("total rel error: %s +- %s" % (relErrorMean, relErrorStd))


	if showPlot:
		plt.figure(22)
		plt.title('relative error interpolation\nid: {}, tx: {} ({})'.format(analysisID, topology, dataType), fontsize=14)
		plt.xlabel('mass mother [GeV]')
		plt.ylabel('mass daughter [GeV]')
		plt.scatter(X,Y, c=E, cmap='rainbow', vmin=0, vmax=1)
		plt.colorbar()
		plt.tight_layout()

		fileName = analysisID + "_" + topology + "_interpolation_error.png" # .eps
		plt.savefig(os.getcwd() + "/" +  fileName)
		plt.show()

	heuristicData = {
		"edges": edges,
		"relErrorMean": relErrorMean,
		"relErrorStd": relErrorStd,
		"rawData": E
	}

	return heuristicData


if __name__=='__main__':

	topology = "TChiWZ" # "T6bbWW"
	analysisID = "ATLAS-SUSY-2016-24" #"CMS-SUS-19-006"

	smodelsPath = "../../../smodels"
	databasePath = "../../../smodels-database"
	sys.path.append(smodelsPath)
	sys.path.append(databasePath)
	from smodels.experiment.databaseObj import Database
	from smodels.experiment.txnameObj import TxNameData
	from smodels.tools.physicsUnits import GeV, fb
	#from smodels.tools.stringTools import concatenateLines	

	expres = Database(databasePath)
	expres = expres.getExpResults(analysisIDs = analysisID, useSuperseded = True, useNonValidated = True)[0]

	getInterpolationError(expres, topology, True)

	
