#!/usr/bin/env python3

""" simple plot of best signal region, should be turned into
a full blown script """

from smodels_utils.plotting import mpkitty as plt
#import matplotlib.pyplot as plt
import copy, os
import numpy
import importlib
import warnings
import subprocess
import time
from matplotlib import colors as C
from smodels_utils.helper.various import getPathName
from smodels_utils.helper import uprootTools
from validation.validationHelpers import getValidationFileContent, shortTxName, \
       mergeExclusionLines, mergeValidationData
        
warnings.simplefilter("ignore")

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
    print ( f"[plotBestSRs] cannot convert axis {newa}" )
    return None

def draw( dbpath, analysis, validationfiles, max_x, max_y, outputfile, defcolors ):
    """ plot.
    :param dbpath: path to database
    :param analysis: analysis to consider
    :param validationfiles: T*.py files
    :param outputfile: name of outputfile, using @a and @t to stand for
     analysis and topology, respectively
    :param defcolors: user-specified colors
    """
    vfiles = validationfiles.split(",")
    lines = []
    contents = []
    txnames = []
    for validationfile in vfiles:
        ipath = getPathName ( dbpath, analysis, validationfile )
        smspath = getPathName ( dbpath, analysis, None )
        p1 = validationfile.find("_")
        topo = validationfile[:p1]
        txnames.append ( topo )
        content = getValidationFileContent ( ipath )
        contents.append ( content )
        ll = uprootTools.getExclusionLine ( smspath, topo, content["meta"]["axes"] )
        lines.append (  ll )
    content = mergeValidationData ( contents )
    data = content["data"]
    line = mergeExclusionLines ( lines )
    bestSRs = []
    noResults = []
    nbsrs = []
    skipped, err = 0, None
    for point in data:
        if "error" in point:
            skipped += 1
            err = point["error"]
            if "axes" in point and point["axes"] != None:
                axes = convertNewAxes ( point["axes"] )
                if max_x != None and axes[1]>max_x:
                    continue
                if max_y != None and axes[0]>max_y:
                    continue
                if axes == None:
                    continue
                noResults.append ( ( axes[1], axes[0] ) )
            continue
        axes = convertNewAxes ( point["axes"] )
        if max_x != None and axes[1]>max_x:
            continue
        if max_y != None and axes[0]>max_y:
            continue
        bestSRs.append ( ( axes[1], axes[0], point["dataset"] ) )
        nbsrs.append ( ( axes[1], axes[0], 0 ) )
    if skipped > 0:
        print ( "[plotBestSRs] skipped %d/%d points: %s" % \
                ( skipped, len(data), err ) )
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
    origcolors = [ "r", "g", "b", "c", "m", "y", "k" ] # "#ffa500", '#115f6a', "#A52A2A", "k" ]
    #origcolors += [ "navy", "teal", "maroon", "coral", "lime", "aqua", "indigo", "wheat" ]
    #origcolors += [ "slate" ]
    for i in range(30):
        origcolors.append ( "k" )
    if defcolors not in [ "", None ]:
        for i,c in enumerate(defcolors.split(",")[:28]):
            origcolors[i]=c
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
        col = colors[n]
        label = nrDict[n]
        if col == "k":
            label = "others"
        plt.scatter ( x, y, s=25, c=[ col ]*len(x), label=label )
    plt.scatter ( noRx, noRy, s=2, c=["grey"]*len(noRx), label="no result" )
    handles, labels = plt.gca().get_legend_handles_labels()
    i =1
    while i<len(labels):
        if labels[i] in labels[:i]:
            del(labels[i])
            del(handles[i])
        else:
            i +=1
    plt.legend(handles, labels, loc="upper left" )
    if line != None:
        plt.plot ( line["x"], line["y"], linewidth=4, color="white" )
        plt.plot ( line["x"], line["y"], linewidth=2, color="black" )
    plt.xlabel ( "m$_{mother}$ [GeV]" )
    plt.ylabel ( "m$_{daughter}$ [GeV]" )
    if min(y)>1e-30 and max(y)<1e-1:
        # the y axis seems to be widths
        ax.set_yscale('log')
        ax.set_ylim ( min(y)*.2, max(y)*5. )
        plt.ylabel ( "$\Gamma$ [GeV]" )
        plt.xlabel ( "m [GeV]" )
    shorttopo = shortTxName ( txnames )
    plt.title ( "Best Signal Region, %s (%s)" % ( analysis, shorttopo ) )
    print ( "[plotBestSRs] plotting %s (%s)" % ( analysis, shorttopo ) )
    fname = outputfile.replace( "@a", analysis ).replace( "@t", shorttopo )
    print ( "[plotBestSRs] saving to %s" % fname )
    plt.savefig ( fname )
    plt.kittyPlot()
    plt.clf()
    return fname

def writeBestSRs( push = False ):
    import glob
    Dir = "../../smodels.github.io/plots/"
    files = glob.glob("%sbestSR*png" % Dir )
    files.sort()
    topos = set()
    for f in files:
        p = f.rfind ( "_" )
        topos.add ( f[p+1:-4] )
    # print ( topos )
    with open ( "%sbestSRs.md" % Dir, "wt" ) as g:
        g.write ( "# plots of best expected signal regions\n" )
        g.write ( "as of %s\n" % time.asctime() )
        g.write ( "checkout also the [ratio plots](README.md)\n" )
        tsorted = list(topos)
        tsorted.sort() ## why???
        for topo in tsorted:
            g.write ( "\n## Topology: %s\n\n" % topo )
            g.write ( "| andre | suchi |\n" )
            for f in files:
                src = f.replace( Dir, "" )
                if not topo in src:
                    continue
                g.write ( '| <img src="%s" /> ' % ( src ) )
            g.write ( "|\n" )
    cmd = "cd ../../smodels.github.io/; git commit -am 'automated commit' ; git push"
    o = ""
    if push:
        o = subprocess.getoutput ( cmd )
    print ( "[plotBestSRs] cmd %s: %s" % (cmd, o ) )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description = "plot of best (expected) signal region per point" )
    argparser.add_argument ( "-d", "--dbpath",
            help="path to database [../../smodels-database/]",
            type=str, default="../../smodels-database/" )
    argparser.add_argument ( "-x", "--max_x",
            help="upper bound on x axis [None]",
            type=float, default=None )
    argparser.add_argument ( "-y", "--max_y",
            help="upper bound on y axis [None]",
            type=float, default=None )
    argparser.add_argument ( "-a", "--analysis",
            help="analysis name, like the directory name [CMS-SUS-16-050-eff]",
            type=str, default="CMS-SUS-16-050-eff" )
    argparser.add_argument ( "-C", "--colors",
            help="specify colors, as string with commas ['r,g,b']",
            type=str, default="r,b,g" )
    argparser.add_argument ( "-v", "--validationfiles",
            help="validation file(s), comma separated within string [T2tt_2EqMassAx_EqMassBy.py]",
            type=str, default="T2tt_2EqMassAx_EqMassBy.py" )
    argparser.add_argument ( "-o", "--outputfile",
            help="output file, replacing @a and @t with analysis and topo name [bestSR_@a_@t.png]",
            type=str, default="./bestSR_@a_@t.png" )
    argparser.add_argument ( "-D", "--default", action="store_true",
            help="default run on arguments. currently set to be the exo 13 006 plots" )
    argparser.add_argument ( "-c", "--copy", action="store_true",
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    argparser.add_argument ( "-p", "--push", action="store_true",
            help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    args = argparser.parse_args()
    if not args.default and not args.analysis.endswith("-eff"):
        print ( "[plotBestSRs] warning, analysis name does not end with -eff, might an error" )
    if args.default:
        for a in [ "CMS-EXO-13-006-andre", "CMS-EXO-13-006-eff" ]:
            for v in [ "THSCPM1b_2EqMassAx_EqWidthAy.py", "THSCPM3_2EqMassAx_EqMassBy**.py", "THSCPM4_*.py", "THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py", "THSCPM6_EqMassA__EqmassAx_EqmassBx-100_Eqma*.py", "THSCPM8_2EqMassAx*.py", "THSCPM2b_*.py" ]:
                print ( "[plotBestSRs:default] now drawing %s:%s" % (a, v ) )
                ipath = getPathName ( args.dbpath, a, v )
                fname = draw( ipath, args.max_x, args.max_y, args.outputfile )
                if args.copy:
                    cmd = "cp %s ../../smodels.github.io/plots/" % fname
                    o = subprocess.getoutput ( cmd )
                    print ( "[plotBestSRs] cmd %s: %s" % (cmd, o ) )
    else:
        fname = draw( args.dbpath, args.analysis, args.validationfiles, 
                      args.max_x, args.max_y, args.outputfile, args.colors )
        if args.copy:
            cmd = "cp %s ../../smodels.github.io/plots/" % fname
            o = subprocess.getoutput ( cmd )
            print ( "[plotBestSRs] cmd %s: %s" % (cmd, o ) )
    if args.copy:
        writeBestSRs( args.push )
