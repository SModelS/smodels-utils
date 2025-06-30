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
            signalRegions = list ( self.datacard.obs.keys() )
            signalRegions.sort()
            self.signalRegions = signalRegions


    def writeObservations ( self ):
        self.fhandle.write ( '    "observations": [\n' )
        for i,sr in enumerate(self.signalRegions):
            value = int ( self.datacard.obs[sr] )
            self.fhandle.write ( '        {\n' )
            self.fhandle.write ( '            "data": [\n' )
            self.fhandle.write ( f'                {value}\n' )
            self.fhandle.write ( '            ],\n' )
            self.fhandle.write ( f'            "name": "{sr}"\n' )
            comma = "," if i+1 < len(self.datacard.obs) else ""
            self.fhandle.write ( f'        }}{comma}\n' )
        self.fhandle.write ( '    ],\n' )

    def writeJsonFile ( self, outfile : os.PathLike ):
        self.outfile = outfile
        self.fhandle = open ( outfile, "w" )
        self.fhandle.write ( "{\n" )
        self.writeObservations()
        self.fhandle.write ( '    version: "1.0.0"\n' )
        self.fhandle.write ( "}\n" )
        self.pprint ( f"{outfile} written." )
        self.fhandle.close()

    def pprint ( self, *args ):
        print ( f"[convert] {' '.join(map(str,args))}" )

    def interact ( self ):
        import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

    def show ( self ):
        if os.path.exists ( self.outfile ):
            with open ( self.outfile, "r" ) as f:
                lines = f.readlines()
                f.close()
                for line in lines:
                    print ( line, end = "" )

    def convert ( self, datacard : os.PathLike, outfile : os.PathLike ) -> bool:
        """ convert the datacard <datacar>
        :returns: true if successful
        """
        self.readCombineCard ( datacard )
        self.writeJsonFile ( outfile )

def main():
    import argparse
    ap = argparse.ArgumentParser(description="script to convert a combine datacard to a pyhf json")
    ap.add_argument('-c', '--datacard',
            help='path to the combine datacard [./sus20004.txt]', default='./sus20004.txt')
    ap.add_argument('-o', '--outfile',
            help='output file [./sus20004.json]', default='./sus20004.json')
    ap.add_argument('-i', '--interact', action="store_true",
            help='after writing json file, start interactive shell' )
    args = ap.parse_args()
    converter = DatacardConverter()
    converter.convert ( args.datacard, args.outfile )
    if args.interact:
        converter.interact()

if __name__ == "__main__":
    main()
