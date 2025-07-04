#!/usr/bin/env python3

"""
.. module:: uglyMatplotlib
   :synopsis: Main method for creating ugly plots, matplotlib version

.. moduleauthor:: Wolfgang Waltenberger

"""

import logging,os,sys,numpy,random,copy,shutil
#sys.path.append('../')
from array import array
import math
logger = logging.getLogger(__name__)
from smodels.base.physicsUnits import fb, GeV, pb
from smodels.experiment import expAuxiliaryFuncs
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname
from plottingFuncs import getGridPoints, yIsLog, getFigureUrl, \
         getDatasetDescription, getAxisRange, isWithinRange, \
         filterWithinRanges
from validationHelpers import widthOfStableParticles, getAxisType, prettyAxes

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
    import matplotlib.pylab as plt
    plt.dontplot = False
    plt.clf()
    plt.grid(visible=False )
    logger.info ( f"now create ugly plot for {validationPlot.expRes.globalInfo.id}, {validationPlot.txName}: {validationPlot.axes}" )
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
    nPointsOnPlane = 0
    # Get excluded and allowed points:
    nmax = len(validationPlot.data)
    if False:
        nmax = 20
    ndots = 30
    ndigits = int(math.ceil(math.log10(nmax)))
    try:
        ndots = shutil.get_terminal_size().columns - 45-ndigits
    except Exception as e:
        pass
    if "COLUMNS" in os.environ:
        ndots = int(os.environ["COLUMNS"])-45-ndigits
    dn = int(math.ceil(nmax/ndots))
    print ( " "*int(43+ndigits+ndots), end="<\r" )
    print ( f"[uglyMatplotlib] checking {nmax} validation points >", end="" )
    xcontainer,ycontainer=[],[]
    for ctPoints,pt in enumerate(validationPlot.data):
        if ctPoints % dn == 0:
            print ( ".", end="", flush=True )
        if ctPoints == nmax:
            print ( "[uglyMatplotlib] emergency break" )
            break
        if "error" in pt.keys():
            if "axes" in pt and pt["axes"]!=None:
                noresult.append ( pt["axes"] )
                nErrors += 1
                nPointsOnPlane += 1
            continue
                # we should not even count these, they are not on our plane
        nPointsOnPlane += 1
        if pt["UL"] == None:
            logger.debug ( f"No upper limit for {pt}" )
            continue
        countPts += 1
        if kfactor == None and "kfactor" in pt:
            kfactor = pt ['kfactor']
        else:
            if "kfactor" in pt:
                if abs(kfactor - pt['kfactor'])> 1e-5:
                    logger.error("kfactor not a constant throughout the plane!")
                    sys.exit()

        xvals = pt['axes']
        if xvals == None:
            # dont have any coordinates? skip.
            logger.warning ( f'do I need to skip {pt}?' )
            continue
        if "t" in pt:
            tavg += pt["t"]
        r = pt['signal']/pt ['UL']
        if type(xvals) == dict:
            if not "x" in xvals:
                continue
        # if isinstance(xvals,dict):
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
        if logY:
            if type(y)==str and y=="stable":
                y = widthOfStableParticles
            if y > 1e-8:
                continue
        if not isWithinRange ( xrange, x ):
            continue
        if not isWithinRange ( yrange, y ):
            continue
        xcontainer.append ( x )
        ycontainer.append ( y )
        coords = { "x": x, "y": y }

        if 'condition' in pt and pt['condition'] and pt['condition'] > 0.05:
            logger.warning( f"Condition violated at {pt['condition']} for file {pt['slhafile']}" )
            cond_violated.append( coords )
        elif r > 1.:
            if r < looseness:
                excluded_border.append( coords )
            else:
                excluded.append( coords )
        else:
            if r> 1./looseness:
                allowed_border.append( coords )
            else:
                allowed.append( coords )
    print ( )


    logger.info ( "done!" )

    massPlane = MassPlane.fromString( validationPlot.txName, validationPlot.axes )
    for ctr,coords in enumerate(origdata):
        #masses = removeUnits ( pt[0], standardUnits=GeV )
        #coords = massPlane.getXYValues(masses)
        if coords != None and "y" in coords and coords["y"] != None:
            if logY and coords["y"]>1e-8:
                # coords["y"]=math.exp(-coords["y"]) * 10**(-3)
                coords["y"]=expAuxiliaryFuncs.unscaleWidth ( coords["y"] )
            if xrange != None and not ( xrange[0] < coords["x"] < xrange[1] ):
                continue
            if yrange != None and not ( yrange[0] < coords["y"] < yrange[1] ):
                continue
            pt = { "i": len(gridpoints), "x": coords["x"], "y": coords["y"] }
            gridpoints.append( pt )

    if countPts == 0:
        logger.warning ( "no good points??" )
        return ( None, None )
    tavg = tavg / len (validationPlot.data )

    for p in validationPlot.officialCurves:
        if type(p) not in [ dict ]:
            logger.error ( "exclusion lines are not dicts, are you sure you are not using sms.root files?" )
            continue
        px, py = filterWithinRanges ( p["points"], xrange, yrange )
        try:
            plt.plot ( px, py, c="white", linewidth=4, zorder=7 )
        except ValueError as e:
            print ( f"[uglyMatplotlib] ValueError: {e}" )
        label = "official exclusion"
        linestyle = "-"
        if "ExclusionP1" in p["name"] or "ExclusionM1" in p["name"]:
            label = ""
            linestyle = "dotted"
        try:
            plt.plot ( px, py, c="black", label=label, linestyle=linestyle, zorder=8 )
        except ValueError as e:
            print ( f"[uglyMatplotlib] ValueError: {e}" )
    ax = plt.gca()
    if logY:
        ax.set_yscale('log')
    fig = plt.gcf()

    base = []
    dx = .12 ## top, left
    nleg = 5
    from sympy import var
    xvar_,yvar_,zvar_,wvar_ = var( "xvar_ yvar_ zvar_ wvar_" )
    g=eval(validationPlot.axes.replace("x","xvar_").replace("y","yvar_").replace("z","zvar_").replace("w","wvar_" ) )
    if type(g) == dict:
        reverse = False
    else:
        reverse = (g[1][0]==yvar_) ## do reverse if [x,*],[y,*] type of plot (eg TGQ)
    if reverse: ## if it is an [x,*],[y,*] plot, put legend to right, not left
        dx = .53
    if len(allowed)>0:
        plt.plot ( get("x",allowed), get("y",allowed), marker="o", \
                   linestyle=None, c="limegreen", linewidth=0, label="allowed", zorder = 3 )
    if len(excluded)>0:
        plt.plot ( get("x",excluded), get("y",excluded), marker="o", \
                   linestyle=None, c="red", linewidth=0, label="excluded", zorder = 4 )
    if len(allowed_border)>0:
        plt.plot ( get("x",allowed_border), get("y",allowed_border), marker="o", \
                   linestyle=None, c="darkgreen", linewidth=0, label="allowed (but close)", zorder = 5)
    if len(excluded_border)>0:
        plt.plot ( get("x",excluded_border), get("y",excluded_border), marker="o", \
                   linestyle=None, c="orange", linewidth=0, label="excluded (but close)", zorder = 6)
    if len(cond_violated)>0:
        plt.plot ( get("x",cond_violated), get("y",cond_violated), marker="o", \
                linestyle=None, c="gray", linewidth=0, label="condition violated")
    if len(noresult)>0 and len(xcontainer)>0:
        filterednoresult = []
        xRange = ( min(xcontainer)*.8-2, max(xcontainer)*1.1+2 )
        yRange = ( min(ycontainer)*.8-2, max(ycontainer)*1.1+2 )
        if logY:
            yRange = ( min(ycontainer)*.2, max(ycontainer)*5. )
        for r in noresult:
            if "x" in r and isWithinRange ( xRange, r["x"] ):
                if not "y" in r:
                    filterednoresult.append (  r )
                elif "y" in r and isWithinRange ( yRange, r["y"] ):
                    filterednoresult.append (  r )
        plt.plot ( get("x",filterednoresult), get("y",filterednoresult), marker="o", \
                   linestyle=None, c="gray", linewidth=0, markersize=2, label="no result", zorder = 1)
    if len(gridpoints)>0:
        zorder = 12
        if len(gridpoints)>3000: # a lot of points? put to background!
            zorder = 2
        plt.plot ( get("x",gridpoints), get("y",gridpoints), marker="+", \
                   linestyle=None, c="blue", linewidth=0, markersize=4, label=f"{len(gridpoints)} SModelS db grid points", zorder = zorder )
    axes = prettyAxes(validationPlot)
    axes = axes.replace("*","")
    axes = axes.replace("0.5",".5")
    axes = axes.replace("100.","100")
    axes = axes.replace("anyBSM","*")
    #axes = axes.replace("MET","$\\\\slash{E}_T}$" )
    title = validationPlot.expRes.globalInfo.id + " " \
            + validationPlot.txName # + ": " + axes
    subtitle = getDatasetDescription ( validationPlot, maxLength = 50 )
    figureUrl = getFigureUrl(validationPlot)

    if len(validationPlot.expRes.datasets) == 1 and \
            type(validationPlot.expRes.datasets[0].dataInfo.dataId)==type(None):
        subtitle = "dataset: UL"

    # sns.set()
    # plt.title(title)
    plt.text ( .04, .95, title, fontsize=12, transform = fig.transFigure )
    if logY: # y>1e-24 and y<1e-6:
        ## assume that its a "width" axis
        ymin = min ( ycontainer ) * 0.5
        ymax = max ( ycontainer ) * 2.
        #base.GetYaxis().SetRangeUser( ymin, ymax )
    else:
        if not "style" in options or not "axis" in options["style"]:
            pass
    plt.xlabel ( xlabel )
    plt.ylabel ( ylabel )
    ysubtitle = .95
    ysubtitle = .02
    plt.text(.04, ysubtitle, subtitle,fontsize=10, transform = fig.transFigure )
    #if figureUrl:
    plt.text ( .95, .95, axes, fontsize = 8, transform = fig.transFigure,
               horizontalalignment = "right" )
    if False:
        plt.text ( .05, .023, str(figureUrl), fontsize=10,
                   horizontalalignment = "right", transform=fig.transFigure )

    if kfactor != None and abs ( kfactor - 1. ) > 1e-2:
        plt.text ( .93, .18, f"k-factor {kfactor:.2f}", c="gray",
                   fontsize = 10, rotation=90, transform = fig.transFigure )
    dxpnr = .95
    halign = "right"
    if reverse: ## if reverse put this line at left of plot
        dxpnr = .12
        halign = "left"
    # ypnr = 0.95
    ypnr = .03
    ### we write <number of error points> / <number of points in plane> [<number of points in tarball]
    plt.text ( dxpnr, ypnr, f"{nErrors}/{nPointsOnPlane} [{len(validationPlot.data)}] points w/o results",
            c="gray", fontsize=10, transform = fig.transFigure,
            horizontalalignment=halign )
    l = plt.legend( loc="best") # could be upper right
    l.set_zorder(20)
    if options["extraInfo"]: ## a timestamp, on the right border
        import time
        plt.text ( .93, .65, time.strftime("%b %d, %Y, %H:%M"), c="gray",
                   fontsize = 9, transform=fig.transFigure,
                   rotation = 90 )
    if options["preliminary"] not in [ False, "False" ]:
        ## preliminary label, ugly plot
        plt.text ( .3, .4, "SModelS preliminary", c="blue",
                   fontsize = 18, transform=fig.transFigure,
                   rotation = -25, zorder=100 )

    if not silentMode:
        _ = raw_input("Hit any key to close\n")

    # plt.savefig ( "this.png" )
    return plt,base
