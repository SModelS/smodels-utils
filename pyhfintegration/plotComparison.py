#!/usr/bin/env python3
# coding: utf-8

import matplotlib.pyplot as plt
import os,glob,copy,subprocess
import numpy as np
import seaborn as sns
import pyslha, copy, pickle
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
from smodels_utils.helper.various import getValidationModule, getPathName
sns.set() #Set style
sns.set_style('ticks',{'font.family':'serif', 'font.serif':'Times New Roman'})
sns.set_context('paper', font_scale=1.8)
sns.set_palette(sns.color_palette("Paired"))
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["mathtext.rm"] = 'serif'
# plt.rcParams["mathtext.it"] = 'serif:italic'
# plt.rcParams["mathtext.bf"] = 'serif:bold'
# plt.rcParams["mathtext.fontset"] = 'custom'
# plt.rcParams['text.usetex'] = True
from smodels_utils.helper import uprootTools

def getContour(xpts,ypts,zpts,levels,ylog=False,xlog=False):
    """
    Uses pyplot tricontour method to obtain contour
    curves in a 2D plane.

    :return: A dictionary with a list of contours for each level
    """
    
    fig = plt.figure()
    x = copy.deepcopy(xpts)
    y = copy.deepcopy(ypts)
    z = copy.deepcopy(zpts)
    
    #Use log scale:
    if ylog:
        y = np.log10(y)
    if xlog:
        x = np.log10(x)
    
    CS = plt.tricontour(x,y,z,levels=levels)    
    levelPts = {}
    for il,level in enumerate(CS.levels):
        levelPts[level] = []
        c = CS.collections[il]        
        paths = c.get_paths()
        for path in paths:
            levelPts[level].append(path.vertices)
    plt.close(fig)
    
    #scale back:
    if ylog or xlog:
        for key,ptsList in levelPts.items():
            newList = []
            for pts in ptsList:
                xpts = pts[:,0]
                ypts = pts[:,1]
                if xlog:
                    xpts = 10**xpts
                if ylog:
                    ypts = 10**ypts
                newList.append(np.column_stack((xpts,ypts)))
            levelPts[key] = newList
        
    
    return levelPts

def plot( dbpath, anaid, txname, axes, xaxis, yaxis ):
    """ plot comparison exclusion lines
    :param dbpath: path to database, e.g. ~/git/smodels-database/
    :param anaid: e.g. ATLAS-SUSY-2018-04
    :param txname: e.g. TStauStau
    :param axes: e.g. 2EqMassAx_EqMassBy
    """
    data  = getValidationModule ( dbpath, anaid+"-eff", f"{txname}_{axes}.py" ).validationData
    dataComb = getValidationModule ( dbpath, anaid+"-eff", f"{txname}_{axes}_combined.py" ).validationData
    dataSL = getValidationModule ( dbpath, anaid+"-SL", f"{txname}_{axes}_combined.py" ).validationData
    Dir = getPathName ( dbpath, anaid, None )

    #Get points to compute exclusion curves:
    xpts = []
    ypts = []
    rpts = []
    for pt in data:
        if 'error' in pt: continue
        xpts.append(pt['axes']['x'])
        ypts.append(pt['axes']['y'])
        rpts.append(pt['signal']/pt['UL'])
    excCurve = getContour(xpts,ypts,rpts,levels=[1.0],ylog=False)

    xpts = []
    ypts = []
    rpts = []
    for pt in dataComb:
        if 'error' in pt: continue
        xpts.append(pt['axes']['x'])
        ypts.append(pt['axes']['y'])
        rpts.append(pt['signal']/pt['UL'])
    excCurveComb = getContour(xpts,ypts,rpts,levels=[1.0],ylog=False)

    xpts = []
    ypts = []
    rpts = []
    for pt in dataSL:
        if 'error' in pt: continue
        xpts.append(pt['axes']['x'])
        ypts.append(pt['axes']['y'])
        rpts.append(pt['signal']/pt['UL'])
    excCurveSL = getContour(xpts,ypts,rpts,levels=[1.0],ylog=False)

    #Official curve
    #excATLAS = np.genfromtxt(Dir+'ATLAS-SUSY-2018-04-SL/orig/HEPData-ins1765529-v1-Exclusion_contour_1_(Obs.).csv',delimiter=',',skip_header=9,
    #                       names=True)
    #smsfile = f'{Dir}{anaid}-eff/'
    smsfile = f'{Dir}-eff/'
    print ( "smsfile", smsfile )
    offCurve = uprootTools.getExclusionLine ( smsfile, txname )
    # print ( "offCurve", offCurve )

    # print(excATLAS.dtype)

    fig = plt.figure(figsize=(9,6))
    plt.plot( offCurve["x"], offCurve["y"],label='ATLAS',
             linewidth=3,linestyle='-',color='black')

    plt.plot(excCurveComb[1.0][0][:,0],excCurveComb[1.0][0][:,1],
             label='SModelS (pyhf)',
             linewidth=3,linestyle='--',color='green')

    plt.plot(excCurveSL[1.0][0][:,0],excCurveSL[1.0][0][:,1],
             label='SModelS (SL)',
             linewidth=3,linestyle='--',color='blue')

    plt.plot(excCurve[1.0][0][:,0],excCurve[1.0][0][:,1],
             label='SModelS (best SR)',
             linewidth=3,linestyle='--',color='red')


    plt.ylabel( yaxis, fontsize=24)
    plt.xlabel( xaxis, fontsize=24)
    plt.title(rf'{anaid}, {txname}', fontsize=18)
    plt.tight_layout()
    plt.legend()
    plt.savefig('comparison.png')

def plotRatio ( Dir, anaid, txname, axes, xlabel, ylabel ):
    cmd = f"../covariances/plotRatio.py -d {Dir} -a1 {anaid}-eff -a2 {anaid}-SL"
    cmd += f" -v1 {txname}_{axes}_combined.py -v2 {txname}_{axes}_combined.py"
    cmd += f" -xl '{xlabel}' -yl '{ylabel}'"
    print ( cmd )
    o = subprocess.getoutput ( cmd )
    print ( o )


if __name__ == "__main__":
    #plot ( "~/git/smodels-database/13TeV/ATLAS/", "ATLAS-SUSY-2018-04", "TStauStau",
    #       "2EqMassAx_EqMassBy", '$m_{\\tilde{\tau}}$ (GeV)', '$m_{\\tilde{\chi}_1^0}$ (GeV)' )
    plot ( "~/git/smodels-database/", "ATLAS-SUSY-2019-08", "TChiWH",
           "2EqMassAx_EqMassBy", '$m_{\\tilde{\chi}_1^\pm}$ (GeV)', '$m_{\\tilde{\chi}_1^0}$ (GeV)' )
    plotRatio ( "~/git/smodels-database/", "ATLAS-SUSY-2019-08", "TChiWH",
           "2EqMassAx_EqMassBy", '$m_{\\tilde{\chi}_1^\pm}$ (GeV)', '$m_{\\tilde{\chi}_1^0}$ (GeV)' )
