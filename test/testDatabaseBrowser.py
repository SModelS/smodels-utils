#!/usr/bin/env python

"""
.. module:: testDatabaseBrowser
   :synopsis: Tests some elementary database browser functionality

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import unittest
import setPath
from smodels_utils.helper import databaseBrowser
from smodels import installation
import types

class TestDatabaseBrowser(unittest.TestCase):
    def testRuns(self):
        dir=installation.installDirectory()+"/validation/database/"
        browser=databaseBrowser.Browser( dir )
        self.assertEqual ( browser.getRuns(), ['ATLAS8TeV', '2012'] )
    def testTopos(self):
        dir=installation.installDirectory()+"/validation/database/"
        browser=databaseBrowser.Browser( dir )
        self.assertTrue ( "T1" in browser.getTopologies() )


if __name__ == "__main__":
    unittest.main()
