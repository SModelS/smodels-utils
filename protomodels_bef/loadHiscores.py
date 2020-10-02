#!/usr/bin/env python3

""" Allows for loading protomodels and running in interactive mode.
"""
from tools.hiscoreTools import main



if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore class as a commandline tool it allows for '
                        'merging, printing, and checking of hiscore list' )
    argparser.add_argument ( '-i', '--infile',
            help='Specify the input pickle file to start with. If none, start with H<n>.hi. [None]',
            type=str, default=None )
    argparser.add_argument ( '-o', '--outfile',
            help='pickle file with hiscores. If none, dont pickle. [none]',
            type=str, default="none" )
    argparser.add_argument ( '-n', '--nmax',
            help='maximum number of entries to store [10]',
            type=int, default=10 )
    argparser.add_argument ( '-c', '--check',
            help='check if we can reproduce Z value of first entry',
            action="store_true" )
    argparser.add_argument ( '-f', '--fetch',
            help='fetch H<n>.hi from clip server',
            action="store_true" )
    argparser.add_argument ( '-p', '--print',
            help='print list to stdout', action="store_true" )
    argparser.add_argument ( '-d', '--detailed',
            help='detailed descriptions (requires -p)', action="store_true" )
    argparser.add_argument ( '-I', '--interactive', help='start interactive session',
                             action="store_true" )
    args = argparser.parse_args()
    main ( args )
