#!/usr/bin/python3

""" downgrade an expResult in the database to the first n datasets. """

import sys, subprocess, os, glob, numpy

def restore ( ) :
    if not os.path.exists ( ".backup" ):
        print ( "trying to restore, but not .backup found" )
        return
    print ( "restoring from .backup ...", end="" )
    # subprocess.getoutput ( "rm -r sr*" )
    subprocess.getoutput ( "cp -r .backup/globalInfo.txt .backup/sr* ." )
    print ( " done." )

def downGrade ( n, noCov, skip=[] ):
    sskip="none"
    if len(skip):
        sskip=",".join(map(str,skip))
    print ( "Downgrading to %d, skipping %s." % ( n, sskip ) )
    if not os.path.exists ( ".backup" ):
        os.mkdir ( ".backup" )
    if not os.path.exists ( ".backup/globalInfo.txt" ):
        subprocess.getoutput ( "cp globalInfo.txt .backup/" )
    for i in glob.iglob ( "sr*" ):
        srN = int ( i[2:] )
        if srN >= n or srN in skip:
            if os.path.exists ( f".backup/{i}" ):
                subprocess.getoutput ( f"rm -r {i}" )
            else:
                subprocess.getoutput ( f"mv {i} .backup/" )
    f=open("globalInfo.txt","r")
    lines=f.readlines()
    f.close()
    f=open("globalInfo.txt","w")
    for line in lines:
        if line == "":
            continue
        if "datasetOrder:" in line:
            newline="datasetOrder: "
            ctr=0
            needsComma=False
            for char in line[14:]:
                if char==",":
                    ctr+=1
                    if not needsComma:
                        char=""
                if ctr==n:
                    break
                if ctr not in skip:
                    newline+=char
                    needsComma=True
            f.write ( newline + "\n" )
        elif "covariance:" in line:
            newline="covariance: ["
            ar = eval ( line[12:] )
            if noCov:
                for i in range(len(ar)):
                    for j in range(len(ar)):
                        if i!=j:
                            ar[i][j]=0.
            rows = ar[:n]
            if len(skip)>0:
                r = numpy.array ( rows )
                bitarray = [ True ]*len(r)
                for ctr,i in enumerate(bitarray):
                    if ctr in skip:
                        bitarray[ctr]=False
                r=r[ bitarray ]
                rows = r.tolist()
            for row in rows:
                columns = row[:n]
                if len(skip)>0:
                    r = numpy.array ( columns )
                    bitarray = [ True ]*len(r)
                    for ctr,i in enumerate(bitarray):
                        if ctr in skip:
                            bitarray[ctr]=False
                    r=r[ bitarray ]
                    columns = r.tolist()
                newline += str(columns)+","
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
