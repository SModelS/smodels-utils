#!/usr/bin/env python

"""
.. module:: massPlaneObjects
   :synopsis: Holds object representing one mass plane

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys
from sympy import var, Eq, lambdify, solve, N, And, sqrt
from scipy.spatial import Delaunay
from itertools import permutations
from smodels_utils.dataPreparation.dataHandlerObjects import DataHandler,ExclusionHandler
import string
import logging
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

class MassPlane(object):
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

    def __init__(self,txDecay, massArray):
        """
        sets the branches to the given axes and initialize the mass plane related
        values an objects
        :param txDecay: object of type TxDecay
        :param massArray: the full mass array containing equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [[x,y],[x,y]])
        :param lspMass: mass of lightest SUSY-particle as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        :param **interMasses: masses of the intermediated particles as
                              sympy.core.symbol.Symbol, containing only the
                              variables 'x', 'y' and numbers as float
        """

        self.branches = []
        self._txDecay = txDecay
        self.figureUrl = None
        self.dataUrl = None
        self.allInputFiles = []
        for i,brMasses in enumerate(massArray):
            if not isinstance(brMasses,list):
                logger.error("Mass array must be in the format [[m1,m2,..],[m3,m4,..]]")
                sys.exit()
            self.setBranch(branchNumber=i,branchMasses=brMasses)

        self.axes = massArray
        #Store plane variables (x,y,..)
        xvars = []
        for br in self.branches:
            for xvar in br._xvars:
                if not xvar in xvars:
                    xvars.append(xvar)
        self.xvars = xvars #All variables used in defining the axes
        self._exclusionCurves = []



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
        massArray = eval(string)
        massPlane = MassPlane(txname,massArray)

        return massPlane

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
                   objectNames=None,indices=None,units=None,coordinates=None,scales=None):
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
                           objectName, index, unit, coordinate, scale)

    def addSource(self,dataLabel,dataFile,dataFormat=None, objectName=None,index=None,
                  unit=None,coordinateMap=None,scale=None):
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
            dataObject = DataHandler(dataLabel,coordinateMap,self.xvars)
        else:
            #Define the default 1D coordinate mapping for exclusion curves
            if not coordinateMap:
                coordinateMap = {x : 0, y : 1, 'value' : None}
                if not y in self.xvars: # 1d data
                    coordinateMap = {x : 0, 'value' : None}
            dataObject = ExclusionHandler(dataLabel,coordinateMap,self.xvars)
            self._exclusionCurves.append(dataObject)

        dataObject.dataUrl = self.dataUrl
        #Set source of object
        dataObject.setSource(dataFile, dataFormat,
                             objectName, index, unit, scale)
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
        massArray = [br.getParticleMasses(**xMass) for br in self.branches]
        return massArray

    def getXYValues(self,massArray,widthArray=None):

        """
        Translate a mass array to a point of the plot.
        Returns a dictionary with the variable labels as keys and the values as values.

        :param massArray: list containing two other lists. Each list contains floats,
        representing the masses of the particles of each branch in GeV
        :param widthArray: list containing two other lists. Each list contains floats,
        representing the widths of the particles of each branch in GeV. If None,
        we assume a width-independent plane.
        :raise massArrayLenError: if length of mass array is unequal 2
        :raise unequalXYValuesError: if the branches return different values for x or y
        :return: None if mass array do not met the conditions of one branch
        else: {'x': x-value in GeV as float, 'y' : y-value in GeV as float, ..}
        """
        #print ( ">> widthArray", widthArray )
        # print ( ">> massArray", massArray )

        if len(massArray) != len(self.branches):
            logger.error("dimension of mass array (%d) inconsistent with branches length (%d)" % ( len(massArray), len(self.branches) ) )
            sys.exit()
        if widthArray != None and len(widthArray) != len(self.branches):
            logger.error("Width array inconsistent with branches length")
            sys.exit()
        xyArray = {}
        if widthArray == None:
            for i,mass in enumerate(massArray):
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
        for i,(mass,width) in enumerate(zip(massArray,widthArray)):
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

        self.hasWarned = {}
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
                logger.error("Input variable %s missing for computing mass" %xv)
                return []
            value = xMass[str(xv)]
            if type(value) in [ str ]:
                logger.error(f"Input variable ''{xv}'' has a string value of ''{value}''" )
                return []
            xValues[str(xv)] = value

        massArray = [mfunc(**xValues) for mfunc in self._massFunctions]
        widthArray = [mfunc(**xValues) for mfunc in self._widthFunctions]
        combinedArray = []
        # print ( "massArray", massArray, "widthArray", widthArray, "widthIndices", self._widthIndices, "xmass", xMass )
        widthCtr=0
        for i,m in enumerate(massArray):
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

    def tuplesInMassContainer ( self, massArray ):
        for im,mass in enumerate(massArray):
            if type(mass)==tuple: ## the old way
                return True
        return False

    def warn ( self, line ):
        if not line in self.hasWarned:
            self.hasWarned[line]=0
        self.hasWarned[line]+=1
        if self.hasWarned[line]<2:
            logger.warning ( line )

    def getXYValues(self,massArray,widthArray=None):

        """
        translate a mass array (for single branch) to a point of the plot

        :param massArray: list containing  floats, representing
        the masses of the particles in GeV
        :return: None if the mass array does not satify the mass equations.
                Otherwise, returns a dictionary:
                {'x' : x-value in GeV as float, 'y' : y-value in GeV as float,...}
        """
        if not massArray:
            return {}

        if not '_xyFunction' in self.__dict__:
            self._setXYFunction()

        massInput = {}
        if False:
            print ( "X massArray", massArray )
            print ( "X widthArray", widthArray )
            print ( "X _massVars", self._massVars )
            print ( "X _widthVars", self._widthVars )
        #    len(massArray) == len(self._massVars) + len(self._widthVars) and \
        if len(massArray)>len(self._massVars) and len(self._widthVars)>0 and \
            widthArray == None:
            ## it seems the widths ended up in the mass array
            widthArray = massArray[1::2]
            massArray = massArray[0::2]
        if self.tuplesInMassContainer ( massArray ):
            ## there are tuples, do it the old way
            for im,mass in enumerate(massArray):
                massInput[ str(self._massVars[im]) ] = mass[0]
                massInput[ str(self._widthVars[im]) ] = mass[1]
        else:
            for im,mass in enumerate(massArray):
                if False:
                    print ( "----------------" )
                    print ( "mass", mass )
                    print ( "massArray", massArray )
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
            #for im,width in enumerate(massArray):
            #    massInput[ str(self._widthVars[im]) ] = None
        else:
            for im,width in enumerate(widthArray):
                if im < len(self._widthVars):
                    massInput[ str(self._widthVars[im]) ] = width
        #Define dictionary with mass variables and values
        #massInput = dict([[str(self._massVars[im]),mass] for im,mass in enumerate(massArray)])
        xValues = {}
        #Get the function for each x,y,.. variable and compute its value
        for l in [ "A", "B", "C" ][:len(massArray)]:
            if not "Mass%s" % l in massInput.keys():
                massInput["Mass%s" % l] = None
            if "Mass%s" % l in massInput.keys() and \
                not "Width%s" % l in massInput.keys(): ## FIXME why is this needed???
                massInput["Width%s" % l ]=None
        #print ( "[getXYValues] massInput", massInput )
        #print ( "[getXYValues] xyFunc", self._xyFunction, str(self._xyFunction) )
        #print ( "massArray", massArray )
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

        #Now check if the x,y,.. values computed give the massArray back:
        newMass = self.getParticleMasses(**xValues)

        def distance ( x, y ):
            ## the distance between x and y
            ## I dont fully understand why there cases where x has a width
            ## and y doesnt ....
            #assert ( type(x) == type(y) )
            if type(x) in [ float, int ] and type(y)==tuple:
                return abs(x-y[0])
            if type(y) in [ float, int ] and type(x)==tuple:
                return abs(x[0]-y)
            if type(x) in [ float, int ] and type(y) in [ float, int ]:
                return abs(x-y)
            assert ( type(x) == tuple )
            d=0.
            for xi,yi in zip ( x, y ):
                d+= ( xi-yi)**2
            return sqrt ( d)

        for im,m in enumerate(newMass[:len(massArray)]):
            ma=massArray[im]
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


    def getXYValues(self,massArray, width=None):

        return None

    def getParticleMasses(self,**xMass):

        return '*'
