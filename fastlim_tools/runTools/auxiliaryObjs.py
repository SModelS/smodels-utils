#!/usr/bin/env python

"""
.. module:: auxiliaryObjs
   :synopsis: Several auxiliary methods and classes

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import os,sys,logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
import tempfile,tarfile
import pyslha, unum
from smodels.base.physicsUnits import GeV, fb, TeV
from collections import OrderedDict

import signal


def prepareSLHA(slhafile,newfile):
    """    
    Removes the XSECTION blocks and adds missing decay blocks from the SLHA file
    and writes the result to a new file.
    
    :param slhafile: path to the original SLHA file
    :param newfile: path to the new SLHA file
    :return: path to new file
    """
    
    
    #Remove XSECTION block from slhafile
    slha = open(slhafile,'r')
    slhadata = slha.read()
    slha.close()
    if 'XSECTION' in slhadata:
        slhadata = slhadata[:slhadata.find('XSECTION')]
    slha = open(newfile,'w')
    slha.write(slhadata)
    slha.close()  
     
    pyslhaData = pyslha.readSLHAFile(slhafile)
    slha = open(newfile,'a')
    for pid in pyslhaData.blocks['MASS'].keys():
        if not pid in pyslhaData.decays:
            slha.write("#         PDG            Width\n")
            slha.write("DECAY   "+str(pid)+"     0.00000000E+00\n")
    slha.close()
        
    return True
    

def getSlhaFiles(slhadir):
    """
    Returns a list of valid SLHA files in slhadir
    :param slhadir: path to the SLHA folder or the tar ball containing the files (string)
    :return: list of SLHA files (list of strings)
    """

    slhaFiles = []
    if os.path.isdir(slhadir):
        slhaD = os.path.abspath(slhadir)
    elif os.path.isfile(slhadir):
        try:
            tar = tarfile.open(slhadir)
            tempdir = tempfile.mkdtemp(dir=os.getcwd())
            tar.extractall(path=tempdir)
            slhaD = tempdir
        except:
            logger.error("Could not extract SLHA files from %s" %slhadir)
            sys.exit()
    else:
        logger.error("%s is not a file nor a folder" %slhadir)
        sys.exit()

    for root, dirs, files in os.walk(slhaD):
        for slhafile in files:
            slhafile = os.path.join(root,slhafile)
            f = open(slhafile,'r')
            fdata = f.read()
            f.close()
            #Skip non-SLHA files
            if not 'BLOCK MASS' in fdata: continue
            slhaFiles.append(slhafile)

    return slhaFiles,slhaD


def formatOutput(slhafile,predictions,extraInfo={},minval=0.00005):
    """
    Format the list of theory predictions and the SLHA file input to a specific output
    format.
    Accepted formats are:
    sms = convert the output to a python dictionary (to be written to a .sms file)
    valplot = convert the output to a python dictionary (to be used in a validation plot)
    
    :param slhafile: Name of the corresponding SLHA file
    :param prediction: TheoryPredictionList object (output of fastlimParser)
        :param extraInfo: Additional information to be stored in the file
    :param minval: Option to remove predictions with very low theory predictions
                   (useful since fastlim already rounds its output to 4 digits)    
    :return: Name of sms file.
    """
    
    ExptRes = []
    for theoryPrediction in predictions:
        expRes = theoryPrediction.expResult        
        expID = expRes.globalInfo.id
        dataset = theoryPrediction.dataset
        datasetID = dataset.dataInfo.dataId
        value = theoryPrediction.value[0].value                     
        upperLimit = dataset.dataInfo.upperLimit
        txnames = [txname.txName for txname in theoryPrediction.txnames]
        weights = [el.weight[0].value.asNumber(fb) for el in theoryPrediction.cluster.elements]
        maxconds = theoryPrediction.getmaxCondition()
        mass = theoryPrediction.mass
        #Cut very low values (since fastlim only prints 4 digits):
        if expRes.globalInfo.lumi*value < minval: continue
                    
        #Fix for the case of eff maps:
        if not mass: mass = [[0.*GeV,0.*GeV],[0.*GeV,0.*GeV]]
        sqrts = dataset.globalInfo.sqrts.asNumber(TeV)
        observedN = dataset.dataInfo.observedN
        expectedBG = dataset.dataInfo.expectedBG
        ExptRes.append({'maxcond': maxconds, 'tval': value.asNumber(fb),
                    'exptlimit': upperLimit.asNumber(fb), 
#                    'AnalysisTopo': txnames,
                    'Weights' : weights,
                    'DaughterMass': mass[0][-1].asNumber(GeV), 
                    'AnalysisName': expID,
                    'DataSet' : datasetID, 
                    'AnalysisSqrts': sqrts,                        
                    'MotherMass': mass[0][0].asNumber(GeV),
                    'observedN' : observedN,
                    'expectedBG' : expectedBG,
                    'lumi' : (expRes.globalInfo.lumi*fb).asNumber()})
        

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



class FastlimError(Exception):
    """
    The fastlim run exception. Raised when the Fastlim fails
    """
    def __init__(self, infile=None):
        self.infile = infile
        Exception.__init__(self, infile)
        
    def __str__(self):
        return 'Fastlim failed for %s' %self.infile

class SModelSError(Exception):
    """
    The smodels run exception. Raised when the SModelS fails
    """
    def __init__(self, infile=None):
        self.infile = infile
        Exception.__init__(self, infile)
        
    def __str__(self):
        return 'SModelS failed for %s' %self.infile    
    

class NoTime(Exception):
    """
    The time out exception. Raised when the running time exceeds timeout
    """
    def __init__(self, value=None):
        self.value = value
        Exception.__init__(self, value)
        
    def __str__(self):
        return '%.2f s time out exceeded' %float(self.value)


class Timeout():
    """Timeout class using ALARM signal."""
    
    def __init__(self, sec):
        self.sec = sec
 
    def __enter__(self):
        if self.sec:            
            signal.signal(signal.SIGALRM, self.raise_timeout)
            signal.alarm(self.sec)            
 
    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm
 
    def raise_timeout(self, *args):
        raise NoTime(self.sec)
