#!/usr/bin/env python3

"""
.. module:: validationObjsBase
   :synopsis: Base class for ValidationPlot and GraphsValidationPlot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import logging
import os, time, sys, copy
from validationHelpers import getDefaultModel, showPlot
from smodels.matching import modelTester
from typing import Union, List
from colorama import Fore as ansi

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.ERROR)

class ValidationObjsBase():
    """
    The base class for ValidationPlot and GraphsValidationPlot, as they share much
    of their code.
    """

    def getValidationDir ( self, validationDir : str ) -> str:
        """ obtain the validation directory, usually,
            self.expRes.path + "/validation" """
        def mkdir ( mydir ):
            if not os.path.isdir(mydir):
                logger.info( f"Creating validation folder {mydir}")
                os.mkdir(mydir)
        if validationDir:
            mkdir ( validationDir )
            return validationDir
        validationFolder = "validation"
        if "validationFolder" in self.options:
            validationFolder = self.options["validationFolder"]
        validationDir = os.path.join(self.expRes.path,validationFolder)
        mkdir ( validationDir )
        return validationDir

    def getPlotFileName(self,validationDir : str, fformat : str = 'pdf') -> str:
        """
        Defines the name of the plot file and returns it

        :param validationDir: Folder where the plots and validation dictionaries
        will be saved
        :return: name of the plot file
        """

        if fformat.startswith("."):
            fformat = fformat[1:]

        filename = self.expRes.globalInfo.id + "_" + self.txName + "_"
        filename += self.niceAxes.replace(",","").replace("(","").replace(")","").\
                    replace("/","d")
        if self.combine:
            filename += '_combined'
        filename += '.'+fformat

        filename = filename.replace(self.expRes.globalInfo.id+"_","")
        filename = os.path.join(validationDir,filename)
        filename = filename.replace("*","").replace(",","").replace("(","").replace(")","").replace("0.0","0").replace("1.0","1").replace("._","_")
        return filename

    def getPrettyPlot(self,silentMode : bool = True ):
        """
        Uses the data in self.data and the official exclusion curve
        in self.officialCurves to generate a pretty exclusion plot
        :param silentMode: If True the plot will not be shown on the screen
        """
        if self.isOneDimensional():
            self.pretty = False
            return
        from prettyMatplotlib import createPrettyPlot
        options = copy.deepcopy ( self.options )
        if options["drawExpected"] == "auto":
            options["drawExpected"] = True

        self.plot, self.base = createPrettyPlot(self,silentMode=silentMode,
                   looseness = 1.2, options = options )
        self.pretty = True

    def savefig ( self, filename : str ):
        """ save the figure, never mind if root or matplotlib """
        if hasattr ( self.plot, "Print" ):
            self.plot.Print(filename)
        if hasattr ( self.plot, "savefig" ):
            self.plot.savefig(filename)

    def savePlot( self,validationDir : Union[None,str] = None,
                  fformat : str = 'png' ):
        """
        Saves the plot in the format specified in the validationDir folder.
        If the folder does not exist, it will be created.
        If the folder is not defined the plot will be created in the
        analysis/validation/ folder

        :param validationDir: Folder where the plot will be saved
        :param fformat: File fformat (accepted by ROOT), i.e. pdf, png, jpg...
        """

        if not hasattr(self,'plot') or not self.plot:
            logger.warning("No plot found. Nothing will be saved")
            return False

        if hasattr ( self.plot, "dontplot" ) and self.plot.dontplot == True:
            logger.warning("Plotting got inhibited." )
            return False

        vDir = self.getValidationDir ( validationDir )

        filename = self.getPlotFileName(vDir,fformat)


        if not self.pretty:
            logger.info ( f"saving plot in {ansi.YELLOW}{filename}{ansi.RESET}" )
            self.savefig(filename)
            filename = filename.replace('.'+fformat,'.png')
            try:
                self.savefig(filename)
            except Exception as e:
                # if fails because of missing dep, then just proceed
                pass
        else:
            from addLogoToPlots import addLogo
            #Print pdf, png and root formats
            filename = filename.replace('.'+fformat,'_pretty.'+fformat)
            logger.info ( f"saving plot in {ansi.YELLOW}{filename}{ansi.RESET}" )
            self.savefig ( filename )
            addLogo ( filename )
            newfilename = filename.replace('.'+fformat,'.pdf')
            if self.options["pdfPlots"]:
               cmd = f"convert {filename} {newfilename}"
               import subprocess
               o = subprocess.getoutput ( cmd )
        self.show ( filename )

        return True

    
    def getUglyPlot(self,silentMode : bool = True ):
        """
        Uses the data in self.data and the official exclusion curve
        in self.officialCurves to generate the exclusion plot
        :param silentMode: If True the plot will not be shown on the screen
        """

        if self.isOneDimensional():
            from oneDPlots import create1DPlot as createUglyPlot
        else:
            from uglyMatplotlib import createUglyPlot
        self.plot, self.base = createUglyPlot( self,silentMode=silentMode,
                                          options = self.options )
        self.pretty = False


    def isOneDimensional ( self ) -> bool:
        """ are the data one-dimensional """
        if "forceOneD" in self.options and self.options["forceOneD"]:
            # we force 1d plotting mode
            return True
        if self.data in [ [], None ]:
            return None
        ys = []
        for ctPoints,pt in enumerate(self.data):
            if pt == None:
                continue
            if "axes" in pt and pt["axes"] != None and "x" in pt["axes"]:
                if not "y" in pt["axes"]:
                    #is1D = True
                    return True
                yvalue = pt["axes"]["y"]
                if yvalue == "stable":
                    yvalue = 1e-26
                if type(yvalue) not in [ str ]:
                    ys.append ( yvalue )
        if len(ys)>0:
            deltay = max(ys)-min(ys)
            if deltay < 1e-14:
               logger.warn ( f"the range in y values {deltay} is quite small. sure you dont want to make a 1d plot? if yes, say forceOneD = True, in the options section in the ini file." )
        return False


    def toPdf ( self, validationDir : str = None ):
        """ convert from png to pdf (new, for uproot) """
        vDir = self.getValidationDir ( validationDir )
        oldfilename = self.getPlotFileName(vDir,"png")
        if self.pretty:
            oldfilename = oldfilename.replace('.png','_pretty.png')
        newfilename = oldfilename.replace(".png",".pdf")
        command = f"convert {oldfilename} {newfilename}"
        import subprocess
        o = subprocess.getoutput ( command )
        # print ( "toPdf", command, o )

    def resultExistsAlready(self,slhafilename : str ) -> bool:
        """ does a result exist already for the given slha file """
        resultfile = f"{self.currentSLHADir}/results/{slhafilename}.py"
        if os.path.exists ( resultfile ):
            return True
        return False

    def runSModelS ( self, outputformat : int = 3 ) -> list:
        """ run SModelS proper 
        :param outputformat: define if the output is v2 or v3
        :returns: list of slha files that we ran over (is this true?)
        """

        self.getSLHAdir()  #Path to the folder containing the SLHA files
        logger.debug( f"SLHA files for validation at {self.currentSLHADir}" )

        #Get list of input files to be tested
        try:
            fileList, inDir = modelTester.getAllInputFiles(self.currentSLHADir)
        except Exception: ## old version?
            fileList = modelTester.getAllInputFiles(self.currentSLHADir)
            inDir = slhaDir
        if self.options["generateData"]==None:
            self.loadData()
            tmp = []
            countSkipped = 0
            for f in fileList:
                if f.endswith ( ".tar.gz" ):
                    continue
                bf = os.path.basename ( f )
                if self.slhafileInData ( bf ):
                    countSkipped += 1
                else:
                    tmp.append ( f )
            if countSkipped > 0:
                logger.info ( f"skipped a total of {countSkipped} points that are already in final dictionary: generateData was set to 'ondemand'." )
            fileList = tmp
        else:
            self.data = []

        #Set temporary outputdir:
        outputDir = os.path.join ( self.currentSLHADir, "results" )
        if os.path.exists ( outputDir ):
            if self.options["generateData"] == None:
                logger.info ( f"results folder exists already, and generateData is ondemand, so will use them" )
            else:
                if self.options["generateData"]==True:
                    logger.warning ( f"weird, {outputDir} already exists, and generateData is {self.options['generateData']}? Removing {outputDir}!" )
                    shutil.rmtree ( outputDir )
                    os.mkdir ( outputDir )
                else:
                    outputDir = tempfile.mkdtemp(dir=self.currentSLHADir,prefix='results_')
                    logger.warning ( f"weird, {outputDir} already exists, and generateData is {self.options['generateData']}? Creating new results folder {outputDir}" )
        else:
            os.mkdir ( outputDir )

        if self.options["generateData"]==None:
            self.loadData()
            tmp = []
            countSkipped = 0
            countSLHAFileInData = 0
            countResultExists = 0
            for f in fileList:
                if f.endswith ( ".tar.gz" ):
                    continue
                if f in [ "results", "coordinates", "comment" ]:
                    continue
                bf = os.path.basename ( f )
                if self.slhafileInData ( bf ):
                    countSkipped += 1
                    countSLHAFileInData += 1
                elif self.resultExistsAlready ( bf ):
                    self.addResultToData ( bf, f"{outputDir}/{bf}.py" )
                    countSkipped += 1
                    countResultExists += 1
                else:
                    tmp.append ( f )
            if countSkipped > 0:
                logger.info ( f"skipped a total of {countSkipped} points that are in temporary folder: generateData was set to 'ondemand'." )
                logger.info ( f" -> {countSLHAFileInData} points are already in final validation dictionary, for {countResultExists} points a file exists in the temporary results folder." )
                # lets randomize in these cases, so we can somewhat parallelize
                # FIXME it would be better if we locked individual slha files
            import random
            random.shuffle ( tmp )
            fileList = tmp
        else:
            self.data = []

        self.outputDir = outputDir

        #Get parameter file:
        parameterFile = self.getParameterFile(tempdir=outputDir,outputformat=outputformat)
        logger.info( f"SLHA dir {self.slhaDir}" )
        logger.info( f"Parameter file: {parameterFile}" )

        #Read and check parameter file, exit parameterFile does not exist
        parser = modelTester.getParameters(parameterFile)

        #Select the desired experimental result
        listOfExpRes = [self.expRes]

        """ Test all input points """
        validationFolder = "validation"
        if "validationFolder" in self.options:
            validationFolder = self.options["validationFolder"]
        timeOut = 5000
        if "timeOut" in self.options:
            timeOut = self.options["timeOut"]
        self.willRun = self.addToListOfRunningFiles ( fileList )
        if False: ## this is currently not working
            pid = os.fork()
            if pid == 0: ## child process
                dirname = os.path.basename ( self.currentSLHADir )
                print ( f"@@0 child process, will need to run progress bar for {dirname}" )
                from progress import Progress
                p = Progress ( dirname, False )
                sys.exit()
        modelTester.testPoints( self.willRun, inDir, outputDir, parser, self.db,
                               timeOut, False, parameterFile )
        self.removeFromListOfRunningFiles ( )
        return fileList

    def getParameterFile(self,tempdir : str = None,
           outputformat : int = 3 ) -> str:
        """
        Creates a temporary parameter file to be passed to runSModelS

        :param tempdir: Temporary folder where the parameter file will be created. Default = current folder.
        :param outputformat: is it v2 or v3 type output?

        :returns: name of temporary parameter file
        """

        #Get the analysis ID, txname and dataset ID:
        expId = self.expRes.globalInfo.id
        txname = self.expRes.getTxNames()[0].txName

        #Get number of cpus:
        if not hasattr(self, 'ncpus') or not self.ncpus:
            self.ncpus  = 1
            if "ncpus" in self.options:
                self.ncpus = self.options["ncpus"]

        if tempdir is None: tempdir = os.getcwd()
        parFile = os.path.join ( tempdir, "parameter.ini" )
        if os.path.exists ( parFile ):
            if self.options['generateData']==None:
                logger.warning ( f"parameter file {parFile} exists already, but generateData is ondemand. Will use." )
            else:
                logger.warning ( f"weird, parameter file {parFile} already exists?" )
                parFile = tempfile.mktemp(dir=tempdir,prefix='parameter_',suffix='.ini' ) # , text=True )
        pf = open ( parFile, "wt" )

        combine = "False"
        if self.combine:
            combine = "True"
            self.validationType="combine"
        model = self.options["model"]
        if model == "default":
            model = getDefaultModel ( tempdir )
        with open ( parFile, "w" ) as f:
            f.write("[options]\ninputType = SLHA\ncheckInput = True\ndoInvisible = True\ndoCompress = True\ncomputeStatistics = True\ntestCoverage = False\n" )
            f.write ( f"combineSRs = {combine}\n" )
            f.write ( f"pyhfbackend = pytorch\n" )
            if self.options["keepTopNSRs"] not in  [ None, 0 ]:
                f.write ( "reportAllSRs = True\n" )
            sigmacut = 0.000000001
            minmassgap = 2.0
            maxcond = 1.0
            promptWidth=1.1
            if "sigmacut" in self.options:
                sigmacut = self.options["sigmacut"]
            if "minmassgap" in self.options:
                minmassgap = self.options["minmassgap"]
            if "maxcond" in self.options:
                maxcond = self.options["maxcond"]
            if "promptWidth" in self.options:
                promptWidth = self.options["promptWidth"]
            dataselector = "all"
            if len(self.expRes.datasets)>1:
                dataselector = "efficiencyMap"
            useTevatron = False
            if "useTevatronCLsConstruction" in self.options:
                useTevatron = self.options["useTevatronCLsConstruction"]
            asimovIsExpected = False
            if "asimovIsExpected" in self.options:
                asimovIsExpected = self.options["asimovIsExpected"]
            if asimovIsExpected or useTevatron:
                f.write(f"[experimentalFeatures]\n" )
            if useTevatron:
                f.write ( f"tevatroncls = {useTevatron}\n" )
            if asimovIsExpected:
                f.write ( f"asimovisexpected = {asimovIsExpected}\n" )
            f.write(f"[parameters]\nsigmacut = {sigmacut}\nminmassgap = {minmassgap}\nmaxcond = {maxcond}\nncpus = {self.ncpus}\n" )
            f.write(f"[database]\npath = {self.databasePath}\nanalyses = {expId}\ntxnames = {txname}\ndataselector = {dataselector}\n" )
            f.write(f"[printer]\noutputFormat = version{outputformat}\noutputType = python\n")
            f.write(f"[particles]\n")
            if not "share.models" in model:
                model = f"share.models.{model}"
            f.write(f"model={model}\n" )
            f.write(f"promptWidth={promptWidth}\n" )
            #expected = "posteriori"
            #expected = "priori"
            expected = self.options["expectationType"]
            f.write( f"[python-printer]\naddElementList = False\ntypeOfExpectedValues='{expected}'\nprinttimespent=True\n")
            if outputformat == 3:
                f.write ( "addNodesMap=True\n" )
            f.close()
        # os.close(pf)
        pf.close()
        return parFile

    def getTxname ( self ):
        """ obtain the correct sms/axes/data maps, i.e. the ones corresponding to
        our txname """
        ds = self.expRes.datasets[0]
        ## FIXME need to search
        for txn in ds.txnameList:
            if txn.txName == self.txName:
                return txn
        return None

    def removeFromListOfRunningFiles ( self ):
        """ remove files listed in fileList to list of running  files """
        fileList = self.willRun
        current = {}
        if os.path.exists ( self.runningDictFile ):
            with open ( self.runningDictFile, "rt" ) as f:
                try:
                    current = eval ( f.read() )
                except Exception as e:
                    logger.info ( f"exception {e}" )
            f.close()
        for f in fileList:
            if f.endswith ( ".tar.gz" ):
                continue
            if f in [ "results", "coordinates", "comment" ]:
                continue
            try:
                current.pop ( f )
            except KeyError as e: # it's not in, so nothing to take out
                # we can ignore
                pass
        self.lockFile()
        with open ( self.runningDictFile, "wt" ) as f:
            f.write ( f"{current}\n" )
            f.close()
        self.unlockFile()
        self.willRun = []
        return


    def addToListOfRunningFiles ( self, fileList : List ) -> List:
        """ add files listed in fileList to list of running  files 
        :returns: list you should actually run
        """
        current = {}
        shouldRun = set()
        if os.path.exists ( self.runningDictFile ):
            with open ( self.runningDictFile, "rt" ) as f:
                try:
                    current = eval ( f.read() )
                except Exception as e:
                    logger.info ( f"exception {e}" )
            f.close()
        cleanedcurrent = {}
        for f,t in current.items():
            dt = ( time.time() - t ) / 60. # minutes
            ## FIXME we should actually only take out once 
            ## we run out of "good" points
            if dt < 15.: # after 15 minutes we take it out!
                cleanedcurrent[f]=t
        current = cleanedcurrent
        for f in fileList:
            if f.endswith ( ".tar.gz" ):
                continue
            if f in [ "results", "coordinates", "comment" ]:
                continue
            if not f in current:
                if self.limitPoints in [-1, None] or len(shouldRun)<self.limitPoints:
                    current[f]=time.time()
                    shouldRun.add ( f )
        self.lockFile()
        with open ( self.runningDictFile, "wt" ) as f:
            f.write ( f"{current}\n" )
            f.close()
        self.unlockFile()
        return shouldRun


    def lockFile ( self, lockfile : Union [ None, str ] = None ):
        """ a locking mechanism """
        if lockfile is None:
            lockfile = self.runningDictLockFile 
        ctr = 0
        while os.path.exists ( lockfile ):
            ctr+=1
            time.sleep ( .1 * ctr )
            if ctr > 10: # we dont wait forever
                self.unlockFile( lockfile )
                return
        from pathlib import Path
        Path ( lockfile ).touch()

    def unlockFile( self, lockfile : Union [ None, str ] = None ):
        """ a locking mechanism """
        if lockfile is None:
            lockfile = self.runningDictLockFile 
        if os.path.exists ( lockfile ):
            try:
                os.unlink ( lockfile )
            except FileNotFoundError as e:
                pass

    def saveData(self,validationDir : Union[None,os.PathLike] =None,
                 datafile : Union[None,os.PathLike] =None) -> bool:
        """
        Saves the data and plot in a text file in the validationDir folder.
        If the folder does not exist, it will be created.
        If the folder is not defined the plot will be created in the
        analysis/validation/ folder
        If datafile is not define, uses the default naming (Txname_axes.py)

        :param validationDir: Folder where the root file will be saved
        :param datafile: Name of the data file

        :returns: true, if all worked fine
        """

        if not hasattr(self,'data') or not self.data:
            logger.warning("No data found. Nothing will be saved")
            return False

        if self.options["generateData"] in [ None, "ondemand" ]:
            nadded = self.loadData ( overwrite = False )
            logger.info ( f"loaded {len(self.data)} data points" )
            if nadded == 0:
                logger.warning("No added points. Nothing will be saved")
                return False

        validationDir = self.getValidationDir ( validationDir )

        if not datafile:
            datafile = self.getDataFile(validationDir)
        self.datafile = datafile
        lockfile = datafile + ".lock"
        self.lockFile ( lockfile )
        print ( f"[validationObjs] saving {len(self.data)} points to {datafile}" )
        #Save data to file
        f = open(datafile,'w')
        dataStr = str(self.data)
        dataStr = dataStr.replace('[fb]','*fb').replace('[pb]','*pb')
        dataStr = dataStr.replace('[GeV]','*GeV').replace('[TeV]','*TeV')
        dataStr = dataStr.replace( "}, {" , "},\n{" )
        if "inf" in dataStr:
            dataStr = dataStr.replace("inf,","float('inf')," )
        f.write("validationData = "+dataStr+"\n")
        from smodels import installation
        from smodels_utils import SModelSUtils
        nerr = 0
        for i in self.data:
            if "error" in i:
                nerr += 1
        dt = round ( ( time.time() - self.t0 ) / 60. / 60., 3 ) ## in hours
        #hostname = "unknown"
        import socket
        hostname = socket.gethostname()
        meta = { "smodelsver": installation.version(), "axes": self.axes,
                 "npoints": len(self.data), "nerr": nerr, "dt[h]": dt,
                 "expectationType": self.options["expectationType"],
                 "utilsver": SModelSUtils.version(), "timestamp": time.asctime() }
        if hasattr ( self.expRes.globalInfo, "includeCRs" ):
            meta["includeCRs"]=self.expRes.globalInfo.includeCRs
        if os.path.exists ( f"{validationDir}/../validation_commentary.txt" ):
            with open( f"{validationDir}/../validation_commentary.txt","rt") as f2:
                txt=f2.read().strip()
                f2.close()
                meta["commentary"]=txt
        if hasattr ( self.expRes.globalInfo, "resultType" ):
            meta["resultType"]=self.expRes.globalInfo.resultType
        from smodels.matching import theoryPrediction
        if "spey" in theoryPrediction.StatsComputer.__module__:
            import spey
            meta["spey"]=spey.__version__
        if hasattr ( self, "pointsInTarFile" ):
            meta["nmax"]=self.pointsInTarFile
        meta["host"]=hostname
        meta["nSRs"]=len ( self.expRes.datasets )
        if hasattr ( self, "meta" ):
            if "runs" in self.meta:
                meta["runs"] = self.meta["runs"]
            if 'dt[h]' in self.meta:
                dt = round ( dt + self.meta["dt[h]"], 3 )
                meta["dt[h]"] = dt
        if not "runs" in meta:
            meta["runs"]=f"{len(self.data)}"
        if hasattr ( self, "ncpus" ):
            meta["ncpus"]=self.ncpus
        if self.namedTarball != None:
            meta["namedTarball"]=self.namedTarball
        meta["tarball"]=self.slhaDir[self.slhaDir.rfind("/")+1:]
        useTevatronCLs = False
        asimovIsExpected = False
        from smodels.base.runtime import experimentalFeature
        try:
            useTevatronCLs = experimentalFeature ( "tevatroncls" )
            asimovIsExpected = experimentalFeature ( "asimovisexpected" )
        except Exception as e:
            print ( f"[validationOjbsBase] experimentalFeature not yet available. its ok we can skip this" )
        if useTevatronCLs:
            meta["tevatroncls"]= useTevatronCLs
        if asimovIsExpected:
            meta["asimovisexpected"]= asimovIsExpected
        f.write( f"meta = {str(meta)}\n" )
        f.close()
        self.unlockFile ( lockfile )

        return True

    def show ( self, filename ):
        """ we were asked to also show <filename> """
        term = os.environ["TERM"]
        if not self.options["show"]: #  or not term == "xterm-kitty":
            return
        showPlot ( filename )

    def getNiceAxes(self,axesStr):
        """
        Convert the axes definition format ('[[x,y],[x,y]]')
        to a nicer format ('Eq(MassA,x)_Eq(MassB,y)_Eq(MassA,x)_Eq(MassB,y)')

        :param axesStr: string defining axes in the old format

        :return: string with a nicer representation of the axes (more suitable for printing)
        """
        return self.massPlane.getNiceAxes ( axesStr )
