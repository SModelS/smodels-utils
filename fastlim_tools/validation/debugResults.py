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
from fastlimParser import fastlimParser
from auxiliaryObjs import compareFiles,getSlhaFiles, formatOutput
from smodels.base.physicsUnits import GeV, fb, TeV
from gridFastlim import runFastlim
from gridSmodels import runSmodelS
from smodels.decomposition import decomposer
from smodels.base import crossSection
from smodels.matching import theoryPrediction
from smodels.tools import databaseBrowser
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
    
    sigmacut = 0.0000001 * fb
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
                if dataset.dataInfo.dataId == datasetId:
                    exp.datasets = [dataset]
                    break
                
    smstoplist = slhaDecomposer.decompose(slhafile, sigmacut,\
                    doCompress=True,doInvisible=False, minmassgap=mingap)
    
#     for top in smstoplist:
#         if top.vertnumb == [2,2] and top.vertparts == [[1,0],[1,0]]:            
#             for el in top.elementList:
#                 if '[[[t+]],[[t-]]]' != str(el): continue
#                 print el,el.getMasses(),el.weight[0].value
#                 for pid in el.getPIDs(): print pid
#                 print '\n'
#                 print el.motherElements
#     sys.exit()
#     totdecomp = 0.*fb
#     for el in smstoplist.getElements():
#         if not el.motherElements: totdecomp += el.weight[0].value
#     print totdecomp
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
    
    minval = 0.00005 #Cut-off to remove txnames which would not appear in fastlim
    expID =  'ATLAS-CONF-2013-047'
    datasetId = 'data-cut4'
    #     expID = None
#     datasetId = None
    slhafile = os.path.join(home,'smodels-utils/fastlim_tools/validation/SLHA/strong_gt_focus/3ttJOQbPLyTqreK.slha')

    smodelsPreds = debugSmodelS(slhafile, expID, datasetId)
    smodelsPreds = sorted(smodelsPreds, key=lambda thpred: thpred.expResult.globalInfo.id)
    
    
    fastPreds = debugFastlim(slhafile, fastlimdir, expID, datasetId)
    fastPreds = sorted(fastPreds, key=lambda thpred: thpred.expResult.globalInfo.id)
    

    
    missPredsFast = []
    for smod in smodelsPreds:
        fast = None
        for j, fth in enumerate(fastPreds):            
            if fth.expResult.globalInfo.id == smod.expResult.globalInfo.id:
                if fth.dataset.dataInfo.dataId == smod.dataset.dataInfo.dataId:
                    fast = fastPreds[j]
                    break
        lum = smod.expResult.globalInfo.lumi
        if not fast:
            missPredsFast.append(smod)
            print '\nSMODELS'
            print smod.expResult.globalInfo.id
            print lum
            print smod.dataset.dataInfo.dataId,\
            '(',SRs[smod.expResult.globalInfo.id][smod.dataset.dataInfo.dataId],')'
            print smod.dataset.dataInfo.observedN,smod.dataset.dataInfo.expectedBG,\
            smod.dataset.dataInfo.upperLimit*lum,smod.dataset.dataInfo.expectedUpperLimit*lum            
            print smod.value[0].value*lum
            smodTxnames = {}
            smodPIDs = {}
            for el in smod.cluster.elements:
                for txname in smod.txnames:
                    if txname.hasElementAs(el):
                        if not txname.txName in smodTxnames:
                            smodTxnames[txname.txName] = [el.weight[0].value*lum,[el.eff]]
                            smodPIDs[txname.txName] = el.getPIDs()
                        else:
                            smodTxnames[txname.txName][0] += el.weight[0].value*lum
                            smodTxnames[txname.txName][1].append(el.eff)
                            smodPIDs[txname.txName] += el.getPIDs()
                        break
            for tx in smodTxnames.keys()[:]:                
                if smodTxnames[tx][0] < minval:  #Remove topologies which would not appear in fastlim
                    smodTxnames.pop(tx)
            print smodTxnames
            print smodPIDs             
            continue
        
        print '\nSMODELS/FASTLIM'
        print smod.expResult.globalInfo.id,'/',fast.expResult.globalInfo.id
        print lum
        print smod.dataset.dataInfo.dataId,'/',fast.dataset.dataInfo.dataId,\
        '(',SRs[fast.expResult.globalInfo.id][fast.dataset.dataInfo.dataId],')'
        print smod.dataset.dataInfo.observedN,smod.dataset.dataInfo.expectedBG,\
        smod.dataset.dataInfo.upperLimit*lum,smod.dataset.dataInfo.expectedUpperLimit*lum,\
        '/',fast.dataset.dataInfo.observedN,fast.dataset.dataInfo.expectedBG,\
        fast.dataset.dataInfo.upperLimit*lum,fast.dataset.dataInfo.expectedUpperLimit*lum
        print round(smod.value[0].value*lum,4),'/',round(fast.value[0].value*lum,4)
        
        smodTxnames = {}
        smodPIDs = {}
        for el in smod.cluster.elements:
            for txname in smod.txnames:
                if txname.hasElementAs(el):
                    if not txname.txName in smodTxnames:
                        smodTxnames[txname.txName] = [el.weight[0].value*lum,[round(el.eff,5)]]
                        smodPIDs[txname.txName] = el.getPIDs()
                    else:
                        smodTxnames[txname.txName][0] += el.weight[0].value*lum
                        smodTxnames[txname.txName][1].append(round(el.eff,5))
                        smodPIDs[txname.txName] += el.getPIDs()
                    break
        for tx in smodTxnames.keys()[:]:
            smodTxnames[tx][0] = round(smodTxnames[tx][0],6)
            if smodTxnames[tx][0] < minval:  #Remove topologies which would not appear in fastlim
                smodTxnames.pop(tx)                
        fastTxnames = {}       
        for iel,el in enumerate(fast.cluster.elements):
            if not fast.txnames[iel].txName in fastTxnames:
                fastTxnames[fast.txnames[iel].txName] = [el.weight[0].value*lum]
            else:
                fastTxnames[fast.txnames[iel].txName][0] += el.weight[0].value*lum
        for tx in fastTxnames.keys()[:]:
            fastTxnames[tx][0] = round(fastTxnames[tx][0],6)
        print smodPIDs                            
        print smodTxnames,'/'
        print fastTxnames
        
        
    missPredsSmod = []
    for fast in fastPreds:
        smod = None
        for j, sth in enumerate(smodelsPreds):            
            if sth.expResult.globalInfo.id == fast.expResult.globalInfo.id:
                if sth.dataset.dataInfo.dataId == fast.dataset.dataInfo.dataId:
                    smod = smodelsPreds[j]
                    break
        if not smod:
            missPredsSmod.append(fast)
            lum = fast.expResult.globalInfo.lumi
            print '\nFASTLIM'
            print fast.expResult.globalInfo.id
            print fast.dataset.dataInfo.dataId,\
            '(',SRs[fast.expResult.globalInfo.id][fast.dataset.dataInfo.dataId],')'
            print fast.dataset.dataInfo.observedN,fast.dataset.dataInfo.expectedBG,\
            fast.dataset.dataInfo.upperLimit*lum,fast.dataset.dataInfo.expectedUpperLimit*lum
            print fast.value[0].value*lum
            fastTxnames = []        
            for iel,el in enumerate(fast.cluster.elements):
                fastTxnames.append([fast.txnames[iel].txName,el.weight[0].value*lum])
            fastTxnames = sorted(fastTxnames, key=lambda tx: tx[1], reverse=True)
            print fastTxnames
            continue
    
    print '\n\n Results missing in Fastlim:'
    print [pred.expResult.globalInfo.id for pred in missPredsFast]
    print ' Results missing in SModelS:'
    print [pred.expResult.globalInfo.id for pred in missPredsSmod]
    
        
            
    sys.exit()
   

