#!/usr/bin/env python3

"""
.. module:: massPlaneObjects
   :synopsis: Holds object representing one mass plane

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys
import string
import logging
from typing import Dict, List, Optional

from sympy import var

from smodels_utils.dataPreparation.massPlaneObjectsBase import \
         MassPlaneBase, x, y, z, w

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

def _xyValuesAgree ( first : float, second : float ) -> bool:
    """Check whether two x/y values computed by different branches agree.

    Values are considered equal if they differ by at most 1e-4 relative to
    their sum.

    :param first: x/y value from one branch
    :param second: x/y value from another branch
    :return: True if the values agree
    """
    if first == second:
        return True
    return not ( abs ( first + second ) == 0. or
                 abs ( first - second ) / abs ( first + second ) > 1e-4 )

class MassPlane(MassPlaneBase):
    """
    Holds all information related to one mass plane
    a mass plane is defined by their axes.
    The variables defined in infoAttr are passed to the corresponding
    txname to be written in txname.txt
    """

    def __init__( self, txDecay, massArray : List ) -> None:
        """
        sets the branches to the given axes and initialize the mass plane related
        values an objects

        :param txDecay: object of type TxDecay
        :param massArray: the full mass array containing equations which relate the
                          physical masses and the plane coordinates, using the
                          pre-defined 'x','y',.. symbols (e.g. [[x,y],[x,y]])
        """
        self.branches = []
        self._initCommon ( txDecay )
        for i, brMasses in enumerate ( massArray ):
            if not isinstance ( brMasses, list ):
                logger.error( f"Mass array must be in the format [[m1,m2,..],[m3,m4,..]], was {massArray}")
                sys.exit()
            self.setBranch( branchNumber=i, branchMasses=brMasses )

        self.axes = massArray
        #Store plane variables (x,y,..)
        xvars = []
        for br in self.branches:
            for xvar in br._xvars:
                if xvar not in xvars:
                    xvars.append ( xvar )
        self.xvars = xvars #All variables used in defining the axes

    @classmethod
    def _fromParsedString ( cls, txname, parsed ) -> MassPlaneBase:
        """Build a MassPlane, or a GraphMassPlane for dictionary axes.

        :param txname: txname string (e.g. T1)
        :param parsed: the evaluated axes expression
        :return: MassPlane or GraphMassPlane instance
        """
        if isinstance ( parsed, dict ):
            from smodels_utils.dataPreparation.graphMassPlaneObjects import \
                 GraphMassPlane
            return GraphMassPlane ( txname, parsed )
        return cls ( txname, parsed )

    @classmethod
    def getNiceAxes( cls, axesStr : str ) -> Optional[str]:
        """
        Convert the axes definition format ('[[x,y],[x,y]]')
        to a nicer format ('Eq(MassA,x)_Eq(MassB,y)_Eq(MassA,x)_Eq(MassB,y)')

        :param axesStr: string defining axes in the old format

        :return: string with a nicer representation of the axes (more suitable for printing)
        """
        if axesStr == "":
            logger.error ( "Axes field is empty: cannot validate." )
            return None
        axes = eval( axesStr, { 'x' : x, 'y' : y, 'z' : z, 'w' : w } )

        eqList = []
        for ib, br in enumerate ( axes ):
            if ib == 0:
                mStr, wStr = 'Mass', 'Width'
            else:
                mStr, wStr = 'mass', 'width'
            mList = []
            for im, eq in enumerate ( br ):
                if isinstance ( eq, tuple ):
                    mList.append( 'Eq(%s,%s)'
                                   %(var(mStr+string.ascii_uppercase[im]),eq[0]) )
                    mList.append( 'Eq(%s,%s)'
                                   %(var(wStr+string.ascii_uppercase[im]),eq[1]) )
                else:
                    mList.append( f'Eq({var(mStr + string.ascii_uppercase[im])},{eq})' )
            mStr = "_".join ( mList )
            eqList.append ( mStr )

        #Simplify symmetric branches:
        if len(eqList) == 2 and eqList[0].lower() == eqList[1].lower():
            eqStr = f"2*{eqList[0]}"
        else:
            eqStr = "__".join ( eqList )

        eqStr = eqStr.replace(" ","")

        return eqStr

    def __str__( self ) -> str:
        return f"{self.axes}"

    def getParticleMasses( self, **xMass ) -> List:
        """
        Translate a point of the plot, given by x- and y-values to a mass Array

        :param xMass: x,y,... values (length depends on the number of dimensions
                      of the plot). Keyword arguments must equal the variable name.
        :return: list containing two other lists. Each list contains floats,
                 representing the masses of the particles of each branch in GeV
        """
        if self.branches is None:
            return []
        return [ br.getParticleMasses( **xMass ) for br in self.branches ]

    def getXYValues( self, massArray : List,
            widthArray : Optional[List] = None ) -> Optional[Dict]:
        """
        Translate a mass array to a point of the plot.
        Returns a dictionary with the variable labels as keys and the values as values.

        :param massArray: list containing two other lists. Each list contains floats,
                          representing the masses of the particles of each branch in GeV
        :param widthArray: list containing two other lists. Each list contains floats,
                           representing the widths of the particles of each branch in GeV.
                           If None, we assume a width-independent plane.
        :return: None if mass array do not met the conditions of one branch
                 else: {'x': x-value in GeV as float, 'y' : y-value in GeV as float, ..}
        """
        if len(massArray) != len(self.branches):
            logger.error(f"dimension of mass array ({len(massArray)}) inconsistent with branches length ({len(self.branches)})" )
            sys.exit()
        if widthArray is not None and len(widthArray) != len(self.branches):
            logger.error("Width array inconsistent with branches length")
            sys.exit()

        if widthArray is None:
            widthArray = [ None ] * len ( massArray )
            skipWildcards = False
        else:
            skipWildcards = True

        xyArray = {}
        for i, ( mass, width ) in enumerate ( zip ( massArray, widthArray ) ):
            if skipWildcards and self.axes[i] == ['*']:  # skip the "any" branches
                continue
            xyDict = self.branches[i].getXYValuesV2 ( mass, width )
            if xyDict is None:
                return None
            for xvar, value in xyDict.items():
                #Check if x,y-values given by distinct branches agree:
                if xvar in xyArray and not _xyValuesAgree ( xyArray[xvar], value ):
                    return None
                xyArray[xvar] = value

        return xyArray
