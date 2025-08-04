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
            print ( f"point {k} has only {int(nR)}/{int(nMax)} regions" )
            ctWrong += 1
    print ( f"{int(ctWrong)} / {len(g)} points dont have all {int(nMax)} regions." )


def main():
    import argparse
    argparser = argparse.ArgumentParser(description="Check an embaked files")
    argparser.add_argument ( '-t', '--topology', nargs='?', help='topology to check [T1]',
                             type=str, default='T1' )
    argparser.add_argument ( '-a', '--analysis', nargs='?', help='analysis to check [ATLAS-SUSY-2016-07]',
                             type=str, default='ATLAS-SUSY-2016-07' )
    args=argparser.parse_args()
    ana = f"{args.analysis}-eff"
    exp = "ATLAS"
    if "CMS" in ana:
        exp = "CMS"
    sqrts="13"
    topo=args.topology
    fname = f"../../smodels-database/{sqrts}TeV/{exp}/{ana}/orig/{topo}.embaked"
    with open(fname) as f:
        g=eval(f.read())
    stats ( g )

def stats ( g ):
    print ( f"we have {len(g)} points" )
    checkRegions ( g )
    tuples = list(g.keys())
    ntuples = np.array ( tuples )
    ndim = len(tuples[0]) 
    print ( f"we have {int(ndim)} dimensions" )
    for i in range( ndim ):
        print ( f" `- dim #{int(i)}: ({int(min(ntuples[:, i]))},{int(max(ntuples[:, i]))})" )
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

    print ( f"largest at meridian {multst[min(mults)]} - {multst[max(mults)]}" )
    print ( f"largest with small LSP {multslastdimt[min(multslastdim)]} - {multslastdimt[max(multslastdim)]}" )
    print ( f"largest with small intermediate {multsonedimt[min(multsonedim)]} - {multsonedimt[max(multsonedim)]}" )
    # print ( g.keys() )

if __name__ == "__main__":
    main()
