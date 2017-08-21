#!/usr/bin/python3

""" downgrade an expResult in the database to the first n datasets. """

import sys, subprocess, os, glob

def restore ( ) :
    if not os.path.exists ( ".backup" ):
        print ( "trying to restore, but not .backup found" )
        return
    print ( "restoring from .backup." )
    # subprocess.getoutput ( "rm -r sr*" )
    subprocess.getoutput ( "cp -r .backup/globalInfo.txt .backup/sr* ." )

def downGrade ( n, noCov, skip="" ):
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
            if noCov:
                for i in range(len(ar)):
                    for j in range(len(ar)):
                        if i!=j:
                            ar[i][j]=0.
            for row in ar[:n]:
                newline += str(row[:n])+","
            newline = newline[:-1]+"]"
            f.write ( newline+"\n" )
        else:
            f.write ( line )
    f.close()

def main():
    import argparse
    argparser = argparse.ArgumentParser(description = "prepares expResults with subsets of datasets" )
    argparser.add_argument ( "-C", "--no_cov", help="discard all covariances, keep only variances", action="store_true" )
    argparser.add_argument ( "-r", "--restore", help="restore all datasets and globalInfo from .backup", action="store_true" )
    argparser.add_argument ( "-n", "--keep", help="keep first <n> datasets", type=int, default=0 )
    argparser.add_argument ( "-s", "--skip", help="skip entries (comma separated list)", type=str, default="" )
    args = argparser.parse_args()
    n=args.keep
    skip=[]
    if len(args.skip)>0:
       skip=list ( map ( int, args.skip.split(",") ) )

    if args.restore:
        restore()
    if n>0:
        downGrade ( n, noCov=args.no_cov, skip=skip )
    
if __name__ == "__main__":
    main()
