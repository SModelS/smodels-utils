#!/usr/bin/env python3

""" simple plot of best signal region, should be turned into 
a full blown script """

import matplotlib.pyplot as plt
import copy
import numpy
import importlib
import warnings
from matplotlib import colors as C
from smodels_utils.helper.various import getPathName

def convertNewAxes ( newa ):
    """ convert new types of axes (dictionary) to old (lists) """
    axes = copy.deepcopy(newa)
    if type(newa)==list:
        return axes[::-1]
    if type(newa)==dict:
        axes = [ newa["x"], newa["y"] ]
        if "z" in newa:
            axes.append ( newa["z"] )
        return axes[::-1]
    print ( "cannot convert this axis" )
    return None

def draw( validationfile ):
    warnings.simplefilter("ignore")
    anaId = "???"
    coll = "CMS"
    p = validationfile.find ( "ATLAS" )
    if p > 0:
        coll = "ATLAS"
    else:
        p = validationfile.find ( "CMS" )
    p2 = validationfile.find("-eff" )
    anaId = validationfile[p+1+len(coll):p2]
    p3 = validationfile.find("validation/")
    p4 = validationfile[p3+10:].find("_")
    topo = validationfile[p3+10+1:p3+p4+10]
    print ( "plotting %s (%s)" % ( anaId, topo ) )
    spec = importlib.util.spec_from_file_location( "output", validationfile )
    output_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(output_module)
    validationData = output_module.validationData
    bestSRs = []
    noResults = []
    nbsrs = []
    skipped, err = 0, None
    for point in validationData:
        if "error" in point:
            skipped += 1
            err = point["error"]
            axes = convertNewAxes ( point["axes"] )
            noResults.append ( ( axes[1], axes[0] ) )
            continue
        axes = convertNewAxes ( point["axes"] )
        bestSRs.append ( ( axes[1], axes[0], point["dataset"] ) )
        nbsrs.append ( ( axes[1], axes[0], 0 ) )
    if skipped > 0:
        print ( "skipped %d/%d points: %s" % ( skipped, len(validationData), err ) )
    bestSRs.sort()
    nbsrs = numpy.array ( nbsrs )
    srDict, nrDict = {}, {}
    srNum = 0
    for ctr,x in enumerate(bestSRs):
        if x[2] not in srDict.keys():
            srDict[x[2]]=srNum
            nrDict[srNum]=x[2]
            srNum+=1
        nbsrs[ctr][0] = x[0]
        nbsrs[ctr][1] = x[1]
        nbsrs[ctr][2] = srDict[x[2]]
    colors = [ "r", "g", "b", "c", "m", "y", "k" ]
    ctr = 0
    while len(nrDict.keys()) > len(colors):
        print ( "ERROR: not enough colors defined!!" )
        colors.append ( list(C.cnames.keys())[ctr] )
        ctr += 1
    noRx, noRy = [], []
    for i in noResults:
        noRx.append ( i[0] )
        noRy.append ( i[1] )
    for n in nrDict.keys():
        x,y=[],[]
        for x_,y_,z_ in nbsrs:
            # print ( "x,y,z,n",x_,y_,int(z_),n )
            if n == int(z_):
                x.append ( x_ )
                y.append ( y_ )
        plt.scatter ( x, y, s=25, c=[colors[n]]*len(x), label=nrDict[n] )
    plt.scatter ( noRx, noRy, s=2, c=["grey"]*len(noRx), label="no result" )
    plt.legend( loc="upper right" )
    plt.xlabel ( "m$_{mother}$ [GeV]" )
    plt.ylabel ( "m$_{daughter}$ [GeV]" )
    #plt.ylabel ( "$\\Delta$m [GeV]" )
    plt.title ( "Best Signal Region, %s (%s)" % ( anaId, topo ) )
    plt.savefig ( "bestSRs.png" )
    
if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser( description = "plot of best (expected) signal region per point" )
    argparser.add_argument ( "-d", "--dbpath", help="path to database [../../smodels-database/]", type=str,
                             default="../../smodels-database/" )
    argparser.add_argument ( "-a", "--analysis", 
            help="first analysis name, like the directory name [CMS-EXO-13-006-andre]", 
            type=str, default="CMS-EXO-13-006-andre" )
    argparser.add_argument ( "-v", "--validationfile", 
            help="first validation file [THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py]", 
            type=str, default="THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py" )
    argparser.add_argument ( "-c", "--copy", action="store_true", 
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/combination/" )
    args = argparser.parse_args()
    ipath = getPathName ( args.dbpath, args.analysis, args.validationfile )
    draw( ipath )
