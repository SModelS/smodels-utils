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



old = {"data-cut10":"8j80 flavor 0 b-jets", "data-cut11":"8j80 flavor 1 b-jets", "data-cut12":"8j80 flavor >=2 b-jets", "data-cut13":"8j50 MJ 340", "data-cut14":"8j50 MJ 420", "data-cut8":"7j80 flavor 1 b-jets", "data-cut9":"7j80 flavor >=2 b-jets", "data-cut2":"8j50 flavor >=2 b-jets", "data-cut3":"9j50 flavor 0 b-jets", "data-cut0":"8j50 flavor 0 b-jets", "data-cut1":"8j50 flavor 1 b-jets", "data-cut6":"10j50 flavor", "data-cut7":"7j80 flavor 0 b-jets", "data-cut4":"9j50 flavor 1 b-jets", "data-cut5":"9j50 flavor >=2 b-jets"}

new = {'data-cut0':'8j50 flavor 0 b-jets', 'data-cut1':'8j50 flavor 1 b-jets', 'data-cut2':'8j50 flavor >=2 b-jets', 'data-cut3':'9j50 flavor 0 b-jets', 'data-cut4':'9j50 flavor 1 b-jets', 'data-cut5':'9j50 flavor >=2 b-jets', 'data-cut6':'10j50 flavor', 'data-cut7':'7j80 flavor 0 b-jets', 'data-cut8':'7j80 flavor 1 b-jets', 'data-cut9':'7j80 flavor >=2 b-jets', 'data-cut10':'8j80 flavor 0 b-jets', 'data-cut11':'8j80 flavor 1 b-jets', 'data-cut12':'8j80 flavor >=2 b-jets', 'data-cut13':'8j50 MJ 340', 'data-cut14':'8j50 MJ 420', 'data-cut15':'9j50 MJ 340', 'data-cut16':'9j50 MJ 420', 'data-cut17':'10j50 MJ 340', 'data-cut18':'10j50 MJ 420'}


for k,v in old.items():
    if not k in new:
        print 'missing',k
        continue
    if new[k] != v:
        print k,"differs:",v,new[k]
        
print len(new),len(old)

sys.exit()

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
