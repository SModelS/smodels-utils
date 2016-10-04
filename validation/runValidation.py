#!/usr/bin/env python

import sys,os
import logging
# logging.basicConfig(filename='val.out')
import argparse,time
from ConfigParser import SafeConfigParser

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)



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
    if not valPlot.data:
        return None
    valPlot.getPlot()
    valPlot.savePlot()
    valPlot.saveData()
    
    return valPlot.computeAgreementFactor() # return agreement factor


def main(analysisIDs,datasetIDs,txnames,dataTypes,kfactorDict,slhadir,databasePath,verbosity='info'):
    """
    Generates validation plots for all the analyses containing the Txname.

    :param analysisIDs: list of analysis ids ([CMS-SUS-13-006,...])
    :param dataType: dataType of the analysis (all, efficiencyMap or upperLimit)
    :param txnames: list of txnames ([TChiWZ,...])
    :param slhadir: Path to the folder containing the txname .tar files
    :param databasePath: Path to the SModelS database
    :param kfactorDict: kfactor dictionary to be applied to the theory cross-sections (e.g. {'TChiWZ' : 1.2, 'T2' : 1.,..})
    :param verbosity: overall verbosity (e.g. error, warning, info, debug) 
    
    :return: A dictionary containing the agreement factors 
    """
    
    

    if not os.path.isdir(databasePath):
        logger.error('%s is not a folder' %databasePath)
    
    try:
        db = Database(databasePath,verbosity=verbosity)
    except:
        logger.error("Error loading database at %s" %databasePath)
        
    
    logger.info('----- Running validation...')
    
    #Select experimental results, txnames and datatypes:
    expResList = db.getExpResults( analysisIDs, datasetIDs, txnames,
                  dataTypes, useSuperseded=True, useNonValidated=True)
    
    if not expResList:
        logger.error("No experimental results found.")    
    
    tval0 = time.time()
    #Loop over experimental results and validate plots
    for expRes in expResList:
        expt0 = time.time()
        logger.info("--------- \033[32m validating  %s \033[0m" %expRes.globalInfo.id)
        #Loop over pre-selected txnames:
        txnames = set([tx for tx in expRes.getTxNames() if not 'assigned' in tx.constraint])
        if not txnames:
            logger.warning("No valid txnames found for %s (not assigned constraints?)" %str(expRes))
            continue
        for txname in txnames:
            txnameStr = txname.txName
            txt0 = time.time()
            logger.info("------------ \033[31m validating  %s \033[0m" %txnameStr)
            tarfile = os.path.join(slhadir,txnameStr+".tar")                
            if not os.path.isfile(tarfile):
                logger.error('Missing .tar file for %s' %txnameStr)
                continue
            if txnameStr.lower() in kfactorDict:
                kfactor = float(kfactorDict[txnameStr.lower()])
            else:
                kfactor = 1.

            tgraphs = plottingFuncs.getExclusionCurvesFor(expRes,txnameStr,get_all=False)
            if not tgraphs or not tgraphs[txnameStr]:
                logger.info("No exclusion curves found for %s" %txnameStr)
                continue
            else:
                tgraphs = tgraphs[txnameStr] 
            #Loop over plots:
            for tgraph in tgraphs:                
                ax = tgraph.GetName().replace('exclusion_',"")
                if not ax in txname.axes: continue
                agreement = validatePlot(expRes,txnameStr,ax,tarfile,kfactor)
                logger.info('               agreement factor = %s' %str(agreement))
            logger.info("------------ \033[31m %s validated in  %.1f min \033[0m" %(txnameStr,(time.time()-txt0)/60.))
        logger.info("--------- \033[32m %s validated in %.1f min \033[0m" %(expRes.globalInfo.id,(time.time()-expt0)/60.))
    logger.info("\n\n----- Finished validation in %.1f min." %((time.time()-tval0)/60.))


if __name__ == "__main__":
    
    ap = argparse.ArgumentParser(description="Produces validation plots and data for the selected results")
    ap.add_argument('-p', '--parfile', 
            help='parameter file specifying the validation options', default='./validation_parameters.ini')
    ap.add_argument('-l', '--log', 
            help='specifying the level of verbosity (error, warning,info, debug)', 
            default = 'info', type = str)
           
    args = ap.parse_args()
                
    if not os.path.isfile(args.parfile):
        logger.error("Parameters file %s not found" %args.parfile)
    else:
        logger.info("Reading validation parameters from %s" %args.parfile)

    parser = SafeConfigParser()
    parser.read(args.parfile)
    
    #Add smodels and smodels-utils to path
    smodelsPath = parser.get("path", "smodelsPath")
    utilsPath = parser.get("path", "utilsPath")    
    sys.path.append(smodelsPath)
    sys.path.append(utilsPath)
    from validation import plottingFuncs, validationObjs
    from smodels.experiment.databaseObj import Database

    #Control output level:
    numeric_level = getattr(logging,args.log.upper(), None)
    logger.setLevel(level=numeric_level)
    plottingFuncs.logger.setLevel(level=numeric_level)
    validationObjs.logger.setLevel(level=numeric_level)
    
    #Seleceted plots for validation:
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
    main(analyses,datasetIDs,txnames,dataTypes,kfactorDict,slhadir,databasePath,args.log)
    
