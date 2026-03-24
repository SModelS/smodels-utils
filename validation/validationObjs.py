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
        self.super_init ( ExptRes, TxNameStr, Axes, db, slhadir, 
                databasePath, options, kfactor, namedTarball, keep, combine )
        self.massPlane = MassPlane.fromString(self.txName,self.axes)
        self.niceAxes = self.getNiceAxes(Axes.strip())

    def specialInits ( self ):
        """ inits for the subclass """
        self.validationType = "unknown"

    def __str__(self):

        vstr = "Validation plot for\n"
        vstr += f'id: {self.expRes.globalInfo.id}\n'
        vstr += f"TxName: {self.txName}\n"
        vstr += f"Axes: {self.axes}"
        return vstr

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

        varsDict = self.massPlane.getXYValues(masses,None)
        if varsDict == None: ## not on this plane!!!
            ret = None
        if varsDict != None and "y" in varsDict:
            ret = [ varsDict["x"], varsDict["y"] ]
        if "T3GQ" in filename: ## fixme we sure?
            ret = [ masses[1][0], masses[1][1] ]
        if "T5GQ" in filename or "T2Disp" in filename: ## fixme we sure?
            ret = [ masses[0][0], masses[0][1] ]
        if "THSCPM6" in filename:
            ret = [ masses[0][0], masses[0][2] ]
        if asDict and ret !=None:
            ret = { "x": ret[0], "y": ret[1] }
        # now remove y values
        if not "y" in self.axes:
            if type(ret) == dict:
                ret.pop("y")
            if type(ret) == list:
                ret = [ ret[0] ]
        return ret


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

