#!/usr/bin/env python

"""
.. module:: plottingFuncs
   :synopsis: Main methods for dealing with the plotting of a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys
sys.path.append('../')

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
from ROOT import TFile,TGraph,gROOT,TMultiGraph,TCanvas,TLatex,TLegend,kGreen,kRed,kOrange
from smodels.tools.physicsUnits import fb, GeV, pb
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot


def getExclusionCurvesFor(expResult,txname=None,axes=None):
    """
    Reads sms.root and returns the TGraph objects for the exclusion
    curves. If txname is defined, returns only the curves corresponding
    to the respective txname. If axes is defined, only returns the curves
    
    :param expResult: an ExpResult object
    :param txname: the TxName in string format (i.e. T1tttt)
    :param axes: the axes definition in string format (i.e. 2*Eq(mother,x)_Eq(lsp,y))
    
    :return: a dictionary, where the keys are the TxName strings
            and the values are the respective list of TGraph objects.
    """
    
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
            if not 'exclusion_' in objName: continue
            if axes and not axes in objName: continue
            txnames[tx].append(obj.ReadObj())
            nplots += 1
    if not nplots:
        logger.warning("No exclusion curve found.")
        return False
    
    return txnames

def getFigureUrl ( validationPlot ):
    txnameinfo = validationPlot.expRes.getTxnameWith ( { "txname": validationPlot.txname } )
    if type ( txnameinfo ) == list:
        logger.error ( "received a list for .getTxnameWith. Dont know what to do with this" )
        txnameinfo=txnameinfo[0]
    if type ( txnameinfo.getInfo ( "figureUrl" ) ) == str:
        return txnameinfo.getInfo ( "figureUrl" )
    if not txnameinfo.getInfo ( "figureUrl" ):
        return None
    if type ( txnameinfo.getInfo ( "figureUrl" ) ) != type ( txnameinfo.getInfo ( "axes" )  ):
            logger.error ( "figureUrl (%s) and axes (%s) are not of the same type" % ( txnameinfo.getInfo ( "figureUrl" ),
                       txnameinfo.getInfo ( "axes" )  ) )
            return None
    if not validationPlot.axes in txnameinfo.getInfo ( "axes" ):
        return None
    pos = [ i for i,x in enumerate ( txnameinfo.getInfo ( "axes" ) ) if x==validationPlot.axes ]
    if len(pos)!=1:
        logger.error ( "found axes %d times" % len(pos ) )
        sys.exit()
    print "pos=",pos
    return txnameinfo.getInfo ( "figureUrl" )[ pos[0] ]

def createSpecialPlot(validationPlot,silentMode=True,looseness=1.2,what = "bestregion", nthpoint =1 ):
    """
    Uses the data in validationPlot.data and the official exclusion curve
    in validationPlot.officialCurve to generate "special" plots, showing
    e.g. upper limits or best signal region
    
    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :param what: what is to be plotted ( "bestregion", "upperlimits", "crosssections")
    :param nthpoint: label only every nth point
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
            if abs ( kfactor - pt['kfactor'] ) > 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()
            x, y = pt['axes']
#             print pt
            if pt['condition'] and max(pt['condition'].values() ) > 0.05:
                #print "pt['condition']",pt['condition']
                logger.warning("Condition violated for file " + pt['slhafile'])
                cond_violated.SetPoint(cond_violated.GetN(), x, y)
            elif pt['signal'] > pt['UL']:
                if pt['signal'] < pt ['UL']* looseness:
                    excluded_border.SetPoint(excluded_border.GetN(), x, y)
                else:
                    excluded.SetPoint(excluded.GetN(), x, y )
            else:
                if pt['signal']*looseness > pt['UL']:
                    allowed_border.SetPoint(allowed_border.GetN(), x, y)
                else:
                    allowed.SetPoint(allowed.GetN(), x, y)

    labels=[]

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurve:
        logger.warning("Official curve for validation plot is not defined.")
    else:
        official = validationPlot.officialCurve
    
    if silentMode: gROOT.SetBatch()    
    setOptions(allowed, Type='allowed')
    setOptions(cond_violated, Type='cond_violated')
    setOptions(allowed_border, Type='allowed_border')
    setOptions(excluded, Type='excluded')
    setOptions(excluded_border, Type='excluded_border')
    setOptions(official, Type='official')
    base = TMultiGraph()
    if allowed.GetN()>0: base.Add(allowed, "P")
    if excluded.GetN()>0: base.Add(excluded, "P")
    if allowed_border.GetN()>0: base.Add(allowed_border, "P")
    if excluded_border.GetN()>0: base.Add(excluded_border, "P")
    if cond_violated.GetN()>0: base.Add(cond_violated, "P")
    base.Add(official, "C")
    title = what+"_"+validationPlot.expRes.getValuesFor('id') + "_" \
            + validationPlot.txname\
            + "_" + validationPlot.axes
    figureUrl = getFigureUrl(validationPlot)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)    
    base.Draw("AP")
    base.SetTitle(title)
    l=TLatex()
    l.SetNDC()
    l.SetTextSize(.04)
    agreement = validationPlot.computeAgreementFactor()
    l.DrawLatex(.15,.85,"validation agreement %.1f %s" % (agreement*100, "%" ) )
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
            if abs ( kfactor - pt['kfactor'] ) > 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()
            x, y = pt['axes']
            import ROOT
            lk=ROOT.TLatex ()
            lk.SetTextSize(.02)
            if what in [ "bestregion", "bestcut" ]:
                bestregion=pt["dataset"].replace("ANA","").replace("CUT","")
                lk.DrawLatex ( x, y, bestregion )
                print "draw",x,y,pt["dataset"]
            elif what == "upperlimits":
                ul=pt["UL"].asNumber(pb)
                lk.DrawLatex ( x, y, str(ul) )
            elif what == "crosssections":
                signalxsec=pt['signal'].asNumber(pb)
                lk.DrawLatex ( x, y, str(signalxsec) )
                # print "point",pt["axes"],pt["signal"]
            else:
                logger.error( "dont know how to draw %s" % what )
                sys.exit()
            labels.append ( lk )

        #Add original grid data to UL plot:
        if what == "upperlimits":
            olk=ROOT.TLatex ()
            olk.SetTextSize(.02)
            origPlot = OrigPlot.fromString(validationPlot.axes)
            txnameObj = validationPlot.expRes.getTxnameWith({'txname': validationPlot.txname})
            txnameData = txnameObj.txnameData.data
            for (itr, (mass,ul)) in enumerate ( txnameData ):
                if itr% nthpoint != 0: continue
                mass_unitless = [[(m/GeV).asNumber() for m in mm] for mm in mass]            
                v=origPlot.getXYValues(mass_unitless)
                if not v: continue
                x,y = v
                ul = ul.asNumber(pb)
                lk.DrawLatex ( x, y, "#color[4]{"+str(ul)+"}" )
                

    l2=TLatex()
    l2.SetNDC()
    l2.SetTextSize(.04)
    l2.DrawLatex(.15,.78,"k-factor %.2f" % kfactor ) 
    base.l2=l2
    l3=TLatex()
    l3.SetNDC()
    l3.SetTextSize(.04)
    drawingwhat="upper limits [pb]"
    if what == "crosssections":
        drawingwhat="theory predictions [pb]"
    if what in [ "bestregion", "bestcut" ]:
        drawingwhat="best signal region"
    l3.DrawLatex(.15,.7, drawingwhat )
    base.l3=l3
    plane.base = base

    if not silentMode: ans = raw_input("Hit any key to close\n")

    plane.labels=labels
    
    return plane
            
        

def createPlot(validationPlot,silentMode=True, looseness = 1.2 ):
    """
    Uses the data in validationPlot.data and the official exclusion curve
    in validationPlot.officialCurve to generate the exclusion plot
    
    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :return: TCanvas object containing the plot
    """
        
    # Check if data has been defined:
    excluded, allowed, excluded_border, allowed_border = TGraph(), TGraph(), TGraph(), TGraph()
    cond_violated=TGraph()
    kfactor=None

    if not validationPlot.data:
        logger.warning("Data for validation plot is not defined.")
    else:
        # Get excluded and allowed points:
        for pt in validationPlot.data:
            if kfactor == None:
                kfactor = pt ['kfactor']
            if abs ( kfactor - pt['kfactor'] ) > 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()
            x, y = pt['axes']
#             print pt
            if pt['condition'] and max(pt['condition'].values() ) > 0.05:
                #print "pt['condition']",pt['condition']
                logger.warning("Condition violated for file " + pt['slhafile'])
                cond_violated.SetPoint(cond_violated.GetN(), x, y)
            elif pt['signal'] > pt['UL']:
                if pt['signal'] < pt ['UL']* looseness:
                    excluded_border.SetPoint(excluded_border.GetN(), x, y)
                else:
                    excluded.SetPoint(excluded.GetN(), x, y )
            else:
                if pt['signal']*looseness > pt['UL']:
                    allowed_border.SetPoint(allowed_border.GetN(), x, y)
                else:
                    allowed.SetPoint(allowed.GetN(), x, y)
        

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurve:
        logger.warning("Official curve for validation plot is not defined.")
    else:
        official = validationPlot.officialCurve
    
    if silentMode: gROOT.SetBatch()    
    setOptions(allowed, Type='allowed')
    setOptions(cond_violated, Type='cond_violated')
    setOptions(allowed_border, Type='allowed_border')
    setOptions(excluded, Type='excluded')
    setOptions(excluded_border, Type='excluded_border')
    setOptions(official, Type='official')
    base = TMultiGraph()
    if allowed.GetN()>0: base.Add(allowed, "P")
    if excluded.GetN()>0: base.Add(excluded, "P")
    if allowed_border.GetN()>0: base.Add(allowed_border, "P")
    if excluded_border.GetN()>0: base.Add(excluded_border, "P")
    if cond_violated.GetN()>0: base.Add(cond_violated, "P")
    base.Add(official, "C")
    title = validationPlot.expRes.getValuesFor('id') + "_" \
            + validationPlot.txname\
            + "_" + validationPlot.axes
    figureUrl = getFigureUrl(validationPlot)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)    
    base.Draw("AP")
    base.SetTitle(title)
    l=TLatex()
    l.SetNDC()
    l.SetTextSize(.04)
    agreement = validationPlot.computeAgreementFactor()
    l.DrawLatex(.15,.85,"validation agreement %.1f %s" % (agreement*100, "%" ) )
    base.l=l
    if figureUrl:
        # print "dawing figureUrl"
        l1=TLatex()
        l1.SetNDC()
        l1.SetTextSize(.025)
        l1.DrawLatex(.12,.15,"%s" % figureUrl)
        base.l1=l1
    l2=TLatex()
    l2.SetNDC()
    l2.SetTextSize(.04)
    l2.DrawLatex(.15,.75,"k-factor %.2f" % kfactor ) 
    base.l2=l2

    if not silentMode: ans = raw_input("Hit any key to close\n")
    
    return plane,base
            
        
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
    elif Type == 'allowed_border':
        obj.SetMarkerStyle(20)    
        obj.SetMarkerColor(kGreen+3)
    elif Type == 'excluded_border':
        obj.SetMarkerStyle(20)    
        obj.SetMarkerColor(kOrange+1)
        
