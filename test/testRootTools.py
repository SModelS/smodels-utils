#!/usr/bin/env python

"""
.. module:: testSlhaManipulator
   :synopsis: Tests the slha manipulation.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import unittest
import setPath
from smodels_utils.helper import rootTools
import types

class TestRootTools(unittest.TestCase):

    def testVersionNumber(self):
        """ remove xsecs completely """
        v=rootTools.getRootVersion(astuple=True )
        return ( v[0]>4 and v[0]<7 )

    def testPaths(self):
        rp=rootTools.getRootPath()
        rlp=rootTools.getRootLibraryPath()
        rrpp=rootTools.getRootPythonPath()
        assert ( type(rp) == type(rlp) and type(rlp)==type(rrpp) and type(rrpp) == types.StringType )

if __name__ == "__main__":
    unittest.main()
