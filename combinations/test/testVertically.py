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
from walker import RandomWalker
import helpers
import scipy.stats
import protomodel

protomodel.maxevents[0]=1000

class VerticalTest( unittest.TestCase ):

    def testRandomNumber(self):
        helpers.seedRandomNumbers ( 1 )
        r = scipy.stats.norm.rvs()
        self.assertAlmostEqual ( r, -0.6117564136500754 )

    def testRun(self):
        helpers.seedRandomNumbers ( 1 )
        walker = RandomWalker ( nsteps=10, dbpath="./testdb.pcl" )
        ret = walker.walk()
        self.assertAlmostEqual ( walker.protomodel.K, -0.666667, 3 )
        self.assertAlmostEqual ( walker.protomodel.masses[1000024], 619.764, 3 )
        self.assertAlmostEqual ( walker.protomodel.decays[1000023][(1000022, 23)], 0.922, 3 )

if __name__ == "__main__":
    unittest.main()
