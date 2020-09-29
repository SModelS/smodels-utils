#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from smodels.tools.stringTools import concatenateLines
from smodels.tools.physicsUnits import GeV, fb

"""
def formatOrigData(dataString):

	#dataString.replace("[[[[", "[[[")
	#dataString.replace("]]]]", "]]]")

	print(dataString)
	
	origData = 0
	
	return origData


def getContent(paramDatabase, whichTag):

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

	return data
"""

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

"""
def getAxesData(logger, paramDatabase):


	axes = getContent(paramDatabase, "axes")

	axesData = []

	axes = axes.replace("[[","")
	axes = axes.replace("]]","")
	axes = axes.replace(" ","")
	axes = axes.split("],[")

	if axes[0] == axes[1]:
		axes = [axes[0]]

	for axis in axes:

		axis = axis.replace("(","")
		axis = axis.replace(")","")

	
		axis = axis.split(",")

		#read x and y from raw axis for mass dependancies
		for n in range(len(axis)):

			noX = axis[n].replace("x", "")
			noY = axis[n].replace("y", "")

			if noX == "": x = n
			elif noY == "": y = n
			

		axisData = []

		for a in axis:

			noX = a.replace("x", "")
			noY = a.replace("y", "")

			if noX == noY and a != noX:
				try: 
					f = float(a)
					d = -1
				except: logger.warning("Failed to read mass axes dependancies. Dataset generation might be slower than usual.")

			elif a != noX and a != noY:
				print("X Y")
				# should be arithemtic mean, both x, y are present in axis
				f = 0
				c = False
				d = [x,y]

			elif a == noY and a != noX:
				#only x present:
				if noX == "":
					f = 0
					c = False
					d = None
				else:
					f = float(noX)
					c = False
					d = x
			elif a == noX and a != noY:
				if noY == "":
					f = 0
					c = False
					d = None
				else:
					f = float(noY)
					c = False
					d = y
			else:
				try:
					float(a)
					f = float(a)
					c = True
					d = None
				except ValueError:
					logger.warning("Failed to read mass axes dependancies. Dataset generation might be slower than usual.")

			axisData.append({"dependancy": d, "offset": f, "constant": c})

		axesData.append(axisData)

	return axesData


if __name__== '__main__':

	ax1 = "[[x, (y, w)], [x, (y, w)]]"
	ax2 = "[[x, y + 10., y], [x, y + 10., y]]"
	ax3 = "[[(x, 1e-22)], [(x, 1e-22)]]"
	ax4 = "[[(x, w)], [(x, w)]]"
	ax5 = "[[(x, y), 100.0], [(x, y), 100.0]]"

	mod = getAxesData(ax5)
	print(mod)

"""
