#!/usr/bin/env python

from __future__ import print_function

import sys,os,shutil,time
import logging,tempfile
# logging.basicConfig(filename='val.out')
import argparse
home = os.path.expanduser("~")
try:
    from ConfigParser import SafeConfigParser
except ImportError as e:
    from configparser import ConfigParser
try:
    import commands
except ImportError as e:
    import subprocess as commands

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)



def createFiles(expResList,txnameStr,templateFile,tarFile,xargs,Npts=300):
    """
    Creates a .tar file for the txname using the data in expResults.
    
    :param expResults: a list of ExpResult objects
    :param txnameStr: String describing the txname (e.g. T2tt)
    :param templateFile: path to the txname template
    :param tarFile: name of the output file
    :param xargs: argparse.Namespace object holding the options for the cross-section calculation
    :param Npts: Trial number of points for each plane.
                    
    :return: True if successful, False otherwise. 
    """

    
    #Create temp folder to store the SLHA files:
    tgraphs = {}
    txnameObjs = []

    #Get axes
    for expResult in expResList:
        txnameObj = [tx for tx in expResult.getTxNames() 
                     if (tx.txName == txnameStr and not 'assigned' in tx.constraint)]           
        if not txnameObj: #Skip result if it does not contain the txname
            continue        
        axes = []
        for tx in txnameObj:
            taxes = tx.axes
            if type(taxes) == str:
                taxes = [taxes]
            for ax in taxes:
                if not ax in axes:
                    axes.append(ax)        
        txnameObjs += txnameObj #Collect all txnames        
        for naxes in axes:
            tgraph = getExclusionCurvesFor(expResult,txnameStr,naxes)
            if not tgraph:
                continue
            if not naxes in tgraphs:
                tgraphs[naxes]=[]
            tgraphs[naxes].append(tgraph[txnameStr][0])

    if not tgraphs:
        logger.warning("No exclusion curves found for %s" %txnameStr)
        return False

       
    #Get SLHA points and create files for each axes
    tempdir = tempfile.mkdtemp(dir=os.getcwd())
    for (axes,ntgraph) in tgraphs.items():
        pts = plotRanges.getPoints(ntgraph, txnameObjs, axes, Npts)
        logger.info("\033[31m %i SLHA files for axes %s \033[0m " %(len(pts),axes))
        if len(pts)==0:
            continue
        tempf = slhaCreator.TemplateFile(templateFile,axes,tempdir)
        tempf.createFilesFor(pts, massesInFileName=True)

    #Set up cross-section options:
    xargs.colors = None
    xargs.alltofile = False 
    xargs.pythia6 = True
    xargs.query = False
    xargs.NLL = False
    xargs.NLO = False
    xargs.LOfromSLHA = False
    xargs.keep = False
    xargs.tofile = True
    xargs.pythiacard = tempf.pythiaCard
    xargs.filename = tempdir
    xargs.verbosity = 30
    #Compute LO cross-sections
    xsecComputer.main(xargs)
    #Compute NLL cross-sections
    xargs.NLL = True
    xargs.LOfromSLHA = True    
    xsecComputer.main(xargs)
    
    
    commands.getoutput("cd %s && tar cf %s *.slha" % (tempdir,tarFile))
    #Remove temp folder containing the SLHA files:
    shutil.rmtree(tempdir)

    
    return True


def main(analysisIDs,datasetIDs,txnames,dataTypes,templatedir,slhadir,
         databasePath,xargs,Npts=300,addToFile=False,verbosity='error'):
    """
    Creates .tar files for all the txnames and analyses.

    :param analysisIDs: list of analysis ids ([CMS-SUS-13-006,...])
    :param dataType: dataType of the analysis (all, efficiencyMap or upperLimit)
    :param txnames: list of txnames ([TChiWZ,...])
    :param templatedir: Path to the folder containing the txname.template files
    :param slhadir: Path to the output folder holding the txname .tar files
    :param databasePath: Path to the SModelS database
    :param Npts: Trial number of points for each plane.
    :param addToFile: If True it will add to the existing .tar file (or create a new one if there is no previous file)
    :param verbosity: overall verbosity (e.g. error, warning, info, debug)
    :param xargs: argparse.Namespace object holding the options for the cross-section calculation
    
    :return: A dictionary containing the list of created .tar files 
    """

    if not os.path.isdir(databasePath):
        logger.error('%s is not a folder' %databasePath)
    
    try:
        db = Database(databasePath)
    except:
        logger.error("Error loading database at %s" %databasePath)
        
    
    logger.info('----- Running creation...')
    
    #Select experimental results, txnames and datatypes:
    expResList = db.getExpResults(analysisIDs, datasetIDs, txnames,
                  dataTypes, useSuperseded=True, useNonValidated=True)
    
    if not expResList:
        logger.error("No experimental results found.")
    
    #Get list of txnames:
    txnameList = []
    for expRes in expResList:
        for tx in expRes.getTxNames():
            if not tx.txName in txnameList:
                txnameList.append(tx.txName)
    txnameList = sorted(txnameList)        
    if not txnameList:
        logger.error("No txnames found.")
    
    #Loop over txnames and create tar files
    for txname in txnameList:
        templateFile = os.path.join(templatedir,txname+'.template')
        tarFile = os.path.join(slhadir,txname+'.tar')
        oldTarFile = None
        if addToFile and os.path.isfile(tarFile):
            oldTarFile = tempfile.mkstemp(suffix='_old.tar', dir=slhadir)
            os.close(oldTarFile[0])
            oldTarFile = oldTarFile[1]
            os.rename(tarFile,oldTarFile)
            logger.info("--------  \033[32m Extending %s \033[0m" %tarFile)
        else:
            logger.info("--------  \033[32m Generating %s \033[0m" %tarFile)            
        t0 = time.time()
        createFiles(expResList,txname,templateFile,tarFile,xargs,Npts)        
        if oldTarFile:
            tempdir = tempfile.mkdtemp(dir='./')
            commands.getoutput("tar -xf %s -C %s" % (tarFile,tempdir))
            commands.getoutput("tar -xf %s -C %s" % (oldTarFile,tempdir))
            os.remove(oldTarFile)
            os.remove(tarFile)
            commands.getoutput("cd %s && tar -cf %s *.slha" % (tempdir,tarFile))
            shutil.rmtree(tempdir)
            logger.info("--------  \033[32m File %s extended in %.1f min. \033[0m \n" %(tarFile,(time.time()-t0)/60.))
        else:
            logger.info("--------  \033[32m File %s generated in %.1f min. \033[0m \n" %(tarFile,(time.time()-t0)/60.))            
    
    logger.info("\n\n----- Finished file creation.")


if __name__ == "__main__":
    
    ap = argparse.ArgumentParser(description="Produces SLHA files for the selected results and txnames")
    ap.add_argument('-p', '--parfile', 
            help='parameter file specifying the file creation options', default='./validation_parameters.ini')
    ap.add_argument('-l', '--log', 
            help='specifying the level of verbosity (error, warning,info, debug)', 
            default = 'info', type = str)
           
    args = ap.parse_args()
    
    if not os.path.isfile(args.parfile):
        logger.error("Parameters file %s not found" %args.parfile)
    else:
        logger.info("Reading validation parameters from %s" %args.parfile)

    try:
        parser = ConfigParser( inline_comment_prefixes=( ';', ) )
    except Exception as e:
        parser = SafeConfigParser()
    parser.read(args.parfile) 
    
    #Add smodels and smodels-utils to path
    smodelsPath = parser.get("path", "smodelsPath")
    utilsPath = parser.get("path", "utilsPath")    
    smodelsPath = smodelsPath.replace ( "$HOME", os.environ["HOME"] )
    utilsPath = utilsPath.replace ( "$HOME", os.environ["HOME"] )
    sys.path.append(smodelsPath)
    sys.path.append(utilsPath)
    from smodels.experiment.databaseObj import Database
    from plottingFuncs import getExclusionCurvesFor
    import plotRanges
    import slhaCreator
    
    

    numeric_level = getattr(logging,args.log.upper(), None)
    logger.setLevel(level=numeric_level)
    plotRanges.logger.setLevel(level=numeric_level)
    from smodels.tools import smodelsLogging, xsecComputer
    smodelsLogging.setLogLevel("error")
    
    
    #Options for cross-section calculation:
    xargs = argparse.Namespace()
    for name,value in parser.items("xsec"):
        setattr(xargs, name, value)
    xargs.sqrts = [[eval(sqrts) for sqrts in xargs.sqrts.split(',')]]
    xargs.ncpus = int(xargs.ncpus)
    xargs.nevents = int(xargs.nevents)    
        
    
    analyses = parser.get("database", "analyses").split(",")
    txnames = parser.get("database", "txnames").split(",")
    if parser.get("database", "dataselector") == "efficiencyMap":
        dataTypes = ['efficiencyMap']
        datasetIDs = ['all']
    elif parser.get("database", "dataselector") == "upperLimit":
        dataTypes = ['upperLimit']
        datasetIDs = ['all']
    else:
        dataTypes = ['all']
        datasetIDs = parser.get("database", "dataselector").split(",")
    

    if parser.get("extra","npts"):
        Npts = int(parser.get("extra","npts"))
    else:
        Npts = 300
    if parser.get("extra","addToFile"):
        addToFile = parser.getboolean("extra","addToFile")
    else:
        addToFile = False        
        
    slhadir = os.path.abspath(parser.get("path", "slhaPath"))
    templatedir = os.path.abspath(parser.get("path", "templatePath"))
    databasePath = os.path.abspath(parser.get("path", "databasePath"))

    #Run creation:
    main(analyses,datasetIDs,txnames,dataTypes,templatedir,slhadir,
         databasePath,xargs,Npts,addToFile)
    
