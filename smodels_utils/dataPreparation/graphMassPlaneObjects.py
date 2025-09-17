#!/usr/bin/env python3

"""
.. module:: graphMassPlaneObjects
   :synopsis: Holds object representing one mass plane,
              for graphs

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys
import numpy as np
from sympy import var, Eq, lambdify, linsolve, solve, N, And, sqrt, Symbol, core, Float, linear_eq_to_matrix
from scipy.spatial import Delaunay
from itertools import permutations
from smodels_utils.dataPreparation.dataHandlerObjects import \
         DataHandler,ExclusionHandler
from smodels_utils.dataPreparation.massPlaneObjectsBase import _lambdify, \
         MassPlaneBase, allvars, x, y, z, w
import string
import logging
from smodels_utils.helper.various import round_to_n
from typing import Union, Dict, List
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

class GraphMassPlane(MassPlaneBase):
    """
    Holds all information related to one mass plane
    a mass plane is defined by their axes.
    The variables defined in infoAttr are passed to the corresponding
    txname to be written in txname.txt
    """

    @classmethod
    def getNiceAxes(cls, axesStr : Union[dict,str] ) -> str:
        """
        Convert the axes definition format, e.g. {0 : 'x', 1 : 'y', 2 : 'x', 3 : 'y'}
        to a nicer format: x_y_

        :param axesStr: string defining axes in the old format
        :return: string with a nicer representation of the axes
        (more suitable for printing, in filenames)
        """

        if axesStr == "":
            logger.error ( "Axes field is empty: cannot validate." )
            return None
        x,y,z,w = var('x y z w')
        axesDict = axesStr
        if type(axesDict)==str:
            axesDict = eval(axesStr,{'x' : x, 'y' : y, 'z': z, 'w': w})

        def isSymmetrical ( axesDict : Dict ) -> bool:
            """ check if dicionary is symmetrical """
            if len(axesDict)%2==1:
                return False ## odd number of entries
            n = int(len(axesDict)/2)
            for i in range(n):
                if axesDict[i] != axesDict[i+n]:
                    return False
            return True
        if isSymmetrical ( axesDict ):
            n = int(len(axesDict)/2)
            for i in range(n,2*n):
                axesDict.pop(i)
        ret = "_".join ( map ( str, axesDict.values() ) )
        ret = ret.replace("/","d")
        # print ( f"@@ graphMassPlaneObjects {axesDict} turned into {ret}" )
        return ret


    def __init__( self, txDecay, parametersMap):
        """
        sets the branches to the given axes and initialize the mass plane related
        values an objects
        :param txDecay: object of type TxDecay
        :param parametersMap: the full mass array containing equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [[x,y],[x,y]])
        """
        self._txDecay = txDecay
        self.figureUrl = None
        self.dataUrl = None
        self.allInputFiles = []

        self.parametersMap = parametersMap
        self._exclusionCurves = []
        xvars = set()
        for k,v in parametersMap.items():
            if type(v) not in [ str ]:
                v=str(v)
            xvars.add ( Symbol(v) )
        self.xvars = list(xvars)

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
        parametersMap = eval(string)
        massPlane = GraphMassPlane(txname,parametersMap)

        return massPlane

    def __str__(self):
        return f"{self.parametersMap}"

    def addSource(self,dataLabel,dataFile,dataFormat=None, objectName=None,index=None,
                  unit=None,coordinateMap=None,scale=None, **args ):
        """
        Defines a single data sources for the plane.

        :param dataLabel: Srings with the dataLabel
                          possible data labels are defined in allowedDataLabels
                          (e.g. efficiencyMap, upperLimits, expectedUpperLimits,...)
        :param dataFile: Strings with the file path to the data file.
        :param dataFormat: Strings with the file format for the data file, e.g.
                           root, csv, embaked. If none, then file extension is
                           format.
        :param objectName: String with the object name stored in root-file or cMacro
        :param index: Index for objects in listOfPrimitives of ROOT.TCanvas
                      if list then entries get added up
                      if dictionary then entries get added up with values as weights
        :param unit: Strings with unit for data (e.g. 'fb',None,'pb',...),
                     similar to "scale", can also be used to re-scale the data, either
                     via a '*' or a '/' symbol
        :param coordinateMap: Dictionaries with the mapping of txt file columns
                            to the x,y,... coordinates (e.g. {x : 0, y: 1, 'ul' :2})
        :param scale: Float to re-scale the data

        """
        if dataFormat == None:
            p1 = dataFile.rfind ( "." )
            dataFormat = dataFile[p1+1:]
            print ( f"[massPlaneObjects] setting format to '{dataFormat}'" )
        self.allInputFiles.append ( dataFile )

        # print ( "adding", dataLabel, dataFile, dataFormat )
        # import IPython ; IPython.embed() ; sys.exit(-1)
        dimensions = len(self.xvars)
        if not dataLabel in self.allowedDataLabels:
            logger.error( f"Data label {dataLabel} is not allowed. Try one of: {', '.join(self.allowedDataLabels)}.")
            sys.exit()
        if not 'exclusion' in dataLabel.lower():
            #Define the default coordinate mapping:
            if not coordinateMap:
                coordinateMap = dict([[xv,i] for i,xv in enumerate(allvars[:dimensions])])
                coordinateMap['value'] = dimensions
            #Initialize a data handler
            dataObject = DataHandler(dataLabel,coordinateMap,self.xvars,
                                     str(self._txDecay) )
        else:
            #Define the default 1D coordinate mapping for exclusion curves
            if not coordinateMap:
                coordinateMap = {x : 0, y : 1, 'value' : None}
                if not y in self.xvars: # 1d data
                    coordinateMap = {x : 0, 'value' : None}
            dataObject = ExclusionHandler(dataLabel,coordinateMap,self.xvars,self.parametersMap )
            self._exclusionCurves.append(dataObject)

        dataObject.dataUrl = self.dataUrl
        #Set source of object
        dataObject.setSource(dataFile, dataFormat,
                             objectName, index, unit, scale, **args )
        #Store it as a mass plane attribute:
        setattr(self,dataLabel,dataObject)

    def getParticleMasses(self,**xMass):

        """
        Translate a point of the plot, given by x- and y-values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
                     Keyword arguments must equal the variable name.
        :return: list containing two other lists. Each list contains floats, representing
        the masses of the particles of each branch in GeV
        """
        # print ( "FIXME implement, getParticleMasses", xMass, "parameterMap is", self.parametersMap )
        ret = [0]*(1+max(self.parametersMap.keys()))
        for k,v in self.parametersMap.items():
            value = str(v)
            for variable,mass in xMass.items():
                value = value.replace(variable,str(mass))
            ret[k]=eval(value)
        return ret

    def hasSimilarEquationAlready ( self, eqs : List, e ):
        """ Check if we have a similar equation already """
        # print ( f"@@12 check if {e} is fuzzily in {eqs}" )
        if len(eqs)==0:
            return False
        for eq in eqs:
            if eq.lhs == e.lhs: ## lefthand sides match
                if type(eq.rhs) == Float and type(e.rhs) == Float:
                    if 1e-8 < abs ( e.rhs - eq.rhs) < 1.6:
                        # print ( f"@@13 fuzzy match!" )
                        return True
        return False

    def getXYValues(self, parameters : List ) -> Union[None,Dict]:
        """
        Translate mass and width arrays to a 2d point in the plot.
        Returns a dictionary for the x and y coordinates.

        :param parameters: a list of masses and widths, corresponding to the dataMap
        :returns: None if an error occurs,
        else {'x': x-value in GeV as float, 'y' : y-value in GeV as float, ..}
        """
        # print ( f"@@11 getXYValues {parameters}" )

        ret = {}
        eqs, free_symbols = set(), set()
        from sympy.parsing.sympy_parser import parse_expr
        for index,param in self.parametersMap.items():
            rhs = float("nan")
            ## FIXME when is it widths instead??
            # print ( f"parameters are {parameters}" )
            if type(parameters[index]) in [ float ]:
                # ret[str(param)] = float ( parameters[index] )
                rhs = round_to_n ( float ( parameters[index] ), 10 )
            elif type(parameters[index]) in [ tuple, list ]:
                # ret[str(param)] = float ( parameters[index][1] )
                rhs = round_to_n ( float ( parameters[index][1] ), 10 )
            elif parameters[index]=="stable":
                rhs = 0.
            lhs = parse_expr ( str(param) )
            if type(lhs)==core.numbers.Float:
                lhs = round_to_n ( float(lhs), 10 )
            if lhs == 0. and rhs == 1.:
              continue # hack for now FIXME
            if type(lhs)==Float and type(rhs)==Float and \
                    1e-8 < abs ( lhs - rhs ) < 1.6:
                continue # hack for now FIXME
            e = Eq ( lhs, rhs )
            if e == True: ## take out trivial expressions
                continue
            if e == False: # if a numerical comparison is wrong, we can stop here
                return ret
            if True: # not self.hasSimilarEquationAlready ( eqs, e ):
                eqs.add ( e )
            for xhs in [ lhs, rhs ]:
                if hasattr ( xhs, "free_symbols" ):
                    for x in xhs.free_symbols:
                        free_symbols.add ( x )

        eqs = list(eqs)
        free_symbols = list(free_symbols)
        try:
            d = linsolve ( eqs, free_symbols )
            if len(d)>0:
                d = dict(zip(free_symbols,list(d)[0]))
            else:
                d = {}
        except Exception as e:
            pass
        if len(d) == 0:
            d = solve ( eqs, simplify=False )
        if len(d) == 0: # d == {} or d == []:
            A, b = linear_eq_to_matrix(eqs, free_symbols)
            A_np = np.array(A, dtype=float)
            b_np = np.array(b, dtype=float)
            sol, residuals, rank, s = np.linalg.lstsq(A_np, b_np, rcond=None)
            d = {}
            if sum(residuals)<1e-2:
                for k,v in zip(free_symbols,sol):
                    d[k]=v[0]

        ret = {}
        if d == []:
            return ret
        for k,v in d.items():
            ret[str(k)]=float(v)
        #if d == {}:
        #    import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()
        # import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()
        # print ( f"@@11 solved {parameters}: {d}" )
        return ret
