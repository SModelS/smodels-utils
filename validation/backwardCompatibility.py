#!/usr/bin/env python3

"""
.. module: backwardCompatibility
   :synopsis: Collection of methods that we only need for backwards-compatibility
              between SModelS 2.0.0 and 1.2.x. The methods here are part of
              smodels-proper in 2.x but not in 1.2.x

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import unum
import numpy as np
from smodels.base.physicsUnits import GeV

def addUnit(obj,unit):
    """
    Add unit to object.
    If the object is a nested list, adds the unit to all of its elements.

    :param obj: Object without units (e.g. [[100,100.]])
    :param unit: Unit to be added to the object (Unum object, e.g. GeV)
    :return: Object with units (e.g. [[100*GeV,100*GeV]])
    """

    if isinstance(obj,list):
        return [addUnit(x,unit) for x in obj]
    elif isinstance(obj,tuple):
        return tuple([addUnit(x,unit) for x in obj])
    elif isinstance(obj,dict):
        return dict([[addUnit(x,unit),addUnit(y,unit)] for x,y in obj.items()])
    elif isinstance(obj,(float,int,unum.Unum)):
        return obj*unit
    else:
        return obj

def removeUnits(value,standardUnits):
    """
    Remove units from unum objects. Uses the units defined
    in physicsUnits.standard units to normalize the data.

    :param value: Object containing units (e.g. [[100*GeV,100.*GeV],3.*pb])
    :param standardUnits: Unum unit or Array of unum units defined to
                          normalize the data.
    :return: Object normalized to standard units (e.g. [[100,100],3000])
    """

    if isinstance(standardUnits,unum.Unum):
        stdunits = [standardUnits]
    else:
        stdunits = standardUnits

    if isinstance(value,list):
        return [removeUnits(x,stdunits) for x in value]
    if isinstance(value,tuple):
        return tuple([removeUnits(x,stdunits) for x in value])
    elif isinstance(value,dict):
        return dict([[removeUnits(x,stdunits),removeUnits(y,stdunits)] for x,y in value.items()])
    elif isinstance(value,unum.Unum):
        #Check if value has unit or not:
        if not value._unit:
            return value.asNumber()
        #Now try to normalize it by one of the standard pre-defined units:
        for unit in stdunits:
            y = (value/unit).normalize()
            if not y._unit:
                return value.asNumber(unit)
        raise SModelSError("Could not normalize unit value %s using the standard units: %s"
                       %(str(value),str(standardUnits)))
    else:
        return value

def rescaleWidth(width):
    """
    The function that is applied to all widths to
    map it into a better variable for interpolation.
    It grows logarithmically from zero (for width=0.)
    to a large number (machine dependent) for width = infinity.

    :param width: Width value (in GeV) with or without units

    :return x: Coordinate value (float)
    """

    if isinstance(width,unum.Unum):
        w = width.asNumber(GeV)
    else:
        w = width

    minWidth = 1e-30 #Any width below this can be safely considered to be zero
    maxWidth = 1e50 #Any width above this can be safely considered to be infinity
    w = (min(w,maxWidth)/minWidth) #Normalize the width and convert it to some finite number (if not finite)
    return np.log(1+w)

def unscaleWidth(x):
    """
    Maps a coordinate value back to width (with GeV unit).
    The mapping is such that x=0->width=0 and x=very large -> width = inf.

    :param x: Coordinate value (float)

    :return width: Width value (in GeV) with unit
    """

    minWidth = 1e-30 #Any width below this can be safely considered to be zero
    maxWidth = 1e50 #Any width above this can be safely considered to be infinity
    with np.errstate(over='ignore'): #Temporarily disable overflow error message
        #The small increase in x is required to enforce unscaleWidth(widthToCoordinae(np.inf)) = np.inf
        width = minWidth*(np.exp(x)-1)
        if width > maxWidth:
            width = np.inf
    return width*GeV
