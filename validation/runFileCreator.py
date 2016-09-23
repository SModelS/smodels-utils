#!/usr/bin/env python

import sys,os,shutil
import logging,tempfile
# logging.basicConfig(filename='val.out')
import argparse
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
sys.path.append(os.path.join(home,'smodels-utils'))
from smodels.experiment.databaseObj import Database
from smodels.tools import xsecComputer, nllFast
from ConfigParser import SafeConfigParser
from plottingFuncs import getExclusionCurvesFor
import plotRanges
import slhaCreator
import commands

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)



def createFiles(expResList,txname,templateFile,tarFile,xargs):
    """
    Creates a .tar file for the txname using the data in expResults.
    
    :param expResults: a list of ExpResult objects
    :param txname: String describing the txname (e.g. T2tt)
    :param templateFile: path to the txname template
    :param tarFile: name of the output file
                    
    :return: True if successful, False otherwise. 
    """

    logger.info("Generating %s file" %tarFile)        

    #Create temp folder to store the SLHA files:
    tgraphs = {}
    txnameObjs = []

    #Get axes
    for expResult in expResList:
        txnameObj = [tx for tx in expResult.getTxNames() if tx.txName == txname]           
        if not txnameObj: #Skip result if it does not contain the txname
            continue
        txnameObj = txnameObj[0]
        txnameObjs.append(txnameObj) #Collect all txnames
        axes = txnameObj.getInfo("axes")
        if type(axes)==str:
            axes=[axes]
        for naxes in axes:
            tgraph = getExclusionCurvesFor(expResult,txname,naxes)
            if not tgraph:
                continue
            if not naxes in tgraphs:
                tgraphs[naxes]=[]
            tgraphs[naxes].append(tgraph[txname][0])

    if not tgraphs:
        logger.warning("No exclusion curves found for %s" %txname)
        return False
        
    #Get SLHA points and create files for each axes
    tempdir = tempfile.mkdtemp(dir=os.getcwd())
    for (axes,ntgraph) in tgraphs.items():
        pts = plotRanges.getPoints(ntgraph, txnameObjs, axes)
        logger.info("%i SLHA files for axes %s" %(len(pts),axes))
        if len(pts)==0:
            continue
        tempf = slhaCreator.TemplateFile(templateFile,axes,tempdir)
        tempf.createFilesFor(pts, massesInFileName=True)

    #Set up cross-section options: 
    xargs.query = False
    xargs.NLL = False
    xargs.NLO = False
    xargs.LOfromSLHA = False
    xargs.keep = False
    xargs.tofile = True
    xargs.pythiacard = tempf.pythiaCard
    xargs.filename = tempdir
    #Compute LO cross-sections
    xsecComputer.main(xargs)
    #Compute NLL cross-sections
    xargs.NLL = True
    xargs.LOfromSLHA = True
    xsecComputer.main(xargs)
    
    
    commands.getoutput("cd %s && tar cf %s *.slha" % (tempdir,tarFile))
    logger.info("-------- File %s created.\n" %tarFile)
    #Remove temp folder containing the SLHA files:
    shutil.rmtree(tempdir)

    
    return True


def main(analysisIDs,datasetIDs,txnames,dataTypes,templatedir,slhadir,databasePath,xargs,verbosity='info'):
    """
    Creates .tar files for all the txnames and analyses.

    :param analysisIDs: list of analysis ids ([CMS-SUS-13-006,...])
    :param dataType: dataType of the analysis (all, efficiencyMap or upperLimit)
    :param txnames: list of txnames ([TChiWZ,...])
    :param templatedir: Path to the folder containing the txname.template files
    :param slhadir: Path to the output folder holding the txname .tar files
    :param databasePath: Path to the SModelS database
    :param verbosity: overall verbosity (e.g. error, warning, info, debug)
    :param xargs: argparse.Namespace object holding the options for the cross-section calculation
    
    :return: A dictionary containing the list of created .tar files 
    """

    if not os.path.isdir(databasePath):
        logger.error('%s is not a folder' %databasePath)
    
    try:
        db = Database(databasePath,verbosity=verbosity)
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
        createFiles(expResList,txname,templateFile,tarFile,xargs)
        
    
    logger.info("\n\n----- Finished file creation.")


if __name__ == "__main__":
    
    ap = argparse.ArgumentParser(description="Produces SLHA files for the selected results and txnames")
    ap.add_argument('-p', '--parfile', 
            help='parameter file specifying the file creation options', default='./validation_parameters.ini')
    ap.add_argument('-l', '--log', 
            help='specifying the level of verbosity (error, warning,info, debug)', 
            default = 'info', type = str)
           
    args = ap.parse_args()
    
    numeric_level = getattr(logging,args.log.upper(), None)
    logger.setLevel(level=numeric_level)
    xsecComputer.logger.setLevel(level=numeric_level+10)
    nllFast.logger.setLevel(level=numeric_level+10)
    plotRanges.logger.setLevel(level=numeric_level+10)
    
                
    if not os.path.isfile(args.parfile):
        logger.error("Parameters file %s not found" %args.parfile)
    else:
        logger.info("Reading validation parameters from %s" %args.parfile)
        
        

    parser = SafeConfigParser()
    parser.read(args.parfile) 
    
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
        
    slhadir = os.path.abspath(parser.get("path", "slhaPath"))
    templatedir = os.path.abspath(parser.get("path", "templatePath"))
    databasePath = os.path.abspath(parser.get("path", "databasePath"))

    #Run creation:
    main(analyses,datasetIDs,txnames,dataTypes,templatedir,slhadir,databasePath,xargs,args.log)
    