#!/usr/bin/env python3

import pickle, os, sys
from randomWalk import Model # RandomWalker
from hiscore import Hiscore
import IPython
from pympler.asizeof import asizeof

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore checker. allows a few modifications to be performed on the hiscore list' )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file with hiscores [best.pcl]',
            type=str, default="best.pcl" )
    argparser.add_argument ( '-i', '--interactive', help='start interactive session',
                             action="store_true" )
    argparser.add_argument ( '-t', '--trim', help='trim the hiscore list to the nth entry',
                             type=int, default=0 )
    argparser.add_argument ( '-s', '--save', help='save the updated hiscore list under this filename [None]',
                             type=str,default=None )
    args = argparser.parse_args()
    hiscore = Hiscore ( 0, False, args.picklefile )
    if args.trim>0:
        hiscore.trimModels( args.trim )
    if args.save not in  [ "", None ]:
        hiscore.writeListToPickle( args.save )
    print ( "Check variable: hiscore" )
    if args.interactive:
        IPython.embed()

if __name__ == "__main__":
    main()
