#!/usr/bin/env python

'''
Created on 09/11/2015

@author: lessa
'''


import multiprocessing
import sys,glob
sys.path.append('../runTools')
from gridSmodels import runSmodelS,getSlhaFiles
from gridFastlim import prepareSLHA,runFastlim
from fastlimOutput import fastlimParser
import os

tlist = fastlimParser('../fastlim-1.0/fastlim.out')
for t in tlist:
    print t.expResult.getValuesFor('id')
    print t.expResult.getValuesFor('dataId')
    print t.dataset.getValuesFor('dataId')
    print t.value
    print t.txnames
    print [el.weight[0].value for el in t.cluster.elements]
    sys.exit()


sys.exit()

database = os.path.join(os.path.expanduser("~"),'smodels-database/')
fastlimdir = os.path.join(os.getcwd(),'../fastlim-1.0/')

slhafile =  '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/test/1a6IaeMU1laZAQC.slha'
outputfile = '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/test/1a6IaeMU1laZAQC.sms'
print runSmodelS(slhafile,outputfile,database)

sys.exit()
#slhaFiles,slhaD = getSlhaFiles(slhadir)
np = 3
pool = multiprocessing.Pool(processes=np)
slhaFiles = glob.glob(os.getcwd()+"/SLHA/test/*.slha")
slhaFiles = slhaFiles[:1]

#Set up multiprocessing:
pool = multiprocessing.Pool(processes=np)

#Loop over SLHA files and compute results:    
results = []
for slhafile in slhaFiles:        
    outputfile = slhafile.replace(".slha",".sms")
    #Run Fastlim (submit threads):    
    results.append([outputfile,
                        pool.apply_async(runSmodelS,args=(slhafile,outputfile,database))])
    
print 'Done submission'
pool.close()
pool.join()
for res in results:
    outputfile,run = res
    try:
        goodRun = run.get(500)
    except multiprocessing.TimeoutError:
        goodRun = False
        
    print outputfile,goodRun
        
sys.exit()

