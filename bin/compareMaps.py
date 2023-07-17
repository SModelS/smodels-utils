#!/usr/bin/python

""" simple script that compares two efficiency / upper limits maps. WW """

from __future__ import print_function

from smodels.base.physicsUnits import GeV, pb

def extractMap ( filename ):
    f = open ( filename )
    lines = f.readlines()
    f.close()
    m = ""
    startingMarker = False
    for l in lines:
        if not startingMarker and not "upperLimits" in l \
                and not "efficiencyMap" in l:
            continue
        startingMarker = True
        m += l.replace ( "upperLimits: ", "" ).replace ( "efficiencyMap: ", "" )
    return eval(m )
    

m1 = extractMap ( "/home/walten/git/smodels-database/8TeV/ATLAS/ATLAS-SUSY-2013-15/data/T6bbWW.txt" )
m2 = extractMap ( "/home/walten/git/branches/smodels-database/8TeV/ATLAS/ATLAS-SUSY-2013-15/data/T6bbWW.txt" )

print ( "Length of m1", len ( m1 ) )
print ( "Length of m2", len ( m2 ) )

already_counted = []

duplicates1,duplicates2=0,0
for l in m2:
    if l[0] in already_counted:
        duplicates2 += 1
    else:
        already_counted.append ( l[0] )
    if not l[0] in [ x[0] for x in m1 ]:
        print ( "in m2, not in m1", l )

print ( "%d duplicates in m2" % duplicates2 )

for l in m1:
    if m1.count(l) > 1:
        duplicates1 += 1. / m1.count(l)
    if not l[0] in [ x[0] for x in m2 ]:
        print ( "in m1, not in m2", l )

print ( "%d duplicates in m1" % duplicates1 )

