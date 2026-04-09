#!/usr/bin/env python3

"""
.. module:: prettyMatplotlib
   :synopsis: the module for the "pretty" matplotlib-based plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

__all__ = [ "createPrettyPlot" ]

import logging,os,sys,random,copy
import numpy as np
# sys.path.append('../')
from array import array
import math,ctypes
logger = logging.getLogger(__name__)
from smodels.base.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname
from validationHelpers import prettyAxes
import matplotlib.ticker as ticker
from matplotlib.pyplot import contour
from smodels_utils.helper.terminalcolors import *
from plottingFuncs import yIsLog, getFigureUrl, getDatasetDescription, \
         getClosestValue, getAxisRange, isWithinRange, filterWithinRanges
from smodels_utils.plotting.plottingRecorder import importMatplot

try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass

from scipy import interpolate
from validationHelpers import getAxisType

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch

def shade_between_contours(cs1, cs2, ax=None,
                           facecolor='lightskyblue', alpha=0.12,
                           edgecolor='none', zorder=2,
                           close_tol=1e-12,
                           mode='auto'):
    """
    Shade the area between two contour sets, closing open contours in the
    shortest way possible.

    Modes
    -----
    - 'auto' (default):
        If each cs has exactly one open polyline, build a single ring by
        connecting nearest endpoints across the two lines (two shortest
        straight connectors) and fill it. Otherwise fall back to 'compound'.
    - 'cross':
        Force the two-connector ring between the (main) polyline from each cs.
    - 'compound':
        Close every subpath individually by a straight line from end to start
        (shortest closure for that subpath) and fill all with even-odd rule.
        This shades the symmetric difference of all closed loops.

    Parameters
    ----------
    cs1, cs2 : contour set-like
        Objects returned by plt.contour/ax.contour (or similar) that expose
        `. _paths`, `.allsegs`, or `.collections`.
    ax : matplotlib.axes.Axes, optional
        Target axes; defaults to current axes.
    facecolor : color, default 'lightskyblue'
        Fill color.
    alpha : float, default 0.12
        Transparency for an almost transparent look.
    edgecolor : color, default 'none'
        Edge color of the filled patch.
    zorder : int, default 2
        Z-order of the fill patch.
    close_tol : float, default 1e-12
        Tolerance to consider a path closed based on endpoints.
    mode : {'auto','cross','compound'}, default 'auto'
        See description above.

    Returns
    -------
    patch : matplotlib.patches.PathPatch
        The added patch.
    """

    if ax is None:
        ax = plt.gca()

    # -------------------- Utilities --------------------
    def to_path(obj):
        if isinstance(obj, Path):
            return obj
        if hasattr(obj, 'vertices'):
            v = np.asarray(obj.vertices)
            c = getattr(obj, 'codes', None)
            return Path(v, c)
        arr = np.asarray(obj)
        if arr.ndim == 2 and arr.shape[1] == 2:
            return Path(arr)
        return None

    def split_subpaths(p):
        # Split a Path with multiple MOVETO/CLOSEPOLY into simple polylines.
        v = np.asarray(p.vertices)
        c = p.codes
        if c is None:
            return [Path(v)]
        segs = []
        start = None
        curr = []
        for i, code in enumerate(c):
            if code == Path.MOVETO:
                if curr:
                    segs.append(Path(np.array(curr)))
                    curr = []
                start = v[i]
                curr = [v[i]]
            elif code == Path.LINETO:
                curr.append(v[i])
            elif code == Path.CLOSEPOLY:
                # CLOSEPOLY closes to the last MOVETO; we can make explicit
                if curr:
                    curr.append(curr[0])
                    segs.append(Path(np.array(curr)))
                    curr = []
                start = None
            else:
                # Treat unknown as LINETO
                curr.append(v[i])
        if curr:
            segs.append(Path(np.array(curr)))
        # Keep only segments with 2D points and at least 2 vertices
        out = []
        for s in segs:
            vv = np.asarray(s.vertices)
            if vv.ndim == 2 and vv.shape[0] >= 2 and vv.shape[1] == 2:
                out.append(Path(vv))
        return out if out else [Path(v)]

    def extract_paths(cs):
        paths = []
        if hasattr(cs, '_paths') and cs._paths is not None:
            for p in cs._paths:
                pp = to_path(p)
                if pp is not None:
                    paths.extend(split_subpaths(pp))
        elif hasattr(cs, 'allsegs') and cs.allsegs is not None:
            for seglist in cs.allsegs:
                for seg in seglist:
                    if seg is None:
                        continue
                    pp = to_path(seg)
                    if pp is not None:
                        paths.extend(split_subpaths(pp))
        elif hasattr(cs, 'collections'):
            for coll in cs.collections:
                if hasattr(coll, 'get_paths'):
                    for p in coll.get_paths():
                        paths.extend(split_subpaths(p))
        # Keep only paths with at least 2 vertices
        keep = []
        for p in paths:
            v = np.asarray(p.vertices)
            if v.ndim == 2 and v.shape[0] >= 2 and v.shape[1] == 2:
                keep.append(Path(v))
        return keep

    def is_closed(p):
        v = np.asarray(p.vertices)
        if v.shape[0] < 3:
            return False
        return np.allclose(v[0], v[-1], atol=close_tol, rtol=0.0)

    def close_shortest(p):
        # Shortest closure for one polyline: straight segment from end to start.
        if is_closed(p):
            return p
        v = np.asarray(p.vertices)
        if not np.allclose(v[0], v[-1], atol=close_tol, rtol=0.0):
            v = np.vstack([v, v[0]])
        codes = np.full(len(v), Path.LINETO, dtype=np.uint8)
        codes[0] = Path.MOVETO
        codes[-1] = Path.CLOSEPOLY
        return Path(v, codes)

    def path_length(v):
        v = np.asarray(v)
        if len(v) < 2: return 0.0
        d = v[1:] - v[:-1]
        return float(np.sqrt((d * d).sum(axis=1)).sum())

    def main_polyline(paths):
        # Pick the longest polyline
        if not paths:
            return None
        lengths = [path_length(p.vertices) for p in paths]
        return paths[int(np.argmax(lengths))]

    def endpoints(p):
        v = np.asarray(p.vertices)
        return v[0], v[-1]

    def orient(p, start_pt):
        v = np.asarray(p.vertices)
        if np.linalg.norm(v[0] - start_pt) <= np.linalg.norm(v[-1] - start_pt):
            return Path(v.copy())
        else:
            return Path(v[::-1].copy())

    def make_ring_from_two_open(p1, p2):
        # Build a single closed ring by connecting nearest endpoints across p1 and p2.
        a1, b1 = endpoints(p1)
        a2, b2 = endpoints(p2)
        d1 = np.linalg.norm(a1 - a2) + np.linalg.norm(b1 - b2)
        d2 = np.linalg.norm(a1 - b2) + np.linalg.norm(b1 - a2)
        if d1 <= d2:
            p1o = orient(p1, a1)  # a1 -> b1
            p2o = orient(p2, b2)  # b2 -> a2 (so we can go b1->b2 then p2o to a2)
            v1 = np.asarray(p1o.vertices)
            v2 = np.asarray(p2o.vertices)
            verts = np.vstack([
                v1,
                [v2[0]],   # connector b1->b2 (implicit straight segment)
                v2,
                [v1[0]]    # connector a2->a1 (implicit straight segment)
            ])
        else:
            p1o = orient(p1, a1)  # a1 -> b1
            p2o = orient(p2, a2)  # a2 -> b2 (so we can go b1->a2 then p2o to b2)
            v1 = np.asarray(p1o.vertices)
            v2 = np.asarray(p2o.vertices)
            verts = np.vstack([
                v1,
                [v2[0]],   # connector b1->a2
                v2[::-1],  # traverse to b2 -> a2, but we started at a2, so reverse to go to b2
                [v1[0]]    # connector b2->a1
            ])
        # Build closed Path
        codes = np.full(len(verts), Path.LINETO, dtype=np.uint8)
        codes[0] = Path.MOVETO
        codes[-1] = Path.CLOSEPOLY
        return Path(verts, codes)

    # -------------------- Extract and decide --------------------
    paths1 = extract_paths(cs1)
    paths2 = extract_paths(cs2)

    open1 = [p for p in paths1 if not is_closed(p)]
    open2 = [p for p in paths2 if not is_closed(p)]

    def add_patch_from_path(p):
        patch = PathPatch(p, transform=ax.transData,
                          facecolor=facecolor, edgecolor=edgecolor,
                          alpha=alpha, zorder=zorder)
        try:
            patch.set_fillrule('evenodd')
        except AttributeError:
            pass
        ax.add_patch(patch)
        return patch

    # Decide mode
    chosen_mode = mode
    if mode == 'auto':
        if len(open1) == 1 and len(open2) == 1 and len(paths1) == 1 and len(paths2) == 1:
            chosen_mode = 'cross'
        else:
            chosen_mode = 'compound'

    # -------------------- Build the fill --------------------
    if chosen_mode == 'cross':
        if not open1 or not open2:
            # Fallback if a closed loop slipped in: compound
            chosen_mode = 'compound'
        else:
            p1 = main_polyline(open1)
            p2 = main_polyline(open2)
            ring = make_ring_from_two_open(p1, p2)
            return add_patch_from_path(ring)

    # 'compound' path: close each subpath individually (shortest closure per path)
    closed_paths = [close_shortest(p) for p in paths1 + paths2]
    compound = Path.make_compound_path(*closed_paths)
    return add_patch_from_path(compound)

def pprint ( xs, ys, values, xrange = None, yrange = None ):
    """ pretty print the values, for debugging """
    for yi,line in enumerate ( values ):
        y = ys[yi]
        if not isWithinRange ( yrange, y ):
            continue
        for xi, value in enumerate ( line ):
            x = xs[xi]
            if not isWithinRange ( xrange, x ):
                continue
            # if not math.isnan ( value )  and y > x:
            print ( f"y={y:.1f} x={x:.1f} value {value:.3f}" )

def retrievePoints ( cs : contour ) -> list[list[dict]]:
    """ retrieve the points from the contour

    :param cs: matplotlib contour
    :returns: list of exclusion lines, where an exclusion line is
    a list of dictionaries with "x" and "y"
    """
    exclusion_lines = []
    x, y = [], []

    def exclusionLineFromPaths ( paths ):
        """ get exclusion line from matplotlib paths """
        exclusion_lines = []
        for paths in paths_cs:
            vertices_cs = paths.vertices
            l_x = vertices_cs[:,0].tolist()
            l_y = vertices_cs[:,1].tolist()
            exclusion_line = []
            if len(l_x)>0:
                for x,y, code in zip ( l_x, l_y, paths.codes ):
                    if code == 1:
                        if len(exclusion_line)>0:
                            exclusion_lines.append( exclusion_line )
                        exclusion_line = []
                    exclusion_line.append ( { "x": round(x,5), "y": round(y,5) } )
            if len(exclusion_line)>0:
                exclusion_lines.append ( exclusion_line )
        return exclusion_lines

    if hasattr ( cs, "collections" ) and len(cs.collections)>0:
        paths_cs = cs.collections[0].get_paths()  #collections[0] refers to the 1st level
        exclusion_lines = exclusionLineFromPaths ( paths_cs )
        return exclusion_lines

    if hasattr ( cs, "_paths" ):
        paths_cs = cs._paths  #collections[0] refers to the 1st level
        exclusion_lines = exclusionLineFromPaths ( paths_cs )
        return exclusion_lines
    return exclusion_lines

def createSModelSExclusionJson( all_lines : dict, validationPlot ):
    """ create the SModelS_ExclusionLines.json exclusion files """
    npoints = sum ( [len(x) for x in all_lines.values() ] )
    if npoints == 0:
        print( f"[prettyMatplotlib] {RED}Skipping creation of SModelS Exclusion JSON: no points{RESET}")
        return

    if not validationPlot.combine: plot_type = "bestSR"
    else: plot_type = "comb"
    axes = validationPlot.axes
    from validationHelpers import getAxisType, axisV2ToV3, getNiceAxes
    if getAxisType ( axes ) == "v2":
        axes = axisV2ToV3 ( axes )
    #store x,y points in json file
    d = {}
    for name,line in all_lines.items():
        sname = "obsExclusion"
        if "exp" in name:
            sname = "expExclusion"
        if "p1" in name:
            sname += "P1"
        if "m1" in name:
            sname += "M1"
        d[ sname ] = line
    plot_dict = { f"{validationPlot.txName}_{plot_type}_{axes}": d }
        
    vDir = validationPlot.getValidationDir (validationDir=None)
    file_js = "SModelS_ExclusionLines.json"
    import json
    plots = plot_dict
    for name,plot in plots.items():
        obsexcl = "obs_excl"
        if "obsExclusion" in plot:
            obsexcl = "obsExclusion"
        if len(plot[ obsexcl ])>0 and type(plot[ obsexcl ][0])==dict:
            print ( f"[prettyMatplotlib] trying to add v2 exclusion lines to v1 file. This doesnt work, but you can simply delete the old json file!" )
            sys.exit(-1)
    if os.path.exists(f"{vDir}/{file_js}"):
        file = open(f'{vDir}/{file_js}','r')
        try:
            plots = json.load(file)
            plots.update(plot_dict)
        except Exception as e:
            print ( f"[prettyMatplotlib] cannot read {vDir}/{file_js}: {e}" )
            sys.exit()

    plots["schema_version"]="2.0"

    print( f"[prettyMatplotlib] {MAGENTA}Creating SModelS Exclusion JSON at {vDir}/{file_js}: we have {npoints} points{RESET}")
    plots = cleanUpPlots ( plots )
    from smodels_utils.helper.various import py_dumps
    ds = py_dumps(plots, indent=4, stop_at_level = 5, double_quotes = True )
    file = open(f'{vDir}/{file_js}','w')
    file.write ( ds + "\n" )
    file.close()

def cleanUpPlots ( plots : dict ) -> dict:
    """ remove empty entries from the plots directory

    :returns: cleaned up dictionary
    """
    newplots = {}
    for plotName,plot in plots.items():
        for i in [ "expExclusion", "obsExclusion", "exp_excl", "obs_excl" ]:
            if i in plot and len(plot[i])==0:
                plot.pop ( i )
        if len(plot)>0:
            newplots[plotName]=plot
    return newplots

def interpolateOverMissing ( xs, ys, T, fill_value : float = float("nan"),
       method : str = "linear" ) -> np.ndarray:
    """ idea copied from
    https://stackoverflow.com/questions/37662180/interpolate-missing-values-2d-python
    interpolate over missing values (nans)
    :param fill_value: what to fill outside of convex hull with
    :param method: one of: cubic, nearest, linear
    """
    image = np.asarray ( T )
    mask = np.isnan ( T )
    from scipy import interpolate

    h, w = image.shape[:2]
    xx, yy = np.meshgrid(np.arange(w), np.arange(h))
    def pluginValues ( indices, values ):
        """ translate list of indices to list of values """
        return [ values[x] for x in indices ]

    known_x = xx[~mask]
    if len(known_x) == 0:
        logger.debug ( "we have no known_x values" )
        return image
    known_y = yy[~mask]
    known_v = image[~mask]
    missing_x = xx[mask]
    missing_y = yy[mask]
    vknown_x = pluginValues ( known_x, xs )
    vknown_y = pluginValues ( known_y, ys )
    vmissing_x = pluginValues ( missing_x, xs )
    vmissing_y = pluginValues ( missing_y, ys )

    interp_image = image.copy()
    try:
        interp_values = interpolate.griddata(
            (vknown_x, vknown_y), known_v, (vmissing_x, vmissing_y),
            method=method, fill_value=fill_value)

        interp_image[missing_y, missing_x] = interp_values
    except Exception as e:
        logger.error ( f"interpolation over missing failed: {e}" )
    return interp_image

def createSModelSExclusionJsonV1( all_lines, validationPlot ):
    """ create the SModelS_ExclusionLines.json exclusion files,
    this is the old version, all exclusion lines merged, x and y separated,
    no schema_version """
    xobs, yobs, xexp, yexp = [[]], [[]], [[]], [[]]
    for excl_line in all_lines["obs"]:
        for pt in excl_line:
            xobs[0].append ( pt["x"] )
            yobs[0].append ( pt["y"] )
    for excl_line in all_lines["exp"]:
        for pt in excl_line:
            xexp[0].append ( pt["x"] )
            yexp[0].append ( pt["y"] )
    if len(xobs)==0 and len(xexp)==0:
        print( f"[prettyMatplotlib] {RED}Skipping creation of SModelS Exclusion JSON: no points{RESET}")
        return

    if not validationPlot.combine: plot_type = "bestSR"
    else: plot_type = "comb"
    axes = validationPlot.axes
    #store x,y points in json file
    plot_dict = {f"{validationPlot.txName}_{plot_type}_{axes}": {"obsExclusion":{'x':xobs,'y':yobs}, "expExclusion":{'x':xexp, 'y':yexp}}}
    vDir = validationPlot.getValidationDir (validationDir=None)
    file_js = "SModelS_ExclusionLines.json"
    import json
    plots = plot_dict
    for name,plot in plots.items():
        if type(plot["obsExclusion"][0])==list:
            print ( f"[prettyMatplotlib] trying to add v1 exclusion lines to v2 file. Correct!" )
            sys.exit(-1)
    if os.path.exists(f"{vDir}/{file_js}"):
        file = open(f'{vDir}/{file_js}','r')
        try:
            plots = json.load(file)
            plots.update(plot_dict)
        except Exception as e:
            print ( f"[prettyMatplotlib] cannot read {vDir}/{file_js}: {e}" )
            sys.exit()

    npoints = 0
    if len(xobs)>0:
        npoints = len(xobs[0])
    plots["schema_version"]="1.0"

    print( f"[prettyMatplotlib] {MAGENTA}Creating SModelS Exclusion JSON at {vDir}/{file_js}: we have {npoints} points{RESET}")

    file = open(f'{vDir}/{file_js}','w')
    json.dump(plots,file,indent=4)
    file.close()

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
    plt = importMatplot ( options["recordPlotCreation"] )
    # Check if data has been defined:
    xrange = getAxisRange ( options, "xaxis" )
    yrange = getAxisRange ( options, "yaxis" )
    tgr, etgr, tgrchi2 = [], [], []
    etgr_p1, etgr_m1 = [], []
    kfactor=None
    xlabel, ylabel, zlabel = 'x [GeV]','y [GeV]', r"$r = \sigma_{signal}/\sigma_{UL}$"
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
    if not hasYValues:
        logger.info ( "it seems like we do not have y-values, so we break off." )
        plt.dontplot = True
        return plt,None

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
        if not "axes" in pt:
            ## try to get axes from slha file
            pt["axes"] = validationPlot.getXYFromSLHAFileName ( pt["slhafile"], asDict=True )
        xvals = pt['axes']
        if xvals == None: ## happens when not on the plane I think
            continue
        if (not "UL" in pt.keys() or pt["UL"]==None) and (not "error" in pt.keys()):
            logger.warning( f"no UL for {xvals}: {pt}" )
        r, rexp = float("nan"), float("nan")
        rexp_p1, rexp_m1 = float("nan"), float("nan")
        if not "error" in pt.keys():
            if pt["UL"]!=None:
                if type(pt["UL"])==str:
                    # for float("inf"), float("nan")
                    pt["UL"]=eval(pt["UL"])
                r = pt['signal']/pt ['UL']
            if "eUL" in pt:
                if type(pt["eUL"])==str:
                    # for float("inf"), float("nan")
                    pt["eUL"]=eval(pt["eUL"])
                if pt["eUL"] != None and pt["eUL"] > 0.:
                    hasExpected = True
                    rexp = pt['signal']/pt ['eUL']
                if "eUL_p1" in pt and pt["eUL_p1"] != None and pt["eUL_p1"] > 0.:
                    rexp_p1 = pt['signal']/pt ['eUL_p1']
                if "eUL_m1" in pt and pt["eUL_m1"] != None and pt["eUL_m1"] > 0.:
                    rexp_m1 = pt['signal']/pt ['eUL_m1']
        if options["significances"]:
            ### dont plot r, plot Z!
            r = float("nan") ## better draw nothing than r instead of Z
            from validationHelpers import significanceFromNLLs
            if not "nll" in pt or not "nll_SM" in pt:
                if not "nll_SM" in pt:
                    # its only weird if only nll_SM is missing
                    logger.error ( f"asked for significances but no nll_SM in {pt['axes']}!" )
                # sys.exit()
            else:
                Z = significanceFromNLLs ( pt["nll_SM"], pt["nll"] )
                r = Z
            # print ( f"Z({xvals['x']:.1f},{xvals['y']:.1f})={Z:.2f}, nll_SM={pt['nll_SM']:.2g} nll_BSM={pt['nll']:.2g}" )
        if r > 3.:
            r=3.
        if rexp > 3.:
            rexp=3.
        if isinstance(xvals,dict):
            if not "x" in xvals: #cant do nothing with this
                continue
            if len(xvals) == 1:
                x,y = xvals['x'],r
                if logY:
                    y = np.log10 ( y )
                ylabel = r"r = $\sigma_{signal}/\sigma_{UL}$"
            else:
                x = xvals["x"]
                if "y" in xvals:
                    y = xvals['y']
                    if y == "stable":
                        y=1e-26
                    if logY and type(y) not in [ str ]:
                        y = np.log10 ( y )
                elif "w" in xvals:
                    y = xvals['w']

        else:
            x,y = xvals
            if logY:
                y = np.log10 ( y )
        if not isWithinRange ( xrange, x ):
            continue
        if not isWithinRange ( yrange, y ):
            continue

        if "condition" in pt.keys() and pt['condition'] and pt['condition'] > 0.05:
            condV += 1
            if condV < 5:
                logger.warning(f"Condition violated for file {pt['slhafile']}")
            if condV == 5:
                logger.warning("Condition violated for more points (not shown)")
        else:
            if not "error" in pt.keys():
                tgr.append( { "i": len(tgr), "x": x, "y": y, "r": r })
                if np.isfinite ( rexp ):
                    etgr.append( { "i": len(etgr), "x": x, "y": y, "r": rexp } )
                if np.isfinite ( rexp_p1 ):
                    etgr_p1.append( { "i": len(etgr), "x": x, "y": y, "r": rexp_p1 } )
                if np.isfinite ( rexp_m1 ):
                    etgr_m1.append( { "i": len(etgr), "x": x, "y": y, "r": rexp_m1 } )
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
    exs_p1 = get( "x", etgr_p1 )
    exs_m1 = get( "x", etgr_m1 )
    eys = get( "y", etgr )
    eys_p1 = get( "y", etgr_p1 )
    eys_m1 = get( "y", etgr_m1 )
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
    resultType = f"{str(types)}"
    if len ( validationPlot.expRes.datasets ) > 1 and validationPlot.combine:
        hasCombinedInfo = False
        for i in [ "covariance", "jsonFiles", "mlModels" ]:
            if hasattr ( validationPlot.expRes.globalInfo, i ):
                hasCombinedInfo = True
                resultType = "combined"
        if not hasCombinedInfo:
            resultType = "efficiencyMap"
    title = f"{title} ({resultType})"

    plt.dontplot = False
    plt.clf()

    #Draw temp plot:
    rs = get ( "r", tgr )
    ers = get ( "r", etgr )
    ers_p1 = get ( "r", etgr_p1 )
    ers_m1 = get ( "r", etgr_m1 )
    Z, eZ = {}, {}
    eZ_p1 = {}
    eZ_m1 = {}
    for t in tgr:
        x,y,r = t["x"],t["y"],t["r"]
        if not isWithinRange ( yrange, y ):
            continue
        if not isWithinRange ( xrange, x ):
            continue
        if not x in Z:
            Z[x]={}
        Z[x][y]=float(r)
    for t in etgr:
        x,y,r = t["x"],t["y"],t["r"]
        if not isWithinRange ( yrange, y ):
            continue
        if not isWithinRange ( xrange, x ):
            continue
        if not x in eZ:
            eZ[x]={}
        eZ[x][y]=float(r)
    for t in etgr_p1:
        x,y,r = t["x"],t["y"],t["r"]
        if not isWithinRange ( yrange, y ):
            continue
        if not isWithinRange ( xrange, x ):
            continue
        if not x in eZ_p1:
            eZ_p1[x]={}
        eZ_p1[x][y]=float(r)
    for t in etgr_m1:
        x,y,r = t["x"],t["y"],t["r"]
        if not isWithinRange ( yrange, y ):
            continue
        if not isWithinRange ( xrange, x ):
            continue
        if not x in eZ_m1:
            eZ_m1[x]={}
        eZ_m1[x][y]=float(r)
    xs = list ( Z.keys() )
    xs.sort( )
    T, eT = [], []
    eT_p1, eT_m1 = [], []
    ys = list ( set ( ys ) )
    ys.sort( )
    # ys.sort( reverse = True )
    for y in ys:
        tmp, etmp = [], []
        etmp_p1, etmp_m1 = [], []
        if not isWithinRange ( yrange, y ):
            continue
        for x in xs:
            if not isWithinRange ( xrange, x ):
                continue
            r, er = float("nan"), float("nan")
            er_p1, er_m1 = float("nan"), float("nan")
            if x in Z and y in Z[x]:
                r = Z[x][y]
            if x in eZ and y in eZ[x]:
                er = eZ[x][y]
            if x in eZ_p1 and y in eZ_p1[x]:
                er_p1 = eZ_p1[x][y]
            if x in eZ_m1 and y in eZ_m1[x]:
                er_m1 = eZ_m1[x][y]
            tmp.append ( r )
            etmp.append ( er )
            etmp_p1.append ( er_p1 )
            etmp_m1.append ( er_m1 )
            rs.append ( r )
            ers.append ( er )
            ers_p1.append ( er_p1 )
            ers_m1.append ( er_m1 )
        T.append ( tmp )
        eT.append ( etmp )
        eT_p1.append ( etmp_p1 )
        eT_m1.append ( etmp_m1 )

    interpolation = options["interpolationType"]
    #print ( "before" )
    # pprint ( xs, ys, T ) #, xrange=(500,1000), yrange=(800,900) )
    T = interpolateOverMissing ( xs, ys, T, float("nan"), interpolation )
    vT = interpolateOverMissing ( xs, ys, T, -10., interpolation )
    eT = interpolateOverMissing ( xs, ys, eT, -10., interpolation )
    eT_p1 = interpolateOverMissing ( xs, ys, eT_p1, -10., interpolation )
    eT_m1 = interpolateOverMissing ( xs, ys, eT_m1, -10., interpolation )
    ax = plt.gca()
    fig = plt.gcf()
    if logY:
        xlabel = "x [mass, GeV]"
        ylabel = "y [width, GeV]"
        ytick_loc = range( int(np.floor(min(ys))),int(np.ceil(max(ys)))+1 )
        ax.set_yticks ( ytick_loc )
        # ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: '1e{:d}'.format(y)))
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f'$10^{{{y:d}}}$' ))
    from plottingFuncs import getColormap
    cm = getColormap()
    xtnt = ( min(xs), max(xs), min(ys), max(ys) )
    # print ( "after" )
    # pprint ( xs, ys, T ) # , xrange=(500,1000), yrange=(800,900) )
    # shading is one of: 'gouraud', 'nearest', 'flat', 'auto'
    im = plt.pcolormesh ( xs, ys, T, cmap = cm, vmax=3., vmin = 0.,
                          shading="nearest" )
    plt.title ( title )
    # plt.text ( .28, .85, title, transform = fig.transFigure )
    plt.xlabel ( xlabel )
    plt.ylabel ( ylabel )

    for p in validationPlot.officialCurves:
        if "name" in p and "P1" in p["name"] or "M1" in p ["name"]:
            continue
        if type(p) not in [ dict ]:
            logger.error ( "exclusion lines are not dicts, are you sure you are not using sms.root files?" )
            continue
        px, py = filterWithinRanges ( p["points"], xrange, yrange, True )
        if logY:
            py = [ np.log10(y) for y in py ]
        plt.plot ( px, py, c="black", label="exclusion (official)" )
    if options["drawExpected"]:
        for p in validationPlot.expectedOfficialCurves:
            if "P1" in p["name"] or "M1" in p ["name"]:
                continue
            if type(p) not in [ dict ]:
                logger.error ( "exclusion lines are not dicts, are you sure you are not using sms.root files?" )
                continue
            px, py = filterWithinRanges ( p["points"], xrange, yrange, True )
            if logY:
                py = [ np.log10(y) for y in py ]
            plt.plot ( px, py, c="black", linestyle="dotted",
                       label="exp. excl. (official)" )
    plt.colorbar ( im, label=zlabel, fraction = .046, pad = .04 )
    try:
        from scipy.ndimage.filters import gaussian_filter
        T = gaussian_filter( T, 1. )
    except:
        pass
    if not options["significances"]:
        cs = plt.contour( xs, ys, vT, colors="blue", levels=[1.], extent = xtnt, origin="image" )
        ## smodels exclusions dont make sense for the significances plot
        csl = plt.plot([-1,-1],[0,0], c = "blue", label = "exclusion (SModelS)",
                  transform = fig.transFigure )
        #convert contour to a list of x,y values

        excl_lines = retrievePoints ( cs )
        exp_excl_lines = []

        all_lines = { "obs": excl_lines }

        if options["drawExpected"] in [ "auto", True ] and not np.all ( np.isnan(eT) ):
            cs = plt.contour( xs, ys, eT, colors="blue", linestyles = "dotted", levels=[1.],
                              extent = xtnt, origin="image" )
            ecsl = plt.plot([-1,-1],[0,0], c = "blue", label = "exp. excl. (SModelS)",
                            transform = fig.transFigure, linestyle="dotted" )
            exp_excl_lines = retrievePoints ( cs )
            all_lines["exp"] = exp_excl_lines

            if True:
                cs_m1 = plt.contour( xs, ys, eT_m1, colors="blue", 
                        linestyles = "dotted", levels=[1.],
                        extent = xtnt, origin="image",
                        linewidths = 1, alpha = 0.5, zorder = 10 )
                exp_excl_lines_m1 = retrievePoints ( cs_m1 )
                all_lines["exp_m1"] = exp_excl_lines_m1

                cs_p1 = plt.contour( xs, ys, eT_p1, colors="blue", 
                        linestyles = "dotted", levels=[1.],
                        extent = xtnt, origin="image",
                        linewidths = 1, alpha = 0.5, zorder = 10 )
                exp_excl_lines_p1 = retrievePoints ( cs_p1 )
                all_lines["exp_p1"] = exp_excl_lines_p1

                # shade_between_contours ( cs_m1, cs_p1, alpha=0.3 )

        if options["createSModelSExclJson"]:
            writeV1Format = False
            if writeV1Format:
                # thats the old format, list of x values, list of y values
                createSModelSExclusionJsonV1( all_lines, validationPlot )
            else:
                createSModelSExclusionJson( all_lines, validationPlot )

    pName = prettyTxname(validationPlot.txName, outputtype="latex" )
    if pName == None:
        pName = "define {validationPlot.txName} in prettyDescriptions"
    backend = ""
    if hasattr ( validationPlot.expRes.globalInfo, "comment" ):
        comment = validationPlot.expRes.globalInfo.comment.lower()
        if "colliderbit" in comment:
            backend = "ColliderBit"
        if "ma5" in comment or "madanalysis" in comment:
            backend = "MA5"
        if "checkmate2" in comment:
            backend = "CheckMate2"
        if "checkmate" in comment:
            backend = "CheckMate"
        if "adl" in comment or "cutlang" in comment:
            backend = "CutLang"
    if backend!="":
        plt.text(.2,.0222,f"backend: {backend}",transform=fig.transFigure,
                 fontsize=9 )
    txStr = f"{validationPlot.txName}: {pName}"
    plt.text(.03,.965,txStr,transform=fig.transFigure, fontsize=9 )
    axStr = prettyAxes(validationPlot)
    axStr = axStr.replace("*","")
    axStr = axStr.replace("0.5",".5")
    axStr = axStr.replace("100.","100")
    axStr = axStr.replace("anyBSM","*")
    plt.text(.95,.965,axStr,transform=fig.transFigure, fontsize=9,
               horizontalalignment="right" )
    figureUrl = getFigureUrl(validationPlot)

    subtitle = getDatasetDescription ( validationPlot, 35 )
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
    plt.text ( .97, .0222, subtitle, transform=fig.transFigure, fontsize=10,
               horizontalalignment="right" )

    #if figureUrl:
    if False:
        plt.text( .13, .13, f"{figureUrl}",
                  transform=fig.transFigure, c = "blue", fontsize = 6 )

    if kfactor is not None and abs ( kfactor - 1.) > .01:
        plt.text( .13,.83, f"k-factor = {kfactor:.2f}", fontsize=10,
                  c="gray", transform = fig.transFigure )
    if options["preliminary"] not in [ False, "False", "false", "0", None ]:
        text = options["preliminary"]
        if text.lower() in [ "true", "1", "yes" ]:
            text = "SModelS preliminary"
        fontsize = 20
        if len(text)>20:
            fontsize = 16
        ## preliminary label, pretty plot
        t = plt.text ( .3, .22, text, transform=fig.transFigure,
                   rotation = 35., fontsize = fontsize, c="red", zorder=100 )
        t.set_bbox(dict(facecolor='white', alpha=0.5, linewidth=0))
    legendplacement = options["legendplacement"]
    legendplacement = legendplacement.replace("bottom","lower")
    legendplacement = legendplacement.replace("top","upper")
    if legendplacement in [ "automatic", None, "", "none" ]:
        legendplacement = "best"
    plt.legend( loc=legendplacement ) # could be upper right
    plt.grid(visible=False)

    if not silentMode:
        ans = raw_input("Hit any key to close\n")

    if False: ## if you want to tweak the pickle file
        f = open ( "trying.pcl", "wb" )
        import pickle
        pickle.dump ( plt.gcf(), f )
        f.close()
    return plt,tgr
