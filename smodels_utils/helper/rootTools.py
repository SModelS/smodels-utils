#!/usr/bin/env python3

"""
.. module:: rootTools
        :synopsis: Collection of methods used in the context of ROOT

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import logging as logger

def getRootVersion ( astuple=False, useimport=False ):
    """ get the ROOT version from root-config

        :param astuple: false returns string, true returns tuple of integers.
        :returns: ROOT version
    """
    if useimport: return getRootVersionFromImport_(astuple)
    import setPath
    try:
        import subprocess
        S=subprocess.getoutput("root-config --version")
        if S.find("not found")>-1:
            logger.error ( S )
            return None
        if not astuple: return S
        return tupelizeVersion ( S )
    except Exception as e:
        logger.error ( e )
        return None

def boundingBoxIsFinite ( bb ):
    """ check if bounding box produced via getBoundingBox is legit """
    import math
    for var in [ "x", "y" ]:
        for i in [ 0, 1 ]:
            if not math.isfinite ( bb[var][i] ):
                return False
    return True

def destroyRoot():
    """ its one of the ROOT wtf's
    :returns: true, if it found ROOT and destroyed it, else false
    """
    try:
        import ROOT
    except ImportError as e:
        # logger.warning ( "could not import ROOT" )
        return False
    for i in ROOT.gROOT.GetListOfCanvases():
        i.Destructor()
    return True

def addROOTPointInFront ( curve, x, y ):
    """ add a point at position 0 in tgraph """
    #import ROOT
    n=curve.GetN()+1
    import ctypes
    xt,yt=ctypes.c_double(),ctypes.c_double()
    xtn,ytn=x,y
    for i in range(n):
        curve.GetPoint(i,xt,yt)
        curve.SetPoint(i,xtn,ytn)
        xtn,ytn=xt.value,yt.value

def printROOTCurve ( curve ):
    n=curve.GetN()
    xt,yt=ctypes.c_double(),ctypes.c_double()
    indices = list(range(3))+list(range(n-3,n))
    for i in indices:
        curve.GetPoint(i,xt,yt)
        y = copy.deepcopy(yt)
        if y < 0.:
            y = unscaleWidth(y)
        #if 0. < y < 1e-6:
        #    y = unscaleWidth(y)
        # print ( "%d: %f,%f" % ( i, xt, y ) )
        # print ( "%d: %f,%g" % ( i, xt, y ) )

def completeROOTGraph ( curve ):
    """ complete the given graph at the ends to cross the axes """
    if type(curve) == dict:
        from smodels_utils.helper.rootTools import exclusionCurveToTGraph
        curve = exclusionCurveToTGraph ( curve )
    if not ( curve.GetN() > 3 ):
        print ( f"problem, i am trying to complete a graph with {int(curve.GetN())} points" )
    if curve.GetN() <= 3:
        return
    import ctypes
    x1,y1=ctypes.c_double(),ctypes.c_double()
    x2,y2=ctypes.c_double(),ctypes.c_double()
    xl,yl=ctypes.c_double(),ctypes.c_double()
    # first compute k of the first three points
    curve.GetPoint ( 0, x1, y1 ) ## get first point
    curve.GetPoint ( 2, x2, y2 ) ## get third point
    curve.GetPoint ( curve.GetN()-1, xl, yl ) ## get last point
    if (( x1.value - xl.value )**2 + ( y1.value - yl.value ) ** 2 ) < 50.:
        ## need not completion
        return
    logY=False
    ax1, ay1 = x1.value, y1.value
    ax2, ay2 = x2.value, y2.value
    tx1, ty1 = x1.value, y1.value
    if max(abs(ay2),abs(ay1))<1e-6:
        logY=True
        ay2 = rescaleWidth(ay2)
        ay1 = rescaleWidth(ay1)
    if ax2 == ax1:
        ax2 = ax1 + 1e-16
    dx = ax2 - ax1
    if dx == 0.:
        dx=1e-6
    k = (ay2 - ay1) / dx
    if abs(k) > 1:
        ## the curve is more vertical -- close with the x-axis (y=0)
        addROOTPointInFront ( curve, tx1, 0. )
    else:
        ## the curve is more horizontal -- close with the y-axis (x=0)
        addROOTPointInFront ( curve, 0., ty1 )

    n = curve.GetN()
    curve.GetPoint ( n-3, x1, y1 ) ## get third last point
    curve.GetPoint ( n-1, x2, y2 ) ## get last point
    #tx1, ty1 = copy.deepcopy(x1), copy.deepcopy(y1)
    #tx2, ty2 = copy.deepcopy(x2), copy.deepcopy(y2)
    tx1, ty1 = x1.value, y1.value
    tx2, ty2 = x2.value, y2.value
    if logY:
        ty2 = rescaleWidth(ty2)
        ty1 = rescaleWidth(ty1)
    if tx2 == tx1:
        tx2 = tx1 + 1e-16
    k = 99999.
    if tx2 != tx1:
        k = (ty2 - ty1) / ( tx2 - tx1 )
    if k > 1 or k < -1:
        ## the curve is more vertical -- close with the x-axis (y=0)
        curve.SetPoint ( n, tx2, 0. )
    elif k < 0:
        ## the curve is more horizontal -- close with the y-axis (x=0)
        curve.SetPoint ( n, tx2, 0. )
    else:
        ## the curve is more horizontal -- close with the y-axis (x=0)
        curve.SetPoint ( n, 0., ty2 )
    curve.SetPoint ( n+1, 0., 0. )

def getBoundingBox ( graph ):
    """ from graph or container of graphs, return 2d bounding box
    :param graph: a TGraph, or a container of them
    :returns: a dict, { "x": [ xmin, xmax ], "y": [ ymin, ymax ] }
    """
    inf = float("inf")
    if type(graph) in [ list, tuple ]:
        ret = { "x": [ inf, -inf ], "y": [ inf, -inf ] }
        for g in graph:
            bb = getBoundingBox ( g )
            for var in [ "x", "y" ]:
                if bb[var][0] < ret[var][0]:
                    ret[var][0] = bb[var][0]
                if bb[var][1] > ret[var][1]:
                    ret[var][1] = bb[var][1]
        return ret
    ret = { "x": [ inf, -inf ], "y": [ inf, -inf ] }
    n = int ( graph.GetN() )
    import ctypes
    x, y = ctypes.c_double(), ctypes.c_double()
    for i in range(n):
        graph.GetPoint ( i, x, y )
        if x.value < ret["x"][0]:
            ret["x"][0] = x.value
        if x.value > ret["x"][1]:
            ret["x"][1] = x.value
        if y.value < ret["y"][0]:
            ret["y"][0] = y.value
        if y.value > ret["y"][1]:
            ret["y"][1] = y.value
    return ret

def getRootVersionFromImport_ ( astuple=False ):
    """ get the ROOT version from python import.

        :param astuple: false returns string, true returns tuple of integers.
        :returns: ROOT version
    """
    import logging
    log = logging.getLogger(__name__)
    try:
        import ROOT
        S=ROOT.gROOT.GetVersion()
        if not astuple: return S
        return tupelizeVersion ( S )
    except Exception as e:
        log.error ( e )
        return None


def tupelizeVersion ( S ):
    T,C=S.split("/")
    A,B=T.split(".")
    return (int(A),int(B),int(C))

def getRootPath ( ):
    """ get the ROOT path, first try via root-config, then query ROOTSYS
        :returns: ROOT path
    """
    import logging
    log = logging.getLogger(__name__)
    try:
        import subprocess
        out=subprocess.getoutput("root-config --prefix")
        if out.find("not found")>-1:
            log.info ( out )
            import os
            ret=os.getenv("ROOTSYS")
            if not ret:
                log.error ( "ROOTSYS not set, either" )
            return None
        else:
            return out
    except Exception as e:
        log.error ( e )
        return None

def getRootLibraryPath ( ):
    """ get the ROOT library path, first try via root-config, then systematically
            try candidate paths.

        :returns: ROOT library path
    """
    import logging
    log = logging.getLogger(__name__)
    try:
        import subprocess
        out=subprocess.getoutput("root-config --libdir")
        if out.find("not found")>-1:
            log.info ( out )
            import os
            ret=os.getenv("ROOTSYS")
            for Dir in [ "lib/x86_64-linux-gnu", "lib64/root", "lib/root" ]:
                F=f"{ret}/{Dir}/libRint.so"
                if os.path.exists ( F ):
                    return F
            log.error ( "no suitable libdir found." )
            return None
        else:
            return out
    except Exception as e:
        log.error ( e )
        return None

def getRootPythonPath ( ):
    """ get the ROOT python path, via .getRootLibraryPath() and .getRootVersion().

        :returns: ROOT python path
    """
    import os
    version = getRootVersion(True)
    libpath = getRootLibraryPath()
    if not version or not libpath:
        return None
    V=f"{version[0]!s}.{version[1]!s}"
    for SubDir in [ V, f"root{V}" ,""]:
        Dir=f"{libpath}/{SubDir}"
        if os.path.exists ( f"{Dir}/ROOT.py" ):
            return Dir
    return None

def getTGraphFromContour(exclhisto):
    """ returns the contour of an exclusion histogram as TGraph"""
    import ROOT
    ROOT.gROOT.SetBatch()
    c1 = ROOT.TCanvas()
    c1.cd()
    exclhisto.Draw("CONT LIST")
    ROOT.gPad.Update()
    ROOT.gROOT.GetListOfSpecials().ls()
    gr = ROOT.gROOT.GetListOfSpecials().FindObject('contours')('TList').At(0)
    return gr

def useNiceColorPalette( palette="temperature", f=0., ngradientcolors=20 ):
    """ create a fine-grained temperature color palette,

            :param palette: which palette. values are temperature, blackwhite, darkbody, deepsea, blueyellow, rainbow, inverteddarkbody, yellowpurple, greenpurple, bluepurple
            :type palette: str
            :param ngradientcolors: how many colors
            :type ngradientcolors: int
            :param f: 0 means full color, 0.5 lighter palette, 1.0 all white
            :type f: float
    """
    from array import array
    import ROOT
    foundpalette=False
    stops,red,green,blue=[],[],[],[]
    if palette=="brown":
        foundpalette=True
        stops = [0.0, 0.5, 0.75, 1.0 ]
        red     = [106./256, 0.38, 1.00, 1.0 ]
        green = [44. /256, 0.21, 0.81, 0.9 ]
        blue    = [0.05 , 0.07, 0.05, 0.05 ]
    if palette=="temperature":
        foundpalette=True
        stops = [0.00, 0.34, 0.61, 0.84, 1.00]
        red     = [0.00, 0.00, 0.87, 1.00, 0.51]
        green = [0.00, 0.91, 1.00, 0.20, 0.00]
        blue    = [0.51, 1.00, 0.12, 0.00, 0.00]
    if palette=="yellowpurple":
        foundpalette=True
        red = [ 0., 0.0, 1.0, 1.0, 1.0 ]
        green = [ 0., 0.0, 0.0, 1.0, 1.0 ]
        blue    = [ 0., 1.0, 0.0, 0.0, 1.0 ]
        stops = [ 0., .25, .50, .75, 1.0 ]
    if palette=="greenpurple":
        foundpalette=True
        red = [ 1.00, 0.50, 0.00 ]
        green = [ 0.50, 0.00, 1.00 ]
        blue    = [ 1.00, 0.00, 0.50 ]
        stops = [ 0.00, 0.50, 1.00 ]
    if palette=="bluepurple":
        foundpalette=True
        red     = [ 1.00, 0.00, 0.00 ]
        green = [ 0.00, 1.00, 0.00 ]
        blue    = [ 1.00, 0.00, 1.00 ]
        stops = [ 0.00, 0.50, 1.00 ]

    if foundpalette:
        if f!=None and f>0.0:
            for (i,r) in enumerate(red):
                r=1-(1.0-r)*f
                red[i]=r
            for (i,r) in enumerate(green):
                r=1-(1.0-r)*f
                green[i]=r
            for (i,r) in enumerate(blue):
                r=1-(1.0-r)*f
                blue[i]=r
        s = array('d', stops)
        r = array('d', red)
        g = array('d', green)
        b = array('d', blue)
        nstops = len(s)
        ROOT.TColor.CreateGradientColorTable(nstops, s, r, g, b, ngradientcolors )
        ROOT.gStyle.SetNumberContours( ngradientcolors )
        ROOT.gStyle.cd()
    if palette=="deepsea":
        foundpalette=True
        ROOT.gStyle.SetPalette(51) ## black-and-white
    if palette=="blackwhite":
        foundpalette=True
        ROOT.gStyle.SetPalette(52) ## black-and-white
    if palette=="darkbody":
        foundpalette=True
        ROOT.gStyle.SetPalette(53)
    if palette=="blueyellow":
        foundpalette=True
        ROOT.gStyle.SetPalette(54)
    if palette=="rainbow":
        foundpalette=True
        ROOT.gStyle.SetPalette(55)
    if palette=="inverteddarkbody":
        foundpalette=True
        ROOT.gStyle.SetPalette(56)
    if not foundpalette:
        print ( "[rootTools.py] error: did not find palette %s. Existing palettes are: temperature, blackwhite, darkbody, deepsea, blueyellow, rainbow, inverteddarkbody" )

def setROOTColorPalette():
    try:
        import ROOT
    except ImportError as e:
        # logger.warning ( "could not import ROOT" )
        return
    #Set nice ROOT color palette for temperature plots:
    stops = [0.00, 0.34, 0.61, 0.84, 1.00]
    red   = [0.00, 0.00, 0.87, 1.00, 0.51]
    green = [0.00, 0.81, 1.00, 0.20, 0.00]
    blue  = [0.51, 1.00, 0.12, 0.00, 0.00]
    from array import array
    s = array('d', stops)
    r = array('d', red)
    g = array('d', green)
    b = array('d', blue)
    ROOT.TColor.CreateGradientColorTable(len(s), s, r, g, b, 999)
    ROOT.gStyle.SetNumberContours(999)

def exclusionCurveToTGraph ( args ):
    """ create ROOT TGraph objects from args.
    :param args: can be a list of dictionaries, or a single dictionary.
                 dictionary should contain "points" and "name".
    :returns: ROOT.TGraph object
    """
    if type(args) in [ list, tuple ]:
        ret = []
        for x in args:
            ret.append ( exclusionCurveToTGraph ( x ) )
        return ret
    import ROOT
    if type(args)== ROOT.TGraph:
        return args
    name = args["name"]
    points = args["points"]
    tgraph = ROOT.TGraph()
    tgraph.SetTitle ( name )
    if not "y" in points:
        ctr = 0
        for x_ in points["x"]:
            for y_ in [ 0., 1., 2. ]:
                tgraph.SetPointX( ctr, x_ )
                tgraph.SetPointY( ctr, y_ )
                ctr+=1
    else:
        for i,(x_,y_) in enumerate ( zip ( points["x"], points["y"] ) ):
            tgraph.SetPointX( i, x_ )
            tgraph.SetPointY( i, y_ )
    return tgraph

if __name__ == "__main__":
    """ as a script, we simply print out the paths """
    print ( "We're using ROOT version",getRootVersion() )
    print ( "ROOT path",getRootPath() )
    print ( "ROOT library path",getRootLibraryPath() )
    print ( "ROOT python path",getRootPythonPath() )
