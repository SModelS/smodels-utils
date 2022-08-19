#!/usr/bin/env python3

"""
.. module:: uglyPlots
   :synopsis: Main method for creating ugly plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,numpy,random,copy
sys.path.append('../')
from array import array
import math, ctypes
logger = logging.getLogger(__name__)
from smodels.tools.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxes
from plottingFuncs import getGridPoints, yIsLog, getFigureUrl, getDatasetDescription
from rootPlottingFuncs import setOptions, setAxes

try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass

def createUglyPlot( validationPlot,silentMode=True, looseness = 1.2, options : dict = {} ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate the "ugly" exclusion plot

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :return: TCanvas object containing the plot
    """
    import ROOT
    logger.info ( "now create ugly plot for %s, %s: %s" % \
       ( validationPlot.expRes.globalInfo.id, validationPlot.txName,
         validationPlot.axes ) )
    origdata = getGridPoints ( validationPlot )

    # Check if data has been defined:
    xlabel, ylabel = 'x','y'
    excluded, allowed, excluded_border, allowed_border = ROOT.TGraph(), ROOT.TGraph(), ROOT.TGraph(), ROOT.TGraph()
    gridpoints = ROOT.TGraph()
    noresult = ROOT.TGraph() ## queried but got no result
    excluded.SetName("excluded")
    allowed.SetName("allowed")
    noresult.SetName("noresult")
    excluded_border.SetName("excluded_border")
    allowed_border.SetName("allowed_border")
    gridpoints.SetName ( "gridpoints" )
    cond_violated=ROOT.TGraph()
    kfactor=None
    logY = yIsLog ( validationPlot )
    tavg = 0.

    countPts = 0 ## count good points

    if not validationPlot.data:
        logger.debug("Data for validation plot is not defined.")
        # x,y = get
        return (None,None)
        ## sys.exit()

    nErrors = 0
    # Get excluded and allowed points:
    nmax = len(validationPlot.data)
    if False:
        nmax = 20
    dn = 50
    print ( " "*int(45+nmax/dn), end="<\r" )
    print ( "[uglyPlots] checking validation points >", end="" )
    ycontainer=[]
    for ctPoints,pt in enumerate(validationPlot.data):
        if ctPoints % dn == 0:
            print ( ".", end="", flush=True )
        if ctPoints == nmax:
            print ( "[uglyPlots] emergency break" )
            break
        if "error" in pt.keys():
            vD = validationPlot.getXYFromSLHAFileName ( pt["slhafile"], asDict=True )
            # print ( "vD", vD, pt["slhafile"], validationPlot.axes )
            if vD != None:
                # print ( "adding no-result point", noresult.GetN(), vD )
                x_, y_ = copy.deepcopy ( vD["x"] ), None
                if "y" in vD.keys():
                    y_ = copy.deepcopy ( vD["y"] )
                elif "w" in vD.keys():
                    y_ = copy.deepcopy ( vD["w"] )
                if y_ is None:
                    logger.error ( "the data is 1d." ) # is separate module now
                    sys.exit()
                noresult.SetPoint(noresult.GetN(), x_, y_ )
            nErrors += 1
            continue
        countPts += 1
        if kfactor == None:
            kfactor = pt ['kfactor']
        if abs(kfactor - pt['kfactor'])> 1e-5:
            logger.error("kfactor not a constant throughout the plane!")
            sys.exit()

        xvals = pt['axes']
        if xvals == None:
            # happens when not on the plane?
            continue
        if "t" in pt:
            tavg += pt["t"]
        if pt["UL"] == None:
            logger.warning ( "No upper limit for %s" % xvals )
            continue
        r = pt['signal']/pt ['UL']
        # print ( "x,y,r",r )
        if xvals == None:
            # dont have any coordinates? skip.
            logger.warning ( f'do I need to skip {pt}?' )
            continue
        if isinstance(xvals,dict):
            if len(xvals) == 1:
                x,y = xvals['x'],r
                ylabel = "r = #sigma_{signal}/#sigma_{UL}"
            else:
                x = xvals["x"]
                if "y" in xvals:
                    y = xvals['y']
                elif "w" in xvals:
                    y = xvals['w']
        else:
            x,y = pt['axes']
        ycontainer.append ( y )

        if 'condition' in pt and pt['condition'] and pt['condition'] > 0.05:
            logger.warning("Condition violated at %f for file %s" % ( pt['condition'], pt['slhafile']) )
            cond_violated.SetPoint(cond_violated.GetN(), x, y)
        elif r > 1.:
            if r < looseness:
                excluded_border.SetPoint(excluded_border.GetN(), x, y)
            else:
                excluded.SetPoint(excluded.GetN(), x, y )
        else:
            if r> 1./looseness:
                allowed_border.SetPoint(allowed_border.GetN(), x, y)
            else:
                allowed.SetPoint(allowed.GetN(), x, y)

    logger.info ( "done!" )

    massPlane = MassPlane.fromString( validationPlot.txName, validationPlot.axes )
    for ctr,coords in enumerate(origdata):
        #masses = removeUnits ( pt[0], standardUnits=GeV )
        #coords = massPlane.getXYValues(masses)
        if coords != None and "y" in coords:
            gridpoints.SetPoint( gridpoints.GetN(), coords["x"], coords["y"] )

    if countPts == 0:
        logger.warning ( "no good points??" )
        return ( None, None )
    tavg = tavg / len (validationPlot.data )

    from smodels_utils.helper.rootTools import exclusionCurveToTGraph
    official = exclusionCurveToTGraph ( validationPlot.officialCurves )
    eofficial = exclusionCurveToTGraph ( validationPlot.expectedOfficialCurves )
    # Check if official exclusion curve has been defined:
    if official == []:
        logger.warning("Official curve for validation plot is not defined.")
    else:
        logger.debug("Official curves have length %d" % len (official) )
    if eofficial == []:
        logger.debug("Expected official curve for validation plot is not defined.")
    else:
        logger.debug("expected official curves have length %d" % len (eofficial) )

    if silentMode: ROOT.gROOT.SetBatch()
    setOptions(allowed, Type='allowed')
    setOptions(cond_violated, Type='cond_violated')
    setOptions(allowed_border, Type='allowed_border')
    setOptions(excluded, Type='excluded')
    setOptions(excluded_border, Type='excluded_border')
    setOptions(noresult, Type='noresult')
    base = ROOT.TMultiGraph()
    for i in official:
        setOptions( i, Type='official')
    for i in eofficial:
        setOptions( i, Type='eofficial')
    setOptions(gridpoints, Type='gridpoints')
    dx = .12 ## top, left
    nleg = 5
    from sympy import var
    xvar_,yvar_,zvar_,wvar_ = var( "xvar_ yvar_ zvar_ wvar_" )
    g=eval(validationPlot.axes.replace("x","xvar_").replace("y","yvar_").replace("z","zvar_").replace("w","wvar_" ) )
    reverse = (g[1][0]==yvar_) ## do reverse if [x,*],[y,*] type of plot (eg TGQ)
    if reverse: ## if it is an [x,*],[y,*] plot, put legend to right, not left
        dx = .53
    x1_, x2_ = dx, 0.35+dx
    y1_, y2_ = 0.82-0.040*nleg,0.88
    if logY: # move it to top right
        x1_, x2_ = 0.37+dx, 0.775+dx
        y1_, y2_ = 0.78-0.040*nleg,0.84
    leg = ROOT.TLegend( x1_,y1_,x2_,y2_ )
    setOptions(leg)
    leg.SetTextSize(0.04)
    if allowed.GetN()>0:
        base.Add(allowed, "P")
        leg.AddEntry ( allowed, "allowed", "P" )
    if excluded.GetN()>0:
        base.Add(excluded, "P")
        leg.AddEntry ( excluded, "excluded", "P" )
    if allowed_border.GetN()>0:
        base.Add(allowed_border, "P")
        leg.AddEntry(allowed_border, "allowed (but close)", "P")
    if excluded_border.GetN()>0:
        base.Add(excluded_border, "P")
        leg.AddEntry(excluded_border, "excluded (but close)", "P")
    if cond_violated.GetN()>0:
        base.Add(cond_violated, "P")
        leg.AddEntry( cond_violated, "condition violated", "P" )
    if noresult.GetN()>0:
        base.Add(noresult, "P")
        leg.AddEntry( noresult, "no result", "P" )
    if xvals != None and len(xvals) == 1:
        for i in official:
            if i.GetN() == 1:
                xtmp,ytmp=ctypes.c_double(),ctypes.c_double()
                i.GetPoint(0,xtmp,ytmp)
                yn = 1.1
                if ytmp.value > .5:
                    yn = 0.
                i.SetPoint(1, xtmp, yn )
    for i in eofficial:
        i.SetLineStyle ( 3 )
        base.Add( i, "L")
    for ctr,i in enumerate(official):
        base.Add( i, "L")
        completed = copy.deepcopy ( i )
        from smodels_utils.helper.rootTools import completeROOTGraph
        completeROOTGraph ( completed )
        completed.SetLineColor( ROOT.kMagenta )
        completed.SetLineStyle( 3 ) # show also how plot is completed
        completed.Draw("LP SAME" )
        base.Add ( completed )
        if ctr == 0:
            leg.AddEntry ( i, "official exclusion", "L" )
        #else:
        #    leg.AddEntry ( i, f"what is this {i.GetName()}", "L" )
    for ctr,i in enumerate(eofficial):
        c2 = copy.deepcopy ( i )
        c2.SetLineColor( ROOT.kMagenta )
        from smodels_utils.helper.rootTools import completeROOTGraph
        completeROOTGraph ( c2 )
        c2.SetLineStyle( 2 ) # show also how plot is completed
        c2.Draw("LP SAME" )
        if ctr == 0:
            leg.AddEntry ( i, "expected off. excl.", "L" )
    #"""
    if gridpoints.GetN()>0:
        base.Add(gridpoints, "P")
        leg.AddEntry(gridpoints, "%d SModelS grid points" % gridpoints.GetN(), "P")
    title = validationPlot.expRes.globalInfo.id + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.axes
            #+ "_" + validationPlot.niceAxes
    subtitle = getDatasetDescription ( validationPlot )
    figureUrl = getFigureUrl(validationPlot)
    plane = ROOT.TCanvas("Validation Plot", title, 0, 0, 800, 600)
    base.SetTitle(title)
    base.Draw("APsame")
    setAxes ( base, options["style"] )
    if logY: # y>1e-24 and y<1e-6:
        ## assume that its a "width" axis
        # print ( "set log", ycontainer )
        plane.SetLogy()
        ymin = min ( ycontainer ) * 0.5
        ymax = max ( ycontainer ) * 2.
        base.GetYaxis().SetRangeUser( ymin, ymax )
    else:
        if not "style" in options or not "axis" in options["style"]:
            from smodels_utils.helper.rootTools import getBoundingBox, boundingBoxIsFinite
            bb = getBoundingBox ( official )
            if boundingBoxIsFinite ( bb ):
                base.GetYaxis().SetRangeUser( .8*bb["y"][0], 1.25*bb["y"][1] )
                base.GetXaxis().SetRangeUser( .8*bb["x"][0], 1.25*bb["x"][1] )
    leg.Draw()
    #base.Draw("Psame")
    base.leg = leg
    try:
        base.GetXaxis().SetTitle(xlabel)
        base.GetYaxis().SetTitle(ylabel)
    except:
        pass
    if xvals != None and len(xvals) == 1:
        base.GetYaxis().SetRangeUser(0.0,2.0)

    l=ROOT.TLatex()
    l.SetNDC()
    l.SetTextSize(.04)
    base.l=l
    l0=ROOT.TLatex()
    l0.SetNDC()
    l0.SetTextSize(.025)
    l0.DrawLatex(.05,.905,subtitle)
    base.l0=l0
    signal_factor = 1. # an additional factor that is multiplied with the signal cross section
    agreement = 0.
    weighted = options["weightedAgreementFactor"] # compute weighted agreement factor?
    af = validationPlot.computeAgreementFactor( signal_factor = signal_factor,
                                                weighted = weighted )
    agreement = 0.
    if math.isfinite(af):
        agreement = round(100.*af)
    logger.info ( "\033[32mAgreement: %d%s\033[0m (with %d points)" % \
                  ( agreement,"%",len(validationPlot.data) ) )
    if options["extraInfo"]:
        lex=ROOT.TLatex()
        lex.SetNDC()
        lex.SetTextColor( ROOT.kBlue+2 ) # kCyan-5 kMagenta-5 kBlue-5
        lex.SetTextSize(.026 )
        import socket
        hn=socket.gethostname()
        phn = hn.find(".")
        if phn > 0:
            hn = hn[:phn]
        lex.DrawLatex(.63,.12,"agreement: %d%s, t~%.1fs [%s]" % (agreement, "%", tavg, hn ) )
        base.lex=lex

    if figureUrl:
        l1=ROOT.TLatex()
        l1.SetNDC()
        l1.SetTextSize(.02)
        l1.DrawLatex(.06,.02,"%s" % figureUrl)
        base.l1=l1
    l2=ROOT.TLatex()
    l2.SetNDC()
    l2.SetTextSize(.025)
    l2.SetTextAngle(90.)
    l2.SetTextColor( ROOT.kGray )
    if True: # abs ( kfactor - 1. ) > 1e-5:
        l2.DrawLatex(.93,.18,"k-factor %.2f" % kfactor)
    base.l2=l2

    l3=ROOT.TLatex()
    l3.SetNDC()
    l3.SetTextSize(.025)
    l3.SetTextColor( ROOT.kGray )
    dxpnr=.68 ## top, right
    if reverse: ## if reverse put this line at left of plot
        dxpnr = .12
    l3.DrawLatex( dxpnr,.87,"%d / %d points with no results" % \
                  (nErrors, len(validationPlot.data) ) )
    base.l3=l3

    if options["extraInfo"]: ## a timestamp, on the right border
        import time
        l9=ROOT.TLatex()
        l9.SetNDC()
        l9.SetTextSize(.025)
        l9.SetTextAngle(90.)
        l9.SetTextColor( ROOT.kGray )
        l9.DrawLatex ( .93, .65, time.strftime("%b %d, %Y, %H:%M") )
        base.l9 = l9

    if options["preliminary"]:
        ## preliminary label, ugly plot
        tprel = ROOT.TLatex()
        tprel.SetNDC()
        tprel.SetTextSize(0.055)
        tprel.SetTextFont(42)
        tprel.SetTextColor ( ROOT.kBlue+3 )
        tprel.SetTextAngle(-25.)
        tprel.DrawLatex(.6,.85,"SModelS preliminary")
        #tprel.SetTextAngle(25.)
        #tprel.DrawLatex(.05,.7,"SModelS preliminary")
        base.tprel = tprel

    if not silentMode:
        _ = raw_input("Hit any key to close\n")

    return plane,base
