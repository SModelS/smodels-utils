#!/usr/bin/env python3

""" Plot the ratio between the upper limit from the UL map, and our
own upper limit computed from combining the efficiency maps. """

import math, os, numpy, copy, sys, glob
import matplotlib.pyplot as plt
import matplotlib
import ROOT
import time
import logging
import subprocess
from scipy.interpolate import griddata
import itertools
import importlib
import setPath
from smodels_utils.helper import prettyDescriptions
from smodels_utils.helper.various import getPathName
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

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

def axisHash ( axes_ ):
    ret = 0
    axes = convertNewAxes ( axes_ )
    for ctr,a in enumerate(axes):
        ret += 10**(3*ctr)*int(a)
    return ret

def getExclusionsFrom ( rootpath, txname, axes=None ):
    """
    :param axes: only specific axes
    """
    get_all = False
    rootFile = ROOT.TFile(rootpath)
    txnames = {}
    #Get list of TxNames (directories in root file)
    for obj in rootFile.GetListOfKeys():
        objName = obj.ReadObj().GetName()
        if txname and txname != objName: continue
        txnames[objName] = obj.ReadObj()
    if not txnames:
        logger.warning("[plotRatio] Exclusion curve for %s not found in %s" %(txname,rootpath))
        return False

    #For each Txname/Directory get list of exclusion curves
    nplots = 0
    for tx,txDir in txnames.items():
        txnames[tx] = []
        for obj in txDir.GetListOfKeys():
            objName = obj.ReadObj().GetName()
            if not 'exclusion' in objName.lower(): continue
            if (not get_all) and (not 'exclusion_' in objName.lower()): continue
            if 'expexclusion' in objName.lower(): continue
            # print "[plottingFuncs.py] name=",objName
            if axes and not axes in objName: continue
            txnames[tx].append(obj.ReadObj())
            nplots += 1
    if not nplots:
        logger.warning("No exclusion curve found.")
        return False
    return txnames[txname][0] ## here we only need the central


def getSModelSExclusion ( rootpath ):
    """ obtain the smodels exclusion line  from validation plot. """
    rootFile = ROOT.TFile(rootpath)
    if not rootFile.IsOpen():
        return []
    vp = rootFile.Get("Validation Plot")
    ret = []
    try:
        for i in range(1,99):
            line = vp.GetListOfPrimitives().At(i)
            col = line.GetLineColor()
            sty = line.GetLineStyle()
            wdh = line.GetLineWidth()
            if sty == 1 and col == 922:
                ret.append ( line )
    except Exception as e:
        pass
    return ret


def getExclusionLine ( line ):
    """ get the values of exclusion line from tgraphs.
    :params line: either a tgraph, or a list of tgraphs
    """
    # line = getExclusionsFrom ( rootpath, txname, axes )
    if type(line)==list:
        x = []
        for l in line:
            xs = getExclusionLine ( l )[0]
            x.append ( xs )
        return x
    x,y=ROOT.Double(),ROOT.Double()
    x_v,y_v=[],[]
    for i in range(line.GetN()):
      line.GetPoint(i,x,y)
      x_v.append(copy.deepcopy(x))
      y_v.append(copy.deepcopy(y))
    return [ { "x": x_v, "y": y_v } ]

def draw ( imp1, imp2, copy, label1, label2, dbpath, output ):
    uls={}
    nsr=""
    noaxes = 0
    for point in imp1.validationData:
        if not "axes" in point:
            noaxes+=1
            if noaxes < 5:
                f1 = imp1.__file__.replace(dbpath,"")
                slhapoint = point["slhafile"].replace(".slha","")
                print ( "INFO: no axes in %s:%s" % ( f1, slhapoint ) )
            if noaxes == 5:
                print ( " ... (more error msgs like these) " )
            continue
        axes_ = point["axes"]
        axes = convertNewAxes ( axes_ )
        h = axisHash ( axes )
        if not "UL" in point:
            continue
        uls[ h ] = point["UL" ] / point["signal"]


    err_msgs = 0

    ipoints = imp2.validationData
    points = []

    for point in ipoints:
        axes = convertNewAxes ( point["axes"] )
        h = axisHash ( axes )
        ul1 = None
        if h in uls.keys():
            ul1 = uls[h]
        if ul1 and ul1>0. and "UL" in point:
            ul2 = point["UL"] / point["signal"]
            ratio = float("nan")
            if ul2 > 0.:
                ratio = ul1 / ul2
            # print ( "ratio",axes[0],axes[1],ratio )
            points.append ( (axes[0],axes[1],ratio ) )
        else:
            err_msgs += 1
            #if err_msgs < 5:
            #    print ( "cannot find data for point", point["slhafile"] )

    points.sort()
    points = numpy.array ( points )
    x = points[::,1].tolist()
    y = points[::,0].tolist()
    col = points[::,2].tolist()
    x_ = numpy.arange ( min(x), max(x), ( max(x)-min(x)) / 1000. )
    y_ = numpy.arange ( min(y), max(y), ( max(y)-min(y)) / 1000. )
    logScale = False
    if False: # max(y) < 1e-10 and min(y) > 1e-40:
        logScale = True
        y_ = numpy.logspace ( numpy.log10(.3*min(y)), numpy.log10(3.*max(y)), 1000 )
    #print ( "y", y[:10] )
    #print ( "x", x[:10] )
    #print ( "y_", y_[:10] )
    #print ( "x_", x_[:10] )
    # yx = numpy.array(list(itertools.product( y ,x )) )
    yx = numpy.array(list(itertools.product(y_,x_)) )
    x = yx[::,1]
    y = yx[::,0]
    col = griddata ( points[::,0:2], points[::,2], yx, rescale=True )

    if err_msgs > 0:
        print ( "[plotRatio] couldnt find data for %d/%d points" % (err_msgs, len( imp2.validationData ) ) )

    cm = plt.cm.get_cmap('jet')
    plt.rc('text', usetex=True)
    vmin,vmax= .5, 1.7
    if False:
        vmax = numpy.nanmax ( col )*1.1
        vmin = numpy.nanmin ( col )*0.9
    opts = { }
    #print ( "vmax", vmax )
    #if logScale:
    #    vmin = 1e-5
    #    vmax = 0.5
    if vmax > 5.:
        opts = { "norm": matplotlib.colors.LogNorm()  }
        
    scatter = plt.scatter ( x, y, s=0.25, c=col, marker="o", cmap=cm,
                            vmin=vmin, vmax=vmax, **opts )
    ax = plt.gca()
    plt.ylabel ( "$\Gamma$ [GeV]", size=13 )
    plt.xlabel ( "m [GeV]", size=13 )
    if logScale:
        ax.set_yscale("log")
        ax.set_ylim ( min(y)*.2, max(y)*5. )
    ax.set_xticklabels(map(int,ax.get_xticks()), { "fontweight": "normal", "fontsize": 14 } )
    if not logScale:
        ax.set_yticklabels(map(int,ax.get_yticks()), { "fontweight": "normal", "fontsize": 14 } )
    plt.rcParams.update({'font.size': 14})
    #plt.rcParams['xtick.labelsize'] = 14
    #plt.rcParams['ytick.labelsize'] = 14
    slhafile=imp2.validationData[0]["slhafile"]
    Dir=os.path.dirname ( imp1.__file__ )
    smsrootfile = Dir.replace("validation","sms.root" )
    analysis=Dir[ Dir.rfind("/")+1: ]
    topo=slhafile[:slhafile.find("_")]
    # print ( "smsrootfile", smsrootfile )
    stopo = prettyDescriptions.prettyTxname ( topo, outputtype="latex" ).replace("*","^{*}" )

    plt.title ( "$f$: %s, %s" % ( imp1.ana.replace("-andre",""), topo) )
    # plt.title ( "$f$: %s, %s %s" % ( s_ana1.replace("-andre",""), topo, stopo) )
    if not logScale:
        plt.xlabel ( "m$_{mother}$ [GeV]", fontsize=13 )
    plt.rc('text', usetex=True)
    label = "m$_{LSP}$ [GeV]"
    if "052" in analysis:
      # label = "$\Delta m$(mother, daughter) [GeV]"
      label = "m$_{mother}$ - m$_{daughter}$ [GeV]"
    if not logScale:
        plt.ylabel ( label, fontsize=13 )

    plt.colorbar()
    # plt.colorbar( format="%.1g" )
    el = []
    hasLegend = False
    line = getExclusionsFrom ( smsrootfile, topo )
    if line is not False:
        el = getExclusionLine ( line )
    label = "official exclusion"
    for E in el:
        hasLegend = True
        plt.plot ( E["x"], E["y"], color='k', linestyle='-', linewidth=4, label=label )
        label = ""
    smodels_root = "%s/%s.root" % ( analysis, topo )
    if not os.path.exists ( smodels_root ):
        print ( "[plotRatio] warn: %s does not exist. It is needed if you want to see the SModelS exclusion line." % smodels_root )
        smodels_line = []
    else:
        smodels_line = getSModelSExclusion ( smodels_root )
    el2 = getExclusionLine ( smodels_line )
    print ( "[plotRatio] Found SModelS exclusion line with %d points." % ( len(el2) ) )
    label="SModelS exclsuion"
    for E in el2:
        hasLegend = True
        plt.plot ( E["x"], E["y"], color='grey', linestyle='-', linewidth=4, label=label )
        label=""

    maxx = max(x)
    maxy = max(y)
    miny = min(y)
    if abs ( miny - 10. ) < 3.:
        miny = 10.15
    if abs ( maxy - 80. ) < 3.:
        maxy = 79.9
    if nsr != "":
        plt.text ( .90*maxx, miny-.19*(maxy-miny), "%s" % ( nsr) , fontsize=14 )
    figname = "%s_%s.png" % ( analysis.replace("validation","ratio" ), topo )
    if output != None:
        # figname = output.replace("@t", topo ).replace("@a",analysis.replace("validation","") )
        figname = output.replace("@t", topo )
    #if srs1 !="all":
    #    figname = "%s_%s_%s.png" % ( analysis, topo, srs )
    """
    a1, a2 = "$a_1$", "$a_2$"
    for ide,label in { "andre": "andre", "eff": "suchi" }.items():
        if ide in imp1.ana:
            a1 = label
        if ide in imp2.ana:
            a2 = label
    """
    a1, a2 = label1, label2
    ypos = .2*max(y)
    if logScale:
        ypos = min(y)*30.
    plt.text ( max(x)+.30*(max(x)-min(x)), ypos, "$f$ = $\sigma_{95}$ (%s) / $\sigma_{95}$ (%s)" % ( a1, a2 ), fontsize=13, rotation = 90)
    print ( "[plotRatio] Saving to %s" % figname )
    if hasLegend:
        plt.legend()
    plt.savefig ( figname )
    if copy:
      cmd="cp %s ../../smodels.github.io/ratioplots/" % ( figname )
      print ( cmd )
      subprocess.getoutput ( cmd )
    print ( "[plotRatio] ratio=%.2f +/- %.2f" % ( numpy.nanmean(col), numpy.nanstd(col) ) )
    plt.clf()

def getModuleFromPath ( ipath, analysis ):
    try:
        spec = importlib.util.spec_from_file_location( "validationData", ipath )
        imp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imp)
        imp.ana = analysis
    except Exception as e:
        print ( "Could not import validation file 1: %s" % e )
    return imp

def getModule ( dbpath, analysis, validationfile ):
    """ get the python module from the path to database, analysis name,
        name of validation file (with globs) """
    ipath = getPathName ( dbpath, analysis, validationfile )
    imp = getModuleFromPath ( ipath, analysis )
    return imp

def writeMDPage( copy ):
    """ write the markdown page that lists all plots """ 
    with open("ratioplots.md","wt") as f:
        f.write ( "# ratio plots on the upper limits, andre / suchi \n" )
        f.write ( "as of %s\n" % time.asctime() )
        f.write ( "see also [best signal regions](bestSRs)\n\n" )
        f.write ( "| ratio plots | ratio plots |\n" )
        files = glob.glob("ratio_*.png" )
        files += glob.glob("atlas_*png" )
        files += glob.glob("cms_*png" )
        files.sort()
        ctr = 0
        for ctr,i in enumerate( files ):
            src = "https://smodels.github.io/ratioplots/%s" % i
            f.write ( '| <img src="%s" /> ' % src )
            if ctr % 2 == 1:
                f.write ( "|\n" )
        if ctr % 2 == 0:
            f.write ( " | |\n" )
        f.close()
    if copy:
        cmd = "cp ratioplots.md ../../smodels.github.io/ratioplots/README.md" 
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
            help="first analysis name, like the directory name [CMS-EXO-13-006-andre]",
            type=str, default="CMS-EXO-13-006-andre" )
    argparser.add_argument ( "-a2", "--analysis2",
            help="second analysis name, like the directory name [CMS-EXO-13-006-eff]",
            type=str, default="CMS-EXO-13-006-eff" )
    argparser.add_argument ( "-l1", "--label1",
            help="label in the legend for analysis1 [andre]",
            type=str, default="andre" )
    argparser.add_argument ( "-o", "--output",
            help="outputfile [None]",
            type=str, default=None )
    argparser.add_argument ( "-l2", "--label2",
            help="label in the legend for analysis2 [suchi]",
            type=str, default="suchi" )
    argparser.add_argument ( "-d", "--dbpath", help="path to database [../../smodels-database/]", type=str,
                             default="../../smodels-database/" )
    argparser.add_argument ( "-D", "--default", action="store_true",
            help="default run on arguments. currently set to be the exo 13 006 plots" )
    argparser.add_argument ( "-c", "--copy", action="store_true",
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/combination/" )
    argparser.add_argument ( "-p", "--push", action="store_true", 
            help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/ratioplots/" )
    args = argparser.parse_args()

    valfiles = [ args.validationfile1 ]
    if args.default:
        valfiles = [ "THSCPM3_2EqMassAx_EqMassBy**.py", "THSCPM4_*.py", "THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py", "THSCPM6_EqMassA__EqmassAx_EqmassBx-100_Eqma*.py", "THSCPM8_2EqMassAx*.py", "THSCPM1b_*.py", "THSCPM2b_*.py" ]
    for valfile1 in valfiles:
        valfile2 = args.validationfile2
        if valfile2 in [ "", "none", "None", None ]:
            valfile2 = valfile1
        imp1 = getModule ( args.dbpath, args.analysis1, valfile1 )
        imp2 = getModule ( args.dbpath, args.analysis2, valfile2 )

        draw ( imp1, imp2, args.copy, args.label1, args.label2, args.dbpath, args.output )

    writeMDPage( args.copy )

    cmd = "cd ../../smodels.github.io/; git commit -am 'automated commit'; git push"
    o = ""
    if args.push:
        print ( "[plotRatio] now performing %s: %s" % (cmd, o ) )
        o = subprocess.getoutput ( cmd )
    else:
        print ( "[plotRatio] now you could do:\n%s: %s" % (cmd, o ) )

main()
