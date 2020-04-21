#!/usr/bin/env python3

import numpy as np

def checkRegions ( g ):
    """ check if all have same # regions """
    nMax=0
    for k,v in g.items():
        nR =len(v)
        if nR > nMax:
            nMax = nR
    ctWrong = 0
    for k,v in g.items():
        nR =len(v)
        if nR < nMax:
            print ( "point %s has only %d/%d regions" % ( k, nR, nMax ) )
            ctWrong += 1
    print ( "%d / %d points dont have all %d regions." % ( ctWrong, len(g), nMax ) )


def main():
    import argparse
    argparser = argparse.ArgumentParser(description="Check an embaked files")
    argparser.add_argument ( '-t', '--topology', nargs='?', help='topology to check [T1]',
                             type=str, default='T1' )
    argparser.add_argument ( '-a', '--analysis', nargs='?', help='analysis to check [ATLAS-SUSY-2016-07]',
                             type=str, default='ATLAS-SUSY-2016-07' )
    args=argparser.parse_args()
    ana = "%s-eff" % args.analysis
    exp = "ATLAS"
    if "CMS" in ana:
        exp = "CMS"
    sqrts="13"
    topo=args.topology
    fname = "../../smodels-database/%sTeV/%s/%s/orig/%s.embaked" % ( sqrts, exp, ana, topo)
    with open(fname) as f:
        g=eval(f.read())
    stats ( g )

def stats ( g ):
    print ( "we have %d points" % len(g) )
    checkRegions ( g )
    tuples = list(g.keys())
    ntuples = np.array ( tuples )
    ndim = len(tuples[0]) 
    print ( "we have %d dimensions" % ndim )
    for i in range( ndim ):
        print ( " `- dim #%d: (%d,%d)" % ( i, min(ntuples[::,i]),max(ntuples[::,i])) )
    mults =  []
    multst= {}
    multslastdim = []
    multslastdimt = {}
    multsonedim = []
    multsonedimt = {}
    for t in tuples:
        tmp=1.
        tmplastdim = 1.
        tmponedim = 1.
        for i in range(ndim):
            tmp = tmp * t[i]
        for i in range(ndim-1):
            tmplastdim = tmplastdim * t[i]
        for i in range(ndim):
            if i != 1:
                tmponedim = tmponedim * t[i]
        mults.append ( tmp )
        multst [ tmp ] = t
        tmplastdim = tmplastdim * ( max(ntuples[::,-1] - t[ndim-1]) )
        tmponedim = tmponedim * ( max(ntuples[::,1] - t[1]) )
        multslastdim.append ( tmplastdim )
        multslastdimt [ tmplastdim ] = t
        multsonedim.append ( tmponedim )
        multsonedimt [ tmponedim ] = t

    print ( "largest at meridian %s - %s" % ( multst[min(mults)], multst[max(mults)] ) )
    print ( "largest with small LSP %s - %s" % ( multslastdimt[min(multslastdim)], multslastdimt[max(multslastdim)] ) )
    print ( "largest with small intermediate %s - %s" % ( multsonedimt[min(multsonedim)], multsonedimt[max(multsonedim)] ) )
    # print ( g.keys() )

if __name__ == "__main__":
    main()
