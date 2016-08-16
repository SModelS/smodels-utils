#!/usr/bin/env python

import sys,os
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
sys.path.append(os.path.join(home,'smodels-utils'))
from validation import plottingFuncs, validationObjs
from smodels.experiment.databaseObj import Database
import logging
import argparse
from ConfigParser import SafeConfigParser

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


def validatePlot(expRes,txname,axes,slhadir,kfactor=1.):
    """
    Creates a validation plot and saves its output.
    
    :param expRes: a ExpResult object containing the result to be validated
    :param txname: String describing the txname (e.g. T2tt)
    :param axes: the axes string describing the plane to be validated
     (i.e.  2*Eq(mother,x),Eq(lsp,y))
    :param slhadir: folder containing the SLHA files corresponding to txname
    or the .tar file containing the SLHA files.
    :param kfactor: optional global k-factor value to re-scale 
                    all theory prediction values
                    
    :return: agreement factor
    """

    logger.info("Generating validation plot for " + expRes.getValuesFor('id')[0]
                +", "+txname+", "+axes)        
    valPlot = validationObjs.ValidationPlot(expRes,txname,axes,kfactor=kfactor)
    valPlot.setSLHAdir(slhadir)
    valPlot.getData()
    valPlot.getPlot()
    valPlot.savePlot()
    valPlot.saveData()
    logger.info("Validation plot done.")
    
    return valPlot.computeAgreementFactor() # return agreement factor


def main(analysisIDs,datasetIDs,txnames,dataTypes,kfactorDict,slhadir,databasePath):
    """
    Generates validation plots for all the analyses containing the Txname.

    :param analysisIDs: list of analysis ids ([CMS-SUS-13-006,...])
    :param dataType: dataType of the analysis (all, efficiencyMap or upperLimit)
    :param txnames: list of txnames ([TChiWZ,...])
    :param slhadir: Path to the folder containing the txname .tar files
    :param databasePath: Path to the SModelS database
    :param kfactorDict: kfactor dictionary to be applied to the theory cross-sections (e.g. {'TChiWZ' : 1.2, 'T2' : 1.,..})
    
    :return: A dictionary containing the agreement factors 
    """

    if not os.path.isdir(databasePath):
        logger.error('%s is not a folder' %databasePath)
    
    try:
        db = Database(databasePath)
    except:
        logger.error("Error loading database at %s" %databasePath)
        
    
    logger.info('-----Running validation...')
    
    #Select experimental results, txnames and datatypes:
    expResList = db.getExpResults( analysisIDs, datasetIDs, txnames,
                  dataTypes, useSuperseded=True, useNonValidated=True)
    
    #Loop over experimental results and validate plots
    for expRes in expResList:
        logger.info("---------Validating  %s" %expRes.globalInfo.id)
        #Loop over pre-selected txnames:
        for tx in expRes.getTxNames():
            txname = tx.txName
            logger.info("------------Validating  %s" %txname)
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
                continue
            else:
                tgraphs = tgraphs[txname] 
            #Loop over plots:
            for tgraph in tgraphs:
                ax = tgraph.GetName().replace('exclusion_',"")
                agreement = validatePlot(expRes,txname,ax,tarfile,kfactor)
                break
        
    logger.info("\n\n-----Finished validation.")


if __name__ == "__main__":
    
    ap = argparse.ArgumentParser(description="Produces validation plots and data for the selected results")
    ap.add_argument('-p', '--parfile', 
            help='parameter file specifying the validation options', default='./validation_parameters.ini')
        
    args = ap.parse_args()
    
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
        
    kfactorDict = dict(parser.items("kfactors"))
    slhadir = parser.get("path", "slhaPath")
    databasePath = parser.get("path", "databasePath")

    #Run validation:
    main(analyses,datasetIDs,txnames,dataTypes,kfactorDict,slhadir,databasePath)
    
    