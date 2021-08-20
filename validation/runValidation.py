#!/usr/bin/env python3

"""
.. module:: runValidation.py
   :synopsis: runs the validation procedure, defined in an ini file.

"""

import sys,os,copy
import logging
import argparse,time

try:
    from ConfigParser import SafeConfigParser, NoOptionError
except ImportError as e:
    from configparser import ConfigParser, NoOptionError

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)

def validatePlot( expRes,txnameStr,axes,slhadir,options : dict, kfactor=1., pretty=False,
                  combine=False, namedTarball = None, keep = False ):
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
    :param pretty: If True it will generate "pretty" plots, if "both", will
    :param combine: combine signal regions, or use best signal region
    :param namedTarball: if not None, then this is the name of the tarball explicitly specified in Txname.txt
    :param keep: keep temporary directories
    :return: True on success
    """

    logger.info("Generating validation plot for " + expRes.globalInfo.id
                +", "+txnameStr+", "+axes)
    valPlot = validationObjs.ValidationPlot(expRes,txnameStr,axes,slhadir = None,
                        options = options,kfactor=kfactor,
                        namedTarball = namedTarball, keep = keep, combine = combine )
    if valPlot.niceAxes == None:
        logger.info ( "valPlot.niceAxes is None. Skip this." )
        return False
    if options["generateData"] != False:
        valPlot.setSLHAdir(slhadir)
    generatedData=False
    if options["generateData"]:
        valPlot.getDataFromPlanes()
        options["generatedData"]=True
    else:
        valPlot.loadData()
    if not valPlot.data:
        if options["generateData"] is None:
            logger.info ( "data generation on demand was specified (generateData=None) and no data found. Lets generate!" )
            valPlot.getDataFromPlanes()
            options["generatedData"]=True
    if pretty in [ True ]:
        valPlot.getPrettyPlot()
        valPlot.pretty = True
        valPlot.savePlot()
        if options["generatedData"]:
            valPlot.saveData()
            if options["pngAlso"]:
                valPlot.savePlot(fformat="png")
    import ROOT
    for i in ROOT.gROOT.GetListOfCanvases():
        i.Destructor()
    if pretty in [ False ]:
        valPlot.getUglyPlot()
        valPlot.pretty = False
        valPlot.savePlot()
        if generatedData:
            valPlot.saveData()
            if pngAlso:
                valPlot.savePlot(fformat="png")
    for i in ROOT.gROOT.GetListOfCanvases():
        i.Destructor()
    return True

def run ( expResList, options : dict, keep ):
    """
    Loop over experimental results and validate plots
    :param options: all flags in the "options" part of the ini file
    :param keep: keep temporary directories
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
        pretty = options["prettyPlots"]
        prettyorugly = [ pretty ]
        if pretty=="both":
            prettyorugly = [ True, False ]
        for itx,txname in enumerate(txnames):
            txnameStr = txname.txName
            txt0 = time.time()
            logger.info("------ \033[31m validating  %s \033[0m" %txnameStr)
            namedTarball = None
            if not tarfiles:
                tarfile = txnameStr+".tar.gz"
            else:
                tarfile = os.path.basename(tarfiles[itx])
            if hasattr ( txname, "validationTarball" ):
                tarfile = txname.validationTarball
                namedTarball = tarfile
                logger.info("Database entry specifies a validation tarball: %s. Will use it." % tarfile )
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
            axis = options["axis"]
            if axis is None:
                for ax in axes:
                    for p in prettyorugly:
                        validatePlot(expRes,txnameStr,ax,tarfile, options, kfactor, p,
                                 combine, namedTarball =namedTarball, keep = keep )
                        options["generateData"]=False
            else:
                from sympy import var
                x,y,z = var("x y z")
                ax = str(eval(axis)) ## standardize the string
                for p in prettyorugly:
                    validatePlot(expRes,txnameStr,ax,tarfile, options, kfactor, p,
                                 combine )
                    generateData = False
            logger.info("------ \033[31m %s validated in  %.1f min \033[0m" %(txnameStr,(time.time()-txt0)/60.))
        logger.info("--- \033[32m %s validated in %.1f min \033[0m" %(expRes.globalInfo.id,(time.time()-expt0)/60.))


def main(analysisIDs,datasetIDs,txnames,dataTypes,kfactorDict,slhadir,databasePath,
         options : dict, tarfiles=None,verbosity='error', combine=False, force_load = None, 
         keep = False ):
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
    :param verbosity: overall verbosity (e.g. error, warning, info, debug)
    :param combine: combine signal regions, or use best signal region
    :param force_load: force loading the text database ("txt"), or the
           binary database ("pcl"), dont force anything if None
    :param keep: keep temporary directories
    """

    if not os.path.isdir(databasePath):
        logger.error('%s is not a folder' %databasePath)

    ## to mark the points of the data grid
    import smodels.experiment.txnameObj
    smodels.experiment.txnameObj.TxNameData._keep_values = True

    if "TGQ12" in txnames:
        print ( "[runValidation] we have TGQ12, turning overlap check off" )
        import smodels.experiment.datasetObj
        smodels.experiment.datasetObj._complainAboutOverlappingConstraints = False

    try:
        db = Database( databasePath, force_load, discard_zeroes = False,
                       subpickle = True )
    except Exception as e:
        logger.error("Error loading database at %s" % ( databasePath ) )
        logger.error("Error: %s" % str(e) )
        sys.exit()

    logger.info('-- Running validation...')


    #Select experimental results, txnames and datatypes:
    expResList = db.getExpResults( analysisIDs, datasetIDs, txnames,
                  dataTypes, useNonValidated=True )

    if not expResList:
        logger.error("No experimental results found.")

    if options["ncpus"] < 0:
        from smodels.tools import runtime
        options["ncpus"] = runtime.nCPUs() + options["ncpus"] + 1
    # logger.info ( "ncpus=%d, n(expRes)=%d, genData=%d" % ( ncpus, len(expResList), generateData ) )

    tval0 = time.time()
    run ( expResList, options, keep )
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
    ap.add_argument('-f', '--force_build', action="store_true",
            help='force building of database pickle file (you may want to do this for the grid datapoints in the ugly plots)' )
    ap.add_argument('-k', '--keep', action="store_true", help='keep temp dir' )
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
    analyses = parser.get("database", "analyses")
    if analyses.find(";")>0:
        analyses = analyses[:analyses.find(";")]
    analyses = analyses.split(",")
    analyses = [ x.strip() for x in analyses ]
    txnames = parser.get("database", "txnames")
    if txnames.find(";")>0:
        txnames = txnames[:txnames.find(";")]
    txnames = txnames.split(",")
    txnames = [ x.strip() for x in txnames ]
    force_load = None
    if args.force_build:
        force_load = "txt"

    dataselector = "upperLimit"
    try:
        dataselector = parser.get("database", "dataselector")
    except NoOptionError as e:
        logger.warning ( "setting 'dataselector' in section 'database' to 'upperLimit'" )
    combine=False
    if dataselector == "efficiencyMap":
        dataTypes = ['efficiencyMap']
        datasetIDs = ['all']
    elif dataselector == "upperLimit":
        dataTypes = ['upperLimit']
        datasetIDs = ['all']
    elif dataselector == "combined":
        dataTypes = ['efficiencyMap']
        datasetIDs = ['all']
        combine=True
    elif dataselector == "all":
        dataTypes = ['all']
        datasetIDs = ['all']
    else:
        #dataTypes = ['all']
        dataTypes = ['efficiencyMap']
        datasetIDs = dataselector.split(",")

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

    options = { "prettyPlots": False, # ## only pretty plots, only ugly plots, or both
                "keepListOfSRs": False, ## keep a list of all signal regions, ordered by their sensitivities (good for trimming and aggregating
                "drawChi2Line": False, # draw an exclusion line derived from chi2 values in green (only on pretty plot )
                "limitPoints": None, ## limit the number of points to run on
                "axis": None, ## the axes to plot. If not given, take from sms.root
                "style": "", # specify a plotting style, currently only 
                # "" and "sabine" are known
                # style "sabine": SR label "pyhf combining 2 SRs" gets moved to
                # top left corner of temperature p lot in pretty print
                "legendplacement": "automatic", # specify how the legend is placed
                # one of: top left, top right, auto [top right]
                "weightedAgreementFactor": False, 
                ## do we weight the points for the agreement factor?
                "extraInfo": False, ## add extra info to the plot?
                "pngAlso": False, ## only pdf plots?
                "drawExpected": "auto", ## draw expected exclusion lines (True,False,auto) 
                "preliminary": False, ## add label 'preliminary' to plot?
                "model": "default", ## which model to use (default = mssm)
                "ncpus": -1, ## number of processes, if negative, subtract that number from number of cores on the machine minus one.
    }
    if parser.has_section("options"):
        if parser.has_option("options","ncpus"):
            options["ncpus"] = parser.getint("options","ncpus")
        if parser.has_option("options","drawExpected"):
            drawExpected = parser.get("options","drawExpected")
            if drawExpected in [ "1", "true", "True", True, 1, "yes" ]:
                drawExpected = True
            if drawExpected in [ "0", "false", "False", False, 0, "no" ]:
                drawExpected = False
            options["drawExpected"] = drawExpected
        if parser.has_option("options","pngPlots"):
            options["pngAlso"] = parser.getboolean("options", "pngPlots" )
        if parser.has_option("options","keepListOfSRs"):
            options["keepListOfSRs"] = parser.getboolean("options", "keepListOfSRs" )
        if parser.has_option("options","axis"):
            options["axis"] = parser.get("options","axis" )
        if parser.has_option("options","drawChi2Line"):
            options["drawChi2Line"] = parser.getboolean("options","drawChi2Line" )
        if parser.has_option("options","prettyPlots"):
            spretty = parser.get("options", "prettyPlots" ).lower()
            if spretty in [ "true", "yes", "1" ]:
                options["prettyPlots"] = True
            if spretty in [ "*", "all", "both" ]:
                options["prettyPlots"] = "both"
            if options["prettyPlots"] == False and spretty in [ "none", "neither", "dontplot" ]:
                options["prettyPlots"] = None
            if options["prettyPlots"] == False and spretty not in [ "false", "0", "no" ]:
                logger.error ( "prettyPlots %s unknown" % spretty )
                sys.exit()
        if parser.has_option("options","limitPoints"):
            options["limitPoints"] = parser.getint("options","limitPoints")
        if parser.has_option("options","extraInfo"):
            options["extraInfo"] = parser.getboolean("options", "extraInfo")
        if parser.has_option("options","preliminary"):
            options["preliminary"] = parser.getboolean("options", "preliminary")
        if parser.has_option("options","style"):
            options["style"] = parser.get("options", "style")
        if parser.has_option("options","legendplacement"):
            options["legendplacement"] = parser.get("options", "legendplacement")
        if parser.has_option("options","weightedAgreementFactor"):
            options["weightedAgreementFactor"] = parser.getboolean("options", "weightedAgreementFactor")
        if parser.has_option("options","model" ):
            options["model"] = parser.get("options","model")
    ## Set to True to run SModelS on the slha files. If False, use the already
    ## existing *.py files in the validation folder. If None or
    ## 'ondemand', produce data only if none are found
    options["generateData"] = _doGenerate ( parser )

    #Run validation:
    main(analyses,datasetIDs,txnames,dataTypes,kfactorDict,slhadir,databasePath, options, 
         tarfiles,args.verbose.lower(), combine, force_load, args.keep )
