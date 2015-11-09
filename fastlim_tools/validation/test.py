#!/usr/bin/env python

'''
Created on 09/11/2015

@author: lessa
'''


import multiprocessing
import sys,glob
sys.path.append('../runTools')
from gridFastlim import runFastlim,getSlhaFiles
import logging as logger
import shutil,os

slhadir = './SLHA/strong_gt_TeV_focus/'
fastlimdir = os.path.join(os.path.expanduser("~"),'smodels-utils/fastlim_tools/fastlim-1.0/')

#slhaFiles,slhaD = getSlhaFiles(slhadir)
slhaFiles = ['/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/strong_lt_TeV_focus/2aOxfvBBClZ6aBk.slha',
             '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/strong_lt_TeV_focus/1RH5gpAdX7C7Kx6.slha',
             '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/strong_lt_TeV_focus/4E8NWYJXzEfkEB6.slha',
             '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/strong_lt_TeV_focus/4evXuqFSx7WPowS.slha',
             '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/strong_lt_TeV_focus/1FmWNHHrf23pLRI.slha',
             '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/strong_lt_TeV_focus/2an6V3SXsVKUPkG.slha']
np = 4

slhaFiles = glob.glob(os.getcwd()+"/SLHA/strong_lt_TeV_focus/*.slha")
slhaFiles = slhaFiles[:50]

#Set up multiprocessing:
pool = multiprocessing.Pool(processes=np)

#Loop over SLHA files and compute results:    
results = []
for slhafile in slhaFiles:        
    outputfile = slhafile.replace(".slha",".sms")
    #Run Fastlim (submit threads):    
    results.append([outputfile,
                    pool.apply_async(runFastlim,args=(slhafile,outputfile,fastlimdir,
                                                      None,None))])
    
print 'Done submission'
for res in results:
    outputfile,run = res
    try:
        goodRun = run.get(30)
    except multiprocessing.TimeoutError:
        goodRun = False
        
    print outputfile,goodRun
        
sys.exit()
#Check results
data = []
for res in results:
    outputfile,goodRun = res
    if not goodRun:
        logger.error("Fastlim failed for file %s" %outputfile)
    else:
        data.append(outputfile)
#Remove temporary folder
if slhaD != slhadir: shutil.rmtree(slhaD)

