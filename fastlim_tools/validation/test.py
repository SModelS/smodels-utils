#!/usr/bin/env python

'''
Created on 09/11/2015

@author: lessa
'''


import sys,os
sys.path.append('../runTools')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
from gridFastlim import runFastlim
from gridSmodels import runSmodelSFor
fastlimdir = os.path.join(os.getcwd(),'../fastlim-1.0/')
databasePath = os.path.join(home,'smodels-database')
home = os.path.expanduser("~")
databaseDir = os.path.join(home,'smodels-database')
from smodels.tools.physicsUnits import fb, GeV, TeV
from smodels.theory import slhaDecomposer, theoryPrediction
from fastlimOutput import formatOutput
from smodels.tools import databaseBrowser
from gridFastlim import getSlhaFiles, prepareSLHA



slhafile = '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/missing/ZtqRWMuYjLZrfk.slha'
outfile = '/home/lessa/smodels-utils/fastlim_tools/validation/ZZwJnsq8Z00T3w.sms'
fastdir = '/home/lessa/smodels-utils/fastlim_tools/fastlim-1.0'


sigmacut = 0.01 * fb
mingap = 10. * GeV

#Load the browser:
browser = databaseBrowser.Browser(databasePath)
browser.selectExpResultsWith(contact = ['fastlim'])
database = browser.database
database.expResultList = browser._selectedExpResults    

smstoplist = slhaDecomposer.decompose(slhafile, sigmacut,\
                doCompress=True,doInvisible=True, minmassgap=mingap)
sys.exit()
predictions = theoryPrediction.TheoryPredictionList()
for expRes in database.expResultList:
    preds =  theoryPrediction.theoryPredictionsFor(expRes, smstoplist, 
                                                   useBestDataset=False)
    if preds:
        predictions += preds

#Format output to a python dictionary
extraInfo={'tool': 'smodels','sigmacut' : sigmacut.asNumber(fb), 'mingap' : mingap.asNumber(GeV)}
output = formatOutput(slhafile,predictions,'sms',extraInfo)         
