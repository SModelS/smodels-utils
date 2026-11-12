#!/usr/bin/env python3

""" the plotting script for the red-black pretty paper plot
"""

__all__ = [ "drawPrettyPaperPlot" ]

import argparse
import json
import os
import random
import sys

import matplotlib.pyplot as plt
import numpy as np

from smodels_utils.helper.prettyDescriptions import prettyDecay
from smodels_utils.helper.terminalcolors import *
from validationHelpers import getAxisType, prettyAxes, axisV2ToV3, getNiceAxes

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

def yvalsAreWidths ( y_label : str , x_vals : list, y_vals : list ) -> tuple:
    """ if y-axes are widths, convert accordingly
    :returns tuple of new xvals and yvals
    """
    if not "Gamma" in y_label:
        return x_vals, y_vals
    print ( f"[drawPaperPlot] {RED}FIXME we need to make sure we also deal "
            f"with the multi-line case here, so i x_vals[0]==list{RESET}" )
    if type(x_vals[0]) != list:
        return x_vals, y_vals

    y_vals = [10**y for y in y_vals]
    y_diff = [y_vals[i+1]/y_vals[i] for i in range(len(y_vals)-1)]
    index_max_diff = -1
    if len(y_diff)>0 and max(y_diff)>100:
        index_max_diff = y_diff.index(max(y_diff))+1
    return x_vals[:index_max_diff], y_vals[index_max_diff]

class PaperPlot:
    def __init__ ( self, validationPlot, general_options : dict,
            specific_options : dict ):
        self.validationPlot = validationPlot
        self.general_options = general_options
        self.specific_options = specific_options

    def _newFigure ( self ) -> Tuple:
        """ create a new figure with the paper-plot defaults """
        plt.rcParams['text.usetex'] = True
        plt.rcParams['font.family'] = 'Cambria Math'
        return plt.subplots ( figsize = ( 5, 4 ) )

    def _addLifetimeAxis ( self, ax, y_label : str ) -> None:
        """ add the secondary lifetime axis used for width (Gamma) plots """
        if "Gamma" not in y_label:
            return
        sec_ax = ax.secondary_yaxis ( 'right',
                functions = ( self.widthToLifetime, self.widthToLifetime ) )
        sec_ax.set_ylabel ( r"$\tau$ [s]", fontsize = 14 )
        sec_ax.set_yscale ( 'log' )

    def _statModelLabel ( self, validationPlot, default : str ) -> str:
        """ label describing the statistical model used for the combined
        curve, e.g. "SModelS: SLv2" or "SModelS: NN" """
        label = default
        gI = validationPlot.expRes.globalInfo
        if not hasattr ( gI, "statModels" ):
            return label
        for srSetName, model_types in gI.statModels.items():
            model_type = model_types[0]
            mtype = model_type[0]
            if mtype == "onnx":
                label = "SModelS: NN"
            if mtype == "sl":
                ver = validationPlot.expRes.typeOfStatsModel ( srSetName,
                        specifySL = True ).replace ( "sl", "SL" )
                label = f"SModelS: {ver}"
        return label

    def _setTitles ( self, analysis : str, num_sr : int, num_cr : int,
            pName : str, fontsize : int ) -> None:
        """ set the left (analysis and region counts) and right (process)
        titles of the current axes """
        nSRs = f"{num_sr} SRs"
        if num_sr == 1:
            nSRs = "1 SR"
        title = f"{analysis}: {nSRs}"
        if num_cr > 0:
            title = f"{analysis}: {num_sr} SRs + {num_cr} CRs"
        right_title = pName
        if self.specific_options["style"] == "sabine":
            title = f"{analysis}: {pName}"
            right_title = f"{num_sr} SRs + {num_cr} CRs"
        plt.title ( title, loc = 'left', fontsize = fontsize, x = -.12 )
        plt.title ( right_title, loc = 'right', fontsize = fontsize )

    def _addCaption ( self, fig, label : str ) -> None:
        """ add the "observed exclusion" / "expected exclusion" caption """
        ox, oy, osize = .55, .65, 10
        if "style" in self.specific_options and \
                self.specific_options["style"] == "sabine":
            ox, oy, osize = 0.25, 0.8, 12
        plt.text ( ox, oy, label, transform = fig.transFigure,
                   fontsize = osize )

    def _saveFigure ( self, outfile : str, dpi : int, add_logos : bool,
            logos_y_offset : int, metadata : Optional[dict] = None ) -> None:
        """ save the current figure as png (and optionally pdf), and add
        the logos to the png """
        plt.savefig ( outfile, dpi = dpi, metadata = metadata )
        if "pdf_also" in self.specific_options and \
                self.specific_options["pdf_also"]:
            plt.savefig ( outfile.replace ( ".png", ".pdf" ), dpi = dpi )
        if add_logos:
            from addLogoToPlots import addLogo
            addLogo ( outfile, dpi = dpi, y_offset = logos_y_offset )

    def fill_between_polylines( self, ax, x1 : np.ndarray, y1 : np.ndarray,
            x2 : np.ndarray, y2 : np.ndarray, **kwargs ) -> object:
        from matplotlib.patches import Polygon
        verts = np.vstack([
            np.column_stack([x1, y1]),
#            np.column_stack([x2, y2]),
            np.column_stack([x2[::-1], y2[::-1]]),
#            np.column_stack([ [ x1[31] ] , [ y1[31] ] ] ),
        ])
        poly = Polygon(verts, closed=False, **kwargs)
        ax.add_patch(poly)
        ax.autoscale_view()
        if "show_points" in self.specific_options and self.specific_options["show_points"]:
            c = kwargs["facecolor"]
            if c == "lightblue":
                c = "blue"
            ax.scatter (x1, y1, s= 5, c = c )
            ax.scatter (x2, y2, s= 5, c = c )

            if True:
                x_all = np.concat ( [ x1, x2 ] )
                y_all = np.concat ( [ y1, y2 ] )
                for i, ( x, y ) in enumerate ( zip(x_all, y_all ) ):
                    if i % 3 != 0:
                        continue
                    #if x > 130:
                    #    continue
                    #if y > 30:
                    #    continue
                    import matplotlib.patheffects as pe
                    ax.annotate( f"{i}", # f'({x:.2f}, {y:.2f})', 
                        xy=(x, y),
                        textcoords="offset points",
                        xytext=(5, 5),           # offset in points from the marker
                        fontsize=6,
                        zorder = 50,
                        color="black", path_effects=[
                        pe.withStroke(linewidth=3, foreground='white')])
        return poly


    def fetchOfficialExclusionLines ( self, axes : str ) -> dict :
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

    def add_jitter ( self, y_vals : list, addJitter : bool,
            delta : float = .02 ) -> list:
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

    def isWithinRec ( self, x : float, y : float, rec : list ) -> bool:
        """ is point x,y with the rectangles rec """
        if type(rec[0][0]) == list: ## multiple rectangles
            for r in rec:
                if self.isWithinRec ( x, y, r ):
                    return True
            return False
        xmin, xmax = rec[0][0], rec[1][0]
        ymin, ymax = rec[0][1], rec[1][1]
        if xmin < x < xmax and ymin < y < ymax:
            return True
        return False

    def removeSegments ( self, x_val : list[float],
            y_val : list[float], label : str = "",
            verbose : bool = False ) -> tuple[list[float]]:
        """ remove the segments of the line that are in side the remove_segments
        boxes.
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
        for x,y in zip ( x_val, y_val ):
            if self.isWithinRec ( x, y, rec ):
                if verbose:
                    print ( f"[removeSegments] removing {x,y}" )
                continue
            if verbose:
                print ( f"[removeSegments] keeping  {x,y}" )
            ret_x.append( x )
            ret_y.append( y )

        return ret_x, ret_y

    def plotLines ( self, ax, x_vals : list, y_vals : list, color : str,
                   linestyle : str, label : str ) -> tuple:
        """ plot lines, return the actually plotted coordinates """
        if len(x_vals)==0:
            return x_vals, y_vals
        if type(x_vals[0]) == list:
            new_x, new_y = [], []
            for x_val, y_val in zip ( x_vals, y_vals ):
                x_val, y_val = self.removeSegments ( x_val, y_val, label = label )
                new_x.append ( x_val )
                new_y.append ( y_val )
                ax.plot( x_val, y_val,color=color, linestyle= linestyle,
                         label = label )
                label = ""
            return new_x, new_y
        x_vals, y_vals = self.removeSegments ( x_vals, y_vals, label = label )
        ax.plot( x_vals, y_vals,color=color, linestyle=linestyle,
                 label = label )
        return x_vals, y_vals

    def findAxisInExclFile ( self, axis : str, exclfile,
            txname : str, type : str ) -> Optional[dict]:
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
            obs_x = getCoordsFromValPlot ( vPlot.officialCurves, "x",
                                           nSigma = 0 )
            obs_y = getCoordsFromValPlot ( vPlot.officialCurves, "y",
                                           nSigma = 0 )
            exp_x = getCoordsFromValPlot ( vPlot.expectedOfficialCurves, "x",
                                           nSigma = 0 )
            exp_y = getCoordsFromValPlot ( vPlot.expectedOfficialCurves, "y",
                                           nSigma = 0 )
            excl_lines = { "obsExclusion": { "x": obs_x, "y": obs_y },
                           "expExclusion": { "x": exp_x, "y": exp_y } }
            return excl_lines

        # saxes = str(axes).replace(" ","").replace("'","")
        #if getAxisType(axes) == "v2":
        #    axes = axisV2ToV3(axes)

        fname = f"{anaDir}/{validationFolder}/SModelS_ExclusionLines.json"
        if not os.path.exists ( fname ):
            self.pprint ( f"error: {fname} does not exist!" )
            return []
        sfname = self.prettyPath ( fname )
        self.pprint ( f"we have an exclusion curve file: {sfname}" )

        with open ( fname, "r" ) as file:
            excl_file = json.load ( file )
        saxes = axes.replace(" ","")
        curve = self.findAxisInExclFile ( axes, excl_file, txname, typ )
        if curve is None:
            print(f"[drawPaperPlot] {CYAN}{txname}:{typ}:{saxes} not found in {sfname}{RESET}")
            if "x - y" in axes:
                axes2 = axes.replace("x - y","y" )
                self.pprint ( f"trying now with {axes2}" )
                curve = self.findAxisInExclFile ( axes2, excl_file, txname, typ )
            if curve is None:
                return {}
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
            excl_lines[i] = { "x": x_, "y": y_ }

        excl_lines = self.coordinateTransform ( excl_lines, axes, eval_axes )
        return excl_lines

    def coordinateTransform ( self, excl_lines : dict, axes : str,
            eval_axes : bool ) -> dict:
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
            validationFolder : os.PathLike ) -> Optional[str]:
        """ i think this about understanding what the axes for the onshell
        version of this offshell topology is, but fixme
        """
        fname = f"{anaDir}/{validationFolder}/SModelS_ExclusionLines.json"
        if not os.path.exists ( fname ):
            self.pprint ( f"{self.prettyPath(fname)} does not exist" )
            return None
        with open ( fname, "r" ) as sm_file, \
                open ( f"{anaDir}/exclusion_lines.json" ) as excl_file_handle:
            excl_file = json.load ( excl_file_handle )
            excl_sm = json.load ( sm_file )
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
        if len(excl_lines)==0 and len(excl_off) > 0:
            ## seems a simple case
            return excl_off
        for typ,excl in excl_lines.items():
            if excl_off[typ]["x"] == []:
                continue

            if excl_off[typ]["x"][0] > excl_off[typ]["x"][-1] or \
                    len(excl_off[typ]["x"]) > 1 and \
                    excl_off[typ]["x"][1] > excl_off[typ]["x"][-2]:
                # print("[drawPaperPlot] off reverse")
                excl_off[typ]["x"].reverse()
                excl_off[typ]["y"].reverse()
            # note: the "official" flag and min_off_y are currently unused
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

    def getPrettyProcessName( self, txname : str ) -> str:
        # remove pp->intermediate state
        pName = prettyDecay(txname, latex = True )
        """
        pName = prettyTxname(txname, outputtype="latex" ).split(',')
        # print("pnamr ", pName)
        if len(pName)>2:
            pName = ','.join(pName[1:])
        else:
            pName = pName[1]
        """
        return pName

    def getPrettyAxisLabels( self, label : str ) -> str:
        #print("label = ", label)
        particle = label.replace('(','').replace(')','').replace('$','').split('m_')[-1]
        if len(particle) and 'm' in particle[0]:
            label = f"$m_{{{particle[1:]}}}$ [GeV]"
        elif 'Gamma' in particle:
            if 'Gamma_' not in particle:
                label = '$\\Gamma_{' + particle.split('Gamma')[-1] + '}$ [GeV]'
            else:
                label = f"${particle}$ [GeV]"
        else :
            label = f"$m_{{{particle}}}$ [GeV]"
        return label

    def widthToLifetime( self, y : np.ndarray ) -> np.ndarray:
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

    def lifetimeToWidth( self, time : np.ndarray ) -> np.ndarray:
        # unused
        hbar = 6.58*10**(-16)
        time *= 10**9
        return hbar/time


    def getExtremeValue( self, excl_line : list, extreme : str,
            e_type : str, width : bool = False ) -> float:
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

    def plotGammaLines ( self, x_vals : list, y_vals : list, ax, label,
           y_label : str, linestyle : Optional[str]=None,
           color : Optional[str]=None ) -> tuple:
        """ plot the lines in x_vals and y_vals, but heed widths """
        y_vals = self.add_jitter ( y_vals, self.addJitter )
        if color == None:
            color = "red"
        x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
        if linestyle == None:
            linestyle="solid"
        return self.plotLines ( ax, x_vals, y_vals, color, linestyle, label )

    def sortSegments ( self, x_vals : list, y_vals : list ) -> tuple:
        """ sort the segments, the ones with the lower x values come first """
        if len(x_vals)==1:
            return x_vals, y_vals
        new_x, new_y = [], []
        dct = {}
        for seg_x, seg_y in zip ( x_vals, y_vals ):
            if len(seg_x)==0:
                continue
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
        return nx_vals, ny_vals

    def sortWithinSegments ( self, x_vals : list, y_vals : list ) -> tuple:
        """ sort within segments, if the order of the x values is larger to
        smaller, then invert """
        new_x, new_y = [], []
        for seg_x, seg_y in zip ( x_vals, y_vals ):
            n = len(seg_x)
            x_f, x_m, x_l  = seg_x[0], seg_x[int(n/2)], seg_x[-1]
            if x_f <= x_m <= x_l: ## right order
                new_x.append ( seg_x )
                new_y.append ( seg_y )
                continue
            new_x.append ( seg_x[::-1] )
            new_y.append ( seg_y[::-1] )
        return new_x, new_y

    def sortArbitrarily ( self, x_vals : list, y_vals : list,
            label : str ) -> tuple:
        """ placeholder for arbitrary reordering; currently a no-op """
        return x_vals, y_vals

    def _asSegments ( self, x_vals : list, y_vals : list ) -> list:
        """ return the curves as a list of (N,2) numpy arrays """
        if x_vals is None or y_vals is None or len ( x_vals ) == 0:
            return []
        if isinstance ( x_vals[0], ( list, tuple, np.ndarray ) ):
            segments = []
            for seg_x, seg_y in zip ( x_vals, y_vals ):
                seg_x = np.asarray ( seg_x, dtype = float ).ravel()
                seg_y = np.asarray ( seg_y, dtype = float ).ravel()
                n = min ( len ( seg_x ), len ( seg_y ) )
                if n > 0:
                    segments.append ( np.column_stack ( [ seg_x[:n], seg_y[:n] ] ) )
            return segments
        seg_x = np.asarray ( x_vals, dtype = float ).ravel()
        seg_y = np.asarray ( y_vals, dtype = float ).ravel()
        n = min ( len ( seg_x ), len ( seg_y ) )
        if n == 0:
            return []
        return [ np.column_stack ( [ seg_x[:n], seg_y[:n] ] ) ]

    def _nearestPointOnSegments ( self, point : np.ndarray,
            segments : list ) -> Optional[np.ndarray]:
        """ return the point on any of the segments that is closest to point """
        best_dist2, best_point = float ( "inf" ), None
        for segment in segments:
            if len ( segment ) == 0:
                continue
            if len ( segment ) == 1:
                delta = segment[0] - point
                dist2 = float ( delta @ delta )
                candidate = segment[0]
            else:
                starts = segment[:-1]
                ends = segment[1:]
                directions = ends - starts
                offsets = point - starts
                denom = np.einsum ( "ij,ij->i", directions, directions )
                denom[denom == 0] = 1e-30
                t = np.clip ( np.einsum ( "ij,ij->i", offsets, directions )
                              / denom, 0, 1 )
                projected = starts + t[:, None] * directions
                dist2s = np.einsum ( "ij,ij->i", projected - point,
                                     projected - point )
                idx = int ( np.argmin ( dist2s ) )
                dist2, candidate = float ( dist2s[idx] ), projected[idx]
            if dist2 < best_dist2:
                best_dist2, best_point = dist2, candidate
        return best_point

    def _segmentsNear ( self, center_segment : np.ndarray,
            side_segments : list,
            margin_fraction : float = 0.1 ) -> list:
        """ keep only the side segments whose bounding box is near the
        center segment; this drops unrelated islands of the side curve """
        if len ( center_segment ) == 0:
            return []
        cmin, cmax = center_segment.min ( axis = 0 ), center_segment.max ( axis = 0 )
        margin = margin_fraction * float ( np.linalg.norm ( cmax - cmin ) )
        near = []
        for segment in side_segments:
            if len ( segment ) < 2:
                continue
            smin, smax = segment.min ( axis = 0 ), segment.max ( axis = 0 )
            if np.any ( smax < cmin - margin ) or \
                    np.any ( smin > cmax + margin ):
                continue
            near.append ( segment )
        if near:
            return near
        # fall back to all proper segments
        return [ segment for segment in side_segments if len ( segment ) >= 2 ]

    def _signedArea ( self, polygon ) -> float:
        """ signed area of a closed polygon """
        x_vals, y_vals = polygon[:, 0], polygon[:, 1]
        return .5 * float ( np.sum ( x_vals * np.roll ( y_vals, -1 ) -
                         y_vals * np.roll ( x_vals, -1 ) ) )

    def _fillCompoundPolygons ( self, ax, polygons : list,
            **kwargs ) -> Optional[object]:
        """ fill several polygons with a single path, so that overlapping
        parts are not painted twice (and hence do not look darker) """
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch
        vertices, codes = [], []
        for polygon in polygons:
            if len ( polygon ) < 3:
                continue
            # make all loops wind in the same direction, otherwise
            # overlapping loops could cancel each other
            if self._signedArea ( polygon ) < 0:
                polygon = polygon[::-1]
            n = len ( polygon )
            vertices.extend ( polygon.tolist() )
            vertices.append ( polygon[0].tolist() )
            codes.extend ( [ Path.MOVETO ] + [ Path.LINETO ] * ( n - 1 ) +
                           [ Path.CLOSEPOLY ] )
        if not codes:
            return None
        patch = PathPatch ( Path ( np.asarray ( vertices ), codes ), **kwargs )
        ax.add_patch ( patch )
        ax.autoscale_view()
        return patch

    def _plotGuessedErrorBand ( self, x_vals1 : list, y_vals1 : list,
            x_vals2 : list, y_vals2 : list, center_x_vals : list,
            center_y_vals : list, ax, color : str, alpha : float ) -> bool:
        """ draw a band around the central line, using the points of the
        +-1 sigma curves that are closest to each central point """
        center_segments = self._asSegments ( center_x_vals, center_y_vals )
        side1_segments = self._asSegments ( x_vals1, y_vals1 )
        side2_segments = self._asSegments ( x_vals2, y_vals2 )
        if not center_segments or not side1_segments or not side2_segments:
            return False
        polygons = []
        for center_segment in center_segments:
            if len ( center_segment ) < 2:
                continue
            side1 = self._segmentsNear ( center_segment, side1_segments )
            side2 = self._segmentsNear ( center_segment, side2_segments )
            for side in ( side1, side2 ):
                if not side:
                    continue
                mapped = []
                for point in center_segment:
                    nearest = self._nearestPointOnSegments ( point, side )
                    if nearest is not None:
                        mapped.append ( nearest )
                if len ( mapped ) < 2:
                    continue
                mapped = np.asarray ( mapped )
                polygon = np.vstack ( [ center_segment, mapped[::-1] ] )
                if len ( polygon ) >= 3:
                    polygons.append ( polygon )
        if not polygons:
            return False
        self._fillCompoundPolygons ( ax, polygons, facecolor = color,
                alpha = alpha, edgecolor = "none", linewidth = 0 )
        return True

    def plotErrorBand ( self, x_vals1 : list, y_vals1 : list, x_vals2 : list,
            y_vals2 : list, ax, label, y_label : str,
            color : Optional[str] = None,
            alpha : float = .4, center_x_vals = None, center_y_vals = None,
            guess : bool = False ) -> None:
        if len(x_vals1)==0:
            return
        x_vals1, y_vals1 = self.sortArbitrarily ( x_vals1, y_vals1, "1" )
        x_vals2, y_vals2 = self.sortArbitrarily ( x_vals2, y_vals2, "2" )
        x_vals1, y_vals1 = self.removeAllSegments ( x_vals1, y_vals1, "error_band" )
        x_vals2, y_vals2 = self.removeAllSegments ( x_vals2, y_vals2, "error_band" )
        # guess_blueband takes precedence over the sort options for this
        # band: the band is anchored on the central line instead.
        sort_segments = False if guess else \
                self.specific_options.get ( "sort_segments", False )
        sort_within_segments = False if guess else \
                self.specific_options.get ( "sort_within_segments", False )
        if sort_segments:
            x_vals1, y_vals1 = self.sortSegments ( x_vals1, y_vals1 )
            x_vals2, y_vals2 = self.sortSegments ( x_vals2, y_vals2 )
        if color == None:
            color = "red"
        x_vals1, y_vals1 = yvalsAreWidths ( y_label, x_vals1, y_vals1 )
        x_vals2, y_vals2 = yvalsAreWidths ( y_label, x_vals2, y_vals2 )
        if guess:
            # Ignore sort_segments/sort_within_segments: instead anchor
            # the band on the plotted central line by matching every
            # central point to its closest +-1 sigma point.
            if self._plotGuessedErrorBand ( x_vals1, y_vals1, x_vals2, y_vals2,
                    center_x_vals, center_y_vals, ax, color, alpha ):
                return
        if sort_within_segments:
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

        self.fill_between_polylines ( ax, x1s, y1s, x2s, y2s,
                   facecolor = color, alpha = alpha, edgecolor = None )

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

    def pprint ( self, *args ) -> None:
        print ( f"[drawPaperPlot] {''.join(map(str,*args))}" )

    def error ( self, *args ) -> None:
        print ( f"[drawPaperPlot] {RED}error: {''.join(map(str,*args))}{RESET}" )

    def getStatModel ( self, validationPlot ) -> Optional[str]:
        """ find out which stat model was used, complain if not always
        the same """
        validationPlot.loadData()
        ret = None
        for entry in validationPlot.data:
            if "StatModel" in entry:
                tmp = entry["StatModel"]
                if ret != None and tmp != ret:
                    print ( f"[drawPaperPlot] ERROR: stat model changed {ret}!={tmp}" )
                    sys.exit(-1)
                ret = tmp
        return ret

    def addRegionCounts ( self, first : dict, second : dict ) -> dict:
        for k,v in second.items():
            if not k in first:
                first[k]=0
            first[k]+=v
        return first

    def countRegions ( self, gI : "GlobalInfo", regionName : str|None ) -> dict:
        nums = { "SR": 0, "CR": 0 }
        if not hasattr ( gI, "regionSets" ):
            print ( f"[drawPaperPlot] {gI.id} has no region sets" )
            return nums
        if regionName == None: ## count all
            for setName in gI.regionSets.keys():
                snums = self.countRegions ( gI, setName )
                self.addRegionCounts ( nums, snums )
            return nums
        regionSet = gI.regionSets [ regionName ]
        if not hasattr ( gI, "regionMappings" ):
            nums["SR"]=len(regionSet)
        else:
            for regionName in regionSet:
                mapping = gI.regionMappings[regionName]
                nums[mapping["type"]]+=1
        return nums

    def getRegionNamesForTxname ( self, expRes, txname : str ) -> list[str]:
        """ find the region sets that contain datasets for this txname """
        gI = expRes.globalInfo
        if not hasattr ( gI, "regionSets" ):
            return []
        regionNames = set()
        for dataset in expRes.datasets:
            if txname not in [ str(tx) for tx in dataset.txnameList ]:
                continue
            dataId = str(dataset.dataInfo.dataId)
            regionNames.add ( dataId )
            if hasattr ( gI, "regionMappings" ):
                for regionName, mapping in gI.regionMappings.items():
                    aliases = [ str(v) for v in mapping.values() if v is not None ]
                    if dataId in aliases:
                        regionNames.add ( regionName )
        return [ name for name in gI.regionSets.keys()
                 if regionNames.intersection ( gI.regionSets[name] ) ]

    def addOnshellCounts ( self, validationPlot, nums : dict, txname : str,
            axes_on ) -> None:
        """ its a combined onshell + offshell plot,
        so we need to add the regions from the onshell """
        offshellRegionName = nums.get ( "regionName" )
        if offshellRegionName is None:
            ## the offshell count was not attributed to a single region set,
            ## so adding onshell regions could count regions twice
            return
        db = getattr ( validationPlot, "db", None )
        if db is None:
            self.error ( f"cannot determine onshell region counts for {txname}: no database" )
            return
        gI = validationPlot.expRes.globalInfo
        expResults = db.getExpResults ( analysisIDs = [ gI.id ],
                txnames = [ txname ], useNonValidated = True )
        if not expResults:
            self.error ( f"cannot determine onshell region counts for {txname}: no experimental result found" )
            return
        onshellExpRes = expResults[0]
        for expRes in expResults:
            if expRes.path == validationPlot.expRes.path:
                onshellExpRes = expRes
                break
        else:
            ## no result in the same folder, try the same data type
            if validationPlot.expRes.datasets:
                dataType = validationPlot.expRes.datasets[0].dataInfo.dataType
                for expRes in expResults:
                    if expRes.datasets and expRes.datasets[0].dataInfo.dataType == dataType:
                        onshellExpRes = expRes
                        break
        onshellRegionNames = self.getRegionNamesForTxname ( onshellExpRes, txname )
        if not onshellRegionNames:
            self.error ( f"cannot determine onshell region counts for {txname}" )
            return
        for regionName in onshellRegionNames:
            if regionName == offshellRegionName:
                ## on- and offshell use the same region set, already counted
                continue
            counts = self.countRegions ( onshellExpRes.globalInfo, regionName )
            nums["num_sr"] += counts["SR"]
            nums["num_cr"] += counts["CR"]

    def countDataSets ( self, validationPlot ) -> dict:
        gI = validationPlot.expRes.globalInfo
        num_sr, num_cr = 0, 0
        ver = "1bin"
        regionName = None
        if hasattr ( gI, "statModels" ):
            ver = "(pyhf)" # how to differentiate between simplified and full?
            for srSetName,model_types in gI.statModels.items():
                for model_type in model_types:
                    mtype = model_type[0]
                    if mtype == "onnx":
                        ver = "(nn)"
                        break
        g_dict = {}
        if hasattr ( gI, "regionMappings" ):
            for label,region in gI.regionMappings.items():
                sname = region["smodels"]
                g_dict [ sname ] = region
        if hasattr ( gI, "statModels" ):
            statModel = self.getStatModel ( validationPlot )
            for sM,models in gI.statModels.items():
                for model in models:
                    if statModel == model[1]: ## we found it!
                        regionName = sM
                        break
            nums = self.countRegions ( gI, regionName )
            num_sr += nums["SR"]
            num_cr += nums["CR"]
        if hasattr ( validationPlot.expRes.datasets[0].dataInfo, "thirdMoment" ):
            ver = "(SLv2)"
        ret = { "ver": ver, "num_sr": num_sr, "num_cr": num_cr,
                "regionName": regionName }
        return ret

    def getRanges ( self, lines : dict ) -> dict:
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

    def describe ( self ) -> None:
        """ simple method to describe what i will be doing """
        print ( "[drawPaperPlot] starting" )
        return ## FIXME
        gen_opts = list ( self.general_options.keys() )
        gen_opts.sort()
        print ( "general options" )
        print ( "===============" )
        for k in gen_opts:
            v = self.general_options[k]
            print ( f"  - {k}: {v}" )
        spe_opts = list ( self.specific_options.keys() )
        spe_opts.sort()
        print ( "specific options" )
        print ( "================" )
        for k in spe_opts:
            v = self.specific_options[k]
            print ( f"  - {k}: {v}" )
        #print ( f"  - {self.general_options}" )
        #print ( f"  - {self.specific_options}" )

    def draw( self, addJitter : bool = True ) -> list:
        """
        Function which holds the generalised plotting parameters
        :param validationPlot: validationPlot object
        :param addJitter: if true, then add jitter to the NN line.
        so we can see it in case its perfectly aligned with the orig line

        :returns: filenames of plots
        """
        self.describe()
        self.addJitter = addJitter
        validationPlot = self.validationPlot
        if validationPlot.isOneDimensional():
            print("[drawPaperPlot] currently we don't have 1d versions of the pretty plots. exiting." )
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
                self.error( f"No best SR SModelS excl line for {self.prettyPath(anaDir)}:{txnameOff}.")
                # self.error ( f"not drawing plot" )
                # return
            bestSR_excl = self.addOffshell(bestSR_excl, bestSR_excl_off)
        else:
            bestSR_excl = self.getCurveFromJson(anaDir, validationFolder, txname,
                    typ="bestSR", axes=axes, eval_axes=eval_axes )
            if not bestSR_excl:
                self.error(f"No best SR SModelS excl line for {self.prettyPath(anaDir)}:{txname}:{axes}.")
                bestSR = False
                # self.error ( f"not drawing plot" )
                # return
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

        nums = self.countDataSets ( validationPlot )
        if offshell and txname != txnameOff:
            self.addOnshellCounts ( validationPlot, nums, txname, axes_on )
        num_sr, num_cr = nums["num_sr"], nums["num_cr"]

        #now plot figure
        # self.pprint("Drawing pretty obs and exp plots")

        #--------observed plot-------
        fig, ax = self._newFigure()

        step_x = int(ranges["max_obs_x"]/100)*10
        if ranges["max_obs_x"] < -.99:
            self.pprint ( "seems like exclusion lines are empty" )
            return
        step_y = int(ranges["max_obs_y"])

        x_label, y_label = "",""

        axis_label = prettyAxes(validationPlot).replace(" ","")
        axis_label = axis_label.replace( "(x,y)", "(xy)" )
        axis_label = axis_label.split(',')
        massg = ""
        for i,lbl in enumerate(axis_label):
            if "=(xy)" in lbl:
                x_label = self.getPrettyAxisLabels(lbl.split("=")[0].strip())
                y_label = x_label.replace("m","\\Gamma")
            elif "=x" in lbl and "=x-" not in lbl:
                x_label = self.getPrettyAxisLabels(lbl.split("=")[0].strip())
                if i == 1 and not "=" in axis_label[0]:
                    tmp = self.getPrettyAxisLabels(axis_label[0])
                    tmp = tmp.replace("[GeV]","")
                    tmp.strip()
                    if not ( r"\mp" in tmp and r"\pm" in x_label):
                        x_label = f"{tmp},{x_label}"
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
            else:
                continue
        # y_label = f"${y_label.replace('$','')}$"
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
        # analysis id on the left, process name on the right
        fs = self.specific_options["title_fontsize"]
        ptxname = validationPlot.txName
        if txnameOff == txname + "off":
            ptxname = txname + "on+off"
        pName = self.getPrettyProcessName(ptxname)
        self._setTitles ( analysis, num_sr, num_cr, pName, fs )

        #plot excl curves
        exp_name = analysis.split('-')[0]
        if "x" in off_excl["obsExclusion"]:
            self.plotLines ( ax, off_excl["obsExclusion"]["x"],
                   off_excl["obsExclusion"]["y"],
                   "black", "solid", label = f'{exp_name} official' )
        plotOffSigmas = self.general_options["errorsForR"]
        if plotOffSigmas:
            for i in [ "obsExclusionP1", "obsExclusionM1" ]:
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
            label = self._statModelLabel ( validationPlot, "SModelS: comb." )
            x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
            self._addLifetimeAxis ( ax, y_label )
            self.plotLines ( ax, x_vals, y_vals, "red", "solid", label )

            if "obsExclusionP1" in comb_excl and "obsExclusionM1" in comb_excl and \
                    self.specific_options["drawobspm1"]==True:
                x_valsp1 = comb_excl["obsExclusionP1"]["x"]
                if len(x_valsp1) == 0:
                    print ( "[drawPaperPlot] asked for red error band but not obsExclusionP1" )
                    return
                y_valsp1 = comb_excl["obsExclusionP1"]["y"]
                addJitter = False
                y_valsp1 = self.add_jitter ( y_valsp1, addJitter, .05 )
                x_valsp1, y_valsp1 = yvalsAreWidths ( y_label, x_valsp1, y_valsp1 )
                # self.plotLines ( ax, x_valsp1, y_valsp1, "red", "dashed", label )
                x_valsm1 = comb_excl["obsExclusionM1"]["x"]
                y_valsm1 = comb_excl["obsExclusionM1"]["y"]
                y_valsm1 = self.add_jitter ( y_valsm1, addJitter, .05 )
                x_valsm1, y_valsm1 = yvalsAreWidths ( y_label, x_valsm1, y_valsm1 )
                self._addLifetimeAxis ( ax, y_label )
                #self.plotLines ( ax, x_valsm1, y_valsm1, "red", "dashed",
                #        label )
                self.plotErrorBand ( x_valsm1, y_valsm1, x_valsp1, y_valsp1, ax,
                        None, y_label, color = "tab:red" )
                # import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()

        if orig_excl not in [ None, [] ] and "obsExclusion" in orig_excl:
            x_vals = orig_excl["obsExclusion"]["x"]
            y_vals = orig_excl["obsExclusion"]["y"]
            label = "SModelS: CR comb."
            # label = f"SModelS: CR comb. {num_cr} SRs+CRs {ver}"
            if cr_is == "orig":
                label = "SModelS: orig pyhf"
                # label = f"SModelS: orig pyhf {num_sr} SRs + {num_cr} CRs"
            x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
            self.plotLines ( ax, x_vals, y_vals, "blue", "solid", label )

            if "obsExclusionP1" in orig_excl:
                x_vals = orig_excl["obsExclusionP1"]["x"]
                y_vals = orig_excl["obsExclusionP1"]["y"]
                y_vals = self.add_jitter ( y_vals, addJitter )
                label = "xxx"
                x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
                self._addLifetimeAxis ( ax, y_label )
                # self.plotLines ( ax, x_vals, y_vals, "green", "solid", label )

        if 'Gamma' in y_label:
            ax.set_yscale('log')
        if massg != "":
            plt.text( 0.6, 0.6, rf"{massg} GeV", transform=fig.transFigure,
                      fontsize = 8)
        #if '2018-14' in analysis and 'TStau' in txname:plt.text(0.6,0.6, r"%s GeV"%(massg), transform=fig.transFigure, fontsize = 8)

        self._addCaption ( fig, r"$\bf observed~exclusion$" )
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
        from smodels_utils.helper.various import pngMetaInfo
        metadata = pngMetaInfo()
        dpi = 300
        self.pprint ( f"saving to {YELLOW}{self.prettyPath(outfile)}{RESET}" )
        add_logos = True
        if "addlogo" in self.specific_options:
            add_logos = self.specific_options["addlogo"]
        logos_y_offset = -125
        self._saveFigure ( outfile, dpi, add_logos, logos_y_offset, metadata )
        plt.clf()
        plt.rcdefaults()
        plt.close()
        outfiles.append ( outfile )

        #--------expected plot-------
        fig, ax = self._newFigure()

        step_x = int(ranges["max_exp_x"]/100)*10
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

        self._setTitles ( analysis, num_sr, num_cr, pName, 12 )

        isPrefitExpected = str ( self.general_options.get ( "expectationType", "" ) ).lower() == "apriori"
        exp_name = analysis.split('-')[0]
        if not isPrefitExpected and "x" in off_excl["expExclusion"]:
            self.plotLines ( ax, off_excl["expExclusion"]["x"],
                    off_excl["expExclusion"]["y"],
                    "black", "solid", f'{exp_name} official')

        plotOffSigmas = self.general_options["errorsForR"]
        if plotOffSigmas and not isPrefitExpected:
            for i in [ "expExclusionP1", "expExclusionM1" ]:
                if i in off_excl and "x" in off_excl[i]:
                    self.plotLines ( ax, off_excl[i]["x"], off_excl[i]["y"],
                            "black", "dotted", None )

        if bestSR and "expExclusion" in bestSR_excl and "y" in bestSR_excl["expExclusion"]:
            x_vals = bestSR_excl["expExclusion"]["x"]
            y_vals = bestSR_excl["expExclusion"]["y"]
            x_vals, y_vals = yvalsAreWidths ( y_label, x_vals, y_vals )
            self._addLifetimeAxis ( ax, y_label )
            self.plotLines ( ax, x_vals, y_vals, "red", "dashed",
                             "SModelS: best SR")
            plt.tick_params( which='major', axis = 'both', direction = 'in',
                             length = 10, top = True, right = True )
            plt.tick_params( labelbottom=True, labelleft=True, labeltop=False,
                             labelright=False )

        if combSR and "expExclusion" in comb_excl:
            x_vals = comb_excl["expExclusion"]["x"]
            y_vals = comb_excl["expExclusion"]["y"]
            label = self._statModelLabel ( validationPlot,
                    "SModelS: orig pyhf" )
            self.plotGammaLines ( x_vals, y_vals, ax, label, y_label, color="red" )

        if orig_excl not in [ None, [], {} ] and "expExclusion" in orig_excl:
            x_vals = orig_excl["expExclusion"]["x"]
            y_vals = orig_excl["expExclusion"]["y"]
            label = "SModelS: CR comb."
            # label = f"SModelS: CR comb. {num_sr} SRs+CRs {ver}"
            if cr_is == "orig":
                label = "SModelS: orig pyhf"
                # label = f"SModelS: orig pyhf {num_sr} SRs + {num_cr} CRs"
            center_x_vals, center_y_vals = self.plotGammaLines ( x_vals, y_vals,
                   ax, label, y_label, linestyle= None, color = "blue" )
            if "expExclusionP1" in orig_excl and "expExclusionM1" in orig_excl:
                x_vals1 = orig_excl["expExclusionP1"]["x"]
                y_vals1 = orig_excl["expExclusionP1"]["y"]
                x_vals2 = orig_excl["expExclusionM1"]["x"]
                y_vals2 = orig_excl["expExclusionM1"]["y"]
                self.plotErrorBand ( x_vals1, y_vals1, x_vals2, y_vals2, ax,
                        None, y_label, color = "lightblue",
                        center_x_vals = center_x_vals,
                        center_y_vals = center_y_vals,
                        guess = self.specific_options.get ( "guess_blueband",
                                                            False ) )

        if 'Gamma' in y_label:
            ax.set_yscale('log')
        if "logy" in self.specific_options:
            ax.set_yscale('log')
            ylim = ax.get_ylim()
            ymin = .3
            if "logymin" in self.specific_options:
                ymin = self.specific_options["logymin"]
            if ylim[0]<1e-10:
                ax.set_ylim ( ymin, ylim[1] )

        if massg != "":
            plt.text( 0.6,0.6, rf"{massg} GeV",
                      transform=fig.transFigure, fontsize = 8)

        expected_label = r"$\bf expected~exclusion$"
        if str ( self.general_options.get ( "expectationType", "" ) ).lower() == "apriori":
            expected_label = r"$\bf pre\textrm{-}fit~expected~exclusion$"
        self._addCaption ( fig, expected_label )
        plt.legend(loc='best', frameon=True, fontsize = 10)
        plt.tight_layout()
        txn = txname if txnameOff == "" else txnameOff
        outfile = f"{vDir}/{txn}_{fig_axes_title}_exp.png"
        self.pprint ( f"saving to {YELLOW}{self.prettyPath(outfile)}{RESET}" )
        self._saveFigure ( outfile, dpi, add_logos, logos_y_offset )
        plt.clf()
        plt.rcdefaults()
        plt.close()
        outfiles.append ( outfile )
        return outfiles



def defaultGeneralOptions () -> dict:
    """ the default general options; keep in sync with the options dict
    in runValidation.py """
    return { "prettyPlots": "False", # only pretty plots, only ugly plots, or both
             "keepTopNSRs": 0, # keep an ordered list of <n> most sensitive signal regions
             "drawChi2Line": False, # draw an exclusion line derived from chi2 values in green
             "limitPoints": -1, # limit the number of points to run on
             "axis": None, # the axes to plot; if not given, take from the database
             "style": "", # specify a plotting style
             "plotInverse": False, # 1d plots only, plot ul(mu), not r
             "limitsOnXSecs": True, # 1d plots only, plot ul, not r
             "ratioPlots": True, # create ratioplots if possible
             "bestSRPlots": True, # create best SR plots if meaningful
             "legendplacement": "automatic", # specify how the legend is placed
             "weightedAgreementFactor": False, # weight the points for the agreement factor?
             "extraInfo": False, # add extra info to the plot?
             "validationFolder": "validation", # folder that stores the validation files
             "useFullJsonLikelihoods": False, # use the full JSON likelihood files
             "forceOneD": False, # force the plot to be interpreted as 1d
             "tempdir": None, # name of the tempdir
             "timeOut": 5000, # timeout per point, in seconds
             "pngPlots": True, # also png plots?
             "recordPlotCreation": False, # record the plot creation?
             "pdfPlots": True, # also pdf plots?
             "significances": False, # significance plot instead of ul plot?
             "continue": False, # continue old productions
             "ratio_comment": None, # comment in ratio plot
             "expectationType": "aposteriori",
             "spey": False, # use spey statistics
             "writeoutyields": False, # write out the yields, for NNs
             "databasepath": "../../smodels-database", # SModelS database
             "minmassgap": 2.0, # the min mass gap in SModelS
             "minmassgapISR": 1.0, # the min mass gap for ISR in SModelS
             "sigmacut": 0.000000001, # sigmacut in SModelS
             "useTevatronCLsConstruction": False, # use tevatron CLs construction
             "asimovIsExpected": False, # asimov data is expected data
             "moreNLLs": True, # write out also nllA, nllE, nllEA
             "maxcond": 1.0, # maximum allowed condition violation in SModelS
             "promptWidth": 1.1, # particles with width above this value are stable
             "drawExpected": "auto", # draw expected exclusion lines (True,False,auto)
             "preliminary": "False", # add label 'preliminary' to plot?
             "model": "default", # which model to use (default = mssm)
             "show": False, # show image after producing it?
             "interpolationType": "cubic", # interpolation type for matplotlib plots
             "ncpus": -4, # number of processes; zero or negative subtracts from nCPU
             "drawPaperPlot": True, # draw the red-black paper plot
             "createSModelSExclJson": True, # create SModelS exclusion JSON file
             "origValidationFolder": "validation", # folder for the -orig information
             "errorsForR": False, # one-sigma band for expected UL values
             "nnErrors": False, # get the heteroskedastic errors
             "removeMLModels": False, # remove existing ML models, use full models
             # runValidation derives this from its config file (None means on demand)
             "generateData": None }


def defaultSpecificOptions () -> dict:
    """ the default PaperPlot-specific options; keep in sync with
    pp_specific_options in runValidation.py """
    return { "drawbestsr": False, "drawobsofficialpm1": False,
             "drawexpofficialpm1": True, "drawobspm1": False,
             "title_fontsize": 12, "sort_segments": True,
             "sort_within_segments": False,
             "guess_blueband": True,
             "max_y": "auto", "min_y": "auto", "min_x": "auto", "max_x": "auto",
             "style": "default", "remove_segments": None,
             "addlogo": True, "show_points": False, "pdf_also": False }


def _str2bool ( value : Union[bool,str] ) -> bool:
    """ convert a command line value to a bool """
    if isinstance ( value, bool ):
        return value
    svalue = str ( value ).strip().lower()
    if svalue in [ "true", "yes", "1", "on" ]:
        return True
    if svalue in [ "false", "no", "0", "off" ]:
        return False
    raise argparse.ArgumentTypeError ( f"expected a boolean, got '{value}'" )


def _str2drawExpected ( value : Union[bool,str] ) -> Union[bool,str]:
    """ convert the drawExpected option, which also accepts 'auto' """
    svalue = str ( value ).strip().lower()
    if svalue in [ "true", "yes", "1" ]:
        return True
    if svalue in [ "false", "no", "0" ]:
        return False
    return value


def _str2generateData ( value : Optional[Union[bool,str]] ) -> Optional[bool]:
    """ convert the generateData option (True, False or None/ondemand) """
    if value is None or isinstance ( value, bool ):
        return value
    svalue = str ( value ).strip().lower()
    if svalue in [ "true", "yes", "1" ]:
        return True
    if svalue in [ "false", "no", "0" ]:
        return False
    if svalue in [ "none", "ondemand" ]:
        return None
    raise argparse.ArgumentTypeError (
            f"expected a boolean or 'ondemand', got '{value}'" )


def _addOptionArguments ( ap, prefix : str, defaults : dict,
        description : str, skip : tuple = () ) -> None:
    """ add one command line argument per option in defaults """
    group = ap.add_argument_group ( description )
    for key, default in defaults.items():
        if key in skip:
            continue
        kwargs = { "dest": f"{prefix}_{key}", "default": default,
                   "help": f"default: {default!r}" }
        if key == "drawExpected":
            kwargs.update ( type = _str2drawExpected, metavar = "BOOL|auto" )
        elif key == "generateData":
            kwargs.update ( type = _str2generateData, nargs = "?",
                    const = True, metavar = "BOOL|ondemand" )
        elif isinstance ( default, bool ):
            kwargs.update ( type = _str2bool, nargs = "?", const = True,
                    metavar = "BOOL" )
        elif isinstance ( default, int ):
            kwargs.update ( type = int, metavar = "INT" )
        elif isinstance ( default, float ):
            kwargs.update ( type = float, metavar = "FLOAT" )
        else:
            kwargs.update ( type = str, metavar = "STR" )
        group.add_argument ( f"--{prefix}-{key}", **kwargs )


def _matchingTxnames ( expRes, txname : str ) -> list:
    """ return the txname objects of expRes that match txname, without duplicates """
    txnames, seen = [], set()
    for tx in expRes.getTxNames():
        if tx.txName != txname or tx.txName in seen:
            continue
        txnames.append ( tx )
        seen.add ( tx.txName )
    return txnames


def _axesForTxname ( tx ) -> list:
    """ return the axes of a TxName object, using the same precedence as
    runValidation """
    if hasattr ( tx, "_axes" ):
        return tx._axes if isinstance ( tx._axes, list ) else [ tx._axes ]
    if hasattr ( tx, "axes" ):
        return tx.axes if isinstance ( tx.axes, list ) else [ tx.axes ]
    if hasattr ( tx, "axesMap" ):
        return tx.axesMap if isinstance ( tx.axesMap, list ) else [ tx.axesMap ]
    return []


def _normalizeAxes ( axes : str ) -> str:
    """ standardize an axes string the same way runValidation does """
    try:
        from sympy import var
        x, y, z, w = var ( "x y z w" )
        return str ( eval ( str ( axes ) ) )
    except Exception:
        return str ( axes ).strip()


def _drawPaperPlot ( valPlot, general_options : dict,
        specific_options : dict ) -> bool:
    """ draw the paper plot for an existing validation plot; this mirrors
    runValidation.drawPaperPlot """
    if not general_options.get ( "drawPaperPlot", True ):
        return False
    axis = valPlot.niceAxes
    if not "y" in axis:
        print ( "[drawPaperPlot] axis is 1d, skipping drawPaperPlot" )
        return False
    if not hasattr ( valPlot, "combine" ) or valPlot.combine == False:
        print ( "[drawPaperPlot] this is not an sr-combine plot: skipping "
                "production of red-black paper plot." )
        return False

    plot = PaperPlot ( valPlot, general_options, specific_options )
    if "off" in valPlot.txName:
        ## add onshell exclusion curves
        onshellTxName = valPlot.txName.replace ( "off", "" )
        obs = valPlot.getOfficialCurves ( True, False, onshellTxName )
        doTransformCoords = False
        if len ( obs ) == 0 and "x - y" in valPlot.axes:
            axes = valPlot.axes.replace ( "x - y", "y" )
            obs = valPlot.getOfficialCurves ( True, False, onshellTxName, axes )
            doTransformCoords = True
        valPlot.addToOfficialCurves ( obs, doTransformCoords )
        exp = valPlot.getOfficialCurves ( True, True, onshellTxName )
        if len ( exp ) == 0 and "x - y" in valPlot.axes:
            axes = valPlot.axes.replace ( "x - y", "y" )
            exp = valPlot.getOfficialCurves ( True, True, onshellTxName, axes )
        valPlot.addToOfficialCurves ( exp, doTransformCoords )

    try:
        of = plot.draw()
    except ( RuntimeError, ) as e:
        print ( f"[drawPaperPlot] RunTimeError when plotting red-and-black "
                f"plot: {e}" )
        return False
    if general_options.get ( "show" ) and of is not None:
        from validationHelpers import showPlot
        for f in of:
            showPlot ( f )
    return True


def _dataSelection ( dataselector : str ) -> Tuple[list[str], list[str], bool]:
    """ translate a runValidation-style data selector into database filters """
    if dataselector == "combined":
        return [ "efficiencyMap" ], [ "all" ], True
    if dataselector == "efficiencyMap":
        return [ "efficiencyMap" ], [ "all" ], False
    if dataselector == "upperLimit":
        return [ "upperLimit" ], [ "all" ], False
    if dataselector == "all":
        return [ "all" ], [ "all" ], False
    return [ "efficiencyMap" ], [ x.strip() for x in dataselector.split ( "," ) ], False


if __name__ == "__main__":
    generalDefaults = defaultGeneralOptions()
    specificDefaults = defaultSpecificOptions()
    ap = argparse.ArgumentParser (
            description = "Draw the red-black paper plot for a validation plot.",
            formatter_class = argparse.RawDescriptionHelpFormatter,
            epilog = "General and PaperPlot-specific options can be set with "
                     "--general-<name> and --specific-<name>. Their defaults "
                     "are the same as in runValidation.py." )
    ap.add_argument ( "analysis", help = "analysis id, e.g. ATLAS-SUSY-2019-09" )
    ap.add_argument ( "txname", help = "txname, e.g. TChiWZoff" )
    ap.add_argument ( "axes", nargs = "?", default = None,
            help = "axes string; if omitted, all axes of the txname are used" )
    ap.add_argument ( "-d", "--database", default = generalDefaults["databasepath"],
            help = "path to the SModelS database folder or pickle file "
                   f"[{generalDefaults['databasepath']}]" )
    ap.add_argument ( "-D", "--dataselector", default = "combined",
            choices = [ "combined", "efficiencyMap", "upperLimit", "all" ],
            help = "database selection, as in runValidation [combined]" )
    ap.add_argument ( "-k", "--kfactor", type = float, default = 1.0,
            help = "k-factor [1.0]" )
    ap.add_argument ( "-f", "--force-build", action = "store_true",
            help = "force rebuilding the database pickle from the text files" )
    ap.add_argument ( "--keep", action = "store_true",
            help = "keep temporary directories" )
    ap.add_argument ( "-s", "--show", action = "store_true",
            help = "show the plots after producing them" )
    ap.add_argument ( "-v", "--verbose", default = "info",
            choices = [ "error", "warning", "info", "debug" ],
            help = "logging verbosity [info]" )
    _addOptionArguments ( ap, "general", generalDefaults, "general options",
            skip = ( "show", ) )
    _addOptionArguments ( ap, "specific", specificDefaults,
            "PaperPlot-specific options" )
    ap.add_argument ( "--guess_blueband", dest = "guess_blueband",
            type = _str2bool, nargs = "?", const = True, default = None,
            help = "guess how to draw the blue error band around the blue "
                   "central line; ignores sort_segments and "
                   "sort_within_segments for the blue band [true]" )
    args = ap.parse_args()

    general_options = { key : getattr ( args, f"general_{key}",
                                              generalDefaults[key] )
                        for key in generalDefaults }
    general_options["databasepath"] = args.database
    if args.show:
        general_options["show"] = True
    specific_options = { key : getattr ( args, f"specific_{key}" )
                         for key in specificDefaults }
    if args.guess_blueband is not None:
        specific_options["guess_blueband"] = args.guess_blueband

    from smodels.base import smodelsLogging
    smodelsLogging.setLogLevel ( args.verbose )

    from smodels.experiment.databaseObj import Database
    import validationObjs, graphsValidationObjs
    from validationHelpers import getAxisType

    databasePath = os.path.expanduser ( args.database )
    buPath = databasePath
    if os.path.isdir ( databasePath ) and \
            os.path.exists ( os.path.join ( databasePath, "validation.pcl" ) ):
        buPath = os.path.join ( databasePath, "validation.pcl" )
    force_load = "txt" if args.force_build else None
    db = Database ( buPath, force_load, subpickle = True )

    dataTypes, datasetIDs, combine = _dataSelection ( args.dataselector )
    expResList = db.getExpResults ( [ args.analysis ], datasetIDs,
            [ args.txname ], dataTypes, useNonValidated = True )
    if not expResList:
        print ( f"[drawPaperPlot] no experimental result found for "
                f"{args.analysis}:{args.txname}" )
        sys.exit ( 1 )
    if not combine:
        print ( "[drawPaperPlot] this is not an sr-combine plot: skipping "
                "production of red-black paper plot." )
        sys.exit ( 0 )

    nplots = 0
    for expRes in expResList:
        txnames = _matchingTxnames ( expRes, args.txname )
        if not txnames:
            continue
        for tx in txnames:
            axis = args.axes
            if axis is None:
                axis = general_options.get ( "axis" )
            if axis not in [ None, "None", "" ]:
                axesList = [ axis ]
            else:
                axesList = _axesForTxname ( tx )
            seenAxes = set()
            for axes in axesList:
                axes = _normalizeAxes ( axes )
                if axes in seenAxes:
                    continue
                seenAxes.add ( axes )
                plotClass = graphsValidationObjs.ValidationPlot \
                        if getAxisType ( axes ) == "v3" \
                        else validationObjs.ValidationPlot
                localOptions = general_options.copy()
                try:
                    valPlot = plotClass ( expRes, tx.txName, axes, db,
                            slhadir = None, options = localOptions,
                            kfactor = args.kfactor, namedTarball = None,
                            keep = args.keep, combine = combine )
                except Exception as e:
                    print ( f"[drawPaperPlot] could not create validation "
                            f"plot for {args.txname}:{axes}: {e}" )
                    continue
                if _drawPaperPlot ( valPlot, localOptions, specific_options ):
                    nplots += 1
    if nplots == 0:
        print ( f"[drawPaperPlot] no paper plot produced for "
                f"{args.analysis}:{args.txname}" )
        sys.exit ( 1 )
