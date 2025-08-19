#!/usr/bin/env python3

"""
.. module:: slhaHelpers
   :synopsis: small functions that help with slha file creation

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os
import numpy as np

def hasXSecs ( slhafile : os.PathLike ):
    """ does the given slha file have xsecs? """
    if not os.path.exists ( slhafile ):
        return None
    import pyslha
    p = pyslha.readSLHAFile ( slhafile )
    hasValidXSec = False
    if len (p.xsections)>0:
        for k,v in p.xsections.items():
            for xsec in v.xsecs:
                if not np.isnan ( xsec.value ):
                    hasValidXSec = True
        return hasValidXSec
    return hasValidXSec
