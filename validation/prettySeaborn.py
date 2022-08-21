#!/usr/bin/env python3

"""
.. module:: prettySeaborn
   :synopsis: the module for the "pretty" seaborn-based plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import logging,os,sys,random,copy
import numpy as np
sys.path.append('../')
from array import array
import math,ctypes
logger = logging.getLogger(__name__)
from smodels.tools.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxes
from plottingFuncs import yIsLog, getFigureUrl, getDatasetDescription, \
         getClosestValue

try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass

from scipy import interpolate
import numpy as np

# copied from https://stackoverflow.com/questions/37662180/interpolate-missing-values-2d-python
def interpolate_missing_pixels(
        image: np.ndarray,
        mask: np.ndarray,
        method: str = 'nearest',
        fill_value: float = 0
):
    """
    :param image: a 2D image
    :param mask: a 2D boolean image, True indicates missing values
    :param method: interpolation method, one of
        'nearest', 'linear', 'cubic'.
    :param fill_value: which value to use for filling up data outside the
        convex hull of known pixel values.
        Default is 0, Has no effect for 'nearest'.
    :return: the image with missing values interpolated
    """
    from scipy import interpolate

    h, w = image.shape[:2]
    xx, yy = np.meshgrid(np.arange(w), np.arange(h))

    known_x = xx[~mask]
    known_y = yy[~mask]
    known_v = image[~mask]
    missing_x = xx[mask]
    missing_y = yy[mask]

    interp_values = interpolate.griddata(
        (known_x, known_y), known_v, (missing_x, missing_y),
        method=method, fill_value=fill_value
    )

    interp_image = image.copy()
    interp_image[missing_y, missing_x] = interp_values

    return interp_image

def createPrettyPlot( validationPlot,silentMode : bool , options : dict, 
                      looseness : float ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate a pretty exclusion plot

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :param looseness: ?
    :param options: the options
    :return: TCanvas object containing the plot
    """
    # Check if data has been defined:
    tgr, etgr, tgrchi2 = [], [], []
    kfactor=None
    xlabel, ylabel, zlabel = 'x [GeV]','y [GeV]',"$r = \sigma_{signal}/\sigma_{UL}$"
    logY = yIsLog ( validationPlot )

    if not validationPlot.data:
        logger.error("Data for validation plot is not defined.")
        return (None,None)
        ## sys.exit()
    # Get excluded and allowed points:
    condV = 0
    hasExpected = False
    ## find out if we have y values
    hasYValues = False
    for pt in validationPlot.data:
        if "error" in pt:
            continue
        if "axes" in pt and "y" in pt["axes"]:
            hasYValues = True
            break
    for pt in validationPlot.data:
        #if "error" in pt.keys():
        #    continue
        if kfactor == None:
            if "kfactor" in pt.keys():
                kfactor = pt ['kfactor']
            elif not "error" in pt.keys():
                kfactor = 1.
        if (not "error" in pt.keys()) and ("kfactor" in pt.keys()) and (abs(kfactor - pt['kfactor'])> 1e-5):
            logger.error("kfactor not a constant throughout the plane!")
            sys.exit()
        #import IPython
        # IPython.embed()
        if not "axes" in pt:
            ## try to get axes from slha file
            pt["axes"] = validationPlot.getXYFromSLHAFileName ( pt["slhafile"], asDict=True )
        xvals = pt['axes']
        if xvals == None: ## happens when not on the plane I think
            continue
        if (not "UL" in pt.keys() or pt["UL"]==None) and (not "error" in pt.keys()):
            logger.warning( "no UL for %s: %s" % (xvals, pt ) )
        r, rexp = float("nan"), float("nan")
        if not "error" in pt.keys():
            if pt["UL"]!=None:
                r = pt['signal']/pt ['UL']
            if "eUL" in pt and pt["eUL"] != None and pt["eUL"] > 0.:
                hasExpected = True
                rexp = pt['signal']/pt ['eUL']
        if r > 3.:
            r=3.
        if rexp > 3.:
            rexp=3.
        if isinstance(xvals,dict):
            if len(xvals) == 1:
                x,y = xvals['x'],r
                ylabel = "r = $\sigma_{signal}/\sigma_{UL}$"
            else:
                x = xvals["x"]
                if "y" in xvals:
                    y = xvals['y']
                elif "w" in xvals:
                    y = xvals['w']

        else:
            x,y = xvals

        if "condition" in pt.keys() and pt['condition'] and pt['condition'] > 0.05:
            condV += 1
            if condV < 5:
                logger.warning("Condition violated for file " + pt['slhafile'])
            if condV == 5:
                logger.warning("Condition violated for more points (not shown)")
        else:
            if not "error" in pt.keys():
                tgr.append( { "i": len(tgr), "x": x, "y": y, "r": r })
                if np.isfinite ( rexp ):
                    etgr.append( { "i": len(etgr), "x": x, "y": y, "rexp": rexp } )
                if "chi2" in pt:
                    tgrchi2.append( { "i": len(tgrchi2), "x": x, "y": y, "chi2": pt["chi2"] / 3.84 } )
    if options["drawExpected"] in [ "auto" ]:
        options["drawExpected"] = hasExpected
    if len ( tgr ) < 4:
        logger.error("No good points for validation plot.")
        return (None,None)

    def get ( var, mlist ): # get variable "var" from list of dicts, mlist
        return [ d[var] for d in mlist ]

    #ROOT has trouble obtaining a histogram from a 1-d graph. So it is
    #necessary to smear the points if they rest in a single line.
    xs = get( "x", tgr )
    ys = get( "y", tgr )
    exs = get( "x", etgr )
    eys = get( "y", etgr )
    if max(ys) == min(ys):
        logger.info("1d data detected, not plotting pretty plot.")
        return None, None
    if max(xs) == min(xs):
        logger.info("1d data detected, not plotting pretty plot.")
        return None, None

    title = validationPlot.expRes.globalInfo.id
    types = []
    for dataset in validationPlot.expRes.datasets:
        ds_txnames = map ( str, dataset.txnameList )
        if not validationPlot.txName in ds_txnames:
            continue
        types.append(dataset.dataInfo.dataType)
    types = list(set(types))
    if len(types) == 1: types = types[0]
    resultType = "%s" %str(types)
    title = title + " ("+resultType+")"
    import matplotlib.pylab as plt
    plt.clf()

    #Get contour graphs:
    contVals = [1./looseness,1.,looseness]
    if options["drawExpected"]:
        contVals = [1.,1.,1.]

    #Draw temp plot:
    rs = get ( "r", tgr )
    Z = {}
    for t in tgr:
        x,y,r = t["x"],t["y"],t["r"]
        if not x in Z:
            Z[x]={}
        Z[x][y]=float(r)
    xs = list ( Z.keys() )
    xs.sort( )
    T = []
    ys.sort( reverse = True )
    for y in ys:
        tmp = []
        for x in xs:
            r = float("nan")
            if y in Z[x]:
                r = Z[x][y]
            else:
                r = getClosestValue ( x, y, tgr, 1. )
            tmp.append ( r )
            rs.append ( r )
                # tmp.append ( float("nan") )
        T.append ( tmp )
    T = np.asarray ( T )
    mask = np.isnan( T )
    T = interpolate_missing_pixels ( T, mask, "cubic", fill_value=float("nan") )
    ax = plt.gca()
    fig = plt.gcf()
    if logY:
        xlabel = "x [mass, GeV]"
        ylabel = "y [width, GeV]"
        ax.set_yscale('log')
    from plottingFuncs import getColormap
    cm = getColormap()
    xtnt = ( min(xs), max(xs), min(ys), max(ys) )
    im = plt.imshow ( T, cmap=cm, extent=xtnt, interpolation="bicubic",
                      vmax = 3.0, vmin = 0., aspect="auto" )
    plt.title ( title )
    # plt.text ( .28, .85, title, transform = fig.transFigure )
    plt.xlabel ( xlabel )
    plt.ylabel ( ylabel )
    
    for p in validationPlot.officialCurves:
        if type(p) not in [ dict ]:
            logger.error ( "exclusion lines are not dicts, are you sure you are not using sms.root files?" )
            continue
        plt.plot ( p["points"]["x"], p["points"]["y"], c="black", label="exclusion (official)" )
    if options["drawExpected"]:
        for p in validationPlot.expectedOfficialCurves:
            if type(p) not in [ dict ]:
                logger.error ( "exclusion lines are not dicts, are you sure you are not using sms.root files?" )
                continue
            plt.plot ( p["points"]["x"], p["points"]["y"], c="black", linestyle="dotted", 
                       label="exp. excl. (official)" )
    plt.colorbar ( im, label=zlabel, fraction = .046, pad = .04 )
    try:
        from scipy.ndimage.filters import gaussian_filter
        T = gaussian_filter( T, 1. )
    except:
        pass
    cs = plt.contour( T, colors="blue", levels=[1.], extent = xtnt, origin="image" )
    csl = plt.plot([-1,-1],[0,0], c = "blue", label = "exclusion (SModelS)", 
                  transform = fig.transFigure ) 
    pName = prettyTxname(validationPlot.txName, outputtype="latex" )
    if pName == None:
        pName = "define {validationPlot.txName} in prettyDescriptions"
    txStr = validationPlot.txName +': '+pName
    plt.text(.03,.95,txStr,transform=fig.transFigure, fontsize=9 )
    axStr = prettyAxes(validationPlot.txName,validationPlot.axes,\
                       outputtype="latex")
    plt.text(.95,.95,axStr,transform=fig.transFigure, fontsize=9,
               horizontalalignment="right" )
    figureUrl = getFigureUrl(validationPlot)

    subtitle = getDatasetDescription ( validationPlot )
    if validationPlot.combine == False and len(validationPlot.expRes.datasets) > 1:
        for ctr,x in enumerate(validationPlot.data):
            if "error" in x.keys():
                continue
            break
        if validationPlot.data != None and validationPlot.data[ctr] != None and "dataset" in validationPlot.data[ctr].keys() and validationPlot.data[ctr]["dataset"]!=None and "combined" in validationPlot.data[ctr]["dataset"]:
            logger.warning ( "asked for an efficiencyMap-type plot, but the cached validationData is for a combined plot. Will label it as 'combined'." )
        else:
            subtitle = "best SR"
    if validationPlot.validationType == "tpredcomb":
            subtitle = "combination of tpreds"
    plt.text ( .95, .0222, subtitle, transform=fig.transFigure, fontsize=10,
               horizontalalignment="right" )
    if figureUrl:
        plt.text( .13, .13, f"{figureUrl}", 
                  transform=fig.transFigure, c = "black", fontsize = 7 )
		    # l1.DrawLatex(.01,0.023,"#splitline{official plot:}{%s}" % figureUrl)

    if kfactor is not None and abs ( kfactor - 1.) > .01:
        plt.text( .65,.83, "k-factor = %.2f" % kfactor, fontsize=10,
                  c="gray", transform = fig.transFigure )
    if options["preliminary"]:
        ## preliminary label, pretty plot
        plt.text ( .3, .4, "SModelS preliminary", transform=fig.transFigure,
                   rotation = 25., fontsize = 18, c="blue", zorder=100 )
    legendplacement = options["legendplacement"]
    legendplacement = legendplacement.replace("bottom","lower")
    legendplacement = legendplacement.replace("top","upper")
    if legendplacement in [ "automatic", None, "", "none" ]:
        legendplacement = "best"
    plt.legend( loc=legendplacement ) # could be upper right
    plt.grid(visible=False)
    # plt.tight_layout()

    if not silentMode:
        ans = raw_input("Hit any key to close\n")

    if not hasYValues:
        logger.error ( "it seems like we do not have y-values, so we break off." )
        plt.dontplot = True

    return plt,tgr
