#!/usr/bin/env python3

"""
.. module:: validationObjsBase
   :synopsis: Base class for ValidationPlot and GraphsValidationPlot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
#import logging
import os, time, sys, copy, tarfile, tempfile, random, glob, shutil
from validationHelpers import getDefaultModel, showPlot, streamlineValidationData
from smodels.matching import modelTester
from typing import Union, List, Dict
from validationHelpers import point_in_hull
from plottingFuncs import getExclusionCurvesFor
from smodels_utils.helper.terminalcolors import *
from smodels.base.smodelsLogging import logger

#logger = logging.getLogger(__name__)
#logger.setLevel(level=logging.INFO)

complaints = { "NoResultsFor": 0 }

class ProgressHandler:
    """ a namespace to handle everything around the progressbar """
    def storePid ( pid : int, pidfile : str = ".progressbar.pid" ):
        """ store the pid of the progress bar in .progressbar.pid,
        so the other process can kill it. """
        f=open(".progressbar.pid","wt")
        f.write ( f"{pid}\n" )
        f.close()

    def readPid ( pidfile : str = ".progressbar.pid" ) -> int:
        """ read the progressbar pid from the pid file """
        if not os.path.exists ( pidfile ):
            return None
        f=open(".progressbar.pid","rt")
        pid = int ( f.read() )
        f.close()
        return pid

    def rmFile ( pidfile : str = ".progressbar.pid" ):
        if os.path.exists ( pidfile ):
            try:
                os.unlink ( pidfile )
            except Exception as e:
                pass

    def killProgressBar ( pidfile : str = ".progressbar.pid" ):
        """ kill the progressbar """
        pid = ProgressHandler.readPid()
        if pid == None:
            return
        import psutil
        if psutil.pid_exists ( pid ):
            p = psutil.Process ( pid )
            p.terminate()
        ProgressHandler.rmFile()

def sha1sum(filename : os.PathLike ) -> str:
    """ get sha1 hash sums for the tarballs
    :returns: sha1 hashsum
    """
    import hashlib
    h  = hashlib.sha1() # 256 is safer but longer
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()

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

    def setSLHAdir(self,slhadir : str ):
        """
        Defines the folder or .tar.gz file containing all the slha files to be
        used to generate the validation plot

        :param slhadir: existing folder containing SLHA files
        """

        if not os.path.isdir(slhadir) and not os.path.isfile(slhadir):
            logger.error( f"SLHA files not found in {slhadir} for {str(self)}" )
            sys.exit()
        else:
            self.slhaDir = slhadir

    def topologyHasWidths ( self ):
        """ is this a topology with a width-dependency? """
        return "(" in self.axes

    def getOfficialCurves(self, get_all : bool = True,
            expected : bool = False ) -> Union[Dict,List]:
        """
        Reads the root file associated to the ExpRes and
        obtain the experimental exclusion curve for the corresponding TxName and Axes.

        :param get_all: get also the +- 1 sigma curves
        :param expected: if true, get expected instead of observed

        :return: a container of root TGraph objects
        """
        tgraphDict = getExclusionCurvesFor(self.expRes,txname=self.txName,
                       axes=self.axes, get_all = get_all, expected=expected )
        if not tgraphDict:
            return []
        tgraph = tgraphDict[self.txName]
        if len(tgraph)==0:
            return tgraph
        if get_all:
            return tgraph
        else:
            return [ tgraph[0] ]

    def getPlotFileName(self,validationDir : str, fformat : str = 'pdf') -> str:
        """
        Defines the name of the plot file and returns it

        :param validationDir: Folder where the plots and validation dictionaries
        will be saved
        :return: name of the plot file
        """

        if fformat.startswith("."):
            fformat = fformat[1:]

        filename = f"{self.expRes.globalInfo.id}_{self.txName}_"
        filename += self.niceAxes.replace(",","").replace("(","").replace(")","").\
                    replace("/","d")
        if self.combine:
            filename += '_combined'
        filename += f".{fformat}"

        filename = filename.replace(f"{self.expRes.globalInfo.id}_","")
        filename = os.path.join(validationDir,filename)
        filename = filename.replace("*","").replace(",","").replace("(","").replace(")","").replace("0.0","0").replace("1.0","1").replace("._","_")
        return filename

    def getSLHAdir(self) -> str:
        """
        Returns path to the folders containing the SLHA files.
        If slhadir is a .tar.gz file, returns a temporary folder where the files
        have been extracted to.

        :return: path to the folder containing the SLHA files
        """

        if os.path.isdir(self.slhaDir):
            self.currentSLHADir = self.slhaDir
            return self.slhaDir
        elif os.path.isfile(self.slhaDir):
            try:
                tar = tarfile.open(self.slhaDir,'r:gz')
                nfiles = 0
                tempdir = "?"
                if "tempdir" in self.options and self.options["tempdir"]!=None:
                    tdir =  self.options["tempdir"]
                    if "/" in tdir or "." in tdir:
                        logger.warning ( f"you supplied {tdir} as a tempdir, I have been expecting a name without a '/' or a '.', you have been warned" )
                    tempdir = os.path.join ( os.getcwd(), tdir )
                    nfiles = len(glob.glob(f"{tempdir}/T*slha")) + 2
                else:
                    tempdir = tempfile.mkdtemp(dir=os.getcwd())
                p1 = tempdir.rfind("/")
                stempdir = tempdir[p1+1:]
                logger.info ( f"tempdir: {GREEN}{stempdir}{RESET}" )
                members=tar.getmembers()
                nmembers = len(members)
                # logger.debug ( f"nfiles {nfiles} nmembers {nmembers}" )
                if nfiles >= nmembers:
                    logger.debug ( f"the slha files seem to already be there, returning {tempdir}" )
                    self.currentSLHADir = tempdir
                    self.pointsInTarFile = nmembers-2
                    return tempdir
                if nfiles > 3:
                    logger.warning ( f"we have {nfiles} files, should have {nmembers}. Lets explode the tarball!" )
                countm = 0
                for m in members:
                    if m.name.endswith ( ".slha" ):
                        countm += 1
                self.pointsInTarFile = countm
                random.shuffle ( members )
                #if self.limitPoints != None and self.limitPoints > 0:
                #    members=members[:self.limitPoints]
                tar.extractall(path=tempdir,members=members)
                tar.close()
                logger.debug(f"SLHA files extracted to {tempdir}" )
                self.currentSLHADir = tempdir
                commentfile = f"{tempdir}/comment"
                with open ( commentfile, "wt" ) as f:
                    d = { "npoints": countm }
                    f.write ( f"{str(d)}\n" )
                    f.close()
                return tempdir
            except Exception as e:
                logger.error(f"Could not extract SLHA files from {self.slhaDir}: {e}")
                sys.exit()
        else:
            logger.error(f"{self.slhaDir} is not a file nor a folder" )
            sys.exit()


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
        self.pprint ( f"saving to {YELLOW}{filename}{RESET}" )
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

        if self.pretty:
            from addLogoToPlots import addLogo
            #Print pdf, png and root formats
            filename = filename.replace(f".{fformat}",f"_pretty.{fformat}")
            logger.info ( f"saving to {YELLOW}{filename}{RESET}" )
            self.savefig ( filename )
            addLogo ( filename )
            newfilename = filename.replace(f".{fformat}",'.pdf')
            if self.options["pdfPlots"]:
               cmd = f"convert {filename} {newfilename}"
               import subprocess
               o = subprocess.getoutput ( cmd )
        else:
            self.savefig(filename)
            if fformat != "png":
                filename = filename.replace(f".{fformat}",'.png')
                try:
                    self.savefig(filename)
                except Exception as e:
                    # if fails because of missing dep, then just proceed
                    pass
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
            if deltay < 1e-17:
               logger.warn ( f"the range in y values {deltay} is quite small. let me make it a 1d plot!" )
               return True
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
        import os
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
                if f in [ "results", "coordinates", "comment", "recipe", "recipe.py" ]:
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
        if self.options["show"]:
            pid = os.fork()
            ## pid == 0 continues on
            if pid == 0:
                ProgressHandler.storePid ( os.getpid() )
                import time
                from progress import Progress
                time.sleep(5) ## wait a little
                dirs = [ self.outputDir.replace("/results","") ]
                p = Progress ( dirs = dirs )
                return
        modelTester.testPoints( self.willRun, inDir, outputDir, parser, self.db,
                               timeOut, False, parameterFile )
        self.removeFromListOfRunningFiles ( )
        ProgressHandler.killProgressBar()
        return fileList

    def pprint ( self, *args ):
        """ convenience """
        print ( f"[validationObjsBase]", *args )

    def addDictionaryForFailedPoint ( self, smodelsOutput : dict, axes ):
        """ a point has failed, no "ExptRes" is in smodelsOutput.
        create the dict that describes the failure.
        :returns: empty dictionary if axes not in plane
        """
        slhafile = os.path.basename ( smodelsOutput["OutputStatus"]["input file"] )
        folder = os.path.dirname ( smodelsOutput["OutputStatus"]["input file"] )
        if axes == None or len(axes)==0:
            return

        complaints["NoResultsFor"]+=1
        if complaints["NoResultsFor"]<4:
            logger.info( f"No results for {slhafile}" )
        if complaints["NoResultsFor"]==4:
            logger.info( f"(quenching more info msgs)" )

        Dict = { 'slhafile': slhafile, 'error': 'no result', 'axes': axes,
                 'comment': "no ExptRes in smodelsOutput" }
        if "OutputStatus" in smodelsOutput:
            if 'file status' in smodelsOutput["OutputStatus"]:
                Dict["file status"]=smodelsOutput["OutputStatus"]["file status"]
            if 'decomposition status' in smodelsOutput["OutputStatus"]:
                Dict["decomposition status"]=smodelsOutput["OutputStatus"]["decomposition status"]
            if "warnings" in smodelsOutput["OutputStatus"]:
                warning = smodelsOutput["OutputStatus"]["warnings"]
                warning = warning.replace( f"{folder}/", "" ).replace ( folder, "" )
                Dict["warnings"] = warning
        self.data.append ( Dict )

    def getWidthsFromSLHAFileName ( self, filename : str ) -> List:
        """ try to guess the mass vector from the SLHA file name
        :returns: mass vector
        """
        tokens = filename.replace(".slha","").split("_")
        if not tokens[0].startswith ( "T" ):
            self.pprint ( f"why does token 0 not start with a T??? {tokens[0]}" )
            sys.exit(-1)
        widths = []
        for t in tokens[1:]:
            try:
                v = float(t)
                widths.append ( v )
            except ValueError as e:
                pass
        ret = []
        for m in widths:
            if m>0. and m<1e-10:
                ret.append ( m )
        return ret

    def slhafileInData ( self, slhafile : str ) -> bool:
        """ is slhafile already in the data? """
        for d in self.data:
            slhashort = os.path.basename ( slhafile )
            if d["slhafile"] in [ slhafile, slhashort ]:
                return True
        return False

    def getMassesFromSLHAFileName ( self, filename : str ) -> List:
        """ try to guess the mass vector from the SLHA file name """
        tokens = filename.replace(".slha","").split("_")
        if not tokens[0].startswith ( "T" ):
            self.pprint ( f"why does token 0 not start with a T??? {tokens[0]}" )
            sys.exit(-1)
        masses = []
        for t in tokens[1:]:
            try:
                v = float(t)
                masses.append ( v )
            except ValueError as e:
                pass
        for m in masses:
            if m>0. and m<1e-10:
                continue
                # self.pprint ( "it seems there are widths in the vector. make sure we use them correctly." )
                # sys.exit()
        n=int(len(masses)/2)
        if len(masses) % 2 != 0:
            if "THSCPM7" in filename:
                n+=1 # for THSCPM7 we have [M1,M2,(M3,W3)],[M1,(M3,W3) ]
                ## so all works out if we just slice at one after the half
            elif not "T3GQ" in filename and not "T5GQ" in filename and not "T2Disp" in filename:
                self.pprint ( f"mass vector {masses} is asymmetrical. dont know what to do" )
            # sys.exit(-1)
        ret = [ masses[:n], masses[n:] ]
        if "T5GQ" in filename:
            ret = [ masses[:n+1], masses[n+1:] ]
        if "T2Disp" in filename:
            ret = [ masses[:2], masses[:2] ]
        return ret

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
            # f.write ( f"pyhfbackend = pytorch\n" )
            if self.options["keepTopNSRs"] not in  [ None, 0 ]:
                f.write ( "reportAllSRs = True\n" )
            sigmacut = 0.000000001
            minmassgap = 2.0
            minmassgapISR = 1.0
            maxcond = 1.0
            promptWidth=1.1
            if "sigmacut" in self.options:
                sigmacut = self.options["sigmacut"]
            if "minmassgap" in self.options:
                minmassgap = self.options["minmassgap"]
            if "minmassgapISR" in self.options:
                minmassgapISR = self.options["minmassgapISR"]
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
            f.write(f"[parameters]\nsigmacut = {sigmacut}\nminmassgap = {minmassgap}\n")
            f.write(f"minmassgapISR = {minmassgapISR}\nmaxcond = {maxcond}\nncpus = {self.ncpus}\n" )
            f.write(f"[database]\npath = {self.databasePath}\nanalyses = {expId}\ntxnames = {txname}\ndataselector = {dataselector}\n" )
            f.write(f"[printer]\noutputFormat = version{outputformat}\noutputType = python\n")
            f.write(f"[particles]\n")
            if not "share.models" in model and not model.endswith(".slha") and not "/" in model:
                model = f"share.models.{model}"
            f.write(f"model={model}\n" )
            f.write(f"promptWidth={promptWidth}\n" )
            expected = self.options["expectationType"]
            f.write( f"[python-printer]\naddElementList = False\ntypeOfExpectedValues={expected}\nprinttimespent=True\n")
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
            logger.warning("No data found." ) # Nothing will be saved")
            return False ## dont return false, as we might need to update meta

        if self.options["generateData"] in [ None, "ondemand" ]:
            nadded = self.loadData ( overwrite = False )
            logger.info ( f"loaded {len(self.data)} data points" )
            if nadded == 0:
                logger.warning("No additional points." ) #  Nothing will be saved")
                # return False # dont return false we might need to update meta

        validationDir = self.getValidationDir ( validationDir )

        if not datafile:
            datafile = self.getDataFile(validationDir)
        self.datafile = datafile
        lockfile = f"{datafile}.lock"
        self.lockFile ( lockfile )
        self.pprint ( f"saving {len(self.data)} points to {datafile}" )
        #Save data to file
        f = open(datafile,'w')
        dataStr = streamlineValidationData ( self.data )
        f.write(f"validationData = {dataStr}\n")
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
        if "style" in self.options:
            meta["style"]=self.options["style"]
        if os.path.isfile ( self.slhaDir ):
            ## currently we have sha1sums only for named tarballs
            meta["sha1for"] = os.path.basename ( self.slhaDir )
            meta["sha1"]=sha1sum ( self.slhaDir )
        if hasattr ( self.expRes.globalInfo, "includeCRs" ):
            meta["includeCRs"]=self.expRes.globalInfo.includeCRs
        if hasattr ( self.expRes.datasets[0].dataInfo, "thirdMoment" ):
            meta["thirdMoments"]=True
        if os.path.exists ( f"{validationDir}/../validation_commentary.txt" ):
            with open( f"{validationDir}/../validation_commentary.txt","rt") as f2:
                txt=f2.read().strip()
                f2.close()
                meta["commentary"]=txt
        if hasattr ( self.expRes.globalInfo, "resultType" ):
            meta["resultType"]=self.expRes.globalInfo.resultType
        if hasattr ( self, "getDataMap" ): # V3
            dm = self.getDataMap()
            dmn = {}
            for k,v in dm.items():
                unit = str(v[2])
                if unit == "1.00E+00 [GeV]":
                    unit = "GeV"
                if unit == "1.00E+00 [MeV]":
                    unit = "MeV"
                vn = ( v[0], v[1], unit )
                dmn[k]=vn
            meta["dataMap"] = dmn
        from smodels.base import runtime
        if type(runtime._experimental)==dict and "spey" in runtime._experimental and \
                runtime._experimental["spey"]==True:
            if self.expRes.datasets[0].dataInfo.dataId != None:
                import spey
                meta["spey"]=spey.__version__
        if hasattr ( self, "pointsInTarFile" ):
            meta["nmax"]=self.pointsInTarFile
        meta["host"]=hostname
        meta["nSRs"]=len ( self.expRes.datasets )
        if not hasattr ( self, "meta" ):
            self.meta = {}
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
        try:
            from smodels.base.runtime import experimentalFeature
            useTevatronCLs = experimentalFeature ( "tevatroncls" )
            asimovIsExpected = experimentalFeature ( "asimovisexpected" )
        except Exception as e:
            self.pprint ( f"experimentalFeature not yet available. its ok we can skip this" )
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
        # term = os.environ["TERM"]
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

    def computeWeight ( self, point ) -> float:
        """ compute the weight of a point by computing the area of its
        voronoi cell """
        if 0.<point[1]<1e-6:
            point[1]=rescaleWidth( point[1] )
        for i,hull in enumerate(self.hulls):
            if point_in_hull ( point, hull ):
                return self.volumes[i]
        return self.average_area


    def computeAgreementFactor ( self, looseness : float =1.2,
            signal_factor : float =1.0, weighted : bool = False ) -> float:
        """ computes how much the plot agrees with the official exclusion curve
        by counting the points that are inside/outside the official
        exclusion curve, and comparing against the points' r values
        ( upper limit / predict theory cross section )
        :param looseness: how much do we loosen the criterion? I.e. by what factor do we
               change the cross sections in favor of getting the right assignment?
        :param signal_factor: an additional factor that is multiplied with
               the signal cross section,
        :param weighted: weight the points with the areas of their Voronoi cells

        :returns: agreement factor
        """
        #import ROOT
        curve = self.getOfficialCurves( get_all = False, expected = False )
        if curve == []:
            logger.error( f"could not get official tgraph curve for {self.expRes.globalInfo.id} {self.txName} {self.axes}" )
            return 1.0
        curve = curve[0]
        if isinstance(curve,list):
            for c in curve:
                objName = c.GetName()
                if 'exclusion_' in objName:
                    curve = c
                    break

        from smodels_utils.helper.rootTools import completeROOTGraph
        completeROOTGraph ( curve )

        pts= { "total": 0, "excluded_inside": 0, "excluded_outside": 0,
               "not_excluded_inside": 0, "not_excluded_outside": 0, "wrong" : 0 }

        self.computeHulls()

        for point in self.data:
            if "error" in point.keys():
                continue
            x,y=None, None
            try: ## we seem to have two different ways of writing the x,y values
                x=point["axes"]['x']
                y=point["axes"]['y']
            except Exception as e:
                pass
            try:
                x,y=point["axes"][0],point["axes"][1]
            except Exception as e:
                pass
            if x == None or y == None:
                continue
            w = 1.
            if weighted:
                w = self.computeWeight ( [x,y] )
            if y==0: y=1.5 ## to avoid points sitting on the line
            if point["UL"]==None:
                continue
            excluded = point["UL"] < point["signal"]
            really_excluded = looseness * point["UL"] < point["signal"] * signal_factor
            really_not_excluded = point["UL"] > looseness * point["signal"] * signal_factor
            from smodels_utils.helper.rootTools import exclusionCurveToTGraph
            rcurve = exclusionCurveToTGraph ( curve )
            inside = rcurve.IsInside ( x, y )
            pts["total"]+=w
            s=""
            if excluded:
                s="excluded"
            else:
                s="not_excluded"
            if inside:
                s+="_inside"
            else:
                s+="_outside"
            pts[s]+=w
            if really_excluded and not inside:
                pts["wrong"]+=w
            if really_not_excluded and inside:
                pts["wrong"]+=w
        if pts["total"]==0:
            return float("nan")
        return 1.0 - float(pts["wrong"]) / float(pts["total"])

    def computeHulls ( self ):
        """ compute the convex hulls from the Voronoi
            partition, so we can later weight points with the areas of the
            Voronoi cell """
        if not self.options["weightedAgreementFactor"]: #  self.weightedAF:
            return
        # we could weight the point with the area of its voronoi partition
        points = []
        for point in self.data:
            try: ## we seem to have two different ways of writing the x,y values
                x,y=point["axes"]['x'],point["axes"]['y']
            except Exception as e:
                x,y=point["axes"][0],point["axes"][1]
            points.append ( [x,y] )
        xy=numpy.array ( points )
        logY=False
        if max ( xy[::,1] ) < 1e-6:
            logY=True
            points = [ [ x,rescaleWidth(y) ] for x,y in points ]

        from scipy.spatial import Voronoi, ConvexHull
        vor = Voronoi ( points )
        ## FIXME now get the bounding box of a point, then
        ## get the area of the bounding box. weight the points with that area.
        # now check for [ 1700. -15. ]
        self.hulls = []
        self.volumes = []
        totalarea = 0.
        n_points = 0
        for i, reg_num in enumerate(vor.point_region):
            indices = vor.regions[reg_num]
            if not (-1 in indices): # s me regions can be opened
                hull = ConvexHull(vor.vertices[indices])
                n_points += 1
                self.hulls.append ( hull )
                vol = hull.volume
                self.volumes.append ( vol )
                totalarea += vol
        self.average_area = totalarea / n_points


    def getDataFile(self,validationDir : str,fformat : str ='pdf') -> str:
        """
        Defines the name of the .py file and returns it

        :param validationDir: Folder where the root file will be saved

        :return: name of the .py file
        """
        if fformat.startswith("."):
            fformat = fformat[1:]
        datafile = self.getPlotFileName(validationDir,fformat)
        datafile = datafile.rstrip(fformat)
        if not datafile.endswith ( "." ):
            datafile += "."
        return f"{datafile}py"
