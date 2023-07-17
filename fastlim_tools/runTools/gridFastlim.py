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
from smodels.base.physicsUnits import fb, GeV, TeV
from fastlimParser import fastlimParser
import subprocess
import multiprocessing
from auxiliaryObjs import Timeout, getSlhaFiles, FastlimError, formatOutput, NoTime

logger.setLevel(level=logging.DEBUG)


def runFastlim(slhafile,outfile,fastlimdir='../fastlim-1.0/',expResID=None,txname=None,tout=None):
    """
    Runs fastlim for the SLHA file and generate the corresponding .sms file.
    
    :param slhafile: Path to the SLHA file
    :param outfile: Path to the outputfile
    :param fastlimdir: Folder containing fastlim data and fastlim.py
    :param txname: Used to only use efficiencies for a specific Txname 
                   (i.e. T2tt,T5bbbb,...). If None will return the total prediction.
    :param expResID: Used to select results for a experimental result (i.e. ATLAS-CONF-xxx)
                   If None will return predictions for all IDs.
    :param tout: Timeout for the process                   
    
    
    :return: True if the run was successful 
    """
    
    #Several checks to make sure Fastlim will run with the correct input
    if not os.path.isdir(fastlimdir):
        logger.error('Fastlim folder %s not found' %fastlimdir)
        return False
    if not os.path.isfile(os.path.join(fastlimdir,'fastlim.py')):
        logger.error("fastlim.py not found in %s" %fastlimdir)
        return False
    if not os.path.isabs(fastlimdir):
        logger.error("Please provide an absolute path for fastlim dir.")
        return False
    
    if not os.path.isfile(slhafile):
        logger.error("File: %s not found" %slhafile)
        return False
    elif not os.path.isabs(slhafile) or not os.path.isabs(outfile):
        logger.error("Please provide absolute paths for files")
        return False
    
    with Timeout(tout):
        infile = slhafile
        try:        
            proc = subprocess.Popen([os.path.join(fastlimdir,'fastlimMod.py'),infile,outfile],
                                    cwd = fastlimdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.wait()
        except NoTime:
            raise
        except:   
            raise FastlimError(infile)
     
        #Convert results to SModelS format (TheoryPredictionList)      
        predictions = fastlimParser(outfile,useBestDataset=False,
                                    expResID=expResID,txname=txname)
        
        #Format output to a python dictionary
        output = formatOutput(slhafile,predictions,extraInfo={'tool': 'fastlim'})         
        outfile = open(outfile,'w')
        outfile.write(str(output))
        outfile.close()
     
    return True

        

def runFastlimFor(slhadir,fastlimdir,expResID=None,txname=None,np=1,tout=None):
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
                                                          expResID,txname,tout))])

    #Close pool:                    
    pool.close()
    #Wait for results to end:
    pool.join()
    #Check if results were successful
    runstatus = {'successful' : [], 'failed' : []}
    for res in results:
        outfile, run = res
        outfile = outfile[outfile.rfind('/')+1:]
        if run.successful():
            runstatus['successful'].append(outfile)
        else:
            try: run.get()
            except Exception as e:
                runstatus['failed'].append([outfile,str(e)])

    #Return the status of each run:
    return runstatus