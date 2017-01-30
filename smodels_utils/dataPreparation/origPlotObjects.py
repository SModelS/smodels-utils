#!/usr/bin/env python

"""
.. module:: origPlotObjects
   :synopsis: Holds object representing one original plot, given by expirimentalists

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""

import sys
from sympy import var, Eq, lambdify, solve, N
from itertools import permutations
import string
import logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

x, y, z = var('x y z')

class OrigPlot(object):

    """
    Holds the axes information for both branches of a singe mass plane, as Axes-objects
    This class is designed to translate between the x- and y-values of one plot,
    representing one mass plane, and the mass Array holding the masses of the particles
    The mass array consists of a list containing two other lists. the first one contain the
    masses of the SUSY-particles of the first branch as float and the second the masses of
    the second branches.

    No units supported!

    """


    def __init__(self):

        """
        initialize both branches with None
        """

        self.branches = []

    def __nonzero__(self):

        """
        :return: True if both branches are set, else False
        """

        if not self.branches:
            return True
        return False

    @classmethod
    def fromString(cls, string):

        """
        build an instance of OrigPlot from a given string

        :raise unknownStringError: If the string do not met the requirements
        :param string: The string must contain a sequence of equations, separated by '_'.
        The equations have to be readable by sympify as sympy.core.relational.Equality-object.
        The equation should only contain the variables:
        x, y, mother, lsp and inter0, inter1, .... interN
        If the sequence of equations starts with '2*' both branches are assumed to be equal
        if the string consists of 2 sequences of equations separated by '+', the first
        sequence is related to the first branch and the second to the second branch.
        """
        origPlot = OrigPlot()
        origPlot.string = string

        massArray = eval(string)
        for ibr,br in enumerate(massArray):
            origPlot.setBranch(ibr,br)
            
        return origPlot


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
            Errors().massArrayLen(massArray)
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

    def __str__(self):

        """
        :return: String containing a sequence of equations, separated by '_'.
        If both branches are equal, the sequence of equations starts with '2*'
        If the two branches are not equal, the string consists of two sequences of
        equations separated by '+'
        """

        if len(self.branches) == 2 and self.branches[0] == self.branches[1]:
            return '2*%s' %self.branches[0]
        else:
            ret = "+".join([str(br) for br in self.branches])
        return ret


class Axes(object):

    """
    Holds the axes information for one both branch of a singe mass plane.

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
        for im,mass in enumerate(massEqs):            
            massVars.append(var('Mass'+string.ascii_uppercase[im]))        
        
        #New format:
        allEqs = []
        for im,mass in enumerate(massEqs):
            #Create mass variable (upper case for first branch and lower case for second)
            eq = Eq(massVars[im],N(mass,5))  
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

    def __eq__(self, other):

        """
        :return: True if string-representations are equal,
        else False
        """

        return str(self) == str(other)

    def __ne__(self, other):

        """
        :return: False if string-representations are equal,
        else True
        """

        return str(self) != str(other)


class Errors(object):

    def __init__(self):

        self._starLine = '\n************************************\n'

    def interMass(self):

        m = self._starLine
        m = m + 'While defining a massPlane an error in Class Axes occurred:\n'
        m = m + 'unkonown interMass chain. First interMass needs always index 0\n'
        m = m + 'secound interMass (if exist) needs index 1, .....\n'
        m = m + 'please check you convert file'
        m = m + self._starLine
        print(m)
        sys.exit()

    def massArrayLen(self, massArray):

        m = self._starLine
        m = m + 'Error in OrigPlot object, getXYValues:\n'
        m = m + 'massArray must have lengh 2\n'
        m = m + 'got: %s \n' %massArray
        m = m + self._starLine
        print(m)
        sys.exit()

    def unequalXYValues(self):

        m = self._starLine
        m = m + 'Error in OrigPlot object, getXYValues:\n'
        m = m + 'different values for branch_1 and branch_2'
        m = m + self._starLine
        print(m)
        sys.exit()

    def unknownString(self, string):

        m = self._starLine
        m = m + 'Error in OrigPlot.fromString:\n'
        m = m + 'can not interpret equation string:\n'
        m = m + '%s' %string
        m = m + self._starLine
        print(m)
        sys.exit()
