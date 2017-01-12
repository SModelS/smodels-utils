#!/usr/bin/env python
"""
.. module::	functionspackage
   :synopsis:   Consists of several functions that are mainly used by plotfunction and ratiofunction
   :submodules: binning, HistoDataProducer, setpalette, definesignalregion, TH2F_Parameters
""" 
###################################################################################################
def get_binning(listofvalues):
	"""
        Computes and returns the binning of an axes as a float number
	"""	
	binslist = []
	listofvalues.sort()

	for value in listofvalues:
	    if value > listofvalues[0]:
	       binning = value - listofvalues[0]
	       listofvalues[0] = value
	       binslist.append(binning)

	binningofaxis = min(binslist)
	return binningofaxis
	#TODO
	#if not all(i == binslist[0] for i in binslist):
	   #print '\n', '***WARNING***', '\n', 'The binning of the axis is not constant', '\n'



###################################################################################################

def HistoDataProducer(File,num='', factor=1):   #indexDat is the name of the region == name of the png file produced == title of the histogram
	"""
	Return X,Y,Z from a three colomns file, separated by the character defined in line @@@@
	"""
	fileF = open(File, "r")
	finalList = []
	for line in fileF:
		if line[0] != '#': # escludo le righe che iniziano con #
			lineElements = line.split(' ') # TODO define splitting @@@@
			convertedLineElements = []

			for element in lineElements:
				if element and element != '\n':  
					conversion = float(element) # strings->float conversion
					convertedLineElements.append(conversion)
			finalList.append(convertedLineElements) # make a list for each line that I read
	fileF.close()

	#finalList.pop(len(finalList) - 1) # remove the last empty lines

	X = []
	Y = []
	Z = []
	#Q = []
	for line in finalList:
   		X.append(line[0])
	for line in finalList:
   		Y.append(line[1])
	if num == 3:
    		for line in finalList:
        		Z.append((float(line[2])*factor))
	#if num == 4:
  		#  for line in finalList:
   			#     Z.append(line[2])
    				#    Q.append(line[3]*100)

	return X,Y,Z#,Q

###################################################################################################

from array import array
from ROOT import gStyle, TColor

def setpalette(name='palette', ncontours=999):
	"""
        Set a color palette from a given RGB list: stops, red, green and blue should all be lists of the same length
	"""

	if name == "gray" or name == "grayscale":
                # produce gray, white and black scale
		stops = [0.00, 0.34, 0.61, 0.84, 1.00]
		red   = [1.00, 0.84, 0.61, 0.34, 0.00]
		green = [1.00, 0.84, 0.61, 0.34, 0.00]
		blue  = [1.00, 0.84, 0.61, 0.34, 0.00]

	if name == "temp":
                #
		stops = [0.00, 0.34, 0.61, 0.84, 1.00]
		red   = [0.00, 0.00, 0.87, 1.00, 0.51]
		green = [0.00, 0.00, 0.00, 0.00, 0.00]
		blue  = [0.51, 1.00, 0.12, 0.00, 0.00]
    
	if name == "bwr":
                # produce three colors scale: blue, white and red. Used mainly by ratioplotter
		stops = [0.00, 0.50, 1.00]
		red   = [0.00, 1.00, 1.00]
		green = [0.00, 1.00, 0.00]
		blue  = [1.00, 1.00, 0.00]

	if name == "mypalette":
		# default palette, looks smooth
		stops = [0.00, 0.34, 0.61, 0.84, 1.00]
		red   = [0.00, 0.00, 0.87, 1.00, 0.51]
		green = [0.00, 0.81, 1.00, 0.20, 0.00]
		blue  = [0.51, 1.00, 0.12, 0.00, 0.00]

	s = array('d', stops)
	r = array('d', red)
	g = array('d', green)
	b = array('d', blue)

	npoints = len(s)
	TColor.CreateGradientColorTable(npoints, s, r, g, b, ncontours)
	gStyle.SetNumberContours(ncontours)

###################################################################################################

def definesignalregion(NameOfFile):
	"""
        Recall the signal region of a map by splitting the name of it
	:param NameOfMap
	:type  string	
	"""
	SPLIT = NameOfFile.split('/')
	Signal_Region = SPLIT[len(SPLIT)-1].split('.dat')[0]
	return Signal_Region

###################################################################################################

import os
def get_th2f_par(maxofxaxis, minofxaxis, maxofyaxis, minofyaxis, xbinning, ybinning):
        """
        Produce the parameters needed to create ROOT-2D-histogram using ROOT.TH2F().
        The condition (max_of_axis - min_of_axis)% binnig_of_axis = 0, which means an axis have an integer bins-number, must be fulfilled. If not the maximum and
        the number of the bins of this axis are changed in such a way, that fulfills the condition.
        required modules: HistoDataProducer, binning
        """
	nbinsx			= (maxofxaxis - minofxaxis)/xbinning   
	nbinsy       		= (maxofyaxis - minofyaxis)/ybinning
        if (maxofxaxis - minofxaxis)%xbinning == 0 and (maxofyaxis - minofyaxis)%ybinning == 0:
         #   	print "No NBins Problems"
                return int(nbinsx), int(minofxaxis), int(maxofxaxis), int(nbinsy), int(minofyaxis), int(maxofyaxis)+200 # 200 units free space for the text on the plot 

        if (maxofxaxis - minofxaxis)%xbinning != 0 and (maxofyaxis - minofyaxis)%ybinning == 0:
                print "Problem in NBinsX", nbinsx
                newmaxofxaxis	= minofxaxis + xbinning*(int(nbinsx)+1)
                newnbinsx	= (newmaxofxaxis - minofxaxis)/xbinning   
                #print "newmaxofxaxis", newmaxofxaxis, "newnbinsx", newnbinsx
                return int(newnbinsx), int(minofxaxis), int(newmaxofxaxis), int(nbinsy), int(minofyaxis), int(maxofyaxis)+200



        elif (maxofxaxis - minofxaxis)%xbinning == 0 and (maxofyaxis - minofyaxis)%ybinning != 0:
                print "Problem in NBinsY", nbinsy
                newmaxofyaxis	= minofyaxis + ybinning*(int(nbinsy)+1)
                newnbinsy	= (newmaxofyaxis - minofyaxis)/ybinning   
                #print "newmaxofyaxis", newmaxofyaxis, "newnbinsy", newnbinsy
                return int(nbinsx), int(minofxaxis), int(maxofxaxis), int(newnbinsy), int(minofyaxis), int(newmaxofyaxis)+200


        elif (maxofxaxis - minofxaxis)%xbinning != 0 and (maxofyaxis - minofyaxis)%ybinning != 0:
                print "Problem in NBinsX", nbinsx, "and NBinsY", nbinsy
                newmaxofxaxis	= minofxaxis + xbinning*(int(nbinsx)+1)
                newnbinsx	= (newmaxofxaxis - minofxaxis)/xbinning
                newmaxofyaxis	= minofyaxis + ybinning*(int(nbinsy)+1)
                newnbinsy	= (newmaxofyaxis - minofyaxis)/ybinning 
                return int(newnbinsx), int(minofxaxis), int(newmaxofxaxis), int(newnbinsy), int(minofyaxis), int(newmaxofyaxis)+200
##################################################################################################
def Find_Eff(database, Mass_Point=[], Analysis=[], txName=[]):
    Res = database.getExpResults(analysisIDs=Analysis, txnames=txName, dataTypes = ['all'], useSuperseded=False, useNonValidated=False)
    Res_Eff = Res[0]
    Tx = Res_Eff.getTxnameWith({'txName':txName[0]})
    Efficiency = Tx.getEfficiencyFor(Mass_Point[0])
    return Efficiency
'''
def Find_Eff(ExpRes, Mass_Point=[], txName=[]):
    Tx = ExpRes.getTxnameWith({'txName':txName[0]})
    Eff = Tx.getEfficiencyFor(Mass_Point[0])
    return Tx, Eff
'''
###################################################################################################
'''
import os
def TH2F_Parameters(FilePath):
	"""
        Produce the parameters needed to create ROOT-2D-histogram using ROOT.TH2F().
        The condition (max_of_axis - min_of_axis)% binnig_of_axis = 0, which means an axis have an integer bins-number, must be fulfilled. If not the maximum and
        the number of the bins of this axis are changed in such a way, that fulfills the condition.
	required modules: HistoDataProducer, binning
	"""

	listx, listy, listz     = HistoDataProducer(FilePath, num=3)#one can add a factor='' if the efficiency is given in precent
	xbinning	 	= binning(listx)
	ybinning 		= binning(listy)
	maxofxaxis		= max(listx)
	minofxaxis  		= min(listx)
	minofyaxis		= min(listy)
	maxofyaxis      	= max(listy)+200 # 200 units free space for the text on the plot 
	nbinsx			= (maxofxaxis - minofxaxis)/xbinning   
	nbinsy       		= (maxofyaxis - minofyaxis)/ybinning

	if (maxofxaxis - minofxaxis)%xbinning == 0 and (maxofyaxis - minofyaxis)%ybinning == 0:
	 #   	print "No NBins Problems"
            	return xbinning, ybinning, int(nbinsx), int(minofxaxis), int(maxofxaxis), int(nbinsy), int(minofyaxis), int(maxofyaxis)

    	if (maxofxaxis - minofxaxis)%xbinning != 0 and (maxofyaxis - minofyaxis)%ybinning == 0:
        	print "Problem in NBinsX", nbinsx
        	newmaxofxaxis	= minofxaxis + xbinning*(int(nbinsx)+1)
        	newnbinsx	= (newmaxofxaxis - minofxaxis)/xbinning   
        	#print "newmaxofxaxis", newmaxofxaxis, "newnbinsx", newnbinsx
            	return xbinning, ybinning, int(newnbinsx), int(minofxaxis), int(newmaxofxaxis), int(nbinsy), int(minofyaxis), int(maxofyaxis)



    	elif (maxofxaxis - minofxaxis)%xbinning == 0 and (maxofyaxis - minofyaxis)%ybinning != 0:
        	print "Problem in NBinsY", nbinsy
        	newmaxofyaxis	= minofyaxis + ybinning*(int(nbinsy)+1)
        	newnbinsy	= (newmaxofyaxis - minofyaxis)/ybinning   
        	#print "newmaxofyaxis", newmaxofyaxis, "newnbinsy", newnbinsy
        	return xbinning, ybinning, int(nbinsx), int(minofxaxis), int(maxofxaxis), int(newnbinsy), int(minofyaxis), int(newmaxofyaxis)


    	elif (maxofxaxis - minofxaxis)%xbinning != 0 and (maxofyaxis - minofyaxis)%ybinning != 0:
        	print "Problem in NBinsX", nbinsx, "and NBinsY", nbinsy
        	newmaxofxaxis	= minofxaxis + xbinning*(int(nbinsx)+1)
        	newnbinsx	= (newmaxofxaxis - minofxaxis)/xbinning
        	newmaxofyaxis	= minofyaxis + ybinning*(int(nbinsy)+1)
        	newnbinsy	= (newmaxofyaxis - minofyaxis)/ybinning 
        	return xbinning, ybinning, int(newnbinsx), int(minofxaxis), int(newmaxofxaxis), int(newnbinsy), int(minofyaxis), int(newmaxofyaxis)

###################################################################################################
'''

