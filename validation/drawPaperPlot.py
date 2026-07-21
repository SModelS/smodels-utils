#!/usr/bin/env python3

"""Drawing red-black paper plots for validation comparison.

This module provides the PaperPlot class for generating publication-quality
comparison plots between official exclusion limits and SModelS predictions.
Produces paired observed and expected exclusion limit plots.
"""

__all__ = ["PaperPlot"]

import os
import random
import json
from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np

from smodels_utils.helper.prettyDescriptions import prettyDecay
from smodels_utils.helper.terminalcolors import RED, RESET, YELLOW
from smodels_utils.helper.various import pngMetaInfo
from validationHelpers import (
    getAxisType, prettyAxes, axisV2ToV3, getNiceAxes,
)


def fill_between_polylines(
    ax, x1: np.ndarray, y1: np.ndarray,
    x2: np.ndarray, y2: np.ndarray, **kwargs
):
    """Fill the area between two polylines with a polygon patch.

    :param ax: matplotlib axes to draw on
    :param x1, y1: coordinates of the first polyline
    :param x2, y2: coordinates of the second polyline (reversed for closure)
    :param kwargs: additional keyword arguments passed to Polygon
    :returns: the Polygon patch
    """
    from matplotlib.patches import Polygon
    verts = np.vstack([
        np.column_stack([x1, y1]),
        np.column_stack([x2[::-1], y2[::-1]]),
    ])
    poly = Polygon(verts, closed=True, **kwargs)
    ax.add_patch(poly)
    ax.autoscale_view()
    return poly


def yvalsAreWidths(
    y_label: str, x_vals: list, y_vals: list
) -> tuple[list, list]:
    """Convert y-values from widths (log10) to linear scale if plotting Gamma.

    When the y-axis represents decay width (Gamma), the y-values are stored
    as log10(width). This function converts them to linear scale and
    truncates at large discontinuities.

    :param y_label: the y-axis label string
    :param x_vals: x-coordinate values (may be nested list of segments)
    :param y_vals: y-coordinate values (log10 of width)
    :returns: tuple of (x_vals, y_vals) with y_vals converted if applicable
    """
    if "Gamma" not in y_label:
        return x_vals, y_vals
    if not isinstance(x_vals[0], list):
        return x_vals, y_vals

    y_vals = [10 ** y for y in y_vals]
    y_diff = [y_vals[i + 1] / y_vals[i] for i in range(len(y_vals) - 1)]
    index_max_diff = -1
    if len(y_diff) > 0 and max(y_diff) > 100:
        index_max_diff = y_diff.index(max(y_diff)) + 1
    return x_vals[:index_max_diff], y_vals[:index_max_diff]


class PaperPlot:
    """Generates publication-quality red-black paper plots.

    Produces paired observed and expected exclusion limit plots comparing
    official experimental results with SModelS predictions (best SR,
    combined SR, and optionally original pyhf implementations).

    :param validationPlot: validation plot object containing experimental data
    :param general_options: general plotting options (e.g. errorsForR)
    :param specific_options: plot-specific options (e.g. style, drawbestsr)
    """

    def __init__(
        self,
        validationPlot,
        general_options: dict,
        specific_options: dict,
    ) -> None:
        self.validationPlot = validationPlot
        self.general_options = general_options
        self.specific_options = specific_options

    # ------------------------------------------------------------------ #
    #  Logging & Formatting
    # ------------------------------------------------------------------ #

    def pprint(self, *args) -> None:
        """Print a message prefixed with [drawPaperPlot]."""
        print(f"[drawPaperPlot] {''.join(map(str, *args))}")

    def prettyPath(self, path: str) -> str:
        """Replace the home directory with ~ for compact display.

        :param path: absolute file path
        :returns: path with home directory replaced by ~
        """
        return path.replace(os.environ["HOME"], "~")

    def getPrettyProcessName(self, txname: str) -> str:
        """Get the pretty-printed LaTeX process name for a txname.

        :param txname: the transaction name (e.g. 'TChiWZ')
        :returns: LaTeX-formatted process description
        """
        return prettyDecay(txname, latex=True)

    def getPrettyAxisLabels(self, label: str) -> str:
        """Convert a raw axis label to a pretty LaTeX-formatted label.

        :param label: raw axis label string (e.g. 'm(chi)' or 'Gamma(t)')
        :returns: formatted label with units (e.g. '$m_{\\chi}$ [GeV]')
        """
        particle = label.replace("(", "").replace(")", "").replace("$", "")
        particle = particle.split("m_")[-1]
        if len(particle) and "m" in particle[0]:
            return f"$m_{{{particle[1:]}}}$ [GeV]"
        if "Gamma" in particle:
            if "Gamma_" not in particle:
                return "$\\Gamma_{" + particle.split("Gamma")[-1] + "}$ [GeV]"
            return f"${particle}$ [GeV]"
        return f"$m_{{{particle}}}$ [GeV]"

    def widthToLifetime(self, y: np.ndarray) -> np.ndarray:
        """Convert decay width (GeV) to lifetime (seconds).

        Used as a matplotlib transform for secondary y-axes on Gamma plots.

        :param y: array of width values in GeV
        :returns: array of lifetime values in seconds
        """
        hbar = 6.58e-16  # GeV * s
        shape = y.shape
        new_y = y.flatten()
        new_y[new_y == 0.0] = 1e-20
        new_y *= 1e9
        new_y = np.reshape(new_y, shape)
        return hbar / new_y

    # ------------------------------------------------------------------ #
    #  Coordinate & Data Access
    # ------------------------------------------------------------------ #

    def getCoordsFromLine(
        self, curve: dict, entry: str, coord: str
    ) -> list:
        """Extract coordinate values from a curve entry.

        :param curve: the curve dictionary
        :param entry: entry key (e.g. 'obsExclusion', 'expExclusion')
        :param coord: coordinate to extract ('x' or 'y')
        :returns: list of coordinate values
        """
        if entry not in curve:
            return []
        if coord in curve[entry]:
            return curve[entry][coord]
        values = []
        for line in curve[entry]:
            one_curve = []
            for d in line:
                if coord in d:
                    one_curve.append(d[coord])
            values.append(one_curve)
        return values

    def getCoords(
        self, efile: dict, curve: str, entry: str, coord: str
    ) -> list:
        """Get coordinates from an exclusion file entry.

        :param efile: the exclusion file dictionary
        :param curve: the curve name key
        :param entry: entry key (e.g. 'obsExclusion')
        :param coord: coordinate to extract ('x' or 'y')
        :returns: coordinate values
        """
        if "schema_version" in efile and efile["schema_version"] == "2.0":
            if entry in efile[curve]:
                return self.getCoordsFromLine(efile[curve], entry, coord)
            return []
        return efile[curve][entry][coord]

    def getExtremeValue(
        self, excl_line: list, extreme: str, e_type: str,
        width: bool = False,
    ) -> float:
        """Get the extreme (min or max) value from an exclusion line.

        :param excl_line: list of values (may be nested list of segments)
        :param extreme: 'min' or 'max'
        :param e_type: type of exclusion ('official', 'bestSR', 'comb')
        :param width: if True, values are log10(width) and must be converted
        :returns: the extreme value, or inf/-1 for empty lines
        """
        if len(excl_line) == 0:
            return -1 if extreme == "max" else np.inf
        if isinstance(excl_line[0], list):
            excl_line = sum(excl_line, [])

        if e_type == "official":
            return max(excl_line) if extreme == "max" else min(excl_line)

        values = [10 ** y for y in excl_line] if width else excl_line
        if len(values) == 0:
            return -1 if extreme == "max" else np.inf
        return max(values) if extreme == "max" else min(values)

    def getRange(
        self, lines: dict, whatExcl: str, whatVar: str
    ) -> tuple[float, float]:
        """Get the min/max range across multiple exclusion line collections.

        :param lines: dict of {name: excl_lines} (e.g. {'official': ...})
        :param whatExcl: which exclusion to query (e.g. 'obsExclusion')
        :param whatVar: which variable (e.g. 'x' or 'y')
        :returns: (min, max) tuple
        """
        min_var, max_var = float("inf"), -float("inf")
        for name, line in lines.items():
            if whatExcl not in line:
                continue
            if whatVar in line[whatExcl]:
                max_tmp = self.getExtremeValue(
                    line[whatExcl][whatVar], extreme="max", e_type=name
                )
                min_tmp = self.getExtremeValue(
                    line[whatExcl][whatVar], extreme="min", e_type=name
                )
                min_var = min(min_var, min_tmp)
                max_var = max(max_var, max_tmp)
        return min_var, max_var

    def getRanges(self, lines: dict) -> dict:
        """Compute axis ranges for both observed and expected plots.

        Harmonizes ranges between observed and expected and applies any
        user-specified min/max overrides from specific_options.

        :param lines: dict of exclusion line collections
        :returns: dict with keys like 'min_obs_x', 'max_obs_x', etc.
        """
        r: dict = {}
        r["min_obs_x"], r["max_obs_x"] = self.getRange(
            lines, "obsExclusion", "x"
        )
        r["min_obs_y"], r["max_obs_y"] = self.getRange(
            lines, "obsExclusion", "y"
        )
        r["min_exp_x"], r["max_exp_x"] = self.getRange(
            lines, "expExclusion", "x"
        )
        r["min_exp_y"], r["max_exp_y"] = self.getRange(
            lines, "expExclusion", "y"
        )

        min_x = min(r["min_obs_x"], r["min_exp_x"])
        max_x = max(r["max_obs_x"], r["max_exp_x"])
        min_y = min(r["min_obs_y"], r["min_exp_y"])
        max_y = max(r["max_obs_y"], r["max_exp_y"])

        for axis in ("min_y", "max_y", "min_x", "max_x"):
            val = self.specific_options.get(axis)
            if val in (None, "auto"):
                continue
            if axis == "max_y":
                max_y = float(val) / 2.0
            elif axis == "min_y":
                min_y = float(val)
            elif axis == "max_x":
                max_x = float(val)
            elif axis == "min_x":
                min_x = float(val)

        r["min_obs_x"] = r["min_exp_x"] = min_x
        r["max_obs_x"] = r["max_exp_x"] = max_x
        r["min_obs_y"] = r["min_exp_y"] = min_y
        r["max_obs_y"] = r["max_exp_y"] = max_y
        return r

    def countDataSets(self, validationPlot) -> dict:
        """Count the number of signal and control regions.

        :param validationPlot: the validation plot object
        :returns: dict with 'ver' (stat model version), 'num_sr', 'num_cr'
        """
        gI = validationPlot.expRes.globalInfo
        num_sr, num_cr = 0, 0
        ver = "1bin"

        if hasattr(gI, "statModels"):
            ver = "(pyhf)"
            for srSetName, model_types in gI.statModels.items():
                for model_type in model_types:
                    if model_type[0] == "onnx":
                        ver = "(nn)"
                        break

        g_dict: dict = {}
        if hasattr(gI, "regionMappings"):
            for label, region in gI.regionMappings.items():
                g_dict[region["smodels"]] = region

        for ds in validationPlot.expRes.datasets:
            name = ds.dataInfo.dataId
            if name in g_dict:
                t = g_dict[name]["type"]
                assert t in ("SR", "CR"), f"Unknown region type {t}"
                if t == "SR":
                    num_sr += 1
                elif t == "CR":
                    num_cr += 1

        if hasattr(gI, "covariance"):
            ver = "(SLv1)"
        if hasattr(validationPlot.expRes.datasets[0].dataInfo, "thirdMoment"):
            ver = "(SLv2)"

        return {"ver": ver, "num_sr": num_sr, "num_cr": num_cr}

    # ------------------------------------------------------------------ #
    #  Data Processing
    # ------------------------------------------------------------------ #

    def add_jitter(
        self, y_vals: list, addJitter: bool, delta: float = 0.02
    ) -> list:
        """Add small random jitter to y-values for visual separation.

        :param y_vals: y-coordinate values (may contain nested lists)
        :param addJitter: if False, return values unchanged
        :param delta: fractional jitter range (default +/-2%)
        :returns: modified y_vals with jitter applied
        """
        if not addJitter:
            return y_vals
        for i, y in enumerate(y_vals):
            if isinstance(y, list):
                for j, yy in enumerate(y):
                    y_vals[i][j] = yy * random.uniform(1 - delta, 1 + delta)
            else:
                y_vals[i] = y * random.uniform(1 - delta, 1 + delta)
        return y_vals

    def removeSegments(
        self, x_val: list[float], y_val: list[float], label: str = ""
    ) -> tuple[list[float], list[float]]:
        """Remove line segments falling within the remove_segments bounding box.

        :param x_val: x-coordinate values for one segment
        :param y_val: y-coordinate values for one segment
        :param label: label for debugging output
        :returns: (x_val, y_val) with points inside the box removed
        """
        if self.specific_options["remove_segments"] in (None, []):
            return x_val, y_val

        rec = self.specific_options["remove_segments"]
        if isinstance(rec, str):
            rec = eval(rec)
        assert isinstance(rec, list), (
            f"remove_segments {rec} needs to be a list of lists"
        )

        xmin, xmax = rec[0][0], rec[1][0]
        ymin, ymax = rec[0][1], rec[1][1]
        ret_x, ret_y = [], []
        for x, y in zip(x_val, y_val):
            if xmin < x < xmax and ymin < y < ymax:
                continue
            ret_x.append(x)
            ret_y.append(y)
            if "official" in label:
                print(f"{x,y} survived {label}")
        return ret_x, ret_y

    def removeAllSegments(
        self, x_vals: list, y_vals: list, label: str = "all"
    ) -> tuple[list, list]:
        """Remove segments from all polyline segments.

        :param x_vals: list of x-coordinate lists (one per segment)
        :param y_vals: list of y-coordinate lists (one per segment)
        :param label: label for debugging output
        :returns: (x_vals, y_vals) with filtered segments
        """
        nx_vals, ny_vals = [], []
        for x_val, y_val in zip(x_vals, y_vals):
            x_val, y_val = self.removeSegments(x_val, y_val, label=label)
            nx_vals.append(x_val)
            ny_vals.append(y_val)
        return nx_vals, ny_vals

    def sortSegments(
        self, x_vals: list, y_vals: list
    ) -> tuple[list, list]:
        """Sort polyline segments by their minimum x-value.

        Segments with lower minimum x-values come first.

        :param x_vals: list of x-coordinate lists
        :param y_vals: list of y-coordinate lists
        :returns: (x_vals, y_vals) with segments sorted by min x
        """
        if len(x_vals) == 1:
            return x_vals, y_vals

        dct: dict = {}
        for seg_x, seg_y in zip(x_vals, y_vals):
            min_x = min(seg_x)
            while min_x in dct:
                min_x += 1e-8
            dct[min_x] = {"x": seg_x, "y": seg_y}

        keys = sorted(dct.keys(), reverse=True)
        new_x = [dct[k]["x"] for k in keys]
        new_y = [dct[k]["y"] for k in keys]
        return new_x, new_y

    def sortWithinSegments(
        self, x_vals: list, y_vals: list
    ) -> tuple[list, list]:
        """Ensure x-values within each segment are in ascending order.

        If a segment's x-values go from large to small, the segment
        is reversed to ensure consistent ordering.

        :param x_vals: list of x-coordinate lists
        :param y_vals: list of y-coordinate lists
        :returns: (x_vals, y_vals) with consistently ordered segments
        """
        new_x, new_y = [], []
        for seg_x, seg_y in zip(x_vals, y_vals):
            n = len(seg_x)
            x_f, x_m, x_l = seg_x[0], seg_x[n // 2], seg_x[-1]
            if x_f <= x_m <= x_l:
                new_x.append(seg_x)
                new_y.append(seg_y)
            else:
                new_x.append(seg_x[::-1])
                new_y.append(seg_y[::-1])
        return new_x, new_y

    # ------------------------------------------------------------------ #
    #  Exclusion Line Fetching
    # ------------------------------------------------------------------ #

    def fetchOfficialExclusionLines(self, axes: str) -> dict:
        """Fetch official exclusion curves and convert to internal format.

        :param axes: the axis specification string
        :returns: dict with keys like 'obsExclusion', 'expExclusion',
                  and optionally 'P1'/'M1' sigma variants
        """

        def fetchPointsNewFormat(
            curves: list, idx: int = 0, x_minus_y: bool = False
        ) -> dict:
            ret: dict = {"x": [], "y": []}
            for segment in curves[idx]["points"]:
                for point in segment:
                    x = point["x"]
                    ret["x"].append(x)
                    if "y" in point:
                        y = point["y"]
                        if x_minus_y:
                            y = x - y
                        ret["y"].append(y)
            return ret

        def fetchPointsOldFormat(
            curves: list, idx: int = 0, x_minus_y: bool = False
        ) -> dict:
            ret: dict = {"x": [], "y": []}
            points = curves[idx]["points"]
            for x, y in zip(points["x"], points["y"]):
                ret["x"].append(x)
                if x_minus_y:
                    y = x - y
                ret["y"].append(y)
            return ret

        def fetchPoints(curves: list, idx: int = 0) -> dict:
            """Fetch points, detecting whether axes need x-y transform."""
            if len(curves) == 0:
                return {}
            c_axes = axes.replace(" ", "")
            m_axes = curves[idx]["name"].replace(" ", "")
            x_minus_y = (
                ("x-y" in c_axes and "x-y" not in m_axes)
                or ("x-y" in m_axes and "x-y" not in c_axes)
            )
            points = curves[idx]["points"]
            if isinstance(points, list):
                return fetchPointsNewFormat(curves, idx, x_minus_y)
            return fetchPointsOldFormat(curves, idx, x_minus_y)

        def getIndex(curves: list, pm1: str) -> Optional[int]:
            """Find curve index by sigma label ('' for central, 'P1'/'M1')."""
            for idx, curve in enumerate(curves):
                if pm1 != "" and pm1 in curve["name"]:
                    return idx
                if pm1 == "" and "P1" not in curve["name"] \
                        and "M1" not in curve["name"]:
                    return idx
            return None

        vPlot = self.validationPlot
        ret: dict = {}

        c_idx = getIndex(vPlot.officialCurves, "")
        ret["obsExclusion"] = fetchPoints(vPlot.officialCurves, c_idx)

        if self.specific_options.get("drawobsofficialpm1"):
            for suffix in ("P1", "M1"):
                key = f"obsExclusion{suffix}"
                idx = getIndex(vPlot.officialCurves, suffix)
                if idx is not None:
                    ret[key] = fetchPoints(vPlot.officialCurves, idx)

        c_idx = getIndex(vPlot.expectedOfficialCurves, "")
        ret["expExclusion"] = fetchPoints(vPlot.expectedOfficialCurves, c_idx)

        if self.specific_options.get("drawexpofficialpm1"):
            for suffix in ("P1", "M1"):
                key = f"expExclusion{suffix}"
                idx = getIndex(vPlot.expectedOfficialCurves, suffix)
                if idx is not None:
                    ret[key] = fetchPoints(vPlot.expectedOfficialCurves, idx)

        return ret

    def findAxisInExclFile(
        self, axis: str, exclfile: dict, txname: str, typ: str
    ) -> Optional[dict]:
        """Find axis entry in exclusion file, trying v2/v3 variants.

        :param axis: axis specification string
        :param exclfile: the exclusion file dictionary
        :param txname: transaction name
        :param typ: type (e.g. 'comb', 'bestSR', 'combined')
        :returns: curve dict or None if not found
        """
        name = f"{txname}_{typ}_{axis}"
        if name in exclfile:
            return exclfile[name]
        if getAxisType(axis) == "v2":
            v3axis = axisV2ToV3(axis)
            name = f"{txname}_{typ}_{v3axis}"
            if name in exclfile:
                return exclfile[name]
        if typ == "comb":
            return self.findAxisInExclFile(axis, exclfile, txname, "combined")
        return None

    def coordinateTransform(
        self, excl_lines: dict, axes: str, eval_axes: bool
    ) -> dict:
        """Apply x-y coordinate transformation if axes specify x-y.

        When axes are expressed as 'x - y', this computes the difference
        between x and y coordinates for each exclusion line.

        :param excl_lines: exclusion lines dict
        :param axes: axis specification string
        :param eval_axes: if True, apply the x-y = x - y transform
        :returns: transformed exclusion lines
        """
        if ("x - y" in axes or "x-y" in axes) and eval_axes:
            for typ, excl in excl_lines.items():
                excl_y = []
                for l_x, l_y in zip(excl["x"], excl["y"]):
                    excl_y.append(
                        (np.array(l_x) - np.array(l_y)).tolist()
                    )
                excl_lines[typ] = {"x": excl["x"], "y": excl_y}
        return excl_lines

    def getOnshellAxesForOffshell(
        self, anaDir: str, tx_onshell: str, validationFolder: str
    ) -> Optional[str]:
        """Determine the axes for the onshell version of an offshell topology.

        :param anaDir: path to the analysis directory
        :param tx_onshell: the onshell transaction name
        :param validationFolder: validation subfolder name
        :returns: axes string if found, None otherwise
        """
        fname = f"{anaDir}/{validationFolder}/SModelS_ExclusionLines.json"
        if not os.path.exists(fname):
            self.pprint(f"{self.prettyPath(fname)} does not exist")
            return None

        with open(fname) as sm_file, \
             open(f"{anaDir}/exclusion_lines.json") as file:
            excl_file = json.load(file)
            excl_sm = json.load(sm_file)

        sm_file_keys = [k for k in excl_sm if f"{tx_onshell}_" in k]
        check_tx_on = [
            True for k in sm_file_keys
            if f"{tx_onshell}_comb_" in k or f"{tx_onshell}_bestSR_" in k
        ]

        if tx_onshell not in excl_file:
            print(
                f"[drawPaperPlot] {tx_onshell} not found in official excl. "
                "Plotting only offshell"
            )
            return None
        if not sm_file_keys or False in check_tx_on:
            print(
                f"[drawPaperPlot] {tx_onshell} in official excl but not "
                "found in SModelS Json. Plotting only offshell"
            )
            return None

        return sm_file_keys[0].split("_")[-1]

    def addOffshell(
        self, excl_lines: Union[list, dict], excl_off: dict,
        min_off_y: float = 0.0, official: bool = False,
    ) -> Union[list, dict]:
        """Combine onshell and offshell exclusion lines.

        Prepends offshell exclusion data to the onshell exclusion lines,
        handling reversed order and edge cases at the junction.

        :param excl_lines: onshell exclusion lines
        :param excl_off: offshell exclusion lines
        :param min_off_y: minimum y-value threshold for offshell
        :param official: if True, use official min_off_y
        :returns: combined onshell + offshell exclusion lines
        """
        if isinstance(excl_lines, list):
            print("[drawPaperPlot] error: addOffshell for lists not implemented")
            return excl_lines

        for typ, excl in excl_lines.items():
            if excl_off[typ]["x"] == []:
                continue

            # Reverse offshell if x-values are in descending order
            if (excl_off[typ]["x"][0] > excl_off[typ]["x"][-1]
                    or (len(excl_off[typ]["x"]) > 1
                        and excl_off[typ]["x"][1] > excl_off[typ]["x"][-2])):
                excl_off[typ]["x"].reverse()
                excl_off[typ]["y"].reverse()

            if official:
                min_off_y = excl_off[typ]["y"][0]  # noqa: F841

            # Trim offshell tail if y-values drop below start
            if (not isinstance(excl_off[typ]["y"][0], list)
                    and excl_off[typ]["y"][-1] < excl_off[typ]["y"][0]):
                index = [
                    i for i, y in enumerate(excl_off[typ]["y"])
                    if y > excl_off[typ]["y"][0] + 50
                ]
                if len(index) > 0:
                    excl_off[typ]["x"] = excl_off[typ]["x"][:index[-1]]
                    excl_off[typ]["y"] = excl_off[typ]["y"][:index[-1]]

            # Reverse onshell if needed
            if len(excl["x"]) > 0 and excl["x"][0] > excl["x"][-1]:
                excl["x"].reverse()
                excl["y"].reverse()

            # Trim onshell head if it overlaps with offshell tail
            if (len(excl_off[typ]["x"]) > 0
                    and not isinstance(excl_off[typ]["x"][0], list)
                    and len(excl["x"]) > 0
                    and excl_off[typ]["x"][-1] > excl["x"][0]):
                index = [
                    i for i, x in enumerate(excl["x"])
                    if x > excl_off[typ]["x"][-1] + 20
                ]
                if len(index) > 0:
                    excl["x"] = excl["x"][index[0]:]
                    excl["y"] = excl["y"][index[0]:]

            # Prepend offshell to onshell
            excl["x"] = excl_off[typ]["x"] + excl["x"]
            excl["y"] = excl_off[typ]["y"] + excl["y"]

        return excl_lines

    def getCurveFromJson(
        self, anaDir: str, validationFolder: str,
        txname: str, typ: str, axes: str = None,
        eval_axes: bool = True,
    ) -> Union[dict, list]:
        """Get exclusion curves from SModelS JSON files.

        :param anaDir: path to analysis directory
        :param validationFolder: validation subfolder (usually 'validation')
        :param txname: transaction name (e.g. 'TChiWZ')
        :param typ: curve type ('bestSR', 'combined')
        :param axes: axes specification for the exclusion line
        :param eval_axes: if True, apply x-y transformation
        :returns: dict of exclusion lines, or empty dict/list on failure
        """
        fname = f"{anaDir}/{validationFolder}/SModelS_ExclusionLines.json"
        if not os.path.exists(fname):
            self.pprint(f"error: {fname} does not exist!")
            return []
        sfname = self.prettyPath(fname)
        self.pprint(f"we have an exclusion curve file: {sfname}")

        with open(fname) as f:
            excl_file = json.load(f)

        curve = self.findAxisInExclFile(axes, excl_file, txname, typ)
        if curve is None:
            self.pprint(
                f"{txname}:{typ}:{axes.replace(' ', '')} not found in {sfname}"
            )
            if "x - y" in axes:
                axes2 = axes.replace("x - y", "y")
                self.pprint(f"trying now with {axes2}")
                curve = self.findAxisInExclFile(axes2, excl_file, txname, typ)
            if curve is None:
                return {}

        excl_lines: dict = {}
        for key in ("obsExclusion", "obsExclusionP1", "obsExclusionM1",
                     "expExclusion", "expExclusionP1", "expExclusionM1"):
            if key in curve:
                x_ = self.getCoordsFromLine(curve, key, "x")
                y_ = self.getCoordsFromLine(curve, key, "y")
                if len(x_) == 0:
                    pass
                excl_lines[key] = {"x": x_, "y": y_}

        # Also check obs_excl / exp_excl naming convention
        for old_key, new_key in [("obs_excl", "obsExclusion"),
                                  ("exp_excl", "expExclusion")]:
            if old_key in curve and new_key not in excl_lines:
                x_ = self.getCoordsFromLine(curve, old_key, "x")
                y_ = self.getCoordsFromLine(curve, old_key, "y")
                excl_lines[new_key] = {"x": x_, "y": y_}

        return self.coordinateTransform(excl_lines, axes, eval_axes)

    # ------------------------------------------------------------------ #
    #  Plotting Primitives
    # ------------------------------------------------------------------ #

    def plotLines(
        self, ax, x_vals: list, y_vals: list,
        color: str, linestyle: str, label: str,
    ) -> None:
        """Plot one or more line segments on the axes.

        :param ax: matplotlib axes
        :param x_vals: x-coordinates (may be nested list of segments)
        :param y_vals: y-coordinates (may be nested list of segments)
        :param color: line color
        :param linestyle: line style ('solid', 'dashed', 'dotted')
        :param label: legend label
        """
        if len(x_vals) == 0:
            return
        if isinstance(x_vals[0], list):
            for x_val, y_val in zip(x_vals, y_vals):
                x_val, y_val = self.removeSegments(
                    x_val, y_val, label=label
                )
                ax.plot(
                    x_val, y_val, color=color, linestyle=linestyle,
                    label=label,
                )
                label = ""
            return
        ax.plot(
            x_vals, y_vals, color=color, linestyle=linestyle, label=label
        )

    def plotGammaLines(
        self, x_vals: list, y_vals: list, ax, label: str,
        y_label: str, linestyle: Optional[str] = None,
        color: Optional[str] = None,
    ) -> None:
        """Plot lines with jitter and width-to-linear conversion if Gamma.

        :param x_vals: x-coordinates
        :param y_vals: y-coordinates (log10 of width if Gamma)
        :param ax: matplotlib axes
        :param label: legend label
        :param y_label: y-axis label (used to detect Gamma)
        :param linestyle: line style (default: solid)
        :param color: line color (default: red)
        """
        y_vals = self.add_jitter(y_vals, self.addJitter)
        color = color or "red"
        linestyle = linestyle or "solid"
        x_vals, y_vals = yvalsAreWidths(y_label, x_vals, y_vals)
        self.plotLines(ax, x_vals, y_vals, color, linestyle, label)

    def plotErrorBand(
        self, x_vals1: list, y_vals1: list,
        x_vals2: list, y_vals2: list,
        ax, label: str, y_label: str,
        color: Optional[str] = None, alpha: float = 0.4,
    ) -> None:
        """Plot an error band between two sets of exclusion lines.

        :param x_vals1, y_vals1: coordinates of the first boundary
        :param x_vals2, y_vals2: coordinates of the second boundary
        :param ax: matplotlib axes
        :param label: legend label (currently unused in rendering)
        :param y_label: y-axis label (used for width conversion)
        :param color: fill color (default: red)
        :param alpha: transparency (default: 0.4)
        """
        if len(x_vals1) == 0:
            return
        x_vals1, y_vals1 = self.removeAllSegments(
            x_vals1, y_vals1, "error_band"
        )
        x_vals2, y_vals2 = self.removeAllSegments(
            x_vals2, y_vals2, "error_band"
        )

        if self.specific_options.get("sort_segments"):
            x_vals1, y_vals1 = self.sortSegments(x_vals1, y_vals1)
            x_vals2, y_vals2 = self.sortSegments(x_vals2, y_vals2)

        color = color or "red"
        x_vals1, y_vals1 = yvalsAreWidths(y_label, x_vals1, y_vals1)
        x_vals2, y_vals2 = yvalsAreWidths(y_label, x_vals2, y_vals2)

        if self.specific_options.get("sort_segments"):
            x_vals1, y_vals1 = self.sortWithinSegments(x_vals1, y_vals1)
            x_vals2, y_vals2 = self.sortWithinSegments(x_vals2, y_vals2)

        x1s = np.array([])
        x2s = np.array([])
        y1s = np.array([])
        y2s = np.array([])

        for idx in range(max(len(x_vals1), len(x_vals2))):
            if idx < len(x_vals1):
                x1s = np.concatenate([x1s, np.array(x_vals1[idx])])
                y1s = np.concatenate([y1s, np.array(y_vals1[idx])])
            if idx < len(x_vals2):
                x2s = np.concatenate([x2s, np.array(x_vals2[idx])])
                y2s = np.concatenate([y2s, np.array(y_vals2[idx])])

        fill_between_polylines(
            ax, x1s, y1s, x2s, y2s,
            facecolor=color, alpha=alpha, edgecolor=None,
        )

    # ------------------------------------------------------------------ #
    #  Plot Configuration Helpers (extracted from draw)
    # ------------------------------------------------------------------ #

    def _compute_axis_labels(
        self, validationPlot
    ) -> tuple[str, str]:
        """Compute formatted x-axis and y-axis labels from the validation plot.

        :param validationPlot: the validation plot object
        :returns: (x_label, y_label) tuple of formatted label strings
        """
        axis_label = prettyAxes(validationPlot).replace(" ", "")
        axis_label = axis_label.replace("(x,y)", "(xy)")
        axis_label = axis_label.split(",")

        x_label, y_label = "", ""
        for lbl in axis_label:
            if "=(xy)" in lbl:
                x_label = self.getPrettyAxisLabels(
                    lbl.split("=")[0].strip()
                )
                y_label = x_label.replace("m", "\\Gamma")
            elif "=x" in lbl and "=x-" not in lbl:
                x_label = self.getPrettyAxisLabels(
                    lbl.split("=")[0].strip()
                )
            elif "=x-y" in lbl:
                x_l = x_label.replace("[GeV]", "")
                m2 = self.getPrettyAxisLabels(lbl.split("=")[0].strip())
                y_label = x_l + "-" + m2
            elif "x=" in lbl:
                x_label = self.getPrettyAxisLabels(
                    lbl.split("=")[-1].strip()
                )
            elif ("=y" in lbl or "-y" in lbl) and "=y-" not in lbl:
                y_label = self.getPrettyAxisLabels(
                    lbl.split("=")[0].strip()
                )
            elif "y=" in lbl:
                y_label = self.getPrettyAxisLabels(
                    lbl.split("=")[-1].strip()
                )

        y_label = f"${y_label.replace('$', '')}$"
        return x_label, y_label

    def _adjust_gamma_ranges(
        self, ranges: dict, prefix: str,
        off_excl: dict, bestSR: bool, bestSR_excl: dict,
        combSR: bool, comb_excl: dict,
    ) -> int:
        """Compute and apply Gamma-specific y-axis ranges.

        When plotting decay widths (Gamma), the y-axis values need special
        treatment because they are in log10 space.

        :param ranges: ranges dict to modify in-place
        :param prefix: 'obs' or 'exp' for the exclusion type
        :param off_excl: official exclusion lines
        :param bestSR: whether best SR is plotted
        :param bestSR_excl: best SR exclusion lines
        :param combSR: whether combined SR is plotted
        :param comb_excl: combined SR exclusion lines
        :returns: step_y value for axis limit padding
        """
        excl_key = f"{prefix}Exclusion"

        max_val = self.getExtremeValue(
            off_excl[excl_key]["y"], extreme="max", e_type="official"
        )
        min_val = self.getExtremeValue(
            off_excl[excl_key]["y"], extreme="min", e_type="official"
        )
        if bestSR and excl_key in bestSR_excl:
            max_val = max(
                max_val,
                self.getExtremeValue(
                    bestSR_excl[excl_key]["y"], extreme="max",
                    e_type="bestSR", width=True,
                ),
            )
            min_val = min(
                min_val,
                self.getExtremeValue(
                    bestSR_excl[excl_key]["y"], extreme="min",
                    e_type="bestSR", width=True,
                ),
            )
        if combSR and excl_key in comb_excl:
            max_val = max(
                max_val,
                self.getExtremeValue(
                    comb_excl[excl_key]["y"], extreme="max",
                    e_type="comb", width=True,
                ),
            )
            min_val = min(
                min_val,
                self.getExtremeValue(
                    comb_excl[excl_key]["y"], extreme="min",
                    e_type="comb", width=True,
                ),
            )

        ranges[f"max_{prefix}_y"] = max_val
        ranges[f"min_{prefix}_y"] = min_val
        return max_val * 1000

    def _add_gamma_secondary_axis(self, ax) -> None:
        """Add a secondary y-axis showing lifetime corresponding to width.

        :param ax: matplotlib axes with a log-scaled Gamma y-axis
        """
        sec_ax = ax.secondary_yaxis(
            "right",
            functions=(self.widthToLifetime, self.widthToLifetime),
        )
        sec_ax.set_ylabel(r"$\tau$ [s]", fontsize=14)
        sec_ax.set_yscale("log")

    def _compute_titles(
        self, analysis: str, num_sr: int, num_cr: int, pName: str
    ) -> tuple[str, str]:
        """Compute left and right title strings for the plot.

        :param analysis: analysis identifier string (e.g. 'CMS-SUS-19-006')
        :param num_sr: number of signal regions
        :param num_cr: number of control regions
        :param pName: pretty process name in LaTeX
        :returns: (left_title, right_title) tuple
        """
        if num_sr == 1:
            nSRs = "1 SR"
        else:
            nSRs = f"{num_sr} SRs"

        title = f"{analysis}: {nSRs}"
        if num_cr > 0:
            title = f"{analysis}: {num_sr} SRs + {num_cr} CRs"

        right_title = pName
        if self.specific_options.get("style") == "sabine":
            title = f"{analysis}: {pName}"
            right_title = f"{num_sr} SRs + {num_cr} CRs"

        return title, right_title

    def _get_stat_model_label(self, validationPlot) -> str:
        """Determine the SModelS label from the statistical model.

        :param validationPlot: the validation plot object
        :returns: label string (e.g. 'SModelS: NN', 'SModelS: SLv1')
        """
        gI = validationPlot.expRes.globalInfo
        label = "SModelS: comb."
        if not hasattr(gI, "statModels"):
            return label
        for srSetName, model_types in gI.statModels.items():
            mtype = model_types[0][0]
            if mtype == "onnx":
                label = "SModelS: NN"
            elif mtype == "sl":
                ver = validationPlot.expRes.typeOfStatsModel(
                    srSetName, specifySL=True
                ).replace("sl", "SL")
                label = f"SModelS: {ver}"
        return label

    def _get_title_position(self) -> tuple[float, float, int]:
        """Get title position parameters based on plot style.

        :returns: (x_offset, y_offset, font_size)
        """
        if self.specific_options.get("style") == "sabine":
            return 0.25, 0.8, 12
        return 0.55, 0.65, 10

    def _setup_figure(self) -> tuple:
        """Create a new matplotlib figure with standard LaTeX settings.

        :returns: (fig, ax) tuple
        """
        plt.rcParams["text.usetex"] = True
        plt.rcParams["font.family"] = "Cambria Math"
        return plt.subplots(figsize=(5, 4))

    def _save_figure(self, outfile: str) -> None:
        """Save the current figure to disk and close it.

        :param outfile: output file path
        """
        self.pprint(
            f"saving to {YELLOW}{self.prettyPath(outfile)}{RESET}"
        )
        plt.savefig(outfile, dpi=250, metadata=pngMetaInfo())
        plt.clf()
        plt.rcdefaults()
        plt.close()

    def _configure_axes(
        self, ax, ranges: dict, prefix: str,
        x_label: str, y_label: str,
        off_excl: dict, bestSR: bool, bestSR_excl: dict,
        combSR: bool, comb_excl: dict,
    ) -> None:
        """Configure axis labels and limits.

        :param ax: matplotlib axes
        :param ranges: computed axis ranges
        :param prefix: 'obs' or 'exp'
        :param x_label, y_label: axis label strings
        :param off_excl, bestSR_excl, comb_excl: exclusion line dicts
        :param bestSR, combSR: whether these lines are present
        """
        ax.set_xlabel(x_label, fontsize=14)
        ax.set_ylabel(y_label, fontsize=14)

        step_x = int(ranges[f"max_{prefix}_x"] / 100) * 10
        ax.set_xlim([
            int(ranges[f"min_{prefix}_x"] / 10) * 10,
            round(ranges[f"max_{prefix}_x"] + step_x, -1),
        ])

        if "Gamma" in y_label:
            self.pprint(
                f"{RED}FIXME we need to make sure we also deal with the "
                f"multi-line case here, so i x_vals[0]==list{RESET}"
            )
            step_y = self._adjust_gamma_ranges(
                ranges, prefix, off_excl, bestSR, bestSR_excl,
                combSR, comb_excl,
            )
            ax.set_ylim([
                ranges[f"min_{prefix}_y"],
                ranges[f"max_{prefix}_y"] + step_y,
            ])
        else:
            step_y = int(ranges[f"max_{prefix}_y"])
            ax.set_ylim([
                0,
                round(ranges[f"max_{prefix}_y"] + step_y, -1),
            ])

    def _plot_official_with_sigmas(
        self, ax, off_excl: dict, key: str, exp_name: str,
        show_sigmas: bool,
    ) -> None:
        """Plot official exclusion line and optionally its +/-1 sigma variants.

        :param ax: matplotlib axes
        :param off_excl: official exclusion lines dict
        :param key: 'obsExclusion' or 'expExclusion'
        :param exp_name: experiment name for legend
        :param show_sigmas: if True, plot P1/M1 sigma bands
        """
        if key in off_excl and "x" in off_excl[key]:
            self.plotLines(
                ax, off_excl[key]["x"], off_excl[key]["y"],
                "black", "solid", f"{exp_name} official",
            )
        if show_sigmas:
            for suffix in ("P1", "M1"):
                sigma_key = f"{key}{suffix}"
                if sigma_key in off_excl and "x" in off_excl[sigma_key]:
                    self.plotLines(
                        ax, off_excl[sigma_key]["x"],
                        off_excl[sigma_key]["y"],
                        "black", "dotted", None,
                    )

    def _plot_bestSR(
        self, ax, bestSR_excl: dict, key: str,
        y_label: str, addJitter: bool,
    ) -> None:
        """Plot the best SR exclusion line.

        :param ax: matplotlib axes
        :param bestSR_excl: best SR exclusion lines dict
        :param key: 'obsExclusion' or 'expExclusion'
        :param y_label: y-axis label
        :param addJitter: whether to add jitter
        """
        if key not in bestSR_excl:
            return
        x_vals = bestSR_excl[key]["x"]
        y_vals = bestSR_excl[key]["y"]

        if key == "obsExclusion":
            y_vals = self.add_jitter(y_vals, addJitter)

        x_vals, y_vals = yvalsAreWidths(y_label, x_vals, y_vals)
        if "Gamma" in y_label:
            self._add_gamma_secondary_axis(ax)

        self.plotLines(
            ax, x_vals, y_vals, "red", "dashed", "SModelS: best SR"
        )
        plt.tick_params(
            which="major", axis="both", direction="in",
            length=10, top=True, right=True,
        )
        plt.tick_params(
            labelbottom=True, labelleft=True,
            labeltop=False, labelright=False,
        )

    def _extract_plot_info(self) -> Optional[dict]:
        """Extract analysis metadata from the validation plot.

        :returns: dict with analysis info or None if 1D (unsupported)
        """
        vPlot = self.validationPlot
        if vPlot.isOneDimensional():
            print(
                "[drawPaperPlot] currently we don't have 1d versions "
                "of the pretty plots. exiting."
            )
            return None

        analysis = vPlot.expRes.globalInfo.id
        vDir = vPlot.getValidationDir(validationDir=None)
        validationFolder = os.path.basename(vDir)
        anaDir = os.path.dirname(vDir)
        if anaDir.endswith("validation"):
            anaDir = anaDir[:-10]
            validationFolder = f"validation/{validationFolder}"

        txname = vPlot.txName
        axes = vPlot.axes
        saxes = str(axes).replace(" ", "").replace("'", "")
        self.pprint(f"Drawing pretty paper plot for {txname}:{saxes}")

        offshell = False
        txnameOff = ""
        axes_on = axes
        if "off" in txname:
            axes_on = self.getOnshellAxesForOffshell(
                anaDir, txname.split("off")[0], validationFolder
            )
            if axes_on:
                offshell = True
                txnameOff = txname
                txname = txname.split("off")[0]

        if axes_on is None:
            axes_on = axes

        return {
            "analysis": analysis,
            "vDir": vDir,
            "validationFolder": validationFolder,
            "anaDir": anaDir,
            "txname": txname,
            "txnameOff": txnameOff,
            "axes": axes,
            "axes_on": axes_on,
            "offshell": offshell,
        }

    def _fetch_all_exclusion_lines(self, info: dict) -> Optional[dict]:
        """Fetch all exclusion lines (official, bestSR, combined, orig).

        :param info: plot info dict from _extract_plot_info
        :returns: dict of exclusion lines or None on failure
        """
        anaDir = info["anaDir"]
        validationFolder = info["validationFolder"]
        txname = info["txname"]
        txnameOff = info["txnameOff"]
        axes = info["axes"]
        axes_on = info["axes_on"]
        offshell = info["offshell"]

        off_excl = self.fetchOfficialExclusionLines(axes_on)

        bestSR, combSR = self.specific_options["drawbestsr"], True
        bestSR_excl, comb_excl = [], []

        if offshell and bestSR:
            bestSR_excl = self.getCurveFromJson(
                anaDir, validationFolder, txname,
                typ="bestSR", axes=axes_on, eval_axes=False,
            )
            bestSR_excl_off = self.getCurveFromJson(
                anaDir, validationFolder, txnameOff,
                typ="bestSR", axes=axes, eval_axes=False,
            )
            if not bestSR_excl_off:
                self.pprint(
                    f"No best SR SModelS excl line for "
                    f"{self.prettyPath(anaDir)}:{txnameOff}. "
                    "Not drawing paper plot."
                )
                return None
            bestSR_excl = self.addOffshell(bestSR_excl, bestSR_excl_off)
        else:
            bestSR_excl = self.getCurveFromJson(
                anaDir, validationFolder, txname,
                typ="bestSR", axes=axes,
            )
            if not bestSR_excl:
                self.pprint(
                    f"No best SR SModelS excl line for "
                    f"{self.prettyPath(anaDir)}:{txname}:{axes}."
                )
                return None

        origDir = anaDir.replace("-eff", "-CR")
        cr_is = "CR"
        if not os.path.exists(origDir):
            origDir = anaDir.replace("-eff", "-orig")
            cr_is = "orig"

        origValidationFolder = self.general_options.get(
            "origValidationFolder", validationFolder
        )

        orig_excl = None
        if anaDir != origDir and os.path.exists(origDir):
            orig_excl = self.getCurveFromJson(
                origDir, origValidationFolder, txname,
                typ="comb", axes=axes,
            )
            if offshell:
                orig_excl_off = self.getCurveFromJson(
                    origDir, origValidationFolder, txnameOff,
                    typ="comb", axes=axes, eval_axes=True,
                )
                orig_excl = self.addOffshell(orig_excl, orig_excl_off)
            self.pprint(f"found curve for {origDir}!")

        if offshell:
            comb_excl = self.getCurveFromJson(
                anaDir, validationFolder, txname,
                typ="comb", axes=axes_on,
            )
            comb_excl_off = self.getCurveFromJson(
                anaDir, validationFolder, txnameOff,
                typ="comb", axes=axes,
            )
            if not comb_excl_off:
                self.pprint(
                    "No comb SR SModelS excl line. "
                    "Not drawing paper plot."
                )
                return None
            comb_excl = self.addOffshell(comb_excl, comb_excl_off)
        else:
            comb_excl = self.getCurveFromJson(
                anaDir, validationFolder, txname,
                typ="comb", axes=axes,
            )
            if not comb_excl:
                self.pprint(
                    "No comb SR SModelS excl line. "
                    "Not drawing paper plot."
                )
                return None
            self.pprint(
                f"got combined curve from {anaDir}: "
                f"{len(comb_excl)} points"
            )

        return {
            "off_excl": off_excl,
            "bestSR_excl": bestSR_excl,
            "bestSR": bestSR,
            "comb_excl": comb_excl,
            "combSR": combSR,
            "orig_excl": orig_excl,
            "cr_is": cr_is,
        }

    # ------------------------------------------------------------------ #
    #  Main Entry Point
    # ------------------------------------------------------------------ #

    def draw(self, addJitter: bool = True) -> list[str]:
        """Generate paired observed and expected paper plots.

        Produces two PNG files: one for observed exclusion limits and
        one for expected exclusion limits, comparing official results
        with SModelS predictions.

        :param addJitter: add small random offset to NN lines for visibility
        :returns: list of output file paths
        """
        self.addJitter = addJitter

        info = self._extract_plot_info()
        if info is None:
            return []

        excl = self._fetch_all_exclusion_lines(info)
        if excl is None:
            return []

        lines: dict = {"official": excl["off_excl"]}
        if excl["bestSR"]:
            lines["bestSR"] = excl["bestSR_excl"]
        if excl["combSR"]:
            lines["comb"] = excl["comb_excl"]

        ranges = self.getRanges(lines)
        nums = self.countDataSets(self.validationPlot)
        ver, num_sr, num_cr = nums["ver"], nums["num_sr"], nums["num_cr"]
        x_label, y_label = self._compute_axis_labels(self.validationPlot)

        analysis = info["analysis"]
        txname = info["txname"]
        txnameOff = info["txnameOff"]
        axes = info["axes"]
        vDir = info["vDir"]

        ptxname = txname
        if txnameOff == txname + "off":
            ptxname = txname + "on+off"
        pName = self.getPrettyProcessName(ptxname)

        if getAxisType(axes) == "v2":
            axes = axisV2ToV3(axes)
        fig_axes_title = getNiceAxes(axes)
        fig_axes_title = (
            fig_axes_title.replace("(", "").replace(")", "")
            .replace(",", "")
        )
        txn = txname if txnameOff == "" else txnameOff

        outfiles: list[str] = []
        exp_name = analysis.split("-")[0]
        show_off_sigmas = self.general_options.get("errorsForR", False)
        fs = self.specific_options["title_fontsize"]
        ox, oy, osize = self._get_title_position()

        # -------------------------------------------------------------- #
        #  Observed plot
        # -------------------------------------------------------------- #
        if ranges["max_obs_x"] < -0.99:
            self.pprint("seems like exclusion lines are empty")
            return []

        fig, ax = self._setup_figure()
        self._configure_axes(
            ax, ranges, "obs", x_label, y_label,
            excl["off_excl"], excl["bestSR"], excl["bestSR_excl"],
            excl["combSR"], excl["comb_excl"],
        )

        title, right_title = self._compute_titles(
            analysis, num_sr, num_cr, pName
        )
        plt.title(title, loc="left", fontsize=fs, x=-0.12)
        plt.title(right_title, loc="right", fontsize=fs)

        self._plot_official_with_sigmas(
            ax, excl["off_excl"], "obsExclusion", exp_name,
            show_off_sigmas,
        )

        if excl["bestSR"]:
            self._plot_bestSR(
                ax, excl["bestSR_excl"], "obsExclusion",
                y_label, addJitter,
            )

        if excl["combSR"] and "obsExclusion" in excl["comb_excl"]:
            x_vals = excl["comb_excl"]["obsExclusion"]["x"]
            y_vals = excl["comb_excl"]["obsExclusion"]["y"]
            y_vals = self.add_jitter(y_vals, addJitter)
            label = self._get_stat_model_label(self.validationPlot)
            x_vals, y_vals = yvalsAreWidths(y_label, x_vals, y_vals)
            if "Gamma" in y_label:
                self._add_gamma_secondary_axis(ax)
            self.plotLines(ax, x_vals, y_vals, "red", "solid", label)

            if (self.specific_options.get("drawobspm1")
                    and "obsExclusionP1" in excl["comb_excl"]
                    and "obsExclusionM1" in excl["comb_excl"]):
                for suffix in ("P1", "M1"):
                    key = f"obsExclusion{suffix}"
                    xv = excl["comb_excl"][key]["x"]
                    yv = self.add_jitter(
                        excl["comb_excl"][key]["y"], False, 0.05
                    )
                    xv, yv = yvalsAreWidths(y_label, xv, yv)
                    if "Gamma" in y_label:
                        self._add_gamma_secondary_axis(ax)
                xp1 = excl["comb_excl"]["obsExclusionP1"]["x"]
                yp1 = self.add_jitter(
                    excl["comb_excl"]["obsExclusionP1"]["y"], False, 0.05
                )
                xm1 = excl["comb_excl"]["obsExclusionM1"]["x"]
                ym1 = self.add_jitter(
                    excl["comb_excl"]["obsExclusionM1"]["y"], False, 0.05
                )
                xp1, yp1 = yvalsAreWidths(y_label, xp1, yp1)
                xm1, ym1 = yvalsAreWidths(y_label, xm1, ym1)
                self.plotErrorBand(
                    xm1, ym1, xp1, yp1, ax, None, y_label,
                    color="tab:red",
                )

        orig = excl["orig_excl"]
        if orig not in (None, []) and "obsExclusion" in orig:
            x_vals = orig["obsExclusion"]["x"]
            y_vals = orig["obsExclusion"]["y"]
            label = "SModelS: CR comb."
            if excl["cr_is"] == "orig":
                label = "SModelS: orig pyhf"
            x_vals, y_vals = yvalsAreWidths(y_label, x_vals, y_vals)
            self.plotLines(ax, x_vals, y_vals, "blue", "solid", label)

            if "obsExclusionP1" in orig:
                x_vals = orig["obsExclusionP1"]["x"]
                y_vals = self.add_jitter(
                    orig["obsExclusionP1"]["y"], addJitter
                )
                x_vals, y_vals = yvalsAreWidths(y_label, x_vals, y_vals)
                if "Gamma" in y_label:
                    self._add_gamma_secondary_axis(ax)
                self.plotLines(ax, x_vals, y_vals, "green", "solid", "")

        if "Gamma" in y_label:
            ax.set_yscale("log")

        plt.text(
            ox, oy, r"$\bf observed~exclusion$",
            transform=fig.transFigure, fontsize=osize,
        )
        plt.legend(loc="best", frameon=True, fontsize=10)
        plt.tight_layout()

        obs_outfile = f"{vDir}/{txn}_{fig_axes_title}_obs.png"
        self._save_figure(obs_outfile)
        outfiles.append(obs_outfile)

        # -------------------------------------------------------------- #
        #  Expected plot
        # -------------------------------------------------------------- #
        fig, ax = self._setup_figure()
        self._configure_axes(
            ax, ranges, "exp", x_label, y_label,
            excl["off_excl"], excl["bestSR"], excl["bestSR_excl"],
            excl["combSR"], excl["comb_excl"],
        )

        title, right_title = self._compute_titles(
            analysis, num_sr, num_cr, pName
        )
        plt.title(title, loc="left", fontsize=12, x=-0.12)
        plt.title(right_title, loc="right", fontsize=12)

        self._plot_official_with_sigmas(
            ax, excl["off_excl"], "expExclusion", exp_name,
            show_off_sigmas,
        )

        if excl["bestSR"]:
            self._plot_bestSR(
                ax, excl["bestSR_excl"], "expExclusion",
                y_label, addJitter,
            )

        if excl["combSR"] and "expExclusion" in excl["comb_excl"]:
            x_vals = excl["comb_excl"]["expExclusion"]["x"]
            y_vals = excl["comb_excl"]["expExclusion"]["y"]
            gI = self.validationPlot.expRes.globalInfo
            label = "SModelS: orig pyhf"
            if hasattr(gI, "statModels"):
                for srSetName, model_types in gI.statModels.items():
                    mtype = model_types[0][0]
                    if mtype == "onnx":
                        label = "SModelS: NN"
                    elif mtype == "sl":
                        ver = (
                            self.validationPlot.expRes.typeOfStatsModel(
                                srSetName, specifySL=True
                            ).replace("sl", "SL")
                        )
                        label = f"SModelS: {ver}"
            self.plotGammaLines(
                x_vals, y_vals, ax, label, y_label, color="red"
            )

        orig = excl["orig_excl"]
        if orig not in (None, [], {}) and "expExclusion" in orig:
            x_vals = orig["expExclusion"]["x"]
            y_vals = orig["expExclusion"]["y"]
            label = "SModelS: CR comb."
            if excl["cr_is"] == "orig":
                label = "SModelS: orig pyhf"
            self.plotGammaLines(
                x_vals, y_vals, ax, label, y_label, color="blue"
            )
            if ("expExclusionP1" in orig
                    and "expExclusionM1" in orig):
                self.plotErrorBand(
                    orig["expExclusionP1"]["x"],
                    orig["expExclusionP1"]["y"],
                    orig["expExclusionM1"]["x"],
                    orig["expExclusionM1"]["y"],
                    ax, None, y_label, color="lightblue",
                )

        if "Gamma" in y_label:
            ax.set_yscale("log")
        if "logy" in self.specific_options:
            ax.set_yscale("log")
            ylim = ax.get_ylim()
            ymin = self.specific_options.get("logymin", 0.3)
            if ylim[0] < 1e-10:
                ax.set_ylim(ymin, ylim[1])

        plt.text(
            ox, oy, r"$\bf expected~exclusion$",
            transform=fig.transFigure, fontsize=osize,
        )
        plt.legend(loc="best", frameon=True, fontsize=10)
        plt.tight_layout()

        exp_outfile = f"{vDir}/{txn}_{fig_axes_title}_exp.png"
        self._save_figure(exp_outfile)
        outfiles.append(exp_outfile)

        return outfiles
