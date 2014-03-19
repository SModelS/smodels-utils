#!/usr/bin/python

import set_path, argparse, types

argparser = argparse.ArgumentParser(description='simple tool that is meant to draw lessagraphs, as a pdf feynman plot')
argparser.add_argument ( '-T', nargs='?', help='Tx name, will look up lhe file in ../regression/Tx_1.lhe. Will be overriden by the "--lhe" argument', type=types.StringType, default='T1' )
argparser.add_argument ( '-l', '--lhe', nargs='?', help='lhe file name, supplied directly. Takes precedence over "-T" argument.', type=types.StringType, default='' )
argparser.add_argument ( '-o', '--output', nargs='?', help='output file, can be pdf or eps or png (via convert)', type=types.StringType, default='out.pdf' )
argparser.add_argument ( '-s', '--straight', help='straight, not xkcd style', action='store_true' )
argparser.add_argument ( '-v', '--verbose', help='be verbose', action='store_true' )
args=argparser.parse_args()

import commands, sys
## get the smodels environment
sys.path.append(".")
smodelsdir="/usr"
smodelsconfig="smodels-config"
o=commands.getoutput("%s --installdir" % smodelsconfig )
if o.find("not found")>-1:
  print "[feynDraw.py] %s not found." % smodelsconfig
else:
  smodelsdir=o
  sys.path.append(smodelsdir)

from theory import LHEReader, lheDecomposer, crossSection
from moretools import feynmanGraphs

filename="%s/lhe/%s_1.lhe" % (smodelsdir, args.T )
if args.lhe!="": filename=args.lhe

reader = LHEReader.LHEReader( filename )
Event = reader.next()
E = lheDecomposer.elementFromEvent( Event, crossSection.XSectionList() )

feynmanGraphs.draw ( E, args.output, straight=args.straight, inparts=False, verbose=args.verbose )
