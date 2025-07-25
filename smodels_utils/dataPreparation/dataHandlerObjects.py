#!/usr/bin/env python3

"""
.. module:: dataHandlerObjects
   :synopsis: Holds objects for reading and processing the data in different formats

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

__all__ = [ "ExclusionHandler", "DataHandler" ]

import ctypes
import sys
import os
import logging
import math
import numpy as np
from typing import List, Generator

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

from sympy import var
x,y,z = var('x y z')

# h = 4.135667662e-15 # in GeV * ns
hbar = 6.582119514e-16 # in GeV * ns

## for debugging, if set to true, allow for the acceptance files
## to have multiple entries for the same mass point. that is obviously a bug,
## so use this feature with great care
allowMultipleAcceptances = False

errorcounts = { "pathtupleerror": False, "smallerthanzero": False,
                "wildcards": False, "trimyaxis": False, "trimxaxis": False,
                "trimzaxis": False, "zerovalue": False }

suppressWarnings = { "objectname": False }

def _Hash ( lst ): ## simple hash function for our masses
    ret=0.
    for l in lst:
        ret=100000*ret+l
    return ret

# maximum number of entries before we trim
# (given that allowTrimming is true, see below)
max_nbins = 12000
allowTrimming=True ## allow big grids to be trimmed down
trimmingFactor = [ 2 ] ## the factor by which to trim

fileCache  = {} ## a file cache for input files, to speed things up
pointsCache = {}

class DataHandler(object):

    """
    Iterable class
    Super class used by other dataHandlerObjects.
    Holds attributes for describing original data types and
    methods to set the data source and preprocessing the data
    """
    hasWarned = {}

    def __init__(self,dataLabel,coordinateMap,xvars, txName = None ):

        """
        initialize data-source attributes with None
        and allowNegativeValues with False
        :param name: name as string
        :param dimensions: Dimensions of the data (e.g., for x,y,value, dimensions=2).
        :param coordinateMap: A dictionary mapping the index of the variables
              in the data and the corresponding x,y,.. coordinates used to define the
              plane axes.  (e.g. {x : 0, y : 1, 'ul value' : 2} for a 3-column data,
              where x,y,.. are the sympy symbols and the value key can be anything)
        :param xvars: List with x,y,.. variables (sympy symbols).
        :param txName: the txname, for debugging only
        """

        self.txName = txName
        self.name = dataLabel
        varsUsed = set()
        for expr in xvars:
            for i in [ "x", "y", "z" ]:
                if i in str(expr):
                    varsUsed.add ( i )
        self.dimensions = len(varsUsed)
        self.coordinateMap = coordinateMap
        self.xvars = xvars
        # so we dont need to parse them so often
        self.path = None
        self.files = []
        self.fileType = None
        self.objectName = None
        self.dataUrl = None
        self.index = None
        self.allowNegativeValues = False
        self.dataset=None
        self._massUnit = 'GeV'
        self._unit = None  #Default unit
        self._rescaleFactors = None

        if self.name == 'upperLimits' or self.name == 'expectedUpperLimits':
            self._unit = 'pb'

        newCoordinateMap = {} # take out entries with 'None'
        for k,v in coordinateMap.items():
            if v != None:
                newCoordinateMap[k]=v
        if len(coordinateMap) != self.dimensions+1 and \
            len(newCoordinateMap) == self.dimensions+1:
                coordinateMap = newCoordinateMap

        nCoordinateMap = 0 ## determine length of coordinate map
        for k,v in coordinateMap.items():
            if k!="constraint":
                nCoordinateMap+=1

        #Consistency checks:
        if nCoordinateMap != self.dimensions+1:
            logger.error( f"Coordinate map {coordinateMap} (dim {nCoordinateMap}) is not consistent with number of dimensions ({self.dimensions+1}) in {dataLabel}" )
            # sys.exit()
        for xy in { "x": x, "y": y, "z": z }.items(): # allow also strings
            if xy[0] in coordinateMap:
                coordinateMap[xy[1]] = coordinateMap[xy[0]]
                coordinateMap.pop ( xy[0] )
        for xv in self.xvars:
            if not xv in coordinateMap:
                try:
                    fl = float(str(xv)) ## if we can cast, its all good
                except ValueError as e:
                    if xv in [ x, y, z ]:
                        logger.error( f"Coordinate {xv}, {type(xv)} has not been defined in coordinateMap" )
                        logger.error ( f"Maybe you wrote '{xv}' instead of {xv} (i.e. a string instead of a sympy Symbol?)" )
                    # sys.exit()


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
        For exclusion lines it defines the units on the x and y axes.
        :param unitString: 'fb','pb' or '', None
        """

        if not unitString:
            return

        if "fficienc" in self.name:
            if self.unit not in [ "%s", None, "perc", "percent", "percentage" ]:
                logger.error("Units should not be defined for efficiency maps" )
                sys.exit()
        if unitString in [ "perc", "percent", "percentage" ]:
            unitString = "%"

        if unitString:
            units = ['/10000','%','fb','pb',('GeV','GeV'),('GeV','ns'),('ns','GeV'),('GeV','X:60'), ( 'GeV','X:60','fb'), ( 'GeV','X:60','pb' ), ( 'GeV', 'ns', '/1' ), ( 'GeV', 'ns', '%' ), ( 'GeV', 'ns', '/10000' ) ]
            if type(unitString) == str and unitString.startswith("/"):
                self._unit = unitString
                return
            if type(unitString) == str and unitString.startswith("*"):
                self._unit = unitString
                return
            if not unitString in units:
                logger.error(f"Units must be in {str(units)}, not {unitString}" )
                sys.exit()
            self._unit = unitString

    def loadData(self):
        """
        Loads the data and stores it in the data attribute
        """

        if not self.fileType:
            logger.error( f"File type for {self.path} has not been defined" )
            sys.exit()

        if self.fileType == "csv" and type(self.path) == tuple:
            if errorcounts["pathtupleerror"] == False:
                print ( f"[dataHandlerObjects] warning: {self.path} is a tuple. will switch from csv to mcsv as your dataformat." )
                errorcounts["pathtupleerror"]  = True
            self.fileType = "mcsv"

        if self.fileType == "direct":
            return

        #Load data
        self.data = []
        strictlyPositive = False
        if self._unit in [ "fb", "pb" ]:
            strictlyPositive = True
        if not hasattr ( self, self.fileType ):
            logger.error ( f"Format type '{self.fileType}' is not defined. Try either one of 'root', 'csv', 'txt', 'embaked', 'mscv', 'effi', 'cMacro', 'canvas', 'svg', 'pdf', 'direct' instead. " )
            sys.exit(-1)
        for point in getattr(self,self.fileType)():
            ptDict = self.mapPoint(point) #Convert point to dictionary
            if self.allowNegativeValues:
                self.data.append(ptDict)
            #Check if the upper limit value is positive:
            else:
                #Just check floats in the point elements which are not variables
                values = [value for xv,value in ptDict.items() if not xv in self.xvars]
                if self._positiveValues(values, strictlyPositive = strictlyPositive ):
                    self.data.append(ptDict)

    def __nonzero__(self):

        """
        :returns: True if contains data
        """

        if hasattr(self,'data') and len(self.data):
            return True

        return False

    def __iter__(self):

        """
        gives the entries of the original upper limit histograms
        :yield: [x-value in GeV, y-value in GeV,..., value]
        """

        for point in self.data:
            yield point

    def __getitem_(self,i):
        """
        Returns the point located at i=x.

        :param i: Integer specifying the point index.

        :return: Point in dictionary format.
        """

        return self.data[i]

    def __len_(self):
        """
        Returns the data length.

        :return: Integer (length)
        """

        return len(self.data)

    def getX(self):

        """
        Iterates over the x,y,.. values for the data
        :yield: {x : x-value, y: y-value,...}
        """

        for point in self.data:
            xDict = {}
            for key,val in point.items():
                if not key in self.xvars:
                    continue
                xDict[str(key)] = val
            yield xDict

    def getValues(self):

        """
        Iterates over the values for the data (e.g. upper limit for upperLimits,
        efficiency for efficiencyMap,...)
        :yield: {'value-keyword' : value}
        """

        for point in self.data:
            vDict = {}
            for key,val in point.items():
                if key in self.xvars:
                    continue
                vDict[str(key)] = val
            yield vDict

    def getPointsWith(self,**xvals):
        """
        Returns point(s) with the properties defined by input.
        (e.g. x=200., y=100., will return all points with these values)

        :param xvals: Values for the variables (e.g. x=x-float, y=y-float,...)

        :return: list of points which satisfy the requirements given by xvals.
        """

        points = []
        #Convert xvals from dictionary to sympy vars:
        varDict = dict([[str(v),v] for v in self.xvars])
        xv = dict([[eval(k,varDict),v] for k,v in xvals.items()])
        for point in self.data:
            addPoint = True
            for key,val in xv.items():
                if not key in point:
                    logger.error(f"Key {key} not allowed for data")
                    sys.exit()
                if point[key] != val:
                    addPoint = False
                    break

            if addPoint:
                points.append(point)

        return points

    def reweightBy(self,data):
        """
        Reweight the values in self by the values in data.
        If data is a float, apply the same rescaling for all points.
        If data is a DataHandler object, multiply the value for the points in self
        by the values for the same points in data. Mainly intended to be
        used to rescale efficiencies by acceptances or to rescale the whole data.

        :param data: float or DataHandler object
        """

        if isinstance(data,float):
            for i,value in enumerate(self.getValues()):
                factor = data
                newvalue = dict([[key,val*factor] for key,val in value.items()])
                self.data[i].update(newvalue)
        elif isinstance(data,DataHandler):
            for i,xvals in enumerate(self.getX()):
                #Get the point in the data which matches the one in self
                pts = data.getPointsWith(**xvals)
                if pts and len(pts)>1 and allowMultipleAcceptances:
                    logger.error(f"More than one point in reweighting data matches point {xvals}")
                    logger.error("But allowMultipleAcceptances is set to true, so will choose first value!" )
                    pts = [ pts[0] ]
                if not pts:
                    continue
                elif len(pts) > 1:
                    logger.error(f"More than one point in reweighting data matches point {xvals}")
                    logger.error("(If you want to allow for this happen, then set dataHandlerObjects.allowMultipleAcceptances = True)" )
                    sys.exit()
                else:
                    pt = pts[0]
                    oldpt = self.data[i]  #Old point
                    for key,val in oldpt.items():
                        if str(key) in xvals.keys() or not key in pt:
                            continue
                        factor = pt[key]
                        oldpt[key] = oldpt[key]*factor  #Rescale values which do not appear in xvals
                    self.data[i] = oldpt #Store rescaled point


    def mapPoint(self,point):
        """
        Convert a point in list format (e.g. [float,float,float])
        to a dictionary using the definitions in self.coordinateMap

        :param point: list with floats

        :return: dictionary with coordinates and value
                 (e.g. {x : x-float, y : y-float, 'ul' : ul-float})
        """

        if len(point) < self.dimensions: # +1:
            logger.error(f"{self.name} should have at least {self.dimensions+1} dimensions ({len(point)} dimensions found)" )
            sys.exit()

        ptDict = {}
        #Return a dictionary with the values:
        for xvar,i in self.coordinateMap.items():
            #Skip variables without indices (relevant for exclusion curves)
            if i is None:
                continue
            if i >= len(point):
                logger.error( f"asking for {i}th element of {point} in {self.path}")
                logger.error( f"coordinate map is {self.coordinateMap}" )
            ptDict[xvar] = point[i]

        return ptDict

    def setSource(self, path, fileType, objectName = None,
                  index = None, unit = None, scale = None, **args ):

        """set path and type of data source
        :param path: path to data file as string
        :param fileType: string describing type of file
        name of every public method of child-class can be used
        :param objectName: name of object stored in root-file or cMacro, or string
            appearing in title of csv table in a multi-table csv file.
            If it is a list, then the elements of the list get aggregated.
        :param index: index of object in listOfPrimitives of ROOT.TCanvas
        :param unit: string defining unit. If None, it will use the default values.
        :param scale: float to re-scale the data.
        """
        self.args = args
        self.path = path
        self.fileType = fileType
        self.objectName = objectName
        self.index = index
        if fileType == "direct":
            if type(path) in [ float, int ]: ## 1d exclusions can be given directly
                self.data = [ [ path ] ]
            elif type(path) in [ list ]:
                self.data = [ path ]
            else:
                logger.error ( f"direct data source but cannot recognize data {path}" )
                sys.exit()

        elif type(path) not in [ tuple, list ] and not os.path.isfile(path):
            logger.error( f"File {path} not found" )
            if type(self.dataUrl ) == str and os.path.basename(path) == os.path.basename ( self.dataUrl ):
                logger.info( "But you supplied a dataUrl with same basename, so I try to fetch it" )
                import requests
                r = requests.get ( self.dataUrl )
                if not r.status_code == 200:
                    logger.error ( f"retrieval failed: {r.status_code}" )
                    sys.exit()
                with open ( path, "wb" ) as f:
                    f.write ( r.content )
                    f.close()
            else:
                sys.exit()

        if unit:
            self.unit = unit

        self.loadData()
        if scale:
            self.reweightBy(scale)

    @property
    def massUnit(self):

        """
        :return: unit as string
        """

        return self._massUnit

    @massUnit.setter
    def massUnit(self, unitString):

        """
        Set unit for masses, default: 'GeV'.
        If unitString is null, it will not set the property
        :param unitString: 'GeV','TeV' or '', None
        """

        if unitString:
            units = ['GeV','TeV']
            if not unitString in units:
                logger.error(f'Mass units must be in {str(units)}')
                sys.exit()
            self._massUnit = unitString

    def _positiveValues(self, values, strictlyPositive = False ):

        """checks if values greater then zero
        :param value: float or integer
        :param strictlyPositive: if true, then dont allow zeroes either
        :return: True if value greater (or equals) 0 or allowNegativeValues == True
        """

        if self.allowNegativeValues:
            return True
        for value in values:
            if not isinstance ( value, ( np.floating, float, int, np.integer) ):
#            if type(value) not in [ float, np.float64, int, np.int32, np.int64, np.int16, np.float32, np.float16 ]:
               #  print ( f"[dataHandlerObjects] value {value}, {type(value)} cannot be cast to float." )
                if type(value) == str and "{" in value:
                    print ( "[dataHandlerObjects] did you try to parse an embaked file as a csv file maybe?" )
                    sys.exit(-1)
            if type(value) in [ float ] and value < 0.0:
                logger.warning(f"Negative value {value} in {self.path} will be ignored")
                return False
            if value == 0.0 and strictlyPositive:
                if not errorcounts["zerovalue"]:
                    logger.warning(f"Zero value {value} in {self.path} will be ignored")
                    errorcounts["zerovalue"]=True
                return False
        return True

    def txt(self):

        """
        iterable method
        preprocessing txt-files containing only columns with
        floats

        :yield: list with values as float, one float for every column
        """

        txtFile = open(self.path,'r')
        content = txtFile.readlines()
        txtFile.close
        lines = []
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
                logger.error(f"Error reading file {self.path}")
                sys.exit()
            values = [value.strip() for value in values]
            try:
                values = [float(value) for value in values]
            except:
                logger.error(f"Error evaluating values {values} in file {self.path}")
                sys.exit()

            lines.append ( values )
        x,y = var('x y')
        xcoord, ycoord = self.coordinateMap[x], self.coordinateMap[y]
        ## FIXME should we ever sort here?
        # lines.sort( key= lambda x: x[xcoord]*1e6+x[ycoord] )
        if len(lines) > max_nbins:
            trimmingFactor[0] = int ( round ( math.sqrt ( len(lines) / 6000. ) ) )
            trimmingFactor[0] = trimmingFactor[0]**2
            newyields = []
            for cty,y in enumerate ( lines ):
                if cty % trimmingFactor[0] == 0:
                    newyields.append ( y )
            logger.warn ( f"trimmed down csv file '{self.name}' from {len(lines)} to {len(newyields)}" )
            lines = newlines
        for line in lines:
            yield line

    def pdf(self):
        """
        iterable method
        preprocessing pdf-files
        floats

        :yield: list with values as float, one float for every column
        """
        from .PDFLimitReader import PDFLimitReader
        if self.index == None or type(self.index) != str:
            print ( "[dataHandlerObjects] index is None. For pdf files, use index to specify axis ranges, e.g. index='x[100,260];y[8,50];z[.1,100,true]'" )
            sys.exit(-1)
        tokens = self.index.split(";")
        ## boundaries in the plot!
        lim = { "x": ( 150, 1200 ), "y": ( 0, 600 ), "z": ( 10**-3, 10**2 ) }
        logz = True ## are the colors in log scale?
        yIsDelta = False
        for cttoken,token in enumerate(tokens):
            axis = token[0]
            lims = token[1:].replace("[","").replace("]","")
            lims = lims.split(",")
            hasMatched = False
            if len(lims)>2:
                if "delta" in lims[2].lower() and cttoken == 1:
                    yIsDelta = True
                    hasMatched = True
                if lims[2].lower() in [ "log", "true" ]:
                    logz = True
                    hasMatched = True
                elif lims[2].lower() in [ "false", "nolog" ]:
                    logz = False
                    hasMatched = True
                if not hasMatched:
                    print ( f"Error: do not understand {lims[2]}. I expected log or nolog or delta (though I accept delta only in y coord)" )
            lims = tuple ( map ( float, lims[:2] ) )
            lim[axis]=lims
        print(f"[dataHandlerObjects] limits {lim}" )

        data =  {
            'name': self.path.replace(".pdf",""),
            'x':{'limits': lim["x"]},
            'y':{'limits': lim["y"]},
            'z':{'limits': lim["z"], 'log':logz },
            }
        r = PDFLimitReader( data )
        logger.warn ( "This is just a prototype of a PDF reader!" )
        logger.warn ( f"{len(r.main_shapes)} shapes in pdf file." )
        import numpy
        data = []
        lastz = float("inf")
        dx = r.deltax
        while dx < 15.:
            dx = 2*dx
        dy = r.deltay
        while dy < 15.:
            dy = 2*dy
        for xi in numpy.arange ( lim["x"][0]+.5*r.deltax, lim["x"][1]+1e-6, dx ):
            for yi in numpy.arange ( lim["y"][0]+.5*r.deltay, lim["y"][1]+1e-6, dy ):
                if yi > xi:
                    continue
                z = r.get_limit ( xi, yi )
                if z == None:
                    continue
                #if z == lastz:
                #    continue
                # print ( "xyz", xi, yi, z )
                if yIsDelta:
                    data.append ( ( xi, xi-yi, z ) )
                else:
                    data.append ( ( xi, yi, z ) )
                lastz = z
        for d in data:
            yield d

    def extendDataToZero ( self, yields ):
        """ if self.args['extended_to_massless_lsp'],
            then extend the data to massless lsps """
        # print ( "extend!", self.args )
        if not "extend_to_massless_lsp" in self.args or \
                self.args["extend_to_massless_lsp"] != True:
            return
        if self.name not in [ "expectedUpperLimits", "upperLimits" ]:
            return
        arr = np.array ( yields )[::,-2]
        minLSP = min ( arr )
        if minLSP > 25.:
            # only do it when its not big
            logger.warn ( f"will not extend to mlsp = 0 since minlsp = {minLSP}" )
            return
        add = []
        for y in yields:
            if abs(y[-2]-minLSP)<1e-6:
                tmp = y[:-2]+[0]+y[-1:]
                add.append ( tmp )
        logger.info ( f"adding {len(add)} points to extend to mlsp=0" )
        for a in add:
            yields.append ( a )
        yields.sort()
        return

    def direct(self):
        """ value was given directly """
        for d in self.data:
            yield d
        # return

    def csv(self):
        """
        iterable method
        preprocessing csv-files
        floats

        :yield: list with values as float, one float for every column
        """
        import csv

        waitFor = None
        if hasattr ( self, "objectName" ) and self.objectName is not None:
            if not suppressWarnings["objectname"]:
                print ( f"[dataHandlerObjects] warning, object name {self.objectName} supplied for an exclusion line. This is used to wait for a key word, not to give the object a name." )
            waitFor = self.objectName
        has_waited = False
        if waitFor == None:
            has_waited = True
        yields = []
        with open(self.path,'r', encoding = 'utf-8', errors='ignore' ) as csvfile:
            reader = csv.reader(filter(lambda row: row[0]!='#', csvfile))
            for r in reader:
                if "@@EOF@@" in r:
                    break
                if len(r)<1:
                    continue
                hasLatexStuff=False
                for _ in r:
                    if "\\tilde" in _: # sometimes its a latex line
                        hasLatexStuff = True
                    if "[GeV]" in _:
                        hasLatexStuff = True
                if hasLatexStuff:
                    continue
                if not has_waited:
                    for i in r:
                        if waitFor in i:
                            has_waited=True
                    continue
                if r[0].startswith("'M(") or r[0].startswith("M("):
                    if waitFor !=None and not waitFor in r[0]:
                        #print ( "set back." )
                        has_waited = False
                    continue
                fr = []
                for i in r:
                    try:
                        fr.append ( float(i) )
                    except:
                        fr.append ( i )
                if type ( self.unit) == tuple:
                    if self.unit[1]=="X:60":
                        frx = fr[0]*fr[1]+60.*( 1.-fr[1] )
                        fr[1]=frx
                yields.append ( fr )
            csvfile.close()
            if len(yields) > max_nbins:
                trimmingFactor[0] = int ( round ( math.sqrt ( len(yields) / 6000. ) ) )
                trimmingFactor[0] = trimmingFactor[0]**2
                newyields = []
                for cty,y in enumerate ( yields ):
                    if cty % trimmingFactor[0] == 0:
                        newyields.append ( y )
                logger.warn ( f"trimmed down csv file '{self.name}' from {len(yields)} to {len(newyields)}" )
                yields = newyields
            # sort upper limits and efficiencies but not points in exclusion lines.
            if "xclusion" in self.name:
                xs,ys=[],[]
                for yr in yields:
                    xs.append ( yr[0] )
                    if len(yr)>1:
                        ys.append ( yr[1] )
            else:
                try:
                    yields.sort()
                except TypeError as e:
                    logger.error ( f"type error when sorting: {e}." )
                    culprits = ""
                    for lno,y in enumerate(yields):
                        for x in y:
                            if type(x) not in ( float, int ):
                                culprits += f"''{x}'' "
                    logger.error ( f"the culprits might be {culprits} in {self.path}" )
                    sys.exit()
            values = [] # compute the final return values from these containers
            for y in yields:
                tmp = self.createEntryFromYield ( y )
                if tmp != None:
                    values.append ( tmp )
            self.extendDataToZero ( values )
            for v in values:
                ## print ( "returning v", v, "coord map is", self.coordinateMap )
                # print ( "name", self.index )
                yield v

    def createEntryFromYield ( self, yld : list ) -> list:
        """ create a return line from a yield line """
        ret = yld
        if type ( self.index ) in [ list, tuple ]:
            ret = []
            for i in self.index:
                ret.append ( yld[i] )
        if type ( self.index ) in [ int ]:
            if self.index >= len(yld):
                print ( f"[dataHandlerObjects] too high index {self.index} for {yr} in {self.path}" )
                sys.exit()
            ret = yld[:self.dimensions] + [ yld[self.index] ]
        if type ( self.index ) in [ str ]:
            if "constraint" in self.coordinateMap:
                if yld[self.coordinateMap["constraint"]] != self.index:
                    ret = None
        return ret


    def mcsv(self):
        """
        iterable method
        preprocessing multiple csv-files, and multiplying the last values
        floats

        :yield: list with values as float, one float for every column
        """
        ret = 1.
        npaths = []
        keys = set()
        for ctr,p in enumerate(self.path):
            path = {}
            ret = list( self.csvForPath( p ) )
            for point in ret:
                key = tuple(point[:-1])
                hasLatexStuff = False
                for k in key:
                    if type(k) == str and "\\tilde" in k:
                        hasLatexStuff = True
                    if type(k) == str and "$" in k:
                        hasLatexStuff = True
                if hasLatexStuff:
                    continue
                keys.add ( key )
                path[key] = point[-1]
            npaths.append ( path )
        for k in keys:
            ret = 1.
            for p in npaths:
                if not k in p.keys():
                    logger.error ( "it seems that point %s is not in all paths? in %s" % \
                                   (str(k), self.path ) )
                    break
                if type(p[k]) in [ str ]:
                    logger.warning ( f"skipping value {p[k]} as it is a string" )
                    continue
                ret = ret * p[k]
            y = list(k)+[ret]
            if ret < 0.:
                ret = 0.
                if errorcounts["smallerthanzero"] == False:
                    errorcounts["smallerthanzero"] = True
                    logger.warning ( f"found value of {ret} in {self.path} -- you sure you want that?" )
            #if ret > 0.:
            yield y


    def csvForPath ( self, path ):
        """ a csv file but giving the path """
        import csv

        waitFor = None
        if hasattr ( self, "objectName" ) and self.objectName is not None:
            print ( f"[dataHandlerObjects] warning, object name {self.objectName} supplied for an exclusion line. This is used to wait for a key word, not to give the object a name." )
            waitFor = self.objectName
        has_waited = False
        if waitFor == None:
            has_waited = True

        if "*" in path or "?" in path:
            import glob
            tmp = glob.glob ( path )
            if len(tmp)==1:
                if not errorcounts["wildcards"]:
                    print ( f"[dataHandlerObjects] wildcards in filename: {path}. they are unique. use them." )
                    errorcounts["wildcards"]=True
                path = tmp[0]
            else:
                print ( f"[dataHandlerObjects] wildcards in filename. they are not unique, found {len(tmp)} matches for {path}. fix it!" )
                sys.exit(-1)

        with open( path,'r') as csvfile:
            reader = csv.reader(filter(lambda row: row[0]!='#', csvfile))
            for r in reader:
                if len(r)<2:
                    continue
                #print ( "line >>%s<< hw=%s, waitFor=>>%s<<" % ( r, has_waited, waitFor ) )
                if not has_waited:
                    for i in r:
                        if waitFor in i:
                            has_waited=True
                    continue
                if r[0].startswith("'M(") or r[0].startswith("M("):
                    if waitFor !=None and not waitFor in r[0]:
                        #print ( "set back." )
                        has_waited = False
                    continue
                fr = []
                for i in r:
                    try:
                        fr.append ( float(i) )
                    except:
                        fr.append ( i )
                if type ( self.unit) == tuple:
                    if self.unit[1]=="X:60":
                        frx = fr[0]*fr[1]+60.*( 1.-fr[1] )
                        fr[1]=frx
                yield fr
            csvfile.close()

    def embaked(self) -> List:
        """
        iterable method
        preprocessing python dictionaries as defined by the em bakery
        floats

        :yield: list with values as float, one float for every column
        """
        SR = self.objectName
        D = None
        if self.path in fileCache:
            D = fileCache[self.path]
        else:
            try:
                with open(self.path) as f:
                    print ( f"[dataHandler] reading {self.path} searching for {SR}" )
                    D=eval(f.read())
                    fileCache[self.path]=D
            except Exception as e:
                logger.error ( f"could not read {self.path}: {e}" )
                sys.exit(-1)
        keys = list(D.keys() )
        keys.sort()
        for pt in keys:
            values = D[pt]
            vkeys = values.keys()
            newentries = {}
            for vkey in vkeys:
                ## awkward hack to make sure we allow for e.g. "SR1" and "SR1_MET...."
                if vkey.startswith ( "SR" ) and vkey.find("_")>1:
                    sr = vkey [ : vkey.find("_") ]
                    newentries[sr] = values [ vkey ]
            values.update ( newentries )
            ret = list(pt)
            eff = 0.
            if type(SR) in [ list, tuple ]:
                for sr in SR:
                    if sr in values.keys():
                        eff += values[sr]
            elif SR in values.keys():
                    eff = values[SR]
            ret += [ eff ]
            yield ret


    def effi(self):

        """
        iterable method
        preprocessing txt-files containing fastlim efficiency maps
        (only columns with floats)

        :yield: list with values as float, one float for every column
        """

        txtFile = open(self.path,'r')
        content = txtFile.readlines()
        txtFile.close
        for line in content:
            #Ignore lines which start with a letter
            if line.strip()[:1].isalpha():
                continue
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
                logger.error(f"Error reading file {self.path}")
                sys.exit()
            values = [value.strip() for value in values]
            try:
                values = [float(value) for value in values]
            except:
                logger.error(f"Error evaluating values {values} in file {self.path}")
                sys.exit()

            if values[-2]<4*values[-1]:
                logger.debug(f"Small efficiency value {values[-2]} +- {values[-1]}. Setting to zero.")
                values[-2]= 0.0

            print ( "value", values )
            yield values

    def root(self):
        """
        preprocessing root-files containing root-objects

        :return: ROOT-object
        """
        if isinstance(self.objectName, (list,tuple) ):
            # we can write tuples, list or <name>+<name>
            name = "+".join ( self.objectName )
            return self.rootByName ( name )

        if isinstance(self.objectName, str):
            return self.rootByName ( self.objectName )

        logger.error ( "objectName must be a string or a list" )
        sys.exit()

    def uprootByName(self, name : str ) -> List:
        """ generator of entries for UL and EM maps,
        retrieving from root files using uproot. we know the objects name
        in the root file
        :param name: the name of the object in the root file. if a "+" is in
        this name, we assume it's two objects and we concatenate.
        """
        import uproot
        if "+" in name:
            names = name.split("+")
            for name in names:
                ret = self.uprootByName ( name )
                for i in ret:
                    yield i
        # print ( "[dataHandlerObjects] using uproot on", self.path )
        rootFile = uproot.open(self.path)
        obj = rootFile.get(name)
        # self.interact()
        if not obj:
            logger.error( f"Object {name} not found in {self.path}" )
            sys.exit()

        points = list ( self._getUpRootPoints(obj) )
        self.extendDataToZero ( points )
        for point in points:
            yield point
        rootFile.close()

    def rootByName ( self, name ):
        try:
            import uproot
            return self.uprootByName ( name )
        except Exception as e:
            import ROOT
            return self.pyrootByName ( name )
        except Exception as e:
            logger.error ( "neither uproot nor ROOT module found" )
            sys.exit(-1)

    def error ( self, line ):
        if not line in self.hasWarned:
            self.hasWarned[line]=0
        self.hasWarned[line]+=1
        if self.hasWarned[line]<2:
            logger.error ( line )
        if self.hasWarned[line]==2:
            logger.error ( "(suppressing similar messages)" )

    def pyrootByName(self, name):
        """ generator, but by name, pyroot bindings """
        self.error ( "using pyroot, consider switching to uproot" )
        import ROOT
        rootFile = ROOT.TFile(self.path)
        if '"' in name:
            logger.warning ( f"Object {name} has quotation marks in name, will take them out" )
            name = name.replace('"','')
        obj = rootFile.Get(name)
        if not obj:
            logger.error(f"Object {name} not found in {self.path}")
            sys.exit()
        if not isinstance(obj,ROOT.TGraph):
            obj.SetDirectory(0)
        rootFile.Close()

        for point in self._getPyRootPoints(obj):
            yield point

    def cMacro(self):

        """
        preprocessing root c-macros containing root-objects

        :return: ROOT-object
        """

        if not isinstance(self.objectName, str):
            logger.error("objectName for root file should be of string type and not %s"
                         %type(self.objectName))
            sys.exit()

        import ROOT
        ROOT.gROOT.SetBatch()
        ROOT.gROOT.ProcessLine( f".x {self.path}" )
        try:
            limit = eval(f"ROOT.{self.objectName}")
        except:
            logger.error(f"Object {self.objectName} not found in {self.path}" )
            sys.exit()

        for point in self._getUpRootPoints(limit):
            yield point

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
        import ROOT
        rootFile = ROOT.TFile(self.path, 'r')
        canvas = rootFile.Get(self.objectName)
        if not canvas:
            logger.error( f"Object {self.objectName} not found in {self.path}" )
            sys.exit()
        try:
            limit = canvas.GetListOfPrimitives()[self.index]
        except IndexError:
            logger.error( f"ListOfPrimitives {self.objectName} has not index {self.index}" )
            sys.exit()

        for point in self._getRootPoints(limit):
            yield point

    def _getRootPoints ( self, obj ):
        try:
            import ROOT
            return self._getPyRootPoints( obj )
        except:
            pass
        return self._getUprootPoints ( obj )

    def _getUpRootPoints(self,obj):

        """
        Iterable metod for extracting points from root histograms
        :param obj: Root object (THx or TGraph)
        :yield: [x-axes, y-axes,..., bin content]
        """
        import uproot
        from uproot.models import TGraph, TH

        if obj.classname in [ "TH3F", "TH3D" ]:
            return self._getUpRootHistoPoints3D(obj)
        if obj.classname in [ "TH1F", "TH2D", "TH1D", "TH2F" ]:
            return self._getUpRootHistoPoints(obj)
        if obj.classname in [ "TGraph", "TGraph2D" ]:
            return self._getUpRootGraphPoints(obj)
        if obj.classname in [ "TTree" ]:
            return self._getUpRootTreePoints(obj)
        else:
            logger.error( f"ROOT object must be a THx, TTree or TGraphx object, not a {obj.classname}")
            import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()
            sys.exit()

    def _getPyRootPoints(self,obj):

        """
        Iterable metod for extracting points from root histograms
        :param obj: Root object (THx or TGraph)
        :yield: [x-axes, y-axes,..., bin content]
        """
        import ROOT

        if isinstance(obj,ROOT.TH1):
            return self._getPyRootHistoPoints(obj)
        elif isinstance(obj,ROOT.TGraph) or isinstance(obj,ROOT.TGraph2D):
            return self._getPyRootGraphPoints(obj)
        else:
            logger.error("ROOT object must be a THx or TGraphx object")
            sys.exit()

    def interact ( self, stuff ):
        """ interact, for debugging, then exit """
        print ( "I saved thing in 'stuff'" )
        import IPython
        IPython.embed ( )
        sys.exit()

    def _getUpRootHistoPoints3D(self,hist):

        """
        Iterable metod for extracting points from root histograms
        :param hist: Root histogram object (THx)
        :yield: [x-axes, y-axes,..., bin contend]
        """
        if not "index" in self.__dict__:
            logger.error ( "for 3d histos i need a coordinateMap with a 'bin' entry, plus an index" )
        index = self.__dict__["index"]
        #print ( "three D!", self.__dict__ )
        #sys.exit()

        if self.dimensions > 3:
            logger.error("Root histograms can not contain more than 3 axes. \
            (Data is defined as %i-th dimensional)" %self.dimensions)
            sys.exit()

        #Check dimensions:
        if not self.dimensions+1 == len ( hist.axes ):
            logger.error( f"Data dimensions ({self.dimensions}) and histogram dimensions ({hist.name}:{len (hist.axes) }) do not match {self.path}" )

        xAxis = hist.axes[0] # make sure this is the x axis
        assert ( xAxis.tojson()["fName"] == "xaxis" )
        xRange = range(len(xAxis))
        n_bins = len(xRange)
        # self.interact( hist )
        if len(hist.axes) > 1:
            yAxis = hist.axes[1]
            assert ( yAxis.tojson()["fName"] == "yaxis" )
            yRange = range(len(yAxis))
            n_bins=n_bins * len(yRange )
            total_points = len(yRange)*len(xRange)
            if total_points > 6000.:
                trimmingFactor[0] = int ( round ( math.sqrt ( total_points / 6000. ) ) )
                logger.info ( f"total points is {total_points}. set trimmingFactor to {trimmingFactor[0]}" )
        if len(hist.axes) > 2:
            zAxis = hist.axes[2]
            assert ( zAxis.tojson()["fName"] == "zaxis" )
            zRange = range(len(zAxis))
            n_bins=n_bins * len(zRange )
            if n_bins > max_nbins:
                if len(zRange)>50:
                    if allowTrimming:
                        if not errorcounts["trimzaxis"]:
                            errorcounts["trimzaxis"]=True
                            logger.warning ( f"'{self.name}' is too large a map (nbins={n_bins}). Will trim z-axis." )
                        n_bins = n_bins / len(zRange)
                        # zRange = range(1,len(zAxis) + 1, trimmingFactor[0] )
                        zRange = range(0,len(zAxis), trimmingFactor[0] )
                        n_bins = n_bins * len(zRange)
                    else:
                        if not errorcounts["trimzaxis"]:
                            errorcounts["trimzaxis"]=True
                            logger.warning ( "Very large map (nbins in z is %d), but trimming turned off." % n_bins )
        if self.dimensions > 1 and n_bins > max_nbins:
            if len(yRange)>50:
                if allowTrimming:
                    yRange = range(0,len(yAxis), trimmingFactor[0] )
                    # yRange = range(1,len(yAxis) + 1, trimmingFactor[0] )
                    if not errorcounts["trimyaxis"]:
                        logger.warning ( f"'{self.name}' is too large a map: (nbins={n_bins} > {max_nbins}). Will trim y-axis from {len(yAxis)} to {len(yRange)} (turn this off via dataHandlerObjects.allowTrimming)." )
                        errorcounts["trimyaxis"]=True
                    n_bins = n_bins / len(yAxis)
                    n_bins = n_bins * len(yRange)
                else:
                    if not errorcounts["trimyaxis"]:
                        errorcounts["trimyaxis"]=True
                        logger.warning ( "Very large map (nbins in y is %d), but trimming turned off." % n_bins )
        if n_bins > max_nbins:
            if allowTrimming:
                xRange = range(0,len(xAxis), trimmingFactor[0] )
                if not errorcounts["trimxaxis"]:
                    errorcounts["trimxaxis"]=True
                    logger.warning ( f"'{self.name}' is too large a map: (nbins={n_bins} > {max_nbins}). Will trim x-axis from {len(xAxis)} to {len(xRange)} (turn this off via dataHandlerObjects.allowTrimming)" )
                n_bins = n_bins / len(xAxis)
                n_bins = n_bins * len(xRange)

            else:
                if not errorcounts["trimxaxis"]:
                    errorcounts["trimxaxis"]=True
                    logger.warning ( "Very large map (nbins in x is %d), but trimming turned off." % n_bins )

        if False: # total_points > n_bins:
            logger.warning ( f"n_bins={n_bins}, total_points={total_points}, n_dims={self.dimensions}, xRange={list(xRange)[:4]} yRange={list(yRange)[:4]} {self.name}" )

        ct = 0
        # self.interact ( hist )
        for xBin in xRange:
            x = xAxis.centers()[xBin]
            if self.dimensions == 1:
                ul = hist.values()[xBin]
                if ul == 0.: continue
                yield [x, ul]
            elif self.dimensions > 1:
                for yBin in yRange:
                    y = yAxis.centers()[yBin]
                    ul = hist.values()[xBin][yBin]
                    if type(ul) in [ float, np.float32, np.float64 ]:
                        if ul == 0.: continue
                        ct+=1
                        yield [x, y, ul]
                    else:
                        zRange = range(len(zAxis) ) # , trimmingFactor[0] )
                        for zBin in zRange:
                            z = zAxis.centers()[zBin]
                            ul = hist.values()[xBin][yBin][zBin]
                            #if ul == 0.: continue
                            if zBin == index:
                                yield [x, y, ul]

    def _getUpRootHistoPoints(self,hist):

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
        if not self.dimensions == len ( hist.axes ):
            logger.error( f"Data dimensions ({self.dimensions}) and histogram dimensions ({hist.name}:{len (hist.axes) }) do not match {self.path}" )

        xAxis = hist.axes[0] # make sure this is the x axis
        assert ( xAxis.tojson()["fName"] == "xaxis" )
        xRange = range(len(xAxis))
        n_bins = len(xRange)
        # self.interact( hist )
        if self.dimensions > 1:
            yAxis = hist.axes[1]
            assert ( yAxis.tojson()["fName"] == "yaxis" )
            yRange = range(len(yAxis))
            n_bins=n_bins * len(yRange )
            total_points = len(yRange)*len(xRange)
            if total_points > 6000.:
                trimmingFactor[0] = int ( round ( math.sqrt ( total_points / 6000. ) ) )
                logger.info ( f"total points is {total_points}. set trimmingFactor to {trimmingFactor[0]}" )
        if self.dimensions > 2:
            zAxis = hist.axes[2]
            assert ( zAxis.tojson()["fName"] == "zaxis" )
            zRange = range(len(zAxis))
            n_bins=n_bins * len(zRange )
            if len ( n_bins ) > max_nbins:
                if len(zRange)>50:
                    if allowTrimming:
                        if not errorcounts["trimzaxis"]:
                            errorcounts["trimzaxis"]=True
                            logger.warning ( f"'{self.name}' is too large a map (nbins={n_bins}). Will trim z-axis." )
                        n_bins = n_bins / len(zRange)
                        zRange = range(0,len(zAxis), trimmingFactor[0] )
                        # zRange = range(1,len(zAxis) + 1, trimmingFactor[0] )
                        n_bins = n_bins * len(zRange)
                    else:
                        if not errorcounts["trimzaxis"]:
                            errorcounts["trimzaxis"]=True
                            logger.warning ( "Very large map (nbins in z is %d), but trimming turned off." % n_bins )
        if self.dimensions > 1 and n_bins > max_nbins:
            if len(yRange)>50:
                if allowTrimming:
                    yRange = range(0,len(yAxis), trimmingFactor[0] )
                    # yRange = range(1,len(yAxis) + 1, trimmingFactor[0] )
                    if not errorcounts["trimyaxis"]:
                        logger.warning ( f"'{self.name}' for {self.txName} is too large a map: (nbins={n_bins} > {max_nbins}). Will trim y-axis from {len(yAxis)} to {len(yRange)} (turn this off via dataHandlerObjects.allowTrimming)." )
                        errorcounts["trimyaxis"]=True
                    n_bins = n_bins / len(yAxis)
                    n_bins = n_bins * len(yRange)
                else:
                    if not errorcounts["trimyaxis"]:
                        errorcounts["trimyaxis"]=True
                        logger.warning ( "Very large map (nbins in y is %d), but trimming turned off." % n_bins )
        if n_bins > max_nbins:
            if allowTrimming:
                xRange = range(0,len(xAxis),  trimmingFactor[0] )
                if not errorcounts["trimxaxis"]:
                    errorcounts["trimxaxis"]=True
                    logger.warning ( f"'{self.name}' for {self.txName} is too large a map: (nbins={int(n_bins)} > {max_nbins}). Will trim x-axis from {len(xAxis)} to {len(xRange)} (turn this off via dataHandlerObjects.allowTrimming)" )
                n_bins = n_bins / len(xAxis)
                n_bins = n_bins * len(xRange)

            else:
                if not errorcounts["trimxaxis"]:
                    errorcounts["trimxaxis"]=True
                    logger.warning ( "Very large map (nbins in x is %d), but trimming turned off." % n_bins )

        if False: # total_points > n_bins:
            logger.warning ( f"n_bins={n_bins}, total_points={total_points}, n_dims={self.dimensions}, xRange={list(xRange)[:4]} yRange={list(yRange)[:4]} {self.name}" )

        ct = 0
        # self.interact ( hist )
        for xBin in xRange:
            x = xAxis.centers()[xBin]
            if self.dimensions == 1:
                ul = hist.values()[xBin]
                if ul == 0.: continue
                yield [x, ul]
            elif self.dimensions > 1:
                for yBin in yRange:
                    y = yAxis.centers()[yBin]
                    if self.dimensions == 2:
                        ul = hist.values()[xBin][yBin]
                        if ul == 0.: continue
                        ct+=1
                        #if ct % 300 == 0:
                        #    print ( f"yield {ct}: {yBin}/{x},{y} {ul}" )
                        yield [x, y, ul]
                    elif self.dimensions == 3:
                        for zBin in zRange:
                            z = zAxis.centers()[zBin]
                            ul = hist.values()[xBin][yBin][zBin]
                            if ul == 0.: continue
                            yield [x, y, z, ul]

    def _getPyRootHistoPoints(self,hist):

        """
        Iterable metod for extracting points from root histograms
        :param hist: Root histogram object (THx)
        :yield: [x-axes, y-axes,..., bin contend]
        """

        if self.dimensions > 3:
            logger.error("Root histograms can not contain more than 3 axes. \
            (Data is defined as %i-th dimensional)" %self.dimensions)
            sys.exit()

        # self.interact( hist )
        #Check dimensions:
        if not self.dimensions == hist.GetDimension():
            logger.error( f"Data dimensions ({self.dimensions}) and histogram dimensions ({hist.GetName()}:{hist.GetDimension()}) do not match {self.path}" )

        xAxis = hist.GetXaxis()
        xRange = range(1,xAxis.GetNbins() + 1)
        n_bins = len(xRange)
        if self.dimensions > 1:
            yAxis = hist.GetYaxis()
            yRange = range(1,yAxis.GetNbins() + 1)
            n_bins=n_bins * len(yRange )
            total_points = len(yRange)*len(xRange)
            if total_points > 6000.:
                trimmingFactor[0] = int ( round ( math.sqrt ( total_points / 6000. ) ) )
                logger.info ( f"total points is {total_points}. set trimmingFactor to {trimmingFactor[0]}" )
        if self.dimensions > 2:
            zAxis = hist.GetZaxis()
            zRange = range(1,zAxis.GetNbins() + 1)
            n_bins=n_bins * len(zRange )
            if len ( n_bins ) > max_nbins:
                if len(zRange)>50:
                    if allowTrimming:
                        if not errorcounts["trimzaxis"]:
                            errorcounts["trimzaxis"]=True
                            logger.warning ( f"'{self.name}' is too large a map (nbins={n_bins}). Will trim z-axis." )
                        n_bins = n_bins / len(zRange)
                        zRange = range(1,zAxis.GetNbins() + 1, trimmingFactor[0] )
                        n_bins = n_bins * len(zRange)
                    else:
                        if not errorcounts["trimzaxis"]:
                            errorcounts["trimzaxis"]=True
                            logger.warning ( "Very large map (nbins in z is %d), but trimming turned off." % n_bins )
        if self.dimensions > 1 and n_bins > max_nbins:
            if len(yRange)>50:
                if allowTrimming:
                    yRange = range(1,yAxis.GetNbins() + 1, trimmingFactor[0] )
                    if not errorcounts["trimyaxis"]:
                        logger.warning ( f"'{self.name}' is too large a map: (nbins={n_bins} > {max_nbins}). Will trim y-axis from {yAxis.GetNbins()} to {len(yRange)} (turn this off via dataHandlerObjects.allowTrimming)." )
                        errorcounts["trimyaxis"]=True
                    n_bins = n_bins / yAxis.GetNbins()
                    n_bins = n_bins * len(yRange)
                else:
                    if not errorcounts["trimyaxis"]:
                        errorcounts["trimyaxis"]=True
                        logger.warning ( "Very large map (nbins in y is %d), but trimming turned off." % n_bins )
        if n_bins > max_nbins:
            if allowTrimming:
                xRange = range(1,xAxis.GetNbins() + 1,  trimmingFactor[0] )
                if not errorcounts["trimxaxis"]:
                    errorcounts["trimxaxis"]=True
                    logger.warning ( f"'{self.name}' is too large a map: (nbins={n_bins} > {max_nbins}). Will trim x-axis from {xAxis.GetNbins()} to {len(xRange)} (turn this off via dataHandlerObjects.allowTrimming)" )
                n_bins = n_bins / xAxis.GetNbins()
                n_bins = n_bins * len(xRange)

            else:
                if not errorcounts["trimxaxis"]:
                    errorcounts["trimxaxis"]=True
                    logger.warning ( "Very large map (nbins in x is %d), but trimming turned off." % n_bins )

        if False: # total_points > n_bins:
            logger.warning ( f"n_bins={n_bins}, total_points={total_points}, n_dims={self.dimensions}, xRange={list(xRange)[:4]} yRange={list(yRange)[:4]} {self.name}" )

        ct = 0
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
                        ct+=1
                        #if ct % 300 == 0:
                        #    print ( f"yield {ct}: {yBin}/{x},{y} {ul}" )
                        yield [x, y, ul]
                    elif self.dimensions == 3:
                        for zBin in zRange:
                            z = zAxis.GetBinCenter(zBin)
                            ul = hist.GetBinContent(xBin, yBin, zBin)
                            if ul == 0.: continue
                            yield [x, y, z, ul]

    def _getUpRootGraphPoints(self,graph):

        """
        Iterable metod for extracting points from root TGraph objects
        :param graph: Root graph object (TGraphx)
        :yield: tgraph point
        """
        import uproot

        if self.dimensions >= 3:
            logger.error("Root graphs can not contain more than 2 axes. \
            (Data is defined as %i-th dimensional)" %self.dimensions)
            sys.exit()

        #Check dimensions:
        if self.dimensions == 1 and not graph.classname in [ "TGraph" ]:
            logger.error("TGraph dimensions do not match data")
            sys.exit()
        if self.dimensions == 2 and not graph.classname in [ "TGraph2D" ]:
            logger.error("TGraph dimensions do not match data")
            sys.exit()

        for i in range( len(graph.values()[0]) ):
            x, y = graph.values()[0][i], graph.values()[1][i]
            if graph.classname in [ "TGraph" ]:
                yield [ x, y ]
            elif graph.classname in [ "TGraph2D" ]:
                z = graph.values()[2][i]
                yield [ x, y, z ]

    def _getUpRootTreePoints( self, tree ) -> Generator:

        """
        Iterable metod for extracting points from root TTree objects
        :param tree: Root tree object (TTree)
        :yield: ttree point
        """
        if type(self.index) in [ tuple, list ]: ## for aggregation!
            ys = []
            for i in self.index:
                idfier = tree.file.file_path + ":" + tree.name + ":" + i
                if not idfier in pointsCache:
                    self._cacheUpRootTreePoints ( tree )
                for y in pointsCache[idfier]:
                    ys.append ( y )
            ysDict = {}
            for y in ys:
                tmpy = y[:-1]
                if not tmpy in ysDict:
                    ysDict[tmpy]=0.
                ysDict[tmpy]+=y[-1]
            for k,v in ysDict.items():
                t = ( *k, v )
                yield t
            return

        if type(self.index) in [ dict ]: ## for aggregation!
            ys = []
            # tot = sum ( self.index.values() )
            for i,w in self.index.items():
                idfier = tree.file.file_path + ":" + tree.name + ":" + i
                if not idfier in pointsCache:
                    self._cacheUpRootTreePoints ( tree )
                for y in pointsCache[idfier]:
                    y = ( *y[:-1], y[-1]*w ) # /tot )
                    # print ( "@@w", w, "y", y, "tot", tot )
                    ys.append ( y )
            ysDict = {}
            for y in ys:
                tmpy = y[:-1]
                if not tmpy in ysDict:
                    ysDict[tmpy]=0.
                ysDict[tmpy]+=y[-1]
            for k,v in ysDict.items():
                t = ( *k, v )
                yield t
            return

        idfier = tree.file.file_path + ":" + tree.name + ":" + self.index
        if not idfier in pointsCache:
            self._cacheUpRootTreePoints ( tree )
        for y in pointsCache[idfier]:
            yield y

    def _cacheUpRootTreePoints(self,tree ):
        import uproot

        if self.dimensions >= 3:
            logger.error(f"Root trees can not contain more than 2 axes. \
            (Data is defined as {self.dimensions}-th dimensional)" )
            sys.exit()

        #Check dimensions:
        if self.dimensions == 1 and not len(tree.keys())==3:
            logger.error(f"TTree dimensions ({self.dimensions}) do not match data ({len(tree.keys())}). Will assume that this is ok, but you have been warned.")
            # sys.exit()
        if self.dimensions == 2 and not len(tree.keys())==4:
            logger.error(f"TTree dimensions ({self.dimensions}) do not match data ({len(tree.keys())}). Will assume that this is ok, but you have been warned.")
            #sys.exit()

        branches = tree.arrays()
        keys = tree.keys()
        xvar, yvar = keys[0], keys[1] # get the names of the branches!
        effs = branches [ "AccEff" ]
        yields = []
        print ( f"[dataHandlerObjects] caching {len(branches[xvar])} ttree entries!" )
        # import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()
        for i in range( len(branches[xvar]) ):
#            if type(self.index) == str: # and \
#                    self.index != branches["SearchBin"][i]:
#                continue
            eff = float(effs[i])
            x = float(branches[ xvar ][i])
            tidfier = tree.file.file_path + ":" + tree.name + ":" + branches["SearchBin"][i]
            if not tidfier in pointsCache:
                pointsCache[tidfier] = []
            if self.dimensions == 1:
                pointsCache[tidfier].append ( ( x, eff ) )
            elif self.dimensions == 2:
                y = float(branches[ yvar ][i])
                pointsCache[tidfier].append ( ( x, y, eff ) )

    def _getPyRootGraphPoints(self,graph):

        """
        Iterable metod for extracting points from root TGraph objects
        :param graph: Root graph object (TGraphx)
        :yield: tgraph point
        """
        import ROOT

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


        x, y, z = ctypes.c_double(0.),ctypes.c_double(0.),ctypes.c_double(0.)
        # x, y, z = ROOT.Double(0.),ROOT.Double(0.),ROOT.Double(0.)
        for i in range(0, graph.GetN()):
            if isinstance(graph,ROOT.TGraph):
                graph.GetPoint(i, x, y)
                yield [ x.value, y.value ]
                # yield [float(x), float(y)]
            elif isinstance(graph,ROOT.TGraph2D):
                graph.GetPoint(i, x, y, z)
                yield [ x.value, y.value, z.value ]
                # yield [float(x), float(y), float(z)]


class ExclusionHandler(DataHandler):

    """
    iterable class to hold and process exclusion curve data.
    This Class is designed to iterate over the point of the
    exclusion line
    """

    def __init__(self,name,coordinateMap,xvars,axes=None):

        """
        attributes 'sort' and 'reverse' are initialized with False
        :param name: name as string
        :param coordinateMap: A dictionary mapping the index of the variables
               in the data and the
               corresponding x,y,.. coordinates used to define the plane axes.
               (e.g. {x : 0, y : 1, 'ul value' : 2} for a 3-column data,
               where x,y,.. are the sympy symbols and the value key can be anything)

        """

        #Exclusion curve always has dimensions = 1 (x-value)
        DataHandler.__init__(self,name,coordinateMap,xvars)
        self.axes = axes
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
            ret = self.mapPoint(point)
            if type(self.unit)==tuple:
                assert ( self.unit[0] == "GeV" )
                if self.unit[1]=="ns":
                    ret[y]=hbar/ret[y]
            yield ret

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
            logger.error(f"Unknown svg format in {self.path}:\n {lines[0].split()[0]}")
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
                logger.error(f"Unknown axis in {self.path}:\n {tick.split(':')[0][:1]}")
                sys.exit()
        if len(xticks) != 2 or len(yticks) != 2:
            logger.error(f"Unknown axis format {self.path}")
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
                yield [x,y]
        else:
            for l in lines[1:]:
                v = l.split(' ')
                xorig = float(v[0])
                yorig = float(v[1])
                x = (xorig-x0)/xGeV
                y = (yorig-y0)/yGeV
                yield [x,y]


    def pdf(self):

        """
        iterable method for  processing files with coordinates in pdf format.
        :yield: [x-value in GeV, y-value in GeV]
        """
        #print ( "[dataHandlerObjects] here!!", self.path  )
        #print ( )
        from .PDFLimitReader import PDFLimitReader
        if self.index == None or type(self.index) != str:
            print ( "[dataHandlerObjects] index is None. For pdf files, use index to specify axis ranges, e.g. index='x[100,260];y[8,50];z[.1,100,true]'" )
            sys.exit(-1)
        tokens = self.index.split(";")
        ## boundaries in the plot!
        lim = { "x": ( 150, 1200 ), "y": ( 0, 600 ), "z": ( 10**-3, 10**2 ) }
        logz = True ## are the colors in log scale?
        yIsDelta = False
        for cttoken,token in enumerate(tokens):
            axis = token[0]
            lims = token[1:].replace("[","").replace("]","")
            lims = lims.split(",")
            hasMatched = False
            if len(lims)>2:
                if "delta" in lims[2].lower() and cttoken == 1:
                    yIsDelta = True
                    hasMatched = True
                if lims[2].lower() in [ "log", "true" ]:
                    logz = True
                    hasMatched = True
                elif lims[2].lower() in [ "false", "nolog" ]:
                    logz = False
                    hasMatched = True
                if not hasMatched:
                    print ( f"Error: do not understand {lims[2]}. I expected log or nolog" )
            lims = tuple ( map ( float, lims[:2] ) )
            lim[axis]=lims

        data =  {
            'name': self.path.replace(".pdf",""),
            'x':{'limits': lim["x"]},
            'y':{'limits': lim["y"]},
            'z':{'limits': lim["z"], 'log':logz },
            }
        r = PDFLimitReader( data )
        points = r.exclusions [ self.name ]
        for p in points:
            yield p
