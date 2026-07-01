#!/usr/bin/env python3

""" the plotting script for the red-black pretty paper plot
"""

__all__ = [ "drawPrettyPaperPlot" ]

import os, random
import matplotlib.pyplot as plt
import numpy as np
from numpy import array
import json, tokenize, sys
import matplotlib.lines as mlines
from smodels.base.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxesV2
from validationHelpers import getAxisType, prettyAxes, axisV2ToV3, getNiceAxes
import matplotlib.ticker as ticker
from smodels_utils.helper.terminalcolors import *
from typing import Union, Optional, Tuple

def countRegionsOfType ( regions : list, regionType : str = "SR" ) -> int:
    """ count the number of control regions
    :param regionType: one of: SR, CR, VR
    """
    ctr = 0
    for r in regions:
        if "type" in r:
            if r["type"]==regionType:
                ctr += 1
        elif regionType == "SR": # if no type is mentioned, its an SR
            ctr += 1
    return ctr

def fill_between_polylines(ax, x1, y1, x2, y2, **kwargs):
    from matplotlib.patches import Polygon
    verts = np.vstack([
        np.column_stack([x1, y1]),
        np.column_stack([x2[::-1], y2[::-1]]),
    ])
    poly = Polygon(verts, closed=True, **kwargs)
    ax.add_patch(poly)
    ax.autoscale_view()
    return poly

def yvalsAreWidths ( y_label : str , x_vals : list, y_vals : list ) -> tuple:
    """ if y-axes are widths, convert accordingly
    :returns tuple of new xvals and yvals
    """
    if not "Gamma" in y_label:
        return x_vals, y_vals
    self.pprint ( f"{RED}FIXME we need to make sure we also deal with the multi-line case here, so i x_vals[0]==list" )
    if type(x_vals[0]) != list:
        return x_vals, y_vals

    y_vals = [10**y for y in y_vals]
    y_diff = [y_vals[i+1]/y_vals[i] for i in range(len(y_vals)-1)]
    index_max_diff = -1
    if len(y_diff)>0 and max(y_diff)>100:
        index_max_diff = y_diff.index(max(y_diff))+1
    return x_vals[:index_max_diff], y_vals[_index_max_diff]

class PaperPlot:
    def __init__ ( self, validationPlot, general_options : dict,
            specific_options : dict ):
        self.validationPlot = validationPlot
        self.general_options = general_options
        self.specific_options = specific_options

    def fetchOfficialExclusionLines ( self, axes ) -> dict :
        """ fetch the curves and convert to sahanas format """
        ret = {}
        def fetchPointsNewFormat ( curves : list, idx : int = 0,
               x_minus_y : bool = False ) -> dict:
            ret = { "x": [], "y": [] }
            curve = curves[idx]
            #for curve in curves:
            all_segments = curve["points"]
            for segment in all_segments:
                for point in segment:
                    x = point["x"]
                    ret["x"].append ( x )
                    if "y" in point:
                        y = point["y"]
                        if x_minus_y:
                            y = x-y
                        ret["y"].append ( y )
            return ret

        def fetchPointsOldFormat ( curves : list, idx : int = 0,
               x_minus_y : bool = False ) -> dict:
            ret = { "x": [], "y": [] }
            curve = curves[idx]
            #for curve in curves:
            points = curve["points"]
            for x,y in zip(points["x"],points["y"]):
                ret["x"].append ( x )
                if x_minus_y:
                    y = x - y
                ret["y"].append ( y )
            return ret

        def fetchPoints ( curves : list, idx : int = 0 ) -> dict:
            """
            :param pm1: "" for central value "P1" or "M1" for +- 1 sigma
            """
            if len ( curves ) == 0:
                return {}

            points = curves[idx]["points"]
            c_axes = axes.replace(" ","")
            m_axes = curves[idx]["name"].replace(" ","")
            x_minus_y = ("x-y" in c_axes and not "x-y" in m_axes) or \
                        ("x-y" in m_axes and not "x-y" in c_axes )
            if type(points)==list:
                return fetchPointsNewFormat ( curves, idx, x_minus_y )
            return fetchPointsOldFormat ( curves, idx, x_minus_y )

        def getIndex  ( curves : list, pm1 : str ) -> Union[None,int]:
            for idx, curve in enumerate ( curves ):
                if pm1 != "" and pm1 in curve["name"]:
                    return idx
                if pm1 == "" and not "P1" in curve["name"] \
                        and not "M1" in curve["name"]:
                    return idx
            return None

        validationPlot = self.validationPlot
        c_idx = getIndex ( validationPlot.officialCurves, "" )
        ret["obsExclusion"] = fetchPoints ( validationPlot.officialCurves, c_idx )

        if self.specific_options["drawobsofficialpm1"] == True:
            c_idx_p1 = getIndex ( validationPlot.officialCurves, "P1" )
            if c_idx_p1 != None:
                ret["obsExclusionP1"] = fetchPoints ( \
                        validationPlot.officialCurves, c_idx_p1 )
            c_idx_m1 = getIndex ( validationPlot.officialCurves, "M1" )
            if c_idx_m1 != None:
                ret["obsExclusionM1"] = fetchPoints ( \
                        validationPlot.officialCurves, c_idx_m1 )

        c_idx = getIndex ( validationPlot.expectedOfficialCurves, "" )
        ret["expExclusion"] = fetchPoints ( validationPlot.expectedOfficialCurves, c_idx )
        if self.specific_options["drawexpofficialpm1"] == True:
            c_idx_p1 = getIndex ( validationPlot.expectedOfficialCurves, "P1" )
            if c_idx_p1 != None:
                ret["expExclusionP1"] = fetchPoints ( \
                        validationPlot.expectedOfficialCurves, c_idx_p1 )
            c_idx_m1 = getIndex ( validationPlot.expectedOfficialCurves, "M1" )
            if c_idx_m1 != None:
                ret["expExclusionM1"] = fetchPoints ( \
                        validationPlot.expectedOfficialCurves, c_idx_m1 )
        return ret

    def getCoordsFromLine ( self, curve : dict,
                    entry : str, coord : str  ) -> list:
        """ get the coordinates of curve residing in efile

        :param curve: the curve as dict
        :param entry: e.g. obsExclusion, or expExclusion
        :param coord: x, or y
        """
        if not entry in curve:
            return []
        if coord in curve[entry]:
            values = curve[entry][coord]
            return values
        values = []
        for l in curve[entry]:
            one_curve = []
            for d in l:
                if coord in d:
                    one_curve.append ( d[coord] )
            values.append ( one_curve )
        return values

    def getCoords ( self, efile : dict, curve : str,
                    entry : str, coord : str  ) -> list:
        """ get the coordinates of curve residing in efile

        :param efile: the excl_file
        :param curve: the curve as lists
        :param entry: e.g. obsExclusion, or expExclusion
        :param coord: x, or y
        """
        if "schema_version" in efile and efile["schema_version"]=="2.0":
            values = []
            if entry in efile[curve]:
                return self.getCoordsFromLine ( efile[curve], entry, coord )
            return values
        values = efile[curve][entry][coord]
        return values

    def add_jitter ( self, y_vals, addJitter : bool, delta : bool = .02 ):
        """ add jitter
        :bool addJitter: if false, then dont add jitter """
        if not addJitter:
            return y_vals
        for i, y in enumerate(y_vals):
            if type(y)==list:
                for j, yy in enumerate(y):
                    y_vals[i][j]= yy * random.uniform(1-delta,1+delta)
            else:
                y_vals[i]= y * random.uniform(1-delta,1+delta)
        return y_vals

    def removeSegments ( self, x_val : list[float],
            y_val : list[float], label : str = "" ) -> tuple[list[float]]:
        """ remove the segments of the line that are in side the remove_segments
        box.
        :param label: just for debugging, a name for the line
        """
        if self.specific_options["remove_segments"] in [ None, [] ]:
            return x_val, y_val
        if type ( self.specific_options["remove_segments"] ) == str:
            self.specific_options["remove_segments"] = \
                eval ( self.specific_options["remove_segments"] )
        rec = self.specific_options["remove_segments"]
        assert type(rec)==list, f"remove_segments {rec} needs to be a list of lists"
        ret_x, ret_y = [], []
        xmin, xmax = rec[0][0], rec[1][0]
        ymin, ymax = rec[0][1], rec[1][1]
        for x,y in zip ( x_val, y_val ):
            if xmin < x < xmax and ymin < y < ymax:
                continue
            ret_x.append( x )
            ret_y.append( y )
            if True: # "official" in label:
                print ( f"{x,y} survived {label}" )
                
        return ret_x, ret_y

    def plotLines ( self, ax, x_vals, y_vals, color : str, linestyle : str,
                   label : str ):
        """ plot lines """
        if len(x_vals)==0:
            return
        if type(x_vals[0]) == list:
            for x_val, y_val in zip ( x_vals, y_vals ):
                x_val, y_val = self.removeSegments ( x_val, y_val, label = label )
                ax.plot( x_val, y_val,color=color, linestyle= linestyle,
                         label = label )
                label = ""
            return
        ax.plot( x_vals, y_vals,color=color, linestyle=linestyle,
                 label = label )

    def findAxisInExclFile ( self, axis : str, exclfile,
            txname : str, type : str ) -> dict:
        """
        find axis in all variants in exclfile
        :returns: e.g. 'obsExclusion': {'x': [[]], 'y': [[]]}, 'expExclusion': {'x': [[]], 'y': [[]]}}
        """
        name = f"{txname}_{type}_{axis}"
        if name in exclfile.keys():
            return exclfile[name]
        if getAxisType ( axis ) == "v2":
            v3axis = axisV2ToV3 ( axis )
            name = f"{txname}_{type}_{v3axis}"
            if name in exclfile.keys():
                return exclfile[name]
        if type == "comb":
            return self.findAxisInExclFile ( axis, exclfile, txname, "combined" )
        return None

    def prettyPath ( self, path : str ) -> str:
        sfname = path.replace( os.environ["HOME"], "~" )
        return sfname

    def getCurveFromJson( self, anaDir : str, validationFolder : str,
            txname : str, typ : str, axes = None,
            eval_axes : bool = True ) -> dict:
        """
        Get Exclusion Curve from official and SModelS json files
        :param anaDir: path to dir of analysis
        :param validationFolder: usually 'validation'
        :param txname: txname for which we need the exclusion curve,
        e.g. 'TChiWZ'
        :param typ: type of exclusion curve, one of:
        "official", "bestSR", "combined"
        official curve, SModelS bestSR, SModelS combined SR
        :param axes: axes map of official exclusion line
        :param eval_axes: this is true if we need to transform y <-> x-y
        I believe

        :returns: a dict of obs and exp exclusion lines
        """
        def getCoordsFromValPlot ( curves : list, var : str = "x",
                                   nSigma : int = 0 ) -> list:
            idx = 0
            if len(curves)==3:
                idx = nSigma + 1
            ret = curves[idx]["points"][var]
            return ret

        if typ == "official":
            vPlot = self.validationPlot
            excl_x = getCoordsFromValPlot ( vPlot.officialCurves, "x",
                                            nSigma = 0 )
            excl_y = getCoordsFromValPlot ( vPlot.officialCurves, "y",
                                            nSigma = 0 )
            excl_x = getCoordsFromValPlot ( vPlot.expectedOfficialCurves, "x",
                                            nSigma = 0 )
            excl_y = getCoordsFromValPlot ( vPlot.expectedOfficialCurves, "y",
                                            nSigma = 0 )


            excl_lines = { "obsExclusion":{"x":excl_x,"y":excl_y},
                           "expExclusion":{"x":expExclusion_x,"y":expExclusion_y}}
            return excl_lines

        # saxes = str(axes).replace(" ","").replace("'","")
        #if getAxisType(axes) == "v2":
        #    axes = axisV2ToV3(axes)
        saxes = axes

        excl_lines = {}
        all_obs_x, all_obs_y, all_exp_x, all_exp_y = [], [], [], []

        fname = f"{anaDir}/{validationFolder}/SModelS_ExclusionLines.json"
        if not os.path.exists ( fname ):
            self.pprint ( f"error: {fname} does not exist!" )
            return []
        sfname = self.prettyPath ( fname )
        self.pprint ( f"we have an exclusion curve file: {sfname}" )

        file = open(fname,"r")
        excl_file = json.load(file)
        saxes = axes.replace(" ","")
        curve = self.findAxisInExclFile ( axes, excl_file, txname, typ )
        col = CYAN
        if curve is None:
            print(f"[drawPaperPlot] {CYAN}{txname}:{typ}:{saxes} not found in {sfname}{RESET}")
            if "x - y" in axes:
                axes2 = axes.replace("x - y","y" )
                self.pprint ( f"trying now with {axes2}" )
                curve = self.findAxisInExclFile ( axes2, excl_file, txname, typ )
            if curve is None:
                return {}
                return { "obsExclusion": { "x": [], "y": [] }, "expExclusion": { "y": [], "x": [] } }
        excl_lines = {}
        if "obs_excl" in curve:
            x_ = self.getCoordsFromLine ( curve, "obs_excl", "x" )
            y_ = self.getCoordsFromLine ( curve, "obs_excl", "y" )
            excl_lines["obsExclusion"] = { "x": x_, "y": y_ }
        if "exp_excl" in curve:
            x_ = self.getCoordsFromLine ( curve, "exp_excl", "x" )
            y_ = self.getCoordsFromLine ( curve, "exp_excl", "y" )
            excl_lines["expExclusion"] = { "x": x_, "y": y_ }
        for i in [ "obsExclusion", "obsExclusionP1", "obsExclusionM1",
                   "expExclusion", "expExclusionP1", "expExclusionM1" ]:
            if not i in curve:
                continue
            x_ = self.getCoordsFromLine ( curve, i, "x" )
            y_ = self.getCoordsFromLine ( curve, i, "y" )
            if len(x_)==0:
                col = RED
            if False:
                self.pprint (f"{col}we have exclusion line from {sfname} for {i} with: {sum(len(x) for x in x_)} points{RESET}" )
            excl_lines[i] = { "x": x_, "y": y_ }

        excl_lines = self.coordinateTransform ( excl_lines, axes, eval_axes )
        return excl_lines

    def coordinateTransform ( self, excl_lines, axes, eval_axes ):
        if ('x - y' in axes or 'x-y' in axes) and eval_axes:
            for typ, excl in excl_lines.items():
                excl_y = []
                for l_x, l_y in zip ( excl["x"], excl["y"] ):
                    tmp = (np.array ( l_x ) - np.array ( l_y ) ).tolist()
                    excl_y.append ( tmp )
                # excl_y = (np.array(excl["x"]) - np.array(excl["y"])).tolist()
                excl_lines[typ] = {"x":excl["x"],"y":excl_y}

        return excl_lines

    def getOnshellAxesForOffshell( self, anaDir : os.PathLike, tx_onshell : str,
            validationFolder : os.PathLike ):
        """ i think this about understanding what the axes for the onshell
        version of this offshell topology is, but fixme
        """
        fname = f"{anaDir}/{validationFolder}/SModelS_ExclusionLines.json"
        if not os.path.exists ( fname ):
            self.pprint ( f"{self.prettyPath(fname)} does not exist" )
            return None
        sm_file = open(fname,"r")
        file = open(f"{anaDir}/exclusion_lines.json")
        excl_file = json.load(file)
        excl_sm = json.load(sm_file)
        sm_file_keys = [key for key in excl_sm.keys() if f"{tx_onshell}_" in key]
        check_tx_on = [True for key in sm_file_keys if (f"{tx_onshell}_comb_" in key or f"{tx_onshell}_bestSR_" in key)]

        if tx_onshell not in excl_file:
            print(f"[drawPaperPlot] {tx_onshell} not found in official excl. Plotting only offshell")
            return None
        elif sm_file_keys == [] or False in check_tx_on:
            print(f"[drawPaperPlot] {tx_onshell} in official excl but not found in SModelS Json. Plotting only offshell")
            return None
        else:
            axes = sm_file_keys[0].split('_')[-1]
            return axes


    def addOffshell( self, excl_lines : Union[list,dict], excl_off : dict,
               min_off_y : float = 0.0, official : bool = False ) -> dict:
        """ I think this adds the offshell parts to onshell exclusion
        lines, returns the sum
        :returns: exclusion lines, on- and offshell together
        """
        # return excl_lines
        # print("[drawPaperPlot] min_off_y ", min_off_y )
        if type ( excl_lines ) == list:
            print("[drawPaperPlot] error: addOffshell for lists not implemented" )
            return excl_lines
        for typ,excl in excl_lines.items():
            if excl_off[typ]["x"] == []:
                continue

            if excl_off[typ]["x"][0] > excl_off[typ]["x"][-1] or \
                    len(excl_off[typ]["x"]) > 1 and \
                    excl_off[typ]["x"][1] > excl_off[typ]["x"][-2]:
                # print("[drawPaperPlot] off reverse")
                excl_off[typ]["x"].reverse()
                excl_off[typ]["y"].reverse()
            if official:
                min_off_y = excl_off[typ]["y"][0]

            ## FIXME no idea what that does
            if type(excl_off[typ]["y"][0]) != list and excl_off[typ]["y"][-1] < excl_off[typ]["y"][0]:# and official:
                # print("[drawPaperPlot] yes ")
                index = [i for i,y  in enumerate(excl_off[typ]["y"]) if y>excl_off[typ]["y"][0]+50]
                if len(index)>0:
                    excl_off[typ]["x"] = excl_off[typ]["x"][:index[-1]]
                    excl_off[typ]["y"] = excl_off[typ]["y"][:index[-1]]

            if len(excl["x"])>0 and excl["x"][0] > excl["x"][-1]:
                # print("[drawPaperPlot] on reverse")
                excl["x"].reverse()
                excl["y"].reverse()

            ## FIXME no idea what that does
            if len(excl_off[typ]["x"])>0 and type(excl_off[typ]["x"][0])!=list \
                    and len(excl["x"])>0 and excl_off[typ]["x"][-1] > excl["x"][0]:
                index = [i for i,x  in enumerate(excl["x"]) if x>excl_off[typ]["x"][-1]+20]
                # print("[drawPaperPlot] cut off ", excl["x"][index[0]])
                if len(index)>0:
                    excl["x"] = excl["x"][index[0]:]
                    excl["y"] = excl["y"][index[0]:]

            excl["x"] = excl_off[typ]["x"] + excl["x"]
            excl["y"] = excl_off[typ]["y"] + excl["y"]

        return excl_lines

    def getPrettyProcessName( self, txname):
        # remove pp->intermediate state
        pName = prettyTxname(txname, outputtype="latex" ).split(',')
        # print("pnamr ", pName)
        if len(pName)>2:
            pName = ','.join(pName[1:])
        else:
            pName = pName[1]
        return pName

    def getPrettyAxisLabels( self, label):
        #print("label = ", label)
        particle = label.split('m(')[-1]
        particle = label.replace('(','').replace(')','').replace('$','').split('m_')[-1]
        if len(particle) and 'm' in particle[0]:
            label = f"$m_{{{particle[1:]}}}$ [GeV]"
        elif 'Gamma' in particle:
            if 'Gamma_' not in particle: label = '$\\Gamma_{' + particle.split('Gamma')[-1] + '}$ [GeV]'
            else: label = f"${particle}$ [GeV]"
        else : label = f"$m_{{{particle}}}$ [GeV]"
        return label

    def widthToLifetime( self, y):
        shape = y.shape
        #print("y ", y.shape)
        y = y.flatten()
        hbar = 6.58*10**(-16)
        new_y = []
        for yval in y:
            if yval == 0.0: yval = 10**(-20)
            new_y.append(yval)
        #print("new_y ", new_y)
        new_y = np.array(new_y)
        new_y *= 10**9
        new_y = np.reshape(new_y, shape)
        #print("yes here")
        return hbar/new_y

    def lifetimeToWidth( self, time):
        # unused
        hbar = 6.58*10**(-16)
        time *= 10**9
        return hbar/time


    def getExtremeValue( self, excl_line, extreme : str, e_type : str,
            width : bool = False) -> float:
        """ get the extreme  value
        :param extreme: 'min' or 'max'
        """
        if len(excl_line)==0:
            if extreme == "max":
                return -1
            return np.inf
        if type(excl_line[0]) == list:
            excl_line = sum(excl_line,[])
        if e_type == "official":
            if extreme == "max":
                return max(excl_line)
            else:
                if len(excl_line)==0: return np.inf
                return min(excl_line)
        else:
            if extreme == "max":
                maxi = -1
                if width:
                    excl = [10**y for y in excl_line]
                    if len(excl)>0:
                        maxi = max(maxi, max(excl))
                    return maxi
                if len(excl_line)>0:
                    maxi = max(maxi, max(excl_line))
                return maxi
            else:
                mini = np.inf
                if width:
                    excl = [10**y for y in excl_line]
                    if len(excl)>0:
                        mini = min(mini, min(excl))
                    return mini
                if len(excl_line)>0:
                    mini = min(mini, min(excl_line))
                #else:
                #    mini =
                return mini

    def plotGammaLines ( self, x_vals, y_vals, ax, label, y_label,
           linestyle : Optional[str]=None, color : Optional[str]=None ):
        """ plot the lines in x_vals and y_vals, but heed widths """
        y_vals = self.add_jitter ( y_vals, self.addJitter )
        if color == None:
            color = "red"
        x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
        if linestyle == None:
            linestyle="solid"
        self.plotLines ( ax, x_vals, y_vals, color, linestyle, label )

    def sortSegments ( self, x_vals, y_vals ) -> tuple:
        """ sort the segments, the ones with the lower x values come first """
        if len(x_vals)==1:
            return x_vals, y_vals
        new_x, new_y = [], []
        dct = {}
        for idx, (seg_x, seg_y) in enumerate ( zip ( x_vals, y_vals ) ):
            min_x = min ( seg_x )
            while min_x in dct:
                min_x += 1e-8
            dct[min_x] = { "x": seg_x, "y": seg_y }
        keys = list ( dct.keys() )
        keys.sort( reverse = True )
        for k in keys:
            value = dct[k]
            new_x.append ( value["x"] )
            new_y.append ( value["y"] )
        return new_x, new_y

    def removeAllSegments ( self, x_vals : list, y_vals : list,
           label : str = "all" ) -> tuple:
        nx_vals, ny_vals = [], []
        for x_val, y_val in zip ( x_vals, y_vals ):
            x_val, y_val = self.removeSegments ( x_val, y_val, label=label )
            nx_vals.append( x_val )
            ny_vals.append( y_val )
        x_vals, y_vals = nx_vals, ny_vals
        return nx_vals, ny_vals

    def sortWithinSegments ( self, x_vals, y_vals ) -> tuple:
        """ sort within segments, if the order of the x values is larger to
        smaller, then invert """
        new_x, new_y = [], []
        for idx, (seg_x, seg_y) in enumerate ( zip ( x_vals, y_vals ) ):
                n = len(seg_x)
                x_f, x_m, x_l  = seg_x[0], seg_x[int(n/2)], seg_x[-1]
                if x_f <= x_m <= x_l: ## right order
                    new_x.append ( seg_x )
                    new_y.append ( seg_y )
                    continue
                new_x.append ( seg_x[::-1] )
                new_y.append ( seg_y[::-1] )
        return new_x, new_y

    def plotErrorBand ( self, x_vals1, y_vals1, x_vals2, y_vals2, ax, label,
            y_label, color : Optional[str] = None,
            alpha : float = .4 ):
        if len(x_vals1)==0:
            return
        x_vals1, y_vals1 = self.removeAllSegments ( x_vals1, y_vals1, "error_band" )
        x_vals2, y_vals2 = self.removeAllSegments ( x_vals2, y_vals2, "error_band" )
        if self.specific_options["sort_segments"]:
            x_vals1, y_vals1 = self.sortSegments ( x_vals1, y_vals1, "error_band" )
            x_vals2, y_vals2 = self.sortSegments ( x_vals2, y_vals2, "error_band" )
        if color == None:
            color = "red"
        x_vals1, y_vals1 = yvalsAreWidths ( y_label, x_vals1, y_vals1 )
        x_vals2, y_vals2 = yvalsAreWidths ( y_label, x_vals2, y_vals2 )
        if self.specific_options["sort_segments"]:
            x_vals1, y_vals1 = self.sortWithinSegments ( x_vals1, y_vals1 )
            x_vals2, y_vals2 = self.sortWithinSegments ( x_vals2, y_vals2 )
        drawBand = True
        indices = list ( range(max(len(x_vals1),len(x_vals2))) )
        if not drawBand:
            indices = []
        x1s, x2s, y1s, y2s = np.array([]), np.array([]), np.array([]), np.array([])
        for idx in indices:
            #if not idx in x_vals2:
            #    continue
            if idx < len(x_vals1):
                x1 = np.array ( x_vals1[idx] )
                y1 = np.array ( y_vals1[idx] )
                x1s = np.concatenate ( [ x1s, x1 ] )
                y1s = np.concatenate ( [ y1s, y1 ] )

            if idx < len(x_vals2):
                x2 = np.array ( x_vals2[idx] )
                y2 = np.array ( y_vals2[idx] )

                x2s = np.concatenate ( [ x2s, x2 ] )
                y2s = np.concatenate ( [ y2s, y2 ] )

        poly = fill_between_polylines(ax, x1s, y1s, x2s, y2s,
                   facecolor=color, alpha=alpha, edgecolor=None )

        drawContoursAlso = False
        if drawContoursAlso:
            linestyle = "-"
            if type(x_vals1[0]) == list:
                for x_val, y_val in zip ( x_vals1, y_vals1 ):
                    ax.plot( x_val, y_val,color=color, linestyle= linestyle,
                             linewidth = 1, label = label, zorder=-10 )
                    label = ""
                for x_val, y_val in zip ( x_vals2, y_vals2 ):
                    ax.plot( x_val, y_val,color=color, linestyle= linestyle,
                             linewidth = 1, label = label, zorder=-10 )
                    label = ""
        # import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()
        #    return

    def getRange ( self, lines : dict, whatExcl : str, whatVar : str ) -> Tuple:
        """
        :param lines: e.g. { "official": off_excl }
        :param whatExcl: e.g. obsExclusion
        :param whatVar: e.g. x
        :returns tuple (min,max)
        """
        min_var, max_var = float("inf"), -float("inf")
        for name,line in lines.items():
            if not whatExcl in line:
                continue
            if whatVar in line[whatExcl]:
                max_tmp = self.getExtremeValue( line[whatExcl][whatVar],
                        extreme = "max", e_type = name )
                min_tmp = self.getExtremeValue( line[whatExcl][whatVar],
                        extreme = "min", e_type = name )
                min_var = min ( min_var, min_tmp )
                max_var = max ( max_var, max_tmp )
        return min_var, max_var

    def pprint ( self, *args ):
        print ( f"[drawPaperPlot] {''.join(map(str,*args))}" )

    def countDataSets ( self, validationPlot ) -> dict:
        gI = validationPlot.expRes.globalInfo
        num_sr, num_cr = 0, 0
        ver = "1bin"
        if hasattr ( gI, "statModels" ):
            ver = "(pyhf)" # how to differentiate between simplified and full?
            for srSetName,model_types in gI.statModels.items():
                for model_type in model_types:
                    mtype = model_type[0]
                    if mtype == "onnx":
                        ver = "(nn)"
                        break
        g_dict = {}
        if hasattr ( gI, "srMappings" ):
            for label,region in gI.srMappings.items():
                sname = region["smodels"]
                g_dict [ sname ] = region
        for ds in validationPlot.expRes.datasets:
            name = ds.dataInfo.dataId
            if name in g_dict:
                t = g_dict[name]["type"]
                assert t in [ "SR", "CR" ], f"dont know SR type {t}"
                if t == "SR":
                    num_sr += 1
                elif t == "CR":
                    num_cr += 1
        if hasattr ( validationPlot.expRes.globalInfo, "covariance" ):
            ver = "(SLv1)"   #SLv1 vs SLv2
        if hasattr ( validationPlot.expRes.datasets[0].dataInfo, "thirdMoment" ):
            ver = "(SLv2)"
        ret = { "ver": ver, "num_sr": num_sr, "num_cr": num_cr }
        return ret

    def getRanges ( self, lines ):
        r = {}
        r["min_obs_x"], r["max_obs_x"] = \
            self.getRange( lines, "obsExclusion", "x" )
        r["min_obs_y"], r["max_obs_y"] = \
            self.getRange( lines, "obsExclusion", "y" )
        r["min_exp_x"], r["max_exp_x"] = \
            self.getRange( lines, "expExclusion", "x" )
        r["min_exp_y"], r["max_exp_y"] = \
            self.getRange( lines, "expExclusion", "y" )
        if True: ## harmonize ranges between exp and obs
            min_x = min ( r["min_obs_x"], r["min_exp_x"] )
            max_x = max ( r["max_obs_x"], r["max_exp_x"] )
            min_y = min ( r["min_obs_y"], r["min_exp_y"] )
            max_y = max ( r["max_obs_y"], r["max_exp_y"] )
            if "max_y" in self.specific_options and self.specific_options["max_y"] not in [ None, "auto" ]:
                max_y = float ( self.specific_options["max_y"] ) / 2.
            if "min_y" in self.specific_options and self.specific_options["min_y"] not in [ None, "auto" ]:
                min_y = float ( self.specific_options["min_y"] )
            if "max_x" in self.specific_options and self.specific_options["max_x"] not in [ None, "auto" ]:
                max_x = float ( self.specific_options["max_x"] )
            if "min_x" in self.specific_options and self.specific_options["min_x"] not in [ None, "auto" ]:
                min_x = float ( self.specific_options["min_x"] )
            r["min_obs_x"], r["min_exp_x"] = min_x, min_x
            r["max_obs_x"], r["max_exp_x"] = max_x, max_x
            r["min_obs_y"], r["min_exp_y"] = min_y, min_y
            r["max_obs_y"], r["max_exp_y"] = max_y, max_y
        return r

    def draw( self, addJitter : bool = True ) -> list:
        """
        Function which holds the generalised plotting parameters
        :param validationPlot: validationPlot object
        :param addJitter: if true, then add jitter to the NN line.
        so we can see it in case its perfectly aligned with the orig line

        :returns: filenames of plots
        """
        self.addJitter = addJitter
        validationPlot = self.validationPlot
        if validationPlot.isOneDimensional():
            print(f"[drawPaperPlot] currently we don't have 1d versions of the pretty plots. exiting." )
            return []
        #get info about the analysis and txname from validationPlot
        analysis = validationPlot.expRes.globalInfo.id
        vDir = validationPlot.getValidationDir (validationDir=None)
        validationFolder = os.path.basename ( vDir )
        anaDir = os.path.dirname(vDir)
        if anaDir.endswith ( "validation" ):
            anaDir = anaDir[:-10]
            validationFolder = f"validation/{validationFolder}"
        txname = validationPlot.txName
        axes = validationPlot.axes
        eval_axes = False
        saxes = str(axes).replace(" ","").replace("'","")
        print(f"[drawPaperPlot] Drawing pretty paper plot for {txname}:{saxes} ")

        offshell = False
        txnameOff = ''
        axes_on = axes
        if 'off' in txname:
            axes_on = self.getOnshellAxesForOffshell( anaDir,
                      txname.split('off')[0], validationFolder )
            if axes_on:
                # print("[drawPaperPlot] yes offshell")
                offshell=True
                txnameOff = txname
                txname = txname.split('off')[0]
            if False:
                offshell = True
                axes_on = axes

        #get exclusion lines for official and SModelS
        off_excl, comb_excl, bestSR_excl = [],[],[]
        if axes_on == None:
            axes_on = axes
        off_excl = self.fetchOfficialExclusionLines ( axes_on )

        bestSR, combSR = self.specific_options["drawbestsr"], True
        if offshell and bestSR:
            bestSR_excl = self.getCurveFromJson(anaDir, validationFolder, txname,
                    typ="bestSR", axes=axes_on, eval_axes = eval_axes )
            bestSR_excl_off = self.getCurveFromJson(anaDir, validationFolder,
                    txnameOff, typ="bestSR", axes=axes, eval_axes = eval_axes )
            if not bestSR_excl_off:
                self.pprint( f"No best SR SModelS excl line for {self.prettyPath(anaDir)}:{txnameOff}. Not drawing paper plot.")
                return
            bestSR_excl = self.addOffshell(bestSR_excl, bestSR_excl_off)
        else:
            bestSR_excl = self.getCurveFromJson(anaDir, validationFolder, txname,
                    typ="bestSR", axes=axes, eval_axes=eval_axes )
            if not bestSR_excl:
                self.pprint(f"No best SR SModelS excl line for {self.prettyPath(anaDir)}:{txname}:{axes}.")
                bestSR = False
                return
        origDir = anaDir.replace("-eff","-CR")
        cr_is = "CR"
        if not os.path.exists ( origDir ):
            origDir = anaDir.replace("-eff","-orig")
            cr_is = "orig"

        origValidationFolder = validationFolder
        if "origValidationFolder" in self.general_options:
            origValidationFolder = self.general_options["origValidationFolder"]

        orig_excl = None
        if anaDir != origDir and os.path.exists ( origDir ):
            orig_excl = self.getCurveFromJson (origDir, origValidationFolder,
                    txname, typ="comb", axes=axes, eval_axes=eval_axes )
            if offshell:
                orig_excl_off = self.getCurveFromJson( origDir,
                    origValidationFolder, txnameOff, typ="comb", axes=axes,
                    eval_axes = True )
                orig_excl = self.addOffshell ( orig_excl, orig_excl_off )
            self.pprint ( f"found curve for {origDir}!" )

        if offshell:
            comb_excl = self.getCurveFromJson(anaDir, validationFolder, txname,
                typ="comb", axes=axes_on )
            comb_excl_off = self.getCurveFromJson(anaDir, validationFolder,
                    txnameOff, typ="comb", axes=axes )
            if not comb_excl_off:
                self.pprint("No comb SR SModelS excl line. Not drawing paper plot.")
                return
            comb_excl = self.addOffshell(comb_excl, comb_excl_off)
        else:
            comb_excl = self.getCurveFromJson(anaDir, validationFolder, txname,
                typ="comb", axes=axes, eval_axes=eval_axes )
            if not comb_excl:
                self.pprint("No comb SR SModelS excl line. Not drawing paper plot.")
                combSR = False
                return
            self.pprint( f"got combined curve from {anaDir}: {len(comb_excl)} points" )
        # get the range of x values in obs and exp curves to set lim on plot ranges.
        # low limit on y axes usually 0 for plot (except for width plots)
        lines = { "official": off_excl }
        if bestSR:
            lines["bestSR"] = bestSR_excl
        if combSR:
            lines["comb"] = comb_excl

        ranges = self.getRanges( lines )


        num_sr, num_cr = 0, 0
        ver = ""

        nums = self.countDataSets ( validationPlot )
        ver, num_sr, num_cr = nums["ver"], nums["num_sr"], nums["num_cr"]

        #now plot figure
        # self.pprint("Drawing pretty obs and exp plots")

        #--------observed plot-------
        plt.rcParams['text.usetex'] = True
        plt.rcParams['font.family'] = 'Cambria Math'

        fig,ax = plt.subplots(figsize=(5,4))

        step_x = int(ranges["max_obs_x"]/100)*10
        mid_x = 0
        if ranges["max_obs_x"] < -.99:
            self.pprint ( f"seems like exclusion lines are empty" )
            return
        if ranges["max_obs_x"] > -.99:
            mid_x = int((ranges["max_obs_x"] - ranges["min_obs_x"])/2)
        step_y = int(ranges["max_obs_y"])

        x_label, y_label = "",""

        axis_label = prettyAxes(validationPlot).replace(" ","")
        axis_label = axis_label.replace( "(x,y)", "(xy)" )
        axis_label = axis_label.split(',')
        massg = ""
        for lbl in axis_label:
            if "=(xy)" in lbl:
                x_label = self.getPrettyAxisLabels(lbl.split("=")[0].strip())
                y_label = x_label.replace("m","\\Gamma")
            if "=x" in lbl and "=x-" not in lbl:
                x_label = self.getPrettyAxisLabels(lbl.split("=")[0].strip())
            elif "=x-y" in lbl:
                # y_label = r'$\Delta m$'
                x_l = x_label.replace("[GeV]","")
                m2 = self.getPrettyAxisLabels(lbl.split("=")[0].strip())
                y_label = x_l + "-" + m2
            elif "x=" in lbl:
                x_label = self.getPrettyAxisLabels(lbl.split("=")[-1].strip())
            elif ("=y" in lbl or "-y" in lbl) and "=y-" not in lbl:
                y_label = self.getPrettyAxisLabels(lbl.split("=")[0].strip())
            elif "y=" in lbl:
                y_label = self.getPrettyAxisLabels(lbl.split("=")[-1].strip())
            else: continue
        y_label = f"${y_label.replace('$','')}$"

        ax.set_xlabel(x_label,fontsize = 14)
        ax.set_ylabel(y_label,fontsize = 14)
        ax.set_xlim([int(ranges["min_obs_x"]/10)*10,round(ranges["max_obs_x"]+step_x,-1)])
        if 'Gamma' in y_label:
            self.pprint ( f"{RED}FIXME we need to make sure we also deal with the multi-line case here, so i x_vals[0]==list" )
            ranges["max_obs_y"] = self.getExtremeValue(off_excl["obsExclusion"]["y"], extreme = "max", e_type="official")
            if bestSR: ranges["max_obs_y"] = max(ranges["max_obs_y"], self.getExtremeValue(bestSR_excl["obsExclusion"]["y"], extreme = "max", e_type="bestSR", width=True))
            if combSR: ranges["max_obs_y"] = max(ranges["max_obs_y"], self.getExtremeValue(comb_excl["obsExclusion"]["y"], extreme = "max", e_type="comb", width=True))

            ranges["min_obs_y"] = self.getExtremeValue(off_excl["obsExclusion"]["y"], extreme = "min", e_type="official")
            if bestSR: ranges["min_obs_y"] = min(ranges["min_obs_y"], self.getExtremeValue(bestSR_excl["obsExclusion"]["y"], extreme = "min", e_type="bestSR", width=True))
            if combSR: ranges["min_obs_y"] = min(ranges["min_obs_y"], self.getExtremeValue(comb_excl["obsExclusion"]["y"], extreme = "min", e_type="comb", width=True))
            step_y = ranges["max_obs_y"]*1000
            ax.set_ylim([ranges["min_obs_y"], ranges["max_obs_y"]+step_y])
        else:
            ax.set_ylim([0,round(ranges["max_obs_y"]+step_y,-1)])
        if hasattr ( validationPlot.expRes.globalInfo, "includeCRs" ):
            if validationPlot.expRes.globalInfo.includeCRs == False:
                num_cr = 0
        nSRs = f"{num_sr} SRs"
        if num_sr == 1:
            nSRs = f"1 SR"
        title = f"{analysis}: {nSRs}"
        if num_cr > 0:
            title = f"{analysis}: {num_sr} SRs + {num_cr} CRs"
        # analysis id on left of title
        fs = self.specific_options["title_fontsize"]
        # processName
        # pName = prettyTxname(validationPlot.txName, outputtype="latex" )
        ptxname = validationPlot.txName
        if txnameOff == txname + "off":
            ptxname = txname + "on+off"
        pName = self.getPrettyProcessName(ptxname)
        right_title = pName
        # process string on right of title
        if self.specific_options["style"]=="sabine":
            title = f"{analysis}: {pName}"
            right_title = f"{num_sr} SRs + {num_cr} CRs"
        plt.title( title, loc='left', fontsize=fs, x=-.12)
        plt.title( right_title,loc='right', fontsize=fs)

        #plot excl curves
        exp_name = analysis.split('-')[0]
        if "x" in off_excl["obsExclusion"]:
            self.plotLines ( ax, off_excl["obsExclusion"]["x"],
                   off_excl["obsExclusion"]["y"],
                   "black", "solid", label = f'{exp_name} official' )
        plotOffSigmas = self.general_options["errorsForR"]
        if plotOffSigmas:
            for i in [ "obsExclusionP1", "obsExclusionP1", "obsExclusionM1",
                       "obsExclusionM1" ]:
                if i in off_excl and "x" in off_excl[i]:
                    self.plotLines ( ax, off_excl[i]["x"],
                        off_excl[i]["y"], "black", "dotted", None )
        if bestSR:
            x_vals = bestSR_excl["obsExclusion"]["x"]
            y_vals = bestSR_excl["obsExclusion"]["y"]
            x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
            self.plotLines( ax, x_vals, y_vals, "red", "dashed",
                            label = "SModelS: best SR")
            plt.tick_params( which='major', axis = 'both', direction = 'in',
                             length = 10, top = True, right = True)
            plt.tick_params( labelbottom=True, labelleft=True, labeltop=False,
                             labelright=False )

        if combSR and "obsExclusion" in comb_excl:
            x_vals = comb_excl["obsExclusion"]["x"]
            y_vals = comb_excl["obsExclusion"]["y"]
            y_vals = self.add_jitter ( y_vals, addJitter )
            label = f"SModelS: comb."
            gI = validationPlot.expRes.globalInfo
            # label = f"SModelS: comb. {num_sr} SRs {ver}"
            if hasattr ( gI, "statModels" ):
                for srSetName,model_types in gI.statModels.items():
                    model_type = model_types[0]
                    mtype = model_type[0]
                    if mtype == "onnx":
                        label = f"SModelS: NN"
                    if mtype == "sl":
                        ver = validationPlot.expRes.typeOfStatsModel(srSetName, specifySL=True ).replace("sl","SL")
                        label = f"SModelS: {ver}"
                # label = f"SModelS: NN {num_sr} SRs + {num_cr} CRs"
            x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
            if 'Gamma' in y_label:
                sec_ax = ax.secondary_yaxis('right', functions=(self.widthToLifetime,
                            self.widthToLifetime))
                # print("yes gamma 3")
                sec_ax.set_ylabel(r"$\tau$ [s]", fontsize=14)
                sec_ax.set_yscale('log')
            self.plotLines ( ax, x_vals, y_vals, "red", "solid", label )

            if "obsExclusionP1" in comb_excl and "obsExclusionM1" in comb_excl and \
                    self.specific_options["drawobspm1"]==True:
                x_valsp1 = comb_excl["obsExclusionP1"]["x"]
                y_valsp1 = comb_excl["obsExclusionP1"]["y"]
                addJitter = False
                y_valsp1 = self.add_jitter ( y_valsp1, addJitter, .05 )
                label = f""
                x_valsp1, y_valsp1 = yvalsAreWidths ( y_label, x_valsp1, y_valsp1 )
                # self.plotLines ( ax, x_valsp1, y_valsp1, "red", "dashed", label )
                x_valsm1 = comb_excl["obsExclusionM1"]["x"]
                y_valsm1 = comb_excl["obsExclusionM1"]["y"]
                y_valsm1 = self.add_jitter ( y_valsm1, addJitter, .05 )
                label = f""
                x_valsm1, y_valsm1 = yvalsAreWidths ( y_label, x_valsm1, y_valsm1 )
                if 'Gamma' in y_label:
                    sec_ax = ax.secondary_yaxis('right',
                            functions=(self.widthToLifetime,
                            self.widthToLifetime))
                    # print("yes gamma 3")
                    sec_ax.set_ylabel(r"$\tau$ [s]", fontsize=14)
                    sec_ax.set_yscale('log')
                #self.plotLines ( ax, x_valsm1, y_valsm1, "red", "dashed",
                #        label )
                self.plotErrorBand ( x_valsm1, y_valsm1, x_valsp1, y_valsp1, ax,
                        None, y_label, color = "tab:red" )

        if orig_excl not in [ None, [] ] and "obsExclusion" in orig_excl:
            x_vals = orig_excl["obsExclusion"]["x"]
            y_vals = orig_excl["obsExclusion"]["y"]
            label = f"SModelS: CR comb."
            # label = f"SModelS: CR comb. {num_cr} SRs+CRs {ver}"
            if cr_is == "orig":
                label = f"SModelS: orig pyhf"
                # label = f"SModelS: orig pyhf {num_sr} SRs + {num_cr} CRs"
            x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
            self.plotLines ( ax, x_vals, y_vals, "blue", "solid", label )

            if "obsExclusionP1" in orig_excl:
                x_vals = orig_excl["obsExclusionP1"]["x"]
                y_vals = orig_excl["obsExclusionP1"]["y"]
                y_vals = self.add_jitter ( y_vals, addJitter )
                label = f"xxx"
                x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
                if 'Gamma' in y_label:
                    sec_ax = ax.secondary_yaxis('right', functions=(self.widthToLifetime,
                                self.widthToLifetime))
                    # print("yes gamma 3")
                    sec_ax.set_ylabel(r"$\tau$ [s]", fontsize=14)
                    sec_ax.set_yscale('log')
                self.plotLines ( ax, x_vals, y_vals, "green", "solid", label )

        if 'Gamma' in y_label:
            ax.set_yscale('log')
        if massg != "":
            plt.text( 0.6, 0.6, rf"{massg} GeV", transform=fig.transFigure,
                      fontsize = 8)
        #if '2018-14' in analysis and 'TStau' in txname:plt.text(0.6,0.6, r"%s GeV"%(massg), transform=fig.transFigure, fontsize = 8)

        ox,oy,osize=.55,.65, 10
        if "style" in self.specific_options and self.specific_options["style"]=="sabine":
            ox,oy,osize = 0.25,0.8, 12
        plt.text( ox, oy, r"$\bf observed~exclusion$",
                  transform=fig.transFigure, fontsize = osize )
        plt.legend(loc='best', frameon=True, fontsize = 10)
        plt.tight_layout()

        #get_name_of_plot
        if getAxisType(axes) == "v2":
            axes = axisV2ToV3(axes)
        fig_axes_title = getNiceAxes ( axes )
        fig_axes_title = fig_axes_title.replace("(","").replace(")","").replace(",","")
        outfiles = []

        txn = txname if txnameOff == "" else txnameOff
        outfile = f"{vDir}/{txn}_{fig_axes_title}_obs.png"
        self.pprint ( f"saving to {YELLOW}{self.prettyPath(outfile)}{RESET}" )
        from smodels_utils.helper.various import pngMetaInfo
        metadata = pngMetaInfo()
        plt.savefig(outfile, dpi=250, metadata=metadata )
        plt.clf()
        plt.rcdefaults()
        plt.close()
        outfiles.append ( outfile )

        #--------expected plot-------
        plt.rcParams['text.usetex'] = True
        plt.rcParams['font.family'] = 'Cambria Math'

        fig,ax = plt.subplots(figsize=(5,4))

        step_x = int(ranges["max_exp_x"]/100)*10
        mid_x = int((ranges["max_exp_x"] - ranges["min_exp_x"])/2)
        step_y = int(ranges["max_exp_y"])

        #print("max exp y ", max_exp_y)
        #print("exp step y ", step_y)
        #plt.ylim([5*10**(-16),5*10**(-13)])

        ax.set_xlabel(x_label,fontsize = 14)
        ax.set_ylabel(y_label,fontsize = 14)
        ax.set_xlim([int(ranges["min_obs_x"]/10)*10,round(ranges["max_obs_x"]+step_x,-1)])
        if 'Gamma' in y_label:
            self.pprint ( f"{RED} FIXME we need to make sure we also deal with the multi-line case here, so i x_vals[0]==list" )
            ranges["max_exp_y"] = self.getExtremeValue(off_excl["expExclusion"]["y"], extreme = "max", e_type="official")
            if bestSR:
                ranges["max_exp_y"] = max(ranges["max_exp_y"], self.getExtremeValue(bestSR_excl["expExclusion"]["y"], extreme = "max", e_type="bestSR", width=True))
            if combSR:
                ranges["max_exp_y"] = max(ranges["max_exp_y"], self.getExtremeValue(comb_excl["expExclusion"]["y"], extreme = "max", e_type="comb", width=True))

            ranges["min_exp_y"] = self.getExtremeValue(off_excl["expExclusion"]["y"], extreme = "min", e_type="official")
            if bestSR:
                ranges["min_exp_y"] = min(ranges["min_exp_y"], self.getExtremeValue(bestSR_excl["expExclusion"]["y"], extreme = "min", e_type="bestSR", width=True))
            if combSR:
                ranges["min_exp_y"] = min(ranges["min_exp_y"], self.getExtremeValue(comb_excl["expExclusion"]["y"], extreme = "min", e_type="comb", width=True))
            print("min exp y ", ranges["min_exp_y"])
            step_y = ranges["max_exp_y"]*1000
            print("step exp y ", step_y)
            ax.set_ylim([ranges["min_exp_y"],ranges["max_exp_y"]+step_y])
        else: ax.set_ylim([0,round(ranges["max_exp_y"]+step_y,-1)])

        nSRs = f"{num_sr} SRs"
        if num_sr == 1:
            nSRs = f"1 SR"
        title = f"{analysis}: {nSRs}"
        if num_cr > 0:
            title = f"{analysis}: {num_sr} SRs + {num_cr} CRs"
        right_title = pName
        if self.specific_options["style"]=="sabine":
            title = f"{analysis}: {pName}"
            right_title = f"{num_sr} SRs + {num_cr} CRs"
        plt.title( title, loc='left', fontsize=12, x=-.12 )
        plt.title( right_title,loc='right', fontsize=12 )

        exp_name = analysis.split('-')[0]
        if "x" in off_excl["expExclusion"]:
            self.plotLines ( ax, off_excl["expExclusion"]["x"], 
                    off_excl["expExclusion"]["y"],
                    "black", "solid", f'{exp_name} official')

        plotOffSigmas = self.general_options["errorsForR"]
        if plotOffSigmas:
            for i in [ "expExclusionP1", "expExclusionM1" ]:
                if i in off_excl and "x" in off_excl[i]:
                    self.plotLines ( ax, off_excl[i]["x"], off_excl[i]["y"],
                            "black", "dotted", None )

        if bestSR and "expExclusion" in bestSR_excl and "y" in bestSR_excl["expExclusion"]:
            x_vals = bestSR_excl["expExclusion"]["x"]
            y_vals = bestSR_excl["expExclusion"]["y"]
            x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
            if "Gamma" in y_label:
                sec_ax = ax.secondary_yaxis('right',
                        functions=(self.widthToLifetime, self.widthToLifetime))
                sec_ax.set_ylabel(r"$\tau$ [s]", fontsize=14)
                sec_ax.set_yscale('log')
            self.plotLines ( ax, x_vals, y_vals, "red", "dashed",
                             "SModelS: best SR")
            plt.tick_params( which='major', axis = 'both', direction = 'in',
                             length = 10, top = True, right = True )
            plt.tick_params( labelbottom=True, labelleft=True, labeltop=False,
                             labelright=False )

        if combSR and "expExclusion" in comb_excl:
            x_vals = comb_excl["expExclusion"]["x"]
            y_vals = comb_excl["expExclusion"]["y"]
            label = f"SModelS: comb."
            # label = f"SModelS: comb. {num_sr} SRs {ver}"
            gI = validationPlot.expRes.globalInfo
            label = f"SModelS: orig pyhf"
            if hasattr ( gI, "statModels" ):
                if hasattr ( gI, "statModels" ):
                    for srSetName,model_types in gI.statModels.items():
                        model_type = model_types[0]
                        mtype = model_type[0]
                        if mtype == "onnx":
                            label = f"SModelS: NN"
                        if mtype == "sl":
                            ver = validationPlot.expRes.typeOfStatsModel(srSetName, specifySL=True ).replace("sl","SL")
                            label = f"SModelS: {ver}"
                # label = f"SModelS: NN {num_sr} SRs + {num_cr} CRs"
            self.plotGammaLines ( x_vals, y_vals, ax, label, y_label, color="red" )
            for i in []: # [ "expExclusionP1", "expExclusionM1" ]:
                if i in comb_excl:
                    x_vals = comb_excl[i]["x"]
                    y_vals = comb_excl[i]["y"]
                    y_vals = self.add_jitter ( y_vals, addJitter )
                    linestyle = "dashed"
                    self.plotGammaLines ( x_vals, y_vals, ax, None, y_label,
                           linestyle = "dashed", color = "red" )

        if orig_excl not in [ None, [], {} ] and "expExclusion" in orig_excl:
            x_vals = orig_excl["expExclusion"]["x"]
            y_vals = orig_excl["expExclusion"]["y"]
            label = f"SModelS: CR comb."
            # label = f"SModelS: CR comb. {num_sr} SRs+CRs {ver}"
            if cr_is == "orig":
                label = f"SModelS: orig pyhf"
                # label = f"SModelS: orig pyhf {num_sr} SRs + {num_cr} CRs"
            self.plotGammaLines ( x_vals, y_vals, ax, label, y_label,
                   linestyle= None, color = "blue" )
            if "expExclusionP1" in orig_excl and "expExclusionM1" in orig_excl:
                x_vals1 = orig_excl["expExclusionP1"]["x"]
                y_vals1 = orig_excl["expExclusionP1"]["y"]
                x_vals2 = orig_excl["expExclusionM1"]["x"]
                y_vals2 = orig_excl["expExclusionM1"]["y"]
                self.plotErrorBand ( x_vals1, y_vals1, x_vals2, y_vals2, ax,
                        None, y_label, color = "lightblue" )

        if 'Gamma' in y_label:
            ax.set_yscale('log')
        if "logy" in self.specific_options:
            ax.set_yscale('log')
            ylim = ax.get_ylim()
            ymin = .3
            if "logymin" in self.specific_options:
                ymin = self.specific_options["logymin"]
            if ylim[0]<1e-10:
                ax.set_ylim ( .3, ylim[1] )

        if massg != "":
            plt.text( 0.6,0.6, rf"{massg} GeV",
                      transform=fig.transFigure, fontsize = 8)

        ox,oy,osize=.55,.65, 10
        if "style" in self.specific_options and self.specific_options["style"]=="sabine":
            ox,oy,osize = 0.25,0.8, 12
        plt.text( ox, oy, r"$\bf expected~exclusion$",
                  transform=fig.transFigure, fontsize = osize )
        plt.legend(loc='best', frameon=True, fontsize = 10)
        plt.tight_layout()
        txn = txname if txnameOff == "" else txnameOff
        outfile = f"{vDir}/{txn}_{fig_axes_title}_exp.png"
        self.pprint ( f"saving to {YELLOW}{self.prettyPath(outfile)}{RESET}" )
        plt.savefig( outfile, dpi=250)
        plt.clf()
        plt.rcdefaults()
        plt.close()
        outfiles.append ( outfile )
        return outfiles

