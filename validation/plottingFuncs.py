#!/usr/bin/env python

"""
.. module:: plottingFuncs
   :synopsis: Main methods for dealing with the plotting of a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,numpy,random
sys.path.append('../')
from array import array

logger = logging.getLogger(__name__)
from ROOT import (TFile,TGraph,TGraph2D,gROOT,TMultiGraph,TCanvas,TLatex,
                  TLegend,kGreen,kRed,kOrange,kBlack,kGray,TPad,
                  TPolyLine3D,Double,TColor,gStyle,TH2D,TImage)
from smodels.tools.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxes

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



def getExclusionCurvesFor(expResult,txname=None,axes=None, get_all=False ):
    """
    Reads sms.root and returns the TGraph objects for the exclusion
    curves. If txname is defined, returns only the curves corresponding
    to the respective txname. If axes is defined, only returns the curves
    
    :param expResult: an ExpResult object
    :param txname: the TxName in string format (i.e. T1tttt)
    :param axes: the axes definition in string format (i.e. 2*Eq(mother,x)_Eq(lsp,y))
    :param get_all: Get also the +-1 sigma curves?
    
    :return: a dictionary, where the keys are the TxName strings
            and the values are the respective list of TGraph objects.
    """
    
    if type(expResult)==list:
        expResult=expResult[0]
    rootpath = os.path.join(expResult.path,'sms.root')
    if not os.path.isfile(rootpath):
        logger.error("Root file %s not found" %rootpath)
        return False
    
    rootFile = TFile(rootpath)
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
            if 'expexclusion' in objName.lower(): continue
            # print "[plottingFuncs.py] name=",objName
            if axes and not axes in objName: continue
            txnames[tx].append(obj.ReadObj())
            nplots += 1
    if not nplots:
        logger.warning("No exclusion curve found.")
        return False
    
    return txnames

def getFigureUrl(validationPlot ):
    
    txname = validationPlot.expRes.datasets[0].txnameList[0]
    txurl = txname.getInfo("figureUrl")
    txaxes = txname.getInfo("axes")
    if isinstance(txurl,str):
        return txname.getInfo("figureUrl" )
    if not txurl:
        return None
    if type(txurl) != type(txaxes):
        logger.error("figureUrl (%s) and axes (%s) are not of the same type" %(txurl,
                       txaxes))
        return None
    elif isinstance(txurl,list) and len(txurl) != len(txaxes):
        logger.error("figureUrl (%s) and axes (%s) are not of the same length" %(txurl,
                       txaxes))
        return None 
    if not validationPlot.axes in txaxes:
        return None
    pos = [i for i,x in enumerate(txaxes) if x==validationPlot.axes ]
    
    if len(pos)!=1:
        logger.error("found axes %d times" % len(pos))
        sys.exit()
    return txurl[pos[0]]

def createSpecialPlot(validationPlot,silentMode=True,looseness=1.2,what = "bestregion", nthpoint =1, 
       signal_factor = 1. ):
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

    excluded, allowed, excluded_border, allowed_border = TGraph(), TGraph(), TGraph(), TGraph()
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
        # print "[plottingFuncs.py] official=",len(official)
    
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
        base.Add(official, "L")
    title = what+"_"+validationPlot.expRes.getValuesFor('id')[0] + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.niceAxes
    figureUrl = getFigureUrl(validationPlot)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)    
    base.Draw("AP")
    base.SetTitle(title)
    l=TLatex()
    l.SetNDC()
    l.SetTextSize(.04)
    base.l=l
    if figureUrl:
        # print "dawing figureUrl"
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
#                 print "draw",x,y,pt["dataset"]
            elif what == "upperlimits":
                ul=pt["UL"].asNumber(pb)
                lk.DrawLatex(x, y, str(ul) )
            elif what == "crosssections":
                signalxsec=pt['signal'].asNumber(pb)
                lk.DrawLatex(x, y, str(signalxsec) )
                # print "point",pt["axes"],pt["signal"]
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
                #print "txnameObj=",txnameObj,type(txnameObj),txnameObj.txName
                txnameData = txnameObj.txnameData.data
                #print "txnameData=",txnameData
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
            
def createPlot(validationPlot,silentMode=True, looseness = 1.2, extraInfo=False ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate the exclusion plot
    
    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :return: TCanvas object containing the plot
    """
        
    # Check if data has been defined:
    xlabel, ylabel = 'x','y'
    excluded, allowed, excluded_border, allowed_border = TGraph(), TGraph(), TGraph(), TGraph()
    excluded.SetName("excluded")
    allowed.SetName("allowed")
    excluded_border.SetName("excluded_border")
    allowed_border.SetName("allowed_border")
    cond_violated=TGraph()
    kfactor=None
    tavg = 0.

    if not validationPlot.data:
        logger.error("Data for validation plot is not defined.")
        return (None,None)
        ## sys.exit()
    else:
        # Get excluded and allowed points:
        for pt in validationPlot.data:
            if kfactor == None:
                kfactor = pt ['kfactor']
            if abs(kfactor - pt['kfactor'])> 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()

            xvals = pt['axes']
            if "t" in pt:
                tavg += pt["t"]
            r = pt['signal']/pt ['UL']
            if isinstance(xvals,dict):
                if len(xvals) == 1:
                    x,y = xvals['x'],r
                    ylabel = "r = #sigma_{signal}/#sigma_{UL}"
                else:
                    x,y = xvals['x'],xvals['y']
            else:
                x,y = pt['axes']
            

            if pt['condition'] and pt['condition'] > 0.05:
                #print "pt['condition']",pt['condition']
                logger.warning("Condition violated for file " + pt['slhafile'])
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

    tavg = tavg / len (validationPlot.data )

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurves:
        logger.warning("Official curve for validation plot is not defined.")
        official = None
    else:
        official = validationPlot.officialCurves
        logger.debug("Official curves have length %d" % len (official) )
    
    if silentMode: gROOT.SetBatch()    
    setOptions(allowed, Type='allowed')
    setOptions(cond_violated, Type='cond_violated')
    setOptions(allowed_border, Type='allowed_border')
    setOptions(excluded, Type='excluded')
    setOptions(excluded_border, Type='excluded_border')
    if official:
        for i in official:
            setOptions( i, Type='official')
    base = TMultiGraph()
    if allowed.GetN()>0: base.Add(allowed, "P")
    if excluded.GetN()>0: base.Add(excluded, "P")
    if allowed_border.GetN()>0: base.Add(allowed_border, "P")
    if excluded_border.GetN()>0: base.Add(excluded_border, "P")
    if cond_violated.GetN()>0: base.Add(cond_violated, "P")
    if official:
        for i in official:
            base.Add( i, "L")
    title = validationPlot.expRes.getValuesFor('id')[0] + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.niceAxes
    subtitle = "%d datasets: " % len(validationPlot.expRes.datasets)
    for dataset in validationPlot.expRes.datasets:
        ds_txnames = map ( str, dataset.txnameList )
        if not validationPlot.txName in ds_txnames:
            continue
        dataId = str(dataset.dataInfo.dataId)
        # print "[plottingFuncs.py] add to %s: %s, %s" % ( validationPlot.txName, id, str ( map ( str, dataset.txnameList  ) ) )
        subtitle+=dataId+", "
    subtitle = subtitle[:-2]
    if hasattr ( validationPlot.expRes.globalInfo, "covariance" ):
        subtitle = "%d aggregate regions" % len(validationPlot.expRes.datasets)
    if len(subtitle) > 100:
        subtitle = subtitle[:100] + " ..."
    if len(validationPlot.expRes.datasets) == 1 and type(validationPlot.expRes.datasets[0].dataInfo.dataId)==type(None):
        subtitle = "dataset: upper limit"
        
    figureUrl = getFigureUrl(validationPlot)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)    
    base.Draw("AP")
    base.SetTitle(title)
    base.GetXaxis().SetTitle(xlabel)
    base.GetYaxis().SetTitle(ylabel)    
    l=TLatex()
    l.SetNDC()
    l.SetTextSize(.04)
    base.l=l
    l0=TLatex()
    l0.SetNDC()
    l0.SetTextSize(.025)
    l0.DrawLatex(.05,.905,subtitle)
    signal_factor = 1. # an additional factor that is multiplied with the signal cross section
    agreement = round(100.*validationPlot.computeAgreementFactor( signal_factor = signal_factor ))
    logger.info ( "Agreement: %d%s" % (agreement,"%") )
    if extraInfo:
        lex=TLatex()
        lex.SetNDC()
        # lex.SetTextColor( kGray )
        lex.SetTextSize(.026 )
        import socket
        hn=socket.gethostname()
        lex.DrawLatex(.59,.12,"agreement: %d%s, t~%.1fs [%s]" % (agreement, "%", tavg, hn ) )
        base.lex=lex
    base.l0=l0
    if figureUrl:
        l1=TLatex()
        l1.SetNDC()
        l1.SetTextSize(.02)
        l1.DrawLatex(.06,.02,"%s" % figureUrl)
        base.l1=l1
    l2=TLatex()
    l2.SetNDC()
    l2.SetTextSize(.025)
    l2.SetTextAngle(90.)
    l2.SetTextColor( kGray )
    l2.DrawLatex(.93,.15,"k-factor %.2f" % kfactor)
    #l2.DrawLatex(.15,.75,"k-factor %.2f" % kfactor)
    base.l2=l2
    if extraInfo: ## a timestamp, on the right border
        import time
        l9=TLatex()
        l9.SetNDC()
        l9.SetTextSize(.025)
        l9.SetTextAngle(90.)
        l9.SetTextColor( kGray )
        l9.DrawLatex ( .93, .65, time.strftime("%b %d, %Y, %H:%M") )
        base.l9 = l9

    if not silentMode:
        _ = raw_input("Hit any key to close\n")
    
    return plane,base

def createPrettyPlot(validationPlot,silentMode=True, looseness = 1.2 ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate a pretty exclusion plot
    
    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :return: TCanvas object containing the plot
    """

    # Check if data has been defined:
    tgr = TGraph2D()
    kfactor=None
    xlabel, ylabel, zlabel = 'x','y',"r = #sigma_{signal}/#sigma_{UL}"
    
    if not validationPlot.data:
        logger.error("Data for validation plot is not defined.")
        return (None,None)
        ## sys.exit()
    else:
        # Get excluded and allowed points:
        for pt in validationPlot.data:
            if kfactor == None:
                kfactor = pt ['kfactor']
            if abs(kfactor - pt['kfactor'])> 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()
            xvals = pt['axes']
            r = pt['signal']/pt ['UL']
            if isinstance(xvals,dict):
                if len(xvals) == 1:
                    x,y = xvals['x'],r
                    ylabel = "r = #sigma_{signal}/#sigma_{UL}"
                else:
                    x,y = xvals['x'],xvals['y']
            else:
                x,y = xvals
            
            if pt['condition'] and pt['condition'] > 0.05:
                logger.warning("Condition violated for file " + pt['slhafile'])
            else:
                tgr.SetPoint(tgr.GetN(), x, y, r)

    if tgr.GetN() == 0:
        logger.error("No good points for validation plot.")
        return (None,None)

    #ROOT has trouble obtaining a histogram from a 1-d graph. So it is
    #necessary to smear the points if they rest in a single line.
    if tgr.GetYmax() == tgr.GetYmin():
        logger.info("1d data detected, smearing Y values")
        buff = tgr.GetX()
        buff.SetSize(sys.maxsize)
        xpts = numpy.frombuffer(buff,count=tgr.GetN())
        buff = tgr.GetY()
        buff.SetSize(sys.maxsize)
        ypts = numpy.frombuffer(buff,count=tgr.GetN())
        buff = tgr.GetZ()
        buff.SetSize(sys.maxsize)
        zpts = numpy.frombuffer(buff,count=tgr.GetN())
        for i in range(tgr.GetN()):
            tgr.SetPoint(i,xpts[i],ypts[i]+random.uniform(0.,0.001),zpts[i])
    if tgr.GetXmax() == tgr.GetXmin():
        logger.info("1d data detected, smearing X values")
        buff = tgr.GetX()
        buff.SetSize(sys.maxsize)
        xpts = numpy.frombuffer(buff,count=tgr.GetN())
        buff = tgr.GetY()
        buff.SetSize(sys.maxsize)
        ypts = numpy.frombuffer(buff,count=tgr.GetN())
        buff = tgr.GetZ()
        buff.SetSize(sys.maxsize)
        zpts = numpy.frombuffer(buff,count=tgr.GetN())
        for i in range(tgr.GetN()):
            tgr.SetPoint(i,xpts[i]+random.uniform(0.,0.001),ypts[i],zpts[i])

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurves:
        logger.warning("Official curve for validation plot is not defined.")
        official = None
    else:
        official = validationPlot.officialCurves
        logger.debug("Official curves have length %d" % len (official) )
    
    
    if silentMode: gROOT.SetBatch()  
    setOptions(tgr, Type='allowed')
    title = validationPlot.expRes.getValuesFor('id')[0]
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
    h.GetXaxis().SetTitle(xlabel)
    h.GetYaxis().SetTitle(ylabel)
    h.GetZaxis().SetTitle(zlabel)
    h.SetContour(200)
    h.Draw("COLZ")
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
            setOptions(gr, Type='official')
            gr.Draw("L SAME")
    
    #Draw additional info      
    ltx=TLatex()
    ltx.SetNDC()
    ltx.SetTextSize(.035)
    ltx.SetTextFont(12)
    txStr = validationPlot.txName +' : '+prettyTxname(validationPlot.txName)
    axStr = prettyAxes(validationPlot.txName,validationPlot.axes)
    axStr = str(axStr).replace(']','').replace('[','').replace("'","")
    infoStr = "#splitline{"+txStr+'}{'+axStr+'}'
    ltx.DrawLatex(.03,.89,infoStr)
    tgr.ltx = ltx
    figureUrl = getFigureUrl(validationPlot)
    if figureUrl:
        l1=TLatex()
        l1.SetNDC()
        l1.SetTextSize(.025)
        """l1.DrawLatex(.01,0.023,"#splitline{official plot:}{%s}" % figureUrl)"""
        tgr.l1=l1
    if kfactor > 1.0:
        l2=TLatex()
        l2.SetNDC()
        l2.SetTextFont(132)
        l2.SetTextSize(.04)
        l2.DrawLatex(0.16,0.6,"k-factor = %.2f" % kfactor)
        tgr.l2=l2
    
    subtitle = "%d datasets" % len(validationPlot.expRes.datasets)
    if validationPlot.expRes.datasets[0].dataInfo.dataId.startswith("ar"):
        subtitle = "%d aggregate datasets" % len(validationPlot.expRes.datasets)
    #for dataset in validationPlot.expRes.datasets:
    #    ds_txnames = map ( str, dataset.txnameList )
    #    if not validationPlot.txName in ds_txnames:
    #        continue
        dataId = str(dataset.dataInfo.dataId)
    #    # print "[plottingFuncs.py] add to %s: %s, %s" % ( validationPlot.txName, id, str ( map ( str, dataset.txnameList  ) ) )
    #    subtitle+=dataId+", "
    #subtitle = subtitle[:-2]
    #if hasattr ( validationPlot.expRes.globalInfo, "covariance" ):
    #    subtitle = "%d aggregate regions" % len(validationPlot.expRes.datasets)
    #if len(subtitle) > 100:
    #    subtitle = subtitle[:100] + " ..."
    if len(validationPlot.expRes.datasets) == 1 and type(validationPlot.expRes.datasets[0].dataInfo.dataId)==type(None):
        subtitle = "upper limit"
    if validationPlot.combine == False and len(validationPlot.expRes.datasets) > 1:
        subtitle = "best SR"
    lsub=TLatex()
    lsub.SetNDC()
    lsub.SetTextAlign(31)
    lsub.SetTextSize(.025)
    lsub.DrawLatex(.98,.086,subtitle)
    tgr.lsub=lsub
    
    
    #Count the number of entries in legend:
    nleg = min(2,len(cgraphs)-list(cgraphs.values()).count([])) + min(2,len(official))
    #Draw legend: 
    dx = 0. ## top, left
    dx = .33 ## top, right
    leg = TLegend(0.15+dx,0.83-0.045*nleg,0.495+dx,0.83)
    setOptions(leg)    
    leg.SetFillStyle(0)
    leg.SetTextSize(0.04)
    added = False    
    for cval,grlist in cgraphs.items():        
        if not grlist:
            continue
        if cval == 1.0:
            leg.AddEntry(grlist[0],"exclusion (SModelS)","L")
        elif (cval == looseness or cval == 1./looseness) and not added:
            leg.AddEntry(grlist[0],"#pm20% (SModelS)","L")
            added = True
    added = False
    for gr in official:
        if 'xclusion_' in gr.GetTitle():
            leg.AddEntry(gr,"exclusion (official)","L")
        elif 'xclusionP1_' in gr.GetTitle() or 'xclusionM1_' in gr.GetTitle() and not added:
            leg.AddEntry(gr,"#pm1#sigma (official)","L")
            added = True
    
    leg.Draw()
    tgr.leg = leg
    plane.Update()  

    if not silentMode:
        ans = raw_input("Hit any key to close\n")
    
    return plane,tgr

def createTempPlot(validationPlot,silentMode=True,what = "R", nthpoint =1, signal_factor =1.):
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
    title = validationPlot.expRes.getValuesFor('id')[0] + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.niceAxes
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
        obj.SetLineColor(1)
        obj.SetLineStyle(1)
        obj.SetLineWidth(1)
        obj.SetFillColor(0)
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
        obj.SetLineWidth(4)
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
    #Draw temp plot:
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
    x1, y1 = Double(), Double()
    curve.GetPoint(0, x1, y1)
    yline = []
    for ipt in range(curve.GetN() + 1): 
        x, y = Double(), Double()
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

    x2, y2 = Double(), Double()
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
