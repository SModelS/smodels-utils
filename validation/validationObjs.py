#!/usr/bin/env python3

"""
.. module:: validationObjs
   :synopsis: Main classes and methods for generating a single validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,time,math,numpy,copy,ctypes,random

logger = logging.getLogger(__name__)
from smodels.tools.physicsUnits import GeV
from smodels.tools import modelTester
try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth,addUnit
except:
    from backwardCompatibility import addUnit,rescaleWidth

from plottingFuncs import getExclusionCurvesFor
from prettyPlots import createPrettyPlot
from uglyPlots import createUglyPlot
import tempfile,tarfile,shutil,copy
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels.experiment.exceptions import SModelSExperimentError as SModelSError
from sympy import var
import pyslha
import string

logger.setLevel(level=logging.ERROR)

def point_in_hull(point, hull, tolerance=1e-12):
    return all( (numpy.dot(eq[:-1], point) + eq[-1] <= tolerance) for eq in hull.equations)

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

    def __init__(self, ExptRes, TxNameStr, Axes, slhadir=None, databasePath=None,
                 kfactor = 1., limitPoints=None, extraInfo=False, preliminary=False,
                 combine=False, weightedAgreementFactor=True, model="default",
                 style = "", legendplacement = "top right", drawExpected = True,
                 namedTarball = None, keep = False ):
        """
        :param weightedAgreementFactor: when computing the agreement factor,
            weight points by the area of their Voronoi cell
        :param namedTarball: if not None, then this is the name of the tarball explicitly specified in Txname.txt
        :param keep: keep temporary directories
        """

        self.expRes = copy.deepcopy(ExptRes)
        self.model = model
        self.keep = keep
        self.txName = TxNameStr
        self.namedTarball = namedTarball
        self.axes = Axes.strip()
        self.style = style
        self.drawExpected = drawExpected
        self.niceAxes = self.getNiceAxes(Axes.strip())
        self.slhaDir = None
        self.data = None
        self.officialCurves = self.getOfficialCurves( get_all = not self.drawExpected,
                expected = False )
        self.expectedOfficialCurves = self.getOfficialCurves( get_all = False,
                expected = True )
        self.kfactor = kfactor
        self.limitPoints = limitPoints
        self.extraInfo = extraInfo
        self.preliminary = preliminary
        self.weightedAF = weightedAgreementFactor
        self.combine = combine
        self.legendplacement = legendplacement

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

    def __str__(self):

        vstr = "Validation plot for\n"
        vstr += 'id: %s\n' % self.expRes.globalInfo.id
        vstr += 'TxName: '+self.txName+'\n'
        vstr += 'Axes: '+self.niceAxes
        return vstr

    def completeGraph ( self, curve ):
        """ complete the given graph at the ends to cross the axes """
        if not ( curve.GetN() > 3 ):
            print ( "problem, i am trying to complete a graph with %d points" % ( curve.GetN() ) )
        if curve.GetN() <= 3:
            return
        import ROOT
        #x1,y1=ROOT.Double(),ROOT.Double()
        #x2,y2=ROOT.Double(),ROOT.Double()
        #xl,yl=ROOT.Double(),ROOT.Double()
        x1,y1=ctypes.c_double(),ctypes.c_double()
        x2,y2=ctypes.c_double(),ctypes.c_double()
        xl,yl=ctypes.c_double(),ctypes.c_double()
        # first compute k of the first three points
        curve.GetPoint ( 0, x1, y1 ) ## get first point
        curve.GetPoint ( 2, x2, y2 ) ## get third point
        curve.GetPoint ( curve.GetN()-1, xl, yl ) ## get last point
        if (( x1.value - xl.value )**2 + ( y1.value - yl.value ) ** 2 ) < 50.:
            ## need not completion
            return
        logY=False
        #ax1, ay1 = copy.deepcopy(x1), copy.deepcopy(y1)
        #ax2, ay2 = copy.deepcopy(x2), copy.deepcopy(y2)
        #tx1, ty1 = copy.deepcopy(x1), copy.deepcopy(y1)
        ax1, ay1 = x1.value, y1.value
        ax2, ay2 = x2.value, y2.value
        tx1, ty1 = x1.value, y1.value
        if max(abs(ay2),abs(ay1))<1e-6:
            logY=True
            ay2 = rescaleWidth(ay2)
            ay1 = rescaleWidth(ay1)
        if ax2 == ax1:
            ax2 = ax1 + 1e-16
        dx = ax2 - ax1
        if dx == 0.:
            dx=1e-6
        k = (ay2 - ay1) / dx
        if abs(k) > 1:
            ## the curve is more vertical -- close with the x-axis (y=0)
            self.addPointInFront ( curve, tx1, 0. )
        else:
            ## the curve is more horizontal -- close with the y-axis (x=0)
            self.addPointInFront ( curve, 0., ty1 )

        n = curve.GetN()
        curve.GetPoint ( n-3, x1, y1 ) ## get third last point
        curve.GetPoint ( n-1, x2, y2 ) ## get last point
        #tx1, ty1 = copy.deepcopy(x1), copy.deepcopy(y1)
        #tx2, ty2 = copy.deepcopy(x2), copy.deepcopy(y2)
        tx1, ty1 = x1.value, y1.value
        tx2, ty2 = x2.value, y2.value
        if logY:
            ty2 = rescaleWidth(ty2)
            ty1 = rescaleWidth(ty1)
        if tx2 == tx1:
            tx2 = tx1 + 1e-16
        k = 99999.
        if tx2 != tx1:
            k = (ty2 - ty1) / ( tx2 - tx1 )
        if k > 1 or k < -1:
            ## the curve is more vertical -- close with the x-axis (y=0)
            curve.SetPoint ( n, tx2, 0. )
        elif k < 0:
            ## the curve is more horizontal -- close with the y-axis (x=0)
            curve.SetPoint ( n, tx2, 0. )
        else:
            ## the curve is more horizontal -- close with the y-axis (x=0)
            curve.SetPoint ( n, 0., ty2 )
        curve.SetPoint ( n+1, 0., 0. )

    def addPointInFront ( self, curve, x, y ):
        """ add a point at position 0 in tgraph """
        import ROOT
        n=curve.GetN()+1
        #xt,yt=ROOT.Double(),ROOT.Double()
        #xtn,ytn=ROOT.Double(),ROOT.Double()
        xt,yt=ctypes.c_double(),ctypes.c_double()
        # xtn,ytn=ctypes.c_double(),ctypes.c_double()
        # xtn,ytn=x.value,y.value
        xtn,ytn=x,y
        #xtn,ytn=copy.deepcopy(x),copy.deepcopy(y)
        for i in range(n):
            curve.GetPoint(i,xt,yt)
            curve.SetPoint(i,xtn,ytn)
            xtn,ytn=xt.value,yt.value
            # xtn,ytn=copy.deepcopy(xt),copy.deepcopy(yt)

    def printCurve ( self, curve ):
        import ROOT
        n=curve.GetN()
        # xt,yt=ROOT.Double(),ROOT.Double()
        xt,yt=ctypes.c_double(),ctypes.c_double()
        #indices = list(range(n))
        indices = list(range(3))+list(range(n-3,n))
        for i in indices:
            curve.GetPoint(i,xt,yt)
            y = copy.deepcopy(yt)
            if y < 0.:
                y = unscaleWidth(y)
            #if 0. < y < 1e-6:
            #    y = unscaleWidth(y)
            # print ( "%d: %f,%f" % ( i, xt, y ) )
            # print ( "%d: %f,%g" % ( i, xt, y ) )

    def computeHulls ( self ):
        """ compute the convex hulls from the Voronoi
            partition, so we can later weight points with the areas of the
            Voronoi cell """
        if not self.weightedAF:
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
        import ROOT
        curve = self.getOfficialCurves( get_all = False, expected = False )
        if curve == []:
            logger.error( "could not get official tgraph curve for %s %s %s" % ( self.expRes,self.txName,self.axes  ) )
            return 1.0
        curve = curve[0]
        if isinstance(curve,list):
            for c in curve:
                objName = c.GetName()
                if 'exclusion_' in objName:
                    curve = c
                    break

        self.completeGraph ( curve )

        pts= { "total": 0, "excluded_inside": 0, "excluded_outside": 0,
               "not_excluded_inside": 0, "not_excluded_outside": 0, "wrong" : 0 }

        self.computeHulls()

        for point in self.data:
            if "error" in point.keys():
                continue
            y=0.
            try: ## we seem to have two different ways of writing the x,y values
                x=point["axes"]['x']
                y=point["axes"]['y']
            except Exception as e:
                pass
                #x,y=point["axes"][0],point["axes"][1]
            w = 1.
            if weighted:
                w = self.computeWeight ( [x,y] )
            if y==0: y=1.5 ## to avoid points sitting on the line
            excluded = point["UL"] < point["signal"]
            really_excluded = looseness * point["UL"] < point["signal"] * signal_factor
            really_not_excluded = point["UL"] > looseness * point["signal"] * signal_factor
            inside = curve.IsInside ( x,y )
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
            logger.error("SLHA files not found in %s for %s" %(slhadir,str(self)))
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
            return self.slhaDir
        elif os.path.isfile(self.slhaDir):
            try:
                tar = tarfile.open(self.slhaDir,'r:gz')
                tempdir = tempfile.mkdtemp(dir=os.getcwd())
                members=tar.getmembers()
                random.shuffle ( members )
                if self.limitPoints != None and self.limitPoints > 0:
                    members=members[:self.limitPoints]
                tar.extractall(path=tempdir,members=members)
                tar.close()
                logger.debug("SLHA files extracted to %s" %tempdir)
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
            self.ncpus  = -1

        if tempdir is None: tempdir = os.getcwd()
        pf, parFile = tempfile.mkstemp(dir=tempdir,prefix='parameter_',suffix='.ini', text=True )
        combine = "False"
        if self.combine:
            combine = "True"
        model = self.model
        if model == "default":
            ## FIXME here we could define different defaults for eg T5Gamma
            model = "mssm"
        with open ( parFile, "w" ) as f:
            f.write("[options]\ninputType = SLHA\ncheckInput = True\ndoInvisible = True\ndoCompress = True\ncomputeStatistics = True\ntestCoverage = False\ncombineSRs = %s\n" % combine )
            f.write("[parameters]\nsigmacut = 0.000000001\nminmassgap = 2.0\nmaxcond = 1.\nncpus = %i\n" %self.ncpus)
            f.write("[database]\npath = %s\nanalyses = %s\ntxnames = %s\ndataselector = all\n" % (self.databasePath,expId,txname))
            f.write("[printer]\noutputType = python\n")
            f.write("[particles]\nmodel=share.models.%s\npromptWidth=1.1\n" % \
                     model )
            f.write("[python-printer]\naddElementList = False\n")
            f.close()
        os.close(pf)
        return parFile

    def loadData(self):
        """
        Tries to load an already existing python output.
        """

        validationDir = os.path.join(self.expRes.path,'validation')
        datafile = self.getDataFile(validationDir)
        if not os.path.isfile(datafile):
            logger.error("Validation datafile %s not found" %datafile)
            self.data = None
            return

        #Save data to file
        f = open(datafile,'r')
        lines = f.readlines()
        self.data = eval(lines[0].replace("validationData = ",""))
        if len(lines)>1 and lines[1].startswith ( "meta" ):
            self.meta = eval(lines[1].replace("meta = ",""))
        f.close()

    def getWidthsFromSLHAFileName ( self, filename ):
        """ try to guess the mass vector from the SLHA file name """
        tokens = filename.replace(".slha","").split("_")
        if not tokens[0].startswith ( "T" ):
            print ( "why does token 0 not start with a T??? %s" % tokens[0] )
            sys.exit(-1)
        widths = list ( map ( float, tokens[1:] ) )
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
        masses = list ( map ( float, tokens[1:] ) )
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


    def getXYFromSLHAFileName ( self, filename, asDict=False ):
        """ get the 'axes' from the slha file name. uses .getMassesFromSLHAFileName.
        Meant as fallback for when no ExptRes is available.
        :param asDict: if True, return { "x": x, "y": y } dict, else list
        """
        from filenameCoords import coords
        if not self.txName in coords:
            return self.getXYFromSLHAFileNameOld ( filename, asDict )
        oldc = coords[self.txName]
        tname = filename.replace(".slha","")
        tokens = tname.split("_")
        replacedc = copy.deepcopy ( oldc )
        for ib,b in enumerate(oldc["masses"]):
            for iv,v in enumerate(b):
                replacedc["masses"][ib][iv]=float(tokens[v])
        if type(oldc["widths"]) == list:
            for ib,b in enumerate(oldc["widths"]):
                for iv,v in enumerate(b):
                    replacedc["widths"][ib][iv]=float(tokens[v])
        massPlane = MassPlane.fromString(self.txName,self.axes)
        varsDict = massPlane.getXYValues(replacedc["masses"],replacedc["widths"])
        if varsDict == None or asDict:
            return varsDict
        return (varsDict["x"],varsDict["y"])

    def getXYFromSLHAFileNameOld ( self, filename, asDict=False ):
        """ get the 'axes' from the slha file name. uses .getMassesFromSLHAFileName.
        Meant as fallback for when no ExptRes is available.
        :param asDict: if True, return { "x": x, "y": y } dict, else list
        """
        masses = self.getMassesFromSLHAFileName ( filename )
        widths = self.getWidthsFromSLHAFileName ( filename )
        if ".5" in self.axes:
            if len(masses[0])>2 and abs(masses[0][0]+masses[0][2]-2*masses[0][1])<1.1:
                masses[0][1] = (masses[0][0]+masses[0][2])/2. ## fix rounding in file name
            if len(masses[1])>2 and abs(masses[1][0]+masses[1][2]-2*masses[1][1])<1.1:
                masses[1][1] = (masses[1][0]+masses[1][2])/2. ## fix rounding in file name
        if len(masses[0])>1:
            ret = [ masses[0][0], masses[0][1] ]
        else:
            ret = [ masses[0][0], masses[1][0] ]
        massPlane = MassPlane.fromString(self.txName,self.axes)

        varsDict = massPlane.getXYValues(masses,None)
        if varsDict != None and "y" in varsDict:
            ret = [ varsDict["x"], varsDict["y"] ]
        if varsDict == None: ## not on this plane!!!
            ret = None
        if "T3GQ" in filename: ## fixme we sure?
            ret = [ masses[1][0], masses[1][1] ]
        if "T5GQ" in filename or "T2Disp" in filename: ## fixme we sure?
            ret = [ masses[0][0], masses[0][1] ]
        if "THSCPM6" in filename:
            ret = [ masses[0][0], masses[0][2] ]
        if asDict and ret !=None:
            return { "x": ret[0], "y": ret[1] }
        return ret

    def getDataFromPlanes(self):
        """
        Runs SModelS on the SLHA files from self.slhaDir and store
        the relevant data in self.data.
        Uses runSModelS.main.
        """

        #Get list of SLHA files:
        if not self.slhaDir:
            logger.warning("SLHA folder not defined")
            return False
        slhaDir = self.getSLHAdir()  #Path to the folder containing the SLHA files
        logger.debug("SLHA files for validation at %s" %slhaDir)

        #Get list of input files to be tested
        try:
            fileList, inDir = modelTester.getAllInputFiles(slhaDir)
        except Exception: ## old version?
            fileList = modelTester.getAllInputFiles(slhaDir)
            inDir = slhaDir


        #Set temporary outputdir:
        outputDir = tempfile.mkdtemp(dir=slhaDir,prefix='results_')

        #Get parameter file:
        parameterFile = self.getParameterFile(tempdir=outputDir)
        logger.debug("Parameter file: %s" %parameterFile)
        print ("Parameter file: %s" %parameterFile)

        #Read and check parameter file, exit parameterFile does not exist
        parser = modelTester.getParameters(parameterFile)

        #Select the desired experimental result
        listOfExpRes = [self.expRes]

        t0=time.time()
        """ Test all input points """
        modelTester.testPoints(fileList, inDir, outputDir, parser, 'validation',
                 listOfExpRes, 5000, False, parameterFile)
        dt=(time.time()-t0) / len(fileList) ## for now we just write out avg time

        #Define original plot
        massPlane = MassPlane.fromString(self.txName,self.axes)
        if massPlane == None:
            logger.error ( "no mass plane!" )
            return False
        #Now read the output and collect the necessary data
        self.data = []
        slhafiles= os.listdir(slhaDir)
        ct_nooutput=0
        slhafiles.sort() ## make sure we also go in the same order
        for slhafile in slhafiles:
            if not os.path.isfile(os.path.join(slhaDir,slhafile)):  #Exclude the results folder
                continue
            fout = os.path.join(outputDir,slhafile + '.py')
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
            cmd = ff.read().replace('\n','')
            exec( cmd, globals() )
            ff.close()
            if not 'ExptRes' in smodelsOutput:
                logger.debug("No results for %s " %slhafile)
                ## still get the masses from the slhafile name
                axes = self.getXYFromSLHAFileName ( slhafile, asDict=True )
                ## log also the errors in the py file
                Dict = { 'slhafile': slhafile, 'error': 'no results', 'axes': axes }
                self.data.append ( Dict )
                continue
            res = smodelsOutput['ExptRes']
            expRes = res[0]
            #Double checks (to make sure SModelS ran as expected):
            if len(res) != 1:
                logger.debug("Wait. We have multiple dataset Ids. Lets see if there is a combined result." )
                found_combined=False
                for eR in res:
                    if "combined" in eR["DataSetID"]:
                        logger.debug ( "found a combined result. will use it." )
                        found_combined=True
                        expRes = eR
                if not found_combined:
                    logger.warning("We have multiple dataset ids, but none is a combined one. Dont know what to do." )
                    return False
            if expRes['AnalysisID'] != self.expRes.globalInfo.id:
                logger.error("Something went wrong. Obtained results for the wrong analyses")
                return False
            if self.txName != expRes['TxNames'][0] or len(expRes['TxNames']) != 1:
                logger.error("Something went wrong. Obtained results for the wrong txname")
                return False

            #Replaced rounded masses by original masses
            #(skip rounding to check if mass is in the plane)
            roundmass = expRes['Mass (GeV)']
            """
            width = copy.deepcopy ( roundmass )
            for ib,br in enumerate(width):
                for ic,w in enumerate(br):
                    width[ib][ic]=None
            """
            width = None
            if "Width (GeV)" in expRes:
                width = expRes['Width (GeV)']
            #print ( "roundmass", slhafile, roundmass )
            #print ( "expRes", expRes )
            if roundmass is None or "TGQ12" in slhafile:
                ## FIXME, for TGQ12 why cant i use exptres?
                import inspect
                frame = inspect.currentframe()
                line = frame.f_lineno
                #print ( "roundmass is not given in validationObjs.py:%s" % line )
                #print ( "we try to extract the info from the slha file name %s" % \
                #        slhafile )
                roundmass = self.getMassesFromSLHAFileName ( slhafile )
            # print ( "after", slhafile, roundmass )
            mass = [br[:] for br in roundmass]
            slhadata = pyslha.readSLHAFile(os.path.join(slhaDir,slhafile))
            origmasses = list(set(slhadata.blocks['MASS'].values()))
            for i,br in enumerate(mass):
                for im,m in enumerate(br):
                    for omass in origmasses:
                        if round(omass,1) == m:
                            mass[i][im] = omass
                            break

            #print ( "get xy", mass, width )
            varsDict = massPlane.getXYValues(mass,width)
            #print ( "varsdict", varsDict )
            if varsDict is None:
                logger.debug( "dropping %s, doesnt fall into the plane of %s." % \
                               (slhafile, massPlane ) )
                continue
            Dict = {'slhafile' : slhafile, 'axes' : varsDict, 't': dt,
                    'signal': expRes['theory prediction (fb)'],
                    'UL': expRes['upper limit (fb)'], 'condition': expRes['maxcond'],
                    'dataset': expRes['DataSetID'] }
            if 'expected upper limit (fb)' in expRes:
                Dict['eUL']=expRes["expected upper limit (fb)"]
                if self.drawExpected == "auto":
                    self.drawExpected = True
            if "efficiency" in expRes.keys():
                Dict["efficiency"] = expRes['efficiency']
            if expRes['dataType'] == 'efficiencyMap':
                #Select the correct dataset (best SR):
                dataset = [dset for dset in self.expRes.datasets if dset.dataInfo.dataId == expRes['DataSetID']]
                if len(dataset)==1:
                    dataset = dataset[0]
                else: ## probably the combined case. we take any dataset.
                    dataset = self.expRes.datasets[0]

                txname = [tx for tx in dataset.txnameList if tx.txName == expRes['TxNames'][0]][0]
                mnw=[]
                if width == None:
                    mnw = mass
                else:
                    for bm,bw in zip(mass,width):
                        br=[]
                        for m,w in zip(bm,bw):
                            br.append( (m,w) )
                        mnw.append(br)
                massGeV = addUnit ( mnw, GeV )
                if not "efficiency" in Dict.keys():
                    try:
                        Dict['efficiency'] = txname.txnameData.getValueFor(massGeV)
                    except SModelSError as e:
                        logger.error ( "could not handle %s: %s" % ( slhafile, e ) )
                        Dict=None
            logger.debug('expres keys : {}'.format(expRes.keys()))
            if 'best combination' in expRes.keys():
                Dict['best combination'] = expRes['best combination']

            if Dict:
                self.data.append(Dict)

        #Remove temporary folder
        if slhaDir != self.slhaDir and not self.keep: shutil.rmtree(slhaDir)

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

    def getUglyPlot(self,silentMode=True):
        """
        Uses the data in self.data and the official exclusion curve
        in self.officialCurves to generate the exclusion plot
        :param silentMode: If True the plot will not be shown on the screen
        """

        self.plot,self.base = createUglyPlot(self,silentMode=silentMode,
                extraInfo=self.extraInfo,preliminary=self.preliminary,
                weightedAgreementFactor=self.weightedAF )

    def getPrettyPlot(self,silentMode=True):
        """
        Uses the data in self.data and the official exclusion curve
        in self.officialCurves to generate a pretty exclusion plot
        :param silentMode: If True the plot will not be shown on the screen
        """

        self.plot,self.base = createPrettyPlot(self,silentMode=silentMode,
                   preliminary=self.preliminary, style = self.style,
                   legendplacement = self.legendplacement, drawExpected = self.drawExpected )

    def savePlot(self,validationDir=None,fformat='pdf'):
        """
        Saves the plot in .pdf format in the validationDir folder.
        If the folder does not exist, it will be created.
        If the folder is not defined the plot will be created in the
        analysis/validation/ folder

        :param validationDir: Folder where the plot will be saved
        :param fformat: File fformat (accepted by ROOT), i.e. pdf, png, jpg...
        """


        if not hasattr(self,'plot') or not self.plot:
            logger.warning("No plot found. Nothing will be saved")
            return False

        if not validationDir:
            vDir = os.path.join(self.expRes.path,'validation')
        else: vDir = validationDir

        if not os.path.isdir(vDir):
            logger.debug("Creating validation folder "+vDir)
            os.mkdir(vDir)

        filename = self.getPlotFile(vDir,fformat)

        if not self.pretty:
            logger.info ( "saving plot in %s" % filename )
            self.plot.Print(filename)
            filename = filename.replace('.'+fformat,'.png')
            try:
                self.plot.Print(filename)
            except Exception as e:
                # if fails because of missing dep, then just proceed
                pass
        else:
            from addLogoToPlots import addLogo
            #Print pdf, png and root formats
            filename = filename.replace('.'+fformat,'_pretty.'+fformat)
            self.plot.Print(filename)
            addLogo ( filename )
            filename = filename.replace('.'+fformat,'.png')
            logger.info ( "saving plot in %s (and pdf and root)" % filename )
            self.plot.Print(filename)
            addLogo ( filename )
            filename = filename.replace('.png','.root')
            self.plot.Print(filename)
            addLogo ( filename )

        return True

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

        if not hasattr(self,'plot') or not self.plot:
            logger.warning("No plot found. Nothing will be saved")
            return False
        if not hasattr(self,'data') or not self.data:
            logger.warning("No data found. Nothing will be saved")
            return False

        if not validationDir:
            validationDir = os.path.join(self.expRes.path,'validation')

        if not os.path.isdir(validationDir):
            logger.info("Creating validation folder "+validationDir)
            os.mkdir(validationDir)

        if not datafile:
            datafile = self.getDataFile(validationDir)
        #Save data to file
        f = open(datafile,'w')
        dataStr = str(self.data)
        dataStr = dataStr.replace('[fb]','*fb').replace('[pb]','*pb')
        dataStr = dataStr.replace('[GeV]','*GeV').replace('[TeV]','*TeV')
        f.write("validationData = "+dataStr+"\n")
        from smodels import installation
        from smodels_utils import SModelSUtils
        meta = { "smodelsver": installation.version(),
                 "utilsver": SModelSUtils.version(), "timestamp": time.asctime() }
        if self.namedTarball != None:
            meta["tarball"]=self.namedTarball
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
        datafile = self.getPlotFile(validationDir,fformat)
        datafile = datafile.rstrip(fformat)
        if not datafile.endswith ( "." ):
            datafile += "."
        return datafile+'py'

    def getPlotFile(self,validationDir,fformat='pdf'):
        """
        Defines the name of the plot file and returns it

        :param validationDir: Folder where the root file will be saved

        :return: name of the plot file
        """

        if fformat.startswith("."):
            fformat = fformat[1:]

        filename = self.expRes.globalInfo.id + "_" + self.txName + "_"
        filename += self.niceAxes.replace(",","").replace("(","").replace(")","")
        if self.combine:
            filename += '_combined'
        filename += '.'+fformat

        filename = filename.replace(self.expRes.globalInfo.id+"_","")
        filename = os.path.join(validationDir,filename)
        filename = filename.replace("*","").replace(",","").replace("(","").replace(")","")

        return filename

    def getNiceAxes(self,axesStr):
        """
        Convert the axes definition format ('[[x,y],[x,y]]')
        to a nicer format ('Eq(MassA,x)_Eq(MassB,y)_Eq(MassA,x)_Eq(MassB,y)')

        :param axesStr: string defining axes in the old format

        :return: string with a nicer representation of the axes (more suitable for printing)
        """

        x,y,z,w = var('x y z w')
        if axesStr == "":
            logger.error ( "Axes field is empty: cannot validate." )
            return None
        axes = eval(axesStr,{'x' : x, 'y' : y, 'z': z, 'w': w})

        eqList = []
        for ib,br in enumerate(axes):
            if ib == 0:
                mStr,wStr = 'Mass','Width'
            else:
                mStr,wStr = 'mass','width'
            mList = []
            for im,eq in enumerate(br):
                if type(eq)==tuple:
                    mList.append('Eq(%s,%s)'
                                   %(var(mStr+string.ascii_uppercase[im]),eq[0]))
                    mList.append('Eq(%s,%s)'
                                   %(var(wStr+string.ascii_uppercase[im]),eq[1]))
                else:
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

        return eqStr
