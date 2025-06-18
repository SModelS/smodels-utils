#!/usr/bin/env python3

"""
.. module:: validationObjs
   :synopsis: Main classes and methods for generating a single validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,time,math,numpy,copy
#logger = logging.getLogger(__name__)
from smodels.base.smodelsLogging import logger
from smodels.base.physicsUnits import GeV
from smodels_utils.helper.various import round_to_n
from typing import Union, Dict, List
import numpy as np
try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth, \
         rescaleWidth, addUnit
except:
    from backwardCompatibility import addUnit, rescaleWidth

from plottingFuncs import getExclusionCurvesFor
import shutil,copy
from smodels_utils.dataPreparation.graphMassPlaneObjects import GraphMassPlane
from smodels.experiment.exceptions import SModelSExperimentError as SModelSError
from smodels.experiment.databaseObj import Database
from validationObjsBase import ValidationObjsBase
from sympy import var
import pyslha
import string
import glob

logger.setLevel(level=logging.ERROR)

complaints = { "NoResultsFor": 0 }

class ValidationPlot( ValidationObjsBase ):
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
        super ( ValidationPlot, self ).__init__ ( ) 
        anaID = ExptRes.globalInfo.id
        if databasePath:
            if os.path.isdir(databasePath):
                self.databasePath = databasePath
            else:
                logger.error("Database folder "+databasePath+" does not exist")
                sys.exit()
        #Try to guess the path:
        else:
            self.databasePath = ExptRes.path[:ExptRes.path.find('/'+anaID)]
            self.databasePath = self.databasePath[:self.databasePath.rfind('/')]
            self.databasePath = self.databasePath[:self.databasePath.rfind('/')+1]
            if not os.path.isdir(self.databasePath):
                logger.error("Could not define databasePath folder")
                sys.exit()
        self.expRes = copy.deepcopy(ExptRes)
        self.db = db
        self.keep = keep
        self.runningDictFile = f"run_{anaID}.dict"
        self.runningDictLockFile = f"run_{anaID}.lock"
        if not options["continue"]:
            if os.path.exists ( self.runningDictFile ):
                try:
                    os.unlink ( self.runningDictFile )
                except FileNotFoundError as e:
                    pass
            if os.path.exists ( self.runningDictLockFile ):
                try:
                    os.unlink ( self.runningDictLockFile )
                except FileNotFoundError as e:
                    pass
        self.t0 = time.time()
        self.options = options
        self.limitPoints = self.options["limitPoints"]
        self.willRun = []
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
        return vstr

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
                slhafile = d["slhafile"]
                if d != slhafiles[ slhafile ]:
                    logger.error ( f"entry {d['slhafile']} changed content {d} != {slhafiles[ slhafile ]}" )
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

    def addResultToData ( self, slhafile : str, resultsfile : str ) -> int: 
        """ returns 1 if success else 0 """
        fout = resultsfile
        if not os.path.isfile(fout):
            if self.ct_nooutput>4:
                ## suppress subsequently same error messages
                return
            logger.info( f"No SModelS output found for {slhafile} (should be {fout})" )
            self.ct_nooutput+=1
            if self.ct_nooutput==5:
                logger.info("did not find SModelS output 5 times subsequently. Will quench error msgs from now on.")
            return
        logger.debug ( f"reading {fout}" )
        ff = open(fout,'r')
        txt = ff.read()
        cmd = txt.replace('\n','') # .replace("inf,","float('inf'),")
        myglobals = globals()
        myglobals["inf"]=float("inf")
        myglobals["nan"]=float("nan")
        try:
            exec( cmd, myglobals )
        except SyntaxError as e:
            logger.error ( f"when reading {fout}: {e}. will skip" ) 
            os.unlink ( fout )
            return 0
        ff.close()
        if not 'ExptRes' in smodelsOutput:
            logger.debug( f"No results for {slhafile}" )
            ## still get the masses from the slhafile name
            axes = self.getXYFromSLHAFileName ( slhafile, asDict=True )
            ## log also the errors in the py file
            Dict = { 'slhafile': slhafile, 'error': 'no results here', 'axes': axes }
            self.data.append ( Dict )
            return 1
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
                datasetId = eR["DataSetID"]
                if datasetId != None and  "combined" in datasetId:
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
                logger.warning("We have multiple dataset ids, but none is a combined one. Skipping this point." )
                return 0
        if expRes['AnalysisID'] != self.expRes.globalInfo.id:
            logger.error("Something went wrong. Obtained results for the wrong analyses")
            return 0
        if self.txName != expRes['TxNames'][0] or len(expRes['TxNames']) != 1:
            logger.error( f"Something went wrong. Obtained results for the wrong txname: got {expRes['TxNames']} but want {self.txName}")
            return 0

        #Replaced rounded masses by original masses
        #(skip rounding to check if mass is in the plane)
        roundmass = expRes['Mass (GeV)']
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
        slhadata = pyslha.readSLHAFile(os.path.join(self.currentSLHADir,slhafile))
        origmasses = list(set(slhadata.blocks['MASS'].values()))

        nodesMap = expRes["Nodes Map"]
        parameters = self.constructParameterVector ( mass, width, nodesMap )
        varsDict = self.massPlane.getXYValues( parameters )
        if varsDict is None:
            logger.debug( f"dropping {slhafile}, doesnt fall into the plane of {self.massPlane}." )
            return 0
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
        if len(leadingDSes)>0:
            s = []
            n = self.options["keepTopNSRs"]
            for k,v in sorted ( leadingDSes.items(), reverse=True )[:n]:
                s.append ( (k,v) )
            Dict["leadingDSes"]= s
        if "nll_min" in expRes and "nll" in expRes:
            for i in [ "nll", "nll_SM", "nll_min" ]:
                Dict[i]=expRes[i]
        if "l_max" in expRes and "likelihood" in expRes:
            #Dict["llhd"]= round_to_n ( expRes["likelihood"], 4 )
            #Dict["lmax"]= round_to_n ( expRes["l_max"], 4 )
            #Dict['l_SM']= round_to_n ( expRes['l_SM'], 4 )
            nll = 900.
            if expRes["likelihood"]>0.:
                nll = round_to_n ( - np.log ( expRes["likelihood"] ), 4 )
            Dict["nll"]= nll
            nll_min = 900.
            if expRes["l_max"]>0.:
                nll_min = round_to_n ( - np.log ( expRes["l_max"] ), 4 )
            Dict["nll_min"]= nll_min
            nll_SM = 900.
            if expRes["l_SM"]>0.:
                nll_SM = round_to_n ( - np.log ( expRes['l_SM'] ), 4 ) 
            Dict['nll_SM']= nll_SM
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
            mnw=[]
            massGeV = []
            if width == None:
                mnw = mass
            else:
                # br=[]
                for bm,bw in zip(mass,width):
                    for m,w in zip(bm,bw):
                        if w == 'stable' or ( type(w) not in [ str ] and w > .08 ):
                            massGeV.append( m )
                            # br.append( (m,0.0) )
                        else:
                            massGeV.append( (m,w) )
                    # mnw.append(br)
            # massGeV = addUnit ( mnw, GeV )
            if not "efficiency" in Dict.keys():
                try:
                    eff = txname.txnameData.getValueFor(massGeV)
                    if eff != None:
                        Dict['efficiency'] = round ( eff, 8 )
                except SModelSError as e:
                    logger.error ( "could not handle %s: %s" % ( slhafile, e ) )
                    Dict=None
        logger.debug('expres keys : {}'.format(expRes.keys()))
        if 'best combination' in expRes.keys():
            Dict['best combination'] = expRes['best combination']

        if Dict:
            self.data.append(Dict)
            return 1
        return 0

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
            axesDict[nr]=parse_expr ( str(expr) )
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
        if len ( tokens ) == 7 and equal ( tokens[1], tokens[4]) and \
                equal ( tokens[3], tokens[6] ) and \
                abs ( float(tokens[1])+float(tokens[3]) - 2*float(tokens[2])) < 1.5 \
                and Eq ( axesDict[1], .5*x+.5*y )==True:
            # e.g. TChiWH_400_300_200_400_300_200.slha
            ## account for rounding
            D = { "x": round_to_n(float(tokens[1]),5),
                  "y": round_to_n(float(tokens[3]),5) }
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
        fileList = self.runSModelS( outputformat = 3 )

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
            ff = open(fout,'r')
            txt = ff.read()
            cmd = txt.replace('\n','') # .replace("inf,","float('inf'),")
            try:
                exec( cmd, myglobals )
            except SyntaxError as e:
                if os.path.exists ( fout ):
                    try:
                        os.unlink ( fout )
                    except FileNotFoundError as f:
                        pass
                continue
            ff.close()
            if not 'ExptRes' in smodelsOutput:
                complaints["NoResultsFor"]+=1
                if complaints["NoResultsFor"]<4:
                    logger.info( f"No results for {slhafile}" )
                if complaints["NoResultsFor"]==4:
                    logger.info( f"(quenching more info msgs)" )

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
                        # print ( f"@@0 eR {eR}" )
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
                logger.error( f"Something went wrong. Obtained results for the wrong analyses: {expRes['AnalysisID']}!={self.expRes.globalInfo.id}")
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
            if masses == None:
                axes = self.getAxesFromSLHAFileName ( slhafile )
                if len(axes)==0: # drop it, doesnt fall in this plane it seems
                    continue
                D = { "slhafile": slhafile, "error": "masses are None",
                      "axes": axes }
                self.data.append ( D )
                continue
            parameters = self.constructParameterVector ( masses, widths, nodesMap )
            varsDict = massPlane.getXYValues( parameters )
            if varsDict in [ None, {} ]:
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
            if "nll_min" in expRes and "nll" in expRes:
                for i in [ "nll", "nll_SM", "nll_min" ]:
                    Dict[i]=expRes[i]
            if "l_max" in expRes and "likelihood" in expRes:
                #Dict["llhd"]= round_to_n ( expRes["likelihood"], 4 )
                #Dict["lmax"]= round_to_n ( expRes["l_max"], 4 )
                #Dict['l_SM']= round_to_n ( expRes['l_SM'], 4 )
                nll = 900.
                if expRes["likelihood"]>0.:
                    nll = round_to_n ( - np.log ( expRes["likelihood"] ), 4 )
                Dict["nll"]= nll
                nll_min = 900.
                if expRes["l_max"]>0.:
                    nll_min = round_to_n ( - np.log ( expRes["l_max"] ), 4 )
                Dict["nll_min"]= nll_min
                nll_SM = 900.
                if expRes["l_SM"]>0.:
                    nll_SM = round_to_n ( - np.log ( expRes['l_SM'] ), 4 ) 
                Dict['nll_SM']= nll_SM
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
                        #print ( f"@@12 Dict {Dict}" )
                        #print ( f"@@13 parameters {parameters}" )
                        for i,p in enumerate(parameters):
                            if p=="stable":
                                parameters[i]=0.
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
            logger.info ( f"now removing {self.currentSLHADir}" )
            shutil.rmtree(self.currentSLHADir)

        if self.data == []:
            logger.error( f"There is no data for {self.expRes.globalInfo.id}/{self.txName}/{self.axes}.\n Are the SLHA files correct? Are the constraints correct?" )

        #Apply k-factors to theory prediction (default is 1)
        for ipt,pt in enumerate(self.data):
            if "error" in pt.keys():
                continue
            pt['signal'] *= self.kfactor
            self.data[ipt] = pt
            self.data[ipt]['kfactor'] = self.kfactor
