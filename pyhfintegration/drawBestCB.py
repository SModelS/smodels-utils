#!/usr/bin/env python3

""" simple plot of best expected combination, should be turned into
a full blown script """

import matplotlib.pyplot as plt
import copy
import numpy
import importlib
import warnings
import subprocess
import time
from matplotlib import colors as C
import sys
sys.path.insert(0,"../")
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
    p2b = validationfile.find("-andre" )
    if p2 < 1:
        p2 = p2b
    anaId = validationfile[p+1+len(coll):p2]
    p3 = validationfile.find("validation/")
    p4 = validationfile[p3+10:].find("_")
    topo = validationfile[p3+10+1:p3+p4+10]
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
            if "axes" in point:
                if point['axes'] is None:
                    continue
                axes = convertNewAxes ( point["axes"] )
                noResults.append ( ( axes[1], axes[0] ) )
            continue
        axes = convertNewAxes ( point["axes"] )
        bestSRs.append ( ( axes[1], axes[0], point["best combination"] ) )
        nbsrs.append ( ( axes[1], axes[0], 0 ) )
    if skipped > 0:
        print ( f"[drawBestSRs] skipped {int(skipped)}/{len(validationData)} points: {err}" )
    bestSRs.sort()
    nbsrs = numpy.array ( nbsrs )
    srDict, nrDict = {}, {}
    srNum = 0
    predefined = {}
    predefined = { "c000": 3, "c100": 2, "c200": 0, "c300": 1 }
    for k,v in predefined.items():
        srDict[k]=v
        nrDict[v]=k
    for ctr,x in enumerate(bestSRs):
        if x[2] not in srDict.keys():
            while srNum in nrDict:
                srNum+=1
            srDict[x[2]]=srNum
            nrDict[srNum]=x[2]
            srNum+=1
        nbsrs[ctr][0] = x[0]
        nbsrs[ctr][1] = x[1]
        nbsrs[ctr][2] = srDict[x[2]]
    colorCounts,cCounts={},{}
    for i in range(int(1+max(nbsrs[::,2]) ) ):
        colorCounts[i]=list(map(int,nbsrs[::,2])).count(i)
    for k,v in colorCounts.items():
        if not v in cCounts:
            cCounts[v]=[]
        cCounts[v].append(k)
    occs = list ( cCounts.keys() )
    occs.sort( reverse=True )
    ctr = 0
    origcolors = [ "r", "g", "b", "c", "m", "y", "#ffa500", '#115f6a', "#A52A2A", "k" ]
    colors = copy.deepcopy ( origcolors )
    for occ in occs:
        if occ == 0:
            break
        for nr in cCounts[occ]:
            colors[nr]=origcolors[ctr]
            ctr+=1
    ctr = 0
    while len(nrDict.keys()) > len(colors):
        print ( "ERROR: not enough colors defined (%d needed, %d defined)!!" % \
                ( len(nrDict.keys()), len(colors) ) )
        colors.append ( list(C.cnames.keys())[ctr] )
        ctr += 1
    noRx, noRy = [], []
    for i in noResults:
        noRx.append ( i[0] )
        noRy.append ( i[1] )
    ax = plt.gca()
    for n in nrDict.keys():
        x,y=[],[]
        for x_,y_,z_ in nbsrs:
            if n == int(z_):
                x.append ( x_ )
                y.append ( y_ )
        if len(x)==0:
            continue
        plt.scatter ( x, y, s=25, c=[colors[n]]*len(x), label=nrDict[n] )
    plt.scatter ( noRx, noRy, s=2, c=["grey"]*len(noRx), label="no result" )
    plt.legend( loc="upper right" )
    plt.xlabel ( "m$_{mother}$ [GeV]" )
    plt.ylabel ( "m$_{daughter}$ [GeV]" )
    if min(y)>1e-30 and max(y)<1e-1:
        # the y axis seems to be widths
        ax.set_yscale('log')
        ax.set_ylim ( min(y)*.2, max(y)*5. )
        plt.ylabel ( "$\Gamma$ [GeV]" )
        plt.xlabel ( "m [GeV]" )
    #plt.ylabel ( "$\\Delta$m [GeV]" )
    print ( f"[drawBestSRs] plotting {anaId} ({topo})" )
    andre=""
    if "andre" in validationfile:
        andre="-andre"
    plt.title ( f"Best Combination, {anaId + andre} ({topo})" )
    fname = f"bestSR_{anaId}{andre}_{topo}.png"
    print ( "[drawBestSRs} saving to %s" % fname )
    plt.savefig ( fname )
    plt.clf()
    return fname

def writeBestSRs( push = False ):
    import glob
    Dir = "../../smodels.github.io/ratioplots/"
    files = glob.glob(f"{Dir}bestSR*png" )
    files.sort()
    topos = set()
    for f in files:
        p = f.rfind ( "_" )
        topos.add ( f[p+1:-4] )
    # print ( topos )
    with open ( f"{Dir}bestSRs.md", "wt" ) as g:
        g.write ( "# plots of best expected signal regions\n" )
        g.write ( f"as of {time.asctime()}\n" )
        g.write ( "checkout also the [ratio plots](README.md)\n" )
        tsorted = list(topos)
        tsorted.sort() ## why???
        for topo in tsorted:
            g.write ( f"\n## Topology: {topo}\n\n" )
            g.write ( "| andre | suchi |\n" )
            for f in files:
                src = f.replace( Dir, "" )
                if not topo in src:
                    continue
                g.write ( f'| <img src="{src}" /> ' )
            g.write ( "|\n" )
    cmd = "cd ../../smodels.github.io/; git commit -am 'automated commit' ; git push"
    o = ""
    if push:
        o = subprocess.getoutput ( cmd )
    print ( f"[drawBestSRs] cmd {cmd}: {o}" )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser( description = "plot of best (expected) signal region per point" )
    argparser.add_argument ( "-d", "--dbpath", help="path to database [../../smodels-database/]", type=str,
                             default="../../smodels-database/" )
    argparser.add_argument ( "-a", "--analysis",
            help="analysis name, like the directory name [CMS-EXO-13-006-eff]",
            type=str, default="CMS-EXO-13-006-eff" )
    argparser.add_argument ( "-v", "--validationfile",
            help="validation file [THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py]",
            type=str, default="THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py" )
    argparser.add_argument ( "-D", "--default", action="store_true",
            help="default run on arguments. currently set to be the exo 13 006 plots" )
    argparser.add_argument ( "-c", "--copy", action="store_true",
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/ratioplots/" )
    argparser.add_argument ( "-p", "--push", action="store_true",
            help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/ratioplots/" )
    args = argparser.parse_args()
    if not args.default and not args.analysis.endswith("-eff"):
        print ( "[drawBestSRs] warning, analysis name does not end with -eff, might an error" )
    if args.default:
        for a in [ "CMS-EXO-13-006-andre", "CMS-EXO-13-006-eff" ]:
            for v in [ "THSCPM1b_2EqMassAx_EqWidthAy.py", "THSCPM3_2EqMassAx_EqMassBy**.py", "THSCPM4_*.py", "THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py", "THSCPM6_EqMassA__EqmassAx_EqmassBx-100_Eqma*.py", "THSCPM8_2EqMassAx*.py", "THSCPM2b_*.py" ]:
                print ( f"[drawBestSRs:default] now drawing {a}:{v}" )
                ipath = getPathName ( args.dbpath, a, v )
                fname = draw( ipath )
                if args.copy:
                    cmd = f"cp {fname} ../../smodels.github.io/ratioplots/"
                    o = subprocess.getoutput ( cmd )
                    print ( f"[drawBestSRs] cmd {cmd}: {o}" )
    else:
        ipath = getPathName ( args.dbpath, args.analysis, args.validationfile )
        fname = draw( ipath )
        if args.copy:
            cmd = f"cp {fname} ../../smodels.github.io/ratioplots/"
            o = subprocess.getoutput ( cmd )
            print ( f"[drawBestSRs] cmd {cmd}: {o}" )
    if args.copy:
        writeBestSRs( args.push )
