#!/usr/bin/env python3

"""
.. module:: plotRanges
   :synopsis: Given a TGraph object, returns a simple list of points to probe for validation.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

# from __future__ import print_function

import ROOT
import numpy
import unum
import sys
import ctypes
from smodels.experiment.txnameObj import TxNameData
# sys.path.insert(0,"../")
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels.base.physicsUnits import GeV
from smodels_utils.dataPreparation.inputObjects import TxNameInput
from smodels.theory.auxiliaryFunctions import removeUnits, addUnit
import itertools
import logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

def getMinMax ( tgraph ):
    """ get the frame that tgraphs fits in nicely """
    if tgraph.GetN() == 0:
        return None
    xpts,ypts=[],[]
    n=tgraph.GetN()
    for i in range(n):
        # x,y=ROOT.Double(),ROOT.Double()
        x,y=ctypes.c_double(),ctypes.c_double()
        tgraph.GetPoint(i,x,y)
        xpts.append ( x )
        ypts.append ( y )
    minx = 0.8*min(xpts)
    maxx = 1.2*max(xpts)
    miny = 0.9*min(ypts)
    maxy = 1.2*max(ypts)

    return { "x": [minx,maxx], "y": [miny,maxy] }

def getSuperFrame(tgraphs):
    """get the all-enveloping frame of tgraphs"""
    if type ( tgraphs ) == ROOT.TGraph:
        return getMinMax ( tgraphs)
    minx, miny = None, None
    maxx, maxy = None, None
    for tgraph in tgraphs:
        frame = getMinMax ( tgraph )
        if not frame:
            continue
        if minx is None:
            minx, maxx = frame["x"][0],frame["x"][1]
            miny, maxy = frame["y"][0],frame["y"][1]

        minx = min(minx,frame["x"][0])
        maxx = max(maxx,frame["x"][1])
        miny = min(miny,frame["y"][0])
        maxy = max(maxy,frame["y"][1])
    if minx is None:
        logger.info(f"Could not find points for {str(tgraphs)}")
        return None
    logger.info ( f"the super frame (which covers all exclusion curves) is {minx:g} < x < {maxx:g}, {miny:g} < y < {maxy:g}" )
    return { "x": [ minx, maxx], "y": [ miny, maxy ] }

def getExtendedFrame(txnameObjs,axes):
    """
    Gets the frame containing all points in the TxName data which belong
    to the axes definition
    :param txnameObjs: list of TxName objects
    :param axes: Axes definition (string), i.e. 2*Eq(mother,x)_Eq(lsp,y)
    :return: max and min values for x and y in the extended frame
    """

    massPlane = MassPlane.fromString(txnameObjs[0].txName,axes)
    minVars = {}
    maxVars = {}
    for txnameObj in txnameObjs:
        txnameData = txnameObj.txnameData
        data = txnameData.tri.points  #Data grid of rotated points
        if len(data) == 0:
            continue
        for pt in data:
            #Switch back to original mass point
            mass = txnameData.coordinatesToData(pt,rotMatrix=txnameData._V,
                                                transVector=txnameData.delta_x)
            mass = removeUnits(mass,standardUnits=GeV)
            #Check if mass belong to the mass plane:
            varsDict = massPlane.getXYValues(mass)
            if varsDict is None:
                continue
            for xLabel,xValue in varsDict.items():
                if not xLabel in minVars:
                    minVars[xLabel] = xValue
                    maxVars[xLabel] = xValue
                minVars[xLabel] = min(minVars[xLabel],xValue)
                maxVars[xLabel] = max(maxVars[xLabel],xValue)

    if None in minVars or None in maxVars:
        logger.info(f"Could not find points for {axes}")
        return None

    for xLabel in minVars:
        minVars[xLabel] *= 0.8
        maxVars[xLabel] *= 1.2
    rangesDict = dict([[xLabel,[minVars[xLabel],maxVars[xLabel]]] for xLabel in minVars])
    infoMsg = "the extended frame (which covers all data points) is:"
    for xstr,r in list(rangesDict.items()):
        infoMsg += f" {r[0]:g} < {str(xstr)} < {r[1]:g},"
    infoMsg = infoMsg.rstrip(',')
    logger.info( infoMsg)
    return rangesDict

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

def getPoints(tgraphs, txnameObjs, axes = "[[x, x - y], [x, x - y]]", Npts=300):
    """
    Given a TGraph object, returns list of points to probe. If no tgraph
    is given return zero points.

        :param txnameObjs: list of TxName objects
        :param axes: the axes used to transform x,y into mass parameters (for the check
                of the kinematic region)
        :param Npts: Trial number of points for the plot.
    """
    massPlane = MassPlane.fromString(txnameObjs[0].txName,axes)
    txnameInput = TxNameInput(txnameObjs[0].txName)
    txnameInput.constraint = txnameObjs[0].constraint
    vertexChecker = lambda mass: txnameInput.checkMassConstraints(mass)

    logger.debug ( f"get points {massPlane}" )    

    # First generate points for the extended frame (= from the ul/eff maps)
    # with a lower density:
    extframe = getExtendedFrame(txnameObjs,axes)
    if extframe:
        varRanges = extframe
        ptsA = generatePoints(Npts/3,varRanges,
                              txnameObjs,massPlane,vertexChecker)
    else: ptsA = []

    #Now generate points for the exclusion curve frame with a higher density:
    if tgraphs:
        frame = getSuperFrame(tgraphs)
        if frame:
            varRanges = frame
            ptsB = generatePoints(Npts,varRanges,
                                    txnameObjs,massPlane,vertexChecker)
    else: ptsB = []

    pts = ptsA + ptsB

    logger.debug( f"pts[:3]={pts[:3]}" )

    return pts

def generatePoints(Npts,varRanges,txnameObjs,massPlane,vertexChecker):
    """
    Method to generate points between minx,maxx and miny,maxy.
    Uses the PCA decomposition and rotated points in order to best estimate
    what is the relevant region of parameter space where there is data.
    Check if the points belong to the plane described by massPlane an obeys
    the kinematical constraints defined by vertexChecker.
    Also, requires the point to belong to at least one of the data grids in
    txnameObjs.

    :param Npts: Number of points to be tried
    :param varRanges: Dictionary with the labels and ranges for the plane variables
                      (e.g. {'x' : [500.,1000.], 'y' : [100.,500.]} for 2D planes
                      or {'x' : [10.,1000.]} for 1D planes)
    :param txnameObjs: List of Txname objects
    :param massPlane: MassPlane object holding information about the plane
    :param vertexChecker: function which evaluates mass constraints
    :return: List of x,y points belonging to the plot and the data grids. Each point
            is a dict: {'x' : xvalue, 'y': yvalue,...}.
    """


    #Collects all points belonging to the plane:
    planeMasses = []
    reducedData = []
    for tx in txnameObjs:
        txnameData = tx.txnameData
        data = txnameData.tri.points  #Data grid of rotated points
        for i,pt in enumerate(data):
            #Switch back to original mass point
            mass = txnameData.coordinatesToData(pt,rotMatrix=txnameData._V,
                                                transVector=txnameData.delta_x)
            mass = removeUnits(mass,standardUnits=GeV)
            #Check if mass belong to the mass plane:
            xyDict = massPlane.getXYValues(mass)
            if xyDict is None:
                continue
            tmpmass = massPlane.getParticleMasses(**xyDict)
            #Add units:
            mass = addUnit(tmpmass,GeV)
            # mass = [[m*GeV for m in br] for br in tmpmass]
            #Does not include the same mass point twice from distinct signal regions
            if mass in planeMasses:
                continue
            planeMasses.append(mass)
            if hasattr(tx.txnameData, 'y_values'):
                reducedData.append([mass,tx.txnameData.y_values[i]])
            else:
                if hasattr(tx.txnameData, 'xsecUnitless'):
                    reducedData.append([mass,tx.txnameData.xsecUnitless[i]])
                else:
                    reducedData.append([mass,numpy.asscalar(tx.txnameData.xsec[i])])
    #If there is no data, return empty list:
    rangesList = list(varRanges.items())
    ranges = [x[1] for x in rangesList]  #Collect the ranges in order
    xvars = [x[0] for x in rangesList] #Collect the var labels in order

    if not reducedData:
        logger.warning("No data points found for plane.")
        return []
        """
        def dressPoint ( pt ):
            pt=addUnit ( pt, GeV )
            return ( [ mP, 0.1 ] )

        reducedData = [ ]
        import random

        for i in range(1000):
            d={}
            for var in xvars:
                d[var]=random.uniform ( varRanges[var][0], varRanges[var][1] )
            mP = massPlane.getParticleMasses( **d )
            reducedData.append ( dressPoint ( mP ) )
        txdata = TxNameData(reducedData,"upperLimit","dummy")
        """
    else:
        #Compute the PCA for the reduced dataset:
        txdata = TxNameData(reducedData,"upperLimit","dummy")
        ## FIXME maybe this guy doesnt know anything about widths?


    #Transform the min and max values to the rotated plane:

    extremePoints = []
    for x in list(itertools.product(*ranges)):
        xvalues = dict(zip(xvars,x))
        mass = addUnit(massPlane.getParticleMasses(**xvalues),GeV)
        P = txdata.dataToCoordinates(mass)
        extremePoints.append(P)

    #Limit extreme values by data:
    Mp = numpy.array(txdata.tri.points)
    extremePoints = numpy.array(extremePoints)
    newRanges = []
    steps = []
    for iaxis in range(len(xvars)):
        vminData = min(Mp[:,iaxis])
        vmaxData = max(Mp[:,iaxis])
        vminRange = min(extremePoints[:,iaxis])
        vmaxRange = max(extremePoints[:,iaxis])
        newRanges.append([max(vminData,vminRange),min(vmaxData,vmaxRange)])
        dvar = abs(newRanges[-1][1]-newRanges[-1][0]) #Define the step in the variable
        dvar = dvar/(float(Npts)**(1./len(xvars))) #The exponent makes sure the total numper of pts ~ Npts
        steps.append(dvar)

    #Round minimum ranges
    for i,vrange in enumerate(newRanges):
        newRanges[i][0] = round(vrange[0]/steps[i])*steps[i]

    points=[]
    #Create an array with all var points:
    allPoints = []
    for i,vrange in enumerate(newRanges):
        vmin,vmax = vrange
        dv = steps[i]
        if vmax < vmin and dv > 0.: ## swap sign
            dv = - dv
        allPoints.append([x for x in numpy.arange(vmin, vmax+dv/2., dv)])

    for pt in itertools.product(*allPoints):
        pt = list(pt)
        #Check if point is in the convexhull. If not, try another one
        if txdata.tri.find_simplex(pt) < 0:
            continue
        mass = txdata.coordinatesToData(pt,rotMatrix=txdata._V,
                                        transVector=txdata.delta_x)
        mass = removeUnits(mass,standardUnits=GeV)
        #Round all masses (to be consistent with smodels)
        def roundme ( x ):
            if type(x) in (float,int):
                return round(x,1)
            return ( round(x[0],1), x[1] )
        mass = [[roundme(m) for m in br] for br in mass]
        if not vertexChecker(mass):
            continue
        if massPlane.getXYValues(mass) is None:
            continue
        inside = False
        mass_unit = addUnit(mass,GeV)
        # mass_unit = [[m*GeV for m in br] for br in mass]
        for tx in txnameObjs:
            if not (tx.txnameData.getValueFor(mass_unit) is None):
                inside = True
                break
        if not inside:
            continue
        points.append(massPlane.getXYValues(mass))
    return points

def draw ( graph, points ):
    # container=[]
    t=ROOT.TGraph()
    for ctr,point in enumerate(points):
        print ( "draw",point )
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
    graph=f.Get(f"{txname}/exclusion_{axes}" )
    filename2="/home/walten/git/smodels-database/8TeV/ATLAS/ATLAS-SUSY-2013-05/sms.root"
    f2=ROOT.TFile(filename2)
    print ("ls=",f2.ls() )
    graph2=f2.Get(f"T2bb/exclusion_{axes}" )
    print ("graph1,2=",graph,graph2 )

    pts = getPoints ( [graph, graph2], txname, axes, "[[[t+]],[[t-]]]", onshell=True, offshell=False )
    draw ( [graph, graph2] , pts )
