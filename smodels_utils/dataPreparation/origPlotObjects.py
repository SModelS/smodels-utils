#!/usr/bin/env python

"""
.. module:: origPlotObjects
   :synopsis: Holds object representing one original plot, given by expirimentalists

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""

import sys 
from sympy import var, Eq, lambdify, solve, sympify

xValue = var('xValue')
x, y = var('x y')
mother, lsp = var('mother lsp')


class OrigPlot(object):
    
    def __init__(self, MotherEq, lspEq, *interEq):
       
        self._equations = []
        self._equations.append(MotherEq)
        for interEquation in interEq:
                self._equations.append(interEquation)
        self._equations.append(lspEq)
            
    @classmethod
    def fromString(cls, string):
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
        
        motherEq = Eq(mother,motherMass)
        lspEq = Eq(lsp,lspMass)
        interEqs = []
        for k, v in interMasses.iteritems():
            eq = Eq(var(k.replace('Mass','')), v)
            interEqs.append(eq)
        interEqs = sorted(interEqs, key = lambda eq: eq.args[0].name)
        for i,eq in enumerate(interEqs):
            if not eq.args[0].name == 'inter%s' %i:
                Errors().interMass()
        return cls(motherEq , lspEq, *interEqs)
        
    def _getMassFunction(self,equationNr, particle):
        
        mass = solve(self._equations[equationNr],particle)
        massFunction = lambdify([x,y],mass,'math')
        return lambda xMass,yMass: massFunction(xMass,yMass)[0]
        
    def getParticleMasses(self,xMass,yMass):
        
        #if not '_massFuctions' in self.__dict__:
        if True:
            self._massFuctions = []
            for i,eq in enumerate(self._equations):
                self._massFuctions.append(self._getMassFunction(i, eq.args[0]))

        particleMasses = []
        for function in self._massFuctions:
            particleMasses.append(function(xMass,yMass))
        return particleMasses
        
    def _setXYFunction(self):
        
        breaking = False
        for equation1 in self._equations:
            for equation2 in self._equations:
                if equation1 == equation2: continue
                xy = solve([equation1,equation2],[x,y])
                if x in xy and y in xy: 
                    breaking = True
                    break
            if breaking == True: break
        self._xy = xy
        particles = [eq.args[0].name for eq in self._equations]
        self._xyFunction = lambdify(particles,[xy[x],xy[y]],'math')
        
        
    def getXYValues(self,massArray):
            
        if not '_xyFunction' in self.__dict__:
            self._setXYFunction()
        if self.inOrigPlot(massArray):
            return self._xyFunction(*massArray)
        return None
        
    def inOrigPlot(self, massArray):
        
        if len(massArray) != len(self._equations):
            return False
        
        if not '_xy' in self.__dict__:
            self._setXYFunction()
        
        equations = []
        for eq in self._equations:
            equation = eq.subs(x,self._xy[x])
            equation = equation.subs(y,self._xy[y]) 
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
        #return equation.subs(massDublets)
        
    def __str__(self):
        
        string =''
        for equation in self._equations:
            if string: string = '%s_'%string
            string = '%sEq(%s,%s)' %(string, \
            str(equation).split('==')[0].strip().replace(' ',''), \
            str(equation).split('==')[1].strip().replace(' ',''))
        return string
        
    def __eq__(self, other):
        
        return str(self) == str(other)
        
        
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
        