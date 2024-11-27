#!/usr/bin/env python3

"""
.. module:: validationObjsBase
   :synopsis: Base class for ValidationPlot and GraphsValidationPlot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import logging
import os, time
from validationHelpers import getDefaultModel, showPlot
from smodels.matching import modelTester
from typing import Union

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.ERROR)

class ValidationObjsBase():
    """
    The base class for ValidationPlot and GraphsValidationPlot, as they share much
    of their code.
    """

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
            f.write(f"[experimentalFeatures]\n" )
            useTevatron = False
            if "useTevatronCLsConstruction" in self.options:
                useTevatron = self.options["useTevatronCLsConstruction"]
            f.write ( f"tevatroncls = {useTevatron}\n" )
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
        meta["tevatroncls"]= False
        try:
            from smodels.base.runtime import experimentalFeature
            meta["tevatroncls"]= experimentalFeature ( "tevatroncls" )
        except Exception as e:
            print ( f"[validationOjbsBase] experimentalFeature not yet available. its ok we can skip this" )
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

