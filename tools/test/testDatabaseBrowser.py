#!/usr/bin/env python

"""
.. module:: testDatabaseBrowser
   :synopsis: Tests for databaseBrowser.
   
.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Wolfgang Magerl <wolfgang.magerl@gmail.com>

"""
import unittest
import setPath
from smodels_tools.tools import databaseBrowser
from smodels_tools.tools.databaseBrowserException import DatabaseNotFoundException

class TestDatabaseBrowser(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        self.browser = databaseBrowser.Browser("../../../smodels-database")
        
    def testDatabaseVersion(self):
        version = self.browser.databaseVersion
        self.assertIsNotNone(version)
        
    def testIncorrectBase(self):
        with self.assertRaises(DatabaseNotFoundException):
            databaseBrowser.Browser("this/path/does/not/exist")
            
    def testValidAnalysis(self):
        analysis = self.browser._validateAnalysis('SUS13016')
        self.assertEqual(analysis, 'SUS13016')
    
    def testNotValidateAnalysis(self):
        analysis = self.browser._validateAnalysis('bla')
        self.assertEqual(analysis, None)
    
if __name__ == '__main__':
    unittest.main()
