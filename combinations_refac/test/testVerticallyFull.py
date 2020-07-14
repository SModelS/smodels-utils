#!/usr/bin/env python3

"""
.. module:: testVertically
   :synopsis: Testing "vertically", meaning we run a walker with a defined database and
              seed.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys,os
sys.path.insert(0,"../")
import unittest
from walker.randomWalker import RandomWalker
from tools import helpers
helpers.seedRandomNumbers ( 1 )

class VerticalTest(unittest.TestCase):

    def testRun(self):

        if os.path.isfile('H0.pcl'):
            os.remove('H0.pcl')

        walker = RandomWalker ( nsteps=11, dbpath="./database.pcl", nevents = 10000 )
        walker.walk()
        # for p in walker.hiscoreList.hiscores: print(p,'\n',p.step,p.K,p.Z)

        self.assertAlmostEqual ( walker.protomodel.K, 2.047, 2 )
        self.assertEqual ( len(walker.hiscoreList.hiscores), 1 )
        self.assertAlmostEqual ( walker.hiscoreList.hiscores[0].Z, 2.4388,2 )
        self.assertEqual ( walker.hiscoreList.hiscores[0].step, 1 )
        # print(walker.protomodel.K)
        # print(len(walker.hiscoreList.hiscores))
        # print(walker.hiscoreList.hiscores[0].Z)
        # print(walker.hiscoreList.hiscores[0].step)
        # print( walker.protomodel.masses)
        # print( walker.hiscoreList.hiscores[0].masses)
        self.assertAlmostEqual ( walker.protomodel.masses[1000004], 420.069, 2 )
        self.assertAlmostEqual ( walker.protomodel.masses[1000022], 240.309, 2 )
        self.assertAlmostEqual ( walker.hiscoreList.hiscores[0].masses[1000022], 240.309, 2 )
        self.assertAlmostEqual ( walker.hiscoreList.hiscores[0].masses[1000016], 1943.707, 2 )

if __name__ == "__main__":
    unittest.main()
