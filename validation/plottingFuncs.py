#!/usr/bin/env python3

"""
.. module:: plottingFuncs
   :synopsis: Main methods for dealing with the plotting of a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,numpy,random,copy
from typing import Union, Optional
sys.path.append('../')
from array import array
import math, ctypes
logger = logging.getLogger(__name__)
from smodels.tools.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxes
try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass
try:
    from smodels.theory.auxiliaryFunctions import removeUnits
except:
    from backwardCompatibility import removeUnits

def getColormap():
    """ our matplotlib colormap for pretty plots """
    # return plt.cm.RdYlBu_r
    # return plt.cm.RdYlGn_r
    from  matplotlib.colors import LinearSegmentedColormap
    # c = ["darkred","red","lightcoral","lightyellow", "palegreen","green","darkgreen"]
    c = ["darkgreen", "green", "palegreen", "lightgoldenrodyellow", "lightcoral", "red", (.9,0,0), (.7,0,0) ]
    #v = [0,.15,.4,.5,0.6,.9,1.]
    # v = [0,.1,.3,.67,0.8,.9,1.]
    v = [0,.11,.22,.33,0.52,.7,.85,1.]
    l = list(zip(v,c))
    cmap=LinearSegmentedColormap.from_list('rg',l, N=256)
    return cmap

def isWithinRange ( xyrange : list, xy : float ):
    """ check if xy is within xyrange """
    if xyrange == None:
        return True
    return xyrange[0] <= xy <= xyrange[1]

def filterWithinRanges ( points : dict, xrange : Optional[list], \
        yrange : Optional[list], defRetZeroes : bool = False ):
    """ filter from points all that is not within xrange or yrange 
    :param defRetZeroes: if true, then return list of zeroes if no y coordinates
    """
    pxs = points["x"]
    px = []
    if not "y" in points:
        for x in pxs:
            if not isWithinRange ( xrange, x ):
                continue
            px.append ( x )
        py = [0.] * len(px) if defRetZeroes else None
        return px, py
    pys = points["y"]
    px, py = [], []
    for x,y in zip ( pxs, pys ):
        if not isWithinRange ( xrange, x ):
            continue
        if not isWithinRange ( yrange, y ):
            continue
        px.append ( x )
        py.append ( y )
    return px, py

def getAxisRange ( options : dict, label : str = "xaxis" ):
    """ given an options dictionary, obtain a range for the axis named
        <label> 
    :returns: range list, e.g. [0,1000], or None
    """
    if not "style" in options:
         return None
    style = options["style"]
    if label in style:
        plabel = style.find(label)
        pstart = style.find("[",plabel)
        pend = style.find("]",pstart)
        try:
            xrange=eval(style[pstart:pend+1] )
            return xrange
        except Exception as e:
            logger.error ( f"when evaluating {label} range: {e}" )
    return None

def getClosestValue ( x : float, y : float , graph : dict , dmax : float = 1. ):
    """ from the graph dictionary, return point closest to x,y
    :returns: closest value of graph dictionary, as long as its closer than dmax.
              else return nan
    """
    dmin, v = float("inf"), None
    for t in graph:
        d = (t["x"]-x)**2 + (t["y"]-y)**2
        if d < dmax:
            return v
        if d < dmin:
            dmin = d
            v = t["r"]
    #if dmin < dmax:
    #    return v
    return float("nan")


def getExclusionCurvesFor(expResult,txname=None,axes=None, get_all=False,
                          expected=False ):
    """
    Reads exclusion_lines.json and returns the TGraph objects for the exclusion
    curves. If txname is defined, returns only the curves corresponding
    to the respective txname. If axes is defined, only returns the curves
    for that axis

    :param expResult: an ExpResult object
    :param txname: the TxName in string format (i.e. T1tttt)
    :param axes: the axes definition in string format (e.g. [x, y, 60.0], [x, y, 60.0]])
    :param get_all: Get also the +-1 sigma curves?
    :param expected: if true, get expected, not observed

    :return: a dictionary, where the keys are the TxName strings
            and the values are the respective list of TGraph objects.
    """

    import json
    if type(expResult)==list:
        expResult=expResult[0]
    jsonfile = os.path.join(expResult.path,'exclusions.json')
    if not os.path.isfile(jsonfile):
        jsonfile = os.path.join(expResult.path,'exclusion_lines.json')
        if not os.path.isfile(jsonfile):
            logger.error("json file %s not found" % jsonfile )
            from rootPlottingFuncs import getExclusionCurvesForFromSmsRoot
            return getExclusionCurvesForFromSmsRoot ( expResult, txname, axes,
                    get_all, expected )
    from smodels_utils.helper import various
    return various.getExclusionCurvesFor ( jsonfile, txname, axes, get_all,
            expected )

def getDatasetDescription ( validationPlot, maxLength = 100 ):
    """ get the description of the dataset that appears as a subtitle
        in e.g. the ugly plots """
    subtitle = f"{len(validationPlot.expRes.datasets)} datasets: "
    if validationPlot.validationType == "tpredcomb":
        subtitle = f"{len(validationPlot.expRes.datasets)} tpreds: "

    if hasattr ( validationPlot.expRes.globalInfo, "jsonFiles" ) and \
            validationPlot.combine == True:
        ## pyhf combination
        subtitle = "pyhf combining %d SRs: " % len(validationPlot.expRes.datasets)
    for dataset in validationPlot.expRes.datasets:
        ds_txnames = map ( str, dataset.txnameList )
        if not validationPlot.txName in ds_txnames:
            continue
        dataId = str(dataset.dataInfo.dataId)
        if len(dataId)>11:
            dataId = dataId[:8]+" ... "
        subtitle+=dataId+", "
    subtitle = subtitle[:-2]
    if hasattr ( validationPlot.expRes.globalInfo, "covariance" ) and \
            validationPlot.combine == True:
        ver = 0
        if hasattr ( validationPlot.expRes.datasets[0].dataInfo, "thirdMoment"):
            ver=" (SLv2)"
        subtitle = f"combination{ver} of {len(validationPlot.expRes.datasets)} signal regions"
    def find_all(a_str, sub):
        start = 0
        while True:
            start = a_str.find(sub, start)
            if start == -1: return
            yield start
            start += len(sub) # use start += 1 to find overlapping matches
    if len(subtitle) > maxLength:
        pos = maxLength
        idx = numpy.array ( list ( find_all ( subtitle, "," ) ) )
        p1 = idx[idx<maxLength]
        if len(p1)>0:
            pos = p1[-1]
        subtitle = subtitle[:pos] + ", ..."
    if len(validationPlot.expRes.datasets) == 1 and \
            type(validationPlot.expRes.datasets[0].dataInfo.dataId)==type(None):
        subtitle = "dataset: UL"
    return subtitle

def getFigureUrl( validationPlot ):
    """ get the URL of the figure, as a string """
    txname = validationPlot.expRes.datasets[0].txnameList[0]
    txurl = txname.getInfo("figureUrl")
    txaxes = txname.getInfo("axes")
    if isinstance(txurl,str):
        return txname.getInfo("figureUrl" )
    if not txurl:
        return None
    if type(txurl) != type(txaxes):
        logger.error("figureUrl (%s) and axes (%s) are not of the same type" %(txurl,
                       txaxes))
        return None
    elif isinstance(txurl,list) and len(txurl) != len(txaxes):
        logger.error("figureUrl (%s) and axes (%s) are not of the same length" %(txurl,
                       txaxes))
        return None
    if not validationPlot.axes in txaxes:
        return None
    pos = [i for i,x in enumerate(txaxes) if x==validationPlot.axes ]

    if len(pos)!=1:
        logger.error("found axes %d times. Did you declare several maps for the same analysis/dataset/topology combo? Will exit, please fix!" % len(pos))
        sys.exit()
    return txurl[pos[0]]

def getGridPoints ( validationPlot ):
    """ retrieve the grid points of the upper limit / efficiency map.
        currently only works for upper limit maps. """
    ret = []
    massPlane = MassPlane.fromString( validationPlot.txName, validationPlot.axes )
    for dataset in validationPlot.expRes.datasets:
        txNameObj = None
        for ctr,txn in enumerate(dataset.txnameList):
            if txn.txName == validationPlot.txName:
                txNameObj = dataset.txnameList[ctr]
                break
        if txNameObj == None:
            logger.info ( "no grid points: did not find txName" )
            return []
        if not txNameObj.txnameData._keep_values:
            logger.info ( "no grid points: _keep_values is set to False" )
            return []
        if not hasattr ( txNameObj.txnameData, "origdata"):
            logger.info ( "no grid points: cannot find origdata (maybe try a forced rebuild of the database via runValidation.py -f)" )
            return []
        origdata =eval( txNameObj.txnameData.origdata)
        for ctr,pt in enumerate(origdata):
            masses = removeUnits ( pt[0], standardUnits=GeV )
            coords = massPlane.getXYValues(masses)
            if not coords == None and not coords in ret:
                ret.append ( coords )
    logger.info ( "found %d gridpoints" % len(ret) )
    ## we will need this for .dataToCoordinates
    return ret

def yIsLog ( validationPlot ):
    """ determine if to use log for y axis """
    logY = False
    A = validationPlot.axes.replace(" ","")
    p1 = A.find("(")
    p2 = A.find(")")
    py = A.find("y")
    if py == -1:
        py = A.find("w")
    if p1 < py < p2 and A[py-1]==",":
        logY = True
    return logY
