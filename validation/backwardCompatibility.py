#!/usr/bin/env python3

"""
.. module: backwardCompatibility
   :synopsis: Collection of methods that we only need for backwards-compatibility
              between SModelS 2.0.0 and 1.2.x. The methods here are part of 
              smodels-proper in 2.x but not in 1.2.x

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import unum

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
