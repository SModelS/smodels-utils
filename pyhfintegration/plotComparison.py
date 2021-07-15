#!/usr/bin/env python3
# coding: utf-8

import matplotlib.pyplot as plt
import os,glob,copy,subprocess
import numpy as np
import time, random
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


def limitFromLimits ( upperLimit, expectedUpperLimit, expected=False ):
    """ kind of a closure test, from limits compute likelihoods,
        from which you compute a limit again """
    return upperLimit * random.uniform ( .9, 1.1 )
    from smodels.tools.statistics import likelihoodFromLimits
    llhd, mumax = likelihoodFromLimits ( upperLimit, expectedUpperLimit,
                                         None, return_mumax = True )
    totllhd = 0.
    llhds = []
    for i in np.arange ( -1.*(mumax+1), (mumax+1.)*4., (mumax+1.) / 10. ):
        # print ( "compute llhd for", upperLimit, expectedUpperLimit )
        llhd = likelihoodFromLimits ( upperLimit, expectedUpperLimit, i )
        if llhd != None:
            llhds.append ( (i, llhd ) )
            totllhd += llhd
    llhds = [ (x[0], x[1] / totllhd ) for x in llhds ]
    totllhd = 0.
    for i,llhd in llhds:
        totllhd += llhd
        if totllhd > .95:
            return i

def getShortAxis ( axes ):
    smsaxis = "[[x, y], [x, y]]"
    if axes == "2EqMassAx_EqMassBy_EqMassC60.0":
        smsaxis = "[[x, y, 60.0], [x, y, 60.0]]"
    if axes == "2EqMassAx_EqMassBx-y":
        smsaxis = "[[x, x - y], [x, x - y]]"
    return smsaxis

def getContour(xpts,ypts,zpts,levels,ylog=False,xlog=False):
    """
    Uses pyplot tricontour method to obtain contour
    curves in a 2D plane.

    :return: A dictionary with a list of contours for each level
    """
    if len(xpts ) == 0:
        return {}

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


def getXY ( curve, indices = None ):
    """ return x and y coordinates of curve """
    val = 1.0
    x,y = [], []
    if not val in curve:
        print ( f"[plotComparison] could not find curve 1.0, available are: {list(curve.keys())}" )
        return x,y

    crv = curve[val]
    if indices != None:
        if len(crv)< indices[0]:
            print ( f"[plotComparison] index {indices[0]} not in curve" )
            return
        x = crv[indices[0]][:,0].tolist()
        y = crv[indices[0]][:,1].tolist()
        for i in indices[1:]:
            if len(crv)< i:
                print ( f"[plotComparison] index {i} not in curve" )
                continue
            x+= crv[i][:,0].tolist()
            y+= crv[i][:,1].tolist()
        return x,y
    x = crv[0][:,0].tolist()
    y = crv[0][:,1].tolist()
    for i in range(1,len(curve[1.0])):
        x+= crv[i][:,0].tolist()
        y+= crv[i][:,1].tolist()
    return x,y


def plot( dbpath, anaid, txname, axes, xaxis, yaxis, compare ):
    """ plot comparison exclusion lines
    :param dbpath: path to database, e.g. ~/git/smodels-database/
    :param anaid: e.g. ATLAS-SUSY-2018-04
    :param txname: e.g. TStauStau
    :param axes: e.g. 2EqMassAx_EqMassBy
    :param compare: e.g. truncated, bestSR, SL, pyhf, ul
    """
    Dir = getPathName ( dbpath, anaid, None )

    if "bestsr" in compare:
        dataEff = getValidationModule ( dbpath, anaid+"-eff", f"{txname}_{axes}.py" ).validationData
        #Get points to compute exclusion curves:
        xpts = []
        ypts = []
        rpts = []
        for pt in dataEff:
            if 'error' in pt: continue
            xpts.append(pt['axes']['x'])
            ypts.append(pt['axes']['y'])
            rpts.append(pt['signal']/pt['UL'])
        excCurveEff = getContour(xpts,ypts,rpts,levels=[1.0],ylog=False)
    if "ul" in compare:
        dataUL  = getValidationModule ( dbpath, anaid, f"{txname}_{axes}.py" ).validationData
        #Get points to compute exclusion curves:
        xpts = []
        ypts = []
        rpts = []
        for pt in dataUL:
            if 'error' in pt: continue
            xpts.append(pt['axes']['x'])
            ypts.append(pt['axes']['y'])
            rpts.append(pt['signal']/pt['UL'])
        excCurveUL = getContour(xpts,ypts,rpts,levels=[1.0],ylog=False)
    if "pyhf" in compare:
        dataComb = getValidationModule ( dbpath, anaid+"-eff", f"{txname}_{axes}_combined.py" ).validationData
        xpts = []
        ypts = []
        rpts = []
        for pt in dataComb:
            if 'error' in pt: continue
            if pt["UL"]==None: continue
            xpts.append(pt['axes']['x'])
            ypts.append(pt['axes']['y'])
            rpts.append(pt['signal']/pt['UL'])
        excCurveComb = getContour(xpts,ypts,rpts,levels=[1.0],ylog=False)
    if "sl" in compare:
        dataSL = getValidationModule ( dbpath, anaid+"-SL", f"{txname}_{axes}_combined.py" ).validationData
        xpts = []
        ypts = []
        rpts = []
        for pt in dataSL:
            if 'error' in pt: continue
            xpts.append(pt['axes']['x'])
            ypts.append(pt['axes']['y'])
            rpts.append(pt['signal']/pt['UL'])
        excCurveSL = getContour(xpts,ypts,rpts,levels=[1.0],ylog=False)
    if "truncated" in compare:
        dataSLTrunc = getValidationModule ( dbpath, anaid,
                                            f"{txname}_{axes}.py" ).validationData
        xpts = []
        ypts = []
        rpts = []
        hasWarned=False
        for pt in dataSLTrunc:
            if 'error' in pt: continue
            if not "eUL" in pt:
                if not hasWarned:
                    print ( f"[plotComparison] validation file for truncated case has no eUL" )
                    hasWarned=True
                continue
            xpts.append(pt['axes']['x'])
            ypts.append(pt['axes']['y'])
            oUL = pt["UL"] # *random.uniform(.8,1.2)
            eUL = pt["eUL"]
            newoUL = limitFromLimits ( oUL, eUL, False )
            # print ( f"limitFromLimits {oUL} -> {newoUL}" )
            # neweUL = limitFromLimits ( oUL, eUL, True )
            rpts.append(pt['signal']/newoUL)
        excCurveTrunc = getContour(xpts,ypts,rpts,levels=[1.0],ylog=False)

    smsfile = f'{Dir}-eff/'
    # print ( "smsfile", smsfile )
    smsaxis  = getShortAxis ( axes )
    offCurve = uprootTools.getExclusionLine ( smsfile, txname, smsaxis )
    if offCurve == None:
        print ( f"[plotComparison] could not get exclusion line from {smsfile}:{txname}" )
    # print ( "axes", axes, "smsaxis", smsaxis, "offCurve", offCurve )

    # print(excATLAS.dtype)

    fig = plt.figure(figsize=(9,6))
    plt.plot( offCurve["x"], offCurve["y"], label='ATLAS',
              linewidth=3, linestyle='-', color='black' )

    if "ul" in compare:
        x,y = getXY ( excCurveUL )
        if len(x)>0:
            plt.plot( x, y, label='SModelS (UL)', linewidth=3,linestyle='--',color='magenta')

    if "pyhf" in compare:
        x,y = getXY ( excCurveComb )
        if len(x)>0:
            plt.plot( x, y, label='SModelS (pyhf)', linewidth=3,linestyle='--',color='green')

    if "sl" in compare:
        x,y = getXY ( excCurveSL )
        if len(x)>0:
            plt.plot( x, y, linewidth=3,linestyle='--',
                      label="SModelS (simplify)", color='blue' )

    if "bestsr" in compare:
        x,y = getXY ( excCurveEff )
        if len(x)>0:
            plt.plot( x, y, label='SModelS (best SR)',
                 linewidth=3,linestyle='--',color='red')

    if "truncated" in compare:
        x,y = getXY ( excCurveTrunc ) #, [2] )
        if len(x)>0:
            plt.plot( x, y, label='SModelS (truncated Gaussian)',
                 linewidth=3,linestyle='--',color='cyan')


    plt.ylabel( yaxis, fontsize=24)
    plt.xlabel( xaxis, fontsize=24)
    plt.title(rf'{anaid}, {txname}', fontsize=18)
    dx = plt.xlim()[1] - plt.xlim()[0]
    dy = plt.ylim()[1] - plt.ylim()[0]
    xv = plt.xlim()[1] - .27*dx
    yv = plt.ylim()[0] - .12*dy
    if True:
        plt.text ( xv, yv, time.asctime(), c="grey", fontsize=13 )
    import IPython
    # IPython.embed()
    plt.tight_layout()
    plt.legend()
    fname = f'comparison_{anaid}_{txname}.png'
    print ( f"[plotComparison] saving to {fname}" )
    plt.savefig( fname )

def plotRatio ( Dir, anaid, txname, axes, xlabel, ylabel ):
    cmd = f"../covariances/plotRatio.py -d {Dir} -a1 {anaid}-eff -a2 {anaid}-SL"
    cmd += f" -v1 {txname}_{axes}_combined.py -v2 {txname}_{axes}_combined.py"
    cmd += f" -xl '{xlabel}' -yl '{ylabel}' -l1 pyhf -l2 SL"
    print ( cmd )
    o = subprocess.getoutput ( cmd )
    print ( o )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="The comparison plotter")
    parser.add_argument('-a','--analysisid', help='specify analysis id [ATLAS-SUSY-2019-08]',
            type=str, default="ATLAS-SUSY-2019-08" )
    parser.add_argument('-t','--txname', help='specify topolofy, none for the analysis default [TChiWH]',
            type=str, default=None )
    parser.add_argument('-d','--database', help='path to database [~/git/smodels-database]',
            type=str, default="~/git/smodels-database" )
    parser.add_argument('-A','--axes', help='specify axes, none for analysis default [2EqMassAx_EqMassBy]',
            type=str, default=None )
    parser.add_argument('-c','--compare', help='specify which versions to compare [bestSR,SL,pyhf]',
            type=str, default="bestSR,SL,pyhf" )
    parser.add_argument('-x','--xlabel', help='specify label of x axis, none for analysis default [$m_{\\tilde{\chi}_1^\pm}$ (GeV)]',
            type=str, default=None )
    parser.add_argument('-y','--ylabel', help='specify label of y axis, none for analysis default [$m_{\\tilde{\chi}_1^0}$ (GeV)]',
            type=str, default=None )
    parser.add_argument('-r','--ratio', help='ratio plot, not comparison plot',
                        action="store_true" )

    args = parser.parse_args()
    compare = [ x.lower().strip() for x in args.compare.split ( "," ) ]
    nones = [ None, "", "none", "None" ]

    defaultTxnames = { "ATLAS-SUSY-2019-08": "TChiWH",
                       "ATLAS-SUSY-2018-31": "T6bbHH",
                       "ATLAS-SUSY-2018-16": "TSlepSlep",
                       "ATLAS-SUSY-2018-04": "TStauStau",
                       "ATLAS-SUSY-2018-06": "TChiWZ",
    }

    defaultAxes = { "ATLAS-SUSY-2019-08": "2EqMassAx_EqMassBy",
                    "ATLAS-SUSY-2018-31": "2EqMassAx_EqMassBy_EqMassC60.0",
                    "ATLAS-SUSY-2018-16": "2EqMassAx_EqMassBx-y",
                    "ATLAS-SUSY-2018-04": "2EqMassAx_EqMassBy",
                    "ATLAS-SUSY-2018-06": "2EqMassAx_EqMassBy",
    }

    defaultXLabels = { "ATLAS-SUSY-2019-08": "$m_{\\tilde{\chi}_1^\pm}$ (GeV)",
                       "ATLAS-SUSY-2018-31": "$m_{\\tilde{b}}$ (GeV)",
                       "ATLAS-SUSY-2018-16": "$m_{\\tilde{l}}$ (GeV)",
                       "ATLAS-SUSY-2018-04": "$m_{\\tilde{\\tau}}$ (GeV)",
                       "ATLAS-SUSY-2018-06": "$m_{\\tilde{\chi}_1^\pm}$ (GeV)",
    }

    defaultYLabels = { "ATLAS-SUSY-2019-08": "N1",
                       "ATLAS-SUSY-2018-31": "N1",
                       "ATLAS-SUSY-2018-16": "N1",
                       "ATLAS-SUSY-2018-04": "N1",
                       "ATLAS-SUSY-2018-06": "N1",
    }

    if args.analysisid in defaultTxnames and args.txname in nones:
        args.txname = defaultTxnames[args.analysisid]
    if args.analysisid in defaultAxes and args.axes in nones:
        args.axes = defaultAxes[args.analysisid]
    if args.analysisid in defaultXLabels and args.xlabel in nones:
        args.xlabel = defaultXLabels[args.analysisid]
    if args.analysisid in defaultYLabels and args.ylabel in nones:
        args.ylabel = defaultYLabels[args.analysisid]

    if args.xlabel == "stau":
        args.xlabel = "$m_{\\tilde{\tau}}$ (GeV)"
    if args.ylabel == "N1":
        args.ylabel = "$m_{\\tilde{\chi}_1^0}$ (GeV)"
    if args.ratio:
        plotRatio ( args.database, args.analysisid, args.txname, args.axes, args.xlabel,
                    args.ylabel )
    else:
        plot ( args.database, args.analysisid, args.txname, args.axes,
               args.xlabel, args.ylabel, compare )
    #plot ( "~/git/smodels-database/13TeV/ATLAS/", "ATLAS-SUSY-2018-04", "TStauStau",
    #       "2EqMassAx_EqMassBy", '$m_{\\tilde{\tau}}$ (GeV)', '$m_{\\tilde{\chi}_1^0}$ (GeV)' )
    #plot ( "~/git/smodels-database/", "ATLAS-SUSY-2019-08", "TChiWH",
    #       "2EqMassAx_EqMassBy", '$m_{\\tilde{\chi}_1^\pm}$ (GeV)', '$m_{\\tilde{\chi}_1^0}$ (GeV)' )
    #plotRatio ( "~/git/smodels-database/", "ATLAS-SUSY-2019-08", "TChiWH",
    #       "2EqMassAx_EqMassBy", '$m_{\\tilde{\chi}_1^\pm}$ (GeV)', '$m_{\\tilde{\chi}_1^0}$ (GeV)' )
