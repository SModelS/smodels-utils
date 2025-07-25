#!/usr/bin/env python3

"""
.. module:: plotRatio.py
   :synopsis: plots the ratio between two similar results, typically
              the ration of the upper limit from the UL map, and the
              upper limit computed from combining the efficiency maps.
"""

import math, os, numpy, copy, sys, glob, ctypes
from os import PathLike
# import setPath
from smodels_utils.plotting import mpkitty as plt
import matplotlib
import time
import logging
import subprocess
from scipy.interpolate import griddata
import itertools
import importlib
from smodels_utils.helper import prettyDescriptions
from smodels_utils.helper.various import getValidationDataPathName
#from smodels_utils.helper.various import getValidationModule
from validation.validationHelpers import getValidationFileContent, shortTxName, \
       mergeExclusionLines, mergeValidationData
import validationHelpers
from validation.plottingFuncs import convertNewAxes
from smodels_utils.helper.terminalcolors import *
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


def hasDebPkg():
    """ do we have the package installed """
    import distutils.spawn
    dpkg = distutils.spawn.find_executable("dpkg")
    if dpkg == None:
        print ( "we are not on a debian-based distro, skipping check for cm-super-minimal. could be you have to install texlive-type1cm" )
        return
    a = subprocess.getoutput ( "dpkg -l cm-super-minimal | tail -n 1" )
    if a.startswith("ii"):
        return True
    print ( "error, you need cm-super-minimal installed! (apt install cm-super-minimal)" )
    return
    #sys.exit(-1)

def axisHash ( axes_ ):
    ret = 0
    axes = convertNewAxes ( axes_ )
    for ctr,a in enumerate(axes):
        ret += 10**(4*ctr)*int(a)
    return ret

def getSModelSExclusionFromContent ( content ):
    """ this method should construct a contur line from one of the dictionary files,
    by constructing a contour plot from 'content' """
    # print ( "content", content )
    # line = [ { "x": [ 300, 500], "y": [ 50, 100 ] } ]
    line = []
    return line

def addDefaults ( options : dict ) -> dict:
    defaults = { "xmin": None, "xmax": None, "xlabel": None, "ylabel": None,
                 "efficiencies": False, "ymin": None, "ymax": None, "zmin": None,
                 "zmax": None, "title": None, "output": "ratios_@a_@t@sr.png",
                 "label1": None, "label2": None, "show": False, "meta": False,
                 "copy": False, "SR": None, "comment": None, "zlabel_offset": .9,
                }
    defaults.update(options)
    return defaults

def hasAxisInfo ( content ):
    """ the content of a validation dict file has info about
        the axes? """
    if not "meta" in content:
        return False
    if content["meta"] is None:
        return False
    meta = content["meta"]
    if type(meta) == dict:
        if not "axes" in meta:
            return False
        return meta["axes"]
    if type(meta) == list:
        if meta[0] is None:
            return False
        if not "axes" in meta[0]:
            return False
        return meta[0]["axes"]
    print ( f"[plotRatio] when searching for axis info, what case is this: {meta}" )
    return False

def guessLabel ( label, anaId1, anaId2, valfile1 ):
    if label != None:
        return label
    label = "???"
    if anaId2 in anaId1:
        label = anaId1.replace(anaId2,"")
        if "combined" in valfile1:
            label = "combined"
    if anaId1 in anaId2:
        label = anaId2.lower()
    if anaId2 == anaId1 + "-eff":
        label = "ul"
    if anaId2 == anaId1 + "-agg":
        label = "ul"
    if anaId2 == anaId1:
        label = "ul"
    if label.startswith("-"):
        label = label[1:]
    if label == "???":
        p1 = anaId1.rfind("-")
        last = anaId1[p1+1:]
        if not last.isdigit() and not last in [ "eff" ]:
            label = last
    print ( f"[plotRatio] have been asked to guess the label for {anaId1} re {anaId2}: {label}" )
    return label

def draw ( options : dict ):
    """ plot.
    :param options: a dictionary of various options:
    :option zmin: the minimum z value, e.g. .5
    :option zmax: the maximum z value, e.g. 1.7
    :option xlabel: label on x axis, default: x [GeV]
    :option ylabel: label on y axis, default: y [GeV]
    :option show: show plot in terminal
    :option comment: a possible comment to be added to the plot
    """
    analysis1 = options["analysis1"]
    analysis2 = options["analysis2"]
    valfile1 = options["valfile1"]
    valfile2 = options["valfile2"]
    dbpath = options["dbpath"]
    plt.clf()
    options = addDefaults ( options )
    contents = []
    topos = set()
    axis1, axi2 = None, None
    for valfile in valfile1.split(","):
        ipath1 = getValidationDataPathName ( dbpath, analysis1, valfile, options["folder1"] )
        content = getValidationFileContent ( ipath1 )
        axis1 = '[[x, y], [x, y]]'
        if not "meta" in content or content["meta"] is None:
            print ( f"[plotRatio] meta info is missing in {ipath1}. Perhaps rerun validation?" )
            #return
            # continue
            # sys.exit()
        else: 
            if "axes" in content["meta"]:
                axis1 = content["meta"]["axes"]
            else:
                print ( f"[plotRatio] meta 'axes' info is missing in {ipath1}. Perhaps rerun validation?" )
                print ( f"[plotRatio] {dbpath} {analysis1} {valfile} {options['folder1']}" )
                #return
                # sys.exit()
        contents.append ( content )
        p1 = valfile.find("_")
        topos.add ( valfile[:p1] )
    content1 = mergeValidationData ( contents )
    contents = []
    for valfile in valfile2.split(","):
        ipath2 = getValidationDataPathName ( dbpath, analysis2, valfile, options["folder2"] )
        content = getValidationFileContent ( ipath2 )
        if not "meta" in content or content["meta"] is None:
            print ( f"[plotRatio] meta info is missing in {ipath2}. Perhaps rerun validation?" )
        axis2 = axis1
        if "meta" in content and content["meta"] is not None and "axes" in content["meta"]:
            axis2 = content["meta"]["axes"]
        contents.append ( content )
    content2 = mergeValidationData ( contents )
    if "meta" in content1 and len(content1["meta"])>0 and "axes" in \
            content1["meta"][0] and not "y" in content1["meta"][0]["axes"]:
        if "eul" in options:
            return
        print ( f"[plotRatio.py] seems like a 1d plot, delegate to plot1DRatio" )
        import plot1DRatio
        plot1DRatio.draw ( options )
        return
    if "meta" in content2 and len(content2["meta"])>0 and "axes" in \
            content2["meta"][0] and not "y" in content2["meta"][0]["axes"]:
        if "eul" in options:
            return
        print ( f"[plotRatio.py] seems like a 1d plot, delegate to plot1DRatio" )
        import plot1DRatio
        plot1DRatio.draw ( options )
        return

    xlabel, ylabel = options["xlabel"], options["ylabel"]
    if xlabel in [  None, "" ]:
       xlabel = "x [GeV]"
       # xlabel = "m$_{mother}$ [GeV]"
    if ylabel in [  None, "" ]:
       ylabel = "y [GeV]"
       # ylabel = "m$_{LSP}$ [GeV]"

    hasDebPkg()
    rs,effs={},{}
    nsr=""
    noaxes = 0
    data1 = content1["data"]
    ul = "UL"
    if "eul" in options and options["eul"]==True:
        ul = "eUL"
    for ctr,point in enumerate( data1 ):
        if not "axes" in point:
            noaxes+=1
            if noaxes < 5:
                f1 = imp1.__file__.replace(dbpath,"")
                slhapoint = point["slhafile"].replace(".slha","")
                print ( f"INFO: no axes in {f1}:{slhapoint}" )
            if noaxes == 5:
                print ( " ... (more error msgs like these) " )
            continue
        axes_ = point["axes"]
        if axes_ is None:
            continue
            #print ( f"[plotRatio] the axis field is 'None' in {imp1.__file__}. Will stop." )
            #sys.exit()
        axes = convertNewAxes ( axes_ )
        h = axisHash ( axes )
        if not "UL" and not "efficiency" in point:
            continue
        if "y" in point["axes"] and point["axes"]["x"]<point["axes"]["y"]:
            print ( "axes", axes_, "list", axes, "hash", h, "ul", point["UL"], "sig", point["signal"] )
        if ul in point and point[ul] != None:
            if type(point[ul])==str:
                point[ul]=eval(point[ul])
            rs[ h ] = point["signal"] / point[ ul ]
        if "efficiency" in point and point["efficiency"] != None:
            effs[ h ] = point["efficiency"]
            if options["SR"] != None:
                if "leadingDSes" in point:
                    effs[h]=float("nan")
                    for val,nam in point["leadingDSes"]:
                        if nam == options["SR"]:
                            effs[h]=val
                else:
                    print ( f"[plotRatio.py] you specified SR {options['SR']} but no leadingDSes are in validation file {ipath1}. Perhaps rerun validation?" )
                    return
                    # sys.exit()
        # uls[ h ] = point["signal" ] / point["UL"]

    err_msgs = 0

    data2 = content2["data"]
    points = []
    plotEfficiencies = options["efficiencies"]

    for ctr,point in enumerate(data2):
        axes = convertNewAxes ( point["axes"] )
        if axes == None:
            continue
        h = axisHash ( axes )
        r1 = None
        eff1 = None
        if h in rs.keys():
            r1 = rs[h]
        if h in effs.keys():
            eff1 = effs[h]
        hasResult = False
        ul = "UL"
        if "eul2" in options and options["eul2"]==True:
            ul = "eUL"
        if not plotEfficiencies and r1 and r1>0. and ul in point and point[ul] != None:
            r2 = point["signal"] / point[ul]
            ratio = float("nan")
            if r2 > 0.:
                ratio = r1 / r2
            # print ( f"masses:{axes[0],axes[1]} r={ratio} from r1,r2={r1,r2}" )
            #sys.exit()
            tpl = (axes[0],ratio )
            if len(axes)>1:
                tpl = (axes[0],axes[1],ratio )
            points.append ( tpl )
            hasResult = True
        if plotEfficiencies and eff1 and eff1>=0. and "efficiency" in point and options["SR"] is None: ## best SR!!
            eff2 = point["efficiency"]
            ratio = float ("nan" )
            if eff2 > 0.:
                ratio = eff1 / eff2
            points.append ( (axes[0],axes[1],ratio ) )
            hasResult = True
        if plotEfficiencies and eff1 and eff1>=0. and options["SR"] is not None:
            if not "leadingDSes" in point:
                continue
                #print ( f"[plotRatio.py] you specified SR {options['SR']} but no leadingDSes are in validation file {ipath2}. Perhaps rerun validation?" )
                #sys.exit()
            else:
                sr = options["SR"]
                eff2 = float("nan")
                for val,nam in point["leadingDSes"]:
                    if nam == sr:
                        eff2 = val
                ratio = float ("nan" )
                if eff2 > 0.:
                    ratio = eff1 / eff2
                points.append ( (axes[0],axes[1],ratio ) )
                hasResult = True
        if not hasResult:
            err_msgs += 1
            if err_msgs < 3:
                errmsg = ""
                if "error" in point:
                    errmsg = f': {point["error"]}'
                print ( f"[plotRatio] insufficient data to plot point {point['slhafile']}: {errmsg}" )

    if len(points) == 0:
        print ( f"[plotRatio] found no legit points but {err_msgs} err msgs in {ipath2}" )
        return
        # sys.exit()

    points.sort()
    points = numpy.array ( points )
    x = points[::,1].tolist()
    y = points[::,0].tolist()
    # coll = points[::,2].tolist()
    minx, maxx = min(x), max(x)
    miny, maxy = min(y), max(y)
    if options["xmax"]!=None:
        maxx = options["xmax"]
    if options["xmin"]!=None:
        minx = options["xmin"]
    if options["ymax"]!=None:
        maxy = options["ymax"]
    if options["ymin"]!=None:
        miny = options["ymin"]
    ranges = { "x": [ minx, maxx ], "y": [ miny, maxy ] }
    nx, ny = 250, 250
    if abs ( maxx - minx ) / ( maxx + minx ) < 1e-10:
        logger.error ( f"the x range seems to have zero length? x={x}" )
        return
    x_ = numpy.arange ( minx, maxx, ( maxx-minx) / nx )
    y_ = numpy.arange ( miny, maxy, ( maxy-miny) / ny )
    logScale = False
    if max(y) < 1e-10 and min(y) > 1e-40:
        logScale = True
        y_ = numpy.logspace ( numpy.log10(.3*min(y)), numpy.log10(3.*max(y)), ny )
    yx = numpy.array(list(itertools.product(y_,x_)) )
    x = yx[::,1]
    y = yx[::,0]
    dim = len(points[0])-1
    s = 0.35 # size
    if dim==1:
        x = yx[::,0]
        y = [0.]*len(x)
        s = 20.
    col = griddata ( points[::,0:2], points[::,dim], yx, rescale=True )
    if err_msgs > 0:
        print ( "[plotRatio] couldnt find data for %d/%d points" % \
                (err_msgs, len( content2["data"] ) ) )

    #changed colormap to have discrete bins instead of continuous
    try:
        cm = matplotlib.cm.get_cmap('seismic')
    except AttributeError as e:
        cm = plt.colormaps["seismic"]
    plt.rc('text', usetex=True)
    # vmin,vmax= .5, 1.7
    vmin, vmax = options["zmin"], options["zmax"]
    if vmax is None or abs(vmax)<1e-5:
        vmax = min ( numpy.nanmax ( col )*1.1, 2.0 )
    if vmin is None: # or abs(vmin)<1e-5:
        vmin = abs ( numpy.nanmin ( col )*0.9 - 1.0 )
    if (vmax - 1.0 ) < ( 1.0 - vmin ):
        vmax = 2. - vmin
    else:
        vmin = 2. - vmax
    opts = { }
    #print ( "vmax", vmax )
    #if logScale:
    #    vmin = 1e-5
    #    vmax = 0.5
    if vmax > 5.:
        opts = { "norm": matplotlib.colors.LogNorm()  }
    else:
        opts = { "vmin": vmin, "vmax": vmax }

    scatter = plt.scatter ( x, y, s=s, c=col, marker="o", cmap=cm, **opts )
    ax = plt.gca()
    fig = plt.gcf()
    plt.ylabel ( ylabel, size=13 )
    plt.xlabel ( xlabel, size=13 )
    if logScale:
        ax.set_yscale("log")
        ax.set_ylim ( min(y)*.2, max(y)*5. )
    #ax.set_xticklabels(map(int,ax.get_xticks()), { "fontweight": "normal", "fontsize": 14 } )
    #if not logScale:
    #    ax.set_yticklabels(map(int,ax.get_yticks()), { "fontweight": "normal", "fontsize": 14 } )
    plt.rcParams.update({'font.size': 14})
    #plt.rcParams['xtick.labelsize'] = 14
    #plt.rcParams['ytick.labelsize'] = 14
    slhafile=content2["data"][0]["slhafile"]
    Dir=os.path.dirname ( ipath1 )
    Dir2=os.path.dirname ( ipath2 )
    # smsrootfile = Dir.replace("validation","sms.root" )
    # smsrootfile2 = Dir2.replace("validation","sms.root" )
    exclusionlines1 = Dir.replace( options["folder1"],"exclusion_lines.json" )
    exclusionlines2 = Dir2.replace( options["folder2"],"exclusion_lines.json" )
    analysis=Dir[ Dir.rfind("/")+1: ]
    topo = shortTxName ( list ( topos ) )
    stopos = []
    for t in topos:
        stopo = prettyDescriptions.prettyTxname ( t, outputtype="latex" ).replace("*","^{*}" )
        stopos.append ( stopo )
    stopo = "+".join ( stopos )
    if len(topos)==1:
        stopo = "".join(topos)+": "+stopo

    isEff = False
    if "-eff" in analysis1 or "-eff" in analysis2:
        isEff = True
    origAnaId = anaId = analysis1
    anaId = analysis1.replace("-andre","")
    anaId = anaId.replace("-orig","").replace("-old","") # .replace("-eff","")
    anaId2 = analysis2.replace("-andre","")
    anaId2 = anaId2.replace("-orig","").replace("-old","") # .replace("-eff","")
    #title = "%s: $\\frac{\\mathrm{%s}}{\\mathrm{%s}}$" % ( topo, anaId, anaId2 )
    #if anaId2 == anaId:
    #    title = "ratio: %s, %s" % ( anaId, topo )
    title = options["title"]
    if title is None:
        if anaId2 in anaId:
            title = anaId2
        if anaId in anaId2:
            title = anaId
    if "eul" in options and options["eul"]==True:
        title += " (expected)"
    else:
        title += " (observed)"

    plt.title ( title )
    txStr = stopo
    if options["SR"] != None:
        txStr+=f' [{options["SR"]}]'
    plt.text(.03,.95,txStr,transform=fig.transFigure, fontsize=9 )
    dataMap = None
    if "meta" in content and "dataMap" in content["meta"]:
        dataMap = content["meta"]["dataMap"]
    axis = prettyDescriptions.prettyAxes ( list(topos)[0], axis1, dataMap ) #, outputtype="latex" )
    if axis1 != axis2:
        print ( f"[plotRatio] error, different axes: {axis1}!={axis2}" )
        # return
        # sys.exit()
    plt.text(.95,.95,axis,transform=fig.transFigure, fontsize=9,
            horizontalalignment="right" )
    # plt.title ( "$f$: %s, %s %s" % ( s_ana1.replace("-andre",""), topo, stopo) )
    if not logScale:
        plt.xlabel ( xlabel, fontsize=13 )
    plt.rc('text', usetex=True)
    if "052" in analysis:
      # label = "$\Delta m$(mother, daughter) [GeV]"
      label = "m$_{mother}$ - m$_{daughter}$ [GeV]"
    if not logScale:
        plt.ylabel ( ylabel, fontsize=13 )

    plt.colorbar()
    # plt.colorbar( format="%.1g" )
    el = []
    hasLegend = False
    axes = None
    for t in topos:
        axes = hasAxisInfo ( content1 )
        if axes in [ None, False ]: # search on
            axes = hasAxisInfo ( content2 )
        from smodels_utils.helper import various
        el = various.getExclusionCurvesFor ( exclusionlines1, t, axes, ranges=ranges )
        el2 = various.getExclusionCurvesFor ( exclusionlines2, t, axes, ranges=ranges )
        label = "official exclusion"
        # label = anaId
        if hasLegend:
            label = ""
        if el2 == el: # if its exactly identical, then drop
            el2 = []
            #removing analysisID name for contour line
            #label += f"(+{anaId2})"
        if el is not None and t in el:
            for E in el[t]:
                name = E["name"]
                # print ( "name", name )
                hasLegend = True
                px = E["points"]["x"]
                if "y" in E["points"]:
                    py = E["points"]["y"]
                else:
                    py = px
                    px = [ 0. ] * len (py)
                plt.plot ( px, py, color='white', linestyle='-', linewidth=4, label="" )
                plt.plot ( px, py, color='k', linestyle='-', linewidth=3, label=label )
                label = ""
        if el2 != None and t in el2:
            for E in el2[t]:
                label = anaId2
                hasLegend = True
                if "points" in E:
                    E = E["points"]
                px = E["x"]
                plt.plot ( px, E["y"], color='white', linestyle='-', linewidth=4, label="" )
                plt.plot ( px, E["y"], color='darkred', linestyle='-', linewidth=3, label=label )
                label = ""
    smodels_root = f"{analysis}/{topo}.root"
    if not os.path.exists ( smodels_root ):
        # print ( f"[plotRatio] warn: {smodels_root} does not exist. Trying to get the exclusion line directly from the content of the dict file" )
        # print ( "[plotRatio] warn: %s does not exist. It is needed if you want to see the SModelS exclusion line." % smodels_root )
        # smodels_line = []
        el2 = getSModelSExclusionFromContent ( content1 )
    else:
        print ( f"[plotRatio] warn: {smodels_root} does exist. Maybe switch to jsons?" )
        smodels_line = getSModelSExclusion ( smodels_root )
        el2 = getExclusionLine ( smodels_line )
    print ( f"[plotRatio] Found SModelS exclusion line with {len(el2)} points." )
    label="SModelS exclsuion"
    for E in el2:
        hasLegend = True
        px = E["x"]
        plt.plot ( px, E["y"], color='grey', linestyle='-', linewidth=4, label=label )
        label=""

    maxx = max(x)
    maxy = max(y)
    miny = min(y)
    if abs ( miny - 10. ) < 3.:
        miny = 10.15
    if abs ( maxy - 80. ) < 3.:
        maxy = 79.9
    if nsr != "":
        plt.text ( .90*maxx, miny-.19*(maxy-miny), f"{nsr}", fontsize=14 )

    figname = f'{analysis.replace( options["folder1"],"ratio" )}_{topo}_{validationHelpers.getNiceAxes(axes)}.png'
    output = options["output"]
    if output != None:
        figname = output.replace("@t", topo ).replace("@a1", anaId ).replace("@a2", anaId2 )
        figname = figname.replace( "@a",anaId )
    sr = ""
    if options["SR"] != None:
        sr="_"+options["SR"]

    figname = figname.replace("@sr",sr)
    a1, a2 = options["label1"], options["label2"]
    a1 = guessLabel ( options["label1"], origAnaId, anaId2, valfile )
    a2 = guessLabel ( options["label2"], anaId2, anaId, valfile2 )

    line = f"$f$ = $r$({a1}) / $r$({a2})"
    if options["efficiencies"]:
        line = f"$f$ = eff({a1}) / eff({a2})"
    plt.text ( options["zlabel_offset"], .5, line, fontsize=13, rotation = 90,
               verticalalignment="center",
               horizontalalignment="center", transform=fig.transFigure)

    #text about no of SR in combined dataset
    # plt.text ( .97, .0222, "combination of 9 signal regions", transform = fig.transFigure, fontsize=10,
    #            horizontalalignment="right" )
    rmean,rstd,npoints =  numpy.nanmean(col), numpy.nanstd(col),len(col)-sum(numpy.isnan(col))
    plt.text ( .80, .025, f"$\\bar{{f}}={rmean:.2f}\\pm{rstd:.2f}$",
            transform=fig.transFigure, c="grey", fontsize=12  )
    if options["comment"] not in [ None, "", "None" ]:
        plt.text ( .1, .025, options["comment"], transform=fig.transFigure, 
                   c="grey", fontsize=12  )
    print ( f"[plotRatio] Saving to {YELLOW}{figname}{RESET}" )
    if hasLegend:
        plt.legend()
    try:
        plt.savefig ( figname )
    except (RuntimeError,FileNotFoundError) as e:
        print ( f"[plotRatio] error when calling savefig: {e}" )
        if "tex" in str(e).lower():
            print ( f"[plotRatio] consider loading/installing latex, eg via:" )
            # print ( f"ml load texlive/20210324-gcccore-10.2.0 # on the clip cluster" )
            print ( f"ml load texlive/20220321-gcc-12.2.0 # on the clip cluster" )
            print ( f"sudo apt install texlive dvipng # on debian based linux distros" )
            return
            # sys.exit()
    if options["show"]:
        plt.kittyPlot()
#        plt.show()
    if options["copy"]:
      cmd=f"cp {figname} ~/git/smodels.github.io/plots/"
      print ( f"[plotRatio] {cmd}" )
      subprocess.getoutput ( cmd )
    if options["meta"]:
        with open ( "ratios.txt", "at") as f:
            f.write ( f"{figname} {rmean:.2f} +/- {rstd:.2f}\n" )
    print ( f"[plotRatio] ratio={rmean:.2f} +/- {rstd:.2f} (with {npoints} points)" )
    plt.clf()

def writeMDPage( copy ):
    """ write the markdown page that lists all plots """
    with open("ratioplots.md","wt") as f:
        # f.write ( "# ratio plots on the upper limits, andre / suchi \n" )
        f.write ( "# ratio plots on the upper limits\n" )
        f.write ( f"as of {time.asctime()}\n\n" )
        # f.write ( "see also [best signal regions](bestSRs)\n\n" )
        f.write ( "| ratio plots | ratio plots |\n" )
        files = glob.glob("ratio_*.png" )
        files = glob.glob("ratios_*.png" )
        files += glob.glob("atlas_*png" )
        files += glob.glob("cms_*png" )
        files += glob.glob("bestSR_*png" )
        files.sort()
        ctr = 0
        t0=time.time()-1592000000
        for ctr,i in enumerate( files ):
            src = f"https://smodels.github.io/plots/{i}"
            f.write ( '| <img src="%s?%d" /> ' % ( src, t0 ) )
            if ctr % 2 == 1:
                f.write ( "|\n" )
        if ctr % 2 == 0:
            f.write ( " | |\n" )
        f.close()
    if copy:
        cmd = "cp ratioplots.md ~/git/smodels.github.io/plots/README.md"
        subprocess.getoutput ( cmd )

def main():
    import argparse
    argparser = argparse.ArgumentParser( description = "ratio plot" )
    argparser.add_argument ( "-v1", "--validationfile1",
            help="first validation file [THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py]",
            type=str, default="THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py" )
    argparser.add_argument ( "-v2", "--validationfile2",
            help="second validation file. If empty, then same as v1. [""]",
            type=str, default="" )
    argparser.add_argument ( "-a1", "--analysis1",
            help="first analysis name, like the directory name [ATLAS-SUSY-2013-09]",
            type=str, default="ATLAS-SUSY-2013-09" )
    argparser.add_argument ( "-a2", "--analysis2",
            help="second analysis name, like the directory name, if not specified then same as analysis1 [None]",
            type=str, default=None )
    argparser.add_argument ( "-l1", "--label1",
            help="label in the legend for analysis1, guess if None [None]",
            type=str, default=None )
    argparser.add_argument ( "-f1", "--folder1",
            help="validation folder name for analysis1 [validation]",
            type=str, default="validation" )
    argparser.add_argument ( "-f2", "--folder2",
            help="validation folder name for analysis2 [validation]",
            type=str, default="validation" )
    argparser.add_argument ( "--SR",
            help="plot ratio of efficiencies of this signal region. None = bestSR. Will turn on --efficiencies [None]",
            type=str, default=None )
    argparser.add_argument ( "-o", "--output",
            help="outputfile, the @x's get replaced [ratios_@a_@t@sr.png]",
            type=str, default="ratios_@a_@t@sr.png" )
    argparser.add_argument ( "-l2", "--label2",
            help="label in the legend for analysis2, guess if None [None]",
            type=str, default=None )
    argparser.add_argument ( "-yl", "--ylabel",
            help="label on the y axis, guess if None",
            type=str, default=None )
    argparser.add_argument ( "-xl", "--xlabel",
            help="label on the x-axis, guess if None",
            type=str, default=None )
    argparser.add_argument ( "--title",
            help="plot title, guess if None",
            type=str, default=None )
    argparser.add_argument ( "-z", "--zmin",
            help="minimum z value, None means auto [.5]",
            type=float, default=.5 )
    argparser.add_argument ( "-Z", "--zmax",
            help="maximum Z value, None means auto [1.5]",
            type=float, default=1.5 )
    argparser.add_argument ( "-x", "--xmin",
            help="minimum x value, None means auto [None]",
            type=float, default=None )
    argparser.add_argument ( "--zlabel_offset",
            help="offset of zlabel [.9]",
            type=float, default=.9 )
    argparser.add_argument ( "-X", "--xmax",
            help="maximum x value, None means auto [None]",
            type=float, default=None )
    argparser.add_argument ( "-y", "--ymin",
            help="minimum y value, None means auto [None]",
            type=float, default=None )
    argparser.add_argument ( "-Y", "--ymax",
            help="maximum y value, None means auto [None]",
            type=float, default=None )
    argparser.add_argument ( "--comment",
            help="add a comment to the plot [None]",
            type=str, default=None )
    argparser.add_argument ( "-d", "--dbpath",
            help="path to database [../../smodels-database/]", type=str,
            default="../../smodels-database/" )
    argparser.add_argument ( "-e1", "--eul", action="store_true",
            help="for the first analysis, use expected, not observed, upper limits" )
    argparser.add_argument ( "-e2", "--eul2", action="store_true",
            help="for the second analysis, use expected, not observed, upper limits" )
    argparser.add_argument ( "-e", "--efficiencies", action="store_true",
            help="plot ratios of efficencies of best SRs, not ULs" )
    argparser.add_argument ( "-c", "--copy", action="store_true",
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    argparser.add_argument ( "-s", "--show", action="store_true",
            help="show plot in terminal" )
    argparser.add_argument ( "-m", "--meta", action="store_true",
            help="produce the meta files, ratios.txt and ratioplots.md" )
    argparser.add_argument ( "-p", "--push", action="store_true",
            help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    args = argparser.parse_args()
    if args.SR != None:
        args.efficiencies = True
    if args.analysis2 in [ None, "", "None" ]:
        args.analysis2 = args.analysis1
    if not "_" in args.validationfile1:
        args.validationfile1 = args.validationfile1 + "_2EqMassAx_EqMassBy.py"
    if not args.validationfile1.endswith ( ".py" ):
        args.validationfile1 += ".py"

    valfiles = [ args.validationfile1 ]
    for valfile1 in valfiles:
        valfile2 = args.validationfile2
        if valfile2 in [ "", "none", "None", None ]:
            valfile2 = valfile1
        if not "_" in valfile2:
            valfile2 = valfile2 + "_2EqMassAx_EqMassBy.py"
        args.valfile1 = valfile1
        args.valfile2 = valfile2
        draw ( vars(args) )

    if args.meta:
        writeMDPage( args.copy )

    cmd = "cd ~/git/smodels.github.io/; git commit -am 'automated commit'; git push"
    o = ""
    if args.push:
        print ( f"[plotRatio] now performing {cmd}: {o}" )
        o = subprocess.getoutput ( cmd )
    else:
        if args.copy:
            print ( f"[plotRatio] now you could do:\n{cmd}: {o}" )

if __name__ == "__main__":
    main()
