#!/usr/bin/env python3

"""
.. module:: plottingFuncs
   :synopsis: Main methods for dealing with the plotting of a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,numpy,random,copy
from typing import Union, Optional, Set, List
#sys.path.append('../')
from array import array
import math, ctypes
logger = logging.getLogger(__name__)
from smodels.base.physicsUnits import fb, GeV, pb
from smodels.experiment.txnameObj import TxNameData
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname
from validationHelpers import getAxisType, prettyAxes
import numpy as np

try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass
try:
    from smodels.theory.auxiliaryFunctions import removeUnits
except:
    from backwardCompatibility import removeUnits

import time
rt0 = [ time.time() ]

def timeStamp ( comment, t = None ):
    if t == "start":
        t0 = time.time()
        rt0[0] = t0
        t = t0
    if t == None:
        t = time.time()
    dt = t-rt0[0]
    print ( f"{dt:.2f}: {comment}" )

class Recorder:
    """ a wrapper class that records the function calls, stores
        thme in recorder.py """
    def __init__(self, obj):
        self.recordingfilename = "recorder.py"
        self.recordingfile = open ( self.recordingfilename, "wt" )
        self.recordingfile.write ( "#!/usr/bin/env python3\n" )
        self.recordingfile.write ( "#\n" )
        self.recordingfile.write ( "# a python script that recorded the plotting statements,\n" )
        self.recordingfile.write ( "# so we can reproduce the plotting\n\n" )
        self.recordingfile.write ( "from matplotlib import pyplot as plt\n" )
        self.recordingfile.write ( "from plottingFuncs import getColormap\n" )
        # from matplotlib.transforms import BboxTransformTo, TransformedBbox, Bbox
        self.recordingfile.write ( "import numpy as np\n" )
        self.recordingfile.write ( "from numpy import array\n" )
        self.obj = obj
        self.callable_results = []

    def closeFile ( self ):
        self.recordingfile.close()
        os.chmod ( self.recordingfilename, 0o755 )

    def __getattr__(self, attr):
       #  print("Getting {0}.{1}".format(type(self.obj).__name__, attr))
        ret = getattr(self.obj, attr)
        if hasattr(ret, "__call__"):
            return self.FunctionWrapper(self, ret)
        return ret

    class FunctionWrapper:
        def __init__(self, parent, callable):
            self.parent = parent
            self.callable = callable

        def __call__(self, *args, **kwargs):
            #if self.callable.__name__ == "pcolormesh":
            #    import IPython; IPython.embed()
            s_args = ""
            for a in args:
                if "matplotlib" in str(type(a)):
                    continue
                if len(s_args):
                    s_args += ","
                if type(a) == str:
                    a = f"'{a}'"
                if type(a) in [  np.array, np.ndarray ]:
                    a=list(a)
                a = str(a)
                a = a.replace("nan","np.nan" )
                a = a.replace( r"\r","\\\\r" )
                a = a.replace( r"\t","\\\\t" )
                s_args += a
            for k,v in kwargs.items():
                if "matplotlib.colors.LinearSegmentedColormap" in str(v):
                    s_args += f",{k}=getColormap()"
                    continue
                if "transform" in k:
                    s_args += f",transform=fig.transFigure"
                    continue
                #if "matplotlib" in str(type(v)):
                #    print ( "v", v )
                #    continue
                if len(s_args):
                    s_args += ","
                s_args += f"{k}="
                if type(v)==str:
                    s_args += f"'{str(v)}'"
                else:
                    s_args += f"{str(v)}"
            line = f"plt.{self.callable.__name__}({s_args})\n"
            if "savefig" in line:
                line = "plt.savefig('recorded.png')\n"
            if "plt.gcf()" in line:
                line = "fig=plt.gcf()\n"
            self.parent.recordingfile.write ( line )
            ret = self.callable(*args, **kwargs)
            self.parent.callable_results.append(ret)
            return ret


def importMatplot ( record : bool ):
    """ import matplotlib
    :param record: if true, then wrap the module into a recorder class.
                   this class will create a recorder.py script
    """
    if not record:
        import matplotlib.pylab as plt
        return plt
    import matplotlib.pylab as actualplt
    plt = Recorder ( actualplt )
    import atexit
    atexit.register ( plt.closeFile )
    return plt


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

errMsgIssued = { "axis": False }

def convertNewAxes ( newa ):
    """ convert new types of axes (dictionary) to old (lists) """
    axes = copy.deepcopy(newa)
    if type(newa)==list:
        return axes[::-1]
    if type(newa)==dict:
        if len ( newa ) == 0:
            return []
        axes = [ newa["x"] ]
        if "y" in newa:
            axes.append ( newa["y"] )
        if "z" in newa:
            axes.append ( newa["z"] )
        return axes[::-1]
    if not errMsgIssued["axis"]:
        print ( "[plotRatio] cannot convert axis '%s'" % newa )
        errMsgIssued["axis"]=True
    return None

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
    styles = options["style"].split(";")
    for style in styles:
        if label in style:
            plabel = style.find(label)
            if style.find ( ":", plabel ) > 0:
                plabel = style.find(":", plabel)
            pstart = style.find("[",plabel)
            pend = style.find("]",pstart)
            try:
                xrange=eval(style[pstart:pend+1] )
                return xrange
            except Exception as e:
                logger.error ( f"when evaluating {label} range: {e}" )
                logger.error ( f"  ´-- style {options['style']}->{style[pstart:pend+1]}" )
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
            logger.error( f"json file {jsonfile} not found" )
            if os.path.exists ( os.path.join ( expResult.path, "sms.root" ) ):
                logger.warning ( f"trying with sms.root, but please switch!" )
                from rootPlottingFuncs import getExclusionCurvesForFromSmsRoot
                return getExclusionCurvesForFromSmsRoot ( expResult, txname, axes,
                        get_all, expected )
            # no exclusion_lines as well as no sms.root
            return None
    from smodels_utils.helper import various
    return various.getExclusionCurvesFor ( jsonfile, txname, axes, get_all,
            expected )

def getDatasetDescription ( validationPlot, maxLength = 100 ):
    """ get the description of the dataset that appears as a subtitle
        in e.g. the ugly plots """
    subtitle = f"best of {len(validationPlot.expRes.datasets)} SRs: "
    if validationPlot.validationType == "tpredcomb":
        subtitle = f"{len(validationPlot.expRes.datasets)} tpreds: "

    if hasattr ( validationPlot.expRes.globalInfo, "jsonFiles" ) and \
            validationPlot.combine == True:
        ## pyhf combination
        subtitle = f"pyhf combining {len(validationPlot.expRes.datasets)} SRs: "
    if hasattr ( validationPlot.expRes.globalInfo, "mlModel" ) and \
            validationPlot.combine == True:
        subtitle = f"NN combining {len(validationPlot.expRes.datasets)} SRs: "
    for dataset in validationPlot.expRes.datasets:
        ds_txnames = map ( str, dataset.txnameList )
        if not validationPlot.txName in ds_txnames:
            continue
        dataId = str(dataset.dataInfo.dataId)
        if len(dataId)>8:
            dataId = dataId[:7]+"*"
        subtitle+=dataId+", "
    subtitle = subtitle[:-2]
    if hasattr ( validationPlot.expRes.globalInfo, "covariance" ) and \
            validationPlot.combine == True:
        ver = ""
        dI = validationPlot.expRes.datasets[0].dataInfo
        if hasattr ( dI, "thirdMoment") and dI.thirdMoment != None:
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
        subtitle = ""

    return subtitle

def getFigureUrl( validationPlot ):
    """ get the URL of the figure, as a string """
    txname = validationPlot.expRes.datasets[0].txnameList[0]
    txurl = txname.figureUrl
    txaxes = "???"
    if hasattr ( txname, "axes" ):
        txaxes = txname.axes
    else:
        txaxes = txname.axesMap
    if isinstance(txurl,str):
        return txname.figureUrl
    if not txurl:
        return None
    if type(txurl) != type(txaxes):
        logger.error( f"figureUrl ({txurl}) and axes ({txaxes}) are not of the same type" )
        return None
    elif isinstance(txurl,list) and len(txurl) != len(txaxes):
        logger.warning( f"for {txname} -- figureUrl ({len(txurl)}) and axes ({len(txaxes)}) are not of the same length:" )
        """
        for i in txurl:
            print ( f" `- {i}" )
        for i in txaxes:
            print ( f" `- {i}" )
        """
        return None
    if not validationPlot.axes in txaxes:
        return None
    pos = [i for i,x in enumerate(txaxes) if x==validationPlot.axes ]

    if len(pos)!=1:
        logger.error("found axes %d times. Did you declare several maps for the same analysis/dataset/topology combo? Will exit, please fix!" % len(pos))
        sys.exit()
    return txurl[pos[0]]

def convertOrigData ( txnameData : TxNameData ):
    """ convert the original data in txnameobj to lists """
    ret = []
    for t in txnameData.origdata:
        ret.append ( list(t))
    return ret

def getGridPointsV2 ( validationPlot ):
    """ retrieve the grid points of the upper limit / efficiency map,
    for axes of SModelS v2 type """
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
        origdata = convertOrigData ( txNameObj.txnameData )
        axisType = getAxisType ( validationPlot.axes )
        if axisType == "v2":
            from sympy import var
            x,y,z,w = var ( "x y z w" )
            axes = eval ( validationPlot.axes )
            for ctr,pt in enumerate(origdata):
                # masses = removeUnits ( pt[0], standardUnits=GeV )
                # n = int ( len(pt)/2 )
                masses = []
                offset = 0
                for ax in axes:
                    tmp = pt[offset:offset+len(ax)]
                    offset += len(ax)
                    masses.append ( tmp )
                # masses = [ pt[:n], pt[n:] ] ## silly hack for now
                coords = massPlane.getXYValues(masses)
                if not coords == None and not coords in ret:
                    ret.append ( coords )
        else:
            for ctr,masses in enumerate(origdata):
                print ( "masses", masses)
                coords = massPlane.getXYValues(masses)
                if not coords == None and not coords in ret:
                    ret.append ( coords )
    logger.info ( f"found {len(ret)} gridpoints" )
    ## we will need this for .dataToCoordinates
    return ret

def getGridPoints ( validationPlot ) -> List:
    """ retrieve the grid points of the upper limit / efficiency map.
    """
    ret = []
    axisType = getAxisType(validationPlot.axes)
    if axisType == "v2":
        return getGridPointsV2 ( validationPlot )
    massPlane = MassPlane.fromString( validationPlot.txName, validationPlot.axes )
    massesToCoords = {} ## cache the massesToCoords mapping
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
        origdata = convertOrigData ( txNameObj.txnameData )
        for ctr,cmasses in enumerate(origdata):
            if tuple(cmasses) in massesToCoords:
                continue
            masses = copy.deepcopy ( cmasses )
            ## FIXME not sure if this works for widths
            for i,mass in enumerate(masses):
                # info is, e.g.: (1,'mass',GeV)
                masses[i]=(i+1,mass)
            coords = massPlane.getXYValues(masses)
            massesToCoords[tuple(cmasses)] = coords
            if not coords == None and not coords in ret:
                ret.append ( coords )
    logger.info ( f"found {len(ret)} gridpoints" )
    ## we will need this for .dataToCoordinates
    return ret

def yIsLog ( validationPlot ):
    """ determine if to use log for y axis """
    logY = False
    if not "{" in validationPlot.axes: ## axis v2
        A = validationPlot.axes.replace(" ","")
        p1 = A.find("(")
        p2 = A.find(")")
        py = A.find("y")
        if py == -1:
            py = A.find("w")
        if p1 < py < p2 and A[py-1]==",":
            logY = True
        return logY
    # for v3 we look at the axis["y"] values
    yvalues = set()
    for d in validationPlot.data:
        if "axes" in d and "y" in d["axes"]:
            yvalues.add ( d["axes"]["y"] )
    if len(yvalues)>0:
        if 1e-40<max(yvalues)<1e-1:
            logY = True
    return logY
