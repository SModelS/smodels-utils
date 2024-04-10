#!/usr/bin/env python3

__all__ = [ "drawPrettyPaperPlot" ]

import os
import matplotlib.pyplot as plt
import numpy as np
from numpy import array
import json
import matplotlib.lines as mlines
from smodels.base.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxes, prettyAxesV3
from validationHelpers import getAxisType
import matplotlib.ticker as ticker


def getCurveFromJson(anaDir, txname, type=["official", "bestSR", "combined"], axes=None):
    """
    Get Exclusion Curve from official and SModelS json files
    :param anaDir: path to dir of analysis
    :param txname: txname for which we need the exclusion curve
    :param type: type of exclusion curve - official curve, SModelS bestSR, SModelS combined SR
    :param axes: axes map of official exclusion line
    returns a dict of obs and exp exclusion lines
    """

    excl_x,excl_y,exp_excl_x,exp_excl_y = [],[],[],[]
    excl_lines = {}
    if type == "official":
        file = open(f"{anaDir}/exclusion_lines.json")
        excl_file = json.load(file)
        axes = axes.replace(" ", "")
        if txname in excl_file:
            excl_x     = excl_file[txname][f"obsExclusion_{axes}"]['x']
            excl_y     = excl_file[txname][f"obsExclusion_{axes}"]['y']
            if f"expExclusion_{axes}" in excl_file[txname].keys():
                exp_excl_x = excl_file[txname][f"expExclusion_{axes}"]['x']
                exp_excl_y = excl_file[txname][f"expExclusion_{axes}"]['y']
    
    else:
        file = open(f"{anaDir}/validation/SModelS_ExclusionLines.json","r")
        excl_file = json.load(file)
        if type == "bestSR":
            if f"{txname}_bestSR" not in excl_file: return excl_lines
            excl_x     = excl_file[f'{txname}_bestSR']['obs_excl']['x']
            excl_y     = excl_file[f'{txname}_bestSR']['obs_excl']['y']
            exp_excl_x = excl_file[f'{txname}_bestSR']['exp_excl']['x']
            exp_excl_y = excl_file[f'{txname}_bestSR']['exp_excl']['y']
        
        elif type == "combined":
            if f"{txname}_comb" not in excl_file: return excl_lines
            excl_x     = excl_file[f'{txname}_comb']['obs_excl']['x']
            excl_y     = excl_file[f'{txname}_comb']['obs_excl']['y']
            exp_excl_x = excl_file[f'{txname}_comb']['exp_excl']['x']
            exp_excl_y = excl_file[f'{txname}_comb']['exp_excl']['y']
            
    excl_lines = {"obs_excl":{"x":excl_x,"y":excl_y}, "exp_excl":{"x":exp_excl_x,"y":exp_excl_y}}
    '''
    if type != "official":
        excl_lines["obs_excl"] = smooth_excl(excl_lines["obs_excl"])
        excl_lines["exp_excl"] = smooth_excl(excl_lines["exp_excl"])
    '''
    return excl_lines


def smooth_excl(xy_dict):
    #"{x:[],y:[]}"
    
    x_vals = np.array(xy_dict['x'])
    ind_x = np.argsort(x_vals)
    x_vals = np.sort(x_vals)
    y_vals = np.array([xy_dict['y'][i] for i in ind_x ])
    '''
    from scipy.interpolate import splrep, BSpline
    tck = splrep(x_vals, y_vals)
    new_y_vals = BSpline(*tck)(x_vals)
    '''
    xy_dict['x'] = x_vals.tolist()
    xy_dict['y'] = y_vals.tolist()
    return xy_dict

def getPrettyAxisLabels(label):
    particle = label.replace('(','').replace(')','').replace('$','').split('m')[-1]
    label = '$m_{' + particle +'}$ [GeV]'
    return label

def getExtremeValue(excl_line, extreme, type):
    if type == "official":
        if extreme == "max":
            if len(excl_line)==0: return -1
            return max(excl_line)
        else:
            if len(excl_line)==0: return np.inf
            return min(excl_line)
    else:
        if extreme == "max":
            maxi = -1
            for line in excl_line:
                maxi = max(maxi, max(line))
            return maxi
        else:
            mini = np.inf
            for line in excl_line:
                mini = min(mini, min(line))
            return mini

def drawPrettyPaperPlot(validationPlot):
    """
    Function which holds the generalised plotting parameters
    :param validationPlot: validationPlot object
    """
    #get info about the analysis and txname from validationPlot
    analysis = validationPlot.expRes.globalInfo.id
    vDir = validationPlot.getValidationDir (validationDir=None)
    anaDir = os.path.dirname(vDir)
    txname = validationPlot.txName
    
    #get exclusion lines for official and SModelS
    off_excl = getCurveFromJson(anaDir, txname, type="official", axes=validationPlot.axes)
    
    bestSR, combSR = True, True
    
    bestSR_excl = getCurveFromJson(anaDir, txname, type="bestSR")
    if not bestSR_excl:
        print("[drawPrettyPaperPlot] No best SR SModelS excl line.")
        bestSR = False
    
    comb_excl = getCurveFromJson(anaDir, txname, type="combined")
    if not comb_excl:
        print("[drawPrettyPaperPlot] No comb SR SModelS excl line.")
        combSR = False

    #get the range of x values in obs and exp curves to set lim on plot ranges. low limit on y axes always 0 for plot
    max_obs_x = getExtremeValue(off_excl["obs_excl"]["x"], extreme = "max", type="official")
    if bestSR: max_obs_x = max(max_obs_x, getExtremeValue(bestSR_excl["obs_excl"]["x"], extreme = "max", type="bestSR"))
    if combSR: max_obs_x = max(max_obs_x, getExtremeValue(comb_excl["obs_excl"]["x"], extreme = "max", type="combined"))

    max_obs_y = getExtremeValue(off_excl["obs_excl"]["y"], extreme = "max", type="official")
    if bestSR: max_obs_y = max(max_obs_y, getExtremeValue(bestSR_excl["obs_excl"]["y"], extreme = "max", type="bestSR"))
    if combSR: max_obs_y = max(max_obs_y, getExtremeValue(comb_excl["obs_excl"]["y"], extreme = "max", type="combined"))
        
    max_exp_x = getExtremeValue(off_excl["exp_excl"]["x"], extreme = "max", type="official")
    if bestSR: max_exp_x = max(max_exp_x, getExtremeValue(bestSR_excl["exp_excl"]["x"], extreme = "max", type="bestSR"))
    if combSR: max_exp_x = max(max_exp_x, getExtremeValue(comb_excl["exp_excl"]["x"], extreme = "max", type="combined"))

    max_exp_y = getExtremeValue(off_excl["exp_excl"]["y"], extreme = "max", type="official")
    if bestSR: max_exp_y = max(max_exp_y, getExtremeValue(bestSR_excl["exp_excl"]["y"], extreme = "max", type="bestSR"))
    if combSR: max_exp_y = max(max_exp_y, getExtremeValue(comb_excl["exp_excl"]["y"], extreme = "max", type="combined"))

    min_obs_x = getExtremeValue(off_excl["obs_excl"]["x"], extreme = "min", type="official")
    if bestSR: min_obs_x = min(min_obs_x, getExtremeValue(bestSR_excl["obs_excl"]["x"], extreme = "min", type="bestSR"))
    if combSR: min_obs_x = min(min_obs_x, getExtremeValue(comb_excl["obs_excl"]["x"], extreme = "min", type="combined"))
    
    min_exp_x = getExtremeValue(off_excl["exp_excl"]["x"], extreme = "min", type="official")
    if bestSR: min_exp_x = min(min_exp_x, getExtremeValue(bestSR_excl["exp_excl"]["x"], extreme = "min", type="bestSR"))
    if combSR: min_exp_x = min(min_exp_x, getExtremeValue(comb_excl["exp_excl"]["x"], extreme = "min", type="combined"))
    
    num_sr = 0
    ver = ""
    
    if "obs_excl" in comb_excl.keys():
        num_sr = len(validationPlot.expRes.datasets)
        if hasattr ( validationPlot.expRes.globalInfo, "jsonFiles" ): ver = "(pyhf)"    #how to differentiate between simplified and full?
        if hasattr ( validationPlot.expRes.globalInfo, "covariance" ): ver = "(SLv1)"   #SLv1 vs SLv2
    
    #now plot figure
    
    #--------observed plot-------
    fig = plt.figure(figsize=(5,4))
    plt.rcParams['text.usetex'] = True
    plt.rcParams['font.family'] = 'Cambria Math'
    
    step_x = int(max_obs_x/100)*10
    mid_x = int((max_obs_x - min_obs_x)/2)
    step_y = int(max_obs_y/100)
    
    
    plt.xlim([int(min_obs_x/10)*10,round(max_obs_x+step_x,-1)])
    plt.ylim([0,round(max_obs_y+(step_y*100),-1)])
    axis_label = str(validationPlot.axes).replace(" ","")
    if getAxisType ( validationPlot.axes ) == "v3":
        axis_label = prettyAxesV3(validationPlot).split(',')
    x_label, y_label = "",""
    for lbl in axis_label:
        if "x=" in lbl: x_label = getPrettyAxisLabels(lbl.split("=")[-1].strip())
        else: y_label = getPrettyAxisLabels(lbl.split("=")[-1].strip())
    
    plt.xlabel(x_label,fontsize = 14)
    plt.ylabel(y_label,fontsize = 14)
    
    plt.title(analysis, loc='left', fontsize=12)                        #analysis id on left of title
    pName = prettyTxname(validationPlot.txName, outputtype="latex" )    #processName
    plt.title(pName,loc='right', fontsize=12)                           #process srring on right of title
    
    plt.tick_params(which='major', axis = 'both', direction = 'in', length = 10, top = True, right = True)
    plt.tick_params(labelbottom=True, labelleft=True, labeltop=False, labelright=False)
    plt.tight_layout()
    
    #plot excl curves
    exp_name = analysis.split('-')[0]
    plt.plot(off_excl["obs_excl"]["x"], off_excl["obs_excl"]["y"],color='black', linestyle='solid', label = f'{exp_name} official')
    if bestSR:
        for ind, x_vals in enumerate(bestSR_excl["obs_excl"]["x"]):
            y_vals = bestSR_excl["obs_excl"]["y"][ind]
            if ind==0: plt.plot(x_vals, y_vals,color='red', linestyle='dashed', label = "SModelS: best SR")
            else: plt.plot(x_vals, y_vals,color='red', linestyle='dashed')
    if combSR:
        for ind, x_vals in enumerate(comb_excl["obs_excl"]["x"]):
            y_vals = comb_excl["obs_excl"]["y"][ind]
            if ind==0: plt.plot(x_vals, y_vals,color='red', linestyle='solid', label = f"SModelS: comb. {num_sr} SRs {ver}")
            else: plt.plot(x_vals, y_vals,color='red', linestyle='solid')
    
    plt.text(mid_x + step_x*2,max_obs_y+(step_y*30),r"$\bf observed~exclusion$", fontsize = 10)
    
    plt.legend(loc='best', frameon=True, fontsize = 10)
    fig_axes_title = str ( validationPlot.axes )
    if getAxisType ( validationPlot.axes ) == "v3":
        axes = eval(validationPlot.axes).values()
        fig_axes_title = ""
        for ax in axes: fig_axes_title += str(ax) + '_'
    
    plt.savefig(f"{vDir}/{txname}_{fig_axes_title}obs.png", dpi=250)
    
    #--------expected plot-------
    plt.clf()
    fig = plt.figure(figsize=(5,4))
    
    plt.rcParams['text.usetex'] = True
    plt.rcParams['font.family'] = 'Cambria Math'
 
    step_x = int(max_exp_x/100)*10
    mid_x = int((max_exp_x - min_exp_x)/2)
    step_y = int(max_exp_y/100)
    
    plt.xlim([int(min_exp_x/10)*10,round(max_exp_x+step_x,-1)])
    plt.ylim([0,round(max_exp_y+(step_y*100),-1)])
    
    plt.xlabel(x_label,fontsize = 14)
    plt.ylabel(y_label,fontsize = 14)
    
    plt.title(analysis, loc='left', fontsize=12)
    plt.title(pName,loc='right', fontsize=12)
    
    plt.tick_params(which='major', axis = 'both', direction = 'in', length = 10, top = True, right = True)
    plt.tick_params(labelbottom=True, labelleft=True, labeltop=False, labelright=False)
    plt.tight_layout()
    
    exp_name = analysis.split('-')[0]
    plt.plot(off_excl["exp_excl"]["x"], off_excl["exp_excl"]["y"],color='black', linestyle='solid', label = f'{exp_name} official')
    
    if bestSR:
        for ind, x_vals in enumerate(bestSR_excl["exp_excl"]["x"]):
            y_vals = bestSR_excl["exp_excl"]["y"][ind]
            if ind==0: plt.plot(x_vals, y_vals,color='red', linestyle='dashed', label = "SModelS: best SR")
            else: plt.plot(x_vals, y_vals,color='red', linestyle='dashed')
    if combSR:
        for ind, x_vals in enumerate(comb_excl["exp_excl"]["x"]):
            y_vals = comb_excl["exp_excl"]["y"][ind]
            if ind==0: plt.plot(x_vals, y_vals,color='red', linestyle='solid', label = f"SModelS: comb. {num_sr} SRs {ver}")
            else: plt.plot(x_vals, y_vals,color='red', linestyle='solid')
    
    plt.text(mid_x + step_x*2,max_exp_y+(step_y*30),r"$\bf expected~exclusion$", fontsize = 10)
    
    plt.legend(loc='best', frameon=True, fontsize = 10)
    plt.savefig(f"{vDir}/{txname}_{fig_axes_title}exp.png", dpi=250)
    plt.clf()
        
