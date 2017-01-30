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

        if string[:2] == '2*':
            origPlot.branch_1 = Axes.fromString(string[2:])
            origPlot.branch_2 = Axes.fromString(string[2:])
            return origPlot
        if ')+Eq(' in string:
            origPlot.branch_1 = Axes.fromString(string.split(')+Eq(')[0] + ')')
            origPlot.branch_2 = Axes.fromString('Eq(' + string.split(')+Eq(')[1])
            return origPlot
        Errors().unknownString(string)



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


    def getParticleMasses(self,*xMass):

        """
        translate a point of th plot, given by x- and y-values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
        :return: list containing two other lists. Each list contains floats, representing
        the masses of the particles of each branch in GeV
        """
        
        massArray = [br.getParticleMasses(*xMass) for br in self.branches]
        return massArray

    def combine(self, xy_1, xy_2 ):
        """ If x appears in branch1, but y appears in branch2 (think e.g. TGQ),
            then we need to combine the two arrays to a single array
        """
        ret=[]
        for a,b in zip (xy_1,xy_2):
            if a==None:
                ret.append(b)
            elif b==None:
                ret.append(a)
            else:
                logger.error ( "cannot combine the two arrays into a single consistent array, a,b=%s,%s" , a,b )
                return None
        return ret

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

        if not len(massArray) != len(self.branches):
            Errors().massArrayLen(massArray)
        xyArray = {}
        for i,mass in enumerate(massArray):
            xyDict = self.branch[i].getXYValues(mass)
            for xvar,value in xyDict.items():
                if xvar in xyArray and xyArray[xvar] != value:
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

    def __init__(self, massEqs):

        """
        Initialize a list of sympy.core.relational.Equality-object
        Those objects can only contain the variables:
        x, y, z

        :param massEqs: Full list of equations for the branch masses.
                        Each list entry must be a Equalty-object in terms of x,y,z.
        """

        if not isinstance(massEqs,list):
            logger.error("Masses must be a list")
            sys.exit()

        self._equations = massEqs[:]
            
        #Already define the functions and plot dimensions:
        self._setXYFunction()        
        self._xvars = sorted(self._xy.keys(), key= lambda xv: str(xv))  #Variables appearing in branch in correct order
        
        
            
        ## print "Axes ",self._equations


    @classmethod
    def fromConvert(cls, massEqs):

        """
        build an instance of Axes from the given parameters

        :param massEqs:  Full list of equations for the branch masses.
                        Each list entry must be a Equalty-object in terms of x,y,z.
        :return: Axes-object
        """

        # print "lspMass=",type(lspMass),lspMass
        
        #Standard input:        
        if not isinstance(massEqs,list):
            logger.error('Mass must be a list of equations')
        
        #New format:
        allEqs = []
        for im,mass in enumerate(massEqs):
            #Create mass variable (upper case for first branch and lower case for second)
            massVariable = var('Mass'+string.ascii_uppercase[im])
            eq = Eq(massVariable,N(mass,5))  
            allEqs.append(eq)
            
            allEqs = sorted(allEqs, key = lambda eq: eq.args[0].name)
        
        return cls(allEqs)
        

    def _getMassFunction(self):

        """
        Build a function to compute the mass array of a particle for given x,y, .. values.
        The input variables are the ones define in self._xvars.
        :return: lambdify function which returns the mass array given the input variables.
        """
        
        masses = [eq.args[0] for eq in self._equations]
        xvars = self._xvars
        s = solve(self._equations,masses,dict=True)[0]
        massSolution = [s[m] for m in masses]
        #dummify=False allows to keep x,y,z... as valid argument keywords:
        massFunction = lambdify(xvars,massSolution,'math',dummify=False) 
        return lambda **xVals: massFunction(**xVals)

    def getParticleMasses(self,xvalue=None,yvalue=None,zvalue=None):

        """
        translate a point of the plot, given by x,y,.. values to a mass Array
        :param xvalue: Value for the x variable
        :param yvalue: Value for the y variable (optional according to the number of input variables)
        :param zvalue: Value for the z variable (optional according to the number of input variables)
        :return: list containing floats, representing the masses of the particles in GeV
        """

        
        #If mass function has not yet been created, create it now:
        if not '_massFunctions' in self.__dict__:
            self._massFunctions = self._getMassFunction()
            
        #Create dictionary with input values
        xValues = {'x' : xvalue, 'y' : yvalue, 'z' : zvalue}
        #Restrict input variables to the ones require do compute the masses:
        xVals = {}
        for xv in xValues:
            if var(xv) in self._xvars:
                xVals[xv] = xValues[xv]
        
        if len(xVals) != len(self._xvars):
            logger.error("Number of input values and number of variables do not match.")
            return None
         
        return self._massFunctions(**xVals)

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
        particles = [eq.args[0].name for eq in self._equations]        
        self._xyFunction = lambdify(particles,xy.items(),'math')
        self._nArguments = nvars


    def getXYValues(self,massArray):

        """
        translate a mass array (for single branch) to a point of the plot

        :param massArray: list containing  floats, representing
        the masses of the particles in GeV
        :return: None if the d ..mass array do not hold one of the equations in self._equations
        else: dictionary {'x' : x-value in GeV as float, 'y' : y-value in GeV as float,...}
        """

        if not '_xyFunction' in self.__dict__:
            self._setXYFunction()
            
        if not self.inOrigPlot(massArray):
            return None
        
        xValues = self._xyFunction(*massArray)
        if not isinstance(xValues,list) or not len(xValues) == 1:
            logger.error("Error computing x-values from mass array")
            sys.exit()
        return xValues

    def inOrigPlot(self, massArray):

        """
        checks if mass array hold all equations in self._equations

        :return: True if mass array hold all of the equations in self._equations
        else: None
        """

        if len(massArray) != len(self._equations):
            return False

        if not '_xy' in self.__dict__:
            self._setXYFunction()

        equations = []
        for eq in self._equations:
            equation = eq.subs(x,self._xy[x])
            equation = equation.subs(y,self._xy[y])
            try:
                equation = equation.subs(z,self._xy[z])
            except KeyError as e:
                pass
            if equation != True: equations.append(equation)

        massDublets = []
        for i, eq in enumerate(self._equations):
            particle = eq.args[0]
            mass = massArray[i]
            massDublets.append((particle, mass))

        for eq in equations:
            leftSide = eq.args[0]
            rightSide = eq.args[1]
            leftSide = leftSide.subs(massDublets)
            rightSide = rightSide.subs(massDublets)
            if abs(leftSide-rightSide) > 0.000001:
                return False
        return True

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

if __name__ == "__main__":
    axes = "Eq(mother,x)_Eq(lsp,y)+Eq(mother,0.96*x)_Eq(lsp,y)"
    # axes = "Eq(mother,x)_Eq(lsp,0.0)+Eq(mother,y)_Eq(lsp,0.0)"
    # axes = '2*Eq(mother,x)_Eq(inter0,y)_Eq(lsp,60.0)'
    axes = "2*Eq(mother,x)_Eq(inter0,y)_Eq(lsp,z)"
    origPlot = OrigPlot.fromString ( axes )
    x1,y1,z1=150,120,100
    pms=origPlot.getParticleMasses ( x1,y1,z1 )
    print ( "particle masses",pms )
    xyz=origPlot.getXYValues ( pms )
    print ( "xyz values", xyz )
