#!/usr/bin/env python3

"""
.. module:: testSwaps
   :synopsis: Test the swapping two particles

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys
sys.path.insert(0,"../")
import unittest
from protomodel import ProtoModel
from manipulator import Manipulator

class SwapTest(unittest.TestCase):
    def testSwaps(self):
        p = ProtoModel ( 1, dbpath = "../../../smodels-database" )
        p.masses[1000006]=1000.
        p.masses[2000006]=800.
        p.decays[1000006]={(1000022,6):0.8,(1000024,6):0.2}
        p.decays[2000006]={(1000022,6):0.7,(1000024,6):0.3}
        m = Manipulator ( p )
        self.assertTrue ( p.dict() == m.M.dict() )
        m.checkSwaps()
        self.assertTrue ( p.masses[1000006] == 800. )
        self.assertTrue ( p.masses[2000006] == 1000. )
        self.assertTrue ( p.decays[1000006][(1000022,6)] == .7 )

if __name__ == "__main__":
    unittest.main()
