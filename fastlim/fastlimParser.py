#!/usr/bin/env python

"""
.. module:: fastlimParser
   :synopsis: Parses the fastlim output and converts it to a python dictionary format

.. moduleauthor: Andre Lessa <lessa.a.p@gmail.com:

"""
import sys,os,logging
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
from fastlimHelpers import smodels2fastlim
from smodels.tools.physicsUnits import GeV, fb, TeV
from smodels.experiment import databaseObjects, datasetObject, infoObject
from smodels.theory.theoryPrediction import TheoryPrediction, TheoryPredictionList
from smodels.theory.theoryPrediction import _getBestResults
from smodels.theory.crossSection import XSectionList, XSection, XSectionInfo

logger = logging.getLogger(__name__)


def fastlimParser(outputfile,useBestDataset=True,expResID=None,txname=None):
    """
    Parses the fastlim output file and converts it to a TheoryPredictionList object
    :param outputfile: Path to fastlim output file (string)
    :param useBestData: If True will only keep the best dataset (signal region) for
                        each experimental result
    :param txname: Used to select results for a specific Txname (i.e. T2tt,T5bbbb,...)
                   If None will return the total prediction.
    :param expResID: Used to select results for a experimental result (i.e. ATLAS-CONF-xxx)
                   If None will return predictions for all IDs.
    :return: TheoryPredictionList object with TheoryPrediction objects for all datasets
    """
    

    if not os.path.isfile(outputfile):
        logger.error("Output file %s not found" % (outputfile))
        return False
    
    
    if txname:
        fastname = smodels2fastlim(txname)
        if not fastname:
            logger.error("Txname %s not found in dictionary" % (txname))
            return False
    
    outfile = open(outputfile,'r')
    outdata = outfile.readlines()
    outfile.close()
    
    theoryPredictions = TheoryPredictionList()
            
    analysesSection = 0
    for il,l in enumerate(outdata):
        l = l.replace('\n','')
        if 'Analyses Details' in l:
            analysesSection = il            
        if not analysesSection or il <= analysesSection+2: continue
        
        #Beginning of experimental result
        if 'ATLAS' in l or 'CMS' in l:
            expID = l.replace('[','').replace(']','').replace('_','-')
            comment = outdata[il+1]
            url = outdata[il+2]        
            expRes = databaseObjects.ExpResult()
            expRes.datasets = []
            expRes.globalInfo = infoObject.Info()
            expRes.globalInfo.id = expID
            expRes.globalInfo.comment = comment
            expRes.globalInfo.url = url
            datasetPredictionLists = []         
        elif 'Ecm/TeV' in l:
            sqrts = eval(l.split('=')[1])*TeV
            expRes.globalInfo.sqrts = sqrts
        elif 'lumi*fb' in l:
            lumi = eval(l.split('=')[1])/fb
            expRes.globalInfo.lumi = lumi
        
        #Beginning of dataset (signal region):
        elif '#---- ' in l:
            predictionList = TheoryPredictionList()            
            dataset = datasetObject.DataSet(infoObj=expRes.globalInfo)            
            datasetId = l[l.find('#----')+5:l.rfind('----#')].replace(' ','')                       
            dataset.dataInfo = infoObject.Info()
            dataset.dataInfo.dataType = 'efficiencyMap'
            dataset.dataInfo.dataId = datasetId
            
            expRes.datasets.append(dataset)
        elif 'Nobs' in l:
            Nobs = eval(l.split(':')[1])
            dataset.dataInfo.observedN = Nobs
        elif 'Nbg' in l:
            val = l.split(':')[1].replace(' ','')
            expectedBG = eval(val[:val.find('(')])
            bgError = eval(val[val.find('(')+1:val.rfind(')')])
            dataset.dataInfo.expectedBG = expectedBG
            dataset.dataInfo.bgError = bgError
        elif 'Nvis_UL[observed]' in l:
            upperLimit = eval(l.split(':')[1])/lumi
            dataset.dataInfo.upperLimit = upperLimit        
        elif 'Total' in l and not txname:
            theoPred = TheoryPrediction()
            theoPred.expResult = expRes
            theoPred.dataset = dataset
            theoPred.txnames = []
            value = eval(l.split()[1])/lumi
            if value.asNumber(fb) == 0.: continue #Skip empty results
            xsecs = XSectionList()
            xsecs.xSections.append(XSection())
            xsecs[0].value = value
            xsecs[0].info = XSectionInfo()
            xsecs[0].info.sqrts = sqrts
            xsecs[0].info.label = '8 TeV'
            theoPred.value = xsecs
            theoPred.conditions = None
            theoPred.mass = None
            theoPred.PIDs = []            
            predictionList._theoryPredictions.append(theoPred)
            datasetPredictionLists.append(predictionList)
        elif txname and fastname in l:
            theoPred = TheoryPrediction()
            theoPred.expResult = expRes
            theoPred.dataset = dataset            
            theoPred.txnames = [txname]
            #Lines with zero cross-sections are shown as nan for the txnames in fastlim
            if 'nan' in l: continue
            value = eval(l.split()[1])/lumi
            if value.asNumber(fb) == 0.: continue #Skip empty results
            xsecs = XSectionList()
            xsecs.xSections.append(XSection())
            xsecs[0].value = value
            xsecs[0].info = XSectionInfo()
            xsecs[0].info.sqrts = sqrts
            xsecs[0].info.label = '8 TeV'
            theoPred.value = xsecs
            theoPred.conditions = None
            theoPred.mass = None
            theoPred.PIDs = []            
            predictionList._theoryPredictions.append(theoPred)
            datasetPredictionLists.append(predictionList)
            
        #Beginning of next experimental result           
        if '-----------------' in l or il == len(outdata)-1:
            if expResID and expID != expResID: continue 
            if not datasetPredictionLists: continue
            if useBestDataset:
                theoryPredictions += _getBestResults(datasetPredictionLists)
            else:
                for theoPredList in datasetPredictionLists:
                    theoryPredictions += theoPredList
            
            
    return theoryPredictions
            

if __name__ == '__main__':
    theoPreds = fastlimParser('./fastlim-1.0/fastlim.out',useBestDataset=True,
                              txname='T1bbbb',expResID='ATLAS-CONF-2013-054')
    for theoPred in theoPreds:
        expRes = theoPred.expResult
        datasetID = theoPred.dataset.getValuesFor('dataId')[0]
        print 'id=',expRes.getValuesFor('id')[0]
        print 'dataset=',datasetID
        print 'value=',theoPred.value
        print 'ul=', expRes.getUpperLimitFor(dataID=datasetID)
