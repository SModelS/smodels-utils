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

home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
import tempfile,tarfile
from smodels.tools.physicsUnits import fb, GeV, TeV
from fastlimOutput import fastlimParser, formatOutput
import subprocess
import pyslha

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

def runFastlim(slhafile,outfile,fastlimdir='../fastlim-1.0/'):
    """
    Runs fastlim for the SLHA file. The output is copied to outfile.
    
    :param slhafile: Path to the SLHA file
    :param outfile: Path to the outputfile
    :param fastlimdir: Folder containing fastlim data and fastlim.py
    
    :return: True/False if the run was/was not successful 
    """
    
    if not os.path.isdir(fastlimdir):
        logger.error('Fastlim folder %s not found' %fastlimdir)
        return False
    if not os.path.isfile(os.path.join(fastlimdir,'fastlim.py')):
        logger.error("fastlim.py not found in %s" %fastlimdir)
        return False
    
    try:
        proc = subprocess.Popen([os.path.join(fastlimdir,'fastlim.py'),slhafile],
                                cwd = fastlimdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
    except:    
        logger.error('Error running fastlim')
        return False
    
    #Copy the output (default is fastlim.out) to the outfile
    shutil.copy(os.path.join(fastlimdir,'fastlim.out'),outfile)
    return True
    
    

def runFastlimFor(slhadir,fastlimdir,expResID=None,txname=None,outType='sms'):
    """
    Runs fastlim for the SLHA files in slhaFiles. Uses only the best
    dataset for each experimental result.
    
    :param slhadir: Path to the folder with the SLHA files or the tar ball containing the files (string)
    :param fastlimdir: Folder containing fastlim data and fastlim.py
    :param txname: Used to only use efficiencies for a specific Txname 
                   (i.e. T2tt,T5bbbb,...). If None will return the total prediction.
    :param expResID: Used to select results for a experimental result (i.e. ATLAS-CONF-xxx)
                   If None will return predictions for all IDs.
    :param outType: Type of output (see fastlimOutput.formatOutput)                   

    :return: List of dictionaries containing the output of each file
    """

    #Create temp file    
    slhaFiles,slhaD = getSlhaFiles(slhadir)
    
    
    #Loop over SLHA files and compute results:
    data = []
    for slhafile in slhaFiles:
        print slhafile
        infile = tempfile.mkstemp()
        os.close(infile[0])
        infile = infile[1]
        prepareSLHA(slhafile,infile)
        outputfile = 'fastlim.out'
        #Run Fastlim
        proc = runFastlim(infile,outputfile,fastlimdir)
        if not proc:
            logger.error("Fastlim failed for file %s" %slhafile)
            return False

        #Convert results to SModelS format (TheoryPredictionList)      
        predictions = fastlimParser(outputfile,useBestDataset=True,
                                    expResID=expResID,txname=txname)                
        if infile != slhafile: os.remove(infile)
        
        #Format output to a python dictionary
        output = formatOutput(slhafile,predictions,outType)
        if outType == 'sms':            
            outfile = open(slhafile.replace('.slha','.sms'),'w')
            outfile.write(str(output))
            outfile.close()
            data.append(slhafile.replace('.slha','.sms'))
        elif outType == 'dict':
            data.append(output)

    #Remove temporary folder
    if slhaD != slhadir: shutil.rmtree(slhaD)
    #Remove temp file
    if os.path.isfile(outputfile): os.remove(outputfile)

    return data


def prepareSLHA(slhafile,newfile):
    """
    Prepares a SLHA file to be read by fastlim.
    Removes the XSECTION blocks and adds missing decay blocks
    
    :param slhafile: path to the original SLHA file
    :param outfile: path to the new SLHA file
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
    