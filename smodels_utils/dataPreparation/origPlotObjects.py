#!/usr/bin/env python

"""
.. module:: origPlotObjects
   :synopsis: Holds object representing one original plot, given by expirimentalists

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""

from sympy import var, Eq, lambdify, solve, sympify

xValue = var('xValue')
x, y = var('x y')
mother, inter, lsp = var('mother inter lsp')


class OrigPlot(object):
    
    def __init__(self, MotherEq, lspEq, *interEq):
       
        self._equations = []
        self._equations.append(MotherEq)
        self._equations.append(lspEq)
        for interEquation in interEq:
            if isinstance(interEquation,Eq):
                self._equations.append(interEquation)
            
    @classmethod
    def fromString(cls, string):
        
        equations = string.split('_')
        if len(equations) > 3:
            logger.error('Current implementation only work for decays with max.' + \
            '3 particles, got %s particles' %len(equations))
            sys.exit()
        motherEq = sympify(equations[0])
        lspEq = sympify(equations[1])
        if len(equations) == 3:
            interEq = sympify(equations[2])
        else:
            interEq = None
        return cls(motherEq, lspEq, interEq)
       
    @classmethod  
    def fromConvert(cls, motherMass = None, interMass = None, lspMass = None):
        
        motherEq = Eq(mother,motherMass)
        if interMass:
            interEq = Eq(inter,interMass)
        else:
            interEq = None
        lspEq = Eq(lsp,lspMass)
        return cls(motherEq , lspEq, interEq)
        
    def _getMassFunction(self,equationNr, particle):
        
        mass = solve(self._equations[equationNr],particle)
        massFunction = lambdify([x,y],mass,'math')
        return lambda xMass,yMass: massFunction(xMass,yMass)[0]
        
    def getParticleMasses(self,xMass,yMass):
        
        #if not '_massFuctions' in self.__dict__:
        if True:
            self._massFuctions = []
            self._massFuctions.append(self._getMassFunction(0, mother))
            if len(self._equations) == 3:
                self._massFuctions.append(self._getMassFunction(2, inter))
            self._massFuctions.append(self._getMassFunction(1, lsp))

        
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
        self._xyFunction = lambdify([mother,inter,lsp],[xy[x],xy[y]],'math')
        
        
    def getXYValues(self,massArray):
        
        motherMass = massArray[0]
        interMass = 0
        if len(massArray) == 3: interMass = massArray[1]
        lspMass = massArray[1]
        if len(massArray) == 3: lspMass = massArray[2]
        
        if not '_xyFunction' in self.__dict__:
            self._setXYFunction()
        if self.inOrigPlot(motherMass, interMass, lspMass):
            return self._xyFunction(motherMass,interMass,lspMass)
        return None
        
    def inOrigPlot(self,motherMass, interMass, lspMass):
        
        if not '_xy' in self.__dict__:
            self._setXYFunction()
        
        for eq in self._equations:
            equation = eq.subs(x,self._xy[x])
            equation = equation.subs(y,self._xy[y]) 
            if equation != True: break
        return equation.subs([(mother,motherMass),(inter,interMass),\
        (lsp,lspMass)])
        
    def __str__(self):
        
        string =''
        for equation in self._equations:
            if string: string = '%s_'%string
            string = '%sEq(%s,%s)' %(string, \
            str(equation).split('==')[0].strip().replace(' ',''), \
            str(equation).split('==')[1].strip().replace(' ',''))
        return string