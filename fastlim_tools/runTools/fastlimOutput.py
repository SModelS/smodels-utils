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
from smodels.tools.physicsUnits import GeV, fb, TeV
from smodels.experiment import databaseObjects, datasetObject, infoObject
from smodels.theory.theoryPrediction import TheoryPrediction, TheoryPredictionList
from smodels.theory.theoryPrediction import _getBestResults
from smodels.theory.crossSection import XSectionList, XSection, XSectionInfo
from smodels.theory.clusterTools import ElementCluster
from smodels.theory.element import Element
from collections import OrderedDict
from signalregions import SRs
import pyslha, unum
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
        if expResID and expRes.getValuesFor('id')[0] != expResID:
            continue
        predictionList = [] #List of predictions for the datasets
        for datasetBlock in datasets[1:]:
            #Get DataSet object:               
            dataset = getDataSetFromFastlim(datasetBlock,expRes)
            if datasetID and dataset.getValuesFor('dataId')[0] != datasetID:
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

    lumi = expRes.getValuesFor('lumi')[0]
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

    datasetDict = SRs[expRes.getValuesFor('id')[0]]
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

    lumi = expRes.getValuesFor('lumi')[0]
    sqrts = expRes.getValuesFor('sqrts')[0]
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


def formatOutput(slhafile,predictions,outType='sms',extraInfo={}):
    """
    Format the list of theory predictions and the SLHA file input to a specific output
    format.
    Accepted formats are:
    sms = convert the output to a python dictionary (to be written to a .sms file)
    valplot = convert the output to a python dictionary (to be used in a validation plot)
    
    :param slhafile: Name of the corresponding SLHA file
    :param prediction: TheoryPredictionList object (output of fastlimParser)
    :param outType: Type of output (see above)
    :param extraInfo: Additional information to be stored in the file
    
    :return: If outType='sms', name of sms file. If outType='valplot', python dictionary
    """
    
    if outType == 'sms':
        ExptRes = []
        for theoryPrediction in predictions:
            expRes = theoryPrediction.expResult
            expID = expRes.getValuesFor('id')[0]
            dataset = theoryPrediction.dataset
            datasetID = dataset.dataInfo.dataId
            value = theoryPrediction.value[0].value
            upperLimit = expRes.getUpperLimitFor(dataID=datasetID)
            txnames = [txname.txName for txname in theoryPrediction.txnames]
            weights = [el.weight[0].value.asNumber(fb) for el in theoryPrediction.cluster.elements]
            maxconds = theoryPrediction.getmaxCondition()
            mass = theoryPrediction.mass
            #Fix for the case of eff maps:
            if not mass: mass = [[0.*GeV,0.*GeV],[0.*GeV,0.*GeV]]
            sqrts = dataset.getValuesFor('sqrts')[0].asNumber(TeV)
            observedN = dataset.getValuesFor('observedN')[0]
            expectedBG = dataset.getValuesFor('expectedBG')[0]
            ExptRes.append({'maxcond': maxconds, 'tval': value.asNumber(fb),
                        'exptlimit': upperLimit.asNumber(fb), 
                        'AnalysisTopo': txnames,
                        'Weights' : weights,
                        'DaughterMass': mass[0][-1].asNumber(GeV), 
                        'AnalysisName': expID,
                        'DataSet' : datasetID, 
                        'AnalysisSqrts': sqrts,                        
                        'MotherMass': mass[0][0].asNumber(GeV),
                        'observedN' : observedN,
                        'expectedBG' : expectedBG})
            

        
        #Additional data:
        res = pyslha.readSLHAFile(slhafile)
        MINPAR = dict(res.blocks['MINPAR'].entries)
        EXTPAR = dict(res.blocks['EXTPAR'].entries)
        mass = OrderedDict(res.blocks['MASS'].entries.items())
        extra = {'sigmacut' : 0.}
        if extraInfo:
            extra.update(extraInfo)
        
        chimix = {}
        for key in res.blocks['NMIX'].entries:
            val = res.blocks['NMIX'].entries[key]
            if key[0] != 1: continue
            newkey = 'N'+str(key[0])+str(key[1])
            chimix[newkey] = val
        chamix = {}
        for key in res.blocks['UMIX'].entries:
            val = res.blocks['UMIX'].entries[key]
            newkey = 'U'+str(key[0])+str(key[1])
            chamix[newkey] = val  
        for key in res.blocks['VMIX'].entries:
            val = res.blocks['VMIX'].entries[key]
            newkey = 'V'+str(key[0])+str(key[1])
            chamix[newkey] = val  
        stopmix = {}
        for key in res.blocks['STOPMIX'].entries:
            val = res.blocks['STOPMIX'].entries[key]
            newkey = 'ST'+str(key[0])+str(key[1])
            stopmix[newkey] = val  
        sbotmix = {}  
        for key in res.blocks['SBOTMIX'].entries:
            val = res.blocks['SBOTMIX'].entries[key]
            newkey = 'SB'+str(key[0])+str(key[1])
            sbotmix[newkey] = val  
    
        #Order ExptRes according to tval:
        ExptRes = sorted(ExptRes, key=lambda k: k['tval'], reverse=True) 
        
        output =  {'ExptRes' : ExptRes, 'MINPAR' : MINPAR, 'extra' : extra, 'chimix' : chimix,
            'stopmix' : stopmix, 'chamix' : chamix, 'MM' : {}, 'sbotmix' : sbotmix,
             'EXTPAR' : EXTPAR, 'mass' : mass}
        
    elif outType == 'valplot':
        if len(predictions) == 0:
            return {'slhafile' : slhafile, 'signal' : None,
                'UL' : None, 'condition': None,'dataset': None, 'expID': None, 'txnames' : None}
        if len(predictions) > 1:
            logger.error("List of predictions > 1. Can not use valplot format.")
            return False
        
        theoryPrediction = predictions[0]
        expRes = theoryPrediction.expResult
        expID = expRes.getValuesFor('id')[0]
        dataset = theoryPrediction.dataset
        datasetID = dataset.dataInfo.dataId
        value = theoryPrediction.value[0].value.asNumber(fb)
        upperLimit = expRes.getUpperLimitFor(dataID=datasetID)
        cond = theoryPrediction.conditions
        txnames = theoryPrediction.txnames
        output = {'slhafile' : slhafile, 'signal' : value,
                'UL' : upperLimit, 'condition': cond,
                 'dataset': datasetID, 'expID': expID, 'txnames' : txnames}
    

    return output            


def compareFiles(file1,file2,allowedDiff=0.001,ignore=[]):
    """
    Compare two files containing SModelS output in a python dictionary format.
    The numerical values are compared up to the precision defined by allowedDiff.
    
    :param file1: Output file name (containing a python dict)
    :param file2: Output file name (containing a python dict)
    :param allowedDiff: Allowed % difference between two numerical values
    :param ignore: List of keys to be ignored 
                    
    :return: True/False    
    """                
    
    dicts = []
    for f in [file1,file2]:
        if not os.path.isfile(f):
            logger.error("File %s not found" %f)
            return False
        fin = open(f,'r')
        dicts.append(eval(fin.read().replace(' [fb]','*fb').replace('[GeV]','*GeV')))
        fin.close()
    
    return equalObjs(dicts[0],dicts[1],allowedDiff,ignore)
                

def equalObjs(obj1,obj2,allowedDiff,ignore=[]):
    """
    Compare two objects.
    The numerical values are compared up to the precision defined by allowedDiff.
    
    :param obj1: First python object to be compared 
    :param obj2: Second python object to be compared
    :param allowedDiff: Allowed % difference between two numerical values 
    :param ignore: List of keys to be ignored
    :return: True/False    
    """      
    
    if type(obj1) != type(obj2):
        logger.info("Data types differ (%s,%s)" %(type(obj1),type(obj2)))
        return False
    
    if isinstance(obj1,unum.Unum):
        if obj1 == obj2:
            return True
        diff = 2.*abs(obj1-obj2)/abs(obj1+obj2)
        return diff.asNumber() < allowedDiff
    elif isinstance(obj1,float):
        if obj1 == obj2:
            return True
        diff = 2.*abs(obj1-obj2)/abs(obj1+obj2)
        return diff < allowedDiff
    elif isinstance(obj1,str):
        return obj1 == obj2
    elif isinstance(obj1,dict):    
        if len(obj1) != len(obj2):
            logger.info("Dictionaries have distinct lengths (%i,%i)" %(len(obj1),len(obj2)))
            return False
        for key in obj1:
            if key in ignore: continue
            if not key in obj2:
                logger.info("Key %s missing" %key)
                return False
            if not equalObjs(obj1[key],obj2[key],allowedDiff):
                logger.info('Objects differ:\n   %s\n and\n   %s' %(str(obj1[key]),str(obj2[key])))
                return False
    elif isinstance(obj1,list):
        for ival,val in enumerate(sorted(obj1)):
            if not equalObjs(val,sorted(obj2)[ival],allowedDiff):
                logger.info('Objects differ:\n   %s \n and\n   %s' %(str(val),str(sorted(obj2)[ival])))
                return False
    else:
        return obj1 == obj2
            
    return True           

