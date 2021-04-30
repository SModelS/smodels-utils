#!/usr/bin/env python3

""" Plot the ratio between the upper limit from the UL map, and our
own upper limit computed from combining the efficiency maps. """

import math, os, numpy, copy, sys, glob, ctypes
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

errMsgIssued = { "axis": False }

def hasDebPkg():
    """ do we have the package installed """
    a = subprocess.getoutput ( "dpkg -l cm-super-minimal | tail -n 1" )
    if a.startswith("ii"):
        return True
    print ( "error, you need cm-super-minimal installed! (apt install cm-super-minimal)" )
    sys.exit(-1)

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
    if not errMsgIssued["axis"]:
        print ( "[plotRatio] cannot convert axis '%s'" % newa )
        errMsgIssued["axis"]=True
    return None

def axisHash ( axes_ ):
    ret = 0
    axes = convertNewAxes ( axes_ )
    for ctr,a in enumerate(axes):
        ret += 10**(4*ctr)*int(a)
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
    # x,y=ROOT.Double(),ROOT.Double()
    x,y= ctypes.c_double(),ctypes.c_double()
    x_v,y_v=[],[]
    for i in range(line.GetN()):
      line.GetPoint(i,x,y)
      #x_v.append(copy.deepcopy(x.value))
      #y_v.append(copy.deepcopy(y.value))
      x_v.append( x.value )
      y_v.append( y.value )
    return [ { "x": x_v, "y": y_v } ]

def draw ( imp1, imp2, copy, label1, label2, dbpath, output, vmin, vmax ):
    """ plot.
    :params vmin: the minimum z value, e.g. .5
    :params vmax: the maximum z value, e.g. .5
    """
    hasDebPkg()
    uls={}
    nsr=""
    noaxes = 0
    for ctr,point in enumerate(imp1.validationData):
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
        if axes_ is None:
            continue
            #print ( f"[plotRatio] the axis field is 'None' in {imp1.__file__}. Will stop." )
            #sys.exit()
        axes = convertNewAxes ( axes_ )
        h = axisHash ( axes )
        if not "UL" in point:
            continue
        if point["axes"]["x"]<point["axes"]["y"]:
            print ( "axes", axes_, "list", axes, "hash", h, "ul", point["UL"], "sig", point["signal"] )
        uls[ h ] = point["UL" ] / point["signal"]

    err_msgs = 0

    ipoints = imp2.validationData
    points = []

    for ctr,point in enumerate(ipoints):
        axes = convertNewAxes ( point["axes"] )
        if axes == None:
            continue
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

    if len(points) == 0:
        print ( f"[plotRatio] found no legit points but {err_msgs} err msgs in {imp2.__file__}" )
        sys.exit()

    points.sort()
    points = numpy.array ( points )
    x = points[::,1].tolist()
    y = points[::,0].tolist()
    # coll = points[::,2].tolist()
    minx, maxx = min(x), max(x)
    miny, maxy = min(y), max(y)
    nx, ny = 250, 250
    x_ = numpy.arange ( minx, maxx, ( maxx-minx) / nx )
    y_ = numpy.arange ( miny, maxy, ( maxy-miny) / ny )
    logScale = False
    if False: # max(y) < 1e-10 and min(y) > 1e-40:
        logScale = True
        y_ = numpy.logspace ( numpy.log10(.3*min(y)), numpy.log10(3.*max(y)), ny )
    yx = numpy.array(list(itertools.product(y_,x_)) )
    x = yx[::,1]
    y = yx[::,0]
    col = griddata ( points[::,0:2], points[::,2], yx, rescale=True )
    for i in range(len(x)):
        if abs(x[i]-200.) < 10. and abs(y[i]-400.)< 20.:
            print ( "pt", x[i], y[i], yx[i] )

    if err_msgs > 0:
        print ( "[plotRatio] couldnt find data for %d/%d points" % (err_msgs, len( imp2.validationData ) ) )

    cm = plt.cm.get_cmap('jet')
    plt.rc('text', usetex=True)
    # vmin,vmax= .5, 1.7
    if vmax is None or abs(vmax)<1e-5:
        vmax = numpy.nanmax ( col )*1.1
    if vmin is None or abs(vmin)<1e-5:
        vmin = numpy.nanmin ( col )*0.9
    opts = { }
    #print ( "vmax", vmax )
    #if logScale:
    #    vmin = 1e-5
    #    vmax = 0.5
    if vmax > 5.:
        opts = { "norm": matplotlib.colors.LogNorm()  }
        
    scatter = plt.scatter ( x, y, s=0.35, c=col, marker="o", cmap=cm,
                            vmin=vmin, vmax=vmax, **opts )
    ax = plt.gca()
    plt.ylabel ( "$\Gamma$ [GeV]", size=13 )
    plt.xlabel ( "m [GeV]", size=13 )
    if logScale:
        ax.set_yscale("log")
        ax.set_ylim ( min(y)*.2, max(y)*5. )
    #ax.set_xticklabels(map(int,ax.get_xticks()), { "fontweight": "normal", "fontsize": 14 } )
    #if not logScale:
    #    ax.set_yticklabels(map(int,ax.get_yticks()), { "fontweight": "normal", "fontsize": 14 } )
    plt.rcParams.update({'font.size': 14})
    #plt.rcParams['xtick.labelsize'] = 14
    #plt.rcParams['ytick.labelsize'] = 14
    slhafile=imp2.validationData[0]["slhafile"]
    Dir=os.path.dirname ( imp1.__file__ )
    Dir2=os.path.dirname ( imp2.__file__ )
    smsrootfile = Dir.replace("validation","sms.root" )
    smsrootfile2 = Dir2.replace("validation","sms.root" )
    analysis=Dir[ Dir.rfind("/")+1: ]
    topo=slhafile[:slhafile.find("_")]
    # print ( "smsrootfile", smsrootfile )
    stopo = prettyDescriptions.prettyTxname ( topo, outputtype="latex" ).replace("*","^{*}" )

    isEff = False
    if "-eff" in imp1.ana or "-eff" in mp2.ana:
        isEff = True
    anaId = imp1.ana.replace("-andre","")
    anaId = anaId.replace("-orig","").replace("-old","").replace("-eff","")
    anaId2 = imp2.ana.replace("-andre","")
    anaId2 = anaId2.replace("-orig","").replace("-old","").replace("-eff","")
    title = "%s: $\\frac{\\mathrm{%s}}{\\mathrm{%s}}$" % ( topo, anaId, anaId2 )
    if anaId2 == anaId:
        title = "ratio: %s, %s" % ( anaId, topo )
    plt.title ( title )
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
    line2 = getExclusionsFrom ( smsrootfile2, topo )
    if line is not False:
        el = getExclusionLine ( line )
    if line2 is not False:
        el2 = getExclusionLine ( line2 )
    label = "official exclusion"
    label = anaId
    for E in el:
        hasLegend = True
        plt.plot ( E["x"], E["y"], color='white', linestyle='-', linewidth=4, label="" )
        plt.plot ( E["x"], E["y"], color='k', linestyle='-', linewidth=3, label=label )
        label = ""
    for E in el2:
        label = anaId2
        hasLegend = True
        plt.plot ( E["x"], E["y"], color='white', linestyle='-', linewidth=4, label="" )
        plt.plot ( E["x"], E["y"], color='darkred', linestyle='-', linewidth=3, label=label )
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
        figname = output.replace("@t", topo ).replace("@a1", anaId ).replace("@a2", anaId2 )
        figname = figname.replace( "@a",anaId )
        repeff = ""
        if isEff:
            repeff = "-eff"
        figname = figname.replace("@e",repeff)
    a1, a2 = label1, label2
    ypos = .2*max(y)
    if logScale:
        ypos = min(y)*30.
    plt.text ( max(x)+.30*(max(x)-min(x)), ypos, 
               "$f$ = $\sigma_{95}$ (%s) / $\sigma_{95}$ (%s)" % ( a1, a2 ), 
               fontsize=13, rotation = 90)
    print ( "[plotRatio] Saving to %s" % figname )
    if hasLegend:
        plt.legend()
    plt.savefig ( figname )
    if copy:
      cmd="cp %s ../../smodels.github.io/ratioplots/" % ( figname )
      print ( "plotRatio] %s" % cmd )
      subprocess.getoutput ( cmd )
    rmean,rstd =  numpy.nanmean(col), numpy.nanstd(col)
    with open ( "ratios.txt", "at") as f:
        f.write ( "%s %.2f +/- %.2f\n" % ( figname, rmean, rstd ) )
    print ( "[plotRatio] ratio=%.2f +/- %.2f" % ( rmean, rstd ) )
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
        # f.write ( "# ratio plots on the upper limits, andre / suchi \n" )
        f.write ( "# ratio plots on the upper limits\n" )
        f.write ( "as of %s\n" % time.asctime() )
        f.write ( "see also [best signal regions](bestSRs)\n\n" )
        f.write ( "| ratio plots | ratio plots |\n" )
        files = glob.glob("ratio_*.png" )
        files = glob.glob("ratios_*.png" )
        files += glob.glob("atlas_*png" )
        files += glob.glob("cms_*png" )
        files.sort()
        ctr = 0
        t0=time.time()-1592000000
        for ctr,i in enumerate( files ):
            src = "https://smodels.github.io/ratioplots/%s" % i
            f.write ( '| <img src="%s?%d" /> ' % ( src, t0 ) )
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
            help="first analysis name, like the directory name [ATLAS-SUSY-2013-09]",
            type=str, default="ATLAS-SUSY-2013-09" )
    argparser.add_argument ( "-a2", "--analysis2",
            help="second analysis name, like the directory name [ATLAS-CONF-2013-007]",
            type=str, default="ATLAS-CONF-2013-007" )
    argparser.add_argument ( "-l1", "--label1",
            help="label in the legend for analysis1 [susy]",
            type=str, default="susy" )
    argparser.add_argument ( "-o", "--output",
            help="outputfile [ratios_@t_@a.png]",
            type=str, default="ratios_@t_@a@e.png" )
    argparser.add_argument ( "-l2", "--label2",
            help="label in the legend for analysis2 [conf]",
            type=str, default="conf" )
    argparser.add_argument ( "-z", "--zmin",
            help="minimum z value, 0. means auto [.5]",
            type=float, default=.5 )
    argparser.add_argument ( "-Z", "--zmax",
            help="maximum Z value, 0. means auto [1.7]",
            type=float, default=1.7 )
    argparser.add_argument ( "-d", "--dbpath", 
            help="path to database [../../smodels-database/]", type=str,
            default="../../smodels-database/" )
    argparser.add_argument ( "-D", "--default", action="store_true",
            help="default run on arguments. currently set to be the exo 13 006 plots" )
    argparser.add_argument ( "-c", "--copy", action="store_true",
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/combination/" )
    argparser.add_argument ( "-p", "--push", action="store_true", 
            help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/ratioplots/" )
    args = argparser.parse_args()
    if not args.validationfile1.endswith ( ".py" ):
        args.validationfile1 += ".py"

    valfiles = [ args.validationfile1 ]
    if args.default:
        valfiles = [ "THSCPM3_2EqMassAx_EqMassBy**.py", "THSCPM4_*.py", "THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py", "THSCPM6_EqMassA__EqmassAx_EqmassBx-100_Eqma*.py", "THSCPM8_2EqMassAx*.py", "THSCPM1b_*.py", "THSCPM2b_*.py" ]
    for valfile1 in valfiles:
        valfile2 = args.validationfile2
        if valfile2 in [ "", "none", "None", None ]:
            valfile2 = valfile1
        imp1 = getModule ( args.dbpath, args.analysis1, valfile1 )
        imp2 = getModule ( args.dbpath, args.analysis2, valfile2 )

        draw ( imp1, imp2, args.copy, args.label1, args.label2, args.dbpath, args.output,
               args.zmin, args.zmax )

    writeMDPage( args.copy )

    cmd = "cd ../../smodels.github.io/; git commit -am 'automated commit'; git push"
    o = ""
    if args.push:
        print ( "[plotRatio] now performing %s: %s" % (cmd, o ) )
        o = subprocess.getoutput ( cmd )
    else:
        if args.copy:
            print ( "[plotRatio] now you could do:\n%s: %s" % (cmd, o ) )

main()
