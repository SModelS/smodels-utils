#!/usr/bin/env python

"""
.. module:: gridFastlim
   :synopsis: Defines the functionalities required to run fastlim on
   a grid of SLHA files

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
import multiprocessing

logger.setLevel(level=logging.DEBUG)

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

def runFastlim(slhafile,outfile,fastlimdir='../fastlim-1.0/',expResID=None,txname=None):
    """
    Runs fastlim for the SLHA file and generate the corresponding .sms file.
    
    :param slhafile: Path to the SLHA file
    :param outfile: Path to the outputfile
    :param fastlimdir: Folder containing fastlim data and fastlim.py
    :param txname: Used to only use efficiencies for a specific Txname 
                   (i.e. T2tt,T5bbbb,...). If None will return the total prediction.
    :param expResID: Used to select results for a experimental result (i.e. ATLAS-CONF-xxx)
                   If None will return predictions for all IDs.
    
    
    :return: True/False if the run was/was not successful 
    """
    
    #Several checks to make sure Fastlim will run with the correct input
    if not os.path.isdir(fastlimdir):
        logger.error('Fastlim folder %s not found' %fastlimdir)
        return False
    if not os.path.isfile(os.path.join(fastlimdir,'fastlim.py')):
        logger.error("fastlim.py not found in %s" %fastlimdir)
        return False
    if not os.path.isabs(fastlimdir):
        logger.error("Please provide an absolute for fastlim dir.")
        return False
    
    if not os.path.isfile(slhafile):
        logger.error("File: %s not found" %slhafile)
        return False
    elif not os.path.isabs(slhafile) or not os.path.isabs(outfile):
        logger.error("Please provide absolute paths for files")
        return False
    
    infile = tempfile.mkstemp()     #Use temp file to store fastlim-ready SLHA file
    os.close(infile[0])
    infile = infile[1]
    prepareSLHA(slhafile,infile)
    try:        
        proc = subprocess.Popen([os.path.join(fastlimdir,'fastlimMod.py'),infile,outfile],
                                cwd = fastlimdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
    except:    
        logger.error('Error running fastlim')
        return False
 
    #Convert results to SModelS format (TheoryPredictionList)      
    predictions = fastlimParser(outfile,useBestDataset=False,
                                expResID=expResID,txname=txname)
    os.remove(infile)      

    #Format output to a python dictionary
    output = formatOutput(slhafile,predictions,'sms',extraInfo={'tool': 'fastlim'})         
    outfile = open(outfile,'w')
    outfile.write(str(output))
    outfile.close()
     
    return True

        

def runFastlimFor(slhadir,fastlimdir,expResID=None,txname=None,np=1,tout=200):
    """
    Runs fastlim for the SLHA files in slhaFiles. Uses only the best
    dataset for each experimental result.
    
    :param slhadir: Path to the folder with the SLHA files or the tar ball containing the files (string)
    :param fastlimdir: Folder containing fastlim data and fastlim.py
    :param txname: Used to only use efficiencies for a specific Txname 
                   (i.e. T2tt,T5bbbb,...). If None will return the total prediction.
    :param expResID: Used to select results for a experimental result (i.e. ATLAS-CONF-xxx)
                   If None will return predictions for all IDs.  
    :param np: Number of parallel processes. If np=1, run as serial. Otherwise uses multiprocessing
    :param tout: Timeout for each process                

    :return: List of sms files generated
    """

    
    #Create temp file    
    slhaFiles,slhaD = getSlhaFiles(slhadir)
    
    #Set up multiprocessing:
    pool = multiprocessing.Pool(processes=np)
    
    #Loop over SLHA files and compute results:    
    results = []
    for slhafile in slhaFiles:        
        outputfile = slhafile.replace(".slha",".sms")
        #Run Fastlim (submit threads):
        results.append([outputfile,
                        pool.apply_async(runFastlim,args=(slhafile,outputfile,fastlimdir,
                                                          expResID,txname))])
        
        
    pool.close()
    #Check results
    data = {}
    for res in results:
        outputfile,run = res       
        try:
            goodRun = run.get(tout)
        except:
            goodRun = False
        if not goodRun:
            logger.error("Fastlim failed for file %s" %outputfile)
        else:
            data[outputfile[outputfile.rfind('/')+1:]] = goodRun
            

    return data


def prepareSLHA(slhafile,newfile):
    """
    Prepares a SLHA file to be read by fastlim.
    Removes the XSECTION blocks and adds missing decay blocks
    
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
    