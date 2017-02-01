#!/usr/bin/env python

"""
.. module:: massPlaneObjects
   :synopsis: Holds object representing one mass plane

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys
from sympy import var, Eq, lambdify, solve, N
from itertools import permutations
from smodels_utils.dataPreparation.dataHandlerObjects import DataHandler,ExclusionHandler
import string
import logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

#All possible plane variables are defined here:
x, y, z = var('x y z')
allvars = [x,y,z]  #Order assumed for the data columns
     
class MassPlane(object):
    """
    Holds all information related to one mass plane
    a mass plane is defined by their axes.
    The variables defined in infoAttr are passed to the corresponding
    txname to be written in txname.txt
    """
    
    infoAttr = ['figureUrl','dataUrl','axes']
    allowedDataLabels = ['efficiencyMap','upperLimits','expectedUpperLimits',
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
        for i,brMasses in enumerate(massArray):
            if not isinstance(brMasses,list):
                logger.error("Mass array must be in the format [[m1,m2,..],[m3,m4,..]]")
                sys.exit()
            self.setBranch(branchNumber=i,branchMasses=brMasses)
        
        #Count mass plane dimensions:
        xvars = []
        for br in self.branches:
            for xvar in br._xvars:
                if not xvar in xvars:
                    xvars.append(xvar)
        dimensions = len(xvars)
        self.dimensions = dimensions
        self._exclusionCurves = []
        #Define the default labels for the input axes variables
        #(relevant for computing the masses from x,y,z...)
        self.axesLabels = [str(xv) for xv in allvars][:dimensions]
        
        self.axes = massArray       
        self.figure = None
        self.figureUrl = None

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
            self.branches.append(Axes.fromConvert(branchMasses))
        else:
            self.branches[branchNumber] = Axes.fromConvert(branchMasses)

    def setSources(self,dataLabels,dataFiles,dataFormats,objectNames=None,indices=None,units=None):
        """
        Defines the data sources for the plane.
        
        :param dataLabels: Single string with the data label or list of strings with the dataLabels
                          possible data laels are defined in allowedDataLabels
                          (e.g. efficiencyMap, upperLimits, expectedUpperLimits,...)
        :param datafiles: Single string with the file path or list of strings with the file paths
                          to the data files.
        :param dataFormats: Single string with the file format or list of strings with the file formats
                          for the data files.
        
        :param objectName: name of object stored in root-file or cMacro or list of object names                         
        :param indices: index of object in listOfPrimitives of ROOT.TCanvas or lis of indices
        :param units: Unit string for objects (e.g. 'fb',None,'pb',...)
        """

        #Make sure input is consistent:
        if isinstance(dataFiles,list):
            if indices is None:
                indices = [None]*len(dataFiles)
            if objectNames is None:
                objectNames = [None]*len(dataFiles)
            if units is None:
                units = [None]*len(dataFiles)                
            if not isinstance(dataLabels,list) or len(dataLabels) != len(dataFiles):
                logger.error("dataLabels and dataFiles are not consistent:\n %s \n %s" %(dataLabels,dataFiles))
                sys.exit()
            if not isinstance(dataFormats,list) or len(dataFormats) != len(dataFiles):
                logger.error("dataFormats and dataFiles are not consistent:\n %s \n %s" %(dataFormats,dataFiles))
                sys.exit()                
            if not isinstance(indices,list) or len(indices) != len(dataFiles):
                logger.error("indices and dataFiles are not consistent:\n %s \n %s" %(indices,dataFiles))
                sys.exit()
            if not isinstance(objectNames,list) or len(objectNames) != len(dataFiles):
                logger.error("objectNames and dataFiles are not consistent:\n %s \n %s" %(objectNames,dataFiles))
                sys.exit()
                                
        elif not isinstance(dataFiles,str):
            logger.error('dataFiles must be a list or a single string')
        else:
            if not isinstance(dataLabels,str):
                logger.error("dataLabels and dataFiles are not consistent")
                sys.exit()
            if not isinstance(dataFormats,str):
                logger.error("dataFormats and dataFiles are not consistent")
                sys.exit()      
            dataFiles = [dataFiles]
            dataLabels = [dataLabels]
            indices = [indices]
            objectNames = [objectNames]
            
            
        for i,dataFile in enumerate(dataFiles):
            dataLabel = dataLabels[i]
            dataFormat = dataFormats[i]
            index = indices[i]
            objectName = objectNames[i]
            unit = units[i]
            if not dataLabel in self.allowedDataLabels:
                logger.warning("Data label %s is not allowed and will be ignored" %dataLabel)
                continue
            if not 'exclusion' in dataLabel.lower():
                #Initialize a data handler
                dataObject = DataHandler(dataLabel,self.dimensions)
            else:
                dataObject = ExclusionHandler(dataLabel)
                self._exclusionCurves.append(dataObject)
            #Set source of object
            dataObject.setSource(dataFile, dataFormat, objectName, index)
            dataObject.unit = unit
            #Store it as a mass plane attribute:            
            setattr(self,dataLabel,dataObject)
        
    def getParticleMasses(self,**xMass):

        """
        Translate a point of the plot, given by x- and y-values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
                     Keyword arguments must equal the variable name.
        :return: list containing two other lists. Each list contains floats, representing
        the masses of the particles of each branch in GeV
        """
        
        massArray = [br.getParticleMasses(**xMass) for br in self.branches]
        return massArray
                  
    def getXYValues(self,massArray):

        """
        translate a mass array to a point of the plot

        :param massArray: list containing two other lists. Each list contains floats,
        representing the masses of the particles of each branch in GeV
        :raise massArrayLenError: if length of mass array is unequal 2
        :raise unequalXYValuesError: if the branches return different values for x or y
        :return: None if mass array do not met the conditions of one branch
        else: [x-value in GeV as float, y-value in GeV,.. as floats].
        The list is sorted alphabetically according to the variable labels
        """
        
        if len(massArray) != len(self.branches):
            logger.error("Mass array inconsistent with branches length")
            sys.exit()
        xyArray = {}
        for i,mass in enumerate(massArray):
            xyDict = self.branches[i].getXYValues(mass)
            if xyDict is None:
                return None
            for xvar,value in xyDict.items():
                if xvar in xyArray:
                    if abs(xyArray[xvar]-value)/abs(xyArray[xvar]+value) > 0.0001:
                        return None
                xyArray[xvar] = value
        
        xValues = [xvar[1] for xvar in sorted(xyArray.items(), key = lambda xx: xx[0])]
        
        return xValues


class Axes(object):

    """
    Holds the axes information for one branch of a singe mass plane.
    No units supported!
    """

    def __init__(self, massEqs,massVars):

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
        
        #Define mass variables:
        massVars = []
        for im in range(len(massEqs)):            
            massVars.append(var('Mass'+string.ascii_uppercase[im]))        
        
        #New format:
        allEqs = []
        for im,massEq in enumerate(massEqs):
            #Create mass variable (upper case for first branch and lower case for second)
            eq = Eq(massVars[im],N(massEq,5))  
            allEqs.append(eq)
            
            allEqs = sorted(allEqs, key = lambda eq: eq.args[0].name)
        
        return cls(allEqs,massVars)
        
    def _getMassFunction(self):

        """
        Build a function to compute the mass array for given x,y, .. values.
        The input variables are the ones define in self._xvars.
        :return: lambdify function which returns the mass array given the input variables.
        """
        
        #Mass variables:
        masses = self._massVars
        #Solve equation for masses
        s = solve(self._equations,masses,dict=True)[0]
        #dummify=False allows to keep x,y,z... as valid argument keywords:
        #(make sure the x,y,z values are passed as keywords)
        self._massFunctions = []
        for m in self._massVars:
            self._massFunctions.append(lambdify(self._xvars,s[m],'math',dummify=False))

    def getParticleMasses(self,**xMass):

        """
        translate a point of the plot, given by x,y,.. values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
                     Keyword arguments must equal the variable name.
        :return: list containing floats, representing the masses of the particles in GeV
        """

        
        #If mass function has not yet been created, create it now:
        if not '_massFunctions' in self.__dict__:
            self._getMassFunction()
        
        #Create dictionary with input values
        xValues = {}
        for xv in self._xvars:
            if not str(xv) in xMass:  #Missing a variable
                logger.error("Input variable %s missing for computing mass" %xv)
                return None
            xValues[str(xv)] = xMass[str(xv)]
    
        massArray = [mfunc(**xValues) for mfunc in self._massFunctions]
        return massArray

    def _setXYFunction(self):

        """
        Using the equations defined for the axes (branch),
        builds a function to compute the x,y,z values for a given
        mass array. It verifies the number of variables appearing in
        equations and solve for them. The system should not be underconstrained.
        :return: lambdify function
        """
        
        xvars = []
        for eq in self._equations:
            for v in [x,y,z]:
                if v in eq.free_symbols and not v in xvars:
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
            self._xyFunction[xv] = lambdify(self._massVars,xy[xv],'math',dummify=False)
        self._nArguments = nvars

    def getXYValues(self,massArray):

        """
        translate a mass array (for single branch) to a point of the plot

        :param massArray: list containing  floats, representing
        the masses of the particles in GeV
        :return: None if the the mass array does not satify the mass equations.
                Otherwise, returns a dictionary: 
                {'x' : x-value in GeV as float, 'y' : y-value in GeV as float,...}
        """

        if not '_xyFunction' in self.__dict__:
            self._setXYFunction()
            
        #Define dictionary with mass variables and values
        massInput = dict([[str(self._massVars[im]),mass] for im,mass in enumerate(massArray)])
        
        xValues = {}
        #Get the function for each x,y,.. variable and compute its value
        for xv,xfunc in self._xyFunction.items():
            xValues[str(xv)] = xfunc(**massInput)
           
        
        #Now check if the x,y,.. values computed give the massArray back:
        newMass = self.getParticleMasses(**xValues)
        for im,m in enumerate(newMass):
            if abs(m-massArray[im])/abs(m+massArray[im]) > 0.0001: #Masses differ
                return None
        
        return xValues

    def __str__(self):

        string =''
        for equation in self._equations:
            # print "equation=%s %s" % ( type(equation),equation )
            if not "==" in str(equation):
                if len(string)>0:
                    string+="_"
                string += str ( equation ).replace(" ","")
            else:
                if string: string = '%s_'%string
                string = '%sEq(%s,%s)' %(string, \
                str(equation).split('==')[0].strip().replace(' ',''), \
                str(equation).split('==')[1].strip().replace(' ',''))
                #print "string= >>%s<<" % string
        return string

