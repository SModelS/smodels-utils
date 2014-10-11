#!/usr/bin/env python

"""
.. module:: testSlhaManipulator
   :synopsis: Tests the slha manipulation.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import unittest
import setPath

class TestSlhaManipulator(unittest.TestCase):

    def assertEqualFiles(self,file1,file2):
        """ check that file1 == file2 """
      #  print "assertEqualFiles",file1,file2
        try:
            f1=open(file1)
            lines1=f1.readlines()
            f1.close()
            f2=open(file2)
            lines2=f2.readlines()
            f2.close()
            for l in zip(lines1,lines2):
                self.assertEqual ( l[0], l[1] )
        except IOError,e:
            return False

    def testRemoveXSecs(self):
        """ remove xsecs completely """
        from smodels_tools.tools import slhaManipulator
        slhaManipulator.removeXSecs ( "../slha/andrePT4.slha", "/tmp/test.slha" )
        self.assertEqualFiles ( "../slha/andrePT4.slha", "/tmp/test.slha" )
        return None

if __name__ == "__main__":
    unittest.main()
