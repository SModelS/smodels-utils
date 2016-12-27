#!/usr/bin/env python

import logging,sys,os
# logging.basicConfig(filename='val.out')
import subprocess
import glob
import argparse
import signal
from ConfigParser import SafeConfigParser
import time


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)


def checkPlotsFor(txname,update):
    """
    Checks a list of validation plots for the txname and returns the validation result
    set by the user.
    If update is True, it will rewrite the validated field in txname.txt.
    
    :param txname: Txname object corresponding to the    
    :param update: option to update (rewrite) the txname.txt files (True/False)
    
    :return: Validation result (True/False/None or skip)
    """


    axes = txname.axes
    if isinstance(axes,str):
        axes = [axes]
    #Collect validation plots:
    valPlots = []
    missingPlots = []
    for ax in axes:
        ax = ax.replace("*","").replace(",","").replace("(","").replace(")","")
        plotfile = txname.txName+"_"+ax+".pdf"
        valplot = os.path.join(txname.path,'../../validation/'+plotfile)
        valplot = os.path.abspath(valplot)
        if not os.path.isfile(valplot):
            missingPlots.append(valplot)
        else:
            valPlots.append(valplot)

    if not valPlots:
        logger.error('\033[36m       No plots found \033[0m')
        return 'skip'
    else:
        for plot in missingPlots:
            logger.error('\033[36m        plot %s not found \033[0m' %valplot)

    #Check the plots
    plots = []    
    for fig in valPlots:
        try:
            plots.append(subprocess.Popen('evince --preview '+fig,shell=True, preexec_fn=os.setsid, 
                                          stdout=subprocess.PIPE))
        except:
            plots.append(subprocess.Popen(['open',fig]))    
    cfile = os.path.join(os.path.dirname(txname.path),"../validation/"+txname.txName+".comment")
    if os.path.isfile(cfile):
        logger.info('\033[96m  == Txname Comment file found: == \033[0m')        
        cf = open(cfile,'r')
        print "\033[96m"+cf.read()+"\033[0m"
        cf.close()


    val = ""
    while not val.lower() in ['t','f','n','s','exit']:
        val = raw_input("TxName is validated? (Current validation status: %s) \
        \n True/False/None/Skip (t/f/n/s) \n (or type exit to stop)\n" %txname.validated)    
        if val.lower() == 't': validationResult = True
        elif val.lower() == 'f': validationResult = False
        elif val.lower() == 'n': validationResult = None
        elif val.lower() == 's': validationResult = 'skip'
        elif val.lower() == 'exit':
            for plot in plots:
                os.killpg(os.getpgid(plot.pid), signal.SIGTERM)            
            sys.exit()
        else:
            print 'Unknow option. Try again.'
    for plot in plots:
            os.killpg(os.getpgid(plot.pid), signal.SIGTERM)

    return validationResult


    
    

def main(analysisIDs,datasetIDs,txnames,dataTypes,databasePath,check,showPlots,update,printSummary,verbosity='info'):
    """
    Checks validation plots for all the analyses selected.

    :param analysisIDs: list of analysis ids ([CMS-SUS-13-006,...])
    :param dataType: dataType of the analysis (all, efficiencyMap or upperLimit)
    :param txnames: list of txnames ([TChiWZ,...])
    :param databasePath: Path to the SModelS database
    :param check: list containing which type of plots to check ([False,None,..])
    :param showPlots: option to open the plots or not (True/False)
    :param update: option to update (rewrite) the txname.txt files (True/False)
    :param printSummary: option to re-load the database and print the number of
                        validated True/False/None txnames        
    :param verbosity: overall verbosity (e.g. error, warning, info, debug) 
    
    :return: True if all selected plots were checked, False otherwise 
    """
    
    if not os.path.isdir(databasePath):
        logger.error('%s is not a folder' %databasePath)
    
    try:
        db = Database(databasePath,verbosity=verbosity)
    except:
        logger.error("Error loading database at %s" %databasePath)
        
    
    logger.info('----- Checking plots...')
    
    #Select experimental results, txnames and datatypes:
    expResList = db.getExpResults( analysisIDs, datasetIDs, txnames,
                  dataTypes, useSuperseded=True, useNonValidated=True)
    
    if not expResList:
        logger.error("No experimental results found.")    
    
    tval0 = time.time()
    expResList = sorted(expResList, key=lambda exp: exp.globalInfo.id)
    #Loop over experimental results and validate plots
    for expRes in expResList:
        
#         if (not hasattr(expRes.globalInfo,'contact')) or (not 'fastlim' in expRes.globalInfo.contact):
#             continue
        
        expt0 = time.time()
        logger.info("--------- \033[32m Checking  %s \033[0m" %expRes.globalInfo.id)
        #Select only one dataset (for EM results avoid duplicated txnames)
        dataset = expRes.datasets[0]
        #Loop over pre-selected txnames:
        txnameList = [tx for tx in dataset.txnameList if not 'assigned' in tx.constraint]
        txnameList = sorted(txnameList, key=lambda tx: tx.txName)
        if not txnameList:
            logger.warning("No valid txnames found for %s (not assigned constraints?)" %str(expRes))
            continue
        cfile = os.path.join(expRes.path,"general.comment")
        if os.path.isfile(cfile):
            logger.info('\033[96m  == General Comment file found: == \033[0m')        
            cf = open(cfile,'r')
            print "\033[96m"+cf.read()+"\033[0m"
            cf.close()        
        
        for txname in txnameList:
            txnameStr = txname.txName
            if not txname.validated in check: continue
            logger.info("------------ \033[31m Checking  %s \033[0m" %txnameStr)
            if not showPlots:
                continue
            validationResult = checkPlotsFor(txname,update)
            
            if validationResult == 'skip' or not update:
                continue
            
            #Collect all txname.txt files corresponding to this txname string
            #(multiple files only appear for EM results)
            txfiles = []
            for dset in expRes.datasets:
                txfiles += [tx.path for tx in dset.txnameList if tx.txName == txname.txName]
            for txfile in txfiles:
                txfile = txname.path
                if not os.path.isfile(txfile):
                    logger.error('\n\n ******\n Txname file %s NOT FOUND!!! \n**** \n\n' %(txfile))
                    continue
                tf = open(txfile,'r')
                tdata = ""
                for l in tf.readlines():
                    if 'validated:' in l:
                        l = 'validated: '+str(validationResult)+'\n'
                    tdata += l
                tf.close()
                tf = open(txfile,'w')
                tf.write(tdata)
                tf.close()
            
            logger.info("------------ \033[31m %s checked as validated = %s \033[0m" %(txnameStr,str(validationResult)))
        logger.info("--------- \033[32m %s checked in %.1f min \033[0m" %(expRes.globalInfo.id,(time.time()-expt0)/60.))
    logger.info("\n\n----- Finished checking in %.1f min." %((time.time()-tval0)/60.))
    
    #Print summary output, if selected.
    if printSummary:
        validated_true = []
        validated_false = []
        validated_none = []
        #Only reload the database if files were updated:
        if update:
            db = Database(databasePath,verbosity=verbosity)
            expResList = db.getExpResults(analysisIDs, datasetIDs, txnames,
                      dataTypes, useSuperseded=True, useNonValidated=True)
        for expRes in expResList:
#             print expRes
            dataset = expRes.datasets[0]
            txnameList = [tx for tx in dataset.txnameList if not 'assigned' in tx.constraint]
            for txname in txnameList:
                if txname.validated is True:
                    validated_true.append(txname)
                elif txname.validated is False:
                    validated_false.append(txname)
                elif txname.validated is None:
                    validated_none.append(txname)
        #Print results
        logger.info('\033[32m %i Txnames with Validated = True \033[0m' %len(validated_true))
        logger.info('\033[32m %i Txnames with Validated = False \033[0m' %len(validated_false))
        logger.info('\033[32m %i Txnames with Validated = None \033[0m' %len(validated_none))    
 

    
if __name__ == "__main__":
    
    ap = argparse.ArgumentParser(description="Checks the validation plots, set the validated fields and add validation comments")
    ap.add_argument('-p', '--parfile', 
            help='parameter file specifying the plots to be checked', default='./checkval_parameters.ini')
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
    from smodels.experiment.databaseObj import Database


    #Control output level:
    numeric_level = getattr(logging,args.log.upper(), None)
    logger.setLevel(level=numeric_level)
    
    #Selected plots for checking:
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
        
    databasePath = parser.get("path", "databasePath")
    
    check = [eval(c) for c in parser.get("extra","check").split(',')]
    showPlots = parser.getboolean("extra","showPlots")
    update = parser.getboolean("extra","update")
    printSummary = parser.getboolean("extra","printSummary")
  

    #Check plots:
    main(analyses,datasetIDs,txnames,dataTypes,databasePath,check,showPlots,update,printSummary,args.log)
    
