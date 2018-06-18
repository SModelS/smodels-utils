#!/usr/bin/env python3

""" Plot the ratio between the upper limit from the UL map, and our
own upper limit computed from combining the efficiency maps. """

import math, os, numpy, copy, sys
import matplotlib.pyplot as plt
import ROOT
import logging

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

def getExclusionLine ( rootpath, txname, axes=None ):
    line = getExclusionsFrom ( rootpath, txname, axes )
    x,y=ROOT.Double(),ROOT.Double()
    x_v,y_v=[],[]
    for i in range(line.GetN()):
      line.GetPoint(i,x,y)
      x_v.append(copy.deepcopy(x))
      y_v.append(copy.deepcopy(y))
    return x_v, y_v

def main():
    import argparse
    argparser = argparse.ArgumentParser( description = "ratio plot" )
    argparser.add_argument ( "-t", "--topo", help="topology", type=str,
                             default="T4bbffff" )
    argparser.add_argument ( "-a", "--analysis", help="analysis", type=str,
                             default="CMS16052" )
    argparser.add_argument ( "-s", "--sr", help="signal regions", type=str,
                             default="all" )
    args = argparser.parse_args()
    analysis, topo, srs = args.analysis, args.topo, args.sr
    # analysis, topo, srs = "CMS16050", "T2tt", "all"
    FromUl = __import__ ( "%s.%s_ul" % ( analysis, topo), fromlist="%s_ul" % topo )
    FromEff = __import__ ( "%s.%s_%s" % ( analysis, topo, srs ),
                           fromlist="%s_%s" % ( topo, srs ) )
    uls={}


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


    x,y,col=[],[],[]

    for point in FromEff.validationData:
        axes = convertNewAxes ( point["axes"] )
        h = axisHash ( axes )
        ul = None
        if h in uls.keys():
            ul = uls[h]
        # print "ul", axes, point["UL"], point["UL"] / point["efficiency"], ul
        if ul:
            ul_eff = point["UL"] / point["signal"] ##  point["efficiency"]
            ratio = ul_eff / ul
            # ratio = math.log10 ( ul )
            x.append ( axes[1] )
            y.append ( axes[0] )
            col.append ( ratio )

    # cm = plt.cm.get_cmap('RdYlBu')
    cm = plt.cm.get_cmap('RdYlGn')
    scatter = plt.scatter ( x, y, c=col, cmap=cm, vmin=0.5, vmax=1.5 )
    plt.rc('text', usetex=True)
    slhafile=FromEff.validationData[0]["slhafile"]
    Dir=os.path.dirname ( FromEff.__file__ )
    analysis=Dir[ Dir.rfind("/")+1: ]
    topo=slhafile[:slhafile.find("_")]

    x_v,y_v = getExclusionLine ( "%s/sms.root" % analysis, topo )

    plt.title ( "Ratio UL(SModelS) / UL(official), %s, %s" % ( analysis, topo) )
    plt.xlabel ( "m$_{mother}$ [GeV]" )
    label = "m$_{LSP}$ [GeV]"
    if "052" in analysis:
      label = "$\Delta m$(mother, daughter) [GeV]"
    plt.ylabel ( label )
      
    plt.colorbar()
    #print ( "x_v=", x_v )
    #print ( "y_v=", y_v )
    plt.plot ( x_v, y_v, color='k', linestyle='-', linewidth=2 )
    plt.savefig ( "%s_%s.png" % ( analysis, topo ) )

    print ( "ratio=%s +/- %s" % ( numpy.mean(col), numpy.std(col) ) )
    # plt.show()

main()
