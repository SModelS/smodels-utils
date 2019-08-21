#!/usr/bin/env python3

import pickle, os, sys
from randomWalk import Model # RandomWalker
from hiscore import Hiscore
import IPython
# from pympler.asizeof import asizeof

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore checker. allows a few modifications to be performed on the hiscore list' )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file with hiscores [hiscore.pcl]',
            type=str, default="hiscore.pcl" )
    argparser.add_argument ( '-i', '--interactive', help='start interactive session',
                             action="store_true" )
    argparser.add_argument ( '-c', '--contributions', help='analysis of contributions of analyses of first trimmed model',
                             action="store_true" )
    argparser.add_argument ( '-t', '--trim', help='trim the hiscore list to the nth entry',
                             type=int, default=0 )
    argparser.add_argument ( '-s', '--save', help='save the updated hiscore list under this filename [None]',
                             type=str,default=None )
    args = argparser.parse_args()
    h = Hiscore ( 0, False, args.picklefile )
    if args.trim>0:
        h.trimModels( args.trim, True )
    if args.contributions and len (h.trimmed)>0:
        from trimmer import Trimmer
        trimmer = Trimmer( h.trimmed[0] )
        h.trimmed[0] = trimmer.computeAnalysisContributions ( )
    if args.save not in  [ "", None ]:
        h.writeListToPickle( args.save )
    print ( "Check variable: h" )
    if args.interactive:
        # IPython.embed( using= False )
        from traitlets.config import get_config
        c = get_config()
        c.InteractiveShellEmbed.colors = "Linux"
        IPython.embed(config=c)

if __name__ == "__main__":
    main()
