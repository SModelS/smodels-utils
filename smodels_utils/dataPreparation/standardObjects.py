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

    def __init__(self, onShellConstraints):
        
        self.kinConstraints = self._getKinConstraints(onShellConstraints)
        
    def getOffShellVertices(self, massArray_1, massArray_2):
        
        offShellVertices = []
        massArray = [massArray_1, massArray_2]
        massDeltaArray = [[],[]]
        for i, branch in enumerate(massArray):
            for j, mass in enumerate(branch):
                if j == 0: continue
                massDelta =branch[j-1] - mass
                massDeltaArray[i].append(massDelta)
                
        for kinConstraint in self.kinConstraints:
            for i, branch in enumerate(kinConstraint):
                if len(branch) != len(massDeltaArray[i]):
                    Errors().decayChain(self.txName,\
                    len(branch),len(massDeltaArray[i]))
                for j, massDelta in enumerate(branch):
                    if massDeltaArray[i][j] <= massDelta:
                        if not (i,j) in offShellVertices:
                            offShellVertices.append((i,j))
        return offShellVertices
        
    def _getKinConstraints(self, onShellConstraints):
        
        massDict = {'Z': 86., 'W': 76.,'t': 169.,'h': 118}
        startString = '[[['
        endString = ']]]'
        kinConstraints = []
        constraint = onShellConstraints
        
        if constraint == 'not yet assigned':
            for region in txNameObj.kinematikRegions:
                if region: self.topoExtensions.append(region.topoExtension)
            return None
        
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
        
        
class StandardLimits(list):
    
    def append(self, massArray_1, massArray_2, limit):
        
        massArray = [massArray_1, massArray_2]
        inLimit = False
        for point in self:
            if massArray ==  point[0]:
                if abs(limit-point[1]) > 0.0001:
                    Errors().limitDifference\
                    (massArray, point[1], limit)
                inLimit = True
                print 'check: %s' %point
                break
        if not inLimit:
            list.append(self, [massArray, limit])
        
        
        
    
  
                    
class OldStandardLimits(object):
    
    def __init__(self,txNameObj,limitName, dictName):
        
        self.txNameObj = txNameObj
        self.limitName = limitName
        self.topoExtensions = []
        self.vertexChecker = VertexChecker(txNameObj.constraint)
        self.limits = StandardLimits()
        self.dictName = dictName

        
    @property
    def txName(self):
        
        return self.txNameObj.name
        
    def __str__(self):
        
        string = ''
        for topoExtension in self.topoExtensions:
            limit = "%s['%s%s'] = %s\n" \
            %(self.dictName, self.txName, topoExtension, self.limits)
            string = string + limit
        return string
        
    def __nonzero__(self):
        
        return bool(self.limits)
 
        
    def addMassPlane(self, massPlaneObj):
        

        origLimitHisto = massPlaneObj.origLimits[self.limitName]
        if not origLimitHisto: 
                if not self.limitName == 'limit': return
                for region in self.txNameObj.kinematikRegions:
                    setattr(massPlaneObj, region.name, False)
                return    

        if self.vertexChecker.kinConstraints:
            preDefineRegions = self._getPreDefineRegions(massPlaneObj)
                
        for x,y,limit in origLimitHisto:
            massPoints = massPlaneObj.origPlot.getParticleMasses(x,y)
            massArray = [massPoints,massPoints]
            self.limits.append(massPoints, massPoints, limit)
            if not self.vertexChecker.kinConstraints: continue

            for region in self.txNameObj.kinematikRegions:
                if not region.topoExtension in preDefineRegions:
                    continue
                offShellVertices = \
                self.vertexChecker.getOffShellVertices(massPoints, massPoints)
                if region.checkMassArray(offShellVertices, massArray):
                    setattr(massPlaneObj, region.name, True)
                    if not region.topoExtension in self.topoExtensions:
                        self.topoExtensions.append(region.topoExtension)
    
    
    def _getPreDefineRegions(self, massPlaneObj):
        
        preDefineRegions = []
        for region in self.txNameObj.kinematikRegions:
            extension = region.topoExtension
            value = getattr(massPlaneObj, region.name)
            if value: preDefineRegions.append(extension)
            setattr(massPlaneObj, region.name, False)
        return preDefineRegions
        

        
class StandardExclusions(list):
    
    def __init__(self, txNameObj):
        
        self.txName = txNameObj.name
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
            
class StandardInfo(object):
    
    def __init__(self,metaInfo, path):
        
        self.fieldAssign = ': '
        self.txNameAssign = ' -> '
        self.metaInfo = self.mataInfoFormat(metaInfo)
        self.path = path
        self.txNameInfo = []
        for attr in inputObjects.KineamtikRegion.infoAttr:
            self.txNameInfo.append('')
        for attr in inputObjects.TxName.infoAttr:
            self.txNameInfo.append('')
        self.axes = ''
        self.publisheddata = True
        self.lastUpdate = self._getLastUpdate()
    

    def __str__(self):
        
        string = self.metaInfo
        string = string + 'publisheddata:%s\n' %self.publisheddata
        string = string + ''.join(self.txNameInfo)
        string = string + self.axes
        string = string + self.lastUpdate
        return string
        

    def _getLastUpdate(self):
        
        if os.path.isfile(os.getcwd() + self.path):
            lastUpdate = False
            for line in open(os.getcwd() + self.path).readlines():
                if 'lastUpdate' in line:
                    lastUpdate = line
                    break
            if lastUpdate:
                while True:
                    answer = raw_input('overwrite lastUpdate (y/n)?:')
                    if answer == 'y' or answer == 'n': break
                if answer == 'n': return lastUpdate
        today = date.today()
        today = '%s/%s/%s\n' %(today.year, today.month, today.day)
        return 'lastUpdate%s%s' %(self.fieldAssign, today)
        
    def mataInfoFormat(self,metaInfo):
        
        string =''
        for attr in metaInfo.infoAttr:
            if not hasattr(metaInfo, attr): continue
            string = '%s%s%s%s\n' \
            %(string, attr, self.fieldAssign, getattr(metaInfo, attr))
        #for attr in plottingList:
            
        return string
        
    def addTxName(self,txNameObj):
        
        #if txNameObj.onShell:
        #    self._addTxNameInfo(txNameObj, 'condition', False)
        #if txNameObj.offShell:
        #    self._addTxNameInfo(txNameObj, 'condition', True)
        regionName = None
        for region in txNameObj.kinematikRegions:
            if not getattr(txNameObj, region.name): continue
            for i, attr in \
            enumerate(inputObjects.KineamtikRegion.infoAttr):
                
                self._addTxNameInfo(txNameObj, region,region, attr, i)
                
            for plane in txNameObj.planes:
                if plane.limit and not plane.limit.dataUrl: 
                    self.publisheddata = False
                if not getattr(plane, region.name): continue
                if regionName != region.name:
                    regionName = region.name
                    self.axes = '%saxes%s%s%s%s' %(self.axes,\
                    self.fieldAssign, \
                    (txNameObj.name + region.topoExtension),\
                    self.txNameAssign, plane.origPlot)
                    continue
                self.axes = '%s;%s' %(self.axes, plane.origPlot)
            self.axes += '\n'
                
                    
            for j, attr in enumerate(inputObjects.TxName.infoAttr):
                self._addTxNameInfo(txNameObj, region, txNameObj, attr, j+i+1)
            
    def _addTxNameInfo(self, txNameObj, region, obj, attr, index):
        
        requiredAttr = ['condition', 'fuzzycondition', 'constraint']
        txName = txNameObj.name + region.topoExtension

        try:
            value = getattr(obj, attr)
        except AttributeError:
            if attr in requiredAttr: 
                Errors().required(txNameObj.name, region, attr)
            return
        selfValue = self.txNameInfo[index]
        selfValue = '%s%s%s%s%s%s\n'\
        %(selfValue, attr, self.fieldAssign, txName, self.txNameAssign, value)
        self.txNameInfo[index] = selfValue

        
            
        
        
      
    
class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def constraint(self, txName, constraint):
        
        m = self._starLine
        m = m + 'In StandardLimits: Error by while reading the constraint'
        m = m + 'for txName: %s\n' %txName
        m = m + "constraint have to be of form:\n"
        m = m + "[[['particle',...],...]][['particle',...],...]]"
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
        m = m + 'verices in constraint: %s\n' %constraintLen
        m = m + 'vertices in topology: %s' %massArrayLen
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def notAssigned(self, txName):
        
        m = self._starLine
        m = m + "can't split limits for txName: %s because " %txName
        m = m + "constraint is set to 'not yet assigned'\n"
        m = m + "please, set all kinematikRegions propertys of txName"
        m = m + "object to 'False' except of one;\n"
        m = m + "or assign constraints"
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def required(self, txName, kinObj, attr):
        
        m = self._starLine
        m = m + "there is an %s-region for %s " %(kinObj.name, txName) 
        m = m + "but no %s for this region\n" %attr
        m = m + "use txName.%s.%s " %(kinObj.topoExtension, attr)
        m = m + "to set %s" %attr
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def limitDifference(self, massArray, oldLimit, limit):
        
        m = '------------------------\n'
        m = m + "WARNING: massPoint: %s allrady in limits \n" %massArray
        m = m + "but differ in Upperlimit: %s v.s. %s" %(oldLimit, limit)
        m = m + '\n------------------------'
        print(m)
             