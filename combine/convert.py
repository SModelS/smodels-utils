#!/usr/bin/env python3

"""
.. module:: convertCountingAnalysis.py
   :synopsis: Here I am attempting to write a combine2pyhf converter for counting-only analyses. lets see.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import os

class DatacardConverter:
    def __init__ ( self ):
        self.datacard = None

    def readCombineCard ( self, datacard : os.PathLike ):
        print ( f"converting {datacard}" )
        import DatacardParser
        with open( datacard, 'r') as f:
            opts = type("opts", (object,), dict(bin=True, noJMax=False, stat=False, nuisancesToExclude=[], allowNoSignal=True, allowNoBackground=True))
            self.datacard = DatacardParser.parseCard(f, opts)

    def interact ( self ):
            import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

    def convert ( self, datacard : os.PathLike ):
        """ convert the datacard <datacar> """
        self.readCombineCard ( datacard )
        self.interact()

def main():
    import argparse
    ap = argparse.ArgumentParser(description="script to convert a combine datacard to a pyhf json")
    ap.add_argument('-c', '--datacard',
            help='path to the combine datacard [./sus20004.txt]', default='./sus20004.txt')
    args = ap.parse_args()
    converter = DatacardConverter()
    converter.convert ( args.datacard )

if __name__ == "__main__":
    main()
