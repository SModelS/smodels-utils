#!/usr/bin/env python3

"""
.. module:: tools.checkInterpolation.py
   :synopsis:  Checks the interpolation error in the database.
"""

import sys,os
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))

from smodels.experiment.databaseObj import Database
from smodels.base.physicsUnits import GeV, fb, TeV, pb
import random
from ROOT import TCanvas, TGraph2D, TLatex, gPad, gStyle, TH1F
from AuxPlot import Default, set_palette



def createHist(pts,silentMode=False):
    """
    :return: TCanvas object containing the plot
    """

    h = TH1F("errors", "relative errors", 1000,0.,100.)
    for pt in pts:
        if pt[1] == pt[2]: continue
        relError = abs(pt[1]-pt[2])/pt[1]
        h.Fill(relError)
        
    Default(h,"TH1")
#     h.GetXaxis().SetTitle("Relative error")
    h.GetYaxis().SetTitle("Fraction of Interpolations")
    plane = TCanvas("c1", "c1",0,0,800,600)    
    Default(plane,"TCanvas")
    set_palette(gStyle)
    plane.SetLeftMargin(0.17)
    plane.SetBottomMargin(0.16)
    plane.SetRightMargin(0.2)
    plane.SetLogy()
    plane.SetLogx()
    plane.cd()
    h.DrawNormalized()

    if not silentMode:
        ans = raw_input("Hit any key to close\n")    

    return plane
    

def createPlot(pts,silentMode=False):
    """
    :return: TCanvas object containing the plot
    """
    
    
    gr = TGraph2D()
    grOld = TGraph2D()
    #Loop over events and get points
    for pt in pts:
        #Get plotting variables  
        xval = pt[0][0][0].asNumber(GeV)
        yval = pt[0][0][-1].asNumber(GeV)
        zval = abs(pt[1]-pt[2])/pt[1]
        if zval.asNumber() == 0.:
            grOld.SetPoint(grOld.GetN(),xval,yval,zval)
        else:
            gr.SetPoint(gr.GetN(),xval,yval,zval)
        
    #Graph options:
    Default(gr,"TGraph2D")    
    gr.SetMarkerStyle(20)
    gr.SetMarkerSize(2.)
    grOld.SetMarkerStyle(5)
    gr.SetTitle("")    
    gr.GetXaxis().SetTitle("Mother mass (GeV)")
    gr.GetYaxis().SetTitle("Daughter mass (GeV)")
    gr.GetXaxis().SetLimits(gr.GetXmin()*0.9,gr.GetXmax()*1.1)
    gr.GetYaxis().SetLimits(gr.GetYmin()*0.9,gr.GetYmax()*1.1)    
    gr.GetZaxis().SetRangeUser(0.,gr.GetZmax())    
    gr.GetYaxis().SetTitleOffset(1.1)
    gr.GetXaxis().SetTitleOffset(1.2)
    gr.GetYaxis().SetTitleFont(132)
    gr.GetXaxis().SetTitleFont(132)
    gr.GetZaxis().SetTitleFont(132)
    gr.GetZaxis().SetTitleSize(0.075)
    gr.GetYaxis().SetTitleSize(0.075)
    gr.GetXaxis().SetTitleSize(0.075)
    gr.GetYaxis().SetLabelOffset(-0.025)
    gr.GetXaxis().SetLabelOffset(0.015)


    plane = TCanvas("c1", "c1",0,0,800,600)    
    Default(plane,"TCanvas")
    set_palette(gStyle)
    plane.SetLeftMargin(0.17)
    plane.SetBottomMargin(0.16)
    plane.SetRightMargin(0.2)
    plane.cd()
    gr.Draw("PCOLZ")
    grOld.Draw("PSAME")
    plane.SetTheta(90.)
    plane.SetPhi(0.001)
    ztit = TLatex()
    ztit.SetTextFont(12)
    ztit.SetTextSize(0.08)
    ztit.DrawLatexNDC(0.91,0.6, "Relative error")
    
    gPad.Update()
    if not silentMode:
        ans = raw_input("Hit any key to close\n")    
    
    return plane


def rmvPoints(txnameData):
    """
    Remove points from a TxnameData object and returns the points.
    :param txnameData: TxNameData object
    :return: list of points [[mass1,val1],[mass2,val2]...]
    """
    
    random.seed(10.)
    #Make sure data is loaded
    txnameData.loadData()
    pts = []
    maxN = 20
    reducedData = txnameData.data[:]
    while len(pts) < len(txnameData.data)/4. and len(pts) < maxN:
        ipt = random.randint(0,len(reducedData)-1)
        pts.append(reducedData.pop(ipt))
            
    #Reload the reduced data grid:
    txnameData.store_value = reducedData
    txnameData.loadData()
            
    return pts

def checkInterpolationFor(expIds = ['all'], txnames=['all'], datasetIDs = ['all']):
    """
    Remove points from the data grid and interpolate on them.
    Returns the maximum relative error for each txname grid.
    """

    #Load the database
    database = Database(os.path.join(home,'smodels-database'))
    expResults = database.getExpResults(analysisIDs=expIds, txnames=txnames, 
                                        datasetIDs=datasetIDs)
    
    #Get all the txName objects:
    txnames = []
    for expRes in expResults:
        for dataset in expRes.datasets:
            txnames += dataset.txnameList
    
    
    #Loop over each grid and generate a reduced grid partially removing
    #the original points
    removedPts = []
    for txname in txnames:
        removedPts.append(rmvPoints(txname.txnameData))
        
    #Now interpolate for the removed points
    maxErrors = [0.]*len(txnames)
    txnameErrors = {}
    for itx,txname in enumerate(txnames):
        txnameErrors[txname.path] = []
        for pt in removedPts[itx]:            
            val = txname.txnameData.getValueFor(pt[0])
            if type(pt[1]) == type(fb): pt[1] = pt[1].asNumber(fb)
            if pt[1] == 0. or val is None: continue
            elif type(val) == type(fb): val = val.asNumber(fb)
            maxErrors[itx] = max(maxErrors[itx],abs(val-pt[1])/pt[1])
            newpt = pt
            newpt.append(val)
            txnameErrors[txname.path].append(newpt)
        for pt in txname.txnameData.data:
            newpt = pt
            newpt.append(pt[1])
            txnameErrors[txname.path].append(newpt)
    
    #Print results
    for itx,txname in enumerate(txnames):
        print ( txname,'\nmax rel. error=',maxErrors[itx] )
        
    #Plot results
    allPts = []
    for txname,pts in txnameErrors.items():
        allPts += pts
#         createPlot(pts,silentMode=True)
        
    createHist(allPts,silentMode=False) 
        
if __name__ == "__main__":
    expIds = ['all']
    txnames = ['all']
    datasetIDs = ['all']
    checkInterpolationFor(expIds,txnames,datasetIDs)    
