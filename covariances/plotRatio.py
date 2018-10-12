#!/usr/bin/env python3

""" Plot the ratio between the upper limit from the UL map, and our
own upper limit computed from combining the efficiency maps. """

import math, os, numpy, copy, sys
import matplotlib.pyplot as plt
import ROOT
import logging
import subprocess
from scipy.interpolate import griddata
import itertools

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
        logger.warning("Exclusion curve for %s not found in %s" %(txname,rootpath))
        sys.exit()
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
    argparser.add_argument ( "-t", "--topo", help="topology [T2tt]", type=str,
                             default="T2tt" )
    argparser.add_argument ( "-a", "--analysis", help="analysis [CMS16050]", type=str,
                             default="CMS16050" )
    argparser.add_argument ( "-s", "--sr", help="signal regions [all]", type=str,
                             default="all" )
    argparser.add_argument ( "-c", "--copy", action="store_true", 
            help="scp to smodels server, as it appears in http://smodels.hephy.at/wiki/CombinationComparisons" )
    args = argparser.parse_args()
    analysis, topo, srs = args.analysis, args.topo, args.sr
    # analysis, topo, srs = "CMS16050", "T2tt", "all"
    FromUl = __import__ ( "%s.%s_ul" % ( analysis, topo), fromlist="%s_ul" % topo )
    FromEff = __import__ ( "%s.%s_%s" % ( analysis, topo, srs ),
                           fromlist="%s_%s" % ( topo, srs ) )
    uls={}
    nsr=""
    try:
        t = __import__ ( "%s" % ( analysis ) ).nSRs
        if t == "best": 
            nsr = t
        else:
            nsr = "%s SRs" % ( t )
    except Exception as e:
        print ( str(e) )

    if srs != "all":
        nsr=srs

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

    for point in FromUl.validationData:
        axes_ = point["axes"]
        axes = convertNewAxes ( axes_ )
        h = axisHash ( axes )
        uls[ h ] = point["UL" ] / point["signal"]


    err_msgs = 0

    ipoints = FromEff.validationData
    points = []

    for point in ipoints:
        axes = convertNewAxes ( point["axes"] )
        h = axisHash ( axes )
        ul = None
        if h in uls.keys():
            ul = uls[h]
        if ul:
            ul_eff = point["UL"] / point["signal"] ##  point["efficiency"]
            # ratio = ul_eff / ul
            ratio = ul / ul_eff
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
    x_ = numpy.arange ( min(x), max(x), 3. )
    y_ = numpy.arange ( min(y), max(y), .05 )
    yx = numpy.array(list(itertools.product(y_,x_)) )
    x = yx[::,1]
    y = yx[::,0]
    col = griddata ( points[::,0:2], points[::,2], yx )
    print ( "col=", col )

    if err_msgs > 0:
        print ( "couldnt find data for %d/%d points" % (err_msgs, len( FromEff.validationData ) ) )

    cm = plt.cm.get_cmap('jet')
    # cm = plt.cm.get_cmap('RdYlGn')
    # scatter = plt.contourf( x, y, col, cmap=cm, vmin=0.5, vmax=1.5, gridsize=30, bins=None )
    # scatter = plt.hexbin( x, y, C=col, cmap=cm, vmin=0.5, vmax=1.5, gridsize=80, bins=None )
    scatter = plt.scatter ( x, y, s=0.25, c=col, marker="s", cmap=cm, vmin=0.5, vmax=1.5 )
    plt.rc('text', usetex=True)
    slhafile=FromEff.validationData[0]["slhafile"]
    Dir=os.path.dirname ( FromEff.__file__ )
    analysis=Dir[ Dir.rfind("/")+1: ]
    topo=slhafile[:slhafile.find("_")]
    line = getExclusionsFrom ( "%s/sms.root" % analysis, topo )


    s_ana = analysis
    s_ana = s_ana.replace("agg"," (agg)" )
    plt.title ( "UL(official) / UL(SModelS), %s, %s" % ( s_ana, topo) )
    # plt.title ( "Ratio UL(SModelS) / UL(official), %s, %s" % ( analysis, topo) )
    plt.xlabel ( "m$_{mother}$ [GeV]" )
    label = "m$_{LSP}$ [GeV]"
    if "052" in analysis:
      label = "$\Delta m$(mother, daughter) [GeV]"
    plt.ylabel ( label )

    plt.colorbar()
    el = getExclusionLine ( line )
    label = "official exclusion"
    for E in el:
        plt.plot ( E["x"], E["y"], color='k', linestyle='-', linewidth=4, label=label )
        label = ""
    smodels_root = "%s/%s.root" % ( analysis, topo ) 
    smodels_line = getSModelSExclusion ( smodels_root )
    el2 = getExclusionLine ( smodels_line )
    print ( "Found SModelS exclusion line with %d points." % ( len(el2) ) )
    label="SModelS exclsuion"
    for E in el2:
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
        # plt.text ( .98*max(x_v), 1.0*min(y_v)-.27*(max(y_v)-min(y_v)), "%s" % ( nsr) , fontsize=12 )
        plt.text ( .97*maxx, miny-.17*(maxy-miny), "%s" % ( nsr) , fontsize=12 )
    figname = "%s_%s.png" % ( analysis, topo )
    if srs !="all":
        figname = "%s_%s_%s.png" % ( analysis, topo, srs )
    plt.text ( max(x)+.30*(max(x)-min(x)), .7*max(y), "f$_{UL}$: %.2f +/- %.2f" % ( numpy.nanmean(col), numpy.nanstd(col)  ), fontsize=11, rotation = 90)
    # plt.text ( min(x)+.70*(max(x)-min(x)), max(y), "f$_{UL}$: %.2f +/- %.2f" % ( numpy.mean(col), numpy.std(col)  ), fontsize=11)
    print ( "Saving to %s" % figname )
    plt.legend()
    plt.savefig ( figname )
    if args.copy:
      cmd="scp %s smodels.hephy.at:/var/www/images/combination/" % ( figname )
      print ( cmd )
      subprocess.getoutput ( cmd )
    print ( "ratio=%.2f +/- %.2f" % ( numpy.nanmean(col), numpy.nanstd(col) ) )
    # plt.show()

main()
