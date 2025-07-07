#!/usr/bin/env python3

"""
.. module:: slhaHelpers
   :synopsis: small functions that help with slha file creation

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os

def hasXSecs ( slhafile : os.PathLike ):
    """ does the given slha file have xsecs? """
    if not os.path.exists ( slhafile ):
        return None
    import pyslha
    p = pyslha.readSLHAFile ( slhafile )
    if len (p.xsections)>0:
        return True
    return False
