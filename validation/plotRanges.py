#!/usr/bin/env python3

"""
.. module:: plotRanges
   :synopsis: Given a TGraph object, returns a simple list of points to probe for validation.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function

import ROOT
import numpy
import unum
import sys
from smodels.experiment.txnameObj import TxNameData
sys.path.insert(0,"../")
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels.tools.physicsUnits import GeV,fb,standardUnits
try: ## smodels >= 200
    from smodels.theory.auxiliaryFunctions import removeUnits
except ImportError:
    pass
from smodels_utils.dataPreparation.inputObjects import TxNameInput
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
        x,y=ROOT.Double(),ROOT.Double()
        tgraph.GetPoint(i,x,y)
        xpts.append ( x )
        ypts.append ( y )
    minx = 0.8*min(xpts)
    maxx = 1.2*max(xpts)
    miny = 0.9*min(ypts)
    maxy = 1.2*max(ypts)
    ## logger.debug ( "done %f, %f, %f, %f" % ( minx, maxx, miny, maxy ) )
    #xpts,ypts = tgraph.GetX(),tgraph.GetY() ## fixed: was leaky!
    #minx = 0.8*min(n,*xpts)
    #maxx = 1.2*max(n,*xpts)
    #miny = 0.9*min(n,*ypts)
    #maxy = 1.2*max(n,*ypts)
    
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
            minx, maxx = int(frame["x"][0]),int(frame["x"][1])
            miny, maxy = int(frame["y"][0]),int(frame["y"][1])
            
        minx = int(min(minx,frame["x"][0]))
        maxx = int(max(maxx,frame["x"][1]))
        miny = int(min(miny,frame["y"][0]))
        maxy = int(max(maxy,frame["y"][1]))
    if minx is None:
        logger.info("Could not find points for %s" %str(tgraphs))
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
    
    massPlane = MassPlane.fromString(txnameObjs[0].txName,axes)
    minVars = {}
    maxVars = {}
    for txnameObj in txnameObjs:
        data = txnameObj.txnameData.tri.points  #Data grid of rotated points
        if len(data) == 0:
            continue
        for pt in data:
            #Switch back to original mass point
            mass = getMassArrayFor(pt,massPlane,txnameObj.txnameData,unit=None)
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
        logger.info("Could not find points for %s" %axes)
        return None

    for xLabel in minVars:
        minVars[xLabel] *= 0.8
        maxVars[xLabel] *= 1.2
    rangesDict = dict([[xLabel,[minVars[xLabel],maxVars[xLabel]]] for xLabel in minVars])
    infoMsg = "the extended frame is:"
    for xstr,r in list(rangesDict.items()):
        infoMsg += " %0.2f < %s < %0.2f," %(r[0],str(xstr),r[1])
    infoMsg = infoMsg.rstrip(',')    
    logger.info( infoMsg)
    return rangesDict

def getMassArrayFor(pt,massPlane,txnameData,unit=None):
        """
        Transforms the point pt in the PCA space to the original mass array
        :param pt: point with the dimentions of the data dimensionality (e.g. [x,y])
        :param txnameData: TxnameData object holding information about the PCA
        :param massPlane: MassPlane object holding information about the original axes.
        :param unit: Unit for returning the mass array. If None, it will be
                     returned unitless        
        :return: Mass array (e.g. [[mass1,mass2],[mass3,mass4]])
        """
        
        if txnameData._V is None:
            logger.error("Data has not been loaded")
            return None
        if len(pt) != txnameData.dimensionality:
            logger.error("Wrong point dimensions (%i), it should be %i" 
                         %(len(pt),txnameData.dimensionality))
            return None
        fullpt = numpy.append(pt,[0.]*(txnameData.full_dimensionality-len(pt)))        
        mass = numpy.dot(txnameData._V,fullpt) + txnameData.delta_x        
        mass = mass.tolist()[0]
        if not unit is None and isinstance(unit,unum.Unum):
            mass = [m*unit for m in mass]        
        
        return massListToArray(mass,massPlane.axes)
            

def massListToArray(massList,axes):
    """
    Tries to convert a flattened list of floats into a mass array
    according to massShape. If massShape has string elements, these will
    be used instead of the entries in massList.
    e.g.  massList = [5.,10.], massShape = ['*',[x,y]] -> return ['*',[5.,10.]]
    e.g.  massList = [5.,10.], massShape = [[x],[x]] -> return [[5.],[10.]]
    
    :param massList: 1D list of floats (dimension should match number of numerical 
                     entries in axes
    :param axes: Nested list describing the axes (e.g. [[x],[x]] or ['*',[x]])
    
    :return: Nested mass array with entries from massList and shape from axes 
             (e.g. [[5.],[10.]]) 
    """
    
    if isinstance(axes,(list,numpy.ndarray)):
        return [massListToArray(massList,m) for m in axes]
    if isinstance(axes,(tuple,numpy.ndarray)):
        return tuple([massListToArray(massList,m) for m in axes])
    if isinstance(axes,str):
        return axes
    return massList.pop(0)
        
    
        
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
    
    #First generate points for the extended frame with a lower density:
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
    
    return pts

def _addUnits ( masses ):
    """ add units to scalars in nested containers """
    newmasses = []
    for br in masses:
        tmp = []
        for m in br:
            if type(m) in ( float, int ):
                m=m*GeV
            else:
                m=tuple([m[0]*GeV,m[1]*GeV])
            tmp.append(m)
        newmasses.append ( tmp )
    return newmasses


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
        data = tx.txnameData.tri.points  #Data grid of rotated points
        for i,pt in enumerate(data):
            #Switch back to original mass point
            mass = getMassArrayFor(pt,massPlane,tx.txnameData,unit=None)
            #Check if mass belong to the mass plane:
            xyDict = massPlane.getXYValues(mass)            
            if xyDict is None:
                continue
            tmpmass = massPlane.getParticleMasses(**xyDict)
            #Add units:
            mass = _addUnits ( tmpmass )
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
    if not reducedData:
        logger.warning("No data points found for plane.")
        return []
    else:
        #Compute the PCA for the reduced dataset:        
        txdata = TxNameData(reducedData,"upperLimit","dummy")
        
        
    #Transform the min and max values to the rotated plane:
    extremePoints = []    
    rangesList = list(varRanges.items())
    ranges = [x[1] for x in rangesList]  #Collect the ranges in order
    xvars = [x[0] for x in rangesList] #Collect the var labels in order
    for x in list(itertools.product(*ranges)):
        xvalues = dict(zip(xvars,x))
        mass = _addUnits ( massPlane.getParticleMasses(**xvalues) )
        # mass = [[m*GeV for m in br] for br in massPlane.getParticleMasses(**xvalues)]
        if hasattr(txdata, 'flattenMassArray'):
            porig = txdata.flattenMassArray(mass)
        else:
            if hasattr(txdata,"removeUnits"):
                mass = txdata.removeUnits(mass)
            else:
                mass = removeUnits(mass,standardUnits)
            porig = txdata.flattenArray(mass)
        # print ( "porig=", porig )
        p=((numpy.matrix(porig)[0] - txdata.delta_x)).tolist()[0]
        P=numpy.dot(p,txdata._V)  ## rotated point
        extremePoints.append(P)
    #Limit extreme values by data:
    #print ( "points", txdata.tri.points )
    Mp = numpy.array(txdata.tri.points)
    extremePoints = numpy.array(extremePoints)
    newRanges = []
    steps = []
    #print ( "xvars=", xvars )
    for iaxis in range(len(xvars)):
        #print ( "iaxes=", iaxis )
        #print ( "Mp=", Mp )
        #print ( "Mp[:]=", Mp[:,iaxis] )
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
        allPoints.append([x for x in numpy.arange(vmin, vmax+dv/2., dv)])
    
    for pt in itertools.product(*allPoints):
        pt = list(pt)
        #Check if point is in the convexhull. If not, try another one
        if txdata.tri.find_simplex(pt) < 0:
            continue
        mass = getMassArrayFor(pt,massPlane,txdata,unit=None)
        #Round all masses (to be consistent with smodels)
        mass = [[round(m,1) for m in br] for br in mass]
        if not vertexChecker(mass):
            continue
        if massPlane.getXYValues(mass) is None:
            continue
        inside = False
        mass_unit = [[m*GeV for m in br] for br in mass]
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
    graph=f.Get("%s/exclusion_%s" % ( txname, axes) )
    filename2="/home/walten/git/smodels-database/8TeV/ATLAS/ATLAS-SUSY-2013-05/sms.root"
    f2=ROOT.TFile(filename2)
    print ("ls=",f2.ls() )
    graph2=f2.Get("%s/exclusion_%s" % ( "T2bb", axes) )
    print ("graph1,2=",graph,graph2 )

    pts = getPoints ( [graph, graph2], txname, axes, "[[[t+]],[[t-]]]", onshell=True, offshell=False )
    draw ( [graph, graph2] , pts )
