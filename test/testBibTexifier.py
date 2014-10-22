#!/usr/bin/env python

"""
.. module:: testSlhaManipulator
   :synopsis: Tests the slha manipulation.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import unittest
import setPath
from smodels_tools.tools import bibTeXifier
import types

class TestBibTeXifier(unittest.TestCase):
    def testPositive(self):
        tex=bibTeXifier.BibTeXifier ( "SUS14011" ).bibtex
        self.assertTrue ( tex.find("CMS-PAS-SUS-14-011")> 300 ) ## 392

    def testNegative(self):
        texifier=bibTeXifier.BibTeXifier ( "SUS17011" )
        self.assertEqual ( texifier.bibtex, "No bibtex entry found for None" )

if __name__ == "__main__":
    unittest.main()
