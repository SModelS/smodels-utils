#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds objects used by convert.py to create info.txt, sms.root, sms.py and newSms.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   


import sys
import os
import ROOT
from smodels_utils.dataPreparation.standardObjects import\
StandardDataList, VertexChecker, StandardExclusions, StandardTWiki
from preparationHelper import ObjectList
import logging
from datetime import date

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

           
        
class DatabaseCreator(list):
        
    def __init__(self):
        
        self.exclusions = []
        self.metaInfo = None
        self.base = os.getcwd() + '/'
        self.twikitxtPath = './orig/twiki.txt'
        self.smsrootPath = './sms.root'
        self.infoFileDirectory = './'
        self.infoFileExtension = '.txt'
        self.metaInfoFileName = 'info'
        self.assignmentOperator = ': '
        self.txNameField = 'txname'
        list.__init__(self)
            
    def create(self):
        
        print '\n***starting creation of database entry for %s***\n'\
        %self.metaInfo.id
        
        self._extendInfoAttr(self.metaInfo, 'lastUpdate')
        self._setLastUpdate()
        self._delete()
        self._createInfoFile(self.metaInfoFileName, self.metaInfo)
   
        self.tWiki = StandardTWiki(self.metaInfo)
        
        publishedData = True
        for txName in self:
            
            print '\nreading: %s' %txName.name
            
            vertexChecker = VertexChecker(txName)
            upperLimits = StandardDataList()
            expectedUpperLimits = StandardDataList()
            efficiencyMap = StandardDataList(valueUnit ='')
            
            exclusions = ObjectList('name')
            for region in txName.kinematicRegions:
                exclusions.append\
                (StandardExclusions(txName.name + region.topoExtension))
            
            for plane in txName.planes:
                
                print '\nreading mass plane: %s\n' %plane.origPlot
                
                efficiencyMap = self.extendDataList\
                (efficiencyMap, plane, vertexChecker, txName)
                upperLimits = self.extendDataList\
                (upperLimits, plane, vertexChecker, txName, 'limit')
                expectedUpperLimits = self.extendDataList(expectedUpperLimits,\
                plane, vertexChecker, txName, 'expectedlimit')
                
                print 'extending upperLimits to %s entrys'\
                %len(upperLimits)
                print 'extending expectedUpperLimits to %s entrys'\
                %len(expectedUpperLimits)
                print 'extending efficiencyMap to %s entrys'\
                %len(efficiencyMap)
                
                if plane.obsUpperLimit or plane.efficiencyMap:
                    if not plane.obsUpperLimit.dataUrl and \
                    not plane.efficiencyMap.dataUrl: 
                        publishedData = False
                    
                for region in txName.kinematicRegions:      
                    if getattr(plane, region.name) == 'auto' \
                    or getattr(plane, region.name) == False:
                        setattr(plane, region.name, False)
                    else:
                        exclusions[getattr(region, self.txNameField)]\
                        .addMassPlane(plane)
                        print 'Found region: %s' %region.name
                        
                for excl in exclusions:
                    print 'extend exclusionLines for %s to %s entrys'\
                    %(excl.name, len(excl))

                self.tWiki.addMassPlane(txName.name,plane)

            for excl in exclusions: 
                if excl: self.exclusions.append(excl)
            self._extendInfoAttr(txName, 'publishedData')
            self._extendInfoAttr(txName, 'upperLimits')
            self._extendInfoAttr(txName, 'expectedUpperLimits')
            self._extendInfoAttr(txName, 'efficiencyMap')
            if upperLimits: txName.upperLimits = upperLimits
            if expectedUpperLimits: txName.expectedUpperLimits =\
            expectedUpperLimits
            if efficiencyMap: txName.efficiencyMap = efficiencyMap
            txName.publishedData = publishedData

            for region in txName.kinematicRegions:
                if getattr(txName, region.name):
                    if not hasattr(region, 'constraint'):
                        Errors().required(txName.name, region, 'constraint')
                    if not hasattr(region, 'condition'):
                        Errors().required(txName.name, region, 'condition')
                    if not hasattr(region, 'fuzzycondition'):
                        Errors().required(txName.name, region, 'fuzzycondition')
                    self._createInfoFile(getattr(region, self.txNameField), region, txName)
        
        self._createSmsRoot()
        self._createTwikiTxt()
   
        
    def extendDataList(self, dataList, plane, vertexChecker, txName, limitType = None):
        
        if limitType:
            origData = plane.origLimits[limitType] 
        else:
            origData = plane.origEfficiencyMap
        if not origData: return dataList
            
        kinRegions = txName.kinematicRegions
               
        for i,value in enumerate(origData):
            x = value[0] 
            y = value[1]
            value = value[2]
            massArray = plane.origPlot.getParticleMasses(x,y)
            #massArray = [massPoints,massPoints]
            dataList.append(massArray, value)
            
            for region in kinRegions:
                regionExist = getattr(plane, region.name)
                if not regionExist == 'auto':
                    if not isinstance(regionExist , bool):
                        Errors().kinRegionSetter(txName.name, region.name, \
                        regionPreSet)
                    if regionExist == True and i == 0:
                        self._setRegionAttr(txName, region, plane)
                    continue
                if not vertexChecker: 
                    Errors().notAssigned(txName.name)
                offShellVertices = \
                vertexChecker.getOffShellVertices(massArray)
                if region.checkoffShellVertices(offShellVertices):
                    setattr(plane, region.name, True)
                    self._setRegionAttr(txName, region, plane)
        return dataList
        
        
    def _setRegionAttr(self, txName, region, plane):
        
        self._extendInfoAttr(region, self.txNameField,0)
        setattr(region, self.txNameField, txName.name + region.topoExtension)
        self._extendInfoAttr(region, 'validated')
        region.validated = False
        self._extendInfoAttr(region, 'axes')
        if not hasattr(region, 'axes'):
            region.axes = str(plane.origPlot)
        else:
            region.axes = region.axes + ';' +\
            str(plane.origPlot)
    
    
    def _extendInfoAttr(self, obj, attr, position = None):
    
        if attr in obj.infoAttr: return
        if position == None:
            obj.infoAttr.append(attr)
            return
        obj.infoAttr.insert(position, attr)
        
        
    def _setLastUpdate(self):
        
        if os.path.isfile(self.base + self.infoFilePath(self.metaInfoFileName)):
            lastUpdate = False
            implemented_by = False
            oldInfo = open(self.base + self.infoFilePath(self.metaInfoFileName))
            lines = oldInfo.readlines()
            oldInfo.close()
            for line in lines:
                if 'lastUpdate' in line:
                    lastUpdate = line.split(self.assignmentOperator)[1]
                    lastUpdate = lastUpdate.replace('\n','')
                if 'implemented_by' in line:
                    implemented_by = line.split(self.assignmentOperator)[1]
                    implemented_by = implemented_by.replace('\n','')
            if lastUpdate:
                while True:
                    m = 'if one of the following data are changed, '
                    m = m + 'lastUpdate should be overwritten:\n'
                    m = m + 'number or name of txNames, arXiv, publication,'
                    m = m + ' upperLimits\n'
                    m = m + 'overwrite lastUpdate (y/n)?:'
                    answer = raw_input(m)
                    if answer == 'y' or answer == 'n': break
                if answer == 'n': 
                    self.metaInfo.lastUpdate = lastUpdate
                    if not implemented_by: self._setImplementedBy()
                    else: self.metaInfo.implemented_by = implemented_by
                    return
        today = date.today()
        today = '%s/%s/%s\n' %(today.year, today.month, today.day)
        self.metaInfo.lastUpdate = today
        self._setImplementedBy()
        
    def _setImplementedBy(self):
        
        while True:
            answer = raw_input('enter your name or initials: ')
            if answer: break
        self.metaInfo.implemented_by = answer
        
        
    def _delete(self):
        
        predefinedPaths = [
            self.base + self.smsrootPath,
            self.base + self.twikitxtPath,
            self.base + self.infoFilePath(self.metaInfoFileName)
            ]
        for path in predefinedPaths:
            if os.path.exists(path): os.remove(path)
        
        for entry in os.listdir(self.base + self.infoFileDirectory):
            if not entry[-len(self.infoFileExtension):] == self.infoFileExtension:
                continue
            compareLine = '%s%s%s\n' %(self.txNameField,\
            self.assignmentOperator, entry[:-len(self.infoFileExtension):])
            f = open(entry,'r')
            lines = f.readlines()
            f.close()
            if not compareLine in lines: continue
            os.remove(entry)

    def _createSmsRoot(self):
    
        smsRoot = ROOT.TFile(self.base + self.smsrootPath,'recreate')
        for exclusions in self.exclusions:
            directory = smsRoot.mkdir(exclusions.name, exclusions.name)
            directory.cd()
            for exclusion in exclusions: exclusion.Write()
        smsRoot.Close()
        
    def _createTwikiTxt(self):
        
        twikiTxt = open(self.base + self.twikitxtPath,'w')
        twikiTxt.write('%s' %self.tWiki)
        twikiTxt.close()
        
    def _createInfoFile(self, name, *objects):
        
        content = ''
        for obj in objects:
            for attr in obj.infoAttr:
                if not hasattr(obj, attr) and \
                not hasattr(obj.__class__, attr) : continue
                content = '%s%s%s%s\n' %(content, attr,\
                self.assignmentOperator, getattr(obj, attr))
        infoFile = open(self.base + self.infoFilePath(name), 'w')
        infoFile.write(content)
        infoFile.close()
        
    def infoFilePath(self, infoFileName):
        
        path = '%s%s%s' %(self.infoFileDirectory,\
        infoFileName, self.infoFileExtension)
        return path
        
databaseCreator = DatabaseCreator()   

class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'

    def required(self, txName, kinObj, attr):
        
        m = self._starLine
        m = m + "there is an %s-region for %s " %(kinObj.name, txName) 
        m = m + "but no %s for this region\n" %attr
        m = m + "use txName.%s.%s " %(kinObj.topoExtension, attr)
        m = m + "to set %s" %attr
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def kinRegionSetter(self, txName, name, value):
    
        m = self._starLine
        m = m + "in txName %s'\n" %txName
        m = m + "setter for propertsy %s must be of bool type or 'auto'\n"\
        %(name)
        m = m + 'got: %s' %value
        m = m + self._starLine
        print(m)
        sys.exit()
        
        
        
             
