#!/usr/bin/env python3

"""
.. module:: cleanTarball
   :synopsis: Very simple script to take out all slha files from a tarball that have no xsecs

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import os
from slhaHelpers import hasXSecs

def clean ( tarball : os.PathLike ):
    import tarfile
    tar = tarfile.open( tarball,'r:gz')
    members=tar.getmembers()
    newtarball = []
    for m in members:
        tar.extract ( m )
        if m.name.endswith ( ".slha" ):
            if not hasXSecs ( m.name ):
                print ( f"removing {m.name}" )
                os.unlink ( m.name )
            else:
                newtarball.append ( m.name )
        else:
            newtarball.append ( m.name )
    os.rename ( tarball, tarball+".backup" )
    with tarfile.open( tarball, mode="w:gz") as tar:
         for file in newtarball:
            tar.add ( file, arcname=file )
    

def main ():
    import argparse
    argparser = argparse.ArgumentParser(description="Very simple script to take out all slha files from a tarball that have no xsecs")
    argparser.add_argument ( '-t', '--tarball', nargs='?', help='tarball to clean [TChiWZoff.tar.gz]',
        type=str, default='TChiWZoff.tar.gz' )
    args=argparser.parse_args()
    clean ( args.tarball )

if __name__ == "__main__":
    main ()
