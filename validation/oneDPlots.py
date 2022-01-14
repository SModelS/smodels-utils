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
from plottingFuncs import getGridPoints, yIsLog, setOptions, getFigureUrl, setAxes

try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass

def create1DPlot( validationPlot, silentMode=True, 
        looseness = 1.2, options : dict = {} ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate the "1d" exclusion plot

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :return: TCanvas object containing the plot
    """
    logger.error ( "now create 1d plot for %s, %s: %s" % \
       ( validationPlot.expRes.globalInfo.id, validationPlot.txName, 
         validationPlot.axes ) )

    if not validationPlot.data:
        logger.error("Data for validation plot is not defined.")
        return (None,None)

    dn = 50
    nmax = len(validationPlot.data)
    from smodels_utils.plotting import mpkitty as plt

    xvs, yvs = [], []
    values = { "excluded": { "x": [], "y": [] } }
    values["allowed"]= { "x": [], "y": [] }
    values["error"]= { "x": [], "y": [] }
    values["excluded_border"]= { "x": [], "y": [] }
    values["allowed_border"]= { "x": [], "y": [] }
    for ctPoints,pt in enumerate(validationPlot.data):
        if ctPoints % dn == 0:
            print ( ".", end="", flush=True )
        if ctPoints == nmax:
            logger.error ( "emergency break" )
            break
        if "axes" in pt and "x" in pt["axes"]:
            x = pt["axes"]["x"]
            y = float ( "nan" )
            if "signal" in pt and "UL" in pt:
                y = pt["signal"] / pt["UL"] 
            label = "error"
            values[label]["x"].append(x)
            values[label]["y"].append(y)
            if math.isfinite ( y ):
                yvs.append ( y )
                xvs.append ( x )
            if y < float("inf"):
                label = "excluded"
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if y < 1.3:
                label = "excluded_border"
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if y < 1:
                label = "allowed_border"
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if y < 0.7:
                label = "allowed"
                values[label]["x"].append(x)
                values[label]["y"].append(y)
    plt.ylabel ( r"r = $\sigma_\mathrm{signal}$ / $\sigma_\mathrm{UL}$" )
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
            lbl = "SModelS excluded"
        if label == "allowed":
            lbl = "SModelS allowed"
        if label == "allowed_border":
            lbl = "SModelS allowed"
        plt.plot ( values[label]["x"], values[label]["y"], c=c, marker="o", label=lbl )
        # plt.plot ( values[label]["x"], values[label]["y"], c=c )
    fname = "me.png"
    pName = prettyTxname(validationPlot.txName, outputtype="latex" )
    pAxis = "; ".join ( prettyAxes(validationPlot.txName, validationPlot.axes, outputtype="latex" ))
    title = f"{validationPlot.expRes.globalInfo.id}: {pName} \n {pAxis}" 
#       ( validationPlot.expRes.globalInfo.id, validationPlot.txName, 
#         validationPlot.axes ) )
    plt.title ( title )
    official = validationPlot.officialCurves
    eofficial = validationPlot.expectedOfficialCurves
    # print ( "official", official )
    for o in official:
        if o["name"].startswith ( "obsExclusion" ):
            rmin, rmax = min ( yvs ), max ( yvs )
            plt.plot ( o["points"]["x"], [ rmin, rmax ], c="k", 
                       label="official observed exclusion" )
    plt.legend( framealpha=.5 )

    if options["extraInfo"]: ## a timestamp, on the right border
        import time
        t = time.strftime("%b %d, %Y, %H:%M")
        rs = rmin + ( rmax - rmin ) * .6
        dx = max(xvs)+( max(xvs)-min(xvs))*.07
        plt.text ( dx, rs, t, c="grey", rotation="vertical" )
    figureUrl = getFigureUrl(validationPlot)
    if figureUrl:
        rs = rmin - ( rmax - rmin ) * .2
        dx = min(xvs)-( max(xvs)-min(xvs))*.22
        plt.text ( dx, rs, figureUrl, fontsize=7, c="b" )

    # plt.savefig ( fname )
    # plt.kittyPlot()

    return ( plt.gcf(), plt )
