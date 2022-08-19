#!/usr/bin/env python3

"""
.. module:: rootPlottingFuncs
   :synopsis: Some helpers for the root backend

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys
logger = logging.getLogger(__name__)

from smodels_utils.helper.rootTools import setROOTColorPalette
setROOTColorPalette()

def setAxes ( h, style ):
    """ set the axes ranges if anything is specified in 'style' """
    style = style.strip()
    if style.startswith ('"') or style.startswith ("'"):
        logger.error ( "'style' field begins with quotation mark, but strings are without quotation marks in ini files" )
    try:
        styles = style.split(";")
        for s in styles:
            s = s.strip()
            if s.startswith("xaxis"):
                tmp = s.replace("xaxis","")
                ar = eval(tmp)
                h.GetXaxis().SetRangeUser ( ar[0], ar[1] )
            if s.startswith("yaxis"):
                tmp = s.replace("yaxis","")
                ar = eval(tmp)
                h.GetYaxis().SetRangeUser ( ar[0], ar[1] )
    except Exception as e:
        logger.error ( f"when trying to redefine axes: {e}" )

def clean ( obj ):
    """ check for some issues with the exclusion line
    :param obj: the ROOT.TGraph
    """
    ret = obj.ReadObj()
    n = ret.GetN()
    # x, y = Double(), Double()
    x, y = ctypes.c_double(), ctypes.c_double()
    warnedX, warnedY = False, False
    for i in range(n):
        ret.GetPoint(i,x,y)
        if x.value < 0.:
            if not warnedY:
                print ( "[plottingFuncs] ERROR: x value %s of %s smaller than zero! Will set to zero and suppress future warnings." % ( x.value, obj.GetName() ) )
                warnedX = True
            ret.SetPoint ( i, 0., y.value )
        if y.value < 0.:
            if not warnedY:
                print ( "[plottingFuncs] ERROR: y value %s of %s smaller than zero! Will set to zero and suppress future warnings." % ( y.value, obj.GetName() ) )
                warnedY = True
            ret.SetPoint ( i, x.value, 0. )
    return ret

def getExclusionCurvesForFromSmsRoot( expResult, txname=None, axes=None,
        get_all=False, expected=False ):
    """
    Reads sms.root and returns the TGraph objects for the exclusion
    curves. If txname is defined, returns only the curves corresponding
    to the respective txname. If axes is defined, only returns the curves

    :param expResult: an ExpResult object
    :param txname: the TxName in string format (i.e. T1tttt)
    :param axes: the axes definition in string format
                 (e.g. [x, y, 60.0], [x, y, 60.0]])
    :param get_all: Get also the +-1 sigma curves?
    :param expected: if true, get expected, not observed

    :return: a dictionary, where the keys are the TxName strings
            and the values are the respective list of TGraph objects.
    """
    import ROOT

    if type(expResult)==list:
        expResult=expResult[0]
    rootpath = os.path.join(expResult.path,'sms.root')
    if not os.path.isfile(rootpath):
        logger.error("Root file %s not found" %rootpath)
        return False

    rootFile = ROOT.TFile(rootpath)
    txnames = {}
    #Get list of TxNames (directories in root file)
    for obj in rootFile.GetListOfKeys():
        objName = obj.ReadObj().GetName()
        if txname and txname != objName: continue
        txnames[objName] = obj.ReadObj()
    if not txnames:
        logger.warning("Exclusion curve for %s not found in %s" %(txname,rootpath))
        return False

    #For each Txname/Directory get list of exclusion curves
    nplots = 0
    for tx,txDir in txnames.items():
        txnames[tx] = []
        for obj in txDir.GetListOfKeys():
            objName = obj.ReadObj().GetName()
            if not 'exclusion' in objName.lower(): continue
            if (not get_all) and (not 'exclusion_' in objName.lower()): continue
            if expected:
                if not 'expexclusion' in objName.lower():
                    continue
            else:
                if 'expexclusion' in objName.lower():
                    continue
            # print "[plottingFuncs.py] name=",objName
            if axes and not axes in objName: continue
            T = clean ( obj )
            txnames[tx].append( T )
            # txnames[tx].append(obj.ReadObj())
            nplots += 1
    if not nplots:
        if expected: # for expected it's only an info
            logger.info( f"No expected exclusion curve found for {expResult.globalInfo.id}:{txname}:{axes}.")
        else: # for observed it's a warning
            logger.warning( f"No observed exclusion curve found for {expResult.globalInfo.id}:{txname}:{axes}.")
        return False

    return txnames

def createSpecialPlot(validationPlot,silentMode=True,looseness=1.2,
        what = "bestregion", nthpoint =1, signal_factor = 1. ):
    """
    Uses the data in validationPlot.data and the official exclusion curve
    in validationPlot.officialCurves to generate "special" plots, showing
    e.g. upper limits or best signal region

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :param what: what is to be plotted("bestregion", "upperlimits", "crosssections")
    :param nthpoint: label only every nth point
    :param signal_factor: an additional factor that is multiplied with the signal cross section,
    when comparing with the upper limit. Makes it easier to account for multiplicative factors,
    like the number of squark flavors in production
    :return: TCanvas object containing the plot
    """
    kfactor=None

    excluded, allowed = TGraph(), TGraph()
    excluded_border, allowed_border = TGraph(), TGraph()
    cond_violated=TGraph()
    if not validationPlot.data:
        logger.warning("Data for validation plot is not defined.")
    else:
        # Get excluded and allowed points:
        for pt in validationPlot.data:
            if kfactor == None:
                kfactor = pt ['kfactor']
            if abs(kfactor - pt['kfactor'])> 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()
            if isinstance(pt['axes'],dict):
                if len(pt['axes']) == 1:
                    x, y = pt['axes']['x'],pt['signal']/pt['UL']
                else:
                    x, y = pt['axes']['x'],pt['axes']['y']
            else:
                x,y = pt['axes']
            if pt['condition'] and max(pt['condition'].values())> 0.05:
                logger.warning("Condition violated for file " + pt['slhafile'])
                cond_violated.SetPoint(cond_violated.GetN(), x, y)
            elif signal_factor * pt['signal'] > pt['UL']:
                if signal_factor * pt['signal'] < pt ['UL']* looseness:
                    excluded_border.SetPoint(excluded_border.GetN(), x, y)
                else:
                    excluded.SetPoint(excluded.GetN(), x, y )
            else:
                if signal_factor * pt['signal']*looseness > pt['UL']:
                    allowed_border.SetPoint(allowed_border.GetN(), x, y)
                else:
                    allowed.SetPoint(allowed.GetN(), x, y)

    labels=[]

    # print "validationPlot.officialCurves=",validationPlot.officialCurves

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurves:
        logger.warning("Official curve for validation plot is not defined.")
        official = None
    else:
        official = validationPlot.officialCurves
        if isinstance(official,list): official = official[0]

    if silentMode: gROOT.SetBatch()
    setOptions(allowed, Type='allowed')
    setOptions(cond_violated, Type='cond_violated')
    setOptions(allowed_border, Type='allowed_border')
    setOptions(excluded, Type='excluded')
    setOptions(excluded_border, Type='excluded_border')
    if official:
        setOptions(official, Type='official')
    base = TMultiGraph()
    if allowed.GetN()>0: base.Add(allowed, "P")
    if excluded.GetN()>0: base.Add(excluded, "P")
    if allowed_border.GetN()>0: base.Add(allowed_border, "P")
    if excluded_border.GetN()>0: base.Add(excluded_border, "P")
    if cond_violated.GetN()>0: base.Add(cond_violated, "P")
    if official:
        baseiAdd(official, "L")
    title = what+"_"+validationPlot.expRes.globalInfo.id + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.niceAxes
            # + "_" + validationPlot.axes
    figureUrl = getFigureUrl(validationPlot)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)
    base.Draw("AP")
    base.SetTitle(title)
    l=TLatex()
    l.SetNDC()
    l.SetTextSize(.04)
    base.l=l
    if figureUrl:
        l1=TLatex()
        l1.SetNDC()
        l1.SetTextSize(.02)
        l1.DrawLatex(.12,.1,"%s" % figureUrl)
        base.l1=l1

    if not validationPlot.data:
        logger.warning("Data for validation plot is not defined.")
    else:
        # Get excluded and allowed points:
        for ctr,pt in enumerate(validationPlot.data):
            if ctr%nthpoint != 0:
                continue
            if kfactor == None:
                kfactor = pt ['kfactor']
            if abs(kfactor - pt['kfactor'])> 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()
            if isinstance(pt['axes'],dict):
                if len(pt['axes']) == 1:
                    x, y = pt['axes']['x'],pt['signal']/pt['UL']
                else:
                    x, y = pt['axes']['x'],pt['axes']['y']
            else:
                x,y = pt['axes']
            import ROOT
            lk=ROOT.TLatex ()
            lk.SetTextSize(.01)
            if what in [ "bestregion", "bestcut" ]:
                bestregion=pt["dataset"].replace("ANA","").replace("CUT","")
                lk.DrawLatex(x, y, bestregion )
            elif what == "upperlimits":
                ul=pt["UL"].asNumber(pb)
                lk.DrawLatex(x, y, str(ul) )
            elif what == "crosssections":
                signalxsec=pt['signal'].asNumber(pb)
                lk.DrawLatex(x, y, str(signalxsec) )
            elif what == "efficiencies":
                eff = pt['efficiency']
                if isinstance(eff,float):
                    eff = format(eff,'1.0e')
                else:
                    eff = str(eff)
                lk.DrawLatex(x, y, eff)
            else:
                logger.error( "dont know how to draw %s" % what )
                sys.exit()
            labels.append(lk )

        #Add original grid data to UL plot:
        if what == "upperlimits": ## FIXME this doesnt work anymore
            olk=ROOT.TLatex ()
            olk.SetTextSize(.02)
            massPlane = MassPlane.fromString(validationPlot.axes)
            txnameObjs = validationPlot.expRes.getTxnameWith({'txName': validationPlot.txName})
            for txnameObj in txnameObjs:
                txnameData = txnameObj.txnameData.data
                if txnameData==None:
                        continue
                for (itr, (mass,ul)) in enumerate(txnameData ):
                    if itr% nthpoint != 0: continue
                    mass_unitless = [[(m/GeV).asNumber() for m in mm] for mm in mass]
                    varsDict = massPlane.getXYValues(mass_unitless)
                    if not varsDict:
                        continue
                    x ,y = varsDict['x'],varsDict['y']
                    ul = ul.asNumber(pb)
                    lk.DrawLatex(x, y, "#color[4]{%.2f}" % ul )

    l2=TLatex()
    l2.SetNDC()
    l2.SetTextSize(.04)
    l2.DrawLatex(.15,.78,"k-factor %.2f" % kfactor)
    base.l2=l2
    l3=TLatex()
    l3.SetNDC()
    l3.SetTextSize(.04)
    if what == "upperlimits":
        drawingwhat="upper limits [pb]"
    if what == "crosssections":
        drawingwhat="theory predictions [pb]"
    if what in [ "bestregion", "bestcut" ]:
        drawingwhat="best signal region"
    else:
        drawingwhat = what
    l3.DrawLatex(.15,.7, drawingwhat )
    base.l3=l3
    if abs(signal_factor-1.0)>.0001:
        l4=TLatex()
        l4.SetNDC()
        l4.SetTextSize(.04)
        l4.DrawLatex(.15,.62, "signal factor %.1f" % signal_factor )
        base.l4=l4

    plane.base = base

    if not silentMode:
        _ = raw_input("Hit any key to close\n")

    plane.labels=labels

    return plane

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

    import ROOT
    grTemp = ROOT.TGraph2D()
    excluded = ROOT.TGraph()
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
    import ROOT

    #Defaul settings:
    if isinstance(obj,ROOT.TCanvas):
        obj.SetLeftMargin(0.1097891)
        obj.SetRightMargin(0.02700422)
        obj.SetTopMargin(0.02796053)
        obj.SetBottomMargin(0.14796053)
        obj.SetFillColor(0)
        obj.SetBorderSize(0)
        obj.SetFrameBorderMode(0)
    elif isinstance(obj,ROOT.TGraph):
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
    elif isinstance(obj,ROOT.TLegend):
        obj.SetBorderSize(1)
        obj.SetMargin(0.35)
        obj.SetTextFont(132)
        obj.SetTextSize(0.05)
        obj.SetLineColor(ROOT.kBlack)
        obj.SetLineStyle(1)
        obj.SetLineWidth(1)
        obj.SetFillColorAlpha(ROOT.kWhite,.7)
        obj.SetFillStyle(1001)
    elif isinstance(obj,ROOT.TGraph2D) or isinstance(obj,ROOT.TH2D):
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
        obj.SetMarkerColor(ROOT.kGreen)
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
        obj.SetMarkerColorAlpha(ROOT.kBlue,.5)
    elif Type == 'noresult':
        obj.SetMarkerStyle(20)
        obj.SetMarkerSize(.5)
        obj.SetMarkerColor(ROOT.kGray)
    elif Type == 'cond_violated':
        obj.SetMarkerStyle(23)
        obj.SetMarkerColor(ROOT.kGreen)
    elif Type == 'excluded':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(ROOT.kRed)
#        obj.SetFillColorAlpha(kRed,0.15)
        obj.SetLineColor(ROOT.kRed)
        obj.SetLineWidth(4)
        obj.SetLineStyle(2)
    elif Type == 'allowed_border':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(ROOT.kGreen+3)
    elif Type == 'excluded_border':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(ROOT.kOrange+1)
    elif Type == 'official':
        obj.SetLineWidth(3)
        obj.SetLineColor(ROOT.kBlack)
    elif Type == 'smodels':
        obj.SetLineWidth(4)
        obj.SetLineColor(ROOT.kRed)
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


def getContours(tgraph,contVals, name ):
    """
    Returns a list of TGraphs containing the curves corresponding to the
    contour values contVals from the input TGraph2D object
    :param tgraph: ROOT TGraph2D object containing the x,y,r points
    :param contVals: r-values for the contour graphs
    :param name: the name of the contour, for debugging

    :return: a dictionary, where the keys are the contour values
             and the values are a list of TGraph objects containing the curves
             for the respective contour value (e.g. {1. : [TGraph1,TGraph2],...})
    """
    #if name == "prettyPlots:ecgraphs":
    #    return {}
    import ROOT
    from array import array

    if tgraph.GetN() == 0:
        logger.info("No excluded points found for %s" %tgraph.GetName())
        return None

    cVals = sorted(contVals)
    if tgraph.GetN() < 4:
        print ( "Error: Cannot create a contour with fewer than 3 input vertices" )
        return None
    h = tgraph.GetHistogram()
    #Get contour graphs:
    c1 = ROOT.TCanvas()
    h.SetContour(3,array('d',cVals))
    h.Draw("CONT Z LIST")
    c1.Update()
    clist = ROOT.gROOT.GetListOfSpecials().FindObject("contours")
    cgraphs = {}
    for i in range(clist.GetSize()):
        contLevel = clist.At(i)
        curv = contLevel.First()
        cgraphs[cVals[i]] = []
        for j in range(contLevel.GetSize()):
            cgraphs[cVals[i]].append(curv.Clone() )
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
