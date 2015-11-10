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
from convertHelpers import smodels2fastlim
from smodels.tools.physicsUnits import GeV, fb, TeV
from smodels.experiment import databaseObjects, datasetObject, infoObject
from smodels.theory.theoryPrediction import TheoryPrediction, TheoryPredictionList
from smodels.theory.theoryPrediction import _getBestResults
from smodels.theory.crossSection import XSectionList, XSection, XSectionInfo
from collections import OrderedDict
import pyslha, unum
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


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
            ExptRes.append({'maxcond': maxconds, 'tval': value.asNumber(fb),
                        'exptlimit': upperLimit.asNumber(fb), 
                        'AnalysisTopo': txname, 
                        'DaughterMass': mass[0][-1].asNumber(GeV), 
                        'AnalysisName': expID,
                        'DataSet' : datasetID, 
                        'AnalysisSqrts': sqrts,                        
                        'MotherMass': mass[0][0].asNumber(GeV),
                        'ObservedN' : observedN,
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


def compareFiles(file1,file2,allowedDiff=0.001):
    """
    Compare two files containing SModelS output in a python dictionary format.
    The numerical values are compared up to the precision defined by allowedDiff.
    
    :param file1: Output file name (containing a python dict)
    :param file2: Output file name (containing a python dict)
    :param allowedDiff: Allowed % difference between two numerical values 
                    
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
    
    return equalObjs(dicts[0],dicts[1],allowedDiff)
                

def equalObjs(obj1,obj2,allowedDiff):
    """
    Compare two objects.
    The numerical values are compared up to the precision defined by allowedDiff.
    
    :param obj1: First python object to be compared 
    :param obj2: Second python object to be compared
    :param allowedDiff: Allowed % difference between two numerical values 
                    
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


