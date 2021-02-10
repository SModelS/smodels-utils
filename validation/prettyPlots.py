#!/usr/bin/env python3

"""
.. module:: plottingFuncs
   :synopsis: Main methods for dealing with the plotting of a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,numpy,random,copy
sys.path.append('../')
from array import array
import math, ctypes
logger = logging.getLogger(__name__)
from ROOT import (TFile,TGraph,TGraph2D,gROOT,TMultiGraph,TCanvas,TLatex,
                  TLegend,kGreen,kRed,kOrange,kBlack,kGray,TPad,kWhite,gPad,
                  TPolyLine3D,TColor,gStyle,TH2D,TImage,kBlue,kOrange )
from smodels.tools.physicsUnits import fb, GeV, pb
#from smodels.theory.auxiliaryFunctions import coordinateToWidth,withToCoordinate
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxes
from plottingFuncs import yIsLog, getFigureUrl, getContours, setOptions

try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass

#Set nice ROOT color palette for temperature plots:
stops = [0.00, 0.34, 0.61, 0.84, 1.00]
red   = [0.00, 0.00, 0.87, 1.00, 0.51]
green = [0.00, 0.81, 1.00, 0.20, 0.00]
blue  = [0.51, 1.00, 0.12, 0.00, 0.00]
s = array('d', stops)
r = array('d', red)
g = array('d', green)
b = array('d', blue)
TColor.CreateGradientColorTable(len(s), s, r, g, b, 999)
gStyle.SetNumberContours(999)

def createPrettyPlot( validationPlot,silentMode=True, preliminary=False,
                      looseness = 1.2, style = "", legendplacement = "top right",
                      drawExpected = True ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate a pretty exclusion plot

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :param preliminary: if true, write "preliminary" over the plot
    :param looseness: ?
    :param style: allow for styles, currently "", and "sabine"
    :param legendplacement: placement of legend. One of:
                      "automatic", "top right", "top left"
    :param drawExpected: if true, then draw also lines for expected limits
    :return: TCanvas object containing the plot
    """

    # Check if data has been defined:
    tgr, etgr = TGraph2D(), TGraph2D()
    kfactor=None
    xlabel, ylabel, zlabel = 'x [GeV]','y [GeV]',"r = #sigma_{signal}/#sigma_{UL}"
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
            logger.warning( "no UL for %s" % xvals )
        r, rexp = float("nan"), float("nan")
        if not "error" in pt.keys():
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
                ylabel = "r = #sigma_{signal}/#sigma_{UL}"
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
                tgr.SetPoint(tgr.GetN(), x, y, r)
                etgr.SetPoint(etgr.GetN(), x, y, rexp )
    if drawExpected in [ "auto" ]:
        drawExpected = hasExpected
    if tgr.GetN() < 4:
        logger.error("No good points for validation plot.")
        return (None,None)

    #ROOT has trouble obtaining a histogram from a 1-d graph. So it is
    #necessary to smear the points if they rest in a single line.
    if tgr.GetYmax() == tgr.GetYmin():
        logger.info("1d data detected, not plotting pretty plot.")
        return None, None
        logger.info("1d data detected, smearing Y values")
        tgrN = tgr.GetN()
        buff = tgr.GetX()
        #buff.SetSize(tgrN)
        xpts = numpy.frombuffer(buff,count=tgrN)
        buff = tgr.GetY()
        #buff.SetSize(tgrN)
        ypts = numpy.frombuffer(buff,count=tgrN)
        buff = tgr.GetZ()
        #buff.SetSize(tgrN)
        zpts = numpy.frombuffer(buff,count=tgrN)
        for i in range(tgrN):
            tgr.SetPoint(i,xpts[i],ypts[i]+random.uniform(0.,0.001),zpts[i])
    if tgr.GetXmax() == tgr.GetXmin():
        logger.info("1d data detected, not plotting pretty plot.")
        return None, None
        logger.info("1d data detected, smearing X values")
        buff = tgr.GetX()
        buff.reshape((tgr.GetN(),))
        #buff.SetSize(sys.maxsize)
        #print ( "count", tgr.GetN(), type(buff), buff.shape )
        xpts = numpy.frombuffer(buff,count=tgr.GetN())
        buff = tgr.GetY()
        buff.reshape((tgr.GetN(),))
        #buff.SetSize(sys.maxsize)
        ypts = numpy.frombuffer(buff,count=tgr.GetN())
        buff = tgr.GetZ()
        buff.reshape((tgr.GetN(),))
        #buff.SetSize(sys.maxsize)
        zpts = numpy.frombuffer(buff,count=tgr.GetN())
        for i in range(tgr.GetN()):
            tgr.SetPoint(i,xpts[i]+random.uniform(0.,0.001),ypts[i],zpts[i])
    if etgr.GetYmax() == etgr.GetYmin():
        logger.info("1d data detected, smearing Y values")
        etgrN = etgr.GetN()
        buff = etgr.GetX()
        #buff.SetSize(etgrN)
        xpts = numpy.frombuffer(buff,count=etgrN)
        buff = etgr.GetY()
        #buff.SetSize(etgrN)
        ypts = numpy.frombuffer(buff,count=etgrN)
        buff = etgr.GetZ()
        #buff.SetSize(etgrN)
        zpts = numpy.frombuffer(buff,count=etgrN)
        for i in range(etgrN):
            etgr.SetPoint(i,xpts[i],ypts[i]+random.uniform(0.,0.001),zpts[i])
    if etgr.GetXmax() == etgr.GetXmin():
        logger.info("1d data detected, smearing X values")
        buff = etgr.GetX()
        buff.reshape((etgr.GetN(),))
        #buff.SetSize(sys.maxsize)
        #print ( "count", etgr.GetN(), type(buff), buff.shape )
        xpts = numpy.frombuffer(buff,count=etgr.GetN())
        buff = etgr.GetY()
        buff.reshape((etgr.GetN(),))
        #buff.SetSize(sys.maxsize)
        ypts = numpy.frombuffer(buff,count=etgr.GetN())
        buff = etgr.GetZ()
        buff.reshape((etgr.GetN(),))
        #buff.SetSize(sys.maxsize)
        zpts = numpy.frombuffer(buff,count=etgr.GetN())
        for i in range(etgr.GetN()):
            etgr.SetPoint(i,xpts[i]+random.uniform(0.,0.001),ypts[i],zpts[i])

    official = validationPlot.officialCurves
    # Check if official exclusion curve has been defined:
    if official == []:
        logger.warning("Official curve for validation plot is not defined.")
    else:
        logger.debug("Official curves have length %d" % len (official) )

    expectedOfficialCurves = validationPlot.expectedOfficialCurves
    # Check if official exclusion curve has been defined:
    if expectedOfficialCurves == []:
        logger.info("No expected official curves found.")

    if logY:
        for contour in official:
            # x, y = Double(), Double()
            x, y = ctypes.c_double(), ctypes.c_double()
            n = contour.GetN()
            for i in range(n):
                contour.GetPoint(i,x,y)
                # print ( "y",y,rescaleWidth(y) )
                contour.SetPoint(i,x.value,rescaleWidth(y.value) )
        for contour in expectedOfficialCurves:
            # x, y = Double(), Double()
            x, y = ctypes.c_double(), ctypes.c_double()
            n = contour.GetN()
            for i in range(n):
                contour.GetPoint(i,x,y)
                # print ( "y",y,rescaleWidth(y) )
                contour.SetPoint(i,x.value,rescaleWidth(y.value) )

    if silentMode: gROOT.SetBatch()
    setOptions(tgr, Type='allowed')
    setOptions(etgr, Type='allowed')
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
    title = title + "  #scale[0.8]{("+resultType+")}"
    tgr.SetTitle(title)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)
    plane.SetRightMargin(0.16)
    plane.SetTopMargin(0.16)
    plane.SetBottomMargin(0.16)
    plane.SetLeftMargin(0.12)
    gStyle.SetTitleSize(0.045,"t")
    gStyle.SetTitleY(1.005)

    #Get contour graphs:
    contVals = [1./looseness,1.,looseness]
    if drawExpected:
        contVals = [1.,1.,1.]
    cgraphs = getContours(tgr,contVals)
    ecgraphs = {}
    if drawExpected:
        ecgraphs = getContours(etgr,contVals)

    #Draw temp plot:
    h = tgr.GetHistogram()
    setOptions(h,Type='pretty')
    h.GetZaxis().SetRangeUser(0., min(tgr.GetZmax(),3.))
    h.GetXaxis().SetTitleFont(42)
    xa,ya = h.GetXaxis(),h.GetYaxis()
    ya.SetTitleFont(42)
    xa.SetTitleOffset(1.)
    ya.SetTitleOffset(1.2)
    xa.SetTitleSize(.04)
    ya.SetTitleSize(.04)
    xa.SetTitle(xlabel)
    ya.SetTitle(ylabel)
    h.GetZaxis().SetTitle(zlabel)
    h.SetContour(200)
    h.Draw("COLZ")
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
    palette = h.GetListOfFunctions().FindObject("palette")
    palette.SetX1NDC(0.845)
    palette.SetX2NDC(0.895)
    palette.SetY1NDC(0.16)
    palette.SetY2NDC(0.84)
    for cval,grlist in cgraphs.items():
        if cval == 1.0:
            ls = 1
        else:
            ls = 2
        for gr in grlist:
            setOptions(gr, Type='official')
            gr.SetLineColor(kGray+2)
            gr.SetLineStyle(ls)
            gr.Draw("L SAME")
    for cval,grlist in ecgraphs.items():
        if cval == 1.0:
            ls = 2
        else:
            continue
        for gr in grlist:
            setOptions(gr, Type='official')
            gr.SetLineColor(kRed)
            gr.SetLineStyle(ls)
            gr.Draw("L SAME")
    for gr in official:
        # validationPlot.completeGraph ( gr )
        setOptions(gr, Type='official')
        gr.Draw("L SAME")
    for gr in expectedOfficialCurves:
        # validationPlot.completeGraph ( gr )
        setOptions(gr, Type='official')
        gr.SetLineColor ( kOrange+2 )
        gr.Draw("L SAME")

    #Draw additional info
    ltx=TLatex()
    ltx.SetNDC()
    ltx.SetTextSize(.035)
    ltx.SetTextFont(42)
    ltx2 = ltx.Clone()
    ltx2.SetTextAlign(31)
    txStr = validationPlot.txName +': '+prettyTxname(validationPlot.txName,outputtype="root")
    axStr = prettyAxes(validationPlot.txName,validationPlot.axes)
    axStr = str(axStr).replace(']','').replace('[','').replace("'","")
    infoStr = "#splitline{"+txStr+'}{'+axStr+'}'
    ltx.DrawLatex(.03,.88,txStr)
    ltx2.DrawLatex(.96,.88,axStr)
    tgr.ltx = ltx
    figureUrl = getFigureUrl(validationPlot)
    if figureUrl:
        l1=TLatex()
        l1.SetNDC()
        l1.SetTextSize(.025)
        """l1.DrawLatex(.01,0.023,"#splitline{official plot:}{%s}" % figureUrl)"""
        tgr.l1=l1
    if kfactor is not None and abs ( kfactor - 1.) > .01:
        l2=TLatex()
        l2.SetNDC()
        l2.SetTextFont(132)
        l2.SetTextSize(.04)
        l2.DrawLatex(0.16,0.2,"k-factor = %.2f" % kfactor)
        tgr.l2=l2

    subtitle = "%d datasets" % len(validationPlot.expRes.datasets)
    if hasattr ( validationPlot.expRes.globalInfo, "jsonFiles" ):
        ## pyhf combination
        subtitle = "pyhf combining %d SRs" % len(validationPlot.expRes.datasets)
    dId = validationPlot.expRes.datasets[0].dataInfo.dataId
    if type(dId) == str and dId.startswith("ar"):
        subtitle = "%d aggregate datasets" % len(validationPlot.expRes.datasets)
        dataId = str(dataset.dataInfo.dataId)
    if len(validationPlot.expRes.datasets) == 1 and \
            type(validationPlot.expRes.datasets[0].dataInfo.dataId)==type(None):
        subtitle = "" ## no extra info, so leave it blank
        # subtitle = "upper limit"
    if validationPlot.combine == False and len(validationPlot.expRes.datasets) > 1:
        for ctr,x in enumerate(validationPlot.data):
            if "error" in x.keys():
                continue
            break
        if validationPlot.data != None and validationPlot.data[ctr] != None and "dataset" in validationPlot.data[ctr].keys() and validationPlot.data[ctr]["dataset"]!=None and "combined" in validationPlot.data[ctr]["dataset"]:
            logger.warning ( "asked for an efficiencyMap-type plot, but the cached validationData is for a combined plot. Will label it as 'combined'." )
        else:
            subtitle = "best SR"
    lsub=TLatex()
    lsub.SetNDC()
    if style == "sabine":
        lsub.SetTextSize(.037)
        if legendplacement == "top left": # then we move to top right with this
            lsub.DrawLatex(.57,.79,subtitle)
        elif legendplacement == "top right": # then we move to top right with this
            lsub.DrawLatex(.15,.79,subtitle)
        else:
            # lsub.DrawLatex(.57,.79,subtitle)
            lsub.DrawLatex(.15,.79,subtitle)
    else:
        lsub.SetTextAlign(31)
        # lsub.SetTextSize(.025)
        lsub.SetTextSize(.035)
        # lsub.DrawLatex(.81,.068,subtitle)
        lsub.DrawLatex(.91,.068,subtitle)
    tgr.lsub=lsub

    nleg = 1
    if cgraphs != None and official != None:
    #Count the number of entries in legend:
        nleg = min(2,len(cgraphs)-list(cgraphs.values()).count([])) + min(2,len(official))
    #Draw legend:
    dx = 0. ## top, left
    dx = .33 ## top, right
    hasExclLines = False
    # placement = "top left" ## "automatic", "top right", "top left"
    possibleplacements = [ "automatic", "auto", "top left", "top right" ]
    legendplacement = legendplacement.replace("'","")
    legendplacement = legendplacement.replace('"',"")
    legendplacement = legendplacement.lower()
    legendplacement = legendplacement.strip()
    if legendplacement not in possibleplacements:
        print ( "[plottingFuncs] ERROR placement %s not in %s" % \
                ( legendplacement, ", ".join( possibleplacements ) ) )
        sys.exit(-1)
    leg = TLegend() ## automatic placement
    if legendplacement == "top right":
        leg = TLegend(0.23+dx,0.75-0.040*nleg,0.495+dx,0.83)
    elif legendplacement == "top left":
        leg = TLegend(0.15,0.75-0.040*nleg,0.415,0.83)
    else:
        leg = TLegend(0.15,0.75-0.040*nleg,0.415,0.83)
    setOptions(leg)
    leg.SetMargin(.13)
    # leg.SetFillStyle(0)
    leg.SetTextSize(0.04)
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
    if drawExpected:
        for cval,grlist in ecgraphs.items():
            if not grlist:
                continue
            if cval == 1.0:
                leg.AddEntry(grlist[0],"exp. excl (SModelS)","L")
                hasExclLines = True
            elif (cval == looseness or cval == 1./looseness) and not added:
                leg.AddEntry(grlist[0],"#pm20% (SModelS)","L")
                hasExclLines = True
                added = True
    added = False
    for gr in official:
        if 'xclusion_' in gr.GetTitle():
            leg.AddEntry(gr,"exclusion (official)","L")
            hasExclLines = True
        elif ('xclusionP1_' in gr.GetTitle() or 'xclusionM1_' in gr.GetTitle()) and (not added):
            leg.AddEntry(gr,"#pm1#sigma (official)","L")
            hasExclLines = True
            added = True
    for gr in expectedOfficialCurves:
        if 'xclusion_' in gr.GetTitle():
            leg.AddEntry(gr,"exp. excl. (official)","L")
            hasExclLines = True
        elif ('xclusionP1_' in gr.GetTitle() or 'xclusionM1_' in gr.GetTitle()) and (not added):
            leg.AddEntry(gr,"#pm1#sigma (official)","L")
            hasExclLines = True
            added = True

    if hasExclLines:
        leg.Draw()
    tgr.leg = leg
    if preliminary:
        ## preliminary label, pretty plot
        tprel = TLatex()
        tprel.SetTextColor ( kBlue+3 )
        tprel.SetNDC()
        tprel.SetTextAngle(25.)
        tprel.SetTextSize(0.055)
        tprel.SetTextFont(42)
        tprel.DrawLatex(.1,.7,"SModelS preliminary")
        tgr.tprel = tprel
    plane.Update()

    if not silentMode:
        ans = raw_input("Hit any key to close\n")

    return plane,tgr
