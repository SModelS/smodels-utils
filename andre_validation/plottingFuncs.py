#!/usr/bin/env python

"""
.. module:: plottingFuncs
   :synopsis: Main methods for dealing with the plotting of a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
from ROOT import *
from smodels.tools.physicsUnits import fb, GeV


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


def createPlot(validationPlot,silentMode=True):
    """
    Uses the data in validationPlot.data and the official exclusion curve
    in validationPlot.officialCurve to generate the exclusion plot
    
    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :return: TCanvas object containing the plot
    """
        
    # Check if data has been defined:
    excluded = TGraph()
    allowed = TGraph()        
    if not validationPlot.data:
        logger.warning("Data for validation plot is not defined.")
    else:
        # Get excluded and allowed points:
        for pt in validationPlot.data:
            x, y = pt['axes']
            if pt['condition'] and max(pt['condition']) > 0.01:
                logger.warning("Condition violated for file " + pt['slhafile'])
            if pt['signal'] > pt['UL']:
                excluded.SetPoint(excluded.GetN(), x, y)
            else:
                allowed.SetPoint(allowed.GetN(), x, y)

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurve:
        logger.warning("Official curve for validation plot is not defined.")
    else:
        official = validationPlot.officialCurve
    
    if silentMode: gROOT.SetBatch()    
    setOptions(allowed, Type='allowed')
    setOptions(excluded, Type='excluded')
    setOptions(official, Type='official')
    base = TMultiGraph()
    base.Add(allowed, "P")
    base.Add(excluded, "P")
    base.Add(official, "C")
    title = validationPlot.expRes.getValuesFor('id') + "_" \
            + validationPlot.txname\
            + "_" + validationPlot.axes

    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)    
    base.Draw("AP")
    base.SetTitle(title)
    l=TLatex()
    l.SetNDC()
    l.SetTextSize(.04)
    wrongness = validationPlot.computeWrongnessFactor()
    l.DrawLatex(.15,.8,"validation wrong by %.1f %s" % (wrongness*100, "%" ) )
    base.l=l
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
    elif Type == 'excluded':
        obj.SetMarkerStyle(20)    
        obj.SetMarkerColor(kRed)
