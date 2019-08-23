#!/usr/bin/env python3

"""
.. module:: runValidation.py
   :synopsis: runs the validation procedure, defined in an ini file.

"""

import sys,os,copy
import logging
import argparse,time
from smodels.tools import runtime

try:
    from ConfigParser import SafeConfigParser
except ImportError as e:
    from configparser import ConfigParser

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)

def validatePlot( expRes,txnameStr,axes,slhadir,kfactor=1.,ncpus=-1,
                  pretty=False,generateData=True,limitPoints=None,extraInfo=False,
                  combine=False,pngAlso = False, weightedAgreementFactor = True,
                  model = "default" ):
    """
    Creates a validation plot and saves its output.

    :param expRes: a ExpResult object containing the result to be validated
    :param txnameStr: String describing the txname (e.g. T2tt)
    :param axes: the axes string describing the plane to be validated
                 (e.g.  2*[[x,y]])
    :param slhadir: folder containing the SLHA files corresponding to txname
    or the .tar.gz file containing the SLHA files.
    :param kfactor: optional global k-factor value to re-scale
                    all theory prediction values
    :param ncpus: Number of jobs to submit. ncpus = -1 means all processors.

    :param pretty: If True it will generate "pretty" plots, if "both", will 
                   generate pretty *and* non-pretty

    :param generateData: If True, run SModelS on the slha files.
                         If False, use the already existing *.py files in the
                         validation folder.  If None, run SModelS only if
                         needed.
    :param limitPoints: Limit the total number of points to <n> (integer). 
                        Points are chosen randomly.
                        If None or negative, take all points.
    :param extraInfo: add additional info to plot: agreement factor, time spent,
                      time stamp, hostname
    :param combine: combine signal regions, or use best signal region
    :param pngAlso: save also pngs
    :param weightedAgreementFactor: when computing the agreement factor,
                                    weight points by the area of their Voronoi cell
    :param model: the model to use (e.g. mssm, nmssm, idm)
    :return: True
    """

    logger.info("Generating validation plot for " + expRes.globalInfo.id
                +", "+txnameStr+", "+axes)
    valPlot = validationObjs.ValidationPlot(expRes,txnameStr,axes,kfactor=kfactor,
                    limitPoints=limitPoints,extraInfo=extraInfo,combine=combine,
                    weightedAgreementFactor = weightedAgreementFactor,
                    model = model )
    if generateData != False:
        valPlot.setSLHAdir(slhadir)
    valPlot.ncpus = ncpus
    generatedData=False
    if generateData:
        valPlot.getDataFromPlanes()
        generatedData=True
    else:
        valPlot.loadData()
    if not valPlot.data:
        if generateData is None:
            logger.info ( "data generation on demand was specified (generateData=None) and no data found. Lets generate!" )
            valPlot.getDataFromPlanes()
            generatedData=True
    if pretty in [ True, "both" ]:
        tmp = copy.deepcopy ( valPlot ) # work around ROOT quirks
        valPlot.getPrettyPlot()
        valPlot.pretty = True
        valPlot.savePlot()
        if generatedData:
            valPlot.saveData()
            if pngAlso:
                valPlot.savePlot(fformat="png")
        valPlot = tmp # work around ROOT quirks
    if pretty in [ False, "both" ]:
        valPlot.getPlot()
        valPlot.pretty = False
        valPlot.savePlot()
        if generatedData:
            valPlot.saveData()
            if pngAlso:
                valPlot.savePlot(fformat="png")

    return True

def run ( expResList, axis ):
    """
    Loop over experimental results and validate plots
    :param axis: Plot only for these axes. If none, get axes from sms.root
    """
    for expRes in expResList:
        expt0 = time.time()
        logger.info("--- \033[32m validating  %s \033[0m" %expRes.globalInfo.id)
        #Loop over pre-selected txnames:
        txnamesStr = []
        txnames = []
        for tx in expRes.getTxNames():
            if 'assigned' in tx.constraint:
                continue  #Skip not assigned constraints
            if tx.txName in txnamesStr:
                continue #Do not include a txname twice (if it appears in more than one dataset)
            txnames.append(tx)
            txnamesStr.append(tx.txName)

        if not txnames:
            logger.warning("No valid txnames found for %s (not assigned constraints?)" %str(expRes))
            continue
        for itx,txname in enumerate(txnames):
            txnameStr = txname.txName
            txt0 = time.time()
            logger.info("------ \033[31m validating  %s \033[0m" %txnameStr)
            if not tarfiles:
                tarfile = txnameStr+".tar.gz"
            else:
                tarfile = os.path.basename(tarfiles[itx])
            tarfile = os.path.join(slhadir,tarfile)

            if not os.path.isfile(tarfile) and generateData != False:
                logger.info( 'Missing .tar.gz file for %s.' %txnameStr)
                continue

            #Define k-factors
            if txnameStr.lower() in kfactorDict:
                kfactor = float(kfactorDict[txnameStr.lower()])
            else:
                kfactor = 1.

            #Loop over all axes:
            if not isinstance(txname.axes,list):
                axes = [txname.axes]
            else:
                axes = txname.axes     
            if axis is None:
                for ax in axes:
                    validatePlot(expRes,txnameStr,ax,tarfile,kfactor,ncpus,pretty,
                                 generateData,limitPoints,extraInfo,combine,pngAlso,
                                 weightedAgreementFactor, model )
            else:
                from sympy import var
                x,y,z = var("x y z")
                ax = str(eval(axis)) ## standardize the string
                validatePlot(expRes,txnameStr,ax,tarfile,kfactor,ncpus,pretty,
                             generateData,limitPoints,extraInfo,combine,pngAlso,
                             weightedAgreementFactor, model )
            logger.info("------ \033[31m %s validated in  %.1f min \033[0m" %(txnameStr,(time.time()-txt0)/60.))
        logger.info("--- \033[32m %s validated in %.1f min \033[0m" %(expRes.globalInfo.id,(time.time()-expt0)/60.))


def main(analysisIDs,datasetIDs,txnames,dataTypes,kfactorDict,slhadir,databasePath,
        tarfiles=None,ncpus=-1,verbosity='error',pretty=False,generateData=True,
        limitPoints=None,extraInfo=False,combine=False,pngAlso=False,
        weightedAgreementFactor=True, model = "default", axis=None ):
    """
    Generates validation plots for all the analyses containing the Txname.

    :param analysisIDs: list of analysis ids ([CMS-SUS-13-006,...])
    :param dataType: dataType of the analysis (all, efficiencyMap or upperLimit)
    :param txnames: list of txnames ([TChiWZ,...])
    :param slhadir: Path to the folder containing the txname .tar.gz files
    :param databasePath: Path to the SModelS database
    :param kfactorDict: kfactor dictionary to be applied to the theory cross-sections
                        (e.g. {'TChiWZ' : 1.2, 'T2' : 1.,..})
    :param tarfiles: Allows to define a specific list of tarballs to be used.
                     The list should match the txnames list.
                     If set to None, it will use the default file (txname.tar.gz).
    :param ncpus: Number of jobs to submit. ncpus = -1 means all processors.
    :param verbosity: overall verbosity (e.g. error, warning, info, debug)

    :param pretty: If True it will generate "pretty" plots

    :param generateData: If True, run SModelS on the slha files.
              If False, use the already existing *.py files in the validation folder.
              None: generate them if needed.
    :param limitPoints: Limit the number of tested model points to <n> randomly 
              chosen points. If None or negative, test all points.
    :param extraInfo: add additional info to plot: agreement factor, time spent,
              time stamp, hostname

    :param combine: combine signal regions, or use best signal region
    :param pngAlso: save also pngs
    :param model: the model to use (mssm, nmssm, idm, ... )
    :param axis: specify the axes, if None get them from sms.root
    """

    if not os.path.isdir(databasePath):
        logger.error('%s is not a folder' %databasePath)

    try:
        db = Database(databasePath, subpickle = True )
    except Exception as e:
        logger.error("Error loading database at %s" %databasePath)
        logger.error("Error: %s" % str(e) )
        sys.exit()

    logger.info('-- Running validation...')

    #Select experimental results, txnames and datatypes:
    expResList = db.getExpResults( analysisIDs, datasetIDs, txnames,
                  dataTypes, useSuperseded=True, useNonValidated=True)

    if not expResList:
        logger.error("No experimental results found.")

    if ncpus < 0: 
        ncpus = runtime.nCPUs() + ncpus + 1
    # logger.info ( "ncpus=%d, n(expRes)=%d, genData=%d" % ( ncpus, len(expResList), generateData ) )

    tval0 = time.time()
    run ( expResList, axis )
    logger.info("\n\n-- Finished validation in %.1f min." %((time.time()-tval0)/60.))

def _doGenerate ( parser ):
    """ determine if we do want to force generation of data (True),
    explicitly do not generate any data (False), or generate only on-demand
    (None) """
    if parser.has_section("options") and parser.has_option("options","generateData"):
        generateData = parser.get("options", "generateData")
        if generateData in [ None, True, False ]:
            return generateData
        if generateData.lower() in [ "none", "ondemand" ]:
            return None
        if generateData.lower() in [ "true", "yes" ]:
            return True
        if generateData.lower() in [ "false", "no" ]:
            return False
        if not generateData in [ None, True, False ]:
            logger.error ( "generateData value %s is not understood. Set to 'ondemand'." % generateData )
            return None
    logger.info ( "generateData is not defined in ini file. Set to 'ondemand'." )
    return None


if __name__ == "__main__":

    ap = argparse.ArgumentParser(description="Produces validation plots and data for the selected results")
    ap.add_argument('-p', '--parfile',
            help='parameter file specifying the validation options [validation_parameters.ini]', default='./validation_parameters.ini')
    ap.add_argument('-v', '--verbose',
            help='specifying the level of verbosity (error, warning, info, debug) [info]',
            default = 'info', type = str)

    args = ap.parse_args()

    if not os.path.isfile(args.parfile):
        logger.error("Parameters file %s not found" %args.parfile)
    else:
        logger.info("Reading validation parameters from %s" %args.parfile)

    parser = None
    try:
        parser = ConfigParser( inline_comment_prefixes=( ';', ) )
    except Exception as e:
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
    numeric_level = getattr(logging,args.verbose.upper(), None)
    logger.setLevel(level=numeric_level)
    plottingFuncs.logger.setLevel(level=numeric_level)
    validationObjs.logger.setLevel(level=numeric_level)
    from smodels.tools import smodelsLogging
    smodelsLogging.setLogLevel( args.verbose )

    #Selected plots for validation:
    analyses = parser.get("database", "analyses").split(",")
    analyses = [ x.strip() for x in analyses ]
    txnames = parser.get("database", "txnames").split(",")
    txnames = [ x.strip() for x in txnames ]
    combine=False
    if parser.get("database", "dataselector") == "efficiencyMap":
        dataTypes = ['efficiencyMap']
        datasetIDs = ['all']
    elif parser.get("database", "dataselector") == "upperLimit":
        dataTypes = ['upperLimit']
        datasetIDs = ['all']
    elif parser.get("database", "dataselector") == "combined":
        dataTypes = ['efficiencyMap']
        # datasetIDs = ['combined']
        datasetIDs = ['all']
        combine=True
    else:
        dataTypes = ['all']
        datasetIDs = parser.get("database", "dataselector").split(",")

    kfactorDict = dict(parser.items("kfactors"))
    slhadir = parser.get("path", "slhaPath")
    databasePath = parser.get("path", "databasePath")

    tarfiles = None
    if parser.has_option("path","tarfiles"):
        tarfiles = parser.get("path", "tarfiles")
        if not tarfiles or tarfiles == "None":
            tarfiles = None
        else:
            tarfiles = tarfiles.split(',')

    ncpus = -1 ## number of processes, if negative, subtract that number from number of cores on the machine minus one.
    pngAlso = False ## only pdf plots?
    axis = None ## the axes to plot. If not given, take from sms.root
    pretty = False ## only pretty plots, only ugly plots, or both
    limitPoints=None ## limit the number of points to run on
    extraInfo = False ## add extra info to the plot?
    weightedAgreementFactor = False ## do we weight the points for the agreement factor?
    model = "default" ## which model to use (default = mssm)
    if parser.has_section("options"):
        if parser.has_option("options","ncpus"):
            ncpus = parser.getint("options","ncpus")
        if parser.has_option("options","pngPlots"):
            pngAlso = parser.getboolean("options", "pngPlots" )
        if parser.has_option("options","axis"):
            axis = parser.get("options","axis" )
        if parser.has_option("options","prettyPlots"):
            spretty = parser.get("options", "prettyPlots" ).lower()
            if spretty in [ "true", "yes", "1" ]:
                pretty = True
            if spretty in [ "*", "all", "both" ]:
                pretty = "both"
            if pretty == False and spretty not in [ "false", "0", "no" ]:
                logger.error ( "prettyPlots %s unknown" % spretty )
                sys.exit()
        if parser.has_option("options","limitPoints"):
            limitPoints = parser.getint("options","limitPoints")
        if parser.has_option("options","extraInfo"):
            extraInfo = parser.getboolean("options", "extraInfo")
        if parser.has_option("options","weightedAgreementFactor"):
            weightedAgreementFactor = parser.getboolean("options", "weightedAgreementFactor")
        if parser.has_option("options","model" ):
            model = parser.get("options","model")
    generateData = _doGenerate ( parser )

#    try:
#        import ROOT
#        if args.verbose == 'warning':
#            ROOT.gErrorIgnoreLevel = ROOT.kWarning
#        elif args.verbose == 'error':
#            ROOT.gErrorIgnoreLevel = ROOT.kError
#        else:
#            ROOT.gErrorIgnoreLevel = ROOT.kInfo
#    except:
#        pass

    #Run validation:
    main(analyses,datasetIDs,txnames,dataTypes,kfactorDict,slhadir,databasePath,
         tarfiles,ncpus,args.verbose.lower(),pretty,generateData,limitPoints,
         extraInfo,combine,pngAlso,weightedAgreementFactor, model, axis )
