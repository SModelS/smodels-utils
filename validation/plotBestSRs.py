#!/usr/bin/env python3

""" simple plot of best signal region, should be turned into
a full blown script """

from smodels_utils.plotting import mpkitty as plt
#import matplotlib.pyplot as plt
import copy, os, sys
import numpy
import importlib
import warnings
import subprocess
import time
from matplotlib import colors as C
from smodels_utils.helper.various import getPathName, getExclusionCurvesFor
from smodels_utils.helper import prettyDescriptions
from validation.validationHelpers import getValidationFileContent, shortTxName, \
       mergeExclusionLines, mergeValidationData, widthOfStableParticles, \
       prettyAxes
from typing import Union
from plottingFuncs import getAxisRange, filterWithinRanges
from smodels_utils.helper.terminalcolors import *

__all__ = [ "plot" ]
        
warnings.simplefilter("ignore")

def convertNewAxes ( newa ):
    """ convert new types of axes (dictionary) to old (lists) """
    if len(newa)==0:
        return None
    axes = copy.deepcopy(newa)
    if type(newa)==list:
        return axes[::-1]
    if type(newa)==dict and "x" in newa:
        axes = [ newa["x"] ]
        if "y" in newa:
            axes.append( newa["y"] )
        if "z" in newa:
            axes.append ( newa["z"] )
        return axes[::-1] ## invert
    print ( f"[plotBestSRs] cannot convert axis {newa}" )
    return None

def fetchContent ( validationfiles : str, dbpath : str, analysis : str ) -> dict: 
    """ fetch and merge the contents of validation files
    """
    vfiles = validationfiles.split(",")
    lines = []
    contents = []
    txnames = []
    axisv = None
    options = {}
    for validationfile in vfiles:
        if not "_" in validationfile:
            validationfile = validationfile+"_2EqMassAx_EqMassBy.py"
        if "_combined" in validationfile:
            print ( f"[plotBestSRs] weird validationfile is {validationfile}, ie with 'combined' in the file name. You sure it is the right one?" )
        ipath = getPathName ( dbpath, analysis, validationfile )
        print ( f"[plotBestSRs] querying {ipath}" )
        smspath = getPathName ( dbpath, analysis, None )
        if smspath == None:
            print ( f"[plotBestSRs] got no sms path: returning" )
            return
        p1 = validationfile.find("_")
        topo = validationfile[:p1]
        txnames.append ( topo )
        content = getValidationFileContent ( ipath )
        contents.append ( content )
        eljson = os.path.join ( smspath, "exclusion_lines.json" )
        if "meta" in content and type(content["meta"]) == dict:
            if "axes" in content["meta"]:
                axisv = content["meta"]["axes"]
                if os.path.exists ( eljson ):
                    ll = getExclusionCurvesFor ( eljson, topo, content["meta"]["axes"] )
                    if ll is not None:
                        if topo in ll:
                            lines.append (  ll[topo] )
                        else:
                            print ( f"[plotBestSRs] {topo} is not in lines? {ll}" )
            if "style" in content["meta"]:
                options["style"]=content["meta"]["style"]

    content = mergeValidationData ( contents )
    data = content["data"]
    line = mergeExclusionLines ( lines )
    return { "data": data, "line": line, "txnames": txnames, "axis": axisv,
             "options": options }

def isWithinValue ( value, maxvalue ):
    if maxvalue == None:
        return True
    if value <= maxvalue:
        return True
    return False

def getBestSRs ( data, max_x : Union[None,float], max_y : Union[None,float], 
                 rank ) -> list:
    """ get a list of dictionaries of signal regions, None for no result
    :param rank: get best (rank=1), or second best or ....
    """
    bestSRs = [] # a list of dictioanries of x,y,SR
    skipped, err = 0, None # we also count the number of error points

    for point in data:
        if "error" in point:
            skipped += 1
            err = point["error"]
            if "axes" in point and point["axes"] != None:
                axes = convertNewAxes ( point["axes"] )
                if axes == None:
                    continue
                if not isWithinValue ( axes[1], max_x ):
                    continue
                if not isWithinValue ( axes[0], max_y ):
                    continue
                bestSRs.append ( { "x": axes[1], "y": axes[0], "SR": None } )
            continue
        axes = convertNewAxes ( point["axes"] )
        if max_x != None and axes[1]>max_x:
            continue
        if max_y != None and axes[0]>max_y:
            continue
        ds = point["dataset"]
        if rank == 0:
            print ( f"[plotBestSRs] you specified a rank of zero. The rank is one-indexed, did you mean rank=1?" )
            sys.exit()
        if rank > 1:
            if not "leadingDSes" in point:
                # print ( f"[plotBestSRs] you asked for higher ranks but no leadingDSes were found in validation file. Did you maybe provide the combined or the UL dictionary file (I need the effmap one)?")
                continue
            if len(point["leadingDSes"]) < rank:
                print ( f"[plotBestSRs] you want to plot the {rank}th entry, but we only have {len(point['leadingDSes'])} entries. Consider cranking up keepTopNSRs in the validation ini file and rerun validation." )
            ds = point["leadingDSes"][rank-1][1]
        if axes != None:
            bestSRs.append ( { "x": axes[1], "y": axes[0], "SR": ds } )
    if skipped > 0:
        print ( f"[plotBestSRs] skipped {skipped}/{len(data)} points: {err}" )
    return bestSRs

def countSignalRegions ( bestSRs : dict ) -> dict:
    """ count how often each signal region appears """
    counts = {}
    if bestSRs is None:
        return counts
    for bestSR in bestSRs:
        srname = bestSR["SR"]
        if not srname in counts:
            counts[ srname ] = 0
        counts[ srname ] += 1
    return counts

def getListOfColors ( defcolors : Union[None,list], nr : int ) -> list:
    """ get the list of colors we will be using.
    :param defcolors: in case the user gave us a list of colors, use it
    :param nr: the number of colors we will be needing
    """
    colors = []
    if defcolors == None: # here are our defaults
        colors = [ "r", "g", "b", "c", "m", "y" ] 
        # "#ffa500", '#115f6a', "#A52A2A", "k" ]
        colors += [ "navy", "teal", "maroon", "coral", "lime", "aqua" ]
        colors += [ "indigo", "wheat" ]
    else:
        colors = defcolors
        if type(defcolors)==str:
            colors = defcolors.split(",")
        for i,c in enumerate(colors):
            colors[i]=c.replace("'","").replace('"','')
    if len(colors) < nr:
        colors += [ "k" ]*(nr-len(colors))
    colors = colors[:nr]
    return colors

def getListOfSignalRegions ( srcounts : dict, nmax : int ) -> list:
    """ get the ordered list signal regions we actually wish to plot, i.e.
        the <nmax> most prominent ones """
    regions = []
    invertedSRCounts = {} # a dictionary of signal regions with n_occurenses as keys
    for k,v in srcounts.items():
        if k is None:
            continue
        if not v in invertedSRCounts:
            invertedSRCounts[v]=[]
        invertedSRCounts[v].append(k)
    counts = list ( invertedSRCounts.keys() )
    counts.sort( reverse = True )
    for count in counts: ## go downwards
        for sr in invertedSRCounts[count]: # go through SRs for the count
            regions.append ( sr )
            if len(regions) >= nmax:
                return regions
    return regions
        
def fetchPoints ( bestSRs : list, region : Union[str,None] ) -> tuple:
    """ fetch the coordinates of the points that have region as the 
        best signal region.
    :returns: tuple ( x_coordinates, y_coordinates )
    """
    xs, ys = [], [] # that will be the coordinates
    if bestSRs is None:
        return xs, ys
    for point in bestSRs:
        if point["SR"]!=region:
            continue
        xs.append ( point["x"] )
        y = point["y"]
        if type(y)==str and y=="stable":
            y=widthOfStableParticles
        ys.append ( y )
    return xs, ys

def fetchAllOtherPoints ( bestSRs : list, regions : list ) -> tuple:
    """ fetch the coordinates of all points *not* in regions
    :returns: tuple ( x_coordinates, y_coordinates )
    """
    xs, ys = [], [] # that will be the coordinates
    if bestSRs is None:
        return xs, ys
    for point in bestSRs:
        if point["SR"] in regions or point["SR"] is None:
            continue
        xs.append ( point["x"] )
        y = point["y"]
        if y == "stable": 
            y=1e-26
        ys.append ( y )
    return xs, ys

def plot( dbpath : str, analysis : str, validationfiles : str, 
        max_x : Union[None,float], max_y : Union[None,float], 
        outputfile : str, defcolors : Union[None,list], rank : int, nmax : int,
        show : bool = False, validationPlot = None ):
    """ plot.
    :param dbpath: path to database
    :param analysis: analysis to consider
    :param validationfiles: T*.py files
    :param outputfile: name of outputfile, using @a and @t to stand for
     analysis and topology, respectively
    :param defcolors: user-specified colors
    :param rank: draw best (rank=1), or second best or ....
    :param nmax: maximum SRs to draw (6 by default)
    :param show: show plot in the terminal (kitty only)
    """
    plt.clf()
    content = fetchContent ( validationfiles, dbpath, analysis )
    if content is None:
        print ( f"[plotBestSRs] got no content: returning" )
        return None
    xr = None
    if max_x == None:
        xr = getAxisRange ( content["options"], "xaxis" )
    yr = None
    if max_y == None:
        yr = getAxisRange ( content["options"], "yaxis" )
    data, line = content["data"], content["line"]
    txnames, axisv = content["txnames"], content["axis"]
    bestSRs = getBestSRs ( data, max_x, max_y, rank )
    srcounts = countSignalRegions ( bestSRs )
    colors = getListOfColors ( defcolors, min(len(srcounts),nmax) )
    regions = getListOfSignalRegions ( srcounts, nmax )
    miny, maxy = float("inf"), -float("inf")
    for i,color in enumerate ( colors ): ## lets do it!
        # lets make the scatter plot for color #i
        if i >= len(regions):
            continue
        region = regions[i] # thats the region we are interested in
        xs, ys = fetchPoints ( bestSRs, region )
        xs, ys = filterWithinRanges ( { "x": xs, "y": ys }, xr, yr )
        plt.scatter ( xs, ys, s=25, c=[ color ]*len(xs), label=region )
        miny, maxy = min ( ys + [ miny ] ), max ( ys + [ maxy ] )
    if numpy.isinf ( maxy ):
        print ( f"[plotBestSRs] we have no finite points??" )
        return
    xs, ys = fetchAllOtherPoints ( bestSRs, regions )
    xs, ys = filterWithinRanges ( { "x": xs, "y": ys }, xr, yr )
    miny, maxy = min ( ys + [ miny ] ), max ( ys + [ maxy ] )
    if len(xs)>0:
        plt.scatter ( xs, ys, s=25, c=[ "k" ]*len(xs), label="others" )
    # plot also the no results
    xs, ys = fetchPoints ( bestSRs, None )
    xs, ys = filterWithinRanges ( { "x": xs, "y": ys }, xr, yr )
    plt.scatter ( xs, ys, s=2, c=[ "grey" ]*len(xs), label="no result" )
    miny, maxy = min ( ys + [ miny ] ), max ( ys + [ maxy ] )

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
        plt.plot ( line["x"], line["y"], linewidth=3, color="white" )
        plt.plot ( line["x"], line["y"], linewidth=1, color="black" )
    plt.xlabel ( "x [GeV]" )
    plt.ylabel ( "y [GeV]" )
    ax = plt.gca()
    if miny>1e-30 and maxy<1e-1:
        # the y axis seems to be widths
        ax.set_yscale('log')
        ax.set_ylim ( miny*.2, maxy*5. )
        # plt.ylabel ( "$\Gamma$ [GeV]" )
        # plt.xlabel ( "m [GeV]" )
    ttl = "Best Signal Region"
    if rank > 1:
        sr = f"{rank}nth"
        if rank == 2:
            sr = "second"
        if rank == 3:
            sr = "third"
        ttl = f"{sr} best SR"
    ananame = analysis.replace("-eff","")
    topo = txnames[0]
    axis = "???"
    if validationPlot != None:
        axis = prettyAxes ( validationPlot )
    fig = plt.gcf()
    plt.text(.95,.975,axis,transform=fig.transFigure, fontsize=9,
            horizontalalignment="right" )
    plt.title ( f"{ttl}, {ananame}" )
    txStr = prettyDescriptions.prettyTxname ( topo, outputtype="latex" ).replace("*","^{*}" )
    plt.text(.03,.975,txStr,transform=fig.transFigure, fontsize=9 )
    topo = shortTxName ( txnames )
    print ( f"[plotBestSRs] plotting {analysis} ({topo})" )
    fname = outputfile.replace( "@a", analysis ).replace( "@t", topo )
    srank = "best"
    if rank == 2:
        srank = "second"
    if rank == 3:
        srank = "third"
    if rank > 3:
        srank = f"{rank}nth"
    fname = fname.replace ( "@r", srank )
    print ( f"[plotBestSRs] saving to {YELLOW}{fname}{RESET}" )
    plt.savefig ( fname )
    if show:
        plt.kittyPlot()
    plt.clf()
    return fname

def writeBestSRs( push = False ):
    import glob
    Dir = "../../smodels.github.io/plots/"
    files = glob.glob( f"{Dir}bestSR*png" )
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
    print ( f"[plotBestSRs] cmd {cmd}: {o}" )

if __name__ == "__main__":
    """
    .. code-block::

    >>> ./plotBestSRs.py -d ../../smodels-database -a CMS-SUS-21-002-eff -v TChiWZ_2EqMassAx_EqMassBy.py -r 2

    """
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
    argparser.add_argument ( "-r", "--rank",
            help="which rank (one-indexed) to draw, e.g. leading signal region, or second, or ... [1]",
            type=int, default=1 )
    argparser.add_argument ( "-n", "--nmax",
            help="maximum numbers of SRs [6]",
            type=int, default=6 )
    argparser.add_argument ( "-a", "--analysis",
            help="analysis name, like the directory name [CMS-SUS-16-050-eff]",
            type=str, default="CMS-SUS-16-050-eff" )
    argparser.add_argument ( "-C", "--colors",
            help="specify colors, as string with commas, e.g. 'r,g,b' [None]",
            type=str, default=None )
    argparser.add_argument ( "-v", "--validationfiles",
            help="validation file(s), comma separated within string [T2tt_2EqMassAx_EqMassBy.py]",
            type=str, default="T2tt_2EqMassAx_EqMassBy.py" )
    argparser.add_argument ( "-o", "--outputfile",
            help="output file, replacing @a and @t with analysis and topo name [bestSR_@a_@t.png]",
            type=str, default="./@rSR_@a_@t.png" )
    argparser.add_argument ( "-D", "--default", action="store_true",
            help="default run on arguments. currently set to be the exo 13 006 plots" )
    argparser.add_argument ( "-s", "--show", action="store_true",
            help="show plot, after plotting" )
    argparser.add_argument ( "-c", "--copy", action="store_true",
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    argparser.add_argument ( "-p", "--push", action="store_true",
            help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    args = argparser.parse_args()
    if not args.default and not args.analysis.endswith("-eff") and not args.analysis.endswith("-ma5") and not args.analysis.endswith("-agg") and not args.analysis.endswith("-adl"):
        print ( "[plotBestSRs] warning, analysis name does not end with -eff or some such, might be an error" )
    if args.default:
        for a in [ "CMS-EXO-13-006-andre", "CMS-EXO-13-006-eff" ]:
            for v in [ "THSCPM1b_2EqMassAx_EqWidthAy.py", "THSCPM3_2EqMassAx_EqMassBy**.py", "THSCPM4_*.py", "THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py", "THSCPM6_EqMassA__EqmassAx_EqmassBx-100_Eqma*.py", "THSCPM8_2EqMassAx*.py", "THSCPM2b_*.py" ]:
                print ( f"[plotBestSRs:default] now drawing {a}:{v}" )
                ipath = getPathName ( args.dbpath, a, v )
                fname = plot( ipath, args.max_x, args.max_y, args.outputfile,
                              rank = args.rank, nmax = args.nmax, show = args.show )
                if args.copy:
                    cmd = f"cp {fname} ../../smodels.github.io/plots/"
                    o = subprocess.getoutput ( cmd )
                    print ( f"[plotBestSRs] cmd {cmd}: {o}" )
    else:
        fname = plot( args.dbpath, args.analysis, args.validationfiles, 
                      args.max_x, args.max_y, args.outputfile, args.colors,
                      rank = args.rank, nmax = args.nmax, show=args.show )
        if args.copy:
            cmd = f"cp {fname} ../../smodels.github.io/plots/"
            o = subprocess.getoutput ( cmd )
            print ( f"[plotBestSRs] cmd {cmd}: {o}" )
    if args.copy:
        writeBestSRs( args.push )
