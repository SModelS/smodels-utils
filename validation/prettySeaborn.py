#!/usr/bin/env python3

"""
.. module:: prettySeaborn
   :synopsis: the module for the "pretty" seaborn-based plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import logging,os,sys,random,copy
import numpy as np
sys.path.append('../')
from array import array
import math,ctypes
logger = logging.getLogger(__name__)
from smodels.tools.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxes
from plottingFuncs import yIsLog, getFigureUrl, getDatasetDescription

try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass

from scipy import interpolate
import numpy as np

# copied from https://stackoverflow.com/questions/37662180/interpolate-missing-values-2d-python
def interpolate_missing_pixels(
        image: np.ndarray,
        mask: np.ndarray,
        method: str = 'nearest',
        fill_value: float = 0
):
    """
    :param image: a 2D image
    :param mask: a 2D boolean image, True indicates missing values
    :param method: interpolation method, one of
        'nearest', 'bilinear', 'bicubic'.
    :param fill_value: which value to use for filling up data outside the
        convex hull of known pixel values.
        Default is 0, Has no effect for 'nearest'.
    :return: the image with missing values interpolated
    """
    from scipy import interpolate

    h, w = image.shape[:2]
    xx, yy = np.meshgrid(np.arange(w), np.arange(h))

    known_x = xx[~mask]
    known_y = yy[~mask]
    known_v = image[~mask]
    missing_x = xx[mask]
    missing_y = yy[mask]

    interp_values = interpolate.griddata(
        (known_x, known_y), known_v, (missing_x, missing_y),
        method=method, fill_value=fill_value
    )

    interp_image = image.copy()
    interp_image[missing_y, missing_x] = interp_values

    return interp_image

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
    # Check if data has been defined:
    tgr, etgr, tgrchi2 = [], [], []
    kfactor=None
    xlabel, ylabel, zlabel = 'x [GeV]','y [GeV]',"$r = \sigma_{signal}/\sigma_{UL}$"
    logY = yIsLog ( validationPlot )
    if logY:
        xlabel = "x [mass, GeV]"
        ylabel = "y [width, GeV]"

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
        #import IPython
        # IPython.embed()
        if not "axes" in pt:
            ## try to get axes from slha file
            pt["axes"] = validationPlot.getXYFromSLHAFileName ( pt["slhafile"], asDict=True )
        xvals = pt['axes']
        if xvals == None: ## happens when not on the plane I think
            continue
        if (not "UL" in pt.keys() or pt["UL"]==None) and (not "error" in pt.keys()):
            logger.warning( "no UL for %s: %s" % (xvals, pt ) )
        r, rexp = float("nan"), float("nan")
        if not "error" in pt.keys():
            if pt["UL"]!=None:
                r = pt['signal']/pt ['UL']
            if "eUL" in pt and pt["eUL"] != None and pt["eUL"] > 0.:
                hasExpected = True
                rexp = pt['signal']/pt ['eUL']
        if r > 3.:
            r=3.
        if rexp > 3.:
            rexp=3.
        if isinstance(xvals,dict):
            if len(xvals) == 1:
                x,y = xvals['x'],r
                ylabel = "r = $\sigma_{signal}/\sigma_{UL}$"
            else:
                x = xvals["x"]
                if "y" in xvals:
                    y = xvals['y']
                elif "w" in xvals:
                    y = xvals['w']

        else:
            x,y = xvals
        if logY:
            y = rescaleWidth(y)

        if "condition" in pt.keys() and pt['condition'] and pt['condition'] > 0.05:
            condV += 1
            if condV < 5:
                logger.warning("Condition violated for file " + pt['slhafile'])
            if condV == 5:
                logger.warning("Condition violated for more points (not shown)")
        else:
            if not "error" in pt.keys():
                tgr.append( { "i": len(tgr), "x": x, "y": y, "r": r })
                if np.isfinite ( rexp ):
                    etgr.append( { "i": len(etgr), "x": x, "y": y, "rexp": rexp } )
                if "chi2" in pt:
                    tgrchi2.append( { "i": len(tgrchi2), "x": x, "y": y, "chi2": pt["chi2"] / 3.84 } )
    if options["drawExpected"] in [ "auto" ]:
        options["drawExpected"] = hasExpected
    if len ( tgr ) < 4:
        logger.error("No good points for validation plot.")
        return (None,None)

    def get ( var, mlist ):
        ret = []
        for d in mlist:
            ret.append(d[var])
        return ret

    #ROOT has trouble obtaining a histogram from a 1-d graph. So it is
    #necessary to smear the points if they rest in a single line.
    xs = get( "x", tgr )
    ys = get( "y", tgr )
    exs = get( "x", etgr )
    eys = get( "y", etgr )
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
    resultType = "%s" %str(types)
    title = title + " ("+resultType+")"
    import matplotlib.pylab as plt

    #Get contour graphs:
    contVals = [1./looseness,1.,looseness]
    if options["drawExpected"]:
        contVals = [1.,1.,1.]
    cgraphs = {} # getContours(tgr,contVals, "prettyPlots:cgraphs" )
    ecgraphs = {}
    if options["drawExpected"]:
        ecgraphs = {} # getContours(etgr,contVals, "prettyPlots:ecgraphs" )
    chi2graphs = {} # getContours ( tgrchi2, [ 1. ] * 3, "prettyPlots:chi2graphs" )
    # print ( "chi2graphs", chi2graphs )

    #Draw temp plot:
    rs = get ( "r", tgr )
    Z = {}
    def closeValue ( x_, y_, tgr ):
        dmin, v = float("inf"), None
        for t in tgr:
            d = (t["x"]-x_)**2 + (t["y"]-y_)**2
            if d < dmin:
                dmin = d
                v = t["r"]
        if dmin < 1.:
            return v
        return float("nan")

    for t in tgr:
        x = t["x"]
        y = t["y"]
        r = t["r"]
        if not x in Z:
            Z[x]={}
        Z[x][y]=float(r)
    xs = list ( Z.keys() )
    xs.sort( )
    T = []
    ys.sort( reverse = True )
    for y in ys:
        tmp = []
        for x in xs:
            r = float("nan")
            if y in Z[x]:
                r = Z[x][y]
            else:
                r = closeValue ( x, y, tgr )
            tmp.append ( r )
            rs.append ( r )
                # tmp.append ( float("nan") )
        T.append ( tmp )
    T = np.asarray ( T )
    mask = np.isnan( T )
    T = interpolate_missing_pixels ( T, mask, "linear", fill_value=float("nan") )
    ax = plt.gca()
    fig = plt.gcf()
    # print ( "T", T[-3:] )
    # cm = plt.cm.RdYlGn_r
    cm = plt.cm.RdYlBu_r
    xtnt = ( min(xs), max(xs), min(ys), max(ys) )
    im = plt.imshow ( T, cmap=cm, extent=xtnt, interpolation="bicubic",
                      vmax = 3.0, vmin = 0., aspect="auto" )
    plt.title ( title )
    # plt.text ( .28, .85, title, transform = fig.transFigure )
    plt.xlabel ( xlabel )
    plt.ylabel ( ylabel )
    

    for p in validationPlot.officialCurves:
            plt.plot ( p["points"]["x"], p["points"]["y"], c="black", label="exclusion (official)" )
    if options["drawExpected"]:
        for p in validationPlot.expectedOfficialCurves:
                plt.plot ( p["points"]["x"], p["points"]["y"], c="black", linestyle="dotted", 
                       label="exp. excl. (official)" )
    plt.colorbar ( im, label=zlabel, fraction = .046, pad = .04 )
    cs = plt.contour( T, colors="red", levels=[1.], extent = xtnt, 
                       origin="image" )
    cs = plt.plot([-1,-1],[0,0], c = "red", label = "exclusion (SModelS)", 
                  transform = fig.transFigure ) 
    """
    ya = h.GetYaxis()
    if logY:
        ya.SetLabelSize(.06)
        nbins = ya.GetNbins()
        last = 0
        for i in range( 1, nbins ):
            center = ya.GetBinCenter(i)
            width = unscaleWidth ( center )
            if type(width) == type(GeV):
                width = float ( width.asNumber(GeV) )
            center10 = math.log10 ( width )
            r_center = int ( round ( center10 ) )
            delta = abs ( center10 - r_center )
            if r_center != last and delta < .1:
                ya.SetBinLabel( i, "10^{%d}" % r_center )
                last = r_center
    isEqual = {}
    x1,x2 = ctypes.c_double(), ctypes.c_double()
    y1,y2 = ctypes.c_double(), ctypes.c_double()
    for cval,grlist in cgraphs.items():
        isEqual[cval]={}
        if ecgraphs is None or not cval in ecgraphs:
            continue
        tmpe = ecgraphs[cval]
        for i,gr in enumerate(grlist):
            if gr.GetN() == 0:
                continue
            isEqual[cval][i]=False
            if i+1>len(tmpe):
                continue
            if gr.GetN() != tmpe[i].GetN():
                continue
            hasDiscrepancy = False
            for j in range(gr.GetN()):
                gr.GetPoint(j,x1,y1 )
                tmpe[i].GetPoint(j,x2,y2 )
                dx = abs ( (x1.value-x2.value) / ( x1.value+x2.value ) )
                dy = abs ( (y1.value-y2.value) / ( y1.value+y2.value ) )
                if dx > 1e-3 or dy > 1e-3:
                    hasDiscrepancy = True
                    break
            if not hasDiscrepancy:
                isEqual[cval][i]=True

    if ecgraphs is not None:
        for cval,grlist in ecgraphs.items():
            if cval == 1.0:
                ls = 2
            else:
                continue
            for i,gr in enumerate(grlist):
                try:
                    if isEqual[cval][i]: ## is equal we need to add noise!
                        for j in range(gr.GetN()):
                            gr.GetPoint(j,x1,y1 )
                            xn = x1.value*random.gauss(1.,.001)
                            yn = y1.value*random.gauss(1.,.001)
                            gr.SetPoint( j, xn, yn ) 
                except KeyError as e:
                    ## may not exist
                    pass

                setOptions(gr, Type='official')
                gr.SetLineColor(ROOT.kRed) # ROOT.Orange+2)
                # gr.SetLineColor(ROOT.kBlack) # ROOT.Orange+2)
                gr.SetLineStyle(ls)
                if gr.GetN() > 0:
                    gr.Draw("L SAME")
    for cval,grlist in cgraphs.items():
        lw = 1
        if cval == 1.0:
            ls = 1
            lw = 3
        else:
            ls = 2
        if ecgraphs is not None and len(ecgraphs)>0 and options["drawExpected"]:
            ls = 2 ## when expected are drawn also, make this dashed
        for gr in grlist:
            setOptions(gr, Type='official')
            gr.SetLineColor(ROOT.kRed)
            gr.SetLineWidth ( lw )
            #gr.SetLineColor(ROOT.kGray+2)
            #gr.SetLineStyle(ls)
            if gr.GetN() > 0:
                gr.Draw("L SAME")
    if options["drawChi2Line"] and chi2graphs != None: # False:
        for cval,grlist in chi2graphs.items():
            for gr in grlist:
                setOptions(gr, Type='official')
                gr.SetLineColor(ROOT.kGreen+2)
                grN = gr.GetN()
                buff = gr.GetX()
                #buff.SetSize(etgrN)
                xpts = np.frombuffer(buff,count=grN)
                buff = gr.GetY()
                ypts = np.frombuffer(buff,count=grN)
                for i in range(int(gr.GetN())):
                    gr.SetPoint(i,xpts[i],ypts[i]+random.uniform(0.,2.))
                # gr.SetLineStyle(5)
                if gr.GetN() > 0:
                    gr.Draw("L SAME")
    for gr in official:
        # validationPlot.completeGraph ( gr )
        setOptions(gr, Type='official')
        gr.SetLineColor ( ROOT.kBlack )
        if "P1" in gr.GetTitle() or "M1" in gr.GetTitle():
            gr.SetLineWidth(1)
            # gr.SetLineStyle(0)
        if gr.GetN() > 0:
            gr.Draw("L SAME")
    if options["drawExpected"]:
        for gr in expectedOfficialCurves:
            # validationPlot.completeGraph ( gr )
            setOptions(gr, Type='official')
            gr.SetLineColor ( ROOT.kBlack )
            gr.SetLineStyle ( 2 )
            # gr.SetLineColor ( ROOT.kRed+2 )
            if gr.GetN() > 0:
                gr.Draw("L SAME")
    """
    pName = prettyTxname(validationPlot.txName, outputtype="latex" )
    if pName == None:
        pName = "define {validationPlot.txName} in prettyDescriptions"
    txStr = validationPlot.txName +': '+pName
    plt.text(.03,.95,txStr,transform=fig.transFigure, fontsize=9 )
    axStr = prettyAxes(validationPlot.txName,validationPlot.axes,\
                       outputtype="latex")
    axStr = str(axStr).replace(']','').replace('[','').replace("'","")
    axStr = axStr.replace("\\\\t","\\t")
    axStr = axStr.replace("\\\\p","\\p")
    axStr = axStr.replace("\\\\c","\\c")
    plt.text(.77,.95,axStr,transform=fig.transFigure, fontsize=9 )
    figureUrl = getFigureUrl(validationPlot)

    subtitle = getDatasetDescription ( validationPlot )
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
    plt.text ( .6, .0222, subtitle, transform=fig.transFigure, fontsize=10 )
    if figureUrl:
        plt.text( .13, .13, f"{figureUrl}", 
                  transform=fig.transFigure, c = "black", fontsize = 7 )
		    # l1.DrawLatex(.01,0.023,"#splitline{official plot:}{%s}" % figureUrl)

    """
    nleg = 1
    if cgraphs != None and official != None:
    #Count the number of entries in legend:
        nleg = min(2,len(cgraphs)-list(cgraphs.values()).count([])) + min(2,len(official))
    #Draw legend:
    dx = 0. ## top, left
    dx = .33 ## top, right
    hasExclLines = False
    added = False
    for gr in official:
        if 'xclusion_' in gr.GetTitle():
            leg.AddEntry(gr,"exclusion (official)","L")
            hasExclLines = True
        elif ('xclusionP1_' in gr.GetTitle() or 'xclusionM1_' in gr.GetTitle()) and \
                (not added):
            leg.AddEntry(gr,"#pm1#sigma (official)","L")
            hasExclLines = True
            added = True
    added = False
    for gr in expectedOfficialCurves:
        if 'xclusion_' in gr.GetTitle():
            if options["drawExpected"]:
                gr.SetLineColor ( ROOT.kBlack ) # make sure these are right
                gr.SetLineStyle ( 2 )
                leg.AddEntry(gr,"exp. excl. (official)","L")
            hasExclLines = True
        elif ('xclusionP1_' in gr.GetTitle() or 'xclusionM1_' in gr.GetTitle()) and \
                (not added):
            leg.AddEntry(gr,"#pm1#sigma (official)","L")
            hasExclLines = True
            added = True
    added = False
    for cval,grlist in cgraphs.items():
        if not grlist:
            continue
        if cval == 1.0:
            leg.AddEntry(grlist[0],"exclusion (SModelS)","L")
            hasExclLines = True
        elif (cval == looseness or cval == 1./looseness) and not added:
            leg.AddEntry(grlist[0],"#pm20% (SModelS)","L")
            hasExclLines = True
            added = True
    added = False
    if options["drawExpected"] and ecgraphs is not None:
        for cval,grlist in ecgraphs.items():
            if not grlist:
                continue
            if cval == 1.0:
                leg.AddEntry(grlist[0],"exp. excl. (SModelS)","L")
                hasExclLines = True
            elif (cval == looseness or cval == 1./looseness) and not added:
                leg.AddEntry(grlist[0],"#pm20% (SModelS)","L")
                hasExclLines = True
                added = True
    if options["drawChi2Line"] and chi2graphs != None:
        for cval,grlist in chi2graphs.items():
            if not grlist:
                continue
            if cval == 1.0:
                leg.AddEntry(grlist[0],"exclusion (#chi^{2})","L")
                hasExclLines = True

    if hasExclLines:
        leg.Draw()
    """
    if kfactor is not None and abs ( kfactor - 1.) > .01:
        plt.text( .65,.83, "k-factor = %.2f" % kfactor, fontsize=10,
                  c="gray", transform = fig.transFigure )
    if options["preliminary"]:
        ## preliminary label, pretty plot
        plt.text ( .3, .4, "SModelS preliminary", transform=fig.transFigure,
                   rotation = 25., fontsize = 18, c="blue", zorder=100 )
    legendplacement = options["legendplacement"]
    legendplacement = legendplacement.replace("'","")
    legendplacement = legendplacement.replace("bottom","lower")
    legendplacement = legendplacement.replace("top","upper")
    legendplacement = legendplacement.replace('"',"")
    legendplacement = legendplacement.lower()
    legendplacement = legendplacement.strip()
    if legendplacement in [ "automatic", None, "", "None" ]:
        legendplacement = "best"
    plt.legend( loc=legendplacement ) # could be upper right
    # plt.tight_layout()

    if not silentMode:
        ans = raw_input("Hit any key to close\n")

    if not hasYValues:
        logger.error ( "it seems like we do not have y-values, so we break off." )
        plt.dontplot = True

    return plt,tgr
