#!/usr/bin/env python3

"""
.. module: backwardCompatibility
   :synopsis: Collection of methods that we only need for backwards-compatibility
              between SModelS 2.0.0 and 1.2.x. The methods here are part of 
              smodels-proper in 2.x but not in 1.2.x

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import unum

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
