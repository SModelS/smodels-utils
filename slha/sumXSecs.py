#!/usr/bin/env python3

""" sum up cross sections in a given file """

import argparse, tarfile, pyslha, sys, os

def sumUp( filename, sqrts ):
    p = pyslha.readSLHAFile ( filename )
    S = 0.
    for k,xsecs in p.xsections.items():
        for x in xsecs.xsecs:
            xsqrts = x.sqrts
            if abs ( xsqrts - sqrts*1000. ) > 1.:
                continue
            order = x.qcd_order_str
            if order != "NLO+LL":
                continue
            S += x.value
            print ( "xsec", sqrts, "order", order, "value", x.value )
    print ( "total is", S, "pb" )

def unpack ( tarball, slhafile ):
    """ get slhafile out of tarball """
    tar = tarfile.open( tarball,'r:gz')
    members=tar.getmembers()
    for m in members:
        if slhafile == m.name:
            print ( "[sumXSecs] extracting", m.name )
            tar.extract ( m )
            return slhafile
    return None

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="sum up all xsecs in an slhafile")

    argparser.add_argument ( '--tarball', help='name of tarball, None if file is already unpacked [None]',
        type=str, default=None )
    argparser.add_argument ( '--slhafile', help='name of slhafile [None]',
        type=str, default=None )
    argparser.add_argument ( '-s', '--sqrts', help='center-of-mass energy [13]',
        type=int, default=13 )
    argparser.add_argument( '-k', '--keep', action='store_true',
        help="keep temporary slha file" )
    args=argparser.parse_args()
    slhafile = args.slhafile
    doUnlink = False
    if not os.path.exists ( slhafile ):
        # if it didnt exist before, unlink at the end
        doUnlink = True
    if args.tarball != None:
        slhafile = unpack ( args.tarball, args.slhafile )
    if not os.path.exists ( slhafile ):
        print ( f"[sumXSecs] could not find {slhafile}" )
        sys.exit()
    sumUp ( slhafile, args.sqrts )
    if doUnlink and not args.keep:
        os.unlink ( slhafile )
