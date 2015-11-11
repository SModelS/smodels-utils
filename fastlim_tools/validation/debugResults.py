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
from smodels.theory import slhaDecomposer, crossSection
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
    database.expResultList = database.getExpResults(analysisIDs=[expResID])
    useDataset = None
    for dataset in database.expResultList[0].datasets:
        if dataset.getValuesFor('dataId')[0] == datasetId:
            useDataset = dataset
     
    if datasetId: database.expResultList[0].datasets = [useDataset]

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
    print 'total =',total,'totaldecomp = ',totdecomp,'coverage = ',totdecomp/total,'diff = ',total-totdecomp

    from smodels.theory import theoryPrediction
    predictions = theoryPrediction.TheoryPredictionList()    
    for expRes in database.expResultList:
        preds =  theoryPrediction.theoryPredictionsFor(expRes, smstoplist)        
        if preds:
            for theoryPrediction in preds:
                expRes = theoryPrediction.expResult
                expID = expRes.getValuesFor('id')[0]
                dataset = theoryPrediction.dataset
                datasetID = dataset.dataInfo.dataId
                value = theoryPrediction.value[0].value
                upperLimit = expRes.getUpperLimitFor(dataID=datasetID)
                txnames = theoryPrediction.txnames
                if len(txnames) == 1:
                    txname = txnames[0].getInfo('txName')
                else: txname = []
                maxconds = theoryPrediction.getmaxCondition()
                mass = theoryPrediction.mass
                #Fix for the case of eff maps:
                if not mass: mass = [[0.*GeV,0.*GeV],[0.*GeV,0.*GeV]]
                sqrts = dataset.getValuesFor('sqrts')[0].asNumber(TeV)
                observedN = dataset.getValuesFor('observedN')[0]
                expectedBG = dataset.getValuesFor('expectedBG')[0]
                ExptRes = {'maxcond': maxconds, 'tval': value,
                            'exptlimit': upperLimit, 
                            'AnalysisTopo': txname, 
                            'DaughterMass': mass[0][-1].asNumber(GeV), 
                            'AnalysisName': expID,
                            'DataSet' : datasetID, 
                            'AnalysisSqrts': sqrts,                        
                            'MotherMass': mass[0][0].asNumber(GeV),
                            'ObservedN' : observedN,
                            'expectedBG' : expectedBG}
#                 print ExptRes.
#                 for el in theoryPrediction.cluster.elements:
#                     print el,el.weight[0],el.eff
    
            predictions += preds

    for t in predictions:
        print t.expResult.getValuesFor('id')
        print '    ',t.expResult.getValuesFor('dataId')
        print '    ',t.dataset.getValuesFor('dataId')[0],t.dataset.getValuesFor('observedN')[0],t.dataset.getValuesFor('expectedBG')[0]
        print '    ',t.value
        print '    ',[txname.txName for txname in t.txnames]
        print '    ',[el.weight[0].value for el in t.cluster.elements]
        print '    ',[el.eff for el in t.cluster.elements]

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
    for t in predictions:
        print t.expResult.getValuesFor('id')
        print '    ',t.expResult.getValuesFor('dataId')
        print '    ',t.dataset.getValuesFor('dataId')[0],t.dataset.getValuesFor('observedN')[0],t.dataset.getValuesFor('expectedBG')[0]
        print '    ',t.value
        print '    ',t.txnames
        print '    ',[el.weight[0].value for el in t.cluster.elements]
    
              

if __name__ == '__main__':
    expID =  'ATLAS-CONF-2013-047'
    datasetId = 'data-cut4'
    slhafile = os.path.abspath('./SLHA/strong_lt_TeV_focus/1anKWViqpBkaJuC.slha')
    
    print '------FASTLIM:'
    debugFastlim(slhafile, fastlimdir, expID)
    
    print '------SMODELS:'
    debugSmodelS(slhafile, expID, datasetId)
    
    
    sys.exit()
    
    print runSmodelS(slhafile,os.getcwd()+'/smodels.sms',databasePath,expResID=expID,doXsecs=False)
    print runFastlim(slhafile,os.getcwd()+'/fastlim.sms',fastlimdir,expResID=expID)


