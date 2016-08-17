#!/usr/bin/python

import ROOT
import sys

def createList ( hashlist ):
    ret=[]
    for i in hashlist:
        ret.append ( i.GetName() )
    ret.sort()
    return ret

def compareGraphs ( g1, g2 ):
    if g1.GetName() != g2.GetName():
        print "Names of graphs different %s != %s" % \
             ( g1.GetName(), g2.GetName() )
        sys.exit()
    n1,n2 = g1.GetN(), g2.GetN()
    if n1 != n2:
        print "Number of points not equal in %s" % g1.GetName()
        sys.exit()
    for i in range(n1):
        x1,y1 = ROOT.Double(), ROOT.Double()
        x2,y2 = ROOT.Double(), ROOT.Double()
        g1.GetPoint ( i, x1, y1 )
        g2.GetPoint ( i, x2, y2 )
        if x1 != x2 or y1 != y2:
            print "Point different %f,%f != %f,%f" % ( x1,x2,y1,y2 )
            sys.exit()
    print "  %s" % g1.GetName()

def compare ( name1, name2 ):
    f1, f2 = ROOT.TFile ( name1 ), ROOT.TFile ( name2 )

    keys1 = createList ( f1.GetListOfKeys() )
    keys2 = createList ( f2.GetListOfKeys() )

    if len(keys1) != len(keys2 ):
        print "Number of dirs not the same."
        print "%s: %s" % ( name1, ", ".join ( keys1 ) )
        print "%s: %s" % ( name2, ", ".join ( keys2 ) )
        sys.exit()

    for k1,k2 in zip ( keys1, keys2 ):
        if k1 != k2:
            print "Keys disagree: %s != %s" % ( k1, k2 )
            sys.exit()

    for k1,k2 in zip ( keys1, keys2 ):
        print "%s" % ( k1 )
        graphs1 = createList ( f1.Get(k1).GetListOfKeys() )
        graphs2 = createList ( f2.Get(k2).GetListOfKeys() )
        if len( graphs1) != len( graphs2 ):
#        if True:
            print "Number of graphs not the same."
            print "%s,%s: %s" % ( name1, k1, ", ".join ( graphs1 ) )
            print "%s,%s: %s" % ( name2, k2, ", ".join ( graphs2 ) )
            sys.exit()
        for g1,g2 in zip ( graphs1, graphs2 ):
            mg1 = f1.Get( "%s/%s" % ( k1, g1 ) )
            mg2 = f2.Get( "%s/%s" % ( k2, g2 ) )
            compareGraphs ( mg1, mg2 )
    print
    print "Files are equal."

compare ( sys.argv[1], sys.argv[2] )
