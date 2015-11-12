#!/usr/bin/env python

"""
.. module:: debugResults
   :synopsis: Facility to get results for a specific file and compare info

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""


import sys,os,tempfile,subprocess
sys.path.append('../runTools')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
from fastlimOutput import compareFiles, fastlimParser
from smodels.tools.physicsUnits import GeV, fb, TeV
from gridFastlim import runFastlim
from gridSmodels import runSmodelS
from smodels.theory import slhaDecomposer, crossSection, theoryPrediction
from fastlimOutput import formatOutput
from smodels.tools import databaseBrowser
from gridFastlim import getSlhaFiles, prepareSLHA


fastlimdir = os.path.join(os.getcwd(),'../fastlim-1.0/')
databasePath = os.path.join(home,'smodels-database')

def debugSmodelS(slhafile,expResID,datasetId):
    
    sigmacut = 0.01 * fb
    mingap = 10. * GeV
    
    #Load the browser:
    browser = databaseBrowser.Browser(databasePath)
    browser.selectExpResultsWith(contact = ['fastlim'])
    database = browser.database
    database.expResultList = browser._selectedExpResults
    if expResID:
        database.expResultList = database.getExpResults(analysisIDs=[expResID])
    
    if datasetId:        
        for exp in database.expResultList:
            for dataset in exp.datasets:
                if dataset.getValuesFor('dataId')[0] == datasetId:
                    exp.datasets = [dataset]
                    break

    smstoplist = slhaDecomposer.decompose(slhafile, sigmacut,\
                    doCompress=False,doInvisible=False, minmassgap=mingap)
    
    totdecomp = 0.*fb
    for el in smstoplist.getElements():
        if not el.motherElements: totdecomp += el.weight[0].value
    
    total = 0.*fb
    xSectionList = crossSection.getXsecFromSLHAFile(slhafile)
    xSectionList.removeLowerOrder()
    for xsec in xSectionList:
        total += xsec.value
#     print 'total =',total,'totaldecomp = ',totdecomp,'coverage = ',totdecomp/total,'diff = ',total-totdecomp

    predictions = theoryPrediction.TheoryPredictionList()    
    for expRes in database.expResultList:
        preds =  theoryPrediction.theoryPredictionsFor(expRes, smstoplist)        
        if preds:    
            predictions += preds

    return predictions


def debugFastlim(slhafile,fastlimdir,expResID=None,txname=None):
    
    infile = tempfile.mkstemp()     #Use temp file to store fastlim-ready SLHA file
    os.close(infile[0])
    infile = infile[1]
    outfile = infile+'.out'
    prepareSLHA(slhafile,infile)
    proc = subprocess.Popen([os.path.join(fastlimdir,'fastlimMod.py'),infile,outfile],
                            cwd = fastlimdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()

    #Convert results to SModelS format (TheoryPredictionList)      
    predictions = fastlimParser(outfile,useBestDataset=True,
                                expResID=expResID,txname=txname)
    os.remove(infile)
    os.remove(outfile)
    return predictions
              

if __name__ == '__main__':
    expID =  'ATLAS-CONF-2013-047'
    datasetId = 'data-cut4'
    expID = None
    datasetId = None
    slhafile = os.path.abspath('./SLHA/strong_lt_TeV_focus/1anKWViqpBkaJuC.slha')
    slhafile = '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/test/1a3NYRAbKS40cPY.slha'
    
    fastPreds = debugFastlim(slhafile, fastlimdir, expID)
    fastPreds = sorted(fastPreds, key=lambda thpred: thpred.expResult.getValuesFor('id')[0])
    
    smodelsPreds = debugSmodelS(slhafile, expID, datasetId)
    smodelsPreds = sorted(smodelsPreds, key=lambda thpred: thpred.expResult.getValuesFor('id')[0])
    
    
    missPredsFast = []
    for smod in smodelsPreds:
        fast = None
        for j, fth in enumerate(fastPreds):            
            if fth.expResult.getValuesFor('id') == smod.expResult.getValuesFor('id'):
                fast = fastPreds[j]
                break
        if not fast:
            missPredsFast.append(smod)
            continue
        print '\nSMODELS/FASTLIM'
        print smod.expResult.getValuesFor('id'),'/',fast.expResult.getValuesFor('id')
        print smod.dataset.getValuesFor('dataId'),'/',fast.dataset.getValuesFor('dataId')
        print smod.dataset.getValuesFor('observedN'),smod.dataset.getValuesFor('expectedBG'),'/',fast.dataset.getValuesFor('observedN'),fast.dataset.getValuesFor('expectedBG')
        print smod.value[0].value,'/',fast.value[0].value
        print [txname.txName for txname in smod.txnames],'/'
        print [txname.txName for txname in fast.txnames]
        print [el.weight[0].value for el in smod.cluster.elements],'/'
        print [el.weight[0].value for el in fast.cluster.elements]
        
    missPredsSmod = []
    for fast in fastPreds:
        smod = None
        for j, sth in enumerate(smodelsPreds):            
            if sth.expResult.getValuesFor('id') == fast.expResult.getValuesFor('id'):
                smod = smodelsPreds[j]
                break
        if not smod:
            missPredsSmod.append(fast)
            continue
    
    print '\n\n Results missing in Fastlim:'
    print [pred.expResult.getValuesFor('id')[0] for pred in missPredsFast]
    print ' Results missing in SModelS:'
    print [pred.expResult.getValuesFor('id')[0] for pred in missPredsSmod]
    
        
            
    sys.exit()
   

