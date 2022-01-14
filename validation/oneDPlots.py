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
from plottingFuncs import getGridPoints, yIsLog, setOptions, getFigureUrl, \
         setAxes, getDatasetDescription

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
    fig, ax = plt.subplots()

    xvs, yvs = [], []
    values = { "excluded": { "x": [], "y": [], "ex": [], "ey": [] } }
    values["allowed"]= { "x": [], "y": [],"ex": [],  "ey": [] }
    values["error"]= { "x": [], "y": [],"ex": [],  "ey": [] }
    values["excluded_border"]= { "x": [], "y": [],"ex": [],  "ey": [] }
    values["allowed_border"]= { "x": [], "y": [],"ex": [],  "ey": [] }
    for ctPoints,pt in enumerate(validationPlot.data):
        if ctPoints % dn == 0:
            print ( ".", end="", flush=True )
        if ctPoints == nmax:
            logger.error ( "emergency break" )
            break
        if "axes" in pt and "x" in pt["axes"]:
            x = pt["axes"]["x"]
            y, ey = float ( "nan" ), float ( "nan" )
            if "signal" in pt and "UL" in pt:
                y = pt["signal"] / pt["UL"] 
                if "eUL" in pt:
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
            if y < float("inf"):
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if ey < float("inf"):
                values[label]["ex"].append(x)
                values[label]["ey"].append(ey)
            label = "excluded_border"
            if y < 1.3:
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if ey < 1.3:
                values[label]["ex"].append(x)
                values[label]["ey"].append(ey)
            label = "allowed_border"
            if y < 1:
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if ey < 1:
                values[label]["ex"].append(x)
                values[label]["ey"].append(ey)
            label = "allowed"
            if y < 0.7:
                values[label]["x"].append(x)
                values[label]["y"].append(y)
            if ey < 0.7:
                values[label]["ex"].append(x)
                values[label]["ey"].append(ey)
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
            lbl = "SModelS excluded (but close)"
        if label == "allowed":
            lbl = "SModelS allowed"
        if label == "allowed_border":
            lbl = "SModelS allowed (but close)"
        plt.plot ( values[label]["x"], values[label]["y"], c=c, marker="o", label=lbl )
        #if len(values[label]["ey"]) == len(values[label]["ex"]):
        plt.plot ( values[label]["ex"], values[label]["ey"], c=c, linestyle=":", marker=None )
        # plt.plot ( values[label]["x"], values[label]["y"], c=c )
    # fname = "me.png"
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
    for o in eofficial:
        print ( "eo", o )
        if o["name"].startswith ( "expExclusion" ):
            rmin, rmax = min ( yvs ), max ( yvs )
            plt.plot ( o["points"]["x"], [ rmin, rmax ], c="k", 
                       linestyle = ":",
                       label="dashed lines are expected values" )
    plt.legend( framealpha=.5 )

    if options["extraInfo"]: ## a timestamp, on the right border
        import time
        t = time.strftime("%b %d, %Y, %H:%M")
        rs = rmin + ( rmax - rmin ) * .6
        dx = max(xvs)+( max(xvs)-min(xvs))*.07
        plt.text ( dx, rs, t, c="grey", rotation="vertical" )
    figureUrl = getFigureUrl(validationPlot)
    subtitle = getDatasetDescription ( validationPlot )
    plt.text ( -.08, 1.03, subtitle, transform = ax.transAxes, c="grey" )
    if figureUrl:
        plt.text ( -.15, -.122, figureUrl, fontsize=7, c="b", 
                   transform = ax.transAxes )
    return ( plt.gcf(), plt )
