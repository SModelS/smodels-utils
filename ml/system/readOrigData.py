#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from smodels.tools.stringTools import concatenateLines
from smodels.tools.physicsUnits import GeV, fb


def getOrigExpresData(paramDatabase, singleLines = True, stripUnits = True):

	if paramDatabase["dataSelector"] == "upperLimit":
		whichTag = "upperLimits"
	else:
		whichTag = "efficiencyMap"

	#data = getContent(paramDatabase, whichTag)

	# copied from above # 

	expres = paramDatabase["expres"]
	txName = paramDatabase["txName"]
	dataSelector = paramDatabase["dataSelector"]
	signalRegion = paramDatabase["signalRegion"]

	if dataSelector == "upperLimit":
		filePath = expres.path + '/data/' + txName + '.txt'
	else:
		filePath = expres.path + '/' + signalRegion + '/' + txName + '.txt'

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


