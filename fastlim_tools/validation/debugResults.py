#!/usr/bin/env python

"""
.. module:: debugResults
   :synopsis: Facility to get results for a specific file and compare info

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""


import sys,os,subprocess,shutil
sys.path.append('../runTools')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
sys.path.append(os.path.join(home,'smodels-database'))
from fastlimOutput import fastlimParser
from auxiliaryObjs import compareFiles,getSlhaFiles, formatOutput
from smodels.tools.physicsUnits import GeV, fb, TeV
from gridFastlim import runFastlim
from gridSmodels import runSmodelS
from smodels.theory import slhaDecomposer, crossSection, theoryPrediction
from smodels.tools import databaseBrowser
from signalregions import SRs
from datetime import datetime


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
                    doCompress=True,doInvisible=True, minmassgap=mingap)
    
#     for top in smstoplist:
#         if top.vertnumb == [3,3] and top.vertparts == [[1,1,0],[1,1,0]]:
#             for el in top.elementList: print el,el.getMasses(),el.weight
#     sys.exit()
#     totdecomp = 0.*fb
#     for el in smstoplist.getElements():
#         if not el.motherElements: totdecomp += el.weight[0].value
#     
#     total = 0.*fb
#     xSectionList = crossSection.getXsecFromSLHAFile(slhafile)
#     xSectionList.removeLowerOrder()
#     for xsec in xSectionList:
#         total += xsec.value
#     print 'total =',total,'totaldecomp = ',totdecomp,'coverage = ',totdecomp/total,'diff = ',total-totdecomp


    predictions = theoryPrediction.TheoryPredictionList()     
    for expRes in database.expResultList:
        preds =  theoryPrediction.theoryPredictionsFor(expRes, smstoplist,useBestDataset=False)        
        if preds:    
            predictions += preds

    print 'starting format output',str(datetime.now())
    output = formatOutput(slhafile,predictions)
    print 'done format output',str(datetime.now())
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
    
    infile = slhafile
    outfile = infile.replace('.slha','.out')
    proc = subprocess.Popen([os.path.join(fastlimdir,'fastlimMod.py'),infile,outfile],
                            cwd = fastlimdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()

    
    #Convert results to SModelS format (TheoryPredictionList)      
    predictions = fastlimParser(outfile,useBestDataset=False,
                                expResID=expResID,datasetID=datasetID,txname=txname)
    
    shutil.move(outfile,'./fastlim.debug')
    return predictions
              

if __name__ == '__main__':
#     expID =  'ATLAS-CONF-2013-024'
#     datasetId = 'data-cut0'
    expID = None
    datasetId = None
    slhafile = '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/strong_lt_focus/ZuemzNlYC35Qfg.slha'
    slhafile = '/home/lessa/smodels-utils/fastlim_tools/validation/SLHA/bla/zZ7Ljle3Yih14a.slha'    
    
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
        lum = smod.expResult.getValuesFor('lumi')[0]
        if not fast:
            missPredsFast.append(smod)
            print '\nSMODELS'
            print smod.expResult.getValuesFor('id')
            print lum
            print smod.dataset.getValuesFor('dataId'),\
            '(',SRs[smod.expResult.getValuesFor('id')[0]][smod.dataset.getValuesFor('dataId')[0]],')'
            print smod.dataset.getValuesFor('observedN'),smod.dataset.getValuesFor('expectedBG'),\
            smod.dataset.getValuesFor('upperLimit')[0]*lum,smod.dataset.getValuesFor('expectedUpperLimit')[0]*lum            
            print smod.value[0].value*lum
            smodTxnames = {}
            for el in smod.cluster.elements:
                for txname in smod.txnames:
                    if txname.hasElementAs(el):
                        if not txname.txName in smodTxnames:
                            smodTxnames[txname.txName] = [el.weight[0].value*lum,[el.eff]]
                        else:
                            smodTxnames[txname.txName][0] += el.weight[0].value*lum
                            smodTxnames[txname.txName][1].append(el.eff)
                        break
            print smodTxnames            
            continue
        
        print '\nSMODELS/FASTLIM'
        print smod.expResult.getValuesFor('id'),'/',fast.expResult.getValuesFor('id')
        print lum
        print smod.dataset.getValuesFor('dataId'),'/',fast.dataset.getValuesFor('dataId'),\
        '(',SRs[fast.expResult.getValuesFor('id')[0]][fast.dataset.getValuesFor('dataId')[0]],')'
        print smod.dataset.getValuesFor('observedN'),smod.dataset.getValuesFor('expectedBG'),\
        smod.dataset.getValuesFor('upperLimit')[0]*lum,smod.dataset.getValuesFor('expectedUpperLimit')[0]*lum,\
        '/',fast.dataset.getValuesFor('observedN'),fast.dataset.getValuesFor('expectedBG'),\
        fast.dataset.getValuesFor('upperLimit')[0]*lum,fast.dataset.getValuesFor('expectedUpperLimit')[0]*lum
        print smod.value[0].value*lum,'/',fast.value[0].value*lum
        smodTxnames = {}
        for el in smod.cluster.elements:
            for txname in smod.txnames:
                if txname.hasElementAs(el):
                    if not txname.txName in smodTxnames:
                        smodTxnames[txname.txName] = [el.weight[0].value*lum,[el.eff]]
                    else:
                        smodTxnames[txname.txName][0] += el.weight[0].value*lum
                        smodTxnames[txname.txName][1].append(el.eff)
                    break
        fastTxnames = {}       
        for iel,el in enumerate(fast.cluster.elements):
            fastTxnames[fast.txnames[iel].txName] = [el.weight[0].value*lum]
#         smodTxnames = sorted(smodTxnames)
#         fastTxnames = sorted(fastTxnames)
        print smodTxnames,'/'
        print fastTxnames
#         print [el.weight[0].value for el in smod.cluster.elements],'/'
#         print [el.weight[0].value for el in fast.cluster.elements]
        
        
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
            lum = fast.expResult.getValuesFor('lumi')[0]
            print '\nFASTLIM'
            print fast.expResult.getValuesFor('id')
            print fast.dataset.getValuesFor('dataId'),\
            '(',SRs[fast.expResult.getValuesFor('id')[0]][fast.dataset.getValuesFor('dataId')[0]],')'
            print fast.dataset.getValuesFor('observedN'),fast.dataset.getValuesFor('expectedBG'),\
            fast.dataset.getValuesFor('upperLimit')[0]*lum,fast.dataset.getValuesFor('expectedUpperLimit')[0]*lum
            print fast.value[0].value*lum
            fastTxnames = []        
            for iel,el in enumerate(fast.cluster.elements):
                fastTxnames.append([fast.txnames[iel].txName,el.weight[0].value*lum])
            fastTxnames = sorted(fastTxnames, key=lambda tx: tx[1], reverse=True)
            print fastTxnames
            continue
    
    print '\n\n Results missing in Fastlim:'
    print [pred.expResult.getValuesFor('id')[0] for pred in missPredsFast]
    print ' Results missing in SModelS:'
    print [pred.expResult.getValuesFor('id')[0] for pred in missPredsSmod]
    
        
            
    sys.exit()
   

