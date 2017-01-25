#!/usr/bin/env python

"""
.. module:: origPlotObjects
   :synopsis: Holds object representing one original plot, given by expirimentalists

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""

import sys
from sympy import var, Eq, lambdify, solve, sympify, N, Float
from standardObjects import round_to_n
from itertools import permutations
import string
import logging
import inspect
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

xValue = var('xValue')
x, y, z = var('x y z')
mother, lsp = var('mother lsp')

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

        self.branch_1 = None
        self.branch_2 = None

    def __nonzero__(self):

        """
        :return: True if both branches are set, else False
        """

        if branch_1 and branch_2:
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



    def setBranch_1(self, motherMass = None, lspMass = None, **interMasses):

        """
        set branch one to give axes

        :param motherMass: mass of mother particle as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        NEW FORMAT: the motherMass may also be the full mass array containing the 'x','y' symbols.
        In this format lspMass and interMasses should not be defined.
        :param lspMass: mass of lightest SUSY-particle as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        :param **interMasses: masses of the intermediated particles as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        """

        if not isinstance(motherMass,list):
            self.branch_1 = \
            Axes.fromConvert(motherMass = motherMass, lspMass = lspMass, **interMasses)
        else:
            self.branch_1 = Axes.fromConvert(motherMass = motherMass)

    def setBranch_2(self, motherMass = None, lspMass = None, **interMasses):

        """
        set branch two to given axes

        :param motherMass: mass of mother particle as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        NEW FORMAT: the motherMass may also be the full mass array containing the 'x','y' symbols.
        In this format lspMass and interMasses should not be defined.
        :param lspMass: mass of lightest SUSY-particle as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        :param **interMasses: masses of the intermediated particles as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        """

        if not isinstance(motherMass,list):
            self.branch_2 = \
            Axes.fromConvert(motherMass = motherMass, lspMass = lspMass, **interMasses)
        else:
            self.branch_2 = Axes.fromConvert(motherMass = motherMass)

    def getParticleMasses(self,*xMass):

        """
        translate a point of th plot, given by x- and y-values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
        :return: list containing two other lists. Each list contains floats, representing
        the masses of the particles of each branch in GeV
        """
        massArray_1 = self.branch_1.getParticleMasses(*xMass)
        massArray_2 = self.branch_2.getParticleMasses(*xMass)
        return [massArray_1, massArray_2]

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
        else: [x-value in GeV as float, y-value in GeV as float]
        """

        if not len(massArray) == 2: Errors().massArrayLen(massArray)
        xy_1 = self.branch_1.getXYValues(massArray[0])
        ## print "xy_1=",xy_1
        xy_2 = self.branch_2.getXYValues(massArray[1])
        if not xy_1 or not xy_2: return None

        for i, value in enumerate(xy_1):
            if value==None or xy_2[i]==None or abs(value - xy_2[i]) > 0.1:
                return self.combine ( xy_1, xy_2 )
                Errors().unequalXYValues()
        return xy_1

    def __str__(self):

        """
        :return: String containing a sequence of equations, separated by '_'.
        If both branches are equal, the sequence of equations starts with '2*'
        If the two branches are not equal, the string consists of two sequences of
        equations separated by '+'
        """

        if self.branch_1 == self.branch_2:
            return '2*%s' %self.branch_1
        return '%s+%s' %(self.branch_1, self.branch_2)




class Axes(object):

    """
    Holds the axes information for one both branch of a singe mass plane.

    No units supported!

    """

    def __init__(self, MotherEq, lspEq=None, *interEq):

        """
        Initialize a list of sympy.core.relational.Equality-object
        Those objects can only contain the variables:
        x, y, mother, lsp and inter0, inter1 ... interN

        :param MotherEq: Equalty-object describing 'mother' in terms of x and y;
                         NEW FORMAT: It can also be the full list of equations for the branch.
                         In this case, lspEq and interEq should not be defined.
        :param lspEq: Equalty-object describing 'lsp' in terms of x and y
        :param *interEq: Equalty-objects describing 'inter0','inter1' ,...
        in terms of x and y
        """

        #Standard format
        if not isinstance(MotherEq,list):
            self._equations = []
            self._equations.append(MotherEq)
            for interEquation in interEq:
                    self._equations.append(interEquation)
            self._equations.append(lspEq)

        #New format
        if isinstance(MotherEq,list):
            self._equations = MotherEq[:]
            
        #Already define the functions and plot dimensions:
        self._setXYFunction()        
        self._xvars = sorted(self._xy.keys(), key= lambda xv: str(xv))  #Variables appearing in branch in correct order
        
        
            
        ## print "Axes ",self._equations

    @classmethod
    def fromString(cls, string):

        """
        build an instance of Axes from a given string

        :param string: The string must contain a sequence of equations, separated by '_'.
        The equations have to be readable by sympify as sympy.core.relational.Equality-object.
        The equation should only contain the variables:
        x, y, mother, lsp and inter0, inter1, .... interN
        :return: Axes-object
        """

        equations = [sympify(eq) for eq in string.split('_')]
        for i, eq in enumerate(equations):
            if eq.args[0].name == 'mother':
                motherEq = equations.pop(i)
        for i, eq in enumerate(equations):
            if eq.args[0].name == 'lsp':
                lspEq = equations.pop(i)
        interEqs = sorted(equations, key = lambda eq: eq.args[0].name)

        return cls(motherEq, lspEq, *interEqs)

    @classmethod
    def fromConvert(cls, motherMass = None, lspMass = None, **interMasses):

        """
        build an instance of Axes from the given parameters

        :param motherMass: mass of mother particle as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        NEW FORMAT: the motherMass may also be the full mass array containing the 'x','y' symbols.
        In this format lspMass and interMasses should not be defined. 
        :param lspMass: mass of lightest SUSY-particle as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        :param **interMasses: masses of the intermediated particles as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        :raise interMAssError: If the variables 'inter' not correctly ordered
        :return: Axes-object
        """

        # print "lspMass=",type(lspMass),lspMass
        
        #Standard input:        
        if not isinstance(motherMass,list):
            motherEq = Eq(mother,motherMass)
            lspEq = Eq(lsp,lspMass)
            if type(lspMass)==float:
                lspEq = Eq(lsp, N(lspMass,2))
            # print "lspEq=",lspEq
            interEqs = []
            for k, v in interMasses.iteritems():
                eq = Eq(var(k.replace('Mass','')), N(v,5) )
                interEqs.append(eq)
            interEqs = sorted(interEqs, key = lambda eq: eq.args[0].name)
            for i,eq in enumerate(interEqs):
                if not eq.args[0].name == 'inter%s' %i:
                    Errors().interMass()
            return cls(motherEq , lspEq, *interEqs)
        
        #New format:
        if isinstance(motherMass,list):
            allEqs = []
            for im,mass in enumerate(motherMass):
                #Create mass variable (upper case for first branch and lower case for second)
                massVariable = var('Mass'+string.ascii_uppercase[im])
                eq = Eq(massVariable,N(mass,5))  
                allEqs.append(eq)
                
                allEqs = sorted(allEqs, key = lambda eq: eq.args[0].name)
            
            return cls(allEqs)
        

    def _getMassFunction(self):

        """
        build a function to compute the mass of a particle for given x- and y-values
        :param equation: equation in self._equations
        :param particle: name of the variable related to the requested particle mass
        :return: lambdify function
        """
        
        masses = [eq.args[0] for eq in self._equations]
        xvars = self._xvars
        s = solve(self._equations,masses,dict=True)[0]
        massSolution = [s[m] for m in masses]
        massFunction = lambdify(xvars,massSolution,'math')
        return lambda *xMass: massFunction(*xMass)[0]

    def getParticleMasses(self,*xMass):

        """
        translate a point of the plot, given by x,y,.. values to a mass Array
        :param xMass: x,y,... values (length depends on the number of dimensions of the plot)
        :return: list containing floats, representing the masses of the particles in GeV
        """

        
        if not '_massFunctions' in self.__dict__:
            self._massFunctions = self._getMassFunction()
                
        particleMasses = []
        for function in self._massFuctions:
            particleMasses.append(function(*xMass))

        return particleMasses


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
        else: [x-value in GeV as float, y-value in GeV as float]
        """

        if not '_xyFunction' in self.__dict__:
            self._setXYFunction()
        if self.inOrigPlot(massArray):
            return self._xyFunction(*massArray)
        return None

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
