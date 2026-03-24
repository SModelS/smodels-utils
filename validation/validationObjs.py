#!/usr/bin/env python3

"""
.. module:: validationObjs
   :synopsis: Main classes and methods for generating a single validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging
import os,sys,time,copy,shutil
from smodels.base.smodelsLogging import logger
from smodels.base.physicsUnits import GeV
from smodels_utils.helper.various import round_to_n
try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth, \
         rescaleWidth, addUnit
except:
    from backwardCompatibility import addUnit, rescaleWidth

from validationHelpers import equal_dicts
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels.experiment.exceptions import SModelSExperimentError as SModelSError
from smodels.experiment.databaseObj import Database
from sympy import var
import numpy as np
import pyslha
import string
import glob
from typing import List
from validationObjsBase import ValidationObjsBase

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

    def __init__( self, ExptRes, TxNameStr, Axes, db : Database, slhadir=None,
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
                logger.error(f"Database folder {databasePath} does not exist")
                sys.exit()
        #Try to guess the path:
        else:
            self.databasePath = ExptRes.path[:ExptRes.path.find(f"/{anaID}")]
            self.databasePath = self.databasePath[:self.databasePath.rfind('/')]
            self.databasePath = self.databasePath[:self.databasePath.rfind('/')+1]
            if not os.path.isdir(self.databasePath):
                logger.error("Could not define databasePath folder")
                sys.exit()
        self.expRes = copy.deepcopy(ExptRes)
        self.db = db
        self.ct_nooutput = 0
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
        self.massPlane = MassPlane.fromString(self.txName,self.axes)
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
                logger.error(f"Database folder {databasePath} does not exist")
                sys.exit()
        #Try to guess the path:
        else:
            anaID = ExptRes.globalInfo.id
            self.databasePath = ExptRes.path[:ExptRes.path.find(f"/{anaID}")]
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

        vstr = "Validation plot for\n"
        vstr += f'id: {self.expRes.globalInfo.id}\n'
        vstr += f"TxName: {self.txName}\n"
        vstr += f"Axes: {self.axes}"
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
            line = f"Validation datafile {datafile} not found"
            if self.options["generateData"] == False:
                logger.error( line )
            else:
                logger.info( line )
            if overwrite:
                self.data = []
            return
        nprev = len(self.data)

        from validationHelpers import getValidationFileContent
        content = getValidationFileContent ( datafile )
        if overwrite:
            self.data = []
        # dict of current[!] validation content as values, slhafilename as keys
        slhadict = { x["slhafile"] : x for x in self.data }
        ctadded = 0
        # content["data"] is dict of previous[!] validation content
        for d in content["data"]:
            slhafile = d["slhafile"]
            # d here is one entry in the validation dict file
            if slhafile in slhadict:
                if not equal_dicts ( d, slhadict[slhafile], {"t",} ):
                    ## FIXME ignore t!
                    logger.error ( f"entry {d['slhafile']} changed content {d} != {slhadict[slhafile]}" )
            else:
                ctadded+=1
                self.data.append ( d )
        try:
            self.data.sort ( key = lambda x: x["axes"]["x"]*1e6 + x["axes"]["y"] )
        except:
            def getKey ( x ):
                if x["axes"] is None:
                    return -1e9
                return x["axes"]["x"]
            self.data.sort ( key = lambda x: getKey ( x ) )
        self.meta = content["meta"]
        if self.meta is None:
            self.meta = {}
        addedpoints = len(self.data)
        if not overwrite:
            logger.info ( f"merging old data with new: {nprev}+{len(content['data'])}={len(self.data)}" )
            self.meta["runs"]=f"{len(self.data)}"
            """ # we had this behavior before: report all runs, concatenated with a '+' sign.
            # seems too contrived now. WW
            if not "runs" in self.meta:
                self.meta["runs"]=f"{len(self.data)}"
            else:
                prev = eval ( self.meta["runs"] )
                addedpoints = len(self.data)-prev
                self.meta["runs"]=self.meta["runs"]+"+"+f"{addedpoints}"
            """
        # self.data = content["data"]
        ndata = 0
        if self.data != None:
            ndata = len ( self.data )
        self.meta["npoints"] = ndata
        return addedpoints

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
                if v >= len(tokens):
                    logger.error ( f"filename {filename} does not have {v} labels, only {len(tokens)}. Can you please check filenameCoords.py, entry for {self.txName}? It currently reads: {oldc}." )
                    sys.exit(-1)

                try:
                    replacedc["masses"][ib][iv]=float(tokens[v])
                except ValueError as e:
                    print ( f"[validationObjs] caught ValueError {e}" )
                    if v == 0:
                        print ( "[validationObj] seems like you used index 0 in filenameCoords.py, which points to the tx name" )
                    sys.exit(-1)
                except IndexError as e:
                    print ( "[validationObjs] tokens {tokens} v {v}" )
                    print ( "[validationObjs] replacedc {replacedc['masses']}, ib {ib} iv {iv}" )
                    print ( f"[validationObjs] caught IndexError {e}" )
                    sys.exit(-1)
        if type(oldc["widths"]) == list:
            for ib,b in enumerate(oldc["widths"]):
                for iv,v in enumerate(b):
                    replacedc["widths"][ib][iv]=float(tokens[v])
        # massPlane = MassPlane.fromString(self.txName,self.axes)
        varsDict = self.massPlane.getXYValues(replacedc["masses"],replacedc["widths"])
        if varsDict == None or asDict:
            return varsDict
        return (varsDict["x"],varsDict["y"])

    def getVarsDict ( self, roundmass, width, expRes, slhafile ):
        # print ( "after", slhafile, roundmass )
        mass = [br[:] for br in roundmass]
        slhadata = pyslha.readSLHAFile(os.path.join(self.currentSLHADir,slhafile))
        origmasses = list(set(slhadata.blocks['MASS'].values()))
        for i,br in enumerate(mass):
            for im,m in enumerate(br):
                for omass in origmasses:
                    if round(omass,1) == m:
                        mass[i][im] = omass
                        break

        varsDict = self.massPlane.getXYValues(mass,width)
        return varsDict

    def getMassesAndWidths ( self, mass, width ):
        massGeV = []
        widthsGeV = []
        for bm,bw in zip(mass,width):
            for m,w in zip(bm,bw):
                if w == 'stable' or w > .08:
                    massGeV.append( m )
                else:
                    massGeV.append( m )
                    widthsGeV.append( w )
        total = massGeV
        if len(widthsGeV)>0:
            total += widthsGeV
        return total

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
        fileList = self.runSModelS( outputformat = 2 )

        #Define original plot
        # massPlane = MassPlane.fromString(self.txName,self.axes)
        if self.massPlane == None:
            logger.error ( "no mass plane!" )
            return False
        #Now read the output and collect the necessary data
        slhafiles= os.listdir(self.currentSLHADir)
        self.ct_nooutput=0
        slhafiles.sort() ## make sure we also go in the same order
        for slhafile in fileList: # slhafiles:
            if "recipe" in slhafile:
                continue
            if "coordinates" in slhafile:
                continue
            if "comment" in slhafile:
                continue
            if not os.path.isfile(os.path.join(self.currentSLHADir,slhafile)):  #Exclude the results folder
                continue
            fout = os.path.join(self.outputDir,f"{slhafile}.py")
            self.addResultToData ( slhafile, fout )

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

