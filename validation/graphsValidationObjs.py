#!/usr/bin/env python3

"""
.. module:: validationObjs
   :synopsis: Main classes and methods for generating a single validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,time,math,numpy,copy,random

logger = logging.getLogger(__name__)
from smodels.base.physicsUnits import GeV
from smodels.matching import modelTester
from smodels_utils.helper.various import round_to_n
from typing import Union, Dict
try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth, \
         rescaleWidth, addUnit
except:
    from backwardCompatibility import addUnit, rescaleWidth

from plottingFuncs import getExclusionCurvesFor
from validationHelpers import point_in_hull
import tempfile,tarfile,shutil,copy
from smodels_utils.dataPreparation.graphMassPlaneObjects import GraphMassPlane
from smodels.experiment.exceptions import SModelSExperimentError as SModelSError
from smodels.experiment.databaseObj import Database
from sympy import var
import pyslha
import string
import glob

logger.setLevel(level=logging.ERROR)

class ValidationPlot():
    """
    Encapsulates all the data necessary for creating a single validation plot.

    :ivar ExptRes: ExpResult object containing the experimental result for validation
    :ivar TxNameStr: String describing the txname (e.g. T2tt)
    :ivar Axes: String describing the axes (e.g. 2*Eq(mother,x)_Eq(lsp,y))
    :ivar slhadir: path to the SLHA folder or the tar ball containing the files (string)
    :ivar databasePath: path to the database folder. If not defined, the path from ExptRes.path will be
                        used to extract the database path.
    :ivar kfactor: Common kfactor to be applied to all theory cross-sections (float)
    :ivar limitPoints: limits tested model points to n randomly chosen ones.
                   If None or negative, take all points.
    :ivar extraInfo: add additional info to plot: agreement factor, time spent,
                      time stamp, hostname
    :ivar preliminary: if true, write "preliminary" over the plot
    """

    def __init__( self, ExptRes, TxNameStr : str, Axes, db : Database, slhadir=None,
            databasePath=None, options : dict = {}, kfactor = 1.,
            namedTarball = None, keep = False, combine = False ):
        """
        :param namedTarball: if not None, then this is the name of the tarball explicitly specified in Txname.txt
        :param keep: keep temporary directories
        """
        self.expRes = copy.deepcopy(ExptRes)
        self.db = db
        self.keep = keep
        self.t0 = time.time()
        self.options = options
        self.txName = TxNameStr
        self.namedTarball = namedTarball
        self.axes = Axes.strip()
        self.massPlane = GraphMassPlane.fromString(self.txName,self.axes)
        self.niceAxes = self.getNiceAxes(Axes.strip())
        self.slhaDir = None
        self.currentSLHADir = None
        self.outputDir = None # define an output directory
        self.data = []
        self.validationType = "unknown"
        drawExpected = self.options["drawExpected"]
        self.officialCurves = self.getOfficialCurves( get_all = not drawExpected,
                expected = False )
        self.expectedOfficialCurves = self.getOfficialCurves( get_all = False,
                expected = True )
        self.kfactor = kfactor
        self.combine = combine

        #Select the desired txname and corresponding datasets in the experimental result:
        for dataset in self.expRes.datasets:
            dataset.txnameList = [tx for tx in dataset.txnameList[:] if tx.txName == self.txName]
        self.expRes.datasets = [dataset for dataset in self.expRes.datasets[:] if len(dataset.txnameList) > 0]

        if slhadir: self.setSLHAdir(slhadir)
        if databasePath:
            if os.path.isdir(databasePath):
                self.databasePath = databasePath
            else:
                logger.error("Database folder "+databasePath+" does not exist")
                sys.exit()
        #Try to guess the path:
        else:
            anaID = ExptRes.globalInfo.id
            self.databasePath = ExptRes.path[:ExptRes.path.find('/'+anaID)]
            self.databasePath = self.databasePath[:self.databasePath.rfind('/')]
            self.databasePath = self.databasePath[:self.databasePath.rfind('/')+1]
            if not os.path.isdir(self.databasePath):
                logger.error("Could not define databasePath folder")
                sys.exit()

        import plottingFuncs ## propagate logging level!
        plottingFuncs.logger.setLevel ( logger.level )
        self.specialInits()

    def specialInits ( self ):
        """ inits for the subclass """
        self.validationType = "unknown"

    def __str__(self):
        axes = self.axes
        axes = axes.replace(",","").replace("{","").replace("}","").\
                    replace(":","").replace("'","").replace(" ","")
        vstr = f"{self.expRes.globalInfo.id}:{self.txName}_{axes}"
        """
        vstr = "Validation plot for\n"
        vstr += 'id: %s\n' % self.expRes.globalInfo.id
        vstr += 'TxName: '+self.txName+'\n'
        vstr += 'Axes: '+self.axes
        """
        return vstr

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

    def computeWeight ( self, point ):
        """ compute the weight of a point by computing the area of its voronoi cell """
        if 0.<point[1]<1e-6:
            point[1]=rescaleWidth( point[1] )
        for i,hull in enumerate(self.hulls):
            if point_in_hull ( point, hull ):
                return self.volumes[i]
        return self.average_area

    def computeAgreementFactor ( self, looseness=1.2, signal_factor=1.0,
                                 weighted = False ):
        """ computes how much the plot agrees with the official exclusion curve
            by counting the points that are inside/outside the official
            exclusion curve, and comparing against the points' r values
            ( upper limit / predict theory cross section )
            :param looseness: how much do we loosen the criterion? I.e. by what factor do we
                   change the cross sections in favor of getting the right assignment?
            :param signal_factor: an additional factor that is multiplied with
                   the signal cross section,
            :param weighted: weight the points with the areas of their Voronoi cells

        """
        #import ROOT
        curve = self.getOfficialCurves( get_all = False, expected = False )
        if curve == []:
            logger.error( "could not get official tgraph curve for %s %s %s" % ( self.expRes.globalInfo.id,self.txName,self.axes  ) )
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

    def setSLHAdir(self,slhadir):
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

    def getSLHAdir(self):
        """
        Returns path to the folders containing the SLHA files.
        If slhadir is a .tar.gz file, returns a temporary folder where the files
        have been extracted to.

        :param slhadir: path to the SLHA folder or the tar ball containing the files (string)
        :return: path to the folder containing the SLHA files
        """

        if os.path.isdir(self.slhaDir):
            self.currentSLHADir = self.slhaDir
            return self.slhaDir
        elif os.path.isfile(self.slhaDir):
            try:
                tar = tarfile.open(self.slhaDir,'r:gz')
                if "tempdir" in self.options and self.options["tempdir"]!=None:
                    tdir =  self.options["tempdir"]
                    if "/" in tdir or "." in tdir:
                        logger.warning ( f"you supplied {tdir} as a tempdir, I have been expecting a name without a '/' or a '.', you have been warned" )
                    tempdir = os.path.join ( os.getcwd(), tdir )
                else:
                    tempdir = tempfile.mkdtemp(dir=os.getcwd())
                members=tar.getmembers()
                countm = 0
                for m in members:
                    if m.name.endswith ( ".slha" ):
                        countm += 1
                self.pointsInTarFile = countm
                random.shuffle ( members )
                limitPoints = self.options["limitPoints"]
                if limitPoints != None and limitPoints > 0:
                    members=members[:limitPoints]
                tar.extractall(path=tempdir,members=members)
                tar.close()
                logger.debug("SLHA files extracted to %s" %tempdir)
                self.currentSLHADir = tempdir
                return tempdir
            except Exception as e:
                logger.error("Could not extract SLHA files from %s: %s" %\
                              ( self.slhaDir, e ) )
                sys.exit()
        else:
            logger.error("%s is not a file nor a folder" %self.slhaDir)
            sys.exit()

    def getOfficialCurves(self, get_all=True, expected = False ):
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

    def getParameterFile(self,tempdir=None):
        """
        Creates a temporary parameter file to be passed to runSModelS

        :param tempdir: Temporary folder where the parameter file will be created. Default = current folder.
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
            logger.warning ( f"weird, parameter file {parFile} already exists?" )
            parFile = tempfile.mktemp(dir=tempdir,prefix='parameter_',suffix='.ini', text=True )
        pf = open ( parFile, "wt" )

        combine = "False"
        if self.combine:
            combine = "True"
            self.validationType="combine"
        model = self.options["model"]
        if model in [ "mssm", "idm", "nmssm", "dgmssm" ]:
            model = f"share.models.{model}"
        if model == "default":
            ## FIXME here we could define different defaults for eg T5Gamma
            model = "share.models.mssm"
            slhapath = tempdir.replace("/results","")
            files = list ( glob.glob( os.path.join ( slhapath,"*.slha" ) ) )
            if len(files)>0: ## use slha file as model
                model = files[0]
        with open ( parFile, "w" ) as f:
            f.write("[options]\ninputType = SLHA\ncheckInput = True\ndoInvisible = True\ndoCompress = True\ncomputeStatistics = True\ntestCoverage = False\ncombineSRs = %s\n" % combine )
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
            f.write(f"[parameters]\nsigmacut = {sigmacut}\nminmassgap = {minmassgap}\nmaxcond = {maxcond}\nncpus = {self.ncpus}\n" )
            f.write(f"[database]\npath = {self.databasePath}\nanalyses = {expId}\ntxnames = {txname}\ndataselector = all\n" )
            f.write("[printer]\noutputFormat = version3\noutputType = python\n")
            f.write(f"[particles]\nmodel={model}\npromptWidth={promptWidth}\n" )
            #expected = "posteriori"
            #expected = "priori"
            expected = self.options["expectationType"]
            f.write( f"[python-printer]\naddElementList = False\ntypeOfExpectedValues='{expected}'\nprinttimespent=True\naddNodesMap=True\n")
            f.close()
        # os.close(pf)
        pf.close()
        return parFile

    def loadData(self, overwrite = True ):
        """
        Tries to load an already existing python output.
        :param overwrite:  if True, then overwrite any existing data
        :returns: number of points added
        """

        validationDir = self.getValidationDir ( None )
        datafile = self.getDataFile(validationDir)
        if not os.path.isfile(datafile):
            if self.options["generateData"] == False:
                logger.error("Validation datafile %s not found" %datafile)
            else:
                logger.info("Validation datafile %s not found" %datafile)
            if overwrite:
                self.data = []
            return
        nprev = len(self.data)

        from validationHelpers import getValidationFileContent
        content = getValidationFileContent ( datafile )
        if overwrite:
            self.data = []
        slhafiles = { x["slhafile"] : x for x in self.data }
        ctadded = 0
        for d in content["data"]:
            if d["slhafile"] in slhafiles:
                if d != slhafiles[d["slhafile"]]:
                    logger.error ( f"entry {d['slhafile']} changed content {d} != {slhafiles[d]}" )
                continue
            ctadded+=1
            self.data.append ( d )
        try:
            self.data.sort ( key = lambda x: x["axes"]["x"]*1e6 + x["axes"]["y"] )
        except:
            def getKey ( x ):
                if not "axes" in x or x["axes"] is None or not "x" in x["axes"]:
                    return -1e9
                return x["axes"]["x"]
            self.data.sort ( key = lambda x: getKey ( x ) )
        self.meta = content["meta"]
        if self.meta is None:
            self.meta = {}
        addedpoints = len(self.data)
        if not overwrite:
            logger.info ( f"merging old data with new: {nprev}+{len(content['data'])}={len(self.data)}" )
            if not "runs" in self.meta:
                self.meta["runs"]=f"{len(self.data)}"
            else:
                prev = eval ( self.meta["runs"] )
                addedpoints = len(self.data)-prev
                self.meta["runs"]=self.meta["runs"]+"+"+f"{addedpoints}"
        # self.data = content["data"]
        ndata = 0
        if self.data != None:
            ndata = len ( self.data )
        self.meta["npoints"] = ndata
        return addedpoints

    def getWidthsFromSLHAFileName ( self, filename ):
        """ try to guess the mass vector from the SLHA file name """
        tokens = filename.replace(".slha","").split("_")
        if not tokens[0].startswith ( "T" ):
            print ( "why does token 0 not start with a T??? %s" % tokens[0] )
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

    def getMassesFromSLHAFileName ( self, filename ):
        """ try to guess the mass vector from the SLHA file name """
        tokens = filename.replace(".slha","").split("_")
        if not tokens[0].startswith ( "T" ):
            print ( "why does token 0 not start with a T??? %s" % tokens[0] )
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
                # print ( "[validationObjs] it seems there are widths in the vector. make sure we use them correctly." )
                # sys.exit()
        n=int(len(masses)/2)
        if len(masses) % 2 != 0:
            if "THSCPM7" in filename:
                n+=1 # for THSCPM7 we have [M1,M2,(M3,W3)],[M1,(M3,W3) ]
                ## so all works out if we just slice at one after the half
            elif not "T3GQ" in filename and not "T5GQ" in filename and not "T2Disp" in filename:
                print ( "[validationObjs] mass vector %s is asymmetrical. dont know what to do" % masses )
            # sys.exit(-1)
        ret = [ masses[:n], masses[n:] ]
        if "T5GQ" in filename:
            ret = [ masses[:n+1], masses[n+1:] ]
        if "T2Disp" in filename:
            ret = [ masses[:2], masses[:2] ]
        return ret

    def topologyHasWidths ( self ):
        """ is this a topology with a width-dependency? """
        return "(" in self.axes

    def slhafileInData ( self, slhafile : str ) -> bool:
        """ is slhafile already in the data? """
        for d in self.data:
            slhashort = os.path.basename ( slhafile )
            if d["slhafile"] in [ slhafile, slhashort ]:
                return True
        return False

    def runSModelS ( self ) -> list:
        """ run SModelS proper """
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
                bf = os.path.basename ( f )
                if self.slhafileInData ( bf ):
                    countSkipped += 1
                else:
                    tmp.append ( f )
            if countSkipped > 0:
                logger.info ( f"skipped a total of {countSkipped} points: generateData was set to 'ondemand'." )
            fileList = tmp
        else:
            self.data = []

        #Set temporary outputdir:
        outputDir = os.path.join ( self.currentSLHADir, "results" )
        if os.path.exists ( outputDir ):
            logger.warning ( f"weird, {outputDir} already exists?" )
            outputDir = tempfile.mkdtemp(dir=self.currentSLHADir,prefix='results_')
        else:
            os.mkdir ( outputDir )
        self.outputDir = outputDir

        #Get parameter file:
        parameterFile = self.getParameterFile(tempdir=outputDir)
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
        modelTester.testPoints(fileList, inDir, outputDir, parser, self.db,
                               timeOut, False, parameterFile )
        return fileList

    def getDataMap ( self ):
        """ obtain the correct data map, i.e. the one corresponding to
        our txname """
        ds = self.expRes.datasets[0]
        ## FIXME need to search
        for txn in ds.txnameList:
            if txn.txName == self.txName:
                return txn.dataMap
        return None

    def getSmsMap ( self ):
        """ obtain the correct sms map, i.e. the one corresponding to
        our txname """
        ds = self.expRes.datasets[0]
        ## FIXME need to search
        for txn in ds.txnameList:
            if txn.txName == self.txName:
                return txn.smsMap
        return None

    def getTxname ( self ):
        """ obtain the correct sms/axes/data maps, i.e. the ones corresponding to
        our txname """
        ds = self.expRes.datasets[0]
        ## FIXME need to search
        for txn in ds.txnameList:
            if txn.txName == self.txName:
                return txn
        return None

    def constructParameterVector ( self, masses : list, widths : list,
            nodesMap : dict ) -> list:
        """ given the knowledge of the dataMap, construct the
        container of parameters to be fed into the graphs map """
        dataMap = self.getDataMap()
        ret=[float("nan")]*len(dataMap)
        for index,info in dataMap.items():
            ## index is the index in the final parameters vector
            nodeIndex = info[0]
            ## info in dataMap is, e.g.: (1,'mass',GeV)
            nodeName = nodesMap[nodeIndex]
            ret[index] = self.getNodeParameter ( nodeName, masses, widths, info[1] )
        # import IPython; IPython.embed( colors = "neutral" ); sys.exit()
        return ret

    def getNodeParameter ( self, nodeName : str, masses : list, widths : list,
                           parameterType : str ) -> Union[float,None]:
        """ get the parameter value for node "nodeName", given the masses,
        the widths, and knowledge about the parameterType """
        if parameterType in [ "width", "totalwidth" ]:
            for k,v in widths:
                if k==nodeName:
                    return v
            return None
        if parameterType=="mass":
            for k,v in masses:
                if k==nodeName:
                    return v
            return None
        return None

    def getXYFromSLHAFileName ( self, slhafile : str, asDict : bool ) -> Dict:
        """ for compatibility only.
        """
        D = self.getAxesFromSLHAFileName ( slhafile )
        if asDict:
            return D
        return [ D["x"], D["y"] ]


    def getAxesFromSLHAFileName ( self, slhafile : str ) -> Dict:
        """ get the axes dictionary from the slha filename alone.
        meant for points that did not produce any smodels output.

        :param slhafile: the slha filename, e.g. TChiWH_400_200_400_200.slha
        :returns: dictionary of axes, e.g. { "x": 400, "y": 200 }
        """
        logger.debug ( f"need to find axes for {slhafile} ({self.axes})" )
        axesDict = eval ( self.axes )
        from sympy.parsing.sympy_parser import parse_expr
        from sympy import solve, var, Eq
        x,y,z,w = var ( "x y z w" )

        for nr, expr in axesDict.items():
            axesDict[nr]=parse_expr ( expr )
        D = {}
        def equal ( val1 : Union[str,float], val2 : Union[str,float] ) -> bool:
            val1, val2 = float(val1), float(val2)
            if val1 == val2 == 0.:
                return True
            r = abs(val1-val2)/abs(val1+val2)
            return r < 1e-5
        barename = slhafile.replace(".slha","")
        tokens = barename.split("_")
        txname, numbers = tokens[0], tokens[1:]
        eqs = set()
        if len(axesDict) == len(numbers):
            for nr, expr in axesDict.items():
                eqs.add ( Eq( expr, float ( numbers[nr] ) ) )
        d = solve ( eqs )
        if type(d)==dict and len(d)>0:
            for k,v in d.items():
                D[str(k)]=round_to_n(float(v),5)
            return D
        # print ( f"@@axesDict {axesDict} {slhafile}" )
        if len ( tokens ) == 7 and equal ( tokens[1], tokens[4]) and \
                equal ( tokens[3], tokens[6] ) and \
                abs ( float(tokens[1])+float(tokens[3]) - 2*float(tokens[2])) < 1.5 \
                and Eq ( axesDict[1], .5*x+.5*y )==True:
            # e.g. TChiWH_400_300_200_400_300_200.slha
            ## account for rounding
            D = { "x": round_to_n(float(tokens[1]),5),
                  "y": round_to_n(float(tokens[3]),5) }
        """
        if len ( tokens ) == 5 and equal ( tokens[1], tokens[3]) and \
                equal ( tokens[2], tokens[4] ):
            # e.g. TChiWH_400_200_400_200.slha
            D = { "x": float(tokens[1]), "y": float(tokens[2]) }


        if len ( tokens ) == 7 and equal ( tokens[3], 60.) and \
                equal ( tokens[1], tokens[4] ) and \
                equal ( tokens[2], tokens[5] ) and \
                sympy.Eq ( self.axesDict[2], 60. ):
            # e.g. TChiWH_400_300_60_400_300_60.slha
            D = { "x": float(tokens[1]), "y": float(tokens[2]) }
        """

        # print ( f"@@A getAxesFromSLHAFileName: slhafile={slhafile} D={D}" )
        # print ( f"@@A self.axes {self.axes} {type(self.axes)}" )
        #import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

        return D

    def getDataFromPlanes(self):
        """
        Runs SModelS on the SLHA files from self.slhaDir and store
        the relevant data in self.data.
        Uses runSModelS.main.
        Result is stored in self.data
        """
        #Get list of SLHA files:
        if not self.slhaDir:
            logger.warning("SLHA folder not defined")
            return False

        # first, run SModelS
        fileList = self.runSModelS()

        #Define original plot
        massPlane = GraphMassPlane.fromString(self.txName,self.axes)
        if massPlane == None:
            logger.error ( "no mass plane!" )
            return False
        #Now read the output and collect the necessary data
        slhafiles= os.listdir(self.currentSLHADir)
        ct_nooutput=0
        slhafiles.sort() ## make sure we also go in the same order
        myglobals = globals()
        myglobals["inf"]=float("inf")
        myglobals["nan"]=float("nan")
        for slhafile in fileList: # slhafiles:
            if "recipe" in slhafile:
                continue
            if "coordinates" in slhafile:
                continue
            if not os.path.isfile(os.path.join(self.currentSLHADir,slhafile)):  #Exclude the results folder
                continue
            fout = os.path.join(self.outputDir,slhafile + '.py')
            if not os.path.isfile(fout):
                if ct_nooutput>4:
                    ## suppress subsequently same error messages
                    continue
                logger.error("No SModelS output found for %s (should be %s)" % \
                              ( slhafile, fout ) )
                ct_nooutput+=1
                if ct_nooutput==5:
                    logger.error("did not find SModelS output 5 times subsequently. Will quench error msgs from now on.")
                continue
            # print ( "reading %s" % fout )
            ff = open(fout,'r')
            txt = ff.read()
            cmd = txt.replace('\n','') # .replace("inf,","float('inf'),")
            exec( cmd, myglobals )
            ff.close()
            if not 'ExptRes' in smodelsOutput:
                logger.info( f"No results for {slhafile}" )
                axes = self.getAxesFromSLHAFileName ( slhafile )
                if len(axes)==0: # drop it, doesnt fall in this plane it seems
                    continue
                D = { "slhafile": slhafile, "error": "no result here",
                      "axes": axes }
                self.data.append ( D )
                continue
            dt = None
            if "OutputStatus" in smodelsOutput and "time spent" in smodelsOutput["OutputStatus"]:
                dt = smodelsOutput["OutputStatus"]["time spent"]
            res = smodelsOutput['ExptRes']
            expRes = res[0]
            #Double checks (to make sure SModelS ran as expected):
            leadingDSes = {}
            if len(res) != 1:
                logger.debug("Wait. We have multiple dataset Ids. Lets see if there is a combined result." )
                found_combined=False
                for eR in res:
                    if eR == None:
                        continue
                    if "combined" in eR["DataSetID"]:
                        logger.debug ( "found a combined result. will use it." )
                        found_combined=True
                        expRes = eR
                if self.options["keepTopNSRs"] not in [ None, 0 ]:
                    maxR, expRes = -1., None
                    for eR in res:
                        if "r_expected" in eR:
                            r = eR["r_expected"]
                            while r in leadingDSes: # make sure it's unique
                                r = r * .9999
                            leadingDSes[r]=eR["DataSetID"]
                            if r>maxR:
                                maxR = eR["r_expected"]
                                expRes = eR
                if not found_combined and self.options["keepTopNSRs"] in [ None, 0 ]:
                    logger.warning("We have multiple dataset ids, but none is a combined one. Dont know what to do." )
                    return False
            if expRes['AnalysisID'] != self.expRes.globalInfo.id:
                logger.error("Something went wrong. Obtained results for the wrong analyses: {expRes['AnalysisID']}!={self.expRes.globalInfo.id}")
                sys.exit(-1)
                # return False
            if self.txName != expRes['TxNames'][0] or len(expRes['TxNames']) != 1:
                logger.error(f"Something went wrong. Obtained results for the wrong txname: {self.txName} != {expRes['TxNames']}")
                sys.exit()
                continue
                # return False

            masses = expRes["Mass (GeV)"]
            widths = expRes["Width (GeV)"]
            nodesMap = expRes["Nodes Map"]
            parameters = self.constructParameterVector ( masses, widths, nodesMap )
            varsDict = massPlane.getXYValues( parameters )
            if varsDict is None:
                logger.debug( f"dropping {slhafile}, doesnt fall into the plane of {massPlane}." )
                continue
            if type(dt) == str:
                if dt.endswith("s"):
                    dt=dt[:-1]
                dt=float(dt)
            Dict = {'slhafile' : slhafile, 'axes' : varsDict,
                    'signal': expRes['theory prediction (fb)'],
                    'UL': expRes['upper limit (fb)'], 'condition': expRes['maxcond'],
                    'dataset': expRes['DataSetID'] }
            if type(dt)==float:
                Dict["t"]=round(dt,3) ## in seconds
            if len(leadingDSes)>1:
                s = []
                n = self.options["keepTopNSRs"]
                for k,v in sorted ( leadingDSes.items(), reverse=True )[:n]:
                    s.append ( (k,v) )
                Dict["leadingDSes"]= s
            if "l_max" in expRes and "likelihood" in expRes:
                Dict["llhd"]= round_to_n ( expRes["likelihood"], 4 )
                Dict["lmax"]= round_to_n ( expRes["l_max"], 4 )
                if not "chi2" in expRes:
                    try:
                        from smodels.tools.statistics import chi2FromLmax
                        Dict["chi2"] = round_to_n ( chi2FromLmax ( expRes["likelihood"], expRes["l_max"] ), 3 )
                    except Exception as e:
                        pass # not strictly necessary
            if "chi2" in expRes and expRes["chi2"] != None:
                Dict["chi2"] = round_to_n ( expRes["chi2"], 3 )
            if 'expected upper limit (fb)' in expRes:
                Dict['eUL']=expRes["expected upper limit (fb)"]
                drawExpected = self.options["drawExpected"]
                if drawExpected == "auto":
                    drawExpected = True
                self.options["drawExpected"]=drawExpected
            if "efficiency" in expRes.keys():
                Dict["efficiency"] = round ( expRes['efficiency'], 8 )
            if expRes['dataType'] == 'efficiencyMap':
                #Select the correct dataset (best SR):
                dataset = [dset for dset in self.expRes.datasets if dset.dataInfo.dataId == expRes['DataSetID']]
                if len(dataset)==1:
                    dataset = dataset[0]
                else: ## probably the combined case. we take any dataset.
                    dataset = self.expRes.datasets[0]

                txname = [tx for tx in dataset.txnameList if tx.txName == expRes['TxNames'][0]][0]
                if not "efficiency" in Dict.keys():
                    try:
                        eff = txname.txnameData.getValueFor(parameters)
                        if eff != None:
                            Dict['efficiency'] = round ( eff, 8 )
                    except SModelSError as e:
                        logger.error ( f"could not handle {slhafile}: {e}" )
                        Dict=None
            logger.debug('expres keys : {}'.format(expRes.keys()))
            if 'best combination' in expRes.keys():
                Dict['best combination'] = expRes['best combination']

            if Dict:
                self.data.append(Dict)

        #Remove temporary folder
        if self.currentSLHADir != self.slhaDir and not self.keep:
            shutil.rmtree(self.currentSLHADir)

        if self.data == []:
            logger.error("There is no data for %s/%s/%s.\n Are the SLHA files correct? Are the constraints correct?"
                          %(self.expRes.globalInfo.id,self.txName,self.axes))

        #Apply k-factors to theory prediction (default is 1)
        for ipt,pt in enumerate(self.data):
            if "error" in pt.keys():
                continue
            pt['signal'] *= self.kfactor
            self.data[ipt] = pt
            self.data[ipt]['kfactor'] = self.kfactor

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
                ys.append ( pt["axes"]["y"] )
        if len(ys)>0:
            deltay = max(ys)-min(ys)
            if deltay < 1e-14:
               logger.warn ( f"the range in y values {deltay} is quite small. sure you dont want to make a 1d plot? if yes, say forceOneD = True, in the options section in the ini file." )
        return False

    def getUglyPlot(self,silentMode=True):
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

    def getPrettyPlot(self,silentMode=True):
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

    def show ( self, filename ):
        """ we were asked to also show <filename> """
        term = os.environ["TERM"]
        if not self.options["show"] or not term == "xterm-kitty":
            return
        import subprocess, distutils.spawn
        for viewer in [ "timg", "see", "display" ]:
            v = distutils.spawn.find_executable( viewer )
            if not v:
                continue
            if viewer == "timg" and term == "xterm-kitty":
                v += " -p kitty "
            cmd = f"{v} {filename}"
            o = subprocess.getoutput ( cmd )
            print ( f"{cmd}" )
            print ( f"{o}" )
            return

    def savefig ( self, filename ):
        """ save the figure, never mind if root or matplotlib """
        if hasattr ( self.plot, "Print" ):
            self.plot.Print(filename)
        if hasattr ( self.plot, "savefig" ):
            self.plot.savefig(filename)

    def toPdf ( self, validationDir=None ):
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

    def savePlot(self,validationDir=None,fformat='png'):
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
            logger.info ( f"saving plot in {filename}" )
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
            self.savefig ( filename )
            addLogo ( filename )
            newfilename = filename.replace('.'+fformat,'.pdf')
            if self.options["pdfPlots"]:
               cmd = f"convert {filename} {newfilename}"
               import subprocess
               o = subprocess.getoutput ( cmd )
            """
            logger.debug ( "saving plot in %s (and pdf and root)" % filename )
            self.savefig ( filename )
            addLogo ( filename )
            #filename = filename.replace('.png','.root')
            #self.savefig ( filename )
            # addLogo ( filename )
            """
        self.show ( filename )

        return True

    def getValidationDir ( self, validationDir ):
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

    def saveData(self,validationDir=None,datafile=None):
        """
        Saves the data and plot in a text file in the validationDir folder.
        If the folder does not exist, it will be created.
        If the folder is not defined the plot will be created in the
        analysis/validation/ folder
        If datafile is not define, uses the default naming (Txname_axes.py)

        :param validationDir: Folder where the root file will be saved
        :param datafile: Name of the data file
        """

        if not hasattr(self,'data') or not self.data:
            logger.warning("No data found. Nothing will be saved")
            return False

        if self.options["generateData"] in [ None, "ondemand" ]:
            nadded = self.loadData ( overwrite = False )
            print ( "[validationObjs] loaded", len(self.data) )
            if nadded == 0:
                logger.warning("No added points. Nothing will be saved")
                return False

        validationDir = self.getValidationDir ( validationDir )

        if not datafile:
            datafile = self.getDataFile(validationDir)
        self.datafile = datafile
        print ( f"[validationObjs] saving {len(self.data)} points to {datafile}" )
        #Save data to file
        f = open(datafile,'w')
        dataStr = str(self.data)
        dataStr = dataStr.replace('[fb]','*fb').replace('[pb]','*pb')
        dataStr = dataStr.replace('[GeV]','*GeV').replace('[TeV]','*TeV')
        dataStr = dataStr.replace( "}, {" , "},\n{" )
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
        f.write("meta = %s\n" % str(meta) )
        f.close()

        return True

    def getDataFile(self,validationDir,fformat='pdf'):
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
        return datafile+'py'

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
        filename = filename.replace("*","").replace(",","").replace("(","").replace(")","").replace("0.0","0").replace("1.0","1")
        return filename

    def getNiceAxes(self,axesStr):
        """
        Convert the axes definition format ('[[x,y],[x,y]]')
        to a nicer format ('Eq(MassA,x)_Eq(MassB,y)_Eq(MassA,x)_Eq(MassB,y)')

        :param axesStr: string defining axes in the old format

        :return: string with a nicer representation of the axes (more suitable for printing)
        """
        return self.massPlane.getNiceAxes ( axesStr )
