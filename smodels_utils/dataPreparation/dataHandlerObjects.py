#!/usr/bin/env python

"""
.. module:: dataHandlerObjects
   :synopsis: Holds objects for reading and processing the data in different formats

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

from __future__ import print_function
import ctypes
import sys
import os
import logging
import math
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

import numpy as np
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

def _Hash ( lst ): ## simple hash function for our masses
    ret=0.
    for l in lst:
        ret=100000*ret+l
    return ret

allowTrimming=True ## allow big grids to be trimmed down
trimmingFactor = 2 ## the factor by which to trim

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
        and allowNegativeValues with False
        :param name: name as string
        :param dimensions: Dimensions of the data (e.g., for x,y,value, dimensions=2).
        :param coordinateMap: A dictionary mapping the index of the variables
              in the data and the corresponding x,y,.. coordinates used to define the
              plane axes.  (e.g. {x : 0, y : 1, 'ul value' : 2} for a 3-column data,
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
        self.allowNegativeValues = False
        self.dataset=None
        self._massUnit = 'GeV'
        self._unit = None  #Default unit
        self._rescaleFactors = None

        if self.name == 'upperLimits' or self.name == 'expectedUpperLimits':
            self._unit = 'pb'

        newCoordinateMap = {} # take out entries with none
        for k,v in coordinateMap.items():
            if v != None:
                newCoordinateMap[k]=v
        if len(coordinateMap) != self.dimensions+1 and \
            len(newCoordinateMap) == self.dimensions+1:
                coordinateMap = newCoordinateMap
                
        #Consistency checks:
        if len(coordinateMap) != self.dimensions+1:
            logger.error("Coordinate map %s is not consistent with number of dimensions (%i) in %s"
                         %(coordinateMap,self.dimensions+1, dataLabel))
            sys.exit()
        for xv in self.xvars:
            if not xv in coordinateMap:
                logger.error("Coordinate %s has not been defined in coordinateMap" %xv)
                if xv in [ x, y, z ]:
                    logger.error ( "Maybe you wrote '%s' instead of %s (i.e. a string instead of a sympy Symbol?)" % ( xv, xv ) )
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
                logger.error("Units must be in %s, not %s" % (str(units),unitString) )
                sys.exit()
            self._unit = unitString

    def loadData(self):
        """
        Loads the data and stores it in the data attribute
        """

        if not self.fileType:
            logger.error("File type for %s has not been defined" %self.path)
            sys.exit()

        if self.fileType == "csv" and type(self.path) == tuple:
            if errorcounts["pathtupleerror"] == False:
                print ( f"[dataHandlerObjects] warning: {self.path} is a tuple. will switch from csv to mcsv as your dataformat." )
                errorcounts["pathtupleerror"]  = True
            self.fileType = "mcsv"

        #Load data
        self.data = []
        strictlyPositive = False
        if self._unit in [ "fb", "pb" ]:
            strictlyPositive = True
        if not hasattr ( self, self.fileType ):
            logger.error ( "Format type '%s' is not defined. Try either one of 'root', 'csv', 'txt', 'embaked', 'mscv', 'effi', 'cMacro', 'canvas', 'svg', 'pdf' instead. " % self.fileType )
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
                    logger.error("Key %s not allowed for data" %key)
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
                    logger.error("More than one point in reweighting data matches point %s" %xvals)
                    logger.error("But allowMultipleAcceptances is set to true, so will choose first value!" )
                    pts = [ pts[0] ]
                if not pts:
                    continue
                elif len(pts) > 1:
                    logger.error("More than one point in reweighting data matches point %s" %xvals)
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
            logger.error("%s should have at least %i dimensions (%i dimensions found)"
                         %(self.name, self.dimensions+1,len(point)))
            sys.exit()

        ptDict = {}
        #Return a dictionary with the values:
        for xvar,i in self.coordinateMap.items():
            #Skip variables without indices (relevant for exclusion curves)
            if i is None:
                continue
            if i >= len(point):
                logger.error( "asking for %dth element of %s in %s" % \
                              (i, point, self.path ) )
                logger.error( "coordinate map is %s" % self.coordinateMap )
            ptDict[xvar] = point[i]

        return ptDict

    def setSource(self, path, fileType, objectName = None,
                  index = None, unit = None, scale = None):

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

        if type(path) not in [ tuple, list ] and not os.path.isfile(path):
            logger.error("File %s not found" %path)
            if type(self.dataUrl ) == str and os.path.basename(path) == os.path.basename ( self.dataUrl ):
                logger.info( "But you supplied a dataUrl with same basename, so I try to fetch it" )
                import requests
                r = requests.get ( self.dataUrl )
                if not r.status_code == 200:
                    logger.error ( "retrieval failed: %d" % r.status_code )
                    sys.exit()
                with open ( path, "wb" ) as f:
                    f.write ( r.content )
                    f.close()
            else:
                sys.exit()

        if unit:
            self.unit = unit

        self.path = path
        self.fileType = fileType
        self.objectName = objectName
        self.index = index
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
                logger.error('Mass units must be in %s' %str(units))
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
            if type(value) not in [ float, np.float64, int, np.int ]:
                print ( f"[dataHandlerObjects] value {value} cannot be cast to float." )
                if type(value) == str and "{" in value:
                    print ( "[dataHandlerObjects] did you try to parse an embaked file as a csv file maybe?" )
                    sys.exit(-1)
            if value < 0.0:
                logger.warning("Negative value %s in %s will be ignored"%(value,self.path))
                return False
            if value == 0.0 and strictlyPositive:
                if not errorcounts["zerovalue"]:
                    logger.warning("Zero value %s in %s will be ignored"%(value,self.path))
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
                logger.error("Error reading file %s" %self.path)
                sys.exit()
            values = [value.strip() for value in values]
            try:
                values = [float(value) for value in values]
            except:
                logger.error("Error evaluating values %s in file %s" %(values,self.path))
                sys.exit()

            lines.append ( values )
        xcoord, ycoord = self.coordinateMap[x], self.coordinateMap[y]
        lines.sort( key= lambda x: x[xcoord]*1e6+x[ycoord] )
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
                    print ( "Error: do not understand %s. I expected log or nolog or delta (though I accept delta only in y coord)" % lims[2] )
            lims = tuple ( map ( float, lims[:2] ) )
            lim[axis]=lims
        print("[dataHandlerObjects] limits %s" % lim )

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
            print ( "[dataHandlerObjects] warning, object name %s supplied for an exclusion line. This is used to wait for a key word, not to give the object a name." % self.objectName )
            waitFor = self.objectName
        has_waited = False
        if waitFor == None:
            has_waited = True
        yields = []
        with open(self.path,'r') as csvfile:
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
                    logger.error ( "type error when sorting: %s." % e )
                    culprits = ""
                    for lno,y in enumerate(yields):
                        for x in y:
                            if type(x) not in ( float, int ):
                                culprits += f"''{x}'' "
                    logger.error ( "the culprits might be %s in %s" % \
                                   ( culprits, self.path ) )
                    sys.exit()
            for yr in yields:
                yld = yr
                if type ( self.index ) in [ list, tuple ]:
                    ret = []
                    for i in self.index:
                        ret.append ( yr[i] )
                    yld = ret
                if type ( self.index ) in [ int ]:
                    yld = yr[:self.dimensions] + [ yr[self.index] ]
                yield yld

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
            print ( "[dataHandlerObjects] warning, object name %s supplied for an exclusion line. This is used to wait for a key word, not to give the object a name." % self.objectName )
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

    def embaked(self):
        """
        iterable method
        preprocessing python dictionaries as defined by the em bakery
        floats

        :yield: list with values as float, one float for every column
        """
        SR = self.objectName
        try:
            with open(self.path) as f:
                D=eval(f.read())
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
                logger.error("Error reading file %s" %self.path)
                sys.exit()
            values = [value.strip() for value in values]
            try:
                values = [float(value) for value in values]
            except:
                logger.error("Error evaluating values %s in file %s" %(values,self.path))
                sys.exit()

            if values[-2]<4*values[-1]:
                logger.debug("Small efficiency value %s +- %s. Setting to zero." %(values[-2],values[-1]))
                values[-2]= 0.0

            print ( "value", values )
            yield values

    def root(self):

        """
        preprocessing root-files containing root-objects

        :return: ROOT-object
        """
        if isinstance(self.objectName, list):
            return self.rootByList ( self.objectName )

        if isinstance(self.objectName, str):
            return self.rootByName ( self.objectName )

        logger.error ( "objectName must be a string or a list" )
        sys.exit()

    def rootByList(self, namelist ):
        """ generator, but by list of names """
        pts = {}
        import ROOT
        rootFile = ROOT.TFile(self.path)
        hashes={}
        for name in namelist:
            obj = rootFile.Get(name)
            if not obj:
                logger.error("Object %s not found in %s" %(name,self.path))
                sys.exit()
            if not isinstance(obj,ROOT.TGraph):
                obj.SetDirectory(0)

            for point in self._getPoints(obj):
                Hsh = _Hash(point[:-1])
                if not Hsh in pts:
                    pts[ Hsh ] = 0.
                pts[ Hsh ] += point[-1]
                hashes[ Hsh ] = point[:-1]
        rootFile.Close()
        ret = []
        for k,v in hashes.items():
            L = v
            L.append ( pts[k] )
            ret.append ( L )
        for r in ret:
            yield r

    def rootByName(self, name):
        """ generator, but by name """
        import ROOT
        rootFile = ROOT.TFile(self.path)
        obj = rootFile.Get(name)
        if not obj:
            logger.error("Object %s not found in %s" %(name,self.path))
            sys.exit()
        if not isinstance(obj,ROOT.TGraph):
            obj.SetDirectory(0)
        rootFile.Close()

        for point in self._getPoints(obj):
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
        ROOT.gROOT.ProcessLine(".x %s" %self.path)
        try:
            limit = eval("ROOT.%s" %self.objectName)
        except:
            logger.error("Object %s not found in %s" %(self.objectName,self.path))
            sys.exit()

        for point in self._getPoints(limit):
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
            logger.error("Object %s not found in %s" %(self.objectName,self.path))
            sys.exit()
        try:
            limit = canvas.GetListOfPrimitives()[self.index]
        except IndexError:
            logger.error("ListOfPrimitives %s has not index %s"
                          %(self.objectName,self.index))
            sys.exit()

        for point in self._getPoints(limit):
            yield point

    def _getPoints(self,obj):

        """
        Iterable metod for extracting points from root histograms
        :param obj: Root object (THx or TGraph)
        :yield: [x-axes, y-axes,..., bin content]
        """
        import ROOT

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
        n_bins = len(xRange)
        max_nbins = 10000
        if self.dimensions > 1:
            yAxis = hist.GetYaxis()
            yRange = range(1,yAxis.GetNbins() + 1)
            n_bins=n_bins * len(yRange )
            total_points = len(yRange)*len(xRange)
            if total_points > 10000.:
                trimmingFactor = int ( math.sqrt ( total_points / 10000. ) )
                logger.warning ( f"total points is {total_points}. set trimmingFactor to {trimmingFactor}" )
        if self.dimensions > 2:
            zAxis = hist.GetZaxis()
            zRange = range(1,zAxis.GetNbins() + 1)
            n_bins=n_bins * len(zRange )
            if len ( n_bins ) > max_nbins:
                if len(zRange)>50:
                    if allowTrimming:
                        if not errorcounts["trimzaxis"]:
                            errorcounts["trimzaxis"]=True
                            logger.warning ( "Too large map (nbins=%d). Will trim z-axis." % n_bins )
                        n_bins = n_bins / len(zRange)
                        zRange = range(1,zAxis.GetNbins() + 1, trimmingFactor )
                        n_bins = n_bins * len(zRange)
                    else:
                        if not errorcounts["trimzaxis"]:
                            errorcounts["trimzaxis"]=True
                            logger.warning ( "Very large map (nbins in z is %d), but trimming turned off." % n_bins )
        if self.dimensions > 1 and n_bins > max_nbins:
            if len(yRange)>50:
                if allowTrimming:
                    yRange = range(1,yAxis.GetNbins() + 1, trimmingFactor )
                    if not errorcounts["trimyaxis"]:
                        logger.warning ( "Too large map (nbins=%d > %s). Will trim y-axis from %d to %d (turn this off via dataHandlerObjects.allowTrimming)." % \
                                        ( n_bins, max_nbins, yAxis.GetNbins(), len(yRange) ))
                        errorcounts["trimyaxis"]=True
                    n_bins = n_bins / len(yRange)
                    n_bins = n_bins * len(yRange)
                else:
                    if not errorcounts["trimyaxis"]:
                        errorcounts["trimyaxis"]=True
                        logger.warning ( "Very large map (nbins in y is %d), but trimming turned off." % n_bins )
        if n_bins > max_nbins:
            if allowTrimming:
                xRange = range(1,xAxis.GetNbins() + 1,  trimmingFactor )
                if not errorcounts["trimxaxis"]:
                    errorcounts["trimxaxis"]=True
                    logger.warning ( "Too large map (nbins=%d > %d). Will trim x-axis from %d to %d (turn this off via dataHandlerObjects.allowTrimming)" % \
                                 ( n_bins, max_nbins, xAxis.GetNbins(), len(xRange)  ) )

            else:
                if not errorcounts["trimxaxis"]:
                    errorcounts["trimxaxis"]=True
                    logger.warning ( "Very large map (nbins in x is %d), but trimming turned off." % n_bins )





        # print ( "n_bins=%d, n_dims=%d, xRange=%d" % ( n_bins, self.dimensions, len(xRange) ) )

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

    def __init__(self,name,coordinateMap,xvars):

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
                    print ( "Error: do not understand %s. I expected log or nolog" % lims[2] )
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
