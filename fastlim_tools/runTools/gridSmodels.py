#!/usr/bin/env python

"""
.. module:: gridSmodels
   :synopsis: Defines the functionalities required to run smodels on
   a grid of SLHA files

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import os,sys,logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

home = os.path.expanduser("~")
databaseDir = os.path.join(home,'smodels-database')
sys.path.append(os.path.join(home,'smodels'))
from smodels.base.physicsUnits import fb, GeV, TeV
from smodels.theory import slhaDecomposer, theoryPrediction
import multiprocessing
from smodels.tools import databaseBrowser
import subprocess
from auxiliaryObjs import Timeout, SModelSError, getSlhaFiles, formatOutput, prepareSLHA, NoTime

logger.setLevel(level=logging.DEBUG)


def runSmodelS(slhafile,outfile,database,expResID=None,txname=None,
               doXsecs=True,tout=None):
    """
    Runs smodels for the SLHA file and generate the corresponding .sms file.
    
    :param slhafile: Path to the SLHA file
    :param outfile: Path to the outputfile
    :param database: Database object
    :param txname: Used to only use efficiencies for a specific Txname 
                   (i.e. T2tt,T5bbbb,...). If None will return the total prediction.
    :param expResID: Used to select results for a experimental result (i.e. ATLAS-CONF-xxx)
                   If None will return predictions for all IDs.
    :param doXsecs: If True will erase the original cross-sections and compute new ones
    :param tout: Timeout for the process
    
    
    :return: True/False if the run was/was not successful 
    """
    
    
    #Several checks to make sure SModelS will run with the correct input    
    if not os.path.isfile(slhafile):
        logger.error(f"File: {slhafile} not found")
        return False
    elif not os.path.isabs(slhafile) or not os.path.isabs(outfile):
        logger.error("Please provide absolute paths for files")
        return False
    
    with Timeout(tout):        
        #Recompute xsecs
        if doXsecs:
            prepareSLHA(slhafile,slhafile)
            subprocess.call([os.path.join(home,'smodels','runTools.py'), 
                                    'xseccomputer', '-s 8', '-e 10000', '-p', f"-f {slhafile}"],)
            subprocess.call([os.path.join(home,'smodels','runTools.py'), 
                                    'xseccomputer', '-s 8', '-N', '-O', '-e 10000', '-p', f"-f {slhafile}"],)
    
    
        sigmacut = 0.0000001 * fb
        mingap = 10. * GeV
            
        if expResID:
            database.expResultList = database.getExpResults(analysisIDs=[expResID])
        if txname:
            database.expResultList = database.getExpResults(txnames=[txname])
        
        try:
            smstoplist = slhaDecomposer.decompose(slhafile, sigmacut,\
                            doCompress=True,doInvisible=False, minmassgap=mingap)
            predictions = theoryPrediction.TheoryPredictionList()
            for expRes in database.expResultList:
                preds =  theoryPrediction.theoryPredictionsFor(expRes, smstoplist, 
                                                               useBestDataset=False)
                if preds:
                    predictions += preds
        except NoTime:
            raise                    
        except:    
            raise SModelSError(slhafile)
     
        #Format output to a python dictionary
        extraInfo={'tool': 'smodels','sigmacut' : sigmacut.asNumber(fb), 'mingap' : mingap.asNumber(GeV)}
        output = formatOutput(slhafile,predictions,extraInfo)        
        outfile = open(outfile,'w')
        outfile.write(str(output))
        outfile.close()
     
    return True


def runSmodelSFor(slhadir,databasePath,expResID=None,txname=None,np=1,tout=None):
    """
    Runs fastlim for the SLHA files in slhaFiles. Uses only the best
    dataset for each experimental result.
    
    :param slhadir: Path to the folder with the SLHA files or the tar ball containing the files (string)
    :param databasePath: Path to the database folder
    :param txname: Used to only use efficiencies for a specific Txname 
                   (i.e. T2tt,T5bbbb,...). If None will return the total prediction.
    :param expResID: Used to select results for a experimental result (i.e. ATLAS-CONF-xxx)
                   If None will return predictions for all IDs.  
    :param np: Number of parallel processes. If np=1, run as serial. Otherwise uses multiprocessing
    :param tout: Timeout for each process                

    :return: List of sms files generated
    """    
    
    #Load a single database for all processes:    
    if os.path.isdir(databasePath):
        browser = databaseBrowser.Browser(databasePath)
        browser.selectExpResultsWith(contact = ['fastlim'])
        database = browser.database
        database.expResultList = browser._selectedExpResults            
    else:
        logger.error(f'Database folder {databasePath} not found')
        return False

    #Get SLHA files
    slhaFiles,slhaD = getSlhaFiles(slhadir)
    
    #Set up multiprocessing:
    pool = multiprocessing.Pool(processes=np)
    
    #Loop over SLHA files and compute results:    
    results = []
    for slhafile in slhaFiles:        
        outputfile = slhafile.replace(".slha",".sms")
        sfile = open(slhafile,'r')
        sdata = sfile.read()
        sfile.close()
        #Check if file has cross-sections in the new format. If not, re-compute them
        if "xsec unit: pb" in sdata:
            doXsecs = False
        else:
            doXsecs = True
        #Run Fastlim (submit threads):
        results.append([outputfile,
                        pool.apply_async(runSmodelS,args=(slhafile,outputfile,database,
                                                          expResID,txname,doXsecs,tout))])
        
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



