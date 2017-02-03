#!/usr/bin/env python

"""
.. module:: dataHandlerObjects
   :synopsis: Holds objects for reading and processing the data in different formats 

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys
import os
import ROOT
import logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)


class DataHandler(object):
    
    """
    Iterable class
    Super class used by other dataHandlerObjects.    
    Holds attributes for describing original data types and
    methods to set the data source and preprocessing the data
    """
    
    def __init__(self,dataLabel,coordinateMap,xvars):
        
        """
        initialize data-source attributes with None
        and allowNegativValues with False
        :param name: name as string
        :param dimensions: Dimensions of the data (e.g., for x,y,value, dimensions =2).
        :param coordinateMap: A dictionary mapping the index of the variables in the data and the
                          corresponding x,y,.. coordinates used to define the plane axes.
                          (e.g. {x : 0, y : 1, 'ul value' : 2} for a 3-column data,
                          where x,y,.. are the sympy symbols and the value key can be anything)
        :param xvars: List with x,y,.. variables (sympy symbols).
        """
        
        self.name = dataLabel
        self.dimensions = len(xvars)
        self.coordinateMap = coordinateMap
        self.xvars = xvars
        self.path = None
        self.files = []
        self.fileType = None
        self.objectName = None
        self.dataUrl = None
        self.index = None
        self.allowNegativValues = False
        self.dataset=None
        self._massUnit = 'GeV'
        self._unit = None  #Default unit
        
        if self.name == 'upperLimits' or self.name == 'expectedUpperLimits':
            self._unit = 'pb'
            
        #Consistency checks:
        if len(coordinateMap) != self.dimensions+1:
            logger.error("Coordinate map %s is not consistent with number of dimensions (%i)"
                         %(coordinateMap,self.dimensions))
            sys.exit()
        for xv in self.xvars:
            if not xv in coordinateMap:
                logger.error("Coordinate %s has not been defined in coordinateMap" %xv)
                sys.exit()
                       
                
    @property
    def unit(self):
        
        """
        :return: unit as string
        """
        
        return self._unit
        
    @unit.setter
    def unit(self, unitString):        
        """
        Set unit. For upper limits the default is 'pb'.
        For efficiency map the default is None. 
        :param unitString: 'fb','pb' or '', None
        """
        
        if not unitString:
            return
        
        if self.name != 'upperLimits' and self.name != 'expectedUpperLimits':
            logger.error("Units should only be defined for upper limits")
            sys.exit()              

        if unitString:           
            units = ['fb','pb']
            if not unitString in units:
                logger.error("Unit for upper limits must be in %s" %str(units))
                sys.exit()
            self._unit = unitString        

    def __nonzero__(self):
        
        """
        :returns: True if path and fileType is set, else False
        """
        
        if self.path and self.fileType:
            return True
        return False

    def __iter__(self):
        
        """
        gives the entries of the original upper limit histograms
        :yield: [x-value in GeV, y-value in GeV,..., value]
        """
        
        if not self.fileType:
            logger.error("File type for %s has not been defined" %self.path)
            sys.exit()
        
        for point in getattr(self,self.fileType)():
            if self.allowNegativValues:
                yield point
            #Check if the upper limit value is positive:
            else:
                #Just check floats in the point elements which are not variables
                values = [value for xv,value in point.items() if not xv in self.xvars]
                if self._positivValues(values):
                    yield point
    
    def mapPoint(self,point):
        """
        Convert a point in list format (e.g. [float,float,float])
        to a dictionary using the definitions in self.coordinateMap
        
        :param point: list with floats
        
        :return: dictionary with coordinates and value 
                 (e.g. {x : x-float, y : y-float, 'ul' : ul-float})
        """

        if len(point) < self.dimensions+1:
            logger.error("Data should have at least %i dimensions (%i dimensions found)" 
                         %(self.dimensions+1,len(point)))
            sys.exit()

        ptDict = {}
        #Return a dictionary with the values:
        for xvar,i in self.coordinateMap.items():
            #Skip variables without indices (relevant for exclusion curves)
            if i is None:
                continue  
            ptDict[xvar] = point[i]
        
        return ptDict
        
        
    def setSource(self, path, fileType, objectName = None, index = None):
        
        """set path and type of data source
        :param path: path to data file as string
        :param fileType: string describing type of file
        name of every public method of child-class can be used
        :param objectName: name of object stored in root-file or cMacro,
        :param index: index of object in listOfPrimitives of ROOT.TCanvas
        """
        
        if not os.path.isfile(path):
            logger.error("File %s not found" %path)
            sys.exit()
                
        self.path = path
        self.fileType = fileType
        self.objectName = objectName
        self.index = index        
        
    @property
    def massUnit(self):
        
        """
        :return: unit as string
        """
        
        return self._massUnit
        
    @massUnit.setter
    def massUnit(self, unitString):
        
        """
        Set unit for upper limits, default: 'pb'.
        If unitString is null, it will not set the property 
        :param unitString: 'GeV','TeV' or '', None
        """
        
        if unitString:           
            units = ['GeV','TeV']
            if not unitString in units:
                logger.error('Mass units must be in %s' %str(units))
                sys.exit()
            self._massUnit = unitString
            
    def _positivValues(self, values):
        
        """checks if values greater then zero
        :param value: float or integer
        :return: True if value >= 0 or allowNegativValues == True
        """   
        
        if self.allowNegativValues: return True        
        for value in values:
            if value < 0.0:
                logger.warning("Negative value %s in %s will be ignored"%(value,self.path))
                return False
        return True
                
    def txt(self):
        
        """
        iterable method
        preprocessing txt-files containing only columns with
        floats

        :yield: list with values as foat, one float for every column
        """
        
        txtFile = open(self.path,'r')
        content = txtFile.readlines()
        txtFile.close
        for line in content:
            #print(line)
            if line.find("#")>-1:
                line=line[:line.find("#")]
                if line=="":
                    continue
            try:
                values = line.split()
                if values==[]:
                    continue
            except:
                logger.error("Error reading file %s" %self.path)
                sys.exit()
            values = [value.strip() for value in values] 
            try:
                values = [float(value) for value in values]
            except:
                logger.error("Error evaluating values %s in file %s" %(values,self.path))
                sys.exit() 
                
                            
            yield self.mapPoint(values)  
    
    def root(self):
        
        """
        preprocessing root-files containing root-objects
        
        :return: ROOT-object
        """
        
        if not isinstance(self.objectName, str):
            logger.error("objectName for root file should be of string type and not %s"
                         %type(self.objectName))
            sys.exit()
            
        rootFile = ROOT.TFile(self.path)
        obj = rootFile.Get(self.objectName)
        if not obj:
            logger.error("Object %s not found in %s" %(self.objectName,self.path))
            sys.exit()
        if not isinstance(obj,ROOT.TGraph):
            obj.SetDirectory(0)
        rootFile.Close()
        
        for point in self._getPoints(obj):
            yield self.mapPoint(point)  

        
    def cMacro(self):
        
        """
        preprocessing root c-macros containing root-objects
        
        :return: ROOT-object
        """
        
        if not isinstance(self.objectName, str):
            logger.error("objectName for root file should be of string type and not %s"
                         %type(self.objectName))
            sys.exit()

        ROOT.gROOT.SetBatch()
        ROOT.gROOT.ProcessLine(".x %s" %self.path)
        try:
            limit = eval("ROOT.%s" %self.objectName)
        except:
            logger.error("Object %s not found in %s" %(self.objectName,self.path))
            sys.exit()
            
        for point in self._getPoints(limit):
            yield self.mapPoint(point)
            
    def canvas(self):
        
        """
        preprocessing root-file containing canvas with root-objects
        
        :return: ROOT-object
        """
        
        if not isinstance(self.objectName, str):
            logger.error("objectName for root file should be of string type and not %s"
                         %type(self.objectName))
            sys.exit()
        if not isinstance(self.index, int):
            logger.error("index for listOfPrimitives should be of integer type and not %s"
                         %type(self.index))
            sys.exit()
        rootFile = ROOT.TFile(self.path, 'r')
        canvas = rootFile.Get(self.objectName)
        if not canvas:
            logger.error("Object %s not found in %s" %(self.objectName,self.path))
            sys.exit()
        try:
            limit = canvas.GetListOfPrimitives()[self.index]
        except IndexError:
            logger.error("ListOfPrimitives %s has not index %s"
                          %(self.objectName,self.index))
            sys.exit()
        
        for point in self._getPoints(limit):
            yield self.mapPoint(point)
            
    def _getPoints(self,obj):
        
        """
        Iterable metod for extracting points from root histograms
        :param obj: Root object (THx or TGraph)
        :yield: [x-axes, y-axes,..., bin content]
        """
            
        if isinstance(obj,ROOT.TH1):
            return self._getHistoPoints(obj)
        elif isinstance(obj,ROOT.TGraph) or isinstance(obj,ROOT.TGraph2D):
            return self._getGraphPoints(obj)
        else:
            logger.error("ROOT object must be a THx or TGraphx object")
            sys.exit()
            
    def _getHistoPoints(self,hist):
        
        """
        Iterable metod for extracting points from root histograms
        :param hist: Root histogram object (THx)
        :yield: [x-axes, y-axes,..., bin contend]
        """
        
        if self.dimensions > 3:
            logger.error("Root histograms can not contain more than 3 axes. \
            (Data is defined as %i-th dimensional)" %self.dimensions)
            sys.exit()        
        
        #Check dimensions:
        if not self.dimensions == hist.GetDimension():
            logger.error("Data dimensions and histogram dimensions do not match")
            sys.exit()
        
        xAxis = hist.GetXaxis()
        xRange = range(1,xAxis.GetNbins() + 1)
        if self.dimensions > 1:
            yAxis = hist.GetYaxis()
            yRange = range(1,yAxis.GetNbins() + 1)
        if self.dimensions > 2:
            zAxis = hist.GetZaxis()
            zRange = range(1,zAxis.GetNbins() + 1)
            
        for xBin in xRange:
            x = xAxis.GetBinCenter(xBin)
            if self.dimensions == 1:
                ul = hist.GetBinContent(xBin)
                if ul == 0.: continue
                yield [x, ul]
            elif self.dimensions > 1:
                for yBin in yRange:
                    y = yAxis.GetBinCenter(yBin)
                    if self.dimensions == 2:
                        ul = hist.GetBinContent(xBin, yBin)
                        if ul == 0.: continue
                        yield [x, y, ul]
                    elif self.dimensions == 3:
                        for zBin in zRange:
                            z = zAxis.GetBinCenter(zBin)
                            ul = hist.GetBinContent(xBin, yBin, zBin)
                            if ul == 0.: continue
                            yield [x, y, z, ul]                     


    def _getGraphPoints(self,graph):
        
        """
        Iterable metod for extracting points from root TGraph objects
        :param graph: Root graph object (TGraphx)
        :yield: tgraph point
        """
        
        if self.dimensions >= 3:
            logger.error("Root graphs can not contain more than 2 axes. \
            (Data is defined as %i-th dimensional)" %self.dimensions)
            sys.exit()
            
        #Check dimensions:
        if self.dimensions == 1 and not isinstance(graph,ROOT.TGraph):
            logger.error("TGraph dimensions do not match data")
            sys.exit()
        if self.dimensions == 2 and not isinstance(graph,ROOT.TGraph2D):
            logger.error("TGraph dimensions do not match data")
            sys.exit()

        
        x, y, z = ROOT.Double(0.),ROOT.Double(0.),ROOT.Double(0.)
        for i in range(0, graph.GetN()):
            if isinstance(graph,ROOT.TGraph):
                graph.GetPoint(i, x, y)
                yield [float(x), float(y)]  
            elif isinstance(graph,ROOT.TGraph2D):
                graph.GetPoint(i, x, y, z)
                yield [float(x), float(y), float(z)]                      

        
class ExclusionHandler(DataHandler):
    
    """
    iterable class to hold and process exclusion curve data.    
    This Class is designed to iterate over the point of the
    exclusion line
    """
    
    def __init__(self,name,coordinateMap,xvars):
        
        """
        attributes 'sort' and 'reverse' are initialized with False
        :param name: name as string
        :param coordinateMap: A dictionary mapping the index of the variables in the data and the
                          corresponding x,y,.. coordinates used to define the plane axes.
                          (e.g. {x : 0, y : 1, 'ul value' : 2} for a 3-column data,
                          where x,y,.. are the sympy symbols and the value key can be anything)
        
        """
        
        #Exclusion curve always has dimensions = 1 (x-value)
        DataHandler.__init__(self,name,coordinateMap,xvars)  
        self.sort = False
        self.reverse = False
        self.dimensions = 1
        
    def __iter__(self):
        
        """
        Gives the point of the exclusion line
        if sort is set to True: points are sorted by x-values
        in increasing order
        if reverse is set to True: order of points is reversed
        :yield: [x-value, y-value]
        """
        
        points = []
        for point in getattr(self,self.fileType)():
            points.append(point)
        if self.sort:
            points = sorted(points, key = lambda x: x[0])
        if self.reverse:
            points = reversed(points)
        for point in points:
            yield point

            
    def svg(self):
        
        """
        iterable method for  processing files with coordinates in svg format.
        first line in file needs scaling information and the data
        has to be of the form x,y value.
        :yield: [x-value in GeV, y-value in GeV] 
        """
        
        #Check dimensions
        if self.dimensions != 1:
            logger.error("svg format only implemented for x,value data (1D)")
            sys.exit()

        #Open file:
        f = open(self.path, 'r')
        lines = f.readlines()
        f.close()
        xorig = 0
        yorig = 0
        if 'm' in lines[0].split()[0]:
            relative = True
        elif 'M' in lines[0].split()[0]:
            relative = False
        else:
            logger.error("Unknown svg format in %s:\n %s" 
                         %(self.path, lines[0].split()[0]))
            sys.exit()
        ticks = lines[0].split()
        xticks = []
        yticks = []
        for tick in ticks[1:]:
            if tick.split(':')[0][:1] == 'x':
                xticks.append([float(tick.split(':')[0][1:-3]),float(tick.split(':')[1])])
                if tick.split(':')[0][-3:] != 'GeV':
                    logger.error("Unknown mass unit in %s:\n %s" 
                                 %(self.path,tick.split(':')[0][-3:]))
                    sys.exit()

            elif tick.split(':')[0][:1] == 'y':
                yticks.append([float(tick.split(':')[0][1:-3]),float(tick.split(':')[1])])
                if tick.split(':')[0][-3:] != 'GeV':
                    logger.error("Unknown mass unit in %s:\n %s" 
                                 %(self.path,tick.split(':')[0][-3:]))
                    sys.exit()
            else:
                logger.error("Unknown axis in %s:\n %s" 
                                 %(self.path,tick.split(':')[0][:1]))
                sys.exit()
        if len(xticks) != 2 or len(yticks) != 2:
            logger.error("Unknown axis format %s" %self.path)
            sys.exit()    
        xGeV = (xticks[1][1]-xticks[0][1])/(xticks[1][0]-xticks[0][0])
        yGeV = (yticks[1][1]-yticks[0][1])/(yticks[1][0]-yticks[0][0])
        x0 = xticks[0][1] - xticks[0][0]*xGeV
        y0 = yticks[0][1] - yticks[0][0]*yGeV
        if relative:
            for l in lines[1:]:
                v = l.split(' ')
                xorig += float(v[0])
                yorig += float(v[1])
                x = (xorig-x0)/xGeV
                y = (yorig-y0)/yGeV
                yield self.mapPoint([x,y])
        else:
            for l in lines[1:]:
                v = l.split(' ')
                xorig = float(v[0])
                yorig = float(v[1])
                x = (xorig-x0)/xGeV
                y = (yorig-y0)/yGeV
                yield self.mapPoint([x,y])
                