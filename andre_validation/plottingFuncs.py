#!/usr/bin/env python

"""
.. module:: plottingFuncs
   :synopsis: Main methods for dealing with the plotting of a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
from ROOT import *
from smodels.tools.physicsUnits import fb, GeV


def createPlot(validationPlot):
    """
    Uses the data in validationPlot.data and the official exclusion curve
    in validationPlot.officialCurve to generate the exclusion plot
    
    :param validationPlot: ValidationPlot object
    :return: FIXME ????
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
            x = (x / GeV).asNumber()
            y = (y / GeV).asNumber()
            if pt['cond'] and max(pt['cond']) > 0.01:
                logger.warning("Condition violated for file " + pt['slhafile'])
            if pt['signal'] > pt['UL']:
                allowed.SetPoint(allowed.GetN(), x, y)
            else:
                excluded.SetPoint(excluded.GetN(), x, y)

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurve:
        logger.warning("Official curve for validation plot is not defined.")
    else:
        official = validationPlot.officialCurve
        
    setOptions(allowed, type='allowed')
    setOptions(excluded, type='excluded')
    setOptions(official, type='official')
    base = TMultiGraph()
    base.add(allowed, "P")
    base.add(excluded, "P")
    base.add(official, "C")
    title = validationPlot.expRes.getValuesFor('id') + ":" \
            + validationPlot.txname.getInfo('txname')\
            + ":" + validationPlot.axes
    base.setTitle(title)
    plane = TCanvas("c1", "c1", 0, 0, 800, 600)
    base.Draw("AP")
    ans = raw_input("Hit any key to close\n")
            
        
def setOptions(obj,type=None):
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
    if not type: return True
    elif type == 'allowed':
        obj.SetMarkerStyle(20)    
        obj.SetMarkerColor(kGreen)
    elif type == 'excluded':
        obj.SetMarkerStyle(20)    
        obj.SetMarkerColor(kRed)