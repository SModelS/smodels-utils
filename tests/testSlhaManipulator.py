#!/usr/bin/env python

"""
.. module:: testSlhaManipulator
   :synopsis: Tests the slha manipulation.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import unittest
import setPath

class TestSlhaManipulator(unittest.TestCase):

    def testRemoveXSecs(self):
        """ remove xsecs completely """
        from smodels_tools.tools import slhaManipulator
        slhaManipulator.removeXSecs ( "../slha/andrePT4.slha", "test.slha" )

if __name__ == "__main__":
    unittest.main()
