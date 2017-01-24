#!/usr/bin/env python

"""
.. module:: origDataObjects
   :synopsis: Holds objects for reading of data given by experimentalists 

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""

import sys
import os
import ROOT
from smodels_utils.dataPreparation.preparationHelper import Locker
import copy

class Orig(Locker):
    
    """Super class used by other origDataObjects
    holds attributes for describing original data types and
    methods to set the data source and preprocessing the data
    """
    
    
    infoAttr = []
    internalAttr = ['name','path', 'fileType', 'objectName',\
    'dataUrl', 'index', 'allowNegativValues', 'dataset',
    'observedN','expectedBG','bgError', 'percentage','_planeDimensions' ]
    
    def __init__(self,name):
        
        """
        initialize data-source attributes with None
        and allowNegativValues with False
        :param Name: name as string
        """
        
        self.name = name
        self.path = None
        self.fileType = None
        self.objectName = None
        self.dataUrl = None
        self.index = None
        self.allowNegativValues = False
        self.dataset=None
        self.percentage=False

    def setSource(self, path, fileType, objectName = None, index = None, dataset="data" ):
        
        """set path and type of data source
        :param path: path to data file as string
        :param fileType: string describing type of file
        name of every public method of child-class can be used
        :param objectName: name of object stored in root-file or cMacro,
        :param index: index of object in listOfPrimitives of ROOT.TCanvas
        :raise noFileError: if path does not exist
        """
        
        if not os.path.exists(path):
            Errors().noFile(path)
        self.path = path
        self.fileType = fileType
        self.objectName = objectName
        self.index = index
        self.dataset = dataset

    def setStatistics ( self, observedN, expectedBG, bgError ):
        """for efficiency maps set the statistical values
        """
        self.observedN = observedN
        self.expectedBG = expectedBG
        self.bgError = bgError

    def usePercentage ( self, value=True ):
        """ for efficiency maps, data is given in percentage 
            (value=True), or in fractions (value=False)
        """
        self.percentage = value 

    def _positivValues(self, values):
        
        """checks if values greater then zero
        :param value: float or integer
        :return: True if value >= 0 or allowNegativValues == True
        :raise negativValueError: if value < 0 and allowNegativValues == False
        """   
        
        if self.allowNegativValues: return True
        for value in values:
            if values < 0.0: 
                Errors().negativValue(values, path)
                return False
        return True
        
        
    def txt(self):
        
        """
        iterable method
        preprocessing txt-files containing only columns with
        floats
        :raise txtFormatError: if columns can not be split
        :raise valueError: if value can not be interpreted as float
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
                Errors().txtFormat(self.path, 'Orig')
            values = [value.strip() for value in values] 
            try:
                values = [float(value) for value in values]
            except:
               Errors().value(self.path) 
            yield values  

    def effi(self):
#        print("[origDataObjects] effi")
        # file format of fastlim!
        txtFile = open(self.path,'r')
        content = txtFile.readlines()[3:] ## omit the first three lines
        txtFile.close
        for line in content:
            #print(line)
            try:
                values = copy.deepcopy ( line.split() ) ## omit the last column
                if float(values[-2])<4*float(values[-1]):
 #                   print "[origDataObjects] Small value",values[-2],"+-",values[-1],"!"
#                    print "[origDataObjects] Will set to zero."
                    values[-2]="0."
#                print "values=",values
                values=values[:-1]
            except Exception as e:
                print ( "[origDataObjects]",e )
                Errors().effiFormat(self.path, 'Orig')
            values = [value.strip() for value in values] 
            try:
                values = [float(value) for value in values]
            except:
               Errors().value(self.path) 
            yield values  
    
    def root(self):
        
        """
        preprocessing root-files containing root-objects
        
        :raise rootObjectError: if type of objectName is not string
        :raise noRootObjectError: if object not exist or not found in file
        :return: ROOT-object
        """
        
        if not isinstance(self.objectName, str):
            Errors().rootObject(self.objectName,self.path)
            
        rootFile = ROOT.TFile(self.path)
        obj = rootFile.Get(self.objectName)
        if not obj: Errors().noRootObject(self.objectName,self.path)
        if not isinstance(obj,ROOT.TGraph):
            obj.SetDirectory(0)
        rootFile.Close()
        return obj
        
    def cMacro(self):
        
        """
        preprocessing root c-macros containing root-objects
        
        :raise rootObjectError: if type of objectName is not string
        :raise noRootObjectError: if object not exist or not found in file
        :return: ROOT-object
        """
        
        if not isinstance(self.objectName, str):
            Errors().rootObject(self.objectName,self.path)
        ROOT.gROOT.SetBatch()
        ROOT.gROOT.ProcessLine(".x %s" %self.path)
        try:
            return eval("ROOT.%s" %self.objectName)
        except:
            Errors().noRootObject(self.objectName,self.path)

    def canvas(self):
        
        """
        preprocessing root-file containing canvas with root-objects
        
        :raise rootObjectError: if type of objectName is not string
        :raise noRootObjectError: if canvas not exist or not found in file
        :raise indexTypeError: if index type is not integer
        :raise indexError: if index not in listOfPrimitives
        :return: ROOT-object
        """
        
        if not isinstance(self.objectName, str):
            Errors().rootObject(self.objectName, self.path)
        if not isinstance(self.index, int):
            Errors().indexType(self.index, self.path)
        rootFile = ROOT.TFile(self.path, 'r')
        canvas = rootFile.Get(self.objectName)
        if not canvas: Errors().noRootObject(self.objectName,self.path)
        try:
            return canvas.GetListOfPrimitives()[self.index]
        except IndexError:
            Errors().index(self.path, self.objectName, self.index)
    
    def __nonzero__(self):
        
        """
        :returns: True if path and fileType is set, else False
        """
        
        if self.path and self.fileType:
            return True
        return False            
 
 
class OrigLimit(Orig):
    
    """
    iterable class
    Holding original 2D upper limit histogram given by
    experimentalists
    public methods refer to different file-types 
    The files or objects containing the histogram as well as 
    the file type have to be set by using the method setSource
    of the parents class 
    This Class is designed to iterate over the entries of the
    upper limit histogram
    """
    
    plotableAttr = [] + Orig.infoAttr
    internalAttr = ['_unit', 'unit', ] + Orig.internalAttr
    
    def __init__(self,name):
        
        """
        initialize upper limit unit with 'pb'
        :param Name: name as string
        """
        
        Orig.__init__(self,name)
        self._unit = 'pb'
        
    @property
    def unit(self):
        
        """
        :return: unit as string
        """
        
        return self._unit
        
    @unit.setter
    def unit(self, unitString):
        
        """
        set unit for upper limits, default: 'pb' 
        :param unitString: 'fb' or 'pb'
        :raise unitError: if unit is not 'fb' or not 'pb'
        """
        
        units = ['fb','pb']
        if not unitString in units: Errors().unit(unitString)
        self._unit = unitString
        
    def __iter__(self):
        
        """
        gives the entries of the original upper limit histograms
        :yield: [x-value in GeV, y-value in GeV, upper limit in pb]
        """
        
        for point in getattr(self,self.fileType)():
            if self.unit == 'fb': point[-1] = point[-1]/1000.
            if not self._positivValues(point): continue
            yield point
            
    def txt(self):
        
        """
        iterable method
        processing txt-files containing only 3 columns with
        floats. The columns of the file have to contain the values
        for the following variables:
        1. column: x-value in GeV
        2. column: y-value in Gev
        3. column: upper limits in pb or fb 
        :raise txtFormatError: if file do not contain 3 columns 
        :yield: [x-value in GeV, y-value in GeV, upper limit in pb or fb] 
        """
        
        for point in Orig.txt(self):
            if not len(point) == 3:
                Errors().txtFormat(self.path, 'OrigLimit', 3)
            yield point
    
    def root(self):
        
        """
        iterable method
        processing root-files containing root 2D-histograms
        The bins of the histograms have to contain the upper
        limits in pb or fb; unit of x and y-axis: GeV
        :yield: [x-value in GeV, y-value in GeV, upper limit in pb or fb]
        """
        
        limit = Orig.root(self)
        for point in self._getPoints(limit):
            yield point
                
    def cMacro(self):
        
        """
        iterable method
        processing root c-macros containing root 2D-histograms
        The bins of the histograms have to contain the upper
        limits in pb or fb; unit of x and y-axis: GeV
        :yield: [x-value in GeV, y-value in GeV, upper limit in pb or fb]
        """
       
        limit = Orig.cMacro(self)
        for point in self._getPoints(limit):
            yield point
            
    def canvas(self):
        
        """
        iterable method
        processing root-files containing ROOT.TCanvas objects
        with 2D-histograms
        The bins of the histograms have to contain the upper
        limits in pb or fb; unit of x and y-axis: GeV
        :yield: [x-value, y-value, upper limit in pb or fb]
        """
        
        limit = Orig.canvas(self)
        for point in self._getPoints(limit):
            yield point
                
    def _getPoints(self,limit):
        
        """
        iterable metod
        processing root 2D-histograms
        :param limit: root 2D-histogram
        :yield: [x-axes, y-axes, bin contend]
        """
        
        xAxis = limit.GetXaxis()
        yAxis = limit.GetYaxis()
        xRange = range(1,xAxis.GetNbins() + 1)
        yRange = range(1,yAxis.GetNbins() + 1)
        for xBin in xRange:
            x = xAxis.GetBinCenter(xBin)
            for yBin in yRange:
                y = yAxis.GetBinCenter(yBin)
                ul = limit.GetBinContent(xBin, yBin)
                if ul == 0.: continue
                yield [x, y, ul]
        

class OrigEfficiencyMap(Orig):
    
    """
    iterable class
    Holding original 2D efficiency maps  given by
    experimentalists
    public methods refer to different file-types 
    The files or objects containing the efficiency maps as well as 
    the file type have to be set by using the method setSource
    of the parents class 
    This Class is designed to iterate over the entries of the
    efficiency maps
    """
    
    plotableAttr = [] + Orig.infoAttr
    internalAttr = [] + Orig.internalAttr
    
    def __init__(self,name):
        
        """
        :param Name: name as string
        """
        
        Orig.__init__(self,name)
        
    def __iter__(self):
        
        """
        gives the entries of the original efficiency map
        :yield: [x-value in GeV, y-value in GeV,..., efficiency]
        """
        if self.fileType==None:
            raise StopIteration()
        
        for point in getattr(self,self.fileType)():
            if not self._positivValues(point): continue
            if self.percentage:
                point[-1]=point[-1]/100.
            yield point

    def __len__(self):
        """ count how many points """
        x=0
        for point in self:
            if not self._positivValues(point): continue
            x+=1
        return x

    def txt(self):
        
        """
        iterable method
        processing txt-files containing only 3 columns with
        floats. The columns of the file have to contain the values
        for the following variables:
        1. column: x-value in GeV
        2. column: y-value in Gev
    ...
        n. column: efficiency
        :raise txtFormatError: if file do not contain the right number of columns 
        :yield: [x-value in GeV, y-value in GeV,... efficiency] 
        """
        
        for point in Orig.txt(self):
            if not len(point) == self._planeDimensions+1:
                Errors().txtFormat(self.path, 'OrigEfficiencyMap', self._planeDimensions+1)
            yield point

    def effi(self):
        
        for point in Orig.effi(self):
            if not len(point) in [3, 4]:
                Errors().effiFormat(self.path, 'OrigEfficiencyMap', 3)
            yield point

    
    def root(self):
        
        """
        iterable method
        processing root-files containing root 2D-histograms
        The bins of the histograms have to contain the
        efficiencies; unit of x and y-axis: GeV
        :yield: [x-value in GeV, y-value in GeV,..., efficiency]
        """
        
        limit = Orig.root(self)
        for point in self._getPoints(limit):
            yield point
                
    def cMacro(self):
        
        """
        iterable method
        processing root c-macros containing root 2D-histograms
        The bins of the histograms have to contain the 
        efficiencies; unit of x and y-axis: GeV
        :yield: [x-value in GeV, y-value in GeV,..., efficiency]
        """
       
        limit = Orig.cMacro(self)
        for point in self._getPoints(limit):
            yield point
            
    def canvas(self):
        
        """
        iterable method
        processing root-files containing ROOT.TCanvas objects
        with 2D-histograms
        The bins of the histograms have to contain the 
        efficiencies; unit of x and y-axis: GeV
        :yield: [x-value, y-value, efficiency]
        """
        
        limit = Orig.canvas(self)
        for point in self._getPoints(limit):
            yield point
                
    def _getPoints(self,limit):
        
        """
        iterable metod
        processing root 2D-histograms
        :param limit: root 2D-histogram
        :yield: [x-axes, y-axes, bin contend]
        """
        
        naxis = self._planeDimensions
        xAxis = limit.GetXaxis()
        yAxis, zAxis = None,None
        if naxis > 1:
            yAxis = limit.GetYaxis()
        if naxis > 2:
            zAxis = limit.GetYaxis()
            xRange = range(1,xAxis.GetNbins() + 1)
        if yAxis:
            yRange = range(1,yAxis.GetNbins() + 1)
        if zAxis:
            zRange = range(1,zAxis.GetNbins() + 1)
        for xBin in xRange:
            x = xAxis.GetBinCenter(xBin)            
            if not yAxis:
                eff = limit.GetBinContent(xBin)
                if eff == 0.: continue
                yield [x,eff]
                continue
            
            for yBin in yRange:
                y = yAxis.GetBinCenter(yBin)
                if not zAxis:
                    eff = limit.GetBinContent(xBin, yBin)
                    if eff == 0.: continue
                    yield [x, y, eff]
                    continue
 
                for zBin in zRange:
                    z = zAxis.GetBinCenter(zBin)
                    eff = limit.GetBinContent(xBin, yBin, zBin)
                    if eff == 0.: continue
                    yield [x, y, z, eff]

        
class OrigExclusion(Orig):
    
    """
    iterable class
    Holding original exclusion line given by
    experimentalists
    public methods refer to different file-types 
    The files or objects containing the exclusion line as well as 
    the file type have to be set by using the method setSource
    of the parents class 
    This Class is designed to iterate over the point of the
    exclusion line
    """
    
    infoAttr = [] + Orig.infoAttr
    internalAttr = ['sort', 'reverse'] + Orig.internalAttr
    
    def __init__(self,name):
        
        """
        attributes 'sort' and 'reverse' are initialized with False
        :param Name: name as string
        """
        
        Orig.__init__(self,name)
        self.sort = False
        self.reverse = False
        
    def __iter__(self):
        
        """
        gives the point of the exclusion line
        if sort is set to True: points are sorted by x-values
        in increasing order
        if reverse is set to True: order of points is reversed
        :yield: [x-value in GeV, y-value in GeV]
        """
        
        points = []
        for point in getattr(self,self.fileType)():
            points.append(point)
        if self.sort:
            points = sorted(points, key = lambda x: x[0])
        if self.reverse:
            points = reversed(points)
        for point in points:
            if not self._positivValues(point): continue
            yield point

    def txt(self):
        
        """
        iterable method
        processing txt-files containing only 2 columns with
        floats. The columns of the file have to contain the values
        for the following variables:
        1. column: x-value in GeV
        2. column: y-value in Gev
        :raise txtFormatError: if file do not contain 2 columns 
        :yield: [x-value in GeV, y-value in GeV] 
        """
        
        for point in Orig.txt(self):
            if not len(point) == 2:
                Errors().txtFormat(self.path, 'OrigExclusion', 2)
            yield point
            
    def svg(self):
        
        """
        iterable method
        processing files with coordinates in svg format.
        first line in file needs scaling information
        :raise unknownSvgError: if svg format is not 'm' or not 'M'
        :raise unknownMassUnitError: if mass unit is not 'GeV'
        :raise unknownAxisError: if axis is not 'x' or not 'y'
        :raise axesInformationError: if more then 2 axes are given
        :yield: [x-value in GeV, y-value in GeV] 
        """

        f = open(self.path, 'r')
        lines = f.readlines()
        f.close()
        n = len(lines)
        xorig = 0
        yorig = 0
        if 'm' in lines[0].split()[0]:
            relative = True
        elif 'M' in lines[0].split()[0]:
            relative = False
        else:
            Errors().unknownSvg(self, self.path, lines[0].split()[0])
        ticks = lines[0].split()
        xticks = []
        yticks = []
        for tick in ticks[1:]:
            if tick.split(':')[0][:1] == 'x':
                xticks.append([float(tick.split(':')[0][1:-3]),float(tick.split(':')[1])])
                if tick.split(':')[0][-3:] != 'GeV':
                    Errors().unknownMassUnit(self.path, tick.split(':')[0][-3:])
            elif tick.split(':')[0][:1] == 'y':
                yticks.append([float(tick.split(':')[0][1:-3]),float(tick.split(':')[1])])
                if tick.split(':')[0][-3:] != 'GeV':
                    Errors().unknownMassUnit(self.path, tick.split(':')[0][-3:])
            else:
                Errors().unknownAxis(self, self.path, tick.split(':')[0][:1])
        if len(xticks) != 2:
            Errors().axesInformation(self, self.path)
        if len(yticks) != 2:
            Errors().axesInformation(self, self.path)    
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
                yield [x,y]
        else:
            for l in lines[1:]:
                v = l.split(' ')
                xorig = float(v[0])
                yorig = float(v[1])
                x = (xorig-x0)/xGeV
                y = (yorig-y0)/yGeV
                yield [x,y]

                
    def root(self):
        
        """
        iterable method
        processing root-files containing ROOT.TGraphs
        unit of x and y-axis have to be GeV
        :yield: [x-value in GeV, y-value in GeV]
        """
        
        exclusion = Orig.root(self)
        for point in self._getPoints(exclusion):
            yield point
                
    def cMacro(self):
        
        """
        iterable method
        processing root c-macros containing ROOT.TGraphs
        unit of x and y-axis have to be GeV
        :yield: [x-value in GeV, y-value in GeV]
        """
       
        exclusion = Orig.cMacro(self)
        for point in self._getPoints(exclusion):
            yield point
    
    def canvas(self):
        
        """
        iterable method
        processing root-files containing ROOT.TCanvas objects
        with ROOT.TGraphs
        The bins of the histograms have to contain the 
        unit of x and y-axis have to be GeV
        :yield: [x-value in GeV, y-value in GeV]
        """
        
        exclusion = Orig.canvas(self)
        for point in self._getPoints(exclusion):
            yield point
    
    def _getPoints(self, graph):
        
        """
        iterable metod
        processing ROOT.TGraph
        :param graph: ROOT.TGraph
        :yield: [x-axes, y-axes]
        """
        
        x, y = ROOT.Double(0.),ROOT.Double(0.)
        for i in range(0, graph.GetN()):
            graph.GetPoint(i, x, y)
            yield [float(x), float(y)]
        
        
class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def txtFormat(self,filePath, className, columns = ''):
        
        m = self._starLine
        m = m + 'wrong content in txt file: %s!!\n'  %filePath
        m = m + 'file content for a txt file readable by %s should be:\n' %className
        m = m + '%s columns with numbers divided by a split() character' %columns
        m = m + self._starLine
        print(m)
        sys.exit()

    def effiFormat(self,filePath, className, columns = ''):
        
        m = self._starLine
        m = m + 'wrong content in effi file: %s!!\n'  %filePath
        m = m + 'file content for an effi file readable by %s should be:\n' %className
        m = m + '%s columns with numbers divided by a split() character' %columns
        m = m + self._starLine
        print(m)
        sys.exit()
        
        
    def value(self, filePath):
        
        m = self._starLine#
        m = m + 'valueError in file: %s\n' %filePath
        m = m + 'cant convert value to float'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def rootObject(self, objectName, filePath):
        
        m = self._starLine#
        m = m + 'objectError in file: %s\n' %filePath
        m = m + 'objectName for root file should be of string type\n'
        m = m + 'got %s' %objectName
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def noRootObject(self, objectName, filePath):
        
        m = self._starLine#
        m = m + 'objectError in file: %s\n' %filePath
        m = m + 'file contain no root object called %s\n' %objectName
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def indexType(self, index, filePath):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'index for listOfPrimitives should be of integer type\n'
        m = m + 'got %s' % index
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def unit(self, unitString):
        
        m = self._starLine#
        m = m + "unit for limits must be 'fb' or 'pb'\n"
        m = m + 'got %s' %unitString
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def unknownSvg(self, filePath, svg):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'unknown %s (svg)' %svg
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def unknownMassUnit(self, filePath, massUnit):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'unknown mass unit: %s\n' %massUnit
        m = m + 'mass unit have to be: GeV' 
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def unknownAxis(self, filePath, axis):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'unknown axis: %s\n' %axis
        m = m + 'mass unit have to be: x or y'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def axesInformation(self, filePath):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %filePath
        m = m + 'too much/less information about one of the axes!'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def noFile(self, path):

        m = self._starLine
        m = m + 'no file: : %s\n' %path
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def negativValue(self, values, path):
    
        m = m + 'skip negativ value: %s\n' %value
        m = m + 'in orig data file: %s' %path
        print(m)
        
    def index(self ,path ,objectName, index):
        
        m = self._starLine#
        m = m + 'indexError in file: %s\n' %path
        m = m + 'listOfPrimitives of canvas with name: %s\n' %objectName
        m = m + 'have not index %s' %index
        m = m + self._starLine
        print(m)
        sys.exit()
   
        

        
