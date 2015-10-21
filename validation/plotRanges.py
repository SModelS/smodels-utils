#!/usr/bin/env python

"""
.. module:: plotRanges
   :synopsis: Given a TGraph object, returns a simple list of points to probe for validation.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import ROOT
import numpy,math
import sys
sys.path.insert(0,"../")
from smodels_utils.dataPreparation.vertexChecking import VertexChecker
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot
from smodels.tools.physicsUnits import GeV,fb
import logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

def getMinMax ( tgraph ):
    """ get the frame that tgraphs fits in nicely """
    if tgraph.GetN() == 0:
        return None
    xpts,ypts = tgraph.GetX(),tgraph.GetY()
    minx = 0.8*ROOT.TMath.MinElement(tgraph.GetN(),xpts)
    maxx = 1.2*ROOT.TMath.MaxElement(tgraph.GetN(),xpts)
    miny = 0.9*ROOT.TMath.MinElement(tgraph.GetN(),ypts)
    maxy = 1.2*ROOT.TMath.MaxElement(tgraph.GetN(),ypts)
    
    return { "x": [minx,maxx], "y": [miny,maxy] }

def getSuperFrame ( tgraphs ):
    """ get the all-enveloping frame of tgraphs """
    if type ( tgraphs ) == ROOT.TGraph:
        return getMinMax ( tgraphs) 
    minx, miny = float("inf"), float("inf")
    maxx, maxy = 0., 0.
    for tgraph in tgraphs:
        frame = getMinMax ( tgraph )
        if not frame:
            continue    
        minx = int(min(minx,frame["x"][0]))
        maxx = int(max(maxx,frame["x"][1]))
        miny = int(min(miny,frame["y"][0]))
        maxy = int(max(maxy,frame["y"][1]))
    logger.info ( "the super frame is [%f,%f],[%f,%f]" % ( minx, maxx, miny, maxy ) )
    return { "x": [ minx, maxx], "y": [ miny, maxy ] }

def getExtendedFrame(txnameObjs,axes):
    """
    Gets the frame containing all points in the TxName data which belong
    to the axes definition
    :param txnameObj: TxName object
    :param axes: Axes definition (string), i.e. 2*Eq(mother,x)_Eq(lsp,y)
    :return: max and min values for x and y in the extended frame
    """
    
    origPlot = OrigPlot.fromString(axes)
    minx, miny = float("inf"), float("inf")
    maxx, maxy = 0., 0.
    for txnameObj in txnameObjs:
        txnameObj.txnameData.loadData()
        data = txnameObj.txnameData.data  #Data grid of mass points and ULs of efficiencies
        # print "data=",type(data),txnameObj.getInfo("id"),txnameObj,type(txnameObj)
        # print "path=",txnameObj.path,txnameObj.globalInfo
        if data==None:
            continue
        for pt in data:
            mass = pt[0]
            mass_unitless = [[(m/GeV).asNumber() for m in mm] for mm in mass]
            xy = origPlot.getXYValues(mass_unitless)
            if xy is None: continue
            else: x,y = xy
            minx = min(minx,x)
            miny = min(miny,y)
            maxx = max(maxx,x)
            maxy = max(maxy,y)

    minx = 0.8*minx
    maxx = 1.2*maxx
    miny = 0.9*miny
    maxy = 1.2*maxy
    logger.info ( "the extended frame is [%f,%f],[%f,%f]" % ( minx, maxx, miny, maxy ) )
    return { "x": [ minx, maxx], "y": [ miny, maxy ] }
        
    

def addQuotationMarks ( constraint ):
    """ [[[t+]],[[t-]]] -> [[['t+']],[['t-']]] """
    ##print("[plotRanges.py] addQuotationMarks",constraint)
    if constraint.find("'")>-1:
        return constraint
    ret=""
    for i in range(len(constraint)):
        if constraint[i] == "[" and constraint[i+1] not in [ "[", "]" ]:
            ret+=constraint[i]+"'"
            continue
        if constraint[i] == "]" and constraint[i-1] not in [ "[", "]" ]:
            ret+="'" + constraint[i]
            continue
        if constraint[i] == "," and constraint[i-1] not in [ "[", "]" ]:
            ret+="'" + constraint[i] + "'"
            continue
        ret+=constraint[i]
    logger.info ( "added quotation marks: %s" % ret )
    return ret


def getPoints ( tgraphs, txnameObjs, axes = "2*Eq(mother,x)_Eq(lsp,y)", \
                constraint="[[[t+]],[[t-]]]", onshell=True, offshell=True ):
    """ given a TGraph object, returns list of points to probe. You define whether
        you want the onshell region or the offshell region (or both).
        :param txnameObj: TxName object
        :param axes: the axes used to transform x,y into mass parameters (for the check
                of the kinematic region)
        :param constraint: the constraint to check for onshell / offshellness
    """
    
    txname = txnameObjs[0].getInfo('txName')
    print("[plotRanges] txname=>>%s<<" % txname)
    vertexChecker = VertexChecker ( txname, addQuotationMarks ( constraint ) )
    #print "[getPoints] vertexChecker constraint=",addQuotationMarks(constraint)
    #print "[getPoints] vertexChecker kinconstraint=",vertexChecker.kinConstraints
    frame = getSuperFrame(tgraphs)
    extframe = getExtendedFrame(txnameObjs,axes)
    origPlot = OrigPlot.fromString ( axes )
    
    #First generate points for the extended frame with a lower density:
    minx,maxx=extframe["x"][0], extframe["x"][1]
    miny,maxy=extframe["y"][0], extframe["y"][1]    
    dx=(maxx-minx)/(10.-1.)
    dy=(maxy-miny)/(10.-1.)
    dx = round(dx/5.)*5.
    dy = round(dy/5.)*5.
    minx = round(minx/dx)*dx
    miny = round(miny/dy)*dy
    
    ptsA = generatePoints(minx,maxx,miny,maxy,dx,dy,txnameObjs,axes,onshell
                          ,offshell,origPlot,vertexChecker)
    
    #Now generate points for the exclusion curve frame with a higher density:
    minx,maxx=frame["x"][0], frame["x"][1]
    miny,maxy=frame["y"][0], frame["y"][1]    

    #print "x=",minx,maxx
    #print "y=",miny,maxy
    dx=(maxx-minx)/(30.-1.)
    dy=(maxy-miny)/(20.-1.)
    dx = max(1,round(dx/5.)*5.)
    dy = max(1,round(dy/5.)*5.)
    minx = round(minx/dx)*dx
    miny = round(miny/dy)*dy
    
    ptsB = generatePoints(minx,maxx,miny,maxy,dx,dy,txnameObjs,axes,onshell
                          ,offshell,origPlot,vertexChecker)
    
    pts = ptsA + ptsB
    
    return pts


def generatePoints(minx,maxx,miny,maxy,dx,dy,txnameObjs,axes,onshell,offshell,origPlot,vertexChecker):
    points=[]
    if minx==float('inf') or abs(maxx)<1e-5:
        return points
    for i in numpy.arange ( minx, maxx+dx/2., dx ):
        for j in numpy.arange ( miny, maxy+dy/2., dy ):
            masses_unitless = origPlot.getParticleMasses(i,j)
            #Skip points with zero masses (too slow when running pythia)
            if 0. in masses_unitless[0]+masses_unitless[1]: continue
            masses = [[m*GeV for m in mm] for mm in masses_unitless]
            #Skip points which are outside any grid
            inside=False
            for txnameObj in txnameObjs:
                val = txnameObj.txnameData.getValueFor(masses)
                if type(val) in [ type(fb), float ]:
                    inside=True
            if not inside:
#                 print "masses",masses,"not inside any grid"
                continue
            ordered=True
            for k in range(len(masses[0])-1):
                if masses[0][k]<=masses[0][k+1]:
                    ordered=False
            if not ordered:
                continue
            osv=vertexChecker.getOffShellVertices(masses_unitless)
#             print "i,j = ",i,j,"masses = ",masses, "offshell=",osv,"axes=",axes
            if osv==[] and not onshell:
                continue
            if not osv==[] and not offshell:
                continue
            points.append ( [i,j] )
    return points

def draw ( graph, points ):
    # container=[]
    t=ROOT.TGraph()
    for ctr,point in enumerate(points):
        print "draw",point
        # t=ROOT.TMarker ( point[0], point[1], 23 )
        # t.Draw()
        # container.append(t)
        t.SetPoint(ctr,point[0],point[1])
    t.Draw("AP")
    if type(graph)==ROOT.TGraph: graph.Draw("same")
    if type(graph)==list:
        for g in graph:
            g.Draw("same")
    ROOT.c1.Print("save.pdf")

if __name__ == "__main__":
    filename="/home/walten/git/smodels-database/8TeV/ATLAS/ATLAS-SUSY-2013-19/sms.root"
    f=ROOT.TFile(filename)
    axes="2*Eq(mother,x)_Eq(lsp,y)"
    txname="T2tt"
    graph=f.Get("%s/exclusion_%s" % ( txname, axes) )
    filename2="/home/walten/git/smodels-database/8TeV/ATLAS/ATLAS-SUSY-2013-05/sms.root"
    f2=ROOT.TFile(filename2)
    print "ls=",f2.ls()
    graph2=f2.Get("%s/exclusion_%s" % ( "T2bb", axes) )
    print "graph1,2=",graph,graph2

    pts = getPoints ( [graph, graph2], txname, axes, "[[[t+]],[[t-]]]", onshell=True, offshell=False )
    draw ( [graph, graph2] , pts )
