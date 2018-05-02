#!/usr/bin/env python

from __future__ import print_function

import sys,os,shutil,time,tarfile
import logging,tempfile
# logging.basicConfig(filename='val.out')
import argparse
home = os.path.expanduser("~")
try:
    from ConfigParser import SafeConfigParser
except ImportError as e:
    from configparser import ConfigParser

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)



def createFiles(expResList,txnameStr,templateFile,tarFile,addToFile,xargs,Npts=300):
    """
    Creates a .tar.gz file for the txname using the data in expResults.
    
    :param expResults: a list of ExpResult objects
    :param txnameStr: String describing the txname (e.g. T2tt)
    :param templateFile: path to the txname template
    :param tarFile: name of the output file
    :param addToFile: If True it will add to the existing .tar.gz file (or create a new one if there is no previous file)    
    :param xargs: argparse.Namespace object holding the options for the 
                  cross-section calculation
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
            if not naxes in tgraphs:
                tgraphs[naxes]=[]            
            if tgraph:
                tgraphs[naxes].append(tgraph[txnameStr][0])

    ngraphs = sum([len(tg) for tg in tgraphs.values()])
    if ngraphs == 0:
        logger.info("No exclusion curves found for %s" %txnameStr)
       
    #Get SLHA points and create files for each axes
    tempdir = tempfile.mkdtemp(dir=os.getcwd())
    logger.debug("tempdir is %s" % tempdir )
    pythiaVersion = 6
    if xargs.pythia6 and not xargs.pythia8:
        pythiaVersion = 6
    elif not xargs.pythia6 and xargs.pythia8:
        pythiaVersion = 8
    for (axes,ntgraph) in tgraphs.items():
        pts = plotRanges.getPoints(ntgraph, txnameObjs, axes, Npts)
        logger.info("\033[31m %i SLHA files for axes %s \033[0m " %(len(pts),axes))
        if len(pts)==0:
            continue
        tempf = slhaCreator.TemplateFile(templateFile,axes,tempdir,pythiaVersion=pythiaVersion)
        tempf.createFilesFor(pts, massesInFileName=True)

    #Set up cross-section options:
    xargs.colors = None
    xargs.alltofile = False
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
    
    
    #Create tarfile:
    if os.path.isfile(tarFile):
        if addToFile:
            #Extract old slhafiles to the same folder:
            oldtar = tarfile.open(tarFile,'r:gz')
            oldtar.extractall(path=tempdir)
            oldtar.close()
        os.remove(tarFile)
        
    tar = tarfile.open(tarFile,'w:gz')
    for slhafile in os.listdir(tempdir):
        tar.add(os.path.join(tempdir,slhafile),arcname=slhafile)
    tar.close()
    #Remove temp folder containing the SLHA files:
    shutil.rmtree(tempdir)
    
    return True


def main(analysisIDs,datasetIDs,txnames,dataTypes,templatedir,slhadir,
         databasePath,xargs,Npts=300,addToFile=False,verbosity='error'):
    """
    Creates .tar.gz files for all the txnames and analyses.

    :param analysisIDs: list of analysis ids ([CMS-SUS-13-006,...])
    :param dataType: dataType of the analysis (all, efficiencyMap or upperLimit)
    :param txnames: list of txnames ([TChiWZ,...])
    :param templatedir: Path to the folder containing the txname.template files
    :param slhadir: Path to the output folder holding the txname .tar.gz files
    :param databasePath: Path to the SModelS database
    :param Npts: Trial number of points for each plane.
    :param addToFile: If True it will add to the existing .tar.gz file (or create a new one if there is no previous file)
    :param verbosity: overall verbosity (e.g. error, warning, info, debug)
    :param xargs: argparse.Namespace object holding the options for the 
                  cross-section calculation
    
    :return: A dictionary containing the list of created .tar.gz files 
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
    
    #Loop over txnames and create tar.gz files
    for txname in txnameList:
        templateFile = os.path.join(templatedir,txname+'.template')
        tarFile = os.path.join(slhadir,txname+'.tar.gz')
        if addToFile and os.path.isfile(tarFile):
            logger.info("--------  \033[32m Extending %s \033[0m" %tarFile)
        else:
            logger.info("--------  \033[32m Generating %s \033[0m" %tarFile)            
        t0 = time.time()
        createFiles(expResList,txname,templateFile,tarFile,addToFile,xargs,Npts)
        if addToFile and os.path.isfile(tarFile):                
            logger.info("--------  \033[32m File %s extended in %.1f min. \033[0m \n" %(tarFile,(time.time()-t0)/60.))
        else:
            logger.info("--------  \033[32m File %s generated in %.1f min. \033[0m \n" %(tarFile,(time.time()-t0)/60.))            
    
    logger.info("\n\n----- Finished file creation.")


if __name__ == "__main__":
    
    ap = argparse.ArgumentParser(description="Produces SLHA files for the selected results and txnames")
    ap.add_argument('-p', '--parfile', 
            help='parameter file specifying the file creation options', 
            default='./validation_parameters.ini')
    ap.add_argument('-v', '--verbose', 
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
    
    

    numeric_level = getattr(logging,args.verbose.upper(), None)
    logger.setLevel(level=numeric_level)
    plotRanges.logger.setLevel(level=numeric_level)
    from smodels.tools import smodelsLogging, xsecComputer
    smodelsLogging.setLogLevel( args.verbose )
    
    #Options for cross-section calculation:
    xargs = argparse.Namespace()
    #Set pythia6 as default:
    xargs.pythia6 = True
    xargs.pythia8 = False
    for name,value in parser.items("xsec"):
        setattr(xargs, name, value)
        #If pythiaVersion has been defined, use it to select pythia version
        if name.lower() == 'pythiaversion':
            if eval(value) == 8:
                xargs.pythia6 = False
                xargs.pythia8 = True
            elif eval(value) != 6:
                logger.warning("pythiaVersion should be set to 6 or 8. Using default value 6")
                 
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
         databasePath,xargs,Npts,addToFile,verbosity=args.verbose)
    
