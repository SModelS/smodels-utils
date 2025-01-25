#!/usr/bin/env python3

"""
.. module:: massPlaneObjects
   :synopsis: Holds object representing one mass plane

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys
import numpy as np
from sympy import var, Eq, lambdify, solve, N, And, sqrt
from scipy.spatial import Delaunay
from itertools import permutations
from smodels_utils.dataPreparation.dataHandlerObjects import DataHandler,ExclusionHandler
from smodels_utils.dataPreparation.massPlaneObjectsBase import _lambdify, \
         MassPlaneBase, allvars, x, y, z, w, hasWarned
import string
import logging
from typing import Union, List
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

class MassPlane(MassPlaneBase):
    """
    Holds all information related to one mass plane
    a mass plane is defined by their axes.
    The variables defined in infoAttr are passed to the corresponding
    txname to be written in txname.txt
    """

    def __init__(self,txDecay, massArray):
        """
        sets the branches to the given axes and initialize the mass plane related
        values an objects
        :param txDecay: object of type TxDecay
        :param massArray: the full mass array containing equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [[x,y],[x,y]])
        :param lspMass: mass of lightest SUSY-particle as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        :param **interMasses: masses of the intermediated particles as
                              sympy.core.symbol.Symbol, containing only the
                              variables 'x', 'y' and numbers as float
        """

        self.branches = []
        self._txDecay = txDecay
        self.figureUrl = None
        self.dataUrl = None
        self.allInputFiles = []
        for i,brMasses in enumerate(massArray):
            if not isinstance(brMasses,list):
                logger.error( f"Mass array must be in the format [[m1,m2,..],[m3,m4,..]], was {massArray}")
                sys.exit()
            self.setBranch(branchNumber=i,branchMasses=brMasses)

        self.axes = massArray
        #Store plane variables (x,y,..)
        xvars = []
        for br in self.branches:
            for xvar in br._xvars:
                if not xvar in xvars:
                    xvars.append(xvar)
        self.xvars = xvars #All variables used in defining the axes
        self._exclusionCurves = []



    @classmethod
    def fromString(cls,txname,string):

        """
        build an instance of MassPlane from a given string

        :param txname: txname string (e.g. T1)
        :param string: The string must contain a representation of the axes in the format
                      '[[exp1,exp2,..], [Exp1,Exp2,..]]', where exp1,.. are the expressions
                      defining the mass array in terms of the x,y,.. variables
                      (e.g. [[x,y],[x,y]])
        """
        if string in [ "", None, "None" ]:
            if not hasWarned["emptystring"]:
                logger.error ( "cannot build mass plane from empty string!" )
                hasWarned["emptystring"]=True
            return None
        massArray = eval(string)
        if type(massArray) == dict:
            from smodels_utils.dataPreparation.graphMassPlaneObjects import GraphMassPlane
            return GraphMassPlane.fromString ( txname, string )
        massPlane = MassPlane(txname,massArray)

        return massPlane

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


    def __str__(self):
        return f"{self.axes}"

    def addSource(self,dataLabel : str,dataFile : str ,dataFormat : str = None, 
            objectName : str = None, index : Union[List,str,int,None] = None,
                  unit = None, coordinateMap = None, scale=None, **args ):
        """
        Defines a single data sources for the plane.

        :param dataLabel: String with the dataLabel
                          possible data labels are defined in allowedDataLabels
                          (e.g. efficiencyMap, upperLimits, expectedUpperLimits,...)
        :param dataFile: Strings with the file path to the data file.
        :param dataFormat: Strings with the file format for the data file, e.g.
                           root, csv, embaked. If none, then file extension is
                           format.
        :param objectName: String with the object name stored in root-file or cMacro
        :param index: Index for objects in listOfPrimitives of ROOT.TCanvas,
                      if string and csv file, it specifies the value of the constraint
                      (see coordinate map)
        :param unit: Strings with unit for data (e.g. 'fb',None,'pb',...),
                     similar to "scale", can also be used to re-scale the data, either
                     via a '*' or a '/' symbol
        :param coordinateMap: Dictionaries with the mapping of txt file columns
                              to the x,y,... coordinates (e.g. {x : 0, y: 1, 'ul' :2})
                              'constraint' lists the constraint that needs to match "index",
                              see index!
        :param scale: Float to re-scale the data

        """
        if dataFormat == None:
            p1 = dataFile.rfind ( "." )
            dataFormat = dataFile[p1+1:]
            print ( f"[massPlaneObjects] setting format to '{dataFormat}'" )
        self.allInputFiles.append ( dataFile )

        dimensions = len(self.xvars)
        if not dataLabel in self.allowedDataLabels:
            logger.error( f"Data label {dataLabel} is not allowed. Try one of: {', '.join(self.allowedDataLabels)}.")
            sys.exit()
        if not 'exclusion' in dataLabel.lower():
            #Define the default coordinate mapping:
            if not coordinateMap:
                coordinateMap = dict([[xv,i] for i,xv in enumerate(allvars[:dimensions])])
                coordinateMap['value'] = -1 # dimensions
            #Initialize a data handler
            dataObject = DataHandler(dataLabel,coordinateMap,self.xvars,
                                     str(self._txDecay) )
        else:
            #Define the default 1D coordinate mapping for exclusion curves
            if not coordinateMap:
                coordinateMap = {x : 0, y : 1, 'value' : None}
                if not y in self.xvars: # 1d data
                    coordinateMap = {x : 0, 'value' : None}
            dataObject = ExclusionHandler(dataLabel,coordinateMap,self.xvars)
            self._exclusionCurves.append(dataObject)

        dataObject.dataUrl = self.dataUrl
        #Set source of object
        dataObject.setSource(dataFile, dataFormat,
                             objectName, index, unit, scale, **args )
        #Store it as a mass plane attribute:
        setattr(self,dataLabel,dataObject)

    def _removePoints_ ( self, points, obj ):
        """ remove all points within an area spanned by <points> """
        hull = Delaunay ( points )
        newdata=[]
        for i in obj.data:
            p = [ i[x], i[y] ]
            in_hull = hull.find_simplex ( p )
            if in_hull == -1: ## not in a cut-out region
                newdata.append ( i )
            else:
                logger.info ( "removing point %s as it is in cut-out region." % ( p ) )
        obj.data = newdata

    def removeArea(self,points):
        """ remove all points within an area spanned by <points> """
        points.append ( points[0] )
        for i in [ "efficiencyMap", "upperLimits", "expectedUpperLimits" ]:
            if hasattr ( self, i ):
                self._removePoints_ ( points, getattr(self,i) )

    def getParticleMasses(self,**xMass):

        """
        Translate a point of the plot, given by x- and y-values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
                     Keyword arguments must equal the variable name.
        :return: list containing two other lists. Each list contains floats, representing
        the masses of the particles of each branch in GeV
        """

        if self.branches == None:
            return []
        massArray = [br.getParticleMasses(**xMass) for br in self.branches]
        return massArray

    def getXYValues(self,massArray,widthArray=None):

        """
        Translate a mass array to a point of the plot.
        Returns a dictionary with the variable labels as keys and the values as values.

        :param massArray: list containing two other lists. Each list contains floats,
        representing the masses of the particles of each branch in GeV
        :param widthArray: list containing two other lists. Each list contains floats,
        representing the widths of the particles of each branch in GeV. If None,
        we assume a width-independent plane.
        :raise massArrayLenError: if length of mass array is unequal 2
        :raise unequalXYValuesError: if the branches return different values for x or y
        :return: None if mass array do not met the conditions of one branch
        else: {'x': x-value in GeV as float, 'y' : y-value in GeV as float, ..}
        """
        # print ( "@@0 widthArray", widthArray )
        # print ( "@@0 massArray", massArray )

        if len(massArray) != len(self.branches):
            logger.error("dimension of mass array (%d) inconsistent with branches length (%d)" % ( len(massArray), len(self.branches) ) )
            sys.exit()
        if widthArray != None and len(widthArray) != len(self.branches):
            logger.error("Width array inconsistent with branches length")
            sys.exit()
        xyArray = {}
        if widthArray == None:
            for i,mass in enumerate(massArray):
                xyDict = self.branches[i].getXYValues(mass)
                if xyDict is None:
                    return None
                for xvar,value in xyDict.items():
                    if xvar in xyArray:
                        #Check if x,y-values given by distinct branches agree:
                        if xyArray[xvar] != value and (abs(xyArray[xvar]+value) == 0.
                           or abs(xyArray[xvar]-value)/abs(xyArray[xvar]+value) > 1e-4):
                            return None
                    xyArray[xvar] = value
            return xyArray
        for i,(mass,width) in enumerate(zip(massArray,widthArray)):
            if self.axes[i]==['*']: ## skip the "any" branches
                continue
            xyDict = self.branches[i].getXYValues(mass,width)
            if xyDict is None:
                return None
            for xvar,value in xyDict.items():
                if xvar in xyArray:
                    #Check if x,y-values given by distinct branches agree:
                    if xyArray[xvar] != value and (abs(xyArray[xvar]+value) == 0.
                       or abs(xyArray[xvar]-value)/abs(xyArray[xvar]+value) > 1e-4):
                        return None
                xyArray[xvar] = value

        return xyArray

