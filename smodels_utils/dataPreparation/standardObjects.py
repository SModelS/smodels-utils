#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds objects used by convert.py to create info.txt, sms.root, sms.py and newSms.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   

import sys, logging, os, ROOT
from copy import deepcopy
import inputObjects 
from datetime import date


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

class VertexChecker(object):

    def __init__(self, txNameObj):
        
        self.txName = txNameObj.name
        self.kinConstraints = self._getKinConstraints(txNameObj)
        
        
    def getOffShellVertices(self, massArray):

        offShellVertices = []
        massDeltaArray = [[],[]]
        for i, branch in enumerate(massArray):
            for j, mass in enumerate(branch):
                if j == 0: continue
                massDelta =branch[j-1] - mass
                massDeltaArray[i].append(massDelta)
                
        for kinConstraint in self.kinConstraints:
            for i, branch in enumerate(kinConstraint):
                # print "branch=",branch,"massDeltaArray=",massDeltaArray
                if len(branch) != len(massDeltaArray[i]):
                    Errors().decayChain(self.txName,\
                    len(branch),len(massDeltaArray[i]))
                for j, massDelta in enumerate(branch):
                    if massDeltaArray[i][j] <= massDelta:
                        if not (i,j) in offShellVertices:
                            offShellVertices.append((i,j))
        return offShellVertices
        
    def _getKinConstraints(self, txNameObj):
        
        massDict = {'Z': 86., 'W': 76.,'t': 169.,'h': 118}
        startString = '[[['
        endString = ']]]'
        kinConstraints = []
        if not hasattr(txNameObj.on, 'constraint'):
            Errors().missingOnConstraint(txNameObj.name)
        constraint = txNameObj.on.constraint
        
        if constraint == 'not yet assigned': return None
        if not isinstance(constraint, str):
            Errors().constraint(self.txName, constraint)
        if not endString in constraint or not startString in constraint:
            Errors().constraint(self.txName, constraint)
        for i in range(len(constraint)):
            if constraint[i:i + len(startString)] == startString:
                start = i
            if constraint[i:i + len(endString)] == endString:
                end = i + len(endString)
                kinConstraints.append(constraint[start:end])
        try:
            kinConstraints = \
            [eval(constraint) for constraint in kinConstraints]
        except:
            Errors().constraint(self.txName, constraint)
        for i, constraint in enumerate(kinConstraints):
            for j, branch  in enumerate(constraint):
                for k, vertex in enumerate(branch):
                    massSum = 0.
                    for particle in vertex:
                        particle = particle.replace('+','')
                        particle = particle.replace('-','')
                        if particle in massDict:
                            massSum = massSum + massDict[particle]
                    kinConstraints[i][j][k] = massSum
        return kinConstraints
        
    def __nonzero__(self):
        
        return bool(self.kinConstraints)
        
        
class StandardDataList(list):
    
    def __init__(self, massUnit = '*GeV', valueUnit = '*pb'):
        
        self.massUnit = massUnit
        self.valueUnit = valueUnit
        
    
    def append(self, massArray, limit):
        
        self._checkMasses(massArray)
        array = [[],[]]
        for i in range(len(massArray)):
            array[i] = ['%s%s' %(mass, self.massUnit) for mass in massArray[i]]
        inLimit = False
        for point in self:
            if array ==  point[0]:
                oldlimit = float(point[1][:-3])
                if abs(limit-oldlimit) > 0.0001:
                    Errors().limitDifference\
                    (array, point[1], '%s%s' %(limit,self.valueUnit))
                inLimit = True
                break
        limit = '%s%s' %(limit,self.valueUnit)
        if not inLimit:
            list.append(self, [array, limit])
            
    def _checkMasses(self, massArray):
    
        for array in massArray:
            for i, mass in enumerate(array):
                if mass < 0.0: Errors().negativMass(massArray)
                if i > 0: 
                    if mass > previousMass: Errors().massOrder(massArray)
                previousMass = mass
                
    
            
    def __str__(self):
        
        string = '['
        
        for i, entry in enumerate(self):
            if not (i+1) == len(self):
                string = '%s%s,\n' %(string, entry)
                continue
            string = '%s%s]' %(string, entry)
        return string.replace("'","")
        
     
        
class StandardExclusions(list):
    
    def __init__(self, name):
        
        self.name = name
        list.__init__(self)
        
    def addMassPlane(self, massPlaneObj):
        
        for exclusion in massPlaneObj.origExclusions:
            if not exclusion: continue
            stGraph = ROOT.TGraph()
            name = '%s_%s' %(exclusion.name, massPlaneObj.origPlot)
            stGraph.SetName(name)
            stGraph.SetTitle(name)
            for i,point in enumerate(exclusion):
                stGraph.SetPoint(i,point[0],point[1])
            stGraph.SetLineColor ( ROOT.kBlack )
            if 'expected' in exclusion.name:
                stGraph.SetLineColor ( ROOT.kRed )
            stGraph.SetLineStyle(1)
            if 'P1' in exclusion.name or 'M1' in exclusion.name:
                stGraph.SetLineStyle(2)
            self.append(stGraph)
            
class StandardTWiki(object):
    
    def __init__(self, metaInfo):
        
        self.id = self.idFormat(metaInfo)      
        self.txNames = []
        self.axes = []
        self.figures = []
        self.limits = []
        self.exclusions = []
        
    def __str__(self):
        
        
        string = '||%s||' %(self.id)
        for attr in \
        [self.txNames, self.axes, self.figures, self.limits, self.exclusions]:
            string = string + '<<BR>>'.join(attr) + '||'
        return string + '\n'
    
    def addMassPlane(self, txName, plane):
            
        self.txNames.append(self.link('smsDictionary#%s' %txName, txName))
        self.axes.append(str(plane.origPlot))
        self.figures.append(self.link(plane.figureUrl, plane.figure))
        self.limits.append(self.objectFormat(plane.origLimits))
        self.exclusions.append(self.objectFormat(plane.origExclusions))

    def link(self, url, label):
        
        return '[[%s|%s]]' %(url, label)    
      
    def idFormat(self, metaInfo):
        
        ID = self.link(metaInfo.url, metaInfo.id)
        if hasattr(metaInfo, 'superseded_by'):
            ID = '%s<<BR>>ss_by: %s' %(ID, metaInfo.superseded_by)
        return ID
    
    def objectFormat(self, objectList):
        
        string = ''
        for obj in objectList:
            if not obj.dataUrl: continue
            label = 'OBS'
            if 'expected' in obj.name: label = 'EXP'
            if 'M1' in obj.name: label = '-'
            if 'P1' in obj.name: label = '+'
            string = string + self.link(obj.dataUrl, label)
        if not string: string = 'None'
        return string
      
    
class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def constraint(self, txName, constraint):
        
        m = self._starLine
        m = m + 'In VertexChecker: Error while reading the onshell constraint '
        m = m + 'for txName: %s\n' %txName
        m = m + "constraint have to be of form:\n"
        m = m + "\"[[['particle',...],...]][['particle',...],...]]\"\n"
        m = m + 'got: %s' %constraint
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def decayChain(self, txName, constraintLen, massArrayLen):
        
        m = self._starLine
        m = m + 'In StandardLimits: Error while splitting upperlimits'
        m = m + 'for txName: %s\n' %txName
        m = m + "constraints and topology must have the same"
        m = m + "numbers of vertices\n"
        m = m + 'got:\n'
        m = m + 'vertices in constraint: %s\n' %constraintLen
        m = m + 'vertices in topology: %s' %massArrayLen
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def notAssigned(self, txName):
        
        m = self._starLine
        m = m + "can't split limits for txName: %s because " %txName
        m = m + "constraint is set to 'not yet assigned'\n"
        m = m + "please, set all kinematicRegions propertys of txName"
        m = m + "object to 'False' except of one;\n"
        m = m + "or assign constraints"
        m = m + self._starLine
        print(m)
        sys.exit()
        
        
    def limitDifference(self, massArray, oldLimit, limit):
        
        m = '------------------------\n'
        m = m + "WARNING: massPoint: %s allrady in limits \n" %massArray
        m = m + "but differ in Upperlimit: %s v.s. %s" %(oldLimit, limit)
        m = m + '\n------------------------'
        print(m)
             
    def kinRegionSetter(self, txName, name, value):
    
        m = self._starLine
        m = m + "in txName %s'\n" %txName
        m = m + "setter for propertsy %s must be of bool type or 'auto'\n"\
        %(name)
        m = m + 'got: %s' %value
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def missingOnConstraint(self, txName):
        
        m = self._starLine#
        m = m + "in txName %s: on.constraint not set\n" %txName
        m = m + "onShell constraint have to be set for automated splitting\n"
        m = m + 'please use: %s.on.constraint =' %txName
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def negativMass(self, massArray):
        
        m = self._starLine#
        m = m + "Error in StandardDataList: there is a negativ Mass:\n"
        m = m + "%s\n" %massArray
        m = m + 'please check your mass plane deffintion at convert.py'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def massOrder(self, massArray):
    
        m = self._starLine#
        m = m + "Error in StandardDataList\n"
        m = m + "there is a particle with higher mass then the privous one in:\n"
        m = m + "%s\n" %massArray
        m = m + 'please check your mass plane deffintion at convert.py'
        m = m + self._starLine
        print(m)
        sys.exit()
        
        
