#!/usr/bin/env python3

"""
.. module:: graphsValidationObjs
   :synopsis: Validation plot class for v3 (graph/sms-map) mass planes

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,time,math,numpy,copy
#logger = logging.getLogger(__name__)
from smodels.base.smodelsLogging import logger
from smodels.base.physicsUnits import GeV
from smodels_utils.helper.various import round_to_n
from typing import Union, Dict, List, Optional
import numpy as np
try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth, \
         rescaleWidth, addUnit
except:
    from backwardCompatibility import addUnit, rescaleWidth

from validationHelpers import equal_dicts

from plottingFuncs import getExclusionCurvesFor
import shutil,copy
from smodels_utils.dataPreparation.graphMassPlaneObjects import GraphMassPlane as MassPlane
from smodels.experiment.exceptions import SModelSExperimentError as SModelSError
from smodels.experiment.databaseObj import Database
from validationObjsBase import ValidationObjsBase
from sympy import var
import pyslha
import string
import glob

logger.setLevel(level=logging.ERROR)

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

    outputFormat : int = 3
    leadingDSThreshold : int = 1

    def __init__( self, ExptRes, TxNameStr : str, Axes, db : Database, slhadir=None,
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
        axes = self.axes
        axes = axes.replace(",","").replace("{","").replace("}","").\
                    replace(":","").replace("'","").replace(" ","")
        vstr = f"{self.expRes.globalInfo.id}:{self.txName}_{axes}"
        return vstr

    def getVarsDict ( self, roundmass, width, expRes : dict,
            slhafile : str ) -> Optional[dict]:
        """ obtain the x/y values for a point using the nodes map.

        :param roundmass: mass vectors from the SModelS output
        :param width: width vectors from the SModelS output
        :param expRes: the SModelS result dictionary for this point
        :param slhafile: name of the corresponding SLHA file
        :return: dictionary with the x/y values, or None if the point does
                 not lie on the mass plane
        """
        mass = [br[:] for br in roundmass]
        # make sure the SLHA file is readable; the masses themselves come
        # from the SModelS output for v3
        pyslha.readSLHAFile(os.path.join(self.currentSLHADir,slhafile))

        nodesMap = expRes["Nodes Map"]
        parameters = self.constructParameterVector ( mass, width, nodesMap )
        varsDict = self.massPlane.getXYValues( parameters )
        return varsDict

    def selectResults ( self, res : list ) -> list:
        """ pick the ExptRes entry belonging to our txname, if unambiguous.

        A single database result can contain several txnames. When
        validating them together, SModelS reports one ExptRes per txname.
        """
        if len(res) > 1:
            matching = [ eR for eR in res
                         if eR and self.txName in eR.get('TxNames', [] ) ]
            if len ( matching ) == 1:
                return matching
        return res

    def txNameMatches ( self, expRes : dict ) -> bool:
        """ in v3 the txname may appear anywhere in the txname list """
        return self.txName in expRes['TxNames']

    def getMassesAndWidthsForPlane ( self, expRes : dict,
            slhafile : str ) -> tuple:
        """ the masses and widths come directly from the SModelS output;
        the plane is evaluated via the nodes map in getVarsDict. """
        return expRes["Mass (GeV)"], expRes.get("Width (GeV)")

    def getEfficiencyParameters ( self, mass : list, width : list,
            expRes : dict ) -> list:
        """ build the parameter vector for the efficiency map lookup,
        replacing stable particles by zero. """
        nodesMap = expRes["Nodes Map"]
        parameters = self.constructParameterVector ( mass, width, nodesMap )
        for i,p in enumerate(parameters):
            if p == "stable":
                parameters[i] = 0.
        return parameters

    def getDataMap ( self ) -> Optional[dict]:
        """ obtain the data map corresponding to our txname """
        txn = self.getTxname()
        if txn is None:
            return None
        return txn.dataMap

    def getSmsMap ( self ) -> Optional[dict]:
        """ obtain the sms map corresponding to our txname """
        txn = self.getTxname()
        if txn is None:
            return None
        return txn.smsMap

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

    def getXYFromSLHAFileName ( self, slhafile : str, 
                                asDict : bool = True ) -> Dict:
        """ get the axes dictionary from the slha filename alone.
        meant for points that did not produce any smodels output.

        :param slhafile: the slha filename, e.g. TChiWH_400_200_400_200.slha
        :returns: dictionary of axes, e.g. { "x": 400, "y": 200 }
        """
        logger.debug ( f"need to find axes for {slhafile} ({self.axes})" )
        x,y,z,w = var ( "x y z w" )
        axesDict = eval ( self.axes )
        from sympy.parsing.sympy_parser import parse_expr
        from sympy import solve, Eq

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
        numbers = tokens[1:]
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
