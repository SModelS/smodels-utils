#!/usr/bin/python3

""" downgrade an expResult in the database to the first n datasets. """

import sys, subprocess, os, glob

def restore ( ) :
    if not os.path.exists ( ".backup" ):
        print ( "trying to restore, but not .backup found" )
        return
    print ( "restoring from .backup." )
    subprocess.getoutput ( "rm -r sr*" )
    subprocess.getoutput ( "cp -r .backup/globalInfo.txt .backup/sr* ." )

def downGrade ( n ):
    if not os.path.exists ( ".backup" ):
        os.mkdir ( ".backup" )
    if not os.path.exists ( ".backup/globalInfo.txt" ):
        subprocess.getoutput ( "cp globalInfo.txt .backup/" )
    for i in glob.iglob ( "sr*" ):
        srN = int ( i[2:] )
        if srN >= n:
            if os.path.exists ( ".backup/%s" % i ):
                subprocess.getoutput ( "rm -r %s" % i )
            else:
                subprocess.getoutput ( "mv %s .backup/" % i )
    f=open("globalInfo.txt","r")
    lines=f.readlines()
    f.close()
    f=open("globalInfo.txt","w")
    for line in lines:
        if line == "":
            continue
        if "datasetOrder:" in line:
            newline=""
            ctr=0
            for char in line:
                if char==",":
                    ctr+=1
                if ctr==n:
                    break
                newline+=char
            f.write ( newline + "\n" )
        elif "covariance:" in line:
            newline="covariance: ["
            ar = eval ( line[12:] )
            for row in ar[:n]:
                newline += str(row[:n])+","
            newline = newline[:-1]+"]]"
            f.write ( newline+"\n" )
        else:
            f.write ( line )
    f.close()


    #subprocess.getoutput ( "cp globalInfo


if len(sys.argv)<2:
    print ( "Usage: %s <n>" % sys.argv[0] )
    print ( "  n: Number of datasets to keep. 0: restore from .backup." )
    sys.exit()

n = None
try:
    n = int ( sys.argv[1] )
except Exception as e:
    pass

if n>0:
    downGrade ( n )

else:
    restore ()
