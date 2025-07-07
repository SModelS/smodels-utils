#!/usr/bin/env python3

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
from validationHelpers import getAxisType, prettyAxes, translateAxisV2
import matplotlib.ticker as ticker
from smodels_utils.helper.terminalcolors import *

def getCurveFromJson( anaDir, validationFolder, txname, type=["official", "bestSR", "combined"], 
                      axes=None, eval_axes=True ):
    """
    Get Exclusion Curve from official and SModelS json files
    :param anaDir: path to dir of analysis
    :param txname: txname for which we need the exclusion curve
    :param type: type of exclusion curve - official curve, SModelS bestSR, SModelS combined SR
    :param axes: axes map of official exclusion line
    returns a dict of obs and exp exclusion lines
    """
    saxes = str(axes).replace(" ","").replace("'","")

    excl_x,excl_y,exp_excl_x,exp_excl_y = [],[],[],[]
    excl_lines = {}
    
    if type == "official":
        fname = f"{anaDir}/exclusion_lines.json"
        file = open( fname )
        excl_file = json.load(file)
        axes = axes.replace(" ", "")
        import sympy
        x,y,z,w = sympy.var("x y z w")
        daxes = eval(axes)
        from sympy.parsing.sympy_parser import parse_expr
        if txname in excl_file:
            if f"obsExclusion_{axes}" not in excl_file[txname].keys():
                axes_keys = list(excl_file[txname].keys())
                # print ( f"[drawPaperPlot] draw for {axes}" )
                # print ( "[drawPaperPlot] candidates", axes_keys )
                foundNewAxis = False
                for axis_candidate in axes_keys:
                    maxes = axis_candidate.split('_')[-1]
                    tmp = maxes.replace("[","").replace("]","")
                    tokens = tmp.split ( "," )
                    misses = False
                    for k,v in daxes.items():
                        sv = parse_expr ( v )
                        isInTokens = False
                        for t in tokens:
                            try:
                                st = parse_expr ( t )
                            except tokenize.TokenError as e:
                                print ( f"[drawPaperPlot] token error '{e}': '{t}' in {fname}" )
                                sys.exit(-1)
                            if st == sv:
                                isInTokens = True
                                break
                        if not isInTokens:
                            misses=True
                            break
                    if not misses:
                        axes = maxes
                        foundNewAxis = True
                if foundNewAxis:
                    print( f"[drawPaperPlot] {GREEN}converted axis: {axes}{RESET}" )
                else:
                    print( f"[drawPaperPlot] {RED}ERROR could not find new axis. implement! {axes} {RESET}" )
                    sys.exit(-1)
   
            excl_x = excl_file[txname][f"obsExclusion_{axes}"]['x']
            excl_y = excl_file[txname][f"obsExclusion_{axes}"]['y']
            if f"expExclusion_{axes}" in excl_file[txname].keys():
                exp_excl_x = excl_file[txname][f"expExclusion_{axes}"]['x']
                exp_excl_y = excl_file[txname][f"expExclusion_{axes}"]['y']

    else:
        fname = f"{anaDir}/{validationFolder}/SModelS_ExclusionLines.json"
        if not os.path.exists ( fname ):
            print ( f"[drawPaperPlot] error: {fname} does not exist!" )
            return []
        print ( f"[drawPaperPlot] we have an exclusion curve file: {fname}" )

        file = open(fname,"r")
        excl_file = json.load(file)
        if f"{txname}_comb_{axes}" not in excl_file:
            print(f"[drawPaperPlot] {txname}_comb_{saxes[:20]} not found in {fname}")
        if f"{txname}_bestSR_{axes}" not in excl_file:
            print(f"[drawPaperPlot] {txname}_bestSR_{saxes[:20]} not found in {fname}")
            # return excl_lines
        if type == "bestSR" and f'{txname}_bestSR_{axes}' in excl_file:
            print (f"[drawPaperPlot] we have {txname}_bestSR_{axes} as an exclusion line" )
            excl_x     = sum(excl_file[f'{txname}_bestSR_{axes}']['obs_excl']['x'], [])
            excl_y     = sum(excl_file[f'{txname}_bestSR_{axes}']['obs_excl']['y'], [])
            exp_excl_x = sum(excl_file[f'{txname}_bestSR_{axes}']['exp_excl']['x'], [])
            exp_excl_y = sum(excl_file[f'{txname}_bestSR_{axes}']['exp_excl']['y'], [])
        
        elif type == "combined" and f'{txname}_comb_{axes}' in excl_file:
            curve = f'{txname}_comb_{axes}'
            excl_x     = sum(excl_file[curve]['obs_excl']['x'], [])
            excl_y     = sum(excl_file[curve]['obs_excl']['y'], [])
            exp_excl_x = sum(excl_file[curve]['exp_excl']['x'], [])
            exp_excl_y = sum(excl_file[curve]['exp_excl']['y'], [])
            col = CYAN
            if len(excl_x)==0:
                col = RED
            print (f"[drawPaperPlot] {col}we have {curve} as exclusion lines from {fname} with: {len(excl_x)} (observed) and {len(exp_excl_x)} (expected) points{RESET}" )
            
    excl_lines = {"obs_excl":{"x":excl_x,"y":excl_y}, "exp_excl":{"x":exp_excl_x,"y":exp_excl_y}}

    if ('x - y' in axes or 'x-y' in axes) and eval_axes:
        print(f"[drawPaperPlot] {type} {txname} {axes} yes")
        for type, excl in excl_lines.items():
            excl_y = (np.array(excl["x"]) - np.array(excl["y"])).tolist()
            excl_lines[type] = {"x":excl["x"],"y":excl_y}
    
    return excl_lines

def getOnshellAxesForOffshell(anaDir, tx_onshell):
    sm_file = open(f"{anaDir}/{validationFolder}/SModelS_ExclusionLines.json","r")
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
        print("[drawPaperPlot]", axes)
        return axes
        
    
def drawOffshell(excl_lines, excl_off, min_off_y = 0.0, official=False):
    
    print("[drawPaperPlot] min_off_y ", min_off_y )
    for type,excl in excl_lines.items():
        if excl_off[type]["x"] == []:
            continue
        
        if excl_off[type]["x"][0] > excl_off[type]["x"][-1] or excl_off[type]["x"][1] > excl_off[type]["x"][-2]:
            print("[drawPaperPlot] off reverse")
            excl_off[type]["x"].reverse()
            excl_off[type]["y"].reverse()
        if official: min_off_y = excl_off[type]["y"][0]
        
        if excl_off[type]["y"][-1] < excl_off[type]["y"][0]:# and official:
            print("[drawPaperPlot] yes ")
            index = [i for i,y  in enumerate(excl_off[type]["y"]) if y>excl_off[type]["y"][0]+50]
            if len(index)>0:
                excl_off[type]["x"] = excl_off[type]["x"][:index[-1]]
                excl_off[type]["y"] = excl_off[type]["y"][:index[-1]]
        
        if len(excl["x"])>0 and excl["x"][0] > excl["x"][-1]:
            print("[drawPaperPlot] on reverse")
            excl["x"].reverse()
            excl["y"].reverse()
        
        if len(excl_off[type]["x"])>0 and len(excl["x"])>0 and excl_off[type]["x"][-1] > excl["x"][0]:
            index = [i for i,x  in enumerate(excl["x"]) if x>excl_off[type]["x"][-1]+20]
            print("[drawPaperPlot] cut off ", excl["x"][index[0]])
            if len(index)>0:
                excl["x"] = excl["x"][index[0]:]
                excl["y"] = excl["y"][index[0]:]
        
        
        excl["x"] = excl_off[type]["x"] + excl["x"]
        excl["y"] = excl_off[type]["y"] + excl["y"]
    
    
    return excl_lines

def getPrettyProcessName(txname):
    pName = prettyTxname(txname, outputtype="latex" ).split(',')         #remove pp->intermediate state
    #print("pnamr ", pName)
    if len(pName)>2:
        pName = ','.join(pName[1:])
    else:
        pName = pName[1]
    
    return pName

def getPrettyAxisLabels(label):
    #print("label = ", label)
    particle = label.split('m(')[-1]
    particle = label.replace('(','').replace(')','').replace('$','').split('m_')[-1]
    #print("particle = ", particle)
    if 'm' in particle[0]: label = '$m_{' + particle[1:] +'}$ [GeV]'
    elif 'Gamma' in particle:
        if 'Gamma_' not in particle: label = '$\\Gamma_{' + particle.split('Gamma')[-1] + '}$ [GeV]'
        else: label = '$' + particle + '$ [GeV]'
    else : label = '$m_{' + particle +'}$ [GeV]'
    return label

def widthToLifetime(y):
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
    
def lifetimeToWidth(time):
    hbar = 6.58*10**(-16)
    time *= 10**9
    return hbar/time


def getExtremeValue(excl_line, extreme, type, width=False):
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
            else:
                mini = 0.
            return mini

def drawPrettyPaperPlot(validationPlot, addJitter : bool = True ) -> list:
    """
    Function which holds the generalised plotting parameters
    :param validationPlot: validationPlot object
    :param addJitter: if true, then add jitter to the NN line.
    so we can see it in case its perfectly aligned with the orig line

    :returns: filenames of plots
    """
    if validationPlot.isOneDimensional():
        print(f"[drawPaperPlot] currently we don't have 1d versions of the pretty plots. exiting." )
        return []
    #get info about the analysis and txname from validationPlot
    analysis = validationPlot.expRes.globalInfo.id
    vDir = validationPlot.getValidationDir (validationDir=None)
    validationFolder = os.path.basename ( vDir )
    anaDir = os.path.dirname(vDir)
    txname = validationPlot.txName
    axes = validationPlot.axes
    eval_axes = True
    saxes = str(axes).replace(" ","").replace("'","")
    print(f"[drawPaperPlot] Drawing pretty paper plot for {txname}:{saxes} ")
    
    offshell = False
    txnameOff = ''
    axes_on = None
    if 'off' in txname:
        axes_on = getOnshellAxesForOffshell(anaDir, txname.split('off')[0])
        if axes_on:
            print("[drawPaperPlot] yes offshell")
            offshell=True
            txnameOff = txname
            txname = txname.split('off')[0]

    #get exclusion lines for official and SModelS
    off_excl, comb_excl, bestSR_excl = [],[],[]
    
    if 'ATLAS-SUSY-2018-16' in analysis: eval_axes = False
    if 'CMS-PAS-SUS-16-052' in analysis: eval_axes = False
    if offshell:
        off_excl = getCurveFromJson(anaDir, validationFolder, txname, type="official", axes = axes_on)
        off_excl_offshell = getCurveFromJson(anaDir, validationFolder, txnameOff, type="official", axes = axes)
        off_excl = drawOffshell(off_excl, off_excl_offshell, official=True)
    else: off_excl = getCurveFromJson(anaDir, validationFolder, txname, type="official", axes = axes, eval_axes=eval_axes)
    
    bestSR, combSR = True, True
    if offshell:
        bestSR_excl = getCurveFromJson(anaDir, validationFolder, txname, type="bestSR", axes=axes_on)
        bestSR_excl_off = getCurveFromJson(anaDir, validationFolder, txnameOff, type="bestSR", axes=axes)
        if not bestSR_excl_off:
            print( f"[drawPaperPlot] No best SR SModelS excl line for {anaDir}:{txnameOff}. Not drawing paper plot.")
            return
        bestSR_excl = drawOffshell(bestSR_excl, bestSR_excl_off)
    else:
        bestSR_excl = getCurveFromJson(anaDir, validationFolder, txname, type="bestSR", axes=axes, eval_axes=eval_axes)
        if not bestSR_excl:
            print(f"[drawPaperPlot] No best SR SModelS excl line for {anaDir}:{txname}:{axes}.")
            bestSR = False
            return
    crDir = anaDir.replace("-eff","-CR")
    cr_is = "CR"
    if not os.path.exists ( crDir ):
        crDir = anaDir.replace("-eff","-orig")
        cr_is = "orig"

    cr_excl = None
    if os.path.exists ( crDir ):
        cr_excl = getCurveFromJson (crDir, validationFolder, txname, type="combined", axes=axes, eval_axes=eval_axes)
        print ( f"[drawPaperPlot] found curve for {crDir}!" )


    if offshell:
        comb_excl = getCurveFromJson(anaDir, validationFolder, txname, type="combined", axes=axes_on)
        comb_excl_off = getCurveFromJson(anaDir, validationFolder, txnameOff, type="combined", axes=axes)
        if not comb_excl_off:
            print("[drawPaperPlot] No comb SR SModelS excl line. Not drawing paper plot.")
            return
        comb_excl = drawOffshell(comb_excl, comb_excl_off)
    else:
        comb_excl = getCurveFromJson(anaDir, validationFolder, txname, type="combined", axes=axes, eval_axes=eval_axes)
        if not comb_excl:
            print("[drawPaperPlot] No comb SR SModelS excl line. Not drawing paper plot.")
            combSR = False
            return
        print( f"[drawPaperPlot] got combined curve from {anaDir}" )

 
    #get the range of x values in obs and exp curves to set lim on plot ranges. low limit on y axes usually 0 for plot (except for width plots)
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
    
    num_sr, num_cr = 0, 0
    ver = ""
    
    if "obs_excl" in comb_excl.keys():
        num_sr = len(validationPlot.expRes.datasets)
        if hasattr ( validationPlot.expRes.globalInfo, "jsonFiles" ): 
            ver = "(pyhf)"    #how to differentiate between simplified and full?
            for js,files in validationPlot.expRes.globalInfo.jsonFiles.items():
                num_cr += len(files)
        elif hasattr ( validationPlot.expRes.globalInfo, "mlModels" ): 
            ver = "ONNX"    #how to differentiate between simplified and full?
            for js,files in validationPlot.expRes.globalInfo.mlModels.items():
                num_cr += len(files)

        if hasattr ( validationPlot.expRes.globalInfo, "covariance" ): ver = "(SLv1)"   #SLv1 vs SLv2
    
    if hasattr ( validationPlot.expRes.datasets[0].dataInfo, "thirdMoment" ):
        ver = "(SLv2)"
    
    #now plot figure
    # print("[drawPaperPlot] Drawing pretty obs and exp plots")
    
    #--------observed plot-------
    plt.rcParams['text.usetex'] = True
    plt.rcParams['font.family'] = 'Cambria Math'
    
    fig,ax = plt.subplots(figsize=(5,4))
 
    step_x = int(max_obs_x/100)*10
    mid_x = int((max_obs_x - min_obs_x)/2)
    step_y = int(max_obs_y)

    #print("[drawPaperPlot] max obs y ", max_obs_y)
    #print("[drawPaperPlot] step y", step_y)
    #print("[drawPaperPlot] max exp y ", max_exp_y)
    
    axis_label = prettyAxes(validationPlot).split(',')
    # print("[drawPaperPlot] Axis label ", axis_label)
    x_label, y_label = "",""
    massg = ""
    for lbl in axis_label:
        if "=x" in lbl and "=x -" not in lbl: x_label = getPrettyAxisLabels(lbl.split("=")[0].strip())
        elif "x=" in lbl: x_label = getPrettyAxisLabels(lbl.split("=")[-1].strip())
        elif ("=y" in lbl or "- y" in lbl) and "=y -" not in lbl: y_label = getPrettyAxisLabels(lbl.split("=")[0].strip())
        elif "y=" in lbl: y_label = getPrettyAxisLabels(lbl.split("=")[-1].strip())
        else: continue
    
    if '2018-14' in analysis:
        if 'Sel' in txname: particle = '{\\tilde{e}}'
        elif 'Smu' in txname: particle = '{\\tilde{\\mu}}'
        elif 'Stau' in txname: particle = '{\\tilde{\\tau}}'
        x_label = f'$m_{particle} [GeV]$'
        y_label = f'$\\Gamma_{particle} [GeV]$'
        massg = '$ m_{\\tilde{\\chi}_1^0} = 0.0 $'
    
    if '2018-31' in analysis:
        if '130' in axis_label[2]: massg = '$m_{\\tilde{\\chi}_1^0} = m_{\\tilde{\\chi}_2^0}$ - ' + axis_label[2].split('-')[1]
        elif '60' in axis_label[2]: massg = '$m_{\\tilde{\\chi}_1^0}$ = 60'
        else: massg = '$m_{\\tilde{\\chi}_1^0}$ = ' + axis_label[2].split('=')[1]
    if massg.count("$") % 2 == 1:
        print ( f"[drawPaperPlot] something is wrong with the math modes in {massg}" )
        import sys; sys.exit(-1)

    if '2018-13' in analysis:
        if 'TRPV1' in txname:
            if 'm($\\tilde{g}$)' in axis_label[0] and 'x' not in axis_label[0]: massg = '$ m_{\\tilde{g}} = ' + axis_label[0].split('=')[0] + '$'
            elif 'm($\\tilde{\\chi}_1^0$)' in axis_label[1] and 'x' not in axis_label[1] and 'y' not in axis_label[1] : massg = '$ m_{\\tilde{\\chi}_1^0} = ' + axis_label[1].split('=')[0] + '$'
            else:
                massg = '$ \\Gamma_{\\tilde{\\chi}_1^0} = ' + axis_label[2].split('=')[0] + '$'
                # print("massg ", massg)
                expo = massg.index('-')
                massg = massg[:expo-1] + " \\times 10^{" + massg[expo:-1] + "}$"
        else:       #TRPVChijjj
            x_label = '$m_{\\tilde{\\chi}_2^0}$ [GeV]'
            y_label = '$\\Gamma_{\\tilde{\\chi}_2^0}$ [GeV]'
    
    if '2018-16' in analysis:
        if 'TSlep' in txname: y_label = '$  m_{\\tilde{l}} - m_{\\tilde{\\chi}_1^0} $ [GeV]'
        else: y_label = '$  m_{\\tilde{\\chi}_1^{\\pm}} - m_{\\tilde{\\chi}_1^0} $ [GeV]'
    
    if 'CMS-PAS-SUS-16-052' in analysis:
        if 'T2b' in txname: y_label = '$  m_{\\tilde{\\tau}} - m_{\\tilde{\\chi}_1^0} $ [GeV]'
        else:
            y_label = '$  m_{\\tilde{\\tau}} - m_{\\tilde{\\chi}_1^0} $ [GeV]'
            massg = '$  m_{\\tilde{\\chi}_1^{\\pm}} = m_{\\tilde{\\tau}} - 0.5 m_{\\tilde{\\chi}_1^0} $'
    # print("[drawPaperPlot] massg ", massg)
    if 'CMS-SUS-16-050-agg' in analysis:
        if 'T5t' in txname:massg = '$ m_{\\tilde{\\tau}} =  m_{\\tilde{\\chi}_1^0} + 20 $ '
    
    if 'ATLAS-SUSY-2018-33' in analysis:
        x_label = '$m(\\tilde{t}$)'
        y_label = '$\\Gamma(\\tilde{t})$'
    
    
    ax.set_xlabel(x_label,fontsize = 14)
    ax.set_ylabel(y_label,fontsize = 14)
    ax.set_xlim([int(min_obs_x/10)*10,round(max_obs_x+step_x,-1)])
    if 'Gamma' in y_label:
        max_obs_y = getExtremeValue(off_excl["obs_excl"]["y"], extreme = "max", type="official")
        if bestSR: max_obs_y = max(max_obs_y, getExtremeValue(bestSR_excl["obs_excl"]["y"], extreme = "max", type="bestSR", width=True))
        if combSR: max_obs_y = max(max_obs_y, getExtremeValue(comb_excl["obs_excl"]["y"], extreme = "max", type="combined", width=True))
        
        min_obs_y = getExtremeValue(off_excl["obs_excl"]["y"], extreme = "min", type="official")
        if bestSR: min_obs_y = min(min_obs_y, getExtremeValue(bestSR_excl["obs_excl"]["y"], extreme = "min", type="bestSR", width=True))
        if combSR: min_obs_y = min(min_obs_y, getExtremeValue(comb_excl["obs_excl"]["y"], extreme = "min", type="combined", width=True))
        step_y = max_obs_y*1000
        #print("min_obs_y ", min_obs_y)
        #print("step ", step_y)
        ax.set_ylim([min_obs_y, max_obs_y+step_y])
    
    
    else:
        #print("max_obs_y + step ", max_obs_y+step_y )
        ax.set_ylim([0,round(max_obs_y+step_y,-1)])
    
    plt.title(analysis, loc='left', fontsize=12)                        #analysis id on left of title
    #pName = prettyTxname(validationPlot.txName, outputtype="latex" )   #processName
    pName = getPrettyProcessName(validationPlot.txName)
    #print(pName)
    plt.title(pName,loc='right', fontsize=12)                           #process srring on right of title
    
    #plt.tick_params(which='major', axis = 'both', direction = 'in', length = 10, top = True, right = True)
    #plt.tick_params(labelbottom=True, labelleft=True, labeltop=False, labelright=False)
    #plt.tight_layout()
    
    #plot excl curves
    exp_name = analysis.split('-')[0]
    ax.plot(off_excl["obs_excl"]["x"], off_excl["obs_excl"]["y"],color='black', linestyle='solid', label = f'{exp_name} official')
    #print("official : ", off_excl["obs_excl"]["y"] )
    if bestSR:
        x_vals = bestSR_excl["obs_excl"]["x"]
        y_vals = bestSR_excl["obs_excl"]["y"]
        if 'Gamma' in y_label:
            print("yes gamma")
            y_vals = [10**y for y in y_vals]
            y_diff = [y_vals[i+1]/y_vals[i] for i in range(len(y_vals)-1)]
            index_max_diff = -1
            if max(y_diff)>100: index_max_diff = y_diff.index(max(y_diff))+1
            if len(x_vals)>0:
                ax.plot(x_vals[:index_max_diff], y_vals[:index_max_diff],color='red', linestyle='dashed', label = "SModelS: best SR")
                ax.plot(x_vals[index_max_diff:], y_vals[index_max_diff:],color='red', linestyle='dashed')
            #sec_ax = ax.secondary_yaxis('right', functions=(widthToLifetime, widthToLifetime))
            #sec_ax.set_ylabel(r"$\tau$ (s)", fontsize=12)
            #sec_ax.set_yscale('log')
            plt.tick_params(which='major', axis = 'both', direction = 'in', length = 10, top = True, right = False)
            plt.tick_params(labelbottom=True, labelleft=True, labeltop=False, labelright=False)
        else:
            if len(x_vals)>0:
                ax.plot(x_vals, y_vals,color='red', linestyle='dashed', label = "SModelS: best SR")
            plt.tick_params(which='major', axis = 'both', direction = 'in', length = 10, top = True, right = True)
            plt.tick_params(labelbottom=True, labelleft=True, labeltop=False, labelright=False)
            

    if combSR:
        x_vals = comb_excl["obs_excl"]["x"]
        y_vals = comb_excl["obs_excl"]["y"]
        if addJitter:
            for i, y in enumerate(y_vals):
                y_vals[i]= y * random.uniform(.98,1.02)
        label = f"SModelS: comb. {num_sr} SRs {ver}"
        if hasattr ( validationPlot.expRes.globalInfo, "mlModels" ):
            label = f"SModelS: NN {num_sr} SRs + {num_cr-num_sr} CRs"
        if 'Gamma' in y_label:
            y_vals = [10**y for y in y_vals]
            y_diff = [y_vals[i+1]/y_vals[i] for i in range(len(y_vals)-1)]
            index_max_diff = -1
            if max(y_diff)>100: index_max_diff = y_diff.index(max(y_diff))+1
            ax.plot(x_vals[:index_max_diff], y_vals[:index_max_diff],color='red', linestyle='solid', label = label )
            ax.plot(x_vals[index_max_diff:], y_vals[index_max_diff:],color='red', linestyle='solid' )
            sec_ax = ax.secondary_yaxis('right', functions=(widthToLifetime, widthToLifetime))
            # print("yes gamma 3")
            sec_ax.set_ylabel(r"$\tau$ [s]", fontsize=14)
            sec_ax.set_yscale('log')
        else:
            ax.plot(x_vals, y_vals,color='red', linestyle='solid', label = label )

    if cr_excl not in [ None, [] ]:
        x_vals = cr_excl["obs_excl"]["x"]
        y_vals = cr_excl["obs_excl"]["y"]
        label = f"SModelS: CR comb. {num_cr} SRs+CRs {ver}"
        if cr_is == "orig":
            label = f"SModelS: orig pyhf {num_sr} SRs + {num_cr-num_sr} CRs"
        if 'Gamma' in y_label:
            y_vals = [10**y for y in y_vals]
            y_diff = [y_vals[i+1]/y_vals[i] for i in range(len(y_vals)-1)]
            index_max_diff = -1
            if max(y_diff)>100: index_max_diff = y_diff.index(max(y_diff))+1
            ax.plot(x_vals[:index_max_diff], y_vals[:index_max_diff],color='blue', linestyle='solid', label = label )
            ax.plot(x_vals[index_max_diff:], y_vals[index_max_diff:],color='blue', linestyle='solid')
        else:
            ax.plot(x_vals, y_vals,color='blue', linestyle='solid', label = label)

    if 'Gamma' in y_label: ax.set_yscale('log')
    if massg != "":plt.text(0.6,0.6, r"%s GeV"%(massg), transform=fig.transFigure, fontsize = 8)
    #if '2018-14' in analysis and 'TStau' in txname:plt.text(0.6,0.6, r"%s GeV"%(massg), transform=fig.transFigure, fontsize = 8)
    
    plt.text(0.55,0.65, r"$\bf observed~exclusion$", transform=fig.transFigure, fontsize = 10)
    plt.legend(loc='best', frameon=True, fontsize = 10)
    plt.tight_layout()
    
    #get_name_of_plot
    if getAxisType(axes) == "v2":
        axes = translateAxisV2(axes)
    axes = eval(axes).values()
    # print("[drawPaperPlot] fig ", axes)
    fig_axes_title = ""
    for a in axes: fig_axes_title += str(a) + '_'
    fig_axes_title = fig_axes_title.replace('x-y', 'y')
    fig_axes_title = fig_axes_title.replace('00', '0')
    fig_axes_title = fig_axes_title.replace('.0', '')
    outfiles = []

    outfile = f"{vDir}/{txname}_{fig_axes_title}obs.png"
    print ( f"[drawPaperPlot] saving to {YELLOW}{outfile}{RESET}" )
    plt.savefig(outfile, dpi=250)
    plt.clf()
    plt.rcdefaults()
    plt.close()
    outfiles.append ( outfile ) 
    
    #--------expected plot-------
    plt.rcParams['text.usetex'] = True
    plt.rcParams['font.family'] = 'Cambria Math'
    
    fig,ax = plt.subplots(figsize=(5,4))
 
    step_x = int(max_exp_x/100)*10
    mid_x = int((max_exp_x - min_exp_x)/2)
    step_y = int(max_exp_y)
    
    #print("max exp y ", max_exp_y)
    #print("exp step y ", step_y)
    #plt.ylim([5*10**(-16),5*10**(-13)])
    
    ax.set_xlabel(x_label,fontsize = 14)
    ax.set_ylabel(y_label,fontsize = 14)
    ax.set_xlim([int(min_exp_x/10)*10,round(max_exp_x+step_x,-1)])
    if 'Gamma' in y_label:
        max_exp_y = getExtremeValue(off_excl["exp_excl"]["y"], extreme = "max", type="official")
        if bestSR: max_exp_y = max(max_exp_y, getExtremeValue(bestSR_excl["exp_excl"]["y"], extreme = "max", type="bestSR", width=True))
        if combSR: max_exp_y = max(max_exp_y, getExtremeValue(comb_excl["exp_excl"]["y"], extreme = "max", type="combined", width=True))
        
        min_exp_y = getExtremeValue(off_excl["exp_excl"]["y"], extreme = "min", type="official")
        if bestSR: min_exp_y = min(min_exp_y, getExtremeValue(bestSR_excl["exp_excl"]["y"], extreme = "min", type="bestSR", width=True))
        if combSR: min_exp_y = min(min_exp_y, getExtremeValue(comb_excl["exp_excl"]["y"], extreme = "min", type="combined", width=True))
        print("min exp y ", min_exp_y)
        step_y = max_exp_y*1000
        print("step exp y ", step_y)
        ax.set_ylim([min_exp_y,max_exp_y+step_y])
    else: ax.set_ylim([0,round(max_exp_y+step_y,-1)])

    plt.title(analysis, loc='left', fontsize=12)
    plt.title(pName,loc='right', fontsize=12)
    
    exp_name = analysis.split('-')[0]
    ax.plot(off_excl["exp_excl"]["x"], off_excl["exp_excl"]["y"],color='black', linestyle='solid', label = f'{exp_name} official')
    
    if bestSR:
        x_vals = bestSR_excl["exp_excl"]["x"]
        y_vals = bestSR_excl["exp_excl"]["y"]
        if 'Gamma' in y_label:
            y_vals = [10**y for y in y_vals]
            y_diff = [y_vals[i+1]/y_vals[i] for i in range(len(y_vals)-1)]
            index_max_diff = -1
            if max(y_diff)>100: index_max_diff = y_diff.index(max(y_diff))+1
            if len(x_vals)>0:
                ax.plot(x_vals[:index_max_diff], y_vals[:index_max_diff],color='red', linestyle='dashed', label = "SModelS: best SR")
                ax.plot(x_vals[index_max_diff:], y_vals[index_max_diff:],color='red', linestyle='dashed')
            sec_ax = ax.secondary_yaxis('right', functions=(widthToLifetime, widthToLifetime))
            sec_ax.set_ylabel(r"$\tau$ [s]", fontsize=14)
            sec_ax.set_yscale('log')
            plt.tick_params(which='major', axis = 'both', direction = 'in', length = 10, top = True, right = False)
            plt.tick_params(labelbottom=True, labelleft=True, labeltop=False, labelright=False)
        else:
            if len(x_vals)>0:
                ax.plot(x_vals, y_vals,color='red', linestyle='dashed', label = "SModelS: best SR")
            plt.tick_params(which='major', axis = 'both', direction = 'in', length = 10, top = True, right = True)
            plt.tick_params(labelbottom=True, labelleft=True, labeltop=False, labelright=False)

    if combSR:
        x_vals = comb_excl["exp_excl"]["x"]
        y_vals = comb_excl["exp_excl"]["y"]
        if addJitter:
            for i, y in enumerate(y_vals):
                y_vals[i]= y * random.uniform(.98,1.02)
        label = f"SModelS: comb. {num_sr} SRs {ver}"
        if hasattr ( validationPlot.expRes.globalInfo, "mlModels" ):
            label = f"SModelS: NN {num_sr} SRs + {num_cr-num_sr} CRs"
        if 'Gamma' in y_label:
            y_vals = [10**y for y in y_vals]
            y_diff = [y_vals[i+1]/y_vals[i] for i in range(len(y_vals)-1)]
            index_max_diff = -1
            if max(y_diff)>100: index_max_diff = y_diff.index(max(y_diff))+1
            ax.plot(x_vals[:index_max_diff], y_vals[:index_max_diff],color='red', linestyle='solid', label = label )
            ax.plot(x_vals[index_max_diff:], y_vals[index_max_diff:],color='red', linestyle='solid')
        else:
            ax.plot(x_vals, y_vals,color='red', linestyle='solid', label = label )
    if cr_excl not in [ None, [] ]:
        x_vals = cr_excl["exp_excl"]["x"]
        y_vals = cr_excl["exp_excl"]["y"]
        label = f"SModelS: CR comb. {num_sr} SRs+CRs {ver}"
        if cr_is == "orig":
            label = f"SModelS: orig pyhf {num_sr} SRs + {num_cr-num_sr} CRs"
        if 'Gamma' in y_label:
            y_vals = [10**y for y in y_vals]
            y_diff = [y_vals[i+1]/y_vals[i] for i in range(len(y_vals)-1)]
            index_max_diff = -1
            if max(y_diff)>100: index_max_diff = y_diff.index(max(y_diff))+1
            ax.plot(x_vals[:index_max_diff], y_vals[:index_max_diff],color='blue', linestyle='solid', label = label )
            ax.plot(x_vals[index_max_diff:], y_vals[index_max_diff:],color='blue', linestyle='solid')
        else:ax.plot(x_vals, y_vals,color='blue', linestyle='solid', label = label )
    
    if 'Gamma' in y_label: ax.set_yscale('log')
    
    if massg != "":plt.text(0.6,0.6, r"%s GeV"%(massg), transform=fig.transFigure, fontsize = 8)
    #if '2018-14' in analysis and 'TStau' in txname:plt.text(0.6,0.6, r"%s GeV"%(massg), transform=fig.transFigure, fontsize = 8)
    plt.text(0.55,0.65, r"$\bf expected~exclusion$", transform=fig.transFigure, fontsize = 10)
    plt.legend(loc='best', frameon=True, fontsize = 10)
    plt.tight_layout()
    outfile = f"{vDir}/{txname}_{fig_axes_title}exp.png"
    print ( f"[drawPaperPlot] saving to {YELLOW}{outfile}{RESET}" )
    plt.savefig( outfile, dpi=250)
    plt.clf()
    plt.rcdefaults()
    plt.close()
    outfiles.append ( outfile )
    return outfiles
        
