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
sys.path.append(os.path.join(home,'smodels-database'))
from fastlimOutput import compareFiles, fastlimParser
from smodels.tools.physicsUnits import GeV, fb, TeV
from gridFastlim import runFastlim
from gridSmodels import runSmodelS
from smodels.theory import slhaDecomposer, crossSection, theoryPrediction
from fastlimOutput import formatOutput
from smodels.tools import databaseBrowser
from gridFastlim import getSlhaFiles, prepareSLHA
from signalregions import SRs


fastlimdir = os.path.join(os.getcwd(),'../fastlim-1.0/')
databasePath = os.path.join(home,'smodels-database')

def debugSmodelS(slhafile,expResID,datasetId):
    """
    Runs SModelS for a specific slhafile. Allows the user to select a specific experimental
    result and dataset.
    Returns  the list of theory predictions.
    
    :param slhafile: input SLHA file
    :param expResID: ID of specific experimental result to be used (i.e. ATLAS-CONF-2013-053)
    :param datasetId: ID of specific dataset to be used (i.e. data-cut0)
    :return: TheoryPredictionList object containing SModelS results    
    """
    
    sigmacut = 0.001 * fb
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
                    doCompress=True,doInvisible=True, minmassgap=mingap)
    
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
        preds =  theoryPrediction.theoryPredictionsFor(expRes, smstoplist,useBestDataset=False)        
        if preds:    
            predictions += preds

    return predictions


def debugFastlim(slhafile,fastlimdir,expResID=None,datasetID=None,txname=None):
    """
    Runs Fastlim for a specific slhafile. Allows the user to select a specific experimental
    result and txname.
    Returns  the list of theory predictions.
    
    :param slhafile: input SLHA file
    :param fastlimdir: Fastlim folder containing fastlimMod.py
    :param expResID: ID of specific experimental result to be used (i.e. ATLAS-CONF-2013-053)
    :param datasetID: Used to select a specific dataset (i.e. data-cut0)
                   If None will return predictions for the best dataset.
    :param txname: Used to select the contribution of a single topology (i.e. T2tt)    
    :return: TheoryPredictionList object containing Fastlim results    
    """    
    
    infile = tempfile.mkstemp()     #Use temp file to store fastlim-ready SLHA file
    os.close(infile[0])
    infile = infile[1]
    outfile = infile+'.out'
    prepareSLHA(slhafile,infile)
    proc = subprocess.Popen([os.path.join(fastlimdir,'fastlimMod.py'),infile,outfile],
                            cwd = fastlimdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()

    
#     import shutil
#     shutil.copy(outfile,'./fastlim.out')
    #Convert results to SModelS format (TheoryPredictionList)      
    predictions = fastlimParser(outfile,useBestDataset=False,
                                expResID=expResID,datasetID=datasetID,txname=txname)
    os.remove(infile)
    os.remove(outfile)
    return predictions
              

if __name__ == '__main__':
    expID =  'ATLAS-CONF-2013-049'
#     datasetId = 'data-cut3'
#     expID = None
    datasetId = None    
    slhafile = '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/test/1a0gBELT5sweUwa.slha'
    
    fastPreds = debugFastlim(slhafile, fastlimdir, expID, datasetId)
    fastPreds = sorted(fastPreds, key=lambda thpred: thpred.expResult.getValuesFor('id')[0])
    
    smodelsPreds = debugSmodelS(slhafile, expID, datasetId)
    smodelsPreds = sorted(smodelsPreds, key=lambda thpred: thpred.expResult.getValuesFor('id')[0])
    
    missPredsFast = []
    for smod in smodelsPreds:
        fast = None
        for j, fth in enumerate(fastPreds):            
            if fth.expResult.getValuesFor('id') == smod.expResult.getValuesFor('id'):
                if fth.dataset.dataInfo.dataId == smod.dataset.dataInfo.dataId:
                    fast = fastPreds[j]
                    break
        if not fast:
            missPredsFast.append(smod)
            continue
        lum = smod.expResult.getValuesFor('lumi')[0]
        print '\nSMODELS/FASTLIM'
        print smod.expResult.getValuesFor('id'),'/',fast.expResult.getValuesFor('id')
        print smod.dataset.getValuesFor('dataId'),'/',fast.dataset.getValuesFor('dataId'),\
        '(',SRs[fast.expResult.getValuesFor('id')[0]][fast.dataset.getValuesFor('dataId')[0]],')'
        print smod.dataset.getValuesFor('observedN'),smod.dataset.getValuesFor('expectedBG'),\
        smod.dataset.getValuesFor('upperLimit')[0]*lum,smod.dataset.getValuesFor('expectedUpperLimit')[0]*lum,\
        '/',fast.dataset.getValuesFor('observedN'),fast.dataset.getValuesFor('expectedBG'),\
        fast.dataset.getValuesFor('upperLimit')[0]*lum,fast.dataset.getValuesFor('expectedUpperLimit')[0]*lum
        print smod.value[0].value*lum,'/',fast.value[0].value*lum
        smodTxnames = []
        for el in smod.cluster.elements:
            for txname in smod.txnames:
                if txname.hasElementAs(el):
                    smodTxnames.append([txname.txName,el.weight[0].value*lum,el.eff])
                    break
        fastTxnames = []        
        for iel,el in enumerate(fast.cluster.elements):
            fastTxnames.append([fast.txnames[iel].txName,el.weight[0].value*lum])
        smodTxnames = sorted(smodTxnames, key=lambda tx: tx[1], reverse=True)
        fastTxnames = sorted(fastTxnames, key=lambda tx: tx[1], reverse=True)
        print smodTxnames,'/'
        print fastTxnames
#         print [el.weight[0].value for el in smod.cluster.elements],'/'
#         print [el.weight[0].value for el in fast.cluster.elements]
        
        print '\n',[el.eff for el in smod.cluster.elements]
        
    missPredsSmod = []
    for fast in fastPreds:
        smod = None
        for j, sth in enumerate(smodelsPreds):            
            if sth.expResult.getValuesFor('id') == fast.expResult.getValuesFor('id'):
                if sth.dataset.dataInfo.dataId == fast.dataset.dataInfo.dataId:
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
   

