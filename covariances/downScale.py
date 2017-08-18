#!/usr/bin/python3

""" downgrade an expResult in the database to the first n datasets. """

import sys, subprocess, os

def downGrade ( n ):
    if not os.path.exists ( ".backup" ):
        os.mkdir ( ".backup" )
    subprocess.getoutput ( "cp globalInfo.txt .backup/" )

    #subprocess.getoutput ( "cp globalInfo


if len(sys.argv)<2:
    print ( "Usage: %s <n>" % sys.argv[0] )
    print ( "  n: Number of datasets to keep" )
    sys.exit()

n = None
try:
    n = int ( sys.argv[1] )
except Exception as e:
    pass

if n>0:
    downGrade ( n )
