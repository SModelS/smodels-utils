#!/usr/bin/env python3

""" Plot the ratio between the upper limit from the UL map, and our
own upper limit computed from combining the efficiency maps. """

import math, os, numpy, copy, sys, glob
import matplotlib.pyplot as plt
import ROOT
import logging
import subprocess
from scipy.interpolate import griddata
import itertools
import importlib
import setPath
from smodels_utils.helper import prettyDescriptions
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

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
    argparser.add_argument ( "-d", "--dbpath", help="path to database [../../smodels-database/]", type=str,
                             default="../../smodels-database/" )
    argparser.add_argument ( "-c", "--copy", action="store_true", 
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/combination/" )
    args = argparser.parse_args()
    analysis1, valfile1 = args.analysis1, args.validationfile1
    analysis2, valfile2 = args.analysis2, args.validationfile2
    if valfile2 in [ "", "none", "None", None ]:
        valfile2 = valfile1
    if not valfile1.endswith(".py"): valfile1 += ".py"
    if not valfile2.endswith(".py"): valfile2 += ".py"
    s_ana1 = analysis1
    s_ana1 = s_ana1.replace("agg"," (agg)" )
    experiment1 = "ATLAS"
    if "CMS" in analysis1:
        experiment1 = "CMS"
    experiment2 = "ATLAS"
    if "CMS" in analysis2:
        experiment2 = "CMS"
    sqrts1 = 8
    for sqrts1 in [ 8, 13, 14, -1 ]:
        anadir = "%s%dTeV/%s/%s" % ( args.dbpath, sqrts1, experiment1, analysis1 )
        if os.path.exists ( anadir ):
            break
    if sqrts1 == -1:
        print ( "could not find analysis %s. Did you forget e.g. '-eff' at the end?" % analysis1 )
        sys.exit()
    sqrts2 = 8
    s_ana2 = analysis2
    s_ana2 = s_ana2.replace("agg"," (agg)" )
    for sqrts2 in [ 8, 13, 14, -1 ]:
        anadir = "%s%dTeV/%s/%s" % ( args.dbpath, sqrts2, experiment2, analysis2 )
        if os.path.exists ( anadir ):
            break
    if sqrts2 == -1:
        print ( "could not find analysis %s. Did you forget e.g. '-eff' at the end?" % analysis2 )
        sys.exit()
    try:
        ipath = "%s%dTeV/%s/%s/validation/%s" % \
                 ( args.dbpath, sqrts1, experiment1, analysis1, valfile1 )
        files = glob.glob ( ipath )
        if len(files)==0:
            print ( "could not find validation file %s" % ipath )
            sys.exit()
        if len(files)>1:
            print ( "[plotRatio] globbing %s resulted in %d files. please specify." % ( ipath, len(files) ) )
            sys.exit()
        ipath = files[0]
        spec = importlib.util.spec_from_file_location( "validationData", ipath )
        imp1 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imp1)
    except Exception as e:
        print ( "Could not import validation file 1: %s" % e )
    try:
        ipath = "%s%dTeV/%s/%s/validation/%s" % \
                 ( args.dbpath, sqrts2, experiment2, analysis2, valfile2 )
        files = glob.glob ( ipath )
        if len(files)==0:
            print ( "could not find validation file %s" % ipath )
            sys.exit()
        if len(files)>1:
            print ( "[plotRatio] globbing %s resulted in %d files. specify." % ( ipath, len(files) ) )
            sys.exit()
        ipath = files[0]
        spec = importlib.util.spec_from_file_location( "validationData", ipath )
        imp2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imp2)
    except Exception as e:
        print ( "Could not import validation file 2: %s" % e )
    uls={}
    nsr=""

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

    noaxes = 0
    for point in imp1.validationData:
        if not "axes" in point:
            noaxes+=1
            if noaxes < 5:
                print ( "no axes in", imp1.__file__, ",", point["slhafile"] )
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
        if ul1 and "UL" in point:
            ul2 = point["UL"] / point["signal"] ##  point["efficiency"]
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
    yx = numpy.array(list(itertools.product(y_,x_)) )
    x = yx[::,1]
    y = yx[::,0]
    col = griddata ( points[::,0:2], points[::,2], yx )
    # print ( "col=", col )

    if err_msgs > 0:
        print ( "[plotRatio] couldnt find data for %d/%d points" % (err_msgs, len( imp2.validationData ) ) )

    cm = plt.cm.get_cmap('jet')
    plt.rc('text', usetex=True)
    vmax = 1.5
    vmax = 50.
    scatter = plt.scatter ( x, y, s=0.25, c=col, marker="o", cmap=cm, 
                            vmin=0.5, vmax=vmax )
    ax = plt.gca()
    ax.set_xticklabels(map(int,ax.get_xticks()), { "fontweight": "normal", "fontsize": 14 } )
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
    
    plt.title ( "ratio $f$: %s, %s" % ( s_ana1.replace("-andre",""), stopo) )
    plt.xlabel ( "m$_{mother}$ [GeV]", fontsize=13 )
    plt.rc('text', usetex=True)
    label = "m$_{LSP}$ [GeV]"
    if "052" in analysis:
      # label = "$\Delta m$(mother, daughter) [GeV]"
      label = "m$_{mother}$ - m$_{daughter}$ [GeV]"
    plt.ylabel ( label, fontsize=13 )

    plt.colorbar()
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
    figname = "%s_%s.png" % ( analysis, topo )
    #if srs1 !="all":
    #    figname = "%s_%s_%s.png" % ( analysis, topo, srs )
    a1, a2 = "$a_1$", "$a_2$"
    for ide,label in { "andre": "andre", "eff": "suchi" }.items():
        if ide in s_ana1:
            a1 = label
        if ide in s_ana2:
            a2 = label
    plt.text ( max(x)+.30*(max(x)-min(x)), .2*max(y), "$f$ = $\sigma_{95}$ (%s) / $\sigma_{95}$ (%s)" % ( a1, a2 ), fontsize=13, rotation = 90)
    print ( "[plotRatio] Saving to %s" % figname )
    if hasLegend:
        plt.legend()
    plt.savefig ( figname )
    if args.copy:
      cmd="cp %s ../../smodels.github.io/ratioplots/" % ( figname )
      print ( cmd )
      subprocess.getoutput ( cmd )
    print ( "[plotRatio] ratio=%.2f +/- %.2f" % ( numpy.nanmean(col), numpy.nanstd(col) ) )

main()
