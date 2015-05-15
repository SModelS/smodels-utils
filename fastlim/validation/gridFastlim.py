#!/usr/bin/env python

"""
.. module:: gridFastlim
   :synopsis: Defines the functionalities required to run fastlim on
   a grid of SLHA files for producing a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import os,sys,logging,shutil
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

sys.path.append('../')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
import tempfile,tarfile
from smodels.tools.physicsUnits import fb, GeV
from fastlimMod import fastlimMain
from fastlimParser import fastlimParser
from smodels.tools import modpyslha
import subprocess

logger.setLevel(level=logging.DEBUG)

def getSlhaFiles(slhadir):
    """
    Returns a list of valid SLHA files in slhadir
    :param slhadir: path to the SLHA folder or the tar ball containing the files (string)
    :return: list of SLHA files (list of strings)
    """

    slhaFiles = []
    if os.path.isdir(slhadir):
        slhaD = slhadir
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

def runFastlimFor(slhadir,expResID=None,txname=None):
    """
    Runs fastlim for the SLHA files in slhaFiles. Uses only the best
    dataset for each experimental result.
    
    :param slhadir: Path to the folder with the SLHA files
    :param txname: Used to only use efficiencies for a specific Txname 
                   (i.e. T2tt,T5bbbb,...). If None will return the total prediction.
    :param expResID: Used to select results for a experimental result (i.e. ATLAS-CONF-xxx)
                   If None will return predictions for all IDs.

    :return: 
    """

    #Create temp file    
    slhaFiles,slhaD = getSlhaFiles(slhadir)
    
    
    #Loop over SLHA files and compute results:
    data = []
    for slhafile in slhaFiles:
        infile = prepareSLHA(slhafile)
        proc = subprocess.Popen(['../fastlim-1.0/fastlim.py',infile],
                                cwd = '../fastlim-1.0/', stdout=subprocess.PIPE
                                , stderr=subprocess.PIPE)
        proc.wait()
        outputfile = os.path.join(home,'smodels-utils/fastlim/fastlim-1.0/fastlim.out')        
        predictions = fastlimParser(outputfile,useBestDataset=True,
                                    expResID=expResID,txname=txname)
        
        
        if infile != slhafile: os.remove(infile)
        if not predictions:
            logger.info ( "no theory predictions for %s in %s" % ( expResID,slhafile) )
            continue
        
        for theoryPrediction in predictions:
            expRes = theoryPrediction.expResult
            expID = expRes.getValuesFor('id')[0]
            dataset = theoryPrediction.dataset
            datasetID = dataset.dataInfo.dataId
            value = theoryPrediction.value
            cond = theoryPrediction.conditions
            upperLimit = expRes.getUpperLimitFor(dataID=datasetID)
            txnames = theoryPrediction.txnames

            if len(value) != 1:
                logger.warning("More than one cross-section found. Using first one")
            value = value[0].value
            
            Dict= {'slhafile' : slhafile, 'signal' : value,
                    'UL' : upperLimit, 'condition': cond,
                     'dataset': datasetID, 'expID': expID, 'txnames' : txnames}

            data.append(Dict)


    #Remove temporary folder
    if slhaD != slhadir: shutil.rmtree(slhaD)
    #Remove temp file
    if os.path.isfile(outputfile): os.remove(outputfile)


    return data


def prepareSLHA(slhafile):
    """
    Prepares a SLHA file to be read by fastlim.
    Removes the XSECTION blocks and adds missing decay blocks
    
    :param slhafile: path to the SLHA file
    :return: path to new file
    """
    
    #Create new temp file
    newfile = tempfile.mkstemp('.slha','tmp' , './')
    os.close(newfile[0])
    newfile = newfile[1]
    
    #Remove XSECTION block from slhafile
    slha = open(slhafile,'r')
    slhadata = slha.read()
    slha.close()
    if 'XSECTION' in slhadata:
        slhadata = slhadata[:slhadata.find('XSECTION')]
    slha = open(newfile,'w')
    slha.write(slhadata)
    slha.close()  
     
    pyslha = modpyslha.readSLHAFile(slhafile)
    slha = open(newfile,'a')
    for pid in pyslha.blocks['MASS']:
        if not pid in pyslha.decays:
            slha.write("#         PDG            Width\n")
            slha.write("DECAY   "+str(pid)+"     0.00000000E+00\n")
    slha.close()
        
    return newfile
    


if __name__ == '__main__':
    
    slhaDir = '/home/lessa/smodels-utils/slha/T2tt.tar'
    print runFastlimFor(slhaDir,expResID='ATLAS-CONF-2013-053',txname='T2tt')
