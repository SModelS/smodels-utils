#!/usr/bin/env python3

""" python script to add the reference cross sections to slha files.
The cross sections have been scraped off from 
https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections
and stored in the xsec*.txt files. This version of the code 
goes thru the xsecComputer"""

import os, subprocess, sys
import pyslha
from types import SimpleNamespace
from smodels_utils.morexsecs.refxsecComputer import RefXSecComputer

def clean ( F ):
    """ clean up F, if needed. remove double newlines, and ssm line """
    f=open(F,"rt")
    lines=f.readlines()
    f.close()
    f=open(F,"wt")
    newline = False
    for line in lines:
        if "Signal strength multipliers" in line:
            continue
        if newline and line == "\n":
            continue
        if line == "\n":
            newline = True
        else:
            newline = False
        f.write ( line )
    f.close()

def zipThem ( files ):
    """ zip them up """
    topo = files[0][:files[0].find("_")]
    cmd = "tar czvf %s.tar.gz %s*slha" % ( topo, topo )
    print ( cmd )
    subprocess.getoutput ( cmd )
    cmd = "rm %s*slha" % topo
    print ( cmd )
    subprocess.getoutput ( cmd )

def main():
    import argparse, glob
    argparser = argparse.ArgumentParser( description = "add reference cross sections to slha files" )
    argparser.add_argument('-f', '--files', 
                           help = 'file pattern to glob, if tarball given, then unpack [T*.slha]',
                           type=str,default = "T*.slha" )
    argparser.add_argument('-s', '--sqrts', help="sqrts, in TeV. If 0, then both 8 and 13. [0]",
                           type=int, default = 0 )
    argparser.add_argument('-e', '--ewk', help="specify the ewkino process, hino or wino [wino]",
                           type=str, default = "wino" )
    argparser.add_argument('-d', '--dry_run', help="just pretend",
                            action = "store_true" )
    argparser.add_argument('-r', '--remove', help="remove cruft T*slha files before starting",
                            action = "store_true" )
    argparser.add_argument('-z', '--zip', help="zip the files after youre done",
                            action = "store_true" )
    argparser.add_argument('-v', '--verbose', help="increase verbosity",
                            action = "store_true" )
    args = argparser.parse_args()
    if args.ewk not in [ "hino", "wino" ]:
        print ( "[addRefXSecs] error ewk %s not recognised" % args.ewk )
        sys.exit()
    if args.files.endswith(".tar.gz"):
        files = glob.glob("T*slha")
        if args.remove:
            for f in files[:3]:
                print ( "[addRefXSecsSModelS] removing", f )
                os.unlink ( f )
            if len(files)>3:
                print ( f"[addRefXSecsSModelS] (removing {len(files)-3} more files ...) " )
        else:
            if len(files)>0:
                print ( "[addRefXSecs] error, you ask me to unpack a tarball but there are slha files in the directory. Use -r if you want them to be automatically removed." )
                sys.exit()
        ## remove cruft slha files, unpack tarball
        cmd = "rm -rf T*slha" 
        subprocess.getoutput ( cmd )
        cmd = "tar xzvf %s" % args.files
        subprocess.getoutput ( cmd )
        args.files = "T*slha"
    files = glob.glob ( args.files )
    sqrts = [ args.sqrts ]
    if sqrts == [ 0 ]:
        sqrts = [ 8, 13 ]
    computer = RefXSecComputer ( verbose=args.verbose )
    computer.computeForBunch ( sqrts, files, tofile=True )
    ## turn them back into a tarball
    if args.zip:
        zipThem ( files )

if __name__ == "__main__":
    main()
