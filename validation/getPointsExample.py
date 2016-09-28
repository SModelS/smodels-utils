#!/usr/bin/env python

import os,sys
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
sys.path.append(os.path.join(home,'smodels-utils'))
from smodels.tools.databaseBrowser import Browser
from validation.plotRanges import addQuotationMarks,generatePoints
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot
from smodels_utils.dataPreparation import vertexChecking
from smodels.tools.physicsUnits import GeV,fb
import copy
import numpy,math




def generatePointsB(Npts,minx,maxx,miny,maxy,txnameObjs,axes,origPlot,vertexChecker):


    print 'xmin,xmax=',minx,maxx
    print 'ymin,ymax=',miny,maxy
    
    #Create a dummy copy of a TxnameData object to hold all the data corresponding to the plane
    txdata = copy.deepcopy(txnameObjs[0].txnameData)
    txdata.dataTag = 'dummy'
    txdata._id = 'dummy'
    txdata._accept_errors_upto=0.05    
    txdata._V = None
    txdata.Mp = []
    txdata._data = []
    #Collects all points belonging to the plane:
    for tx in txnameObjs:
        print tx.txName
        for pt in tx.txnameData._data:
            mass = [[m.asNumber(GeV) for m in br] for br in pt[0]]
            if not origPlot.getXYValues(mass): continue
            txdata._data.append(pt)
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

    print len(txdata.Mp)
    for ipt,pt in enumerate(txdata.Mp): print pt,txdata._data[ipt][0][0]
    
    print 'xmin,xmax=',xmin,xmax,dx
    print 'ymin,ymax=',ymin,ymax,dy 
    
    points=[]
    massDimensions = [len(br) for br in txdata._data[0][0]] #Store the mass format 
    for i in numpy.arange(xmin, xmax+dx/2., dx):
        for j in numpy.arange(ymin, ymax+dy/2., dy):
            pt = [i,j] + [0.]*(txdata.full_dimensionality-2)  #Point in rotated space
            massFlat = numpy.dot(pt,numpy.transpose(txdata._V)) + txdata.delta_x #Flatten Mass
            massFlat = massFlat.tolist()[0]
            mass = [[massFlat.pop(0) for im in range(brdim)] for brdim in massDimensions] #Nested mass
            print 'i,j=',i,j
            print 'M=',mass
            print vertexChecker.getOffShellVertices(mass),origPlot.getXYValues(mass)            
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
            print 'inside=',inside
#             sys.exit()                
            if not inside:
                continue
            points.append([i,j])
#             points.append(origPlot.getXYValues(mass))
    return points,txdata
#     return points






browser = Browser(os.path.join(home,'smodels-database-simple'))

browser.selectExpResultsWith(id = 'ATLAS-CONF-2013-047', dataType = 'upperLimit')
exp = browser[0]
toff = [tx for tx in exp.getTxNames() if tx.txName == 'T5WWoff'][0]

axes = "2*Eq(mother,x)_Eq(inter0,0.5*x+0.5*y)_Eq(lsp,y)"
axes = "2*Eq(mother,x)_Eq(inter0,y)_Eq(lsp,60.)"
#Define x,y <-> masses mapping:
origPlot = OrigPlot.fromString(axes)
#Define vertexChecker (used to check for kinematically forbidden vertices):
vertexChecker = vertexChecking.VertexChecker(toff, 
                        addQuotationMarks(toff.constraint))

# pts = generatePoints(minx=135.,maxx=1500.,miny=0.,maxy=548.,dx=45.,dy=30.,txnameObjs=[toff],
#                         axes=axes,origPlot=origPlot,vertexChecker=vertexChecker)

# print '%i  points found for %s and axes %s' %(len(pts),toff.txName,axes)
Npts =300
minx,maxx,miny,maxy=160.,1800.,62.991,132.


pts,txdata = generatePointsB(Npts,minx,maxx,miny,maxy,txnameObjs=[toff],
                        axes=axes,origPlot=origPlot,vertexChecker=vertexChecker)

print '%i  points found for %s and axes %s' %(len(pts),toff.txName,axes)

import matplotlib.pyplot as plt
xvals = [pt[0] for pt in pts]
yvals = [pt[1] for pt in pts]
# txvals = [pt[0][0][0].asNumber(GeV) for pt in txdata._data]
# tyvals = [pt[0][0][-1].asNumber(GeV) for pt in txdata._data]
txvals = [pt[0] for pt in txdata.Mp]
tyvals = [pt[1] for pt in txdata.Mp]
# plt.plot(xvals,yvals,'ro')
plt.plot(xvals,yvals,'ro',txvals,tyvals,'bs')
plt.show()
