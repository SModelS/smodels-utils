#!/usr/bin/env python3

"""
.. module:: graphMassPlaneObjects
   :synopsis: Holds object representing one mass plane,
              for graphs

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging
import numpy as np
from sympy import var, Eq, linsolve, solve, Float, Symbol, linear_eq_to_matrix
from smodels_utils.dataPreparation.dataHandlerObjects import ExclusionHandler
from smodels_utils.dataPreparation.massPlaneObjectsBase import MassPlaneBase
from smodels_utils.helper.various import round_to_n
from typing import Dict, List, Optional, Union

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
    def getNiceAxes( cls, axesStr : Union[dict,str] ) -> Optional[str]:
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
        if isinstance ( axesDict, str ):
            axesDict = eval(axesStr,{'x' : x, 'y' : y, 'z': z, 'w': w})

        def isSymmetrical ( axesDict : Dict ) -> bool:
            """ check if dictionary is symmetrical """
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
        return ret

    def __init__( self, txDecay, parametersMap : Dict ) -> None:
        """
        sets the branches to the given axes and initialize the mass plane related
        values an objects

        :param txDecay: object of type TxDecay
        :param parametersMap: the full mass array containing equations which relate the
                              physical masses and the plane coordinates, using the
                              pre-defined 'x','y',.. symbols (e.g. [[x,y],[x,y]])
        """
        self._initCommon ( txDecay )
        self.parametersMap = parametersMap
        self.xvars = list ( { Symbol ( str ( v ) ) for v in parametersMap.values() } )

    def _defaultDataCoordinateMap ( self ) -> Dict:
        """Return the default mapping of data columns to plane variables.

        For graph planes the value column follows the coordinate columns.

        :return: dictionary mapping the plane variables (and 'value') to
                 column indices
        """
        coordinateMap = super()._defaultDataCoordinateMap()
        coordinateMap["value"] = len ( self.xvars )
        return coordinateMap

    def _makeExclusionHandler ( self, dataLabel : str,
            coordinateMap : Dict ) -> ExclusionHandler:
        """Create the exclusion handler, passing the parameters map on."""
        return ExclusionHandler ( dataLabel, coordinateMap, self.xvars,
                                  self.parametersMap )

    def __str__( self ) -> str:
        return f"{self.parametersMap}"

    def getParticleMasses( self, **xMass ) -> List:
        """
        Translate a point of the plot, given by x- and y-values to a mass Array

        :param xMass: x,y,... values (length depends on the number of dimensions
                      of the plot). Keyword arguments must equal the variable name.
        :return: list containing floats, representing the masses of the
                 particles in GeV
        """
        ret = [ 0 ] * ( 1 + max ( self.parametersMap.keys() ) )
        for k, v in self.parametersMap.items():
            value = str ( v )
            for variable, mass in xMass.items():
                value = value.replace ( variable, str ( mass ) )
            ret[k] = eval ( value )
        return ret

    def getXYValues( self, parameters : List ) -> Optional[Dict]:
        """
        Translate mass and width arrays to a 2d point in the plot.
        Returns a dictionary for the x and y coordinates.

        :param parameters: a list of masses and widths, corresponding to the dataMap
        :returns: None if an error occurs,
                  else {'x': x-value in GeV as float, 'y' : y-value in GeV as float, ..}
        """
        ret = {}
        eqs, free_symbols = set(), set()
        from sympy.parsing.sympy_parser import parse_expr
        for index,param in self.parametersMap.items():
            rhs = float("nan")
            ## FIXME when is it widths instead??
            if type(parameters[index]) in [ float ]:
                rhs = round_to_n ( float ( parameters[index] ), 10 )
            elif type(parameters[index]) in [ tuple, list ]:
                rhs = round_to_n ( float ( parameters[index][1] ), 10 )
            elif parameters[index]=="stable":
                rhs = 0.
            lhs = parse_expr ( str(param) )
            if type(lhs)==Float:
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
        except Exception:
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
        return ret
