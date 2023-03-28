#!/usr/bin/env python3

"""
.. module:: runValidation.py
   :synopsis: runs the validation procedure, defined in an ini file.

"""

import sys,os,copy
try:
    import colorama as __c
    GREEN, RED, RESET = __c.Fore.GREEN, __c.Fore.RED, __c.Fore.RESET
except:
    GREEN, RED, RESET = "","",""
import logging
import argparse,time
from sympy import var

try:
    from ConfigParser import SafeConfigParser, NoOptionError
except ImportError as e:
    from configparser import ConfigParser, NoOptionError

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logger = logging.getLogger(__name__)

def starting( expRes, txnameStr, axes ):
    logger.info( f"{expRes.globalInfo.id}:{txnameStr}:{axes.replace(' ','')}" )

def validatePlot( expRes,txnameStr,axes,slhadir,options : dict, kfactor=1.,
        pretty=False, combine=False, namedTarball = None, keep = False ):
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
    :return: ValidationPlot object or False
    """

    starting( expRes, txnameStr, axes )
    valPlot = validationObjs.ValidationPlot(expRes,txnameStr,axes,slhadir = None,
                        options = options,kfactor=kfactor,
                        namedTarball = namedTarball, keep = keep, combine = combine )
    if valPlot.niceAxes == None:
        logger.info ( "valPlot.niceAxes is None. Skip this." )
        return False
    if options["generateData"] != False:
        valPlot.setSLHAdir(slhadir)
    if options["generateData"] != False:
        valPlot.getDataFromPlanes()
    else:
        valPlot.loadData()
    #print ( ">>>>> do we have data?", valPlot.data!=None )
    #if valPlot.data != None:
    #    print ( ">>>>>> len: ", len(valPlot.data) )
    if not valPlot.data:
        if options["generateData"] is None:
            logger.info ( "data generation on demand was specified (generateData=None) and no data found. Lets generate!" )
            valPlot.getDataFromPlanes()
            # we did generate data
            options["generateData"]=True
    if pretty in [ True ]:
        valPlot.getPrettyPlot()
    if pretty in [ True, "dictonly" ]:
        if options["generateData"]!=False:
            # if ondemand we save also, new points might have been added
            valPlot.saveData()
        if pretty not in [ "dictonly" ]:
            valPlot.savePlot( fformat = "png" )
        if options["pdfAlso"] and pretty not in [ "dictonly" ]:
            valPlot.toPdf()
    from smodels_utils.helper.rootTools import destroyRoot
    destroyRoot()
    if pretty in [ False ]:
        valPlot.getUglyPlot()
        if options["generateData"]:
            valPlot.saveData()
        valPlot.savePlot( fformat = "png" )
        if options["pdfAlso"]:
            valPlot.toPdf()
    destroyRoot()
    return valPlot

def addRange ( var : str, opts : dict, xrange : str, axis : str ):
    """ add a range condition to options, overwrite one if already there
    :param var: variable, "x" or "y"
    :param xrange: the *range parameter, eg ['[[x,y],[x,y]]:[200,500]', '[[x,0.0],[x,0.0]]:[220,520]'], or '[200,500]'
    """
    ax = eval ( axis )
    if type(xrange) == list:
        hasFound = False
        for xr in xrange:
            tokens = xr.split(":")
            if eval(tokens[0])==ax:
                xrange = tokens[1]
                logger.info ( f"using {xrange} for {var}range"  )
                hasFound=True
                break
        if not hasFound: # we did not find this
            logger.warning ( f"we did not find axis range for {axis} in {xrange} in database entry {var}range" )
            return opts
    else:
        tokens = xrange.split(":")
        if eval(tokens[0])==ax:
            xrange = tokens[1]
            logger.info ( f"using {xrange} for {var}range"  )
            hasFound=True
    if "style" in opts:
        # if xy-axis is already in, we dont overwrite
        if not var+"axis" in opts["style"]:
            styles = opts["style"].split(";")
            newstyles=[ f"{var}axis{xrange}" ]
            for style in styles:
                style = style.strip()
                if not f"{var}axis" in style and style !="":
                    newstyles.append ( style )
            opts["style"]=";".join(newstyles)
    else:
        opts["style"]=f"{var}axis{xrange}"
    return opts

def checkForRatioPlots ( expRes, txname : str, ax, db, combine, opts, datafile,
       axis ):
    """ check if we should plot a ratio plot 
    :param txname: the txname
    :param combine: is a a combined result that is asked for?
    :param db: the database
    :param datafile: validation file
    """
    from smodels_utils.helper.prettyDescriptions import prettyAxes
    from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
    massplane = MassPlane.fromString(txname, ax )
    #axis = prettyAxes ( txname, ax, output )
    # axis = str(massplane)#  ax.replace(" ","")
    axis = axis.replace(",","").replace("(","").replace(")","").\
                    replace("/","d").replace("*","")
    if not combine: # if it isnt a combination, we dont want 
        return False # a ratio plot
    ulres = db.getExpResults ( [ expRes.globalInfo.id ], [ None ], [ txname ],
                       dataTypes = [ "upperLimit" ] )
    if len(ulres)==0:
        return False # we actually do not have an UL result for that
    dbpath = db.subs[0].base
    ana1 = datafile.replace(dbpath,"")
    p1 = ana1.find("validation")
    ana1 = ana1[:p1-1]
    p2 = ana1.rfind("/")
    ana1 = ana1[p2+1:]
    valfile1 = os.path.basename ( datafile )
    ana2 = expRes.globalInfo.id
    valfile2 = valfile1.replace("_combined","")
    output = os.path.dirname ( datafile ) + f"/ratios_{txname}_{axis}.png"
    options = { "show": opts["show"], "output": output }
    import plotRatio
    plotRatio.draw ( dbpath, ana1, valfile1, ana2, valfile2, options )

def run ( expResList, options : dict, keep, db ):
    """
    Loop over experimental results and validate plots
    :param options: all flags in the "options" part of the ini file
    :param keep: keep temporary directories
    :param db: database, so we can check if ratio plots are desirable
    """
    for expRes in expResList:
        expt0 = time.time()
        logger.info( f"--- {GREEN} validating {expRes.globalInfo.id} {RESET}" )
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
            stype=""
            if combine:
                stype=" (combine) "
            logger.info( f"------ {GREEN} validating {txnameStr}{stype} {RESET}" )
            namedTarball = None
            if not tarfiles:
                tarfile = txnameStr+".tar.gz"
            else:
                tarfile = os.path.basename(tarfiles[itx])
            if hasattr ( txname, "validationTarball" ):
                tarfile = txname.validationTarball
                namedTarball = tarfile
                if type(tarfile) == list:
                    l=f"Database entry specifies validation tarballs: {','.join(tarfile)}. Will use them."
                else:
                    l=f"Database entry specifies a validation tarball: {tarfile}. Will use it."
                logger.info( l )
            # tarfile = os.path.join(slhadir,tarfile)

            # flag needed to identify the case where axes are given
            # for named tarballs, but current axis is different
            hasCorrectAxis=False
            if options["generateData"] != False:
                tokens = tarfile
                if type(tokens) == str:
                    tokens = [ tarfile ]
                #tokens = tarfile.split(";")
                for tf in tokens:
                    tf = tf.strip()
                    #  and not os.path.isfile(tarfile):
                    fname = tf
                    if ":" in tf:
                        axis,fname = fname.split(":")[:2]
                    else:
                        hasCorrectAxis = True
                    tarfile = os.path.join(slhadir,fname )
                    if not os.path.isfile ( tarfile ):
                        logger.info( 'Missing %s file for %s.' % ( tarfile, txnameStr))
                # continue

            gkfactor = 1.
            #Define k-factors
            if txnameStr.lower() in kfactorDict:
                gkfactor = float(kfactorDict[txnameStr.lower()])

            #Loop over all axes:
            if not isinstance(txname.axes,list):
                axes = [txname.axes]
            else:
                axes = txname.axes
            axis = options["axis"]
            # logger.info ( "axis", axis )
            if axis is None:
                for ax in axes:
                    hasCorrectAxis_ = hasCorrectAxis
                    x,y,z = var("x y z")
                    ax = str(eval(ax)) ## standardize the string
                    kfactor = gkfactor
                    fname_ = "none"
                    if type(namedTarball) == str and ":" in namedTarball:
                        myaxis,fname_= namedTarball.split(":")[:2]
                        myaxis = str ( eval ( myaxis ) )
                        if myaxis == ax:
                            hasCorrectAxis_ = True
                            tarfile = os.path.join(slhadir,fname_)
                            break
                    if type(namedTarball) == list:
                        # looks like were given multiples
                        for nt in namedTarball:
                            if ":" in nt:
                                myaxis,fname_= nt.split(":")[:2]
                                myaxis = str ( eval ( myaxis ) )
                                if myaxis == ax:
                                    hasCorrectAxis_ = True
                                    pnamedTarball = fname_
                                    tarfile = os.path.join(slhadir,fname_)
                                    break
                    if fname_ in kfactorDict:
                        # print ( "namedTarball", namedTarball, "ax", ax )
                        if type(namedTarball) == str and ":" in namedTarball:
                            myaxis,fname_= namedTarball.split(":")[:2]
                            myaxis = str ( eval ( myaxis ) )
                            if myaxis == ax:
                                kfactor = float(kfactorDict[fname_])
                                logger.info ( f"kfactor {kfactor} given specifically for tarball {fname_} axis {myaxis}" )
                        else:
                            kfactor = float(kfactorDict[fname_])
                            logger.info ( f"kfactor {kfactor} given specifically for tarball {fname_}" )
                    localopts = copy.deepcopy ( options )
                    if hasattr ( txname, "xrange" ):
                        localopts = addRange ( "x", localopts, txname.xrange, ax )
                    if hasattr ( txname, "yrange" ):
                        localopts = addRange ( "y", localopts, txname.yrange, ax )
                    pnamedTarball = namedTarball
                    if not hasCorrectAxis_:
                        pnamedTarball = None
                        tarfile = os.path.join(slhadir,txnameStr+".tar.gz")

                    for p in prettyorugly:
                        re = validatePlot(expRes,txnameStr,ax, tarfile, localopts,
                                kfactor, p, combine, namedTarball = pnamedTarball,
                                keep = keep )
                        # if not ":" in namedTarball:
                        localopts["generateData"]=False
                        oldNamedTarball = pnamedTarball
                        validationDir = re.getValidationDir ( None )
                        datafile = re.getDataFile(validationDir)
                    checkForRatioPlots ( expRes, txnameStr, ax, db, combine, 
                                         localopts, datafile, re.niceAxes )
            else: # axis is not None
                x,y,z = var("x y z")
                ax = str(eval(axis)) ## standardize the string
                if type(namedTarball) == str and ":" in namedTarball:
                    myaxis,fname_= namedTarball.split(":")[:2]
                    myaxis = str ( eval ( myaxis ) )
                    if myaxis == ax:
                        tarfile = os.path.join(slhadir,fname_)
                        hasCorrectAxis = True
                if type(namedTarball) == list:
                    # looks like were given multiples
                    for nt in namedTarball:
                        if ":" in nt:
                            myaxis,fname_= nt.split(":")[:2]
                            myaxis = str ( eval ( myaxis ) )
                            if myaxis == ax:
                                tarfile = os.path.join(slhadir,fname_)
                                hasCorrectAxis = True
                                break
                ## we need "local" options, since we switch one flag
                pnamedTarball = namedTarball
                if not hasCorrectAxis:
                    pnamedTarball = None
                    tarfile = os.path.join(slhadir,txnameStr+".tar.gz")
                localopts = copy.deepcopy ( options )
                if hasattr ( txname, "xrange" ):
                    localopts = addRange ( "x", localopts, txname.xrange, ax )
                if hasattr ( txname, "yrange" ):
                    localopts = addRange ( "y", localopts, txname.yrange, ax )
                for p in prettyorugly:
                    validatePlot( expRes,txnameStr,ax,tarfile, localopts,
                                  gkfactor, p, combine, namedTarball = pnamedTarball )
                    localopts["generateData"] = False
            logger.info( "------ %s %s validated in  %.1f min %s" % \
                         (RED, txnameStr,(time.time()-txt0)/60., RESET) )
        logger.info( "--- %s %s validated in %.1f min %s" % \
                     (RED, expRes.globalInfo.id,(time.time()-expt0)/60., RESET) )


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

    if options["ncpus"] <= 0:
        from smodels.tools import runtime
        options["ncpus"] = runtime.nCPUs() + options["ncpus"]
        if options["ncpus"] < 1: # cannot be less than 1
            options["ncpus"] = 1

    tval0 = time.time()
    run ( expResList, options, keep, db )
    dt = (time.time()-tval0)/60.
    logger.info( f"\n\n-- Finished validation in {dt:.1f} min." )

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
    ap.add_argument('-s', '--show', action="store_true", help='show plots after producing them. tries a few viewers like timg, see, display.' )
    ap.add_argument('-v', '--verbose',
            help='specifying the level of verbosity (error, warning, info, debug) [info]',
            default = 'info', type = str)

    args = ap.parse_args()

    if not os.path.isfile(args.parfile):
        logger.error("Parameters file ''%s'' not found" %args.parfile)
        sys.exit(-1)
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
    dataTypes = []
    datasetIDs = []
    selectors = dataselector.split(",")
    for s in selectors:
        s = s.strip()
        if s == "efficiencyMap":
            dataTypes += ['efficiencyMap']
            datasetIDs = ['all']
        elif s == "upperLimit":
            dataTypes += ['upperLimit']
            datasetIDs = ['all']
        elif s == "combined":
            dataTypes += ['efficiencyMap']
            datasetIDs = ['all']
            combine=True
        elif s == "all":
            dataTypes += ['all']
            datasetIDs = ['all']
        elif s == "tpredcomb":
            from validation import useTheoPredCombiner as validationObjs
            validationObjs.logger.setLevel(level=numeric_level)
            dataTypes += ['efficiencyMap']
            datasetIDs = ['all']
        else:
            dataTypes += ['efficiencyMap']
            datasetIDs += s.split(",")

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
                "keepTopNSRs": 0, ## keep an ordered list of <n> most sensitive signal regions, needed for trimming and aggregating
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
                "pdfAlso": True, ## only png plots?
                "drawExpected": "auto", ## draw expected exclusion lines (True,False,auto)
                "preliminary": False, ## add label 'preliminary' to plot?
                "model": "default", ## which model to use (default = mssm)
                "show": False, ## show image after producing it?
                "backend": "native", ## backend, can be ROOT or native
                "interpolationType": "cubic", ## interpolation type for matplotlib plots (linear, nearest, cubic)
                "ncpus": -4, ## number of processes, if zero or negative, subtract that number from number of cores on the machine.
    }
    if parser.has_section("options"):
        if parser.has_option("options","ncpus"):
            options["ncpus"] = parser.getint("options","ncpus")
        if parser.has_option("options","validationFolder"):
            options["validationFolder"] = parser.get("options","validationFolder")
        if parser.has_option("options","interpolationType"):
            options["interpolationType"]=parser.get("options","interpolationType")
        if parser.has_option("options","drawExpected"):
            drawExpected = parser.get("options","drawExpected")
            if drawExpected in [ "1", "true", "True", True, 1, "yes" ]:
                drawExpected = True
            if drawExpected in [ "0", "false", "False", False, 0, "no" ]:
                drawExpected = False
            options["drawExpected"] = drawExpected
        if parser.has_option("options","pngPlots"):
            options["pngAlso"] = parser.getboolean("options", "pngPlots" )
        if parser.has_option("options","pdfPlots"):
            options["pdfAlso"] = parser.getboolean("options", "pdfPlots" )
        if parser.has_option("options","backend"):
            options["backend"] = parser.get("options", "backend" )
        options["expectationType"] = "posteriori"
        if parser.has_option("options","expectationType"):
            options["expectationType"] = parser.get ( "options", "expectationType" )
        if parser.has_option("options","keepTopNSRs"):
            options["keepTopNSRs"] = parser.getint("options", "keepTopNSRs" )
            if dataselector in [ "combined", "upperLimit" ] and options["keepTopNSRs"]>0:
               logger.warning ( f"you selected dataselection ''{dataselector}'' but also chose to keepTopNSRs={options['keepTopNSRs']}. The feature ''keepTopNSRs'' will only work with dataselection ''efficiencymap'', not with ''{dataselector}'. You have been warned." )
        else:
            if dataselector in [ "efficiencyMap" ]:
                options["keepTopNSRs"] = 10 ## for effiency maps we want that per default
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
            if spretty in [ "dictonly" ]:
                options["prettyPlots"] = "dictonly"
            if options["prettyPlots"] == False and spretty not in [ "false", "0", "no", "dictonly" ]:
                logger.error ( "prettyPlots %s unknown" % spretty )
                sys.exit()
        if parser.has_option("options","limitPoints"):
            options["limitPoints"] = parser.getint("options","limitPoints")
        if parser.has_option("options","extraInfo"):
            options["extraInfo"] = parser.getboolean("options", "extraInfo")
        if parser.has_option("options","preliminary"):
            options["preliminary"] = parser.getboolean("options", "preliminary")
        if parser.has_option("options","style"):
            o = parser.get("options", "style")
            options["style"] = o
            if o.count("; ")>1 or o.count(" ;")>1:
                logger.warning ( "found more than one semicolon with space in style field ''{o}''. Please check if you didnt add one space too many!" )

        if parser.has_option("options","legendplacement"):
            options["legendplacement"] = parser.get("options", "legendplacement")
            options["legendplacement"] = options["legendplacement"].\
                replace("'","").replace('"',"").lower().strip()
        if parser.has_option("options","weightedAgreementFactor"):
            options["weightedAgreementFactor"] = parser.getboolean("options", "weightedAgreementFactor")
        if parser.has_option("options","model" ):
            options["model"] = parser.get("options","model")
        if parser.has_option("options","show" ):
            options["show"] = parser.get("options","show")
    ## Set to True to run SModelS on the slha files. If False, use the already
    ## existing *.py files in the validation folder. If None or
    ## 'ondemand', produce data only if none are found
    options["generateData"] = _doGenerate ( parser )

    if args.show:
        options["show"]=True

    #Run validation:
    main(analyses,datasetIDs,txnames,dataTypes,kfactorDict,slhadir,databasePath, options,
         tarfiles,args.verbose.lower(), combine, force_load, args.keep )
