#!/usr/bin/env python

import sys,os
import logging
# logging.basicConfig(filename='val.out')
import argparse
from EM_Creator.EM_Baking import TxName
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
sys.path.append(os.path.join(home,'smodels-utils'))
from validation import plottingFuncs, validationObjs
from smodels.experiment.databaseObj import Database
from ConfigParser import SafeConfigParser
from plottingFuncs import getExclusionCurvesFor
import tempfile
import plotRanges
import slhaCreator

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)



def createFiles(expResList,txname,templateFile,tarFile):
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
    tempdir = tempfile.mkdtemp(dir=os.getcwd())
    slhafiles = []
    tgraphs = {}
    txnameObjs = []

    #Get axes
    for expResult in expResList:
        txnameObj = [tx for tx in expResult.getTxNames() if tx.txName == txname]
        if len(txnameObj) != 1:
            logger.error("%i objects found matching the txname %s" %(len(txnameObj),txname))
            return False
        txnameObj = txnameObj[0]
        axes=txnameObj.getInfo("axes")
        if type(axes)==str:
            axes=[axes]
        for naxes in axes:
            tgraph = getExclusionCurvesFor(expResult,txname,naxes)
            if not tgraph:
                continue
            if not naxes in tgraphs:
                tgraphs[naxes]=[]
            tgraphs[naxes].append(tgraph[txname][0])

    #Get SLHA points
    for (axes,ntgraph) in tgraphs.items():
        pts = plotRanges.getPoints(ntgraph, txnameObjs, axes, onshell_constraint, onshell, offshell )
        print "len(pts)=",len(pts)
        # flatpts = plotRanges.mergeListsOfListsOfPoints ( pts )
        if len(pts)==0:
            continue
        tempf=slhaCreator.TemplateFile ( templatefile,axes )
        slhafiles += tempf.createFilesFor ( pts, massesInFileName=True )


    import commands
    cmds=commands.getoutput ( "tar cvf %s.tar %s_*.slha" % ( txname, txname ) )
    print cmds
    #Remove SLHA files
    for f in slhafiles: 
        if os.path.exists ( f ): os.remove(f)


    
    return 


def main(analysisIDs,datasetIDs,txnames,dataTypes,templatedir,slhadir,databasePath,verbosity='info'):
    """
    Creates .tar files for all the txnames and analyses.

    :param analysisIDs: list of analysis ids ([CMS-SUS-13-006,...])
    :param dataType: dataType of the analysis (all, efficiencyMap or upperLimit)
    :param txnames: list of txnames ([TChiWZ,...])
    :param templatedir: Path to the folder containing the txname.template files
    :param slhadir: Path to the output folder holding the txname .tar files
    :param databasePath: Path to the SModelS database
    :param verbosity: overall verbosity (e.g. error, warning, info, debug) 
    
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
    
    #Get list of txnames:
    txnameList = []
    for expRes in expResList:
        for tx in expRes.getTxNames():
            if not tx.txName in txnameList:
                txnameList.append(tx.txName)
    txnameList = sorted(txnameList)        
    #Loop over experimental results and validate plots
    for txname in txnameList:
        templateFile = os.path.join(templatedir,txname+'.txt')
        tarFile = os.path.join(slhadir,txname+'.tar')
        createFiles(expResList,txname,templateFile,tarFile)
        
        
    for expRes in expResList:
        logger.info("--------- validating  %s" %expRes.globalInfo.id)
        #Loop over pre-selected txnames:
        txnames = set([tx.txName for tx in expRes.getTxNames()])
        for txname in txnames:
            logger.info("------------ validating  %s" %txname)
            tarfile = os.path.join(slhadir,txname+".tar")                
            if not os.path.isfile(tarfile):
                logger.error('Missing .tar file for %s' %txname)
                continue
            if txname.lower() in kfactorDict:
                kfactor = float(kfactorDict[txname.lower()])
            else:
                kfactor = 1.

            tgraphs = plottingFuncs.getExclusionCurvesFor(expRes,txname,get_all=False)
            if not tgraphs or not tgraphs[txname]:
                logger.info("No exclusion curves found for %s" %txname)
                continue
            else:
                tgraphs = tgraphs[txname] 
            #Loop over plots:
            for tgraph in tgraphs:                
                ax = tgraph.GetName().replace('exclusion_',"")
                agreement = validatePlot(expRes,txname,ax,tarfile,kfactor)
                logger.info('               agreement factor = %s' %str(agreement))
        
    logger.info("\n\n----- Finished validation.")


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
    plottingFuncs.logger.setLevel(level=numeric_level)
    validationObjs.logger.setLevel(level=numeric_level)
    
                
    if not os.path.isfile(args.parfile):
        logger.error("Parameters file %s not found" %args.parfile)
    else:
        logger.info("Reading validation parameters from %s" %args.parfile)
        
        

    parser = SafeConfigParser()
    parser.read(args.parfile)        

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
        
    slhadir = parser.get("path", "slhaPath")
    templatedir = parser.get("path", "templatePath")
    databasePath = parser.get("path", "databasePath")

    #Run validation:
    main(analyses,datasetIDs,txnames,dataTypes,templatedir,slhadir,databasePath,args.log)
    