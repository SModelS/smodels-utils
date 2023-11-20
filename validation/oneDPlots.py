#!/usr/bin/env python3

"""
.. module:: oneDPlots
   :synopsis: Main method for creating 1d plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,numpy,random,copy
sys.path.append('../')
from array import array
import math, ctypes
logger = logging.getLogger(__name__)
from smodels.tools.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxes
from plottingFuncs import getGridPoints, yIsLog, getFigureUrl, \
                          getDatasetDescription, getAxisRange, isWithinRange


try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass

def getMinGap ( xs ):
    """ determine smallest gap in values """
    if len(xs)==1:
        return 0.
    dx_ = []
    for i in range(len(xs)-1):
        d = xs[i+1]-xs[i]
        if d > 0.:
            dx_.append ( d )
    return min ( dx_ )

def ceilY ( y ):
    """ put a ceiling to y values, above which we declare them as nan """
    if y > 8.:
        return float("nan")
    return y

def plot ( xvalues, yvalues, color, marker, label : str = "", linestyle: str = ":"):
    """ plotting routine so we can split up
    """
    if len(xvalues)==0:
        return
    dxmax = getMinGap ( xvalues )
    from smodels_utils.plotting import mpkitty as plt
    chunks = []
    chunk = { "x": [ xvalues[0] ], "y": [ ceilY ( yvalues[0] ) ] }
    for i in range(len(xvalues)-1):
        dx_ = xvalues[i+1]-xvalues[i]
        if dx_ < dxmax*2.1:
            chunk["x"].append ( xvalues[i+1] )
            chunk["y"].append ( ceilY ( yvalues[i+1] ) )
        else:
            if len(chunk)>0:
                chunks.append ( chunk )
                chunk = { "x": [ xvalues[i+1] ], "y": [ ceilY ( yvalues[i+1] ) ] }
    chunk["x"].append ( xvalues[-1] )
    chunk["y"].append ( ceilY ( yvalues[-1] ) )
    chunks.append ( chunk )
    for chunk in chunks:
        plt.plot ( chunk["x"], chunk["y"], c=color, marker=marker, \
                   label=label, linestyle=linestyle )
        label = ""

def create1DPlot( validationPlot, silentMode=True,
        looseness = 1.2, options : dict = {} ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate the "1d" exclusion plot

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :return: TCanvas object containing the plot
    """
    inverse = False
    if "plotInverse" in options and options["plotInverse"]==True:
        inverse = True
    xrange = getAxisRange ( options, "xaxis" )
    logger.error ( "now create 1d plot for %s, %s: %s" % \
       ( validationPlot.expRes.globalInfo.id, validationPlot.txName,
         validationPlot.axes ) )

    if not validationPlot.data:
        logger.error("Data for validation plot is not defined.")
        return (None,None)

    dn = 50
    nmax = len(validationPlot.data)
    from smodels_utils.plotting import mpkitty as plt
    plt.dontplot = False
    fig, ax = plt.subplots()

    xvs, yvs = [], []
    values = { "excluded": { "x": [], "y": [], "ex": [], "ey": [] } }
    values["allowed"]= { "x": [], "y": [],"ex": [],  "ey": [] }
    values["error"]= { "x": [], "y": [],"ex": [],  "ey": [] }
    values["excluded_border"]= { "x": [], "y": [],"ex": [],  "ey": [] }
    values["allowed_border"]= { "x": [], "y": [],"ex": [],  "ey": [] }
    kfactor = None
    for ctPoints,pt in enumerate(validationPlot.data):
        if ctPoints % dn == 0:
            print ( ".", end="", flush=True )
        if ctPoints == nmax:
            logger.error ( "emergency break" )
            break
        if "kfactor" in pt:
            kfactor = pt["kfactor"]
            if kfactor != None and pt["kfactor"]!=kfactor:
                logger.warn ( f"k-factor changed from one point {kfactor} to the other {pt['kfactor']}" )
        if "axes" in pt and pt["axes"] is not None and "x" in pt["axes"]:
            axes = pt["axes"]
            x = axes["x"]
            numericalA = None
            fulFillsNumericals = True
            for k,v in axes.items():
                try:
                    numericalA = float(k)
                    fulFillsNumericals = (numericalA == v)
                    if not fulFillsNumericals:
                        break
                except ValueError as e:
                    pass
            if not fulFillsNumericals:
                continue
            if not isWithinRange (xrange, x ):
                continue
            y, ey = float ( "nan" ), float ( "nan" )
            if "signal" in pt and "UL" in pt:
                y = pt["signal"] / pt["UL"]
                if "eUL" in pt:
                    if type(pt["eUL"])==str:
                        pt["eUL"]=eval(pt["eUL"])
                    ey = pt["signal"] / pt["eUL"]
            label = "error"
            values[label]["x"].append(x)
            values[label]["y"].append(y)
            values[label]["ex"].append(x)
            values[label]["ey"].append(ey)
            if math.isfinite ( y ):
                yvs.append ( y )
                xvs.append ( x )
            label = "excluded"
            if 1.1 < y < float("inf"):
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if 1.1 < ey < float("inf"):
                values[label]["ex"].append(x)
                values[label]["ey"].append(ey)
            label = "excluded_border"
            if 0.8 < y < 1.3:
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if 0.8 < ey < 1.3:
                values[label]["ex"].append(x)
                values[label]["ey"].append(ey)
            label = "allowed_border"
            if .3 < y < 1:
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if .3 < ey < 1:
                values[label]["ex"].append(x)
                values[label]["ey"].append(ey)
            label = "allowed"
            if y < 0.7:
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if ey < 0.7:
                values[label]["ex"].append(x)
                values[label]["ey"].append(ey)
    ylabel = r"r = $\sigma_\mathrm{signal}$ / $\sigma_\mathrm{UL}$"
    if inverse:
        ylabel = r"$\mathrm{UL}_\mu$"
    plt.ylabel ( ylabel )
    plt.xlabel ( r"m(mother) [GeV]", labelpad=-1., loc="right" )
    colors = { "excluded": "r",
               "excluded_border": "orange",
               "allowed_border": "g",
               "allowed": "lightgreen",
    }
    for label in [ "excluded", "excluded_border", "allowed_border", "allowed" ]:
        c = colors[label]
        lbl = None
        if label == "excluded":
            lbl = "SModelS excluded"
        if label == "excluded_border":
            lbl = "SModelS excluded (but close)"
        if label == "allowed":
            lbl = "SModelS allowed"
        if label == "allowed_border":
            lbl = "SModelS allowed (but close)"
        linestyle = "-"
        #if c != "r":
        #    linestyle = ""
        xs, ys = values[label]["x"], values[label]["y"]
        if inverse:
            ys = [ 1./y for y in ys ]
            for i,e in enumerate ( values[label]["ey"] ):
                values[label]["ey"][i]=1./e
        plot ( xs, ys, color=c, marker="o", label=lbl, linestyle=linestyle )
        #if len(values[label]["ey"]) == len(values[label]["ex"]):
        if linestyle != "":
            linestyle = ":"
        plot ( values[label]["ex"], values[label]["ey"], color=c,
                linestyle=linestyle, marker="." )
    pName = prettyTxname(validationPlot.txName, outputtype="latex" )
    pAxis = prettyAxes(validationPlot.txName, validationPlot.axes, outputtype="latex" )
    title = f"{validationPlot.expRes.globalInfo.id}: {pName} \n {pAxis}"
#       ( validationPlot.expRes.globalInfo.id, validationPlot.txName,
#         validationPlot.axes ) )
    plt.title ( title )
    official = validationPlot.officialCurves
    eofficial = validationPlot.expectedOfficialCurves
    rmin, rmax = 0, 1
    for o in official:
        if o["name"].startswith ( "obsExclusion" ) and len( yvs ) > 0:
            rmin, rmax = .7 * min ( yvs ), min ( 2., max ( yvs ) )
            xvals = set(o["points"]["x"])
            ## we assume the exclusion lines to be "points", so
            ## we draw horizontal lines in each point
            label = "official observed exclusion"
            for xv in xvals:
                plt.plot ( [xv]*2, [ rmin, rmax ], c="k",
                           label=label )
                label = ""
    for o in eofficial:
        # logger.info ( f"exclusion object: {o}" )
        if o["name"].startswith ( "expExclusion" ) and len ( yvs ) > 0:
            rmin, rmax = .7 * min ( yvs ), min ( 2., max ( yvs ) )
            xvals = set(o["points"]["x"])
            label = "dashed lines are expected values"
            for xv in xvals:
                plt.plot ( [xv]*2, [ rmin, rmax ], c="k", linestyle = ":",
                           label=label )
                label = ""
    plt.legend( framealpha=.5 )

    if options["extraInfo"]: ## a timestamp, on the right border
        import time
        t = time.strftime("%b %d, %Y, %H:%M")
        rs = rmin + ( rmax - rmin ) * .6
        dx = 0.
        if len(xvs)>0:
            dx = max(xvs)+( max(xvs)-min(xvs))*.07
        if False:
            plt.text ( dx, rs, t, c="grey", rotation="vertical" )
    if kfactor != None and abs ( kfactor - 1. ) > 1e-4:
        plt.text ( .93, .18, f"k-factor {kfactor:.2f}", c="gray",
                   fontsize = 10, rotation=90, transform = fig.transFigure )
    figureUrl = getFigureUrl(validationPlot)
    subtitle = getDatasetDescription ( validationPlot, maxLength = 60 )
    plt.text ( -.12, -.10, subtitle, transform = ax.transAxes, c="grey" )
    if figureUrl:
        plt.text ( -.15, -.132, figureUrl, fontsize=7, c="b",
                   transform = ax.transAxes )
    if inverse:
        plt.plot ( [min(xvs),max(xvs)], [ 1.0, 1.0 ], c="k" )
    return ( plt.gcf(), plt )
