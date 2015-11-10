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
import os

database = os.path.join(os.path.expanduser("~"),'smodels-database/')
fastlimdir = os.path.join(os.getcwd(),'../fastlim-1.0/')

slhafile =  '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/test/1a1KLBOapEbTeGW.slha'
outputfile = '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/test/1a1KLBOapEbTeGW.sms'
print runFastlim(slhafile,outputfile,fastlimdir,None,None)

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

