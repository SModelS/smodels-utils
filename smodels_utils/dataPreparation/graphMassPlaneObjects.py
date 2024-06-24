#!/usr/bin/env python3

"""
.. module:: graphMassPlaneObjects
   :synopsis: Holds object representing one mass plane,
              for graphs

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys
import numpy as np
from sympy import var, Eq, lambdify, solve, N, And, sqrt, Symbol, core, Float
from scipy.spatial import Delaunay
from itertools import permutations
from smodels_utils.dataPreparation.dataHandlerObjects import \
         DataHandler,ExclusionHandler
import string
import logging
from smodels_utils.helper.various import round_to_n
from typing import Union, Dict, List
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

#Define all available variables
#(The ordering is the default order assumed for columns in source txt files,
# or the x,y,.. bins in ROOT histograms or the x,y values in ROOT TGraphs and svg files)
#This order can be changed using the coordinates keyword in setSources or addSource.
allvars = x,y,z,w = var('x y z w')

hasWarned = { "emptystring": False }

def _lambdify ( a, b, c, dummify ):
    f = lambdify ( a, b, c, dummify=dummify )
    f.expr = "%s: %s" % ( a, b )
    return f

class GraphMassPlane(object):
    """
    Holds all information related to one mass plane
    a mass plane is defined by their axes.
    The variables defined in infoAttr are passed to the corresponding
    txname to be written in txname.txt
    """

    infoAttr = ['figureUrl','dataUrl','axes']
    allowedDataLabels = ['efficiencyMap','upperLimits','expectedUpperLimits',
                         'acceptanceMap',
                        'obsExclusion','obsExclusionP1','obsExclusionM1',
                        'expExclusion','expExclusionP1','expExclusionM1']

    @classmethod
    def getNiceAxes(cls,axesStr):
        """
        Convert the axes definition format, e.g. {0 : 'x', 1 : 'y', 2 : 'x', 3 : 'y'}
        to a nicer format: x_y_

        :param axesStr: string defining axes in the old format
        :return: string with a nicer representation of the axes (more suitable for printing)
        """

        if axesStr == "":
            logger.error ( "Axes field is empty: cannot validate." )
            return None
        x,y,z,w = var('x y z w')
        axesDict = eval(axesStr,{'x' : x, 'y' : y, 'z': z, 'w': w})

        def isSymmetrical ( axesDict : Dict ) -> bool:
            """ check if dicionary is symmetrical """
            if len(axesDict)%2==1:
                return False ## odd number of entries
            n = int(len(axesDict)/2)
            for i in range(n):
                if axesDict[i] != axesDict[i+n]:
                    return False
            return True
        if isSymmetrical ( axesDict ):
            n = int(len(axesDict)/2)
            for i in range(n,2*n):
                axesDict.pop(i)
        ret = "_".join ( map ( str, axesDict.values() ) )
        # print ( f"@@ graphMassPlaneObjects {axesDict} turned into {ret}" )
        return ret


    def __init__( self, txDecay, parametersMap):
        """
        sets the branches to the given axes and initialize the mass plane related
        values an objects
        :param txDecay: object of type TxDecay
        :param parametersMap: the full mass array containing equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [[x,y],[x,y]])
        """
        self._txDecay = txDecay
        self.figureUrl = None
        self.dataUrl = None
        self.allInputFiles = []

        self.parametersMap = parametersMap
        self._exclusionCurves = []
        xvars = set()
        for k,v in parametersMap.items():
            if type(v) not in [ str ]:
                v=str(v)
            xvars.add ( Symbol(v) )
        self.xvars = list(xvars)

    @classmethod
    def fromString(cls,txname,string):

        """
        build an instance of MassPlane from a given string

        :param txname: txname string (e.g. T1)
        :param string: The string must contain a representation of the axes in the format
                      '[[exp1,exp2,..], [Exp1,Exp2,..]]', where exp1,.. are the expressions
                      defining the mass array in terms of the x,y,.. variables
                      (e.g. [[x,y],[x,y]])
        """
        if string in [ "", None, "None" ]:
            if not hasWarned["emptystring"]:
                logger.error ( "cannot build mass plane from empty string!" )
                hasWarned["emptystring"]=True
            return None
        parametersMap = eval(string)
        massPlane = GraphMassPlane(txname,parametersMap)

        return massPlane

    def __str__(self):
        return f"{self.parametersMap}"

    def setSources(self,dataLabels,dataFiles,dataFormats,
                   objectNames=None,indices=None,units=None,coordinates=None,
                   scales=None, **args ):
        """
        Defines the data sources for the plane.

        :param dataLabels: List of strings with the dataLabels
                          possible data labels are defined in allowedDataLabels
                          (e.g. efficiencyMap, upperLimits, expectedUpperLimits,...)
        :param dataFiles: List of strings with the file paths
                          to the data files.
        :param dataFormats: List of strings with the file formats
                          for the data files.
        :param objectNames: List of object names stored in root-file or cMacro.
                            String appearing in title of csv table in csv files.
        :param indices: List of indices objects in listOfPrimitives of ROOT.TCanvas
        :param units: List of strings with units for objects (e.g. 'fb', None, ...)
        :param coordinates: Lists of dictionaries with the mapping of txt file columns
                          to the x,y,... coordinates (e.g. {x : 1, y: 2, 'value' :3})
        :param scales: Lists of floats to rescale the data

        """
        for d in dataFiles:
            self.allInputFiles.append ( d )

        #Make sure input is consistent:
        optionalInput = { "objectNames": objectNames, "indices": indices,
                         "units": units,"coordinates": coordinates,"scales": scales }
        # optionalInput = [objectNames,indices,units,coordinates,scales]
        #allInput = [dataFiles,dataLabels,dataFormats] + optionalInput
        allInput = { "dataFiles": dataFiles, "dataLabels": dataLabels,
                     "dataFormats": dataFormats }
        allInput.update ( optionalInput )
        for i,(key,inputList) in enumerate(allInput.items()):
            if inputList is None and key in optionalInput.keys():
                allInput[key] = [None]*len(dataFiles)
            if not isinstance(allInput[key],list):
                logger.error("Input %s must be a list" % key )
                sys.exit()
            elif len(allInput[key]) != len(dataFiles):
                logger.error("Length of lists is inconsistent: ``%s'' has %d entries -- should have %d.." % ( key, len(allInput[key]),len(dataFiles) ) )
                sys.exit()


        for i,dataFile in enumerate(dataFiles):
            dataLabel = allInput["dataLabels"][i]
            dataFormat = allInput["dataFormats"][i]
            objectName = allInput["objectNames"][i]
            index = allInput["indices"][i]
            unit = allInput["units"][i]
            coordinate = allInput["coordinates"][i]
            scale = allInput["scales"][i]
            self.addSource(dataLabel,dataFile, dataFormat,
                           objectName, index, unit, coordinate, scale, **args )

    def addSource(self,dataLabel,dataFile,dataFormat=None, objectName=None,index=None,
                  unit=None,coordinateMap=None,scale=None, **args ):
        """
        Defines a single data sources for the plane.

        :param dataLabel: Srings with the dataLabel
                          possible data labels are defined in allowedDataLabels
                          (e.g. efficiencyMap, upperLimits, expectedUpperLimits,...)
        :param dataFile: Strings with the file path to the data file.
        :param dataFormat: Strings with the file format for the data file, e.g.
                           root, csv, embaked. If none, then file extension is
                           format.
        :param objectName: String with the object name stored in root-file or cMacro
        :param index: Index for objects in listOfPrimitives of ROOT.TCanvas
        :param unit: Strings with unit for data (e.g. 'fb',None,'pb',...),
                     similar to "scale", can also be used to re-scale the data, either
                     via a '*' or a '/' symbol
        :param coordinateMap: Dictionaries with the mapping of txt file columns
                            to the x,y,... coordinates (e.g. {x : 0, y: 1, 'ul' :2})
        :param scale: Float to re-scale the data

        """
        if dataFormat == None:
            p1 = dataFile.rfind ( "." )
            dataFormat = dataFile[p1+1:]
            print ( f"[massPlaneObjects] setting format to '{dataFormat}'" )
        self.allInputFiles.append ( dataFile )

        # print ( "adding", dataLabel, dataFile, dataFormat )
        # import IPython ; IPython.embed() ; sys.exit(-1)
        dimensions = len(self.xvars)
        if not dataLabel in self.allowedDataLabels:
            logger.error( f"Data label {dataLabel} is not allowed. Try one of: {', '.join(self.allowedDataLabels)}.")
            sys.exit()
        if not 'exclusion' in dataLabel.lower():
            #Define the default coordinate mapping:
            if not coordinateMap:
                coordinateMap = dict([[xv,i] for i,xv in enumerate(allvars[:dimensions])])
                coordinateMap['value'] = dimensions
            #Initialize a data handler
            dataObject = DataHandler(dataLabel,coordinateMap,self.xvars,
                                     str(self._txDecay) )
        else:
            #Define the default 1D coordinate mapping for exclusion curves
            if not coordinateMap:
                coordinateMap = {x : 0, y : 1, 'value' : None}
                if not y in self.xvars: # 1d data
                    coordinateMap = {x : 0, 'value' : None}
            dataObject = ExclusionHandler(dataLabel,coordinateMap,self.xvars,self.parametersMap )
            self._exclusionCurves.append(dataObject)

        dataObject.dataUrl = self.dataUrl
        #Set source of object
        dataObject.setSource(dataFile, dataFormat,
                             objectName, index, unit, scale, **args )
        #Store it as a mass plane attribute:
        setattr(self,dataLabel,dataObject)

    def _removePoints_ ( self, points, obj ):
        """ remove all points within an area spanned by <points> """
        hull = Delaunay ( points )
        newdata=[]
        for i in obj.data:
            p = [ i[x], i[y] ]
            in_hull = hull.find_simplex ( p )
            if in_hull == -1: ## not in a cut-out region
                newdata.append ( i )
            else:
                logger.info ( "removing point %s as it is in cut-out region." % ( p ) )
        obj.data = newdata

    def removeArea(self,points):
        """ remove all points within an area spanned by <points> """
        points.append ( points[0] )
        for i in [ "efficiencyMap", "upperLimits", "expectedUpperLimits" ]:
            if hasattr ( self, i ):
                self._removePoints_ ( points, getattr(self,i) )

    def getParticleMasses(self,**xMass):

        """
        Translate a point of the plot, given by x- and y-values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
                     Keyword arguments must equal the variable name.
        :return: list containing two other lists. Each list contains floats, representing
        the masses of the particles of each branch in GeV
        """
        # print ( "FIXME implement, getParticleMasses", xMass, "parameterMap is", self.parametersMap )
        ret = [0]*(1+max(self.parametersMap.keys()))
        for k,v in self.parametersMap.items():
            value = str(v)
            for variable,mass in xMass.items():
                value = value.replace(variable,str(mass))
            ret[k]=eval(value)
        return ret

    def hasSimilarEquationAlready ( self, eqs : List, e ):
        """ Check if we have a similar equation already """
        # print ( f"@@12 check if {e} is fuzzily in {eqs}" )
        if len(eqs)==0:
            return False
        for eq in eqs:
            if eq.lhs == e.lhs: ## lefthand sides match
                if type(eq.rhs) == Float and type(e.rhs) == Float:
                    if 1e-8 < abs ( e.rhs - eq.rhs) < 1.6:
                        # print ( f"@@13 fuzzy match!" )
                        return True
        return False

    def getXYValues(self, parameters : List ) -> Union[None,Dict]:
        """
        Translate mass and width arrays to a 2d point in the plot.
        Returns a dictionary for the x and y coordinates.

        :param parameters: a list of masses and widths, corresponding to the dataMap
        :returns: None if an error occurs,
        else {'x': x-value in GeV as float, 'y' : y-value in GeV as float, ..}
        """
        # print ( f"@@11 getXYValues {parameters}" )
        
        ret = {}
        eqs = set()
        from sympy.parsing.sympy_parser import parse_expr
        for index,param in self.parametersMap.items():
            rhs = float("nan")
            ## FIXME when is it widths instead??
            # print ( f"parameters are {parameters}" )
            if type(parameters[index]) in [ float ]:
                # ret[str(param)] = float ( parameters[index] )
                rhs = round_to_n ( float ( parameters[index] ), 5 )
            elif type(parameters[index]) in [ tuple, list ]:
                # ret[str(param)] = float ( parameters[index][1] )
                rhs = round_to_n ( float ( parameters[index][1] ), 5 )
            elif parameters[index]=="stable":
                rhs = 0.
            lhs = parse_expr ( str(param) )
            if type(lhs)==core.numbers.Float:
                lhs = round_to_n ( float(lhs), 5 )
            if lhs == 0. and rhs == 1.:
              continue # hack for now FIXME
            if type(lhs)==Float and type(rhs)==Float and \
                    1e-8 < abs ( lhs - rhs ) < 1.6:
                continue # hack for now FIXME
            e = Eq ( lhs, rhs )
            if e == True: ## take out trivial expressions
                continue
            if e == False: # if a numerical comparison is wrong, we can stop here
                return ret
            if True: # not self.hasSimilarEquationAlready ( eqs, e ):
                eqs.add ( e )
        # print ( f"@@11 eqs={eqs}" )
        d = solve ( list(eqs) )
        #print ( f"@@11 solved {parameters}: {d}" )
        ret = {}
        if d == []:
            return ret
        for k,v in d.items():
            ret[str(k)]=float(v)
        return ret

class Axes(object):
    """
    Holds the axes information for one branch of a singe mass plane.
    No units supported!
    """

    hasWarned = {}

    def __init__(self, massEqs,massVars,widthVars=None ):

        """
        Initialize a list of sympy.core.relational.Equality-object
        Those objects can only contain the variables:
        x, y, z

        :param massEqs: Full list of equations for the branch masses.
                        Each list entry must be a Equalty-object in terms of x,y,z.
        :param massVars: Full list of mass variables (sympy symbol object).

        """

        if not isinstance(massEqs,list):
            logger.error("Masses must be a list")
            sys.exit()

        self._equations = massEqs[:] #Store equations
        self._massVars = massVars[:] #Store mass variables
        if widthVars:
            self._widthVars = widthVars[:] #Store width variables

        #Already define the functions and plot dimensions:
        self._setXYFunction()

    @classmethod
    def fromConvert(cls, massEqs):

        """
        build an instance of Axes from the given parameters

        :param massEqs:  Full list of equations for the branch masses.
                        Each list entry must be a Equalty-object in terms of x,y,z.
        :return: Axes-object
        """


        if not isinstance(massEqs,list):
            logger.error('Mass must be a list of equations')

        #Define mass and width variables:
        massVars,widthVars = [], []
        for im in range(len(massEqs)):
            massVars.append(var('Mass'+string.ascii_uppercase[im]))
            widthVars.append(var('Width'+string.ascii_uppercase[im]))

        #New format:
        allEqs = []
        for im,massEq in enumerate(massEqs):
            #Create mass variable (upper case for first branch and lower case for second)
            if type(massEq) == tuple:
                eq1 = Eq(massVars[im],N(massEq[0],5))
                eq2 = Eq(widthVars[im],N(massEq[1],2))
                allEqs.append(eq1)
                allEqs.append(eq2)
            else:
                eq = Eq(massVars[im],N(massEq,5))
                allEqs.append(eq)

            allEqs = sorted(allEqs, key = lambda eq: eq.args[0].name)

        return cls(allEqs,massVars,widthVars)

    def _getMassFunction(self):

        """
        Build a function to compute the mass array for given x,y, .. values.
        The input variables are the ones defined in self._xvars.
        :return: lambdify function which returns the mass array given the input variables.
        """

        #Mass variables:
        masses = self._massVars
        widths = self._widthVars
        #Solve equation for masses
        s = solve(self._equations,masses,dict=True)[0]
        self._massFunctions = []
        self._widthFunctions = []
        self._widthIndices = [] ## take note of where width info was given
        for m in self._massVars:
            self._massFunctions.append(_lambdify(self._xvars,s[m],'math',dummify=False))
        tall = solve(self._equations,widths,dict=True)
        if len(tall)==0:
            return
        t=tall[0]
        for i,m in enumerate(self._widthVars):
            # x=0.
            try:
                x=_lambdify(self._xvars,t[m],'math',dummify=False)
                self._widthFunctions.append ( x )
                self._widthIndices.append ( i )
            except KeyError: ## does not have to be given!
                pass
            # self._widthFunctions.append ( x )

    def getParticleMasses(self,**xMass):

        """
        translate a point of the plot, given by x,y,.. values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
                     Keyword arguments must equal the variable name.
        :return: list containing floats, representing the masses of the particles in GeV
        """

        if not self._equations:
            return []

        #If mass function has not yet been created, create it now:
        if not '_massFunctions' in self.__dict__:
            self._getMassFunction()

        #Create dictionary with input values
        xValues = {}
        for xv in self._xvars:
            if not str(xv) in xMass:  #Missing a variable
                self.error("Input variable %s missing for computing mass" %xv)
                return []
            value = xMass[str(xv)]
            if type(value) in [ str ]:
                self.warn(f"Input variable ''{xv}'' has a string value of ''{value}''. Will skip entry." )
                return []
            xValues[str(xv)] = value

        parametersMap = [mfunc(**xValues) for mfunc in self._massFunctions]
        widthArray = [mfunc(**xValues) for mfunc in self._widthFunctions]
        combinedArray = []
        # print ( "parametersMap", parametersMap, "widthArray", widthArray, "widthIndices", self._widthIndices, "xmass", xMass )
        widthCtr=0
        for i,m in enumerate(parametersMap):
            tmp = m
            if i in self._widthIndices:
                tmp = (m,widthArray[widthCtr])
                widthCtr+=1
            combinedArray.append ( tmp )
        return combinedArray

    def _setXYFunction(self):

        """
        Using the equations defined for the axes (branch),
        builds a function to compute the x,y,z values for a given
        mass array. It verifies the number of variables appearing in
        equations and solve for them. The system should not be underconstrained.
        :return: lambdify function
        """

        self._xyFunction = {}
        self._xvars = []
        self._nArguments = 0
        if not self._equations:
            return

        xvars = []
        for eq in self._equations:
            for v in eq.free_symbols:
                if v in allvars and not v in xvars:
                    xvars.append(v)

        #Vars defines the number of variables to be solved for:
        nvars = len(xvars)
        neqs = len(self._equations)
        if nvars > neqs:
            logger.error('Underconstrained system. We have %i variables and %i equations' %(nvars,neqs))
            sys.exit()
        #Solve for variables in vars using nvars equations:
        for eqs in permutations(self._equations,nvars):
            xy = solve(eqs,xvars,dict=True)
            if not xy:
                continue
            if not isinstance(xy,list) or len(xy) > 1:
                logger.error("Something wrong with the result from solve: %s" %str(xy))
                sys.exit()
            else:
                xy = xy[0]
            #Check solution:
            if len(xy) == nvars:
                break
            else:
                xy = dict([[v,None] for v in xvars]) #Create dictionary with None values

        for sol in xy.values():
            if not sol:
                logger.error("Could not solve the equations for the x,y,... values.\nCheck the mass plane definition.")
        self._xy = xy
        self._xvars = sorted(self._xy.keys(), key= lambda xv: str(xv))  #Variables appearing in branch in correct order

        #Define xy function as dictionary:
        self._xyFunction = {}
        #dummify=False allows to keep MassA,MassB,... as valid argument keywords:
        #(make sure the MassA,MassB,.. values are passed as keywords)
        for xv in self._xvars:
            self._xyFunction[xv] = _lambdify(self._massVars+self._widthVars,xy[xv],'math',dummify=False)
        self._nArguments = nvars

    def tuplesInMassContainer ( self, parametersMap ):
        for im,mass in enumerate(parametersMap):
            if type(mass)==tuple: ## the old way
                return True
        return False

    def warn ( self, line ):
        if not line in self.hasWarned:
            self.hasWarned[line]=0
        self.hasWarned[line]+=1
        if self.hasWarned[line]<2:
            logger.warning ( line )

    def error ( self, line ):
        if not line in self.hasWarned:
            self.hasWarned[line]=0
        self.hasWarned[line]+=1
        if self.hasWarned[line]<2:
            logger.error ( line )

    def getXYValues(self,parametersMap):

        """
        translate a mass array (for single branch) to a point of the plot

        :param parametersMap: list containing  floats, representing
        the masses of the particles in GeV
        :return: None if the mass array does not satify the mass equations.
                Otherwise, returns a dictionary:
                {'x' : x-value in GeV as float, 'y' : y-value in GeV as float,...}
        """
        # print ( f"@@B getXYValues {parameterMap}" )
        if not parametersMap:
            return {}

        if not '_xyFunction' in self.__dict__:
            self._setXYFunction()

        massInput = {}
        if False:
            print ( "X parametersMap", parametersMap )
            print ( "X widthArray", widthArray )
            print ( "X _massVars", self._massVars )
            print ( "X _widthVars", self._widthVars )
        #    len(parametersMap) == len(self._massVars) + len(self._widthVars) and \
        if len(parametersMap)>len(self._massVars) and len(self._widthVars)>0 and \
            widthArray == None:
            ## it seems the widths ended up in the mass array
            widthArray = parametersMap[1::2]
            parametersMap = parametersMap[0::2]
        if self.tuplesInMassContainer ( parametersMap ):
            ## there are tuples, do it the old way
            for im,mass in enumerate(parametersMap):
                if type(mass) in [ tuple ]:
                    massInput[ str(self._massVars[im]) ] = mass[0]
                    massInput[ str(self._widthVars[im]) ] = mass[1]
                else:
                    massInput[ str(self._massVars[im]) ] = mass
        else:
            for im,mass in enumerate(parametersMap):
                if False:
                    print ( "----------------" )
                    print ( "mass", mass )
                    print ( "parametersMap", parametersMap )
                    print ( "widthArray", widthArray )
                    print ( "im", im )
                    print ( "massVars", self._massVars )
                    print ( "widthVars", self._widthVars )
                if im < len(self._massVars):
                    massInput[ str(self._massVars[im]) ] = mass
        if widthArray is None:
            wv = str(self._widthVars[im])
            if not wv in massInput:
                massInput[wv]=None
            #for im,width in enumerate(parametersMap):
            #    massInput[ str(self._widthVars[im]) ] = None
        else:
            for im,width in enumerate(widthArray):
                if im < len(self._widthVars):
                    massInput[ str(self._widthVars[im]) ] = width
        #Define dictionary with mass variables and values
        #massInput = dict([[str(self._massVars[im]),mass] for im,mass in enumerate(parametersMap)])
        xValues = {}
        #Get the function for each x,y,.. variable and compute its value
        for l in [ "A", "B", "C" ][:len(parametersMap)]:
            if not "Mass%s" % l in massInput.keys():
                massInput["Mass%s" % l] = None
            if "Mass%s" % l in massInput.keys() and \
                not "Width%s" % l in massInput.keys(): ## FIXME why is this needed???
                massInput["Width%s" % l ]=None
        #print ( "[getXYValues] massInput", massInput )
        #print ( "[getXYValues] xyFunc", self._xyFunction, str(self._xyFunction) )
        #print ( "parametersMap", parametersMap )
        """import IPython
        IPython.embed()
        sys.exit()"""
        for xv,xfunc in self._xyFunction.items():
            fexpr = str ( xfunc.expr )
            cleanedInput = {}
            for k,v in massInput.items():
                if not k in fexpr:
                    line = f"key {k} is not in func {fexpr}!!"
                    self.warn ( line )
                else:
                    cleanedInput[k]=v
            xValues[str(xv)] = xfunc(**cleanedInput)

        #Now check if the x,y,.. values computed give the parametersMap back:
        newMass = self.getParticleMasses(**xValues)

        def isFloat ( x ):
            return isinstance(x,(np.floating,float))

        def distance ( x, y ):
            ## the distance between x and y
            ## I dont fully understand why there cases where x has a width
            ## and y doesnt ....
            #assert ( type(x) == type(y) )
            if isFloat(x) and type(y)==tuple:
                return abs(x-y[0])
            if isFloat(y) and type(x)==tuple:
                return abs(x[0]-y)
            if isFloat(x) and isFloat(y):
                return abs(x-y)
            assert ( type(x) == tuple )
            d=0.
            for xi,yi in zip ( x, y ):
                d+= ( xi-yi)**2
            return sqrt ( d)

        for im,m in enumerate(newMass[:len(parametersMap)]):
            ma=parametersMap[im]
            d = distance(m,ma )
            if d > 0.11: #Masses differ
                return None
        # print ( "xValues", xValues )
        return xValues

    def __str__(self):

        string =''
        for equation in self._equations:
            if not "==" in str(equation):
                if len(string)>0:
                    string+="_"
                string += str ( equation ).replace(" ","")
            else:
                if string: string = '%s_'%string
                string = '%sEq(%s,%s)' %(string, \
                str(equation).split('==')[0].strip().replace(' ',''), \
                str(equation).split('==')[1].strip().replace(' ',''))
        return string

class WildAxes(Axes):

    """
    Holds the axes information for a wildcard branch ('*') of a singe mass plane.
    No units supported!
    """

    def __init__(self, massEqs,massVars):
        Axes.__init__(self,massEqs,massVars)

    @classmethod
    def fromConvert(cls, massEqs):

        """
        build an instance of Axes from the given parameters

        :param massEqs:  Full list of equations for the branch masses.
                        Each list entry must be a Equalty-object in terms of x,y,z.
        :return: Axes-object
        """

        return cls([],[])


    def getXYValues(self,parametersMap, width=None):

        return None

    def getParticleMasses(self,**xMass):

        return '*'

    def __str__(self):
        return "%s" % ( self.axes )

    def setBranch(self,branchNumber, branchMasses):

        """
        Set masses for branch branchNumber.
        :param branchNumber: index of the branch
        :param branchMasses: list containing the equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [x,y])
        """

        if len(self.branches) <= branchNumber:
            if branchMasses == ['*']:
                self.branches.append(WildAxes.fromConvert(branchMasses))
            else:
                self.branches.append(Axes.fromConvert(branchMasses))
        else:
            if branchMasses == ['*']:
                self.branches[branchNumber] = WildAxes.fromConvert(branchMasses)
            else:
                self.branches[branchNumber] = Axes.fromConvert(branchMasses)


    def setSources(self,dataLabels,dataFiles,dataFormats,
                   objectNames=None,indices=None,units=None,coordinates=None,
                   scales=None, **args ):
        """
        Defines the data sources for the plane.

        :param dataLabels: List of strings with the dataLabels
                          possible data labels are defined in allowedDataLabels
                          (e.g. efficiencyMap, upperLimits, expectedUpperLimits,...)
        :param dataFiles: List of strings with the file paths
                          to the data files.
        :param dataFormats: List of strings with the file formats
                          for the data files.
        :param objectNames: List of object names stored in root-file or cMacro.
                            String appearing in title of csv table in csv files.
        :param indices: List of indices objects in listOfPrimitives of ROOT.TCanvas
        :param units: List of strings with units for objects (e.g. 'fb', None, ...)
        :param coordinates: Lists of dictionaries with the mapping of txt file columns
                          to the x,y,... coordinates (e.g. {x : 1, y: 2, 'value' :3})
        :param scales: Lists of floats to rescale the data

        """
        for d in dataFiles:
            self.allInputFiles.append ( d )

        #Make sure input is consistent:
        optionalInput = { "objectNames": objectNames, "indices": indices,
                         "units": units,"coordinates": coordinates,"scales": scales }
        # optionalInput = [objectNames,indices,units,coordinates,scales]
        #allInput = [dataFiles,dataLabels,dataFormats] + optionalInput
        allInput = { "dataFiles": dataFiles, "dataLabels": dataLabels,
                     "dataFormats": dataFormats }
        allInput.update ( optionalInput )
        for i,(key,inputList) in enumerate(allInput.items()):
            if inputList is None and key in optionalInput.keys():
                allInput[key] = [None]*len(dataFiles)
            if not isinstance(allInput[key],list):
                logger.error("Input %s must be a list" % key )
                sys.exit()
            elif len(allInput[key]) != len(dataFiles):
                logger.error("Length of lists is inconsistent: ``%s'' has %d entries -- should have %d.." % ( key, len(allInput[key]),len(dataFiles) ) )
                sys.exit()


        for i,dataFile in enumerate(dataFiles):
            dataLabel = allInput["dataLabels"][i]
            dataFormat = allInput["dataFormats"][i]
            objectName = allInput["objectNames"][i]
            index = allInput["indices"][i]
            unit = allInput["units"][i]
            coordinate = allInput["coordinates"][i]
            scale = allInput["scales"][i]
            self.addSource(dataLabel,dataFile, dataFormat,
                           objectName, index, unit, coordinate, scale, **args )

    def addSource(self,dataLabel,dataFile,dataFormat=None, objectName=None,index=None,
                  unit=None,coordinateMap=None,scale=None, **args ):
        """
        Defines a single data sources for the plane.

        :param dataLabel: Srings with the dataLabel
                          possible data labels are defined in allowedDataLabels
                          (e.g. efficiencyMap, upperLimits, expectedUpperLimits,...)
        :param dataFile: Strings with the file path to the data file.
        :param dataFormat: Strings with the file format for the data file, e.g.
                           root, csv, embaked. If none, then file extension is
                           format.
        :param objectName: String with the object name stored in root-file or cMacro
        :param index: Index for objects in listOfPrimitives of ROOT.TCanvas
        :param unit: Strings with unit for data (e.g. 'fb',None,'pb',...),
                     similar to "scale", can also be used to re-scale the data, either
                     via a '*' or a '/' symbol
        :param coordinateMap: Dictionaries with the mapping of txt file columns
                            to the x,y,... coordinates (e.g. {x : 0, y: 1, 'ul' :2})
        :param scale: Float to re-scale the data

        """
        if dataFormat == None:
            p1 = dataFile.rfind ( "." )
            dataFormat = dataFile[p1+1:]
            print ( f"[massPlaneObjects] setting format to '{dataFormat}'" )
        self.allInputFiles.append ( dataFile )

        print ( "graphMassPlaneObjects adding", dataLabel, dataFile, dataFormat, "dim", self.xvars )

        dimensions = len(self.xvars)
        if not dataLabel in self.allowedDataLabels:
            logger.error( f"Data label {dataLabel} is not allowed. Try one of: {', '.join(self.allowedDataLabels)}.")
            sys.exit()
        if not 'exclusion' in dataLabel.lower():
            #Define the default coordinate mapping:
            if not coordinateMap:
                coordinateMap = dict([[xv,i] for i,xv in enumerate(allvars[:dimensions])])
                coordinateMap['value'] = -1 # dimensions
            #Initialize a data handler
            dataObject = DataHandler(dataLabel,coordinateMap,self.xvars,
                                     str(self._txDecay) )
        else:
            #Define the default 1D coordinate mapping for exclusion curves
            if not coordinateMap:
                coordinateMap = {x : 0, y : 1, 'value' : None}
                if not y in self.xvars: # 1d data
                    coordinateMap = {x : 0, 'value' : None}
            dataObject = ExclusionHandler(dataLabel,coordinateMap,self.xvars,self.parametersMap )
            self._exclusionCurves.append(dataObject)
        dataObject.dataUrl = self.dataUrl
        #Set source of object
        dataObject.setSource(dataFile, dataFormat,
                             objectName, index, unit, scale, **args )
        #Store it as a mass plane attribute:
        setattr(self,dataLabel,dataObject)

    def _removePoints_ ( self, points, obj ):
        """ remove all points within an area spanned by <points> """
        hull = Delaunay ( points )
        newdata=[]
        for i in obj.data:
            p = [ i[x], i[y] ]
            in_hull = hull.find_simplex ( p )
            if in_hull == -1: ## not in a cut-out region
                newdata.append ( i )
            else:
                logger.info ( "removing point %s as it is in cut-out region." % ( p ) )
        obj.data = newdata

    def removeArea(self,points):
        """ remove all points within an area spanned by <points> """
        points.append ( points[0] )
        for i in [ "efficiencyMap", "upperLimits", "expectedUpperLimits" ]:
            if hasattr ( self, i ):
                self._removePoints_ ( points, getattr(self,i) )

    def getParticleMasses(self,**xMass):

        """
        Translate a point of the plot, given by x- and y-values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
                     Keyword arguments must equal the variable name.
        :return: list containing two other lists. Each list contains floats, representing
        the masses of the particles of each branch in GeV
        """

        if self.branches == None:
            return []
        parametersMap = [br.getParticleMasses(**xMass) for br in self.branches]
        return parametersMap

    def getXYValues(self,parametersMap,widthArray=None):

        """
        Translate a mass array to a point of the plot.
        Returns a dictionary with the variable labels as keys and the values as values.

        :param parametersMap: list containing two other lists. Each list contains floats,
        representing the masses of the particles of each branch in GeV
        :param widthArray: list containing two other lists. Each list contains floats,
        representing the widths of the particles of each branch in GeV. If None,
        we assume a width-independent plane.
        :raise parametersMapLenError: if length of mass array is unequal 2
        :raise unequalXYValuesError: if the branches return different values for x or y
        :return: None if mass array do not met the conditions of one branch
        else: {'x': x-value in GeV as float, 'y' : y-value in GeV as float, ..}
        """
        # print ( f"@@C getXYValues {parameterMap}" )
        #print ( ">> widthArray", widthArray )
        # print ( ">> parametersMap", parametersMap )

        if len(parametersMap) != len(self.branches):
            logger.error("dimension of mass array (%d) inconsistent with branches length (%d)" % ( len(parametersMap), len(self.branches) ) )
            sys.exit()
        if widthArray != None and len(widthArray) != len(self.branches):
            logger.error("Width array inconsistent with branches length")
            sys.exit()
        xyArray = {}
        if widthArray == None:
            for i,mass in enumerate(parametersMap):
                xyDict = self.branches[i].getXYValues(mass)
                if xyDict is None:
                    return None
                for xvar,value in xyDict.items():
                    if xvar in xyArray:
                        #Check if x,y-values given by distinct branches agree:
                        if xyArray[xvar] != value and (abs(xyArray[xvar]+value) == 0.
                           or abs(xyArray[xvar]-value)/abs(xyArray[xvar]+value) > 1e-4):
                            return None
                    xyArray[xvar] = value
            return xyArray
        for i,(mass,width) in enumerate(zip(parametersMap,widthArray)):
            if self.axes[i]==['*']: ## skip the "any" branches
                continue
            xyDict = self.branches[i].getXYValues(mass,width)
            if xyDict is None:
                return None
            for xvar,value in xyDict.items():
                if xvar in xyArray:
                    #Check if x,y-values given by distinct branches agree:
                    if xyArray[xvar] != value and (abs(xyArray[xvar]+value) == 0.
                       or abs(xyArray[xvar]-value)/abs(xyArray[xvar]+value) > 1e-4):
                        return None
                xyArray[xvar] = value

        return xyArray


class Axes(object):

    """
    Holds the axes information for one branch of a singe mass plane.
    No units supported!
    """

    hasWarned = {}

    def __init__(self, massEqs,massVars,widthVars=None ):

        """
        Initialize a list of sympy.core.relational.Equality-object
        Those objects can only contain the variables:
        x, y, z

        :param massEqs: Full list of equations for the branch masses.
                        Each list entry must be a Equalty-object in terms of x,y,z.
        :param massVars: Full list of mass variables (sympy symbol object).

        """

        if not isinstance(massEqs,list):
            logger.error("Masses must be a list")
            sys.exit()

        self._equations = massEqs[:] #Store equations
        self._massVars = massVars[:] #Store mass variables
        if widthVars:
            self._widthVars = widthVars[:] #Store width variables

        #Already define the functions and plot dimensions:
        self._setXYFunction()

    @classmethod
    def fromConvert(cls, massEqs):

        """
        build an instance of Axes from the given parameters

        :param massEqs:  Full list of equations for the branch masses.
                        Each list entry must be a Equalty-object in terms of x,y,z.
        :return: Axes-object
        """


        if not isinstance(massEqs,list):
            logger.error('Mass must be a list of equations')

        #Define mass and width variables:
        massVars,widthVars = [], []
        for im in range(len(massEqs)):
            massVars.append(var('Mass'+string.ascii_uppercase[im]))
            widthVars.append(var('Width'+string.ascii_uppercase[im]))

        #New format:
        allEqs = []
        for im,massEq in enumerate(massEqs):
            #Create mass variable (upper case for first branch and lower case for second)
            if type(massEq) == tuple:
                eq1 = Eq(massVars[im],N(massEq[0],5))
                eq2 = Eq(widthVars[im],N(massEq[1],2))
                allEqs.append(eq1)
                allEqs.append(eq2)
            else:
                eq = Eq(massVars[im],N(massEq,5))
                allEqs.append(eq)

            allEqs = sorted(allEqs, key = lambda eq: eq.args[0].name)

        return cls(allEqs,massVars,widthVars)

    def _getMassFunction(self):

        """
        Build a function to compute the mass array for given x,y, .. values.
        The input variables are the ones defined in self._xvars.
        :return: lambdify function which returns the mass array given the input variables.
        """

        #Mass variables:
        masses = self._massVars
        widths = self._widthVars
        #Solve equation for masses
        s = solve(self._equations,masses,dict=True)[0]
        self._massFunctions = []
        self._widthFunctions = []
        self._widthIndices = [] ## take note of where width info was given
        for m in self._massVars:
            self._massFunctions.append(_lambdify(self._xvars,s[m],'math',dummify=False))
        tall = solve(self._equations,widths,dict=True)
        if len(tall)==0:
            return
        t=tall[0]
        for i,m in enumerate(self._widthVars):
            # x=0.
            try:
                x=_lambdify(self._xvars,t[m],'math',dummify=False)
                self._widthFunctions.append ( x )
                self._widthIndices.append ( i )
            except KeyError: ## does not have to be given!
                pass
            # self._widthFunctions.append ( x )

    def getParticleMasses(self,**xMass):

        """
        translate a point of the plot, given by x,y,.. values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
                     Keyword arguments must equal the variable name.
        :return: list containing floats, representing the masses of the particles in GeV
        """

        if not self._equations:
            return []

        #If mass function has not yet been created, create it now:
        if not '_massFunctions' in self.__dict__:
            self._getMassFunction()

        #Create dictionary with input values
        xValues = {}
        for xv in self._xvars:
            if not str(xv) in xMass:  #Missing a variable
                self.error("Input variable %s missing for computing mass" %xv)
                return []
            value = xMass[str(xv)]
            if type(value) in [ str ]:
                self.warn(f"Input variable ''{xv}'' has a string value of ''{value}''. Will skip entry." )
                return []
            xValues[str(xv)] = value

        parametersMap = [mfunc(**xValues) for mfunc in self._massFunctions]
        widthArray = [mfunc(**xValues) for mfunc in self._widthFunctions]
        combinedArray = []
        # print ( "parametersMap", parametersMap, "widthArray", widthArray, "widthIndices", self._widthIndices, "xmass", xMass )
        widthCtr=0
        for i,m in enumerate(parametersMap):
            tmp = m
            if i in self._widthIndices:
                tmp = (m,widthArray[widthCtr])
                widthCtr+=1
            combinedArray.append ( tmp )
        return combinedArray

    def _setXYFunction(self):

        """
        Using the equations defined for the axes (branch),
        builds a function to compute the x,y,z values for a given
        mass array. It verifies the number of variables appearing in
        equations and solve for them. The system should not be underconstrained.
        :return: lambdify function
        """

        self._xyFunction = {}
        self._xvars = []
        self._nArguments = 0
        if not self._equations:
            return

        xvars = []
        for eq in self._equations:
            for v in eq.free_symbols:
                if v in allvars and not v in xvars:
                    xvars.append(v)

        #Vars defines the number of variables to be solved for:
        nvars = len(xvars)
        neqs = len(self._equations)
        if nvars > neqs:
            logger.error('Underconstrained system. We have %i variables and %i equations' %(nvars,neqs))
            sys.exit()
        #Solve for variables in vars using nvars equations:
        for eqs in permutations(self._equations,nvars):
            xy = solve(eqs,xvars,dict=True)
            if not xy:
                continue
            if not isinstance(xy,list) or len(xy) > 1:
                logger.error("Something wrong with the result from solve: %s" %str(xy))
                sys.exit()
            else:
                xy = xy[0]
            #Check solution:
            if len(xy) == nvars:
                break
            else:
                xy = dict([[v,None] for v in xvars]) #Create dictionary with None values

        for sol in xy.values():
            if not sol:
                logger.error("Could not solve the equations for the x,y,... values.\nCheck the mass plane definition.")
        self._xy = xy
        self._xvars = sorted(self._xy.keys(), key= lambda xv: str(xv))  #Variables appearing in branch in correct order

        #Define xy function as dictionary:
        self._xyFunction = {}
        #dummify=False allows to keep MassA,MassB,... as valid argument keywords:
        #(make sure the MassA,MassB,.. values are passed as keywords)
        for xv in self._xvars:
            self._xyFunction[xv] = _lambdify(self._massVars+self._widthVars,xy[xv],'math',dummify=False)
        self._nArguments = nvars

    def tuplesInMassContainer ( self, parametersMap ):
        for im,mass in enumerate(parametersMap):
            if type(mass)==tuple: ## the old way
                return True
        return False

    def warn ( self, line ):
        if not line in self.hasWarned:
            self.hasWarned[line]=0
        self.hasWarned[line]+=1
        if self.hasWarned[line]<2:
            logger.warning ( line )

    def error ( self, line ):
        if not line in self.hasWarned:
            self.hasWarned[line]=0
        self.hasWarned[line]+=1
        if self.hasWarned[line]<2:
            logger.error ( line )

    def getXYValues(self,parametersMap,widthArray=None):

        """
        translate a mass array (for single branch) to a point of the plot

        :param parametersMap: list containing  floats, representing
        the masses of the particles in GeV
        :return: None if the mass array does not satify the mass equations.
                Otherwise, returns a dictionary:
                {'x' : x-value in GeV as float, 'y' : y-value in GeV as float,...}
        """
        # print ( f"@@D getXYValues {parameterMap}" )
        if not parametersMap:
            return {}

        if not '_xyFunction' in self.__dict__:
            self._setXYFunction()

        massInput = {}
        if False:
            print ( "X parametersMap", parametersMap )
            print ( "X widthArray", widthArray )
            print ( "X _massVars", self._massVars )
            print ( "X _widthVars", self._widthVars )
        #    len(parametersMap) == len(self._massVars) + len(self._widthVars) and \
        if len(parametersMap)>len(self._massVars) and len(self._widthVars)>0 and \
            widthArray == None:
            ## it seems the widths ended up in the mass array
            widthArray = parametersMap[1::2]
            parametersMap = parametersMap[0::2]
        if self.tuplesInMassContainer ( parametersMap ):
            ## there are tuples, do it the old way
            for im,mass in enumerate(parametersMap):
                if type(mass) in [ tuple ]:
                    massInput[ str(self._massVars[im]) ] = mass[0]
                    massInput[ str(self._widthVars[im]) ] = mass[1]
                else:
                    massInput[ str(self._massVars[im]) ] = mass
        else:
            for im,mass in enumerate(parametersMap):
                if False:
                    print ( "----------------" )
                    print ( "mass", mass )
                    print ( "parametersMap", parametersMap )
                    print ( "widthArray", widthArray )
                    print ( "im", im )
                    print ( "massVars", self._massVars )
                    print ( "widthVars", self._widthVars )
                if im < len(self._massVars):
                    massInput[ str(self._massVars[im]) ] = mass
        if widthArray is None:
            wv = str(self._widthVars[im])
            if not wv in massInput:
                massInput[wv]=None
            #for im,width in enumerate(parametersMap):
            #    massInput[ str(self._widthVars[im]) ] = None
        else:
            for im,width in enumerate(widthArray):
                if im < len(self._widthVars):
                    massInput[ str(self._widthVars[im]) ] = width
        #Define dictionary with mass variables and values
        #massInput = dict([[str(self._massVars[im]),mass] for im,mass in enumerate(parametersMap)])
        xValues = {}
        #Get the function for each x,y,.. variable and compute its value
        for l in [ "A", "B", "C" ][:len(parametersMap)]:
            if not "Mass%s" % l in massInput.keys():
                massInput["Mass%s" % l] = None
            if "Mass%s" % l in massInput.keys() and \
                not "Width%s" % l in massInput.keys(): ## FIXME why is this needed???
                massInput["Width%s" % l ]=None
        #print ( "[getXYValues] massInput", massInput )
        #print ( "[getXYValues] xyFunc", self._xyFunction, str(self._xyFunction) )
        #print ( "parametersMap", parametersMap )
        """import IPython
        IPython.embed()
        sys.exit()"""
        for xv,xfunc in self._xyFunction.items():
            fexpr = str ( xfunc.expr )
            cleanedInput = {}
            for k,v in massInput.items():
                if not k in fexpr:
                    line = f"key {k} is not in func {fexpr}!!"
                    self.warn ( line )
                else:
                    cleanedInput[k]=v
            xValues[str(xv)] = xfunc(**cleanedInput)

        #Now check if the x,y,.. values computed give the parametersMap back:
        newMass = self.getParticleMasses(**xValues)

        def isFloat ( x ):
            return isinstance(x,(np.floating,float))

        def distance ( x, y ):
            ## the distance between x and y
            ## I dont fully understand why there cases where x has a width
            ## and y doesnt ....
            #assert ( type(x) == type(y) )
            if isFloat(x) and type(y)==tuple:
                return abs(x-y[0])
            if isFloat(y) and type(x)==tuple:
                return abs(x[0]-y)
            if isFloat(x) and isFloat(y):
                return abs(x-y)
            assert ( type(x) == tuple )
            d=0.
            for xi,yi in zip ( x, y ):
                d+= ( xi-yi)**2
            return sqrt ( d)

        for im,m in enumerate(newMass[:len(parametersMap)]):
            ma=parametersMap[im]
            d = distance(m,ma )
            if d > 0.11: #Masses differ
                return None
        # print ( "xValues", xValues )
        return xValues

    def __str__(self):

        string =''
        for equation in self._equations:
            if not "==" in str(equation):
                if len(string)>0:
                    string+="_"
                string += str ( equation ).replace(" ","")
            else:
                if string: string = '%s_'%string
                string = '%sEq(%s,%s)' %(string, \
                str(equation).split('==')[0].strip().replace(' ',''), \
                str(equation).split('==')[1].strip().replace(' ',''))
        return string

class WildAxes(Axes):

    """
    Holds the axes information for a wildcard branch ('*') of a singe mass plane.
    No units supported!
    """

    def __init__(self, massEqs,massVars):
        Axes.__init__(self,massEqs,massVars)

    @classmethod
    def fromConvert(cls, massEqs):

        """
        build an instance of Axes from the given parameters

        :param massEqs:  Full list of equations for the branch masses.
                        Each list entry must be a Equalty-object in terms of x,y,z.
        :return: Axes-object
        """

        return cls([],[])

    def getXYValues(self,parametersMap):

        return None

    def getParticleMasses(self,**xMass):

        return '*'
