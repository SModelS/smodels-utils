#!/usr/bin/env python3

from __future__ import print_function
import logging,sys,os
# logging.basicConfig(filename='val.out')
import subprocess
import argparse
import signal
try:
    from ConfigParser import SafeConfigParser
except ImportError as e:
    from configparser import ConfigParser
import time
from sympy import var
import string

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)


def getNiceAxes(axesStr):
    """
    Convert the axes definition format ('[[x,y],[x,y]]')
    to a nicer format ('Eq(MassA,x)_Eq(MassB,y)_Eq(MassA,x)_Eq(MassB,y)')

    :param axesStr: string defining axes in the old format

    :return: string with a nicer representation of the axes (more suitable for printing)
    """

    x,y,z,w = var('x y z w')
    if axesStr:
        axes = eval(axesStr,{'x' : x, 'y' : y, 'z': z, 'w' : w})
    else:
        return 'True'

    eqList = []
    for ib,br in enumerate(axes):
        if ib == 0:
            mStr = 'Mass'
        else:
            mStr = 'mass'
        mList = []
        for im,eq in enumerate(br):
            mList.append('Eq(%s,%s)'
                           %(var(mStr+string.ascii_uppercase[im]),eq))
        mStr = "_".join(mList)
        eqList.append(mStr)

    #Simplify symmetric branches:
    if eqList[0].lower() == eqList[1].lower() and len(eqList) == 2:
        eqStr = "2*%s"%eqList[0]
    else:
        eqStr = "__".join(eqList)

    eqStr = eqStr.replace(" ","")

    eqStr = eqStr.replace(",","").replace("(","").replace(")","")

    return eqStr.replace('*','')


def checkPlotsFor(txname,update):
    """
    Checks a list of validation plots for the txname and returns the validation result
    set by the user.
    If update is True, it will rewrite the validated field in txname.txt.

    :param txname: Txname object corresponding to the
    :param update: option to update (rewrite) the txname.txt files (True/False)

    :return: Validation result (True/False/NA/TBD or skip)
    """


    axes = txname.axes
    if isinstance(axes,str):
        axes = [axes]
    #Collect validation plots:
    valPlots = []
    missingPlots = []
    for axe in axes:
        ax = getNiceAxes(axe)
        plotfile = txname.txName+"_"+ax+".png"
        valplot = os.path.join(txname.path,'../../validation/'+plotfile)
        valplot = os.path.abspath(valplot)
        if not os.path.isfile(valplot):
            missingPlots.append(valplot)
        else:
            valPlots.append(valplot)

    if not valPlots:
        logger.error('\033[36m       No plots found \033[0m')
    else:
        for plot in missingPlots:
            logger.error('\033[36m        plot %s not found \033[0m' %valplot)

    #Check the plots
    plots = []
    for fig in valPlots:
        try:
            plots.append(subprocess.Popen('eog -n '+fig,shell=True, preexec_fn=os.setsid,
                                          stdout=subprocess.PIPE))
        except:
            plots.append(subprocess.Popen(['open',fig]))
    cfile = os.path.join(os.path.dirname(txname.path),"../validation/"+txname.txName+".comment")
    if os.path.isfile(cfile):
        logger.info('\033[96m  == Txname Comment file found: == \033[0m')
        cf = open(cfile,'r')
        print("\033[96m"+cf.read()+"\033[0m")
        cf.close()


    val = ""
    while not val.lower() in ['t','f','n','s','tbd','exit']:
        try:
            val = raw_input("TxName is validated? (Current validation status: %s) \
        \n True/False/NA/TBD/Skip (t/f/n/tbd/s) \n (or type exit to stop)\n" %txname.validated)
        except:
            val = input("TxName is validated? (Current validation status: %s) \
        \n True/False/NA/TBD/Skip (t/f/n/tbd/s) \n (or type exit to stop)\n" %txname.validated)
        if val.lower() == 't': validationResult = True
        elif val.lower() == 'f': validationResult = False
        elif val.lower() == 'n': validationResult = 'N/A'
        elif val.lower() == 'tbd': validationResult = 'TBD'
        elif val.lower() == 's': validationResult = 'skip'
        elif val.lower() == 'exit':
            for plot in plots:
                os.killpg(os.getpgid(plot.pid), signal.SIGTERM)
            sys.exit()
        else:
            print('Unknow option. Try again.')
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
    :param check: list containing which type of plots to check ([False,'N/A',..])
    :param showPlots: option to open the plots or not (True/False)
    :param update: option to update (rewrite) the txname.txt files (True/False)
    :param printSummary: option to re-load the database and print the number of
                        validated True/False/Other txnames
    :param verbosity: overall verbosity (e.g. error, warning, info, debug)

    :return: True if all selected plots were checked, False otherwise
    """

    if not os.path.isdir(databasePath):
        logger.error('%s is not a folder' %databasePath)

    try:
        db = Database(databasePath)
    except:
        logger.error("Error loading database at %s" %databasePath)


    logger.info('----- Checking plots...')

    #Select experimental results, txnames and datatypes:
    expResList = db.getExpResults( analysisIDs, datasetIDs, txnames,
                  dataTypes, useNonValidated=True)

    if not expResList:
        logger.error("No experimental results found.")

    tval0 = time.time()
    expResList = sorted(expResList, key=lambda exp: exp.globalInfo.id)
    #Loop over experimental results and validate plots
    for expRes in expResList:

        expt0 = time.time()
        logger.info("--------- \033[32m Checking  %s \033[0m" %os.path.basename(expRes.path))
        txnameList = []
        txnameStrs = []
        for dataset in expRes.datasets:
            for tx in dataset.txnameList:
                if tx.txName in txnameStrs:
                    continue
                txnameList.append(tx)
                txnameStrs.append(tx.txName)
        txnameList = sorted(txnameList, key=lambda tx: tx.txName)
        if not txnameList:
            logger.warning("No valid txnames found for %s (not assigned constraints?)" %str(expRes))
            continue
        cfile = os.path.join(expRes.path,"general.comment")
        if os.path.isfile(cfile):
            logger.info('\033[96m  == General Comment file found: == \033[0m')
            cf = open(cfile,'r')
            print("\033[96m"+cf.read()+"\033[0m")
            cf.close()

        for txname in txnameList:
            txnameStr = txname.txName
            if not txname.validated in check:
                continue
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
        logger.info("--------- \033[32m %s checked in %.1f min \033[0m" %(os.path.basename(expRes.path),(time.time()-expt0)/60.))
    logger.info("\n\n----- Finished checking in %.1f min." %((time.time()-tval0)/60.))

    #Print summary output, if selected.
    if printSummary:
        validated_true = []
        validated_false = []
        validated_none = []
        #Only reload the database if files were updated:
        if update:
            db = Database(databasePath)
            expResList = db.getExpResults(analysisIDs, datasetIDs, txnames,
                      dataTypes, useNonValidated=True )
        for expRes in expResList:
#             print expRes
            dataset = expRes.datasets[0]
            txnameList = [tx for tx in dataset.txnameList if not 'assigned' in tx.constraint]
            for txname in txnameList:
                if txname.validated is True:
                    validated_true.append(txname)
                elif txname.validated is False:
                    validated_false.append(txname)
                else:
                    validated_none.append(txname)
        #Print results
        logger.info('\033[32m %i Txnames with Validated = True \033[0m' %len(validated_true))
        logger.info('\033[32m %i Txnames with Validated = False \033[0m' %len(validated_false))
        logger.info('\033[32m %i Txnames with Validated = "other" \033[0m' %len(validated_none))



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

    try:
        parser = SafeConfigParser()
    except:
        parser = ConfigParser( inline_comment_prefixes=( ';', ) )
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

    check = []
    for c in parser.get("extra","check").split(','):
        try:
            c = eval(c)
        except:
            pass
        if isinstance(c,str):
            c = c.lower()
        check.append(c)

    showPlots = parser.getboolean("extra","showPlots")
    update = parser.getboolean("extra","update")
    printSummary = parser.getboolean("extra","printSummary")


    #Check plots:
    main(analyses,datasetIDs,txnames,dataTypes,databasePath,check,showPlots,update,printSummary,args.log)
