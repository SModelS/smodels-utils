#!/usr/bin/env python3

"""
.. module:: bake
        :synopsis: the script that does the EM baking.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import argparse

def main():
    topology = "T2tt"
    analysis="atlas_sus_2016_07"
    print ( "baking %s:%s" % (analysis,topology ) )

if __name__ == "__main__":
    main()
