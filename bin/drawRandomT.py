#!/usr/bin/env python

def drawRandom ( lhedir ):
    import set_path
    import sys, os, random, argparse
    from theory import LHEReader, lheDecomposer
    from tools import asciiGraph
    """ just one random lhe file from <lhedir>, and draw it """
    Files=os.listdir( lhedir )

    File=""
    while File[-4:]!=".lhe":
      File=random.choice ( Files )

    filename=lhedir+"/"+File
    T=File.replace(".lhe","")
    while T.find("_")!=-1:
      T=T[:T.find("_")]

    print 
    print "Today's Random Topology is ``%s'':" % T
    print

    reader = LHEReader.LHEReader( filename )
    Event = reader.next()
    E = lheDecomposer.elementFromEvent(Event )
    asciiGraph.asciidraw ( E, border=True )


if __name__ == '__main__': 
    import argparse, types
    argparser = argparse.ArgumentParser(description='simple tool that is meant to draw lessagraphs, as a pdf feynman plot')                                     
    argparser.add_argument ( '-d', '--dir', nargs='?', help='name of directory that contains the lhe files to draw from', type=types.StringType, default='/usr/local/smodels/lhe/' )
    args=argparser.parse_args()
    drawRandom ( args.dir )
