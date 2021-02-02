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
from plottingFuncs import yIsLog, getFigureUrl

try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass
try:
    from smodels.theory.auxiliaryFunctions import removeUnits
except:
    from backwardCompatibility import removeUnits


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
                      looseness = 1.2, style = "", legendplacement = "top right" ):
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
    :return: TCanvas object containing the plot
    """

    # Check if data has been defined:
    tgr = TGraph2D()
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
        r = float("nan")
        if not "error" in pt.keys():
            r = pt['signal']/pt ['UL']
        if r > 3.:
            r=3.
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

    if tgr.GetN() < 4:
        logger.error("No good points for validation plot.")
        return (None,None)

    #ROOT has trouble obtaining a histogram from a 1-d graph. So it is
    #necessary to smear the points if they rest in a single line.
    if tgr.GetYmax() == tgr.GetYmin():
        logger.info("1d data detected, smearing Y values")
        tgrN = tgr.GetN()
        buff = tgr.GetX()
        buff.SetSize(tgrN)
        xpts = numpy.frombuffer(buff,count=tgrN)
        buff = tgr.GetY()
        buff.SetSize(tgrN)
        ypts = numpy.frombuffer(buff,count=tgrN)
        buff = tgr.GetZ()
        buff.SetSize(tgrN)
        zpts = numpy.frombuffer(buff,count=tgrN)
        for i in range(tgrN):
            tgr.SetPoint(i,xpts[i],ypts[i]+random.uniform(0.,0.001),zpts[i])
    if tgr.GetXmax() == tgr.GetXmin():
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

    expectedOfficialCurves = None
    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurves:
        logger.warning("Official curve for validation plot is not defined.")
        official = None
    else:
        official = validationPlot.officialCurves
        logger.debug("Official curves have length %d" % len (official) )

    # Check if official exclusion curve has been defined:
    if not validationPlot.expectedOfficialCurves:
        logger.info("No expected official curves found.")
        expectedOfficialCurves = None
    else:
        expectedOfficialCurves = validationPlot.expectedOfficialCurves
        logger.debug("Official curves have length %d" % len (official) )

    if logY:
        if official is None:
            logger.error("could not find any exclusion lines for %s" % validationPlot.txName )
            official = []
        for contour in official:
            # x, y = Double(), Double()
            x, y = ctypes.c_double(), ctypes.c_double()
            n = contour.GetN()
            for i in range(n):
                contour.GetPoint(i,x,y)
                # print ( "y",y,rescaleWidth(y) )
                contour.SetPoint(i,x.value,rescaleWidth(y.value) )
        if expectedOfficialCurves is None:
            logger.error("could not find any exclusion lines for %s" % validationPlot.txName )
            expectedOfficialCurves = []
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
    cgraphs = getContours(tgr,contVals)

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
    if official:
        for gr in official:
            # validationPlot.completeGraph ( gr )
            setOptions(gr, Type='official')
            gr.Draw("L SAME")
    if expectedOfficialCurves:
        for gr in expectedOfficialCurves:
            # validationPlot.completeGraph ( gr )
            setOptions(gr, Type='official')
            gr.SetLineColor ( kRed )
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
        else:
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
        leg = TLegend(0.15+dx,0.75-0.040*nleg,0.495+dx,0.83)
    if legendplacement == "top left":
        leg = TLegend(0.15,0.75-0.040*nleg,0.495,0.83)
    setOptions(leg)
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
    if official != None:
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
                leg.AddEntry(gr,"exp. excl. (off.)","L")
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

def createTempPlot( validationPlot, silentMode=True, what = "R", nthpoint =1,
                    signal_factor =1.):
    """
    Uses the data in validationPlot.data and the official exclusion curve
    in validationPlot.officialCurves to generate temperature plots, showing
    e.g. upper limits or R values

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :param what: what is to be plotted ("upperlimits", "crosssections", "R")
    :param nthpoint: label only every nth point
    :param signal_factor: an additional factor that is multiplied with the signal cross section.
     Makes it easier to account for multiplicative factors, like K-factors.
    :return: TCanvas object containing the plot
    """
    kfactor=None

    grTemp = TGraph2D()
    excluded = TGraph()
    if not validationPlot.data:
        logger.warning("Data for validation plot is not defined.")
        return None
    else:
        # Get points:
        for pt in validationPlot.data:
            if kfactor == None:
                kfactor = pt['kfactor']
            if abs(kfactor - pt['kfactor'])> 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()

            if isinstance(pt['axes'],dict):
                if len(pt['axes']) == 1:
                    x, y = pt['axes']['x'], pt['signal']/pt['UL']
                else:
                    x, y = pt['axes']['x'],pt['axes']['y']
            else:
                x,y = pt['axes']
            pt['signal'] = pt['signal']*signal_factor
            if what == 'R':
                z = pt['signal']/pt['UL']
            elif what == 'upperlimits':
                z = pt['UL'].asNumber(pb)
            elif what == 'crosssections':
                z = pt['signal'].asNumber(pb)
            else:
                logger.error("Unknown plotting variable: %s" %what)
                return None
            grTemp.SetPoint(grTemp.GetN(),x,y,z)
            if pt['signal'] > pt['UL']:
                excluded.SetPoint(excluded.GetN(), x, y )

    zlabel = ""
    if what == "R":
        zlabel = "#sigma_{theory}/#sigma_{UL}"
    elif what == "crosssections":
        zlabel="Theory Predictions [pb]"
    elif what == "upperlimits":
        zlabel = "Upper Limits [pb]"

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurves:
        logger.warning("Official curve for validation plot is not defined.")
        official = None
    else:
        official = validationPlot.officialCurves
        if isinstance(official,list): official = official[0]
    #Get envelopes:
    exclenvelop = TGraph(getEnvelope(excluded))
    setOptions(exclenvelop, Type='excluded')

    if silentMode: gROOT.SetBatch()
    setOptions(grTemp, Type='temperature')
    if official:
        setOptions(official, Type='official')

    base = grTemp
    title = validationPlot.expRes.globalInfo.id + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.niceAxes
            # + "_" + validationPlot.axes
    figureUrl = getFigureUrl(validationPlot)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)
    plane.SetRightMargin(0.16)
    plane.SetLeftMargin(0.15)
    plane.SetBottomMargin(0.15)
    set_palette(gStyle)
    h = grTemp.GetHistogram()
    setOptions(h, Type='temperature')
    h.Draw("COLZ")
    h.GetZaxis().SetTitle(zlabel)
    if official:
        official.Draw("SAMEL")
    exclenvelop.Draw("SAMEL")
    base.SetTitle(title)
    if figureUrl:
        figUrl=TLatex()
        figUrl.SetNDC()
        figUrl.SetTextSize(.02)
        """figUrl.DrawLatex(.12,.1,"%s" % figureUrl)"""
        base.figUrl = figUrl
    if abs(signal_factor-1.0)>.0001:
        sigFac=TLatex()
        sigFac.SetNDC()
        sigFac.SetTextSize(.04)
        sigFac.DrawLatex(.15,.62, "signal factor %.1f" % signal_factor )
        base.sigFac = sigFac
    leg = TLegend(0.5,0.5,0.7,0.7,"")
    leg.AddEntry(official,"Official Exclusion","L")
    leg.Draw()

    plane.base = base
    plane.official = official

    if not silentMode:
        ans = raw_input("Hit any key to close\n")
    plane.Print("test.png")

    return plane


def setOptions(obj,Type=None):
    """
    Define global options for the plotting object according to its type.
    :param obj: a plotting object (TGraph, TMultiGraph, TCanvas,...)
    :param type: a string defining the object (allowed, excluded, official,...)
    """

    #Defaul settings:
    if isinstance(obj,TCanvas):
        obj.SetLeftMargin(0.1097891)
        obj.SetRightMargin(0.02700422)
        obj.SetTopMargin(0.02796053)
        obj.SetBottomMargin(0.14796053)
        obj.SetFillColor(0)
        obj.SetBorderSize(0)
        obj.SetFrameBorderMode(0)
    elif isinstance(obj,TGraph):
        obj.GetYaxis().SetTitleFont(132)
        obj.GetYaxis().SetTitleSize(0.075)
        obj.GetYaxis().CenterTitle(True)
        obj.GetYaxis().SetTitleOffset(1.15)
        obj.GetXaxis().SetTitleFont(132)
        obj.GetXaxis().SetTitleSize(0.075)
        obj.GetXaxis().CenterTitle(True)
        obj.GetXaxis().SetTitleOffset(1.2)
        obj.GetYaxis().SetLabelFont(132)
        obj.GetXaxis().SetLabelFont(132)
        obj.GetYaxis().SetLabelSize(0.055)
        obj.GetXaxis().SetLabelSize(0.06)
    elif isinstance(obj,TLegend):
        obj.SetBorderSize(1)
        obj.SetMargin(0.35)
        obj.SetTextFont(132)
        obj.SetTextSize(0.05)
        obj.SetLineColor(kBlack)
        obj.SetLineStyle(1)
        obj.SetLineWidth(1)
        obj.SetFillColorAlpha(kWhite,.7)
        obj.SetFillStyle(1001)
    elif isinstance(obj,TGraph2D) or isinstance(obj,TH2D):
        obj.GetZaxis().SetTitleFont(132)
        obj.GetZaxis().SetTitleSize(0.06)
        obj.GetZaxis().CenterTitle(True)
        obj.GetZaxis().SetTitleOffset(0.7)
        obj.GetZaxis().SetLabelFont(132)
        obj.GetZaxis().SetLabelSize(0.05)
        obj.GetYaxis().SetTitleFont(132)
        obj.GetYaxis().SetTitleSize(0.075)
        obj.GetYaxis().CenterTitle(True)
        obj.GetYaxis().SetTitleOffset(1.15)
        obj.GetXaxis().SetTitleFont(132)
        obj.GetXaxis().SetTitleSize(0.075)
        obj.GetXaxis().CenterTitle(True)
        obj.GetXaxis().SetTitleOffset(1.2)
        obj.GetYaxis().SetLabelFont(132)
        obj.GetXaxis().SetLabelFont(132)
        obj.GetYaxis().SetLabelSize(0.055)
        obj.GetXaxis().SetLabelSize(0.06)

#Type-specific settings:
    if not Type: return True
    elif Type == 'allowed':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(kGreen)
    elif Type == 'gridpoints':
        obj.SetMarkerStyle(28)
        markersize=.1 ## super small for > 155555
        ngpoints = obj.GetN()
        if ngpoints < 1500:
            markersize = .15
        if ngpoints < 1000:
            markersize = .25
        if ngpoints < 500:
            markersize = .45
        if ngpoints < 150:
            markersize = .7
        if ngpoints < 50:
            markersize = .9
        obj.SetMarkerSize(markersize)
        obj.SetMarkerColorAlpha(kBlue,.5)
    elif Type == 'noresult':
        obj.SetMarkerStyle(20)
        obj.SetMarkerSize(.5)
        obj.SetMarkerColor(kGray)
    elif Type == 'cond_violated':
        obj.SetMarkerStyle(23)
        obj.SetMarkerColor(kGreen)
    elif Type == 'excluded':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(kRed)
#        obj.SetFillColorAlpha(kRed,0.15)
        obj.SetLineColor(kRed)
        obj.SetLineWidth(4)
        obj.SetLineStyle(2)
    elif Type == 'allowed_border':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(kGreen+3)
    elif Type == 'excluded_border':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(kOrange+1)
    elif Type == 'official':
        obj.SetLineWidth(3)
        obj.SetLineColor(kBlack)
    elif Type == 'smodels':
        obj.SetLineWidth(4)
        obj.SetLineColor(kRed)
    elif Type == 'temperature':
        obj.SetMarkerStyle(20)
        obj.SetMarkerSize(1.5)
        obj.SetTitle("")
    elif Type == 'pretty':
        obj.GetXaxis().SetTitleFont(12)
        obj.GetXaxis().SetTitleOffset(0.7)
        obj.GetYaxis().SetTitleFont(12)
        obj.GetYaxis().SetTitleOffset(0.8)
        obj.GetZaxis().CenterTitle()
        obj.GetZaxis().SetTitleOffset(1.05)
        obj.GetXaxis().SetLabelSize(0.045)
        obj.GetYaxis().SetLabelSize(0.045)
        obj.GetZaxis().SetLabelSize(0.04)
        obj.GetXaxis().SetTitleSize(0.06)
        obj.GetYaxis().SetTitleSize(0.06)
        obj.GetZaxis().SetTitleSize(0.051)


def getContours(tgr,contVals):
    """
    Returns a list of TGraphs containing the curves corresponding to the
    contour values contVals from the input TGraph2D object
    :param tgr: ROOT TGraph2D object containing the x,y,r points
    :param contVals: r-values for the contour graphs

    :return: a dictionary, where the keys are the contour values
             and the values are a list of TGraph objects containing the curves
             for the respective contour value (e.g. {1. : [TGraph1,TGraph2],...})
    """

    if tgr.GetN() == 0:
        logger.info("No excluded points found for %s" %tgr.GetName())
        return None

    cVals = sorted(contVals)
    if tgr.GetN() < 4:
        print ( "Error: Cannot create a contour with fewer than 3 input vertices" )
        return None
    h = tgr.GetHistogram()
    #Get contour graphs:
    c1 = TCanvas()
    h.SetContour(3,array('d',cVals))
    h.Draw("CONT Z LIST")
    c1.Update()
    clist = gROOT.GetListOfSpecials().FindObject("contours")
    cgraphs = {}
    for i in range(clist.GetSize()):
        contLevel = clist.At(i)
        curv = contLevel.First()
        cgraphs[cVals[i]] = []
        for j in range(contLevel.GetSize()):
            cgraphs[cVals[i]].append(curv)
            curv = contLevel.After(curv)

    return cgraphs

def getEnvelope(excludedGraph):
    """
    Tries to return the envelope curve of the points in the
    excluded graph (ROOT TGraph).
    :param excludedGraph: ROOT TGraph object containing the excluded points.
    :return: a TGraph object containing the envelope curve
    """
    if excludedGraph.GetN() == 0:
        logger.info("No excluded points found for %s" %excludedGraph.GetName())
        return excludedGraph

    envelop = TGraph()
    envelop.SetName("envelope")
    curve = TGraph(excludedGraph)
    curve.Sort()
    # x1, y1 = Double(), Double()
    x1, y1 = ctypes.c_double(), ctypes.c_double()
    curve.GetPoint(0, x1, y1)
    yline = []
    for ipt in range(curve.GetN() + 1):
        # x, y = Double(), Double()
        x, y = ctypes.c_double(), ctypes.c_double()
        dmin = 0.
        if ipt < curve.GetN(): curve.GetPoint(ipt, x, y)
        if ipt != curve.GetN() and x == x1: yline.append(y)
        else:
            yline = sorted(yline, reverse = True)
            dy = [abs(yline[i] - yline[i + 1]) for i in range(len(yline) - 1)]
            if len(yline) <= 3 or envelop.GetN() == 0:
                newy = max(yline)
                if len(dy) > 2: dmin = min([abs(yline[i] - yline[i + 1]) for i in range(len(yline) - 1)])
            else:
                newy = max(yline)
        #        dmin = min(dy)
                dmin = sum(dy) / float(len(dy))
                for iD in range(len(dy) - 1):
                    if dy[iD] <= dmin and dy[iD + 1] <= dmin:
                        newy = yline[iD]
                        break
            envelop.SetPoint(envelop.GetN(), x1, newy + dmin/2.)
            x1 = x
            yline = [y]

    # x2, y2 = Double(), Double()
    x2, y2 = ctypes.c_double(), ctypes.c_double()
    envelop.GetPoint(envelop.GetN() - 1, x2, y2)
    envelop.SetPoint(envelop.GetN(), x2, 0.)  #Close exclusion curve at zero
    return envelop

def set_palette(gStyle, ncontours=999):
    """Set a color palette from a given RGB list
    stops, red, green and blue should all be lists of the same length
    see set_decent_colors for an example"""

    # default palette, looks cool
    stops = [0.00, 0.34, 0.61, 0.84, 1.00]
    red   = [0.00, 0.00, 0.87, 1.00, 0.51]
    green = [0.00, 0.81, 1.00, 0.20, 0.00]
    blue  = [0.51, 1.00, 0.12, 0.00, 0.00]

    s = array('d', stops)
    r = array('d', red)
    g = array('d', green)
    b = array('d', blue)

    npoints = len(s)
    TColor.CreateGradientColorTable(npoints, s, r, g, b, ncontours)
    gStyle.SetNumberContours(ncontours)
