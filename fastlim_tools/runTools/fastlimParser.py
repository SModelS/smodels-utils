#!/usr/bin/env python

"""
.. module:: fastlimOutput
   :synopsis: Tools for dealing with the fastlim output and converting it to a python dictionary format

.. moduleauthor: Andre Lessa <lessa.a.p@gmail.com:

"""
import sys,os,logging
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
sys.path.append(os.path.join(home,'smodels-utils/fastlim_tools/convertTools'))
sys.path.append(os.path.join(home,'smodels-database'))

from convertHelpers import smodels2fastlim
from smodels.base.physicsUnits import GeV, fb, TeV
from smodels.experiment import databaseObjects, datasetObject, infoObject
from smodels.theory.theoryPrediction import TheoryPrediction, TheoryPredictionList
from smodels.theory.theoryPrediction import _getBestResults
from smodels.theory.crossSection import XSectionList, XSection, XSectionInfo
from smodels.theory.clusterTools import ElementCluster
from smodels.theory.element import Element
from signalregions import SRs
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


def fastlimParser(outputfile,useBestDataset=True,expResID=None,datasetID=None,txname=None):
    """
    Parses the fastlim output file and converts it to a TheoryPredictionList object
    :param outputfile: Path to fastlim output file (string)
    :param useBestData: If True will only keep the best dataset (signal region) for
                        each experimental result
    :param txname: Used to select results for a specific Txname (i.e. T2tt,T5bbbb,...)
                   If None will return the total prediction.
    :param expResID: Used to select results for a experimental result (i.e. ATLAS-CONF-xxx)
                   If None will return predictions for all experimental results.
    :param datasetID: Used to select a specific dataset (i.e. data-cut0)
                   If None will return predictions for all datasets.
                   If != None, it overwrites the useBestDataset option.                   
    :return: TheoryPredictionList object with TheoryPrediction objects for all datasets
    """
    

    if not os.path.isfile(outputfile):
        logger.error("Output file %s not found" % (outputfile))
        return False
        
    if txname:
        if not smodels2fastlim(txname):
            logger.error("Txname %s not found in dictionary" % (txname))
            return False
    
    outfile = open(outputfile,'r')
    data = outfile.read()
    outfile.close()
            
    data = data[data.find('Analyses Details'):]
    #Get list of expResults blocks
    expResults = data.split('------------------------------------------------------------')[1:]
    
    theoryPredictions = TheoryPredictionList()    
    for expBlock in expResults:        
        datasets = expBlock.split('#----')
        #Get ExpResult object:
        expRes = getExpResFromFastlim(datasets[0])
        if expResID and expRes.globalInfo.id != expResID:
            continue
        predictionList = [] #List of predictions for the datasets
        for datasetBlock in datasets[1:]:
            #Get DataSet object:               
            dataset = getDataSetFromFastlim(datasetBlock,expRes)
            if datasetID and dataset.dataInfo.dataId != datasetID:
                continue
            expRes.datasets.append(dataset)
            #Get TheoryPredictionList object (with one entry):
            theoPreds = getTheoryPredFromFastlim(datasetBlock,expRes,dataset,txname) 
            if not theoPreds: continue
            predictionList.append(theoPreds)
        if not predictionList: continue
        if useBestDataset:
            theoryPredictions += _getBestResults(predictionList)
        else:
            for theoPredList in predictionList:
                theoryPredictions += theoPredList
    
    return theoryPredictions
        
def  getExpResFromFastlim(block):
    """
    Reads a Fastlim block containing the basic information
    about an experimental result and returns the corresponding ExpResult object
    :param block: Single block of string containing the required information
    :return: ExpResult object
    """
    
    lines = block.split('\n')
    expID,comment,url,sqrts,lumi = None,None,None,None,None
    for il,l in enumerate(lines):
        if not l.strip(): continue
        if 'ATLAS' in l or 'CMS' in l:            
            expID = l.replace('[','').replace(']','').replace('_','-')
            comment = lines[il+1]
            url = lines[il+2]
        elif 'Ecm/TeV' in l:
            sqrts = eval(l.split('=')[1])*TeV
        elif 'lumi*fb' in l:
            lumi = eval(l.split('=')[1])/fb

    #Create object
    expRes = databaseObjects.ExpResult()
    expRes.datasets = []
    expRes.globalInfo = infoObject.Info()
    expRes.globalInfo.id = expID
    expRes.globalInfo.comment = comment
    expRes.globalInfo.url = url
    expRes.globalInfo.sqrts = sqrts
    expRes.globalInfo.lumi = lumi
    
    return expRes

def  getDataSetFromFastlim(block,expRes):
    """
    Reads a Fastlim block containing the basic information
    about a dataset/signal region and returns the corresponding DataSet object
    :param block: Single block of string containing the required information
    :param expRes: Corresponding ExpResult object (necessary obtaining additional info)
    :return: DataSet object
    """    

    lumi = expRes.globalInfo.lumi
    datasetId,Nobs,expectedBG,bgError,upperLimit = None,None,None,None,None
    lines = block.split('\n')
    for l in lines:
        if not l.strip(): continue
        if '----#' in l:
            datasetId = l.replace('----#','').strip()
        if 'Nobs' in l:
            Nobs = eval(l.split(':')[1])
        elif 'Nbg' in l:
            val = l.split(':')[1].replace(' ','')
            expectedBG = eval(val[:val.find('(')])
            bgError = eval(val[val.find('(')+1:val.rfind(')')])
        elif 'Nvis_UL[observed]' in l:
            upperLimit = eval(l.split(':')[1])/lumi

    datasetDict = SRs[expRes.globalInfo.id]
    for key,val in datasetDict.items():
        if val == datasetId or val.replace(" ","") == datasetId:
            datasetId = key
            break
                
    #Create object:
    dataset = datasetObject.DataSet(infoObj=expRes.globalInfo)
    dataset.dataInfo = infoObject.Info()
    dataset.dataInfo.dataType = 'efficiencyMap'
    dataset.dataInfo.dataId = datasetId
    dataset.dataInfo.observedN = Nobs
    dataset.dataInfo.expectedBG = expectedBG
    dataset.dataInfo.bgError = bgError
    dataset.dataInfo.upperLimit = upperLimit
    dataset.dataInfo.expectedUpperLimit = dataset.getSRUpperLimit(0.05,expected=True,compute=True)
    
    return dataset


def  getTheoryPredFromFastlim(block,expRes,dataset,txname):
    """
    Reads a Fastlim block containing the basic information
    about a dataset/signal region and returns the corresponding TheoryPredictionList object
    (The list only contains a single theory prediction)
    :param block: Single block of string containing the required information
    :param expRes: Corresponding ExpResult object (necessary obtaining additional info)
    :param dataset: Corresponding DataSet object (necessary obtaining additional info)
    :return: TheoryPredictionList object
    """    

    lumi = expRes.globalInfo.lumi
    sqrts = expRes.globalInfo.sqrts
    txnames = []    
    #Select useful part of block:
    lines = block.split('Process')[1].split('\n')[1:]
    cluster = ElementCluster()
    for l in lines:
        if not l.strip(): continue
        if 'Total' in l:
            value = eval(l.split()[1])/lumi
            if value.asNumber(fb) == 0.: return None #Skip null results
            totalXsec = XSectionList()
            totalXsec.xSections.append(XSection())
            totalXsec[0].value = value
            totalXsec[0].info = XSectionInfo()
            totalXsec[0].info.sqrts = sqrts
            totalXsec[0].info.label = '8 TeV'       
        else:
            fastname, Nev, R = l.split()
            fastname = fastname.strip()            
            if 'nan' in Nev: continue
            Nev = eval(Nev)
            if not Nev: continue
            R = eval(R)            
            txnames.append(EmptyTxName(smodels2fastlim('Dict')[fastname]))
            xsec = XSectionList()
            xsec.xSections.append(XSection())
            xsec[0].value = Nev/lumi
            xsec[0].info = XSectionInfo()
            xsec[0].info.sqrts = sqrts
            xsec[0].info.label = '8 TeV'
            element = Element()
            element.weight = xsec
            cluster.elements.append(element)
            
    #Create Object:    
    theoPred = TheoryPrediction()
    theoPred.expResult = expRes
    theoPred.dataset = dataset
    theoPred.cluster = cluster
    theoPred.txnames = txnames
    theoPred.conditions = None
    theoPred.mass = None
    theoPred.PIDs = []  
    #Select specific txname (if required)
    if txname:
        if not txname in txnames:
            return None
        else:
            itx = txnames.index(txname)
            theoPred.cluster.elements = cluster.elements[itx:itx+1]
            theoPred.txnames = txnames[itx:itx+1]
        theoPred.value = theoPred.cluster.getTotalXSec()
    else:
        theoPred.value = totalXsec
    theoPredList = TheoryPredictionList()
    theoPredList._theoryPredictions.append(theoPred)
    
    return theoPredList
        
class EmptyTxName(object):
    """Empty txname object just to hold the TxName label from fastlim"""
    
    def __init__(self, txname=None):
        self.txName = txname    


