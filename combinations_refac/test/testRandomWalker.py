#!/usr/bin/env python3

"""
.. module:: testVertically
   :synopsis: Testing "vertically", meaning we run a walker with a defined database and
              seed.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys,os,glob
sys.path.insert(0,"../")
import unittest
from walker.randomWalker import RandomWalker
from tools import helpers


class VerticalTest(unittest.TestCase):

    def testRun(self):

        if os.path.isfile('H0.pcl'):
            os.remove('H0.pcl')
        helpers.seedRandomNumbers ( 1 )
        walker = RandomWalker ( nsteps=11, dbpath="./database.pcl", nevents = 10000 )
        walker.walk()
        # for p in walker.hiscoreList.hiscores: print(p,'\n',p.step,p.K,p.Z)

        self.assertAlmostEqual ( walker.protomodel.K, 2.047, 2 )
        self.assertEqual ( len(walker.hiscoreList.hiscores), 1 )
        self.assertAlmostEqual ( walker.hiscoreList.hiscores[0].Z, 2.4388,2 )
        self.assertEqual ( walker.hiscoreList.hiscores[0].step, 1 )
        self.assertAlmostEqual ( walker.protomodel.masses[1000004], 420.069, 2 )
        self.assertAlmostEqual ( walker.protomodel.masses[1000022], 240.309, 2 )
        self.assertAlmostEqual ( walker.hiscoreList.hiscores[0].masses[1000022], 240.309, 2 )
        self.assertAlmostEqual ( walker.hiscoreList.hiscores[0].masses[1000016], 1943.707, 2 )

        #Remove files generated during run
        for f in glob.glob('.cur*slha'):
            os.remove(f)

if __name__ == "__main__":
    unittest.main()
