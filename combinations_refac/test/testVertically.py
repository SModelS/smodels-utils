#!/usr/bin/env python3

"""
.. module:: testVertically
   :synopsis: Testing "vertically", meaning we run a walker with a defined database and
              seed.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys
sys.path.insert(0,"../")
import unittest
from modelWalker.randomWalker import RandomWalker
from tools import helpers
import scipy.stats

class VerticalTest(unittest.TestCase):

    def testRandomNumber(self):
        helpers.seedRandomNumbers ( 1 )
        r = scipy.stats.norm.rvs()
        self.assertAlmostEqual ( r, -0.6117564136500754 )

    def testRun(self):
        helpers.seedRandomNumbers ( 1 )
        walker = RandomWalker ( nsteps=2, dbpath="./testdb.pcl" )
        walker.walk()

if __name__ == "__main__":
    unittest.main()
