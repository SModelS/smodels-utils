#!/usr/bin/env python

"""
.. module:: plotRanges
   :synopsis: Given a TGraph object, returns a simple list of points to probe for validation.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import ROOT
import numpy,math,copy
import sys
sys.path.insert(0,"../")
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot
from smodels.tools.physicsUnits import GeV,fb
from smodels_utils.dataPreparation import vertexChecking
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
    minx, miny = None, None
    maxx, maxy = None, None
    for tgraph in tgraphs:
        frame = getMinMax ( tgraph )
        if not frame:
            continue
        if minx is None:
            minx, maxx = int(frame["x"][0]),int(frame["x"][1])
            miny, maxy = int(frame["y"][0]),int(frame["y"][1])
            
        minx = int(min(minx,frame["x"][0]))
        maxx = int(max(maxx,frame["x"][1]))
        miny = int(min(miny,frame["y"][0]))
        maxy = int(max(maxy,frame["y"][1]))
    if minx is None:
        logger.info("Could not find points for %s" %axes)
        return None
    logger.info ( "the super frame is [%f,%f],[%f,%f]" % ( minx, maxx, miny, maxy ) )
    return { "x": [ minx, maxx], "y": [ miny, maxy ] }

def getExtendedFrame(txnameObjs,axes):
    """
    Gets the frame containing all points in the TxName data which belong
    to the axes definition
    :param txnameObjs: list of TxName objects
    :param axes: Axes definition (string), i.e. 2*Eq(mother,x)_Eq(lsp,y)
    :return: max and min values for x and y in the extended frame
    """
    
    origPlot = OrigPlot.fromString(axes)
    minx, miny = None, None
    maxx, maxy = None, None
    for txnameObj in txnameObjs:
        data = txnameObj.txnameData._data  #Data grid of mass points and ULs or efficiencies
        if not data:
            continue
        for pt in data:
            mass = pt[0]
            mass_unitless = [[(m/GeV).asNumber() for m in mm] for mm in mass]
            xy = origPlot.getXYValues(mass_unitless)
            if xy is None: continue
            else: x,y = xy
            if minx is None:
                minx, maxx = x, x
                miny, maxy = y, y
            minx = min(minx,x)
            miny = min(miny,y)
            maxx = max(maxx,x)
            maxy = max(maxy,y)

    if minx is None:
        logger.info("Could not find points for %s" %axes)
        return None

    minx = 0.8*minx
    maxx = 1.2*maxx
    miny = 0.9*miny
    maxy = 1.2*maxy
    logger.info( "the extended frame is [%f,%f],[%f,%f]" % ( minx, maxx, miny, maxy ) )
    return { "x": [ minx, maxx], "y": [ miny, maxy ] }
        
    

def addQuotationMarks ( constraint ):
    """ [[[t+]],[[t-]]] -> [[['t+']],[['t-']]] """

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

    return ret


def getPoints(tgraphs, txnameObjs, axes = "2*Eq(mother,x)_Eq(lsp,y)", Npts=300):
    """ given a TGraph object, returns list of points to probe. 
        :param txnameObjs: list of TxName objects
        :param axes: the axes used to transform x,y into mass parameters (for the check
                of the kinematic region)
        :param Npts: Trial number of points for the plot.
    """
        
        
    frame = getSuperFrame(tgraphs)
    extframe = getExtendedFrame(txnameObjs,axes)
    origPlot = OrigPlot.fromString(axes)
    vertexChecker = vertexChecking.VertexChecker(txnameObjs[0], 
                        addQuotationMarks(txnameObjs[0].constraint))
    

    #First generate points for the extended frame with a lower density:
    if extframe:
        minx,maxx=extframe["x"][0], extframe["x"][1]
        miny,maxy=extframe["y"][0], extframe["y"][1]
        ptsA = generateBetterPoints(Npts/3,minx,maxx,miny,maxy,txnameObjs,origPlot,vertexChecker)
    else: ptsA = []
    
    #Now generate points for the exclusion curve frame with a higher density:
    if frame:
        minx,maxx=frame["x"][0], frame["x"][1]
        miny,maxy=frame["y"][0], frame["y"][1]    
        ptsB = generateBetterPoints(Npts,minx,maxx,miny,maxy,txnameObjs,origPlot,vertexChecker)
    else: ptsB = []
    
    pts = ptsA + ptsB
    
    return pts


def generatePoints(Npts,minx,maxx,miny,maxy,txnameObjs,origPlot,vertexChecker):
    """
    Method to generate points between minx,maxx and miny,maxy.
    Check if the points belong to the plane described by origPlot an obeys
    the kinematical constraints defined by vertexChecker.
    Also, requires the point to belong to at least one of the data grids in
    txnameObjs.

    :param Npts: Number of points to be tried
    :param minx: Minimal x-value for the respective mass plane)
    :param maxx: Maximal x-value for the respective mass plane)
    :param miny: Minimal y-value for the respective mass plane)
    :param maxy: Maximal y-value for the respective mass plane)
    :param txnameObjs: List of Txname objects
    :param origPlot: OrigPlot object holding information about the plane
    :param vertexChecker: VertexChecker object holding information about the
                          kinematical constraints
    :return: List of x,y points belonging to the plot and the data grids.    
    """
    
    #Compute dx and dy values to generate the desired number of points
    dx=(maxx-minx)/math.sqrt(float(Npts))
    dy=(maxy-miny)/math.sqrt(float(Npts))
    minx = round(minx/dx)*dx
    miny = round(miny/dy)*dy
    
    
    points=[]
    if minx==float('inf') or abs(maxx)<1e-5:
        return points
    for i in numpy.arange ( minx, maxx+dx/2., dx ):
        for j in numpy.arange ( miny, maxy+dy/2., dy ):
            masses_unitless = origPlot.getParticleMasses(i,j)
            #Skip points with zero masses (too slow when running pythia)
            if min([br[-1] for br in masses_unitless]) <= 0.: continue
            #Check off-shell vertices. If there are any, skip point
            #(Important to skip possible off-shell points in the on-shell data grid)
            if vertexChecker and vertexChecker.getOffShellVertices(masses_unitless):
                continue            
            masses = [[m*GeV for m in mm] for mm in masses_unitless]
            #Skip points which are outside any grid
            inside=False
            for txnameObj in txnameObjs:
                val = txnameObj.txnameData.getValueFor(masses)
                if type(val) in [ type(fb), float ]:
                    inside=True 
                    break
            if not inside:
                continue
            ordered=True
            for k in range(len(masses[0])-1):
                if masses[0][k]<=masses[0][k+1]:
                    ordered=False
            if not ordered:
                continue
            points.append([i,j])
    return points


def generateBetterPoints(Npts,minx,maxx,miny,maxy,txnameObjs,origPlot,vertexChecker):
    """
    Method to generate points between minx,maxx and miny,maxy.
    Uses the PCA decomposition and rotated points in order to best estimate
    what is the relevant region of parameter space where there is data.
    Check if the points belong to the plane described by origPlot an obeys
    the kinematical constraints defined by vertexChecker.
    Also, requires the point to belong to at least one of the data grids in
    txnameObjs.
    
    :param Npts: Number of points to be tried
    :param minx: Minimal x-value for the respective mass plane)
    :param maxx: Maximal x-value for the respective mass plane)
    :param miny: Minimal y-value for the respective mass plane)
    :param maxy: Maximal y-value for the respective mass plane)
    :param txnameObjs: List of Txname objects
    :param origPlot: OrigPlot object holding information about the plane
    :param vertexChecker: VertexChecker object holding information about the
                          kinematical constraints
    :return: List of x,y points belonging to the plot and the data grids.    
    """
    
    #Create a dummy copy of a TxnameData object to hold all the data corresponding to the plane
    txdata = copy.deepcopy(txnameObjs[0].txnameData)
    txdata.dataTag = 'dummy'
    txdata._id = 'dummy'
    txdata._accept_errors_upto=0.05    
    txdata._V = None
    txdata.Mp = []
    txdata._data = []
    #Collects all points belonging to the plane:
    masses = []
    for tx in txnameObjs:
        for pt in tx.txnameData._data:
            mass = [[m.asNumber(GeV) for m in br] for br in pt[0]]
            if not origPlot.getXYValues(mass): continue
            if not pt[0] in masses:  #Does not include the same mass point twice from distinct signal regions
                txdata._data.append(pt)
                masses.append(pt[0])
    
    #If there is no data, return empty list:
    if not txdata._data:
        logger.warning("No data points found for plane.")
        return []
    else:
    #Compute the PCA for the reduced dataset:
        txdata.computeV()
    #Transform the min and max values to the rotated plane:
    extremes = []
    for x,y in [[minx,miny],[maxx,miny],[minx,maxy],[maxx,maxy]]:
        mass = [[m*GeV for m in br] for br in origPlot.getParticleMasses(x,y)]
        porig = txdata.flattenMassArray(mass)
        p=((numpy.matrix(porig)[0] - txdata.delta_x)).tolist()[0]
        P=numpy.dot(p,txdata._V)  ## rotated point
        extremes.append(P)
    #New values of extremes in the rotated plane (limit values by extremes in data):
    xmin = max(min(numpy.array(extremes)[:,0]),min(numpy.array(txdata.Mp)[:,0]))
    xmax = min(max(numpy.array(extremes)[:,0]),max(numpy.array(txdata.Mp)[:,0])) 
    ymin = max(min(numpy.array(extremes)[:,1]),min(numpy.array(txdata.Mp)[:,1]))
    ymax = min(max(numpy.array(extremes)[:,1]),max(numpy.array(txdata.Mp)[:,1]))
    #Compute dx and dy values to generate the desired number of points
    dx=(xmax-xmin)/math.sqrt(float(Npts))
    dy=(ymax-ymin)/math.sqrt(float(Npts))
    xmin = round(xmin/dx)*dx
    ymin = round(ymin/dy)*dy
    #Detected extended 1D-data:
    if txdata.dimensionality == 2 and len(txdata.Mp) % 2 == 0:
        ydataMin = min(numpy.array(txdata.Mp)[:,1]) 
        ydataMax = max(numpy.array(txdata.Mp)[:,1])
        if ydataMax - ydataMin < 0.001:
            logger.info("1D data detected. Collapsing y-dimension")
            ymin = ymax = (ydataMax+ydataMin)/2.

    points=[]
    massDimensions = [len(br) for br in txdata._data[0][0]] #Store the mass format 
    for i in numpy.arange(xmin, xmax+dx/2., dx):
        for j in numpy.arange(ymin, ymax+dy/2., dy):
            pt = [i,j] + [0.]*(txdata.full_dimensionality-2)  #Point in rotated space
            massFlat = numpy.dot(pt,numpy.transpose(txdata._V)) + txdata.delta_x #Flatten Mass
            massFlat = massFlat.tolist()[0]
            mass = [[massFlat.pop(0) for im in range(brdim)] for brdim in massDimensions] #Nested mass
            if vertexChecker.getOffShellVertices(mass):
                continue
            if origPlot.getXYValues(mass) is None:
                continue
            inside = False
            mass_unit = [[m*GeV for m in br] for br in mass]
            for tx in txnameObjs:                
                if not (tx.txnameData.getValueFor(mass_unit) is None):
                    inside = True
                    break
            if not inside:
                continue
            points.append(origPlot.getXYValues(mass))
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
