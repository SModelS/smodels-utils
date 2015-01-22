#!/usr/bin/env python

"""
.. module:: drawRandomT
   :synopsis: Draw a random "topology of the day", as an ascii graph.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
    
import setPath

def drawRandom ( lhedir ):
    import sys, os, random, argparse
    from smodels.theory import lheReader, lheDecomposer
    from smodels.tools import asciiGraph
    """ just one random lhe file from <lhedir>, and draw it """
    files=os.listdir( lhedir )
    Files=[]
    for File in files:
      if File[-4:]==".lhe": Files.append(File)
    if len(Files)==0:
      print "[drawRandomT.py] error, did not find any files in",lhedir
      sys.exit(1)

    File=random.choice ( Files )

    filename=lhedir+"/"+File
    T=File.replace(".lhe","")
    while T.find("_")!=-1:
      T=T[:T.find("_")]

    print
    print "Today's Random Topology is ``%s'':" % T
    # print

    reader = lheReader.LheReader( filename )
    Event = reader.next()
    E = lheDecomposer.elementFromEvent(Event )
    print asciiGraph.asciidraw ( E, border=True )


if __name__ == '__main__':
    import argparse, types
    argparser = argparse.ArgumentParser(description='simple tool that is meant to draw lessagraphs, as a pdf feynman plot')
    argparser.add_argument ( '-d', '--dir', nargs='?', help='name of directory that contains the lhe files to draw from', type=types.StringType, default='@@installpath@@lhe/' )
    args=argparser.parse_args()
    Dir=args.dir
    import setPath
    from smodels_utils import SModelSUtils
    Dir=Dir.replace("@@installpath@@",SModelSUtils.installDirectory() )
    drawRandom ( Dir )
