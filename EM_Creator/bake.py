#!/usr/bin/env python3

"""
.. module:: bake
        :synopsis: the script that does the EM baking.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import argparse
import numpy
from mg5Wrapper import MG5Wrapper
from ma5Wrapper import MA5Wrapper
from emCreator import emCreator

def main():
    topology = "T2tt"
    analysis="atlas_sus_2016_07"
    nevents = 10
    print ( "baking %s:%s" % (analysis,topology ) )
    motherRange = numpy.arange(500, 2500, 50 )
    mg5 = mg5Wrapper ( nevents = nevents )

if __name__ == "__main__":
    main()
    ## T2, mother 300-1800, daughter 0 - 1800
