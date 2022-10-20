#!/usr/bin/env python3

"""
.. module:: uglySeaborn
   :synopsis: Main method for creating ugly plots, seaborn version

.. moduleauthor:: Wolfgang Waltenberger

"""

import logging,os,sys,numpy,random,copy
sys.path.append('../')
from array import array
import math
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

def createUglyPlot( validationPlot,silentMode=True, looseness = 1.2, 
        options : dict = {} ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate the "ugly" exclusion plot

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :return: TCanvas object containing the plot
    """
    def get ( var, mlist ): # get variable "var" from list of dicts, mlist
        return [ d[var] for d in mlist ]
    import seaborn as sns
    import matplotlib.pylab as plt
    plt.dontplot = False
    plt.clf()
    plt.grid(visible=False )
    logger.info ( "now create ugly plot for %s, %s: %s" % \
       ( validationPlot.expRes.globalInfo.id, validationPlot.txName,
         validationPlot.axes ) )
    origdata = getGridPoints ( validationPlot )
    xlabel, ylabel = 'x','y'
    xrange = getAxisRange ( options, "xaxis" )
    yrange = getAxisRange ( options, "yaxis" )
    excluded, allowed, excluded_border, allowed_border, gridpoints = [],[],[],[],[]
    cond_violated, noresult = [], []
    kfactor=None
    logY = yIsLog ( validationPlot )
    tavg = 0.
    countPts = 0 ## count good points

    if not validationPlot.data:
        logger.debug("Data for validation plot is not defined.")
        # x,y = get
        return (None,None)
        ## sys.exit()

    nErrors = 0
    # Get excluded and allowed points:
    nmax = len(validationPlot.data)
    if False:
        nmax = 20
    dn = 50
    print ( " "*int(45+nmax/dn), end="<\r" )
    print ( "[uglySeaborn] checking validation points >", end="" )
    ycontainer=[]
    for ctPoints,pt in enumerate(validationPlot.data):
        if ctPoints % dn == 0:
            print ( ".", end="", flush=True )
        if ctPoints == nmax:
            print ( "[uglySeaborn] emergency break" )
            break
        if "error" in pt.keys():
            vD = validationPlot.getXYFromSLHAFileName ( pt["slhafile"], asDict=True )
            # print ( "vD", vD, pt["slhafile"], validationPlot.axes )
            if vD != None:
                # print ( "adding no-result point", noresult.GetN(), vD )
                x_, y_ = copy.deepcopy ( vD["x"] ), None
                if "y" in vD.keys():
                    y_ = copy.deepcopy ( vD["y"] )
                elif "w" in vD.keys():
                    y_ = copy.deepcopy ( vD["w"] )
                if y_ is None:
                    logger.error ( "the data is 1d." ) # is separate module now
                    sys.exit()
                if not isWithinRange ( xrange, x_ ):
                    continue
                if not isWithinRange ( yrange, y_ ):
                    continue
                noresult.append( { "i": len(noresult), "x": x_, "y": y_ } )
            nErrors += 1
            continue
        countPts += 1
        if kfactor == None:
            kfactor = pt ['kfactor']
        if abs(kfactor - pt['kfactor'])> 1e-5:
            logger.error("kfactor not a constant throughout the plane!")
            sys.exit()

        xvals = pt['axes']
        if xvals == None:
            # happens when not on the plane?
            continue
        if "t" in pt:
            tavg += pt["t"]
        if pt["UL"] == None:
            logger.warning ( "No upper limit for %s" % xvals )
            continue
        r = pt['signal']/pt ['UL']
        if xvals == None:
            # dont have any coordinates? skip.
            logger.warning ( f'do I need to skip {pt}?' )
            continue
        if isinstance(xvals,dict):
            if len(xvals) == 1:
                x,y = xvals['x'],r
                ylabel = "r = #sigma_{signal}/#sigma_{UL}"
            else:
                x = xvals["x"]
                if "y" in xvals:
                    y = xvals['y']
                elif "w" in xvals:
                    y = xvals['w']
        else:
            x,y = pt['axes']
        if logY and y > 1e-8:
            continue
        if xrange != None and not ( xrange[0] < x < xrange[1] ):
            continue
        if yrange != None and not ( yrange[0] < y < yrange[1] ):
            continue
        ycontainer.append ( y )

        if 'condition' in pt and pt['condition'] and pt['condition'] > 0.05:
            logger.warning("Condition violated at %f for file %s" % ( pt['condition'], pt['slhafile']) )
            cond_violated.append( { "i": len(cond_violated), "x": x, "y": y } )
        elif r > 1.:
            if r < looseness:
                excluded_border.append( { "i": len(excluded_border), "x": x, "y": y } )
            else:
                excluded.append( { "i": len(excluded), "x": x, "y": y } )
        else:
            if r> 1./looseness:
                allowed_border.append( { "i": len(allowed_border), "x": x, "y": y } )
            else:
                allowed.append( { "i": len(allowed), "x": x, "y": y } )

    logger.info ( "done!" )

    massPlane = MassPlane.fromString( validationPlot.txName, validationPlot.axes )
    for ctr,coords in enumerate(origdata):
        #masses = removeUnits ( pt[0], standardUnits=GeV )
        #coords = massPlane.getXYValues(masses)
        if coords != None and "y" in coords:
            if logY and coords["y"]>1e-8:
                continue
            if xrange != None and not ( xrange[0] < coords["x"] < xrange[1] ):
                continue
            if yrange != None and not ( yrange[0] < coords["y"] < yrange[1] ):
                continue
            gridpoints.append( { "i": len(gridpoints), "x": coords["x"], 
                                 "y": coords["y"] } )

    if countPts == 0:
        logger.warning ( "no good points??" )
        return ( None, None )
    tavg = tavg / len (validationPlot.data )

    for p in validationPlot.officialCurves:
        if type(p) not in [ dict ]:
            logger.error ( "exclusion lines are not dicts, are you sure you are not using sms.root files?" )
            continue
        plt.plot ( p["points"]["x"], p["points"]["y"], c="white", linewidth=4, zorder=50 ) 
        plt.plot ( p["points"]["x"], p["points"]["y"], c="black", label="official exclusion", zorder=60 )
    ax = plt.gca()
    if logY:
        ax.set_yscale('log')
    fig = plt.gcf()
    for p in validationPlot.expectedOfficialCurves:
        if type(p) not in [ dict ]:
            logger.error ( "exclusion lines are not dicts, are you sure you are not using sms.root files?" )
            continue
        plt.plot ( p["points"]["x"], p["points"]["y"], c="black", linestyle="dotted", 
                   label="official exclusion (expected)" )
    base = []
    dx = .12 ## top, left
    nleg = 5
    from sympy import var
    xvar_,yvar_,zvar_,wvar_ = var( "xvar_ yvar_ zvar_ wvar_" )
    g=eval(validationPlot.axes.replace("x","xvar_").replace("y","yvar_").replace("z","zvar_").replace("w","wvar_" ) )
    reverse = (g[1][0]==yvar_) ## do reverse if [x,*],[y,*] type of plot (eg TGQ)
    if reverse: ## if it is an [x,*],[y,*] plot, put legend to right, not left
        dx = .53
    if len(allowed)>0:
        plt.plot ( get("x",allowed), get("y",allowed), marker="o", \
                linestyle=None, c="limegreen", linewidth=0, label="allowed" )
    if len(excluded)>0:
        plt.plot ( get("x",excluded), get("y",excluded), marker="o", \
                linestyle=None, c="red", linewidth=0, label="excluded" )
    if len(allowed_border)>0:
        plt.plot ( get("x",allowed_border), get("y",allowed_border), marker="o", \
                linestyle=None, c="darkgreen", linewidth=0, label="allowed (but close)")
    if len(excluded_border)>0:
        plt.plot ( get("x",excluded_border), get("y",excluded_border), marker="o", \
                linestyle=None, c="orange", linewidth=0, label="excluded (but close)")
    if len(cond_violated)>0:
        plt.plot ( get("x",cond_violated), get("y",cond_violated), marker="o", \
                linestyle=None, c="gray", linewidth=0, label="condition violated")
    if len(noresult)>0:
        plt.plot ( get("x",noresult), get("y",noresult), marker="o", \
                linestyle=None, c="gray", linewidth=0, markersize=2, label="no result")
    if len(gridpoints)>0:
        plt.plot ( get("x",gridpoints), get("y",gridpoints), marker="+", \
                linestyle=None, c="blue", linewidth=0, markersize=4, label="%s SModelS grid points" % len(gridpoints) )
        #leg.AddEntry(gridpoints, "%d SModelS grid points" % gridpoints.GetN(), "P")
    title = validationPlot.expRes.globalInfo.id + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.axes
            #+ "_" + validationPlot.niceAxes
    subtitle = getDatasetDescription ( validationPlot, maxLength = 50 )
    figureUrl = getFigureUrl(validationPlot)
    sns.set()
    plt.title(title)
    if logY: # y>1e-24 and y<1e-6:
        ## assume that its a "width" axis
        ymin = min ( ycontainer ) * 0.5
        ymax = max ( ycontainer ) * 2.
        #base.GetYaxis().SetRangeUser( ymin, ymax )
    else:
        if not "style" in options or not "axis" in options["style"]:
            pass
            """
            from smodels_utils.helper.rootTools import getBoundingBox, boundingBoxIsFinite
            bb = getBoundingBox ( official )
            if boundingBoxIsFinite ( bb ):
                base.GetYaxis().SetRangeUser( .8*bb["y"][0], 1.25*bb["y"][1] )
                base.GetXaxis().SetRangeUser( .8*bb["x"][0], 1.25*bb["x"][1] )
            """
    plt.xlabel ( xlabel )
    plt.ylabel ( ylabel )
    """
    if xvals != None and len(xvals) == 1:
        base.GetYaxis().SetRangeUser(0.0,2.0)
    """
    plt.text(.05,.95, subtitle,fontsize=10, transform = fig.transFigure )
    if figureUrl:
        plt.text ( .05, .023, str(figureUrl), fontsize=10, 
                   transform=fig.transFigure )

    if kfactor != None and abs ( kfactor - 1. ) > 1e-2:
        plt.text ( .93, .18, "k-factor %.2f" % kfactor, c="gray",
                   fontsize = 10, rotation=90, transform = fig.transFigure )

    dxpnr=.68 ## top, right
    if reverse: ## if reverse put this line at left of plot
        dxpnr = .12
    plt.text ( dxpnr, .95, "%d / %d points with no results" % \
            (nErrors, len(validationPlot.data) ), c="gray", fontsize=10,
            transform = fig.transFigure )
    plt.legend( loc="best" ) # could be upper right
    if options["extraInfo"]: ## a timestamp, on the right border
        import time
        plt.text ( .93, .65, time.strftime("%b %d, %Y, %H:%M"), c="gray", 
                   fontsize = 9, transform=fig.transFigure,
                   rotation = 90 )
    if options["preliminary"]:
        ## preliminary label, ugly plot
        plt.text ( .3, .4, "SModelS preliminary", c="blue", 
                   fontsize = 18, transform=fig.transFigure,
                   rotation = -25, zorder=100 )

    if not silentMode:
        _ = raw_input("Hit any key to close\n")

    plt.savefig ( "this.png" )
    return plt,base
