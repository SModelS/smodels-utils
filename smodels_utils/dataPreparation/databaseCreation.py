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
StandardLimits, VertexChecker, StandardExclusions, StandardTWiki
from helper import ObjectList
import logging
from datetime import date

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

           
        
class DatabaseCreator(list):
        
    def __init__(self):
        
        self.exclusions = []
        self.limitsDictName = 'Dict'
        self.expectedlimitsDictName = 'ExpectedDict'
        self.metaInfo = None
        self.twikitxtPath = '/orig/twiki.txt'
        self.smsrootPath = '/sms.root'
        self.infoFilePath = '/'
        list.__init__(self)
            
    def create(self):
        
        print '\n***strating creation of database entry for %s***\n'\
        %self.metaInfo.id
        
        self._extendInfoAttr(self.metaInfo, 'lastUpdate')
        self.metaInfo.lastUpdate = self._getLastUpdate()
        self._createInfoFile('info', self.metaInfo)
   
        self.tWiki = StandardTWiki(self.metaInfo)
        
        publishedData = True
        for txName in self:
            
            print '\nreading: %s' %txName.name
            
            vertexChecker = VertexChecker(txName.on.constraint)
            upperLimits = StandardLimits()
            expectedUpperLimits = StandardLimits()
            
            exclusions = ObjectList('name')
            for region in txName.kinematikRegions:
                exclusions.append\
                (StandardExclusions(txName.name + region.topoExtension))
            
            for plane in txName.planes:
                
                print '\nreading mass plane: %s\n' %plane.origPlot
                
                upperLimits = self.extendlimit\
                (upperLimits, 'limit', plane, vertexChecker, txName)
                expectedUpperLimits = self.extendlimit(expectedUpperLimits,\
                'expectedlimit', plane, vertexChecker, txName)
                
                print 'extending upperLimits to %s entrys'\
                %len(upperLimits)
                print 'extending expectedUpperLimits to %s entrys'\
                %len(expectedUpperLimits)
                
                if plane.limit and not plane.limit.dataUrl: 
                    publishedData = False
                    
                for region in txName.kinematikRegions:      
                    if getattr(plane, region.name) == 'auto':
                        setattr(plane, region.name, False)
                    else:
                        exclusions[region.txname].addMassPlane(plane)
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
            if upperLimits: txName.upperLimits = upperLimits
            if expectedUpperLimits: txName.expectedUpperLimits =\
            expectedUpperLimits
            txName.publishedData = publishedData
            
            for region in txName.kinematikRegions:
                if getattr(txName, region.name):
                    self._createInfoFile(region.txname, region, txName)
        
        self._createSmsRoot()
        self._createTwikiTxt()

        
        
    def extendlimit(self, upperLimits, limitType, plane, vertexChecker, txName):
        
        origLimitHisto = plane.origLimits[limitType] 
        if not origLimitHisto: return upperLimits
            
        kinRegions = txName.kinematikRegions
               
        for x,y,limit in origLimitHisto:
            massPoints = plane.origPlot.getParticleMasses(x,y)
            massArray = [massPoints,massPoints]
            upperLimits.append(massArray, limit)
            
            for region in kinRegions:
                regionExist = getattr(plane, region.name)
                if not regionExist == 'auto':
                    if not isinstance(regionExist , bool):
                        Errors().kinRegionSetter(txName.name, region.name, \
                        regionPreSet)
                    continue
                if not vertexChecker: 
                    Errors().notAssigned(txName.name)
                offShellVertices = \
                vertexChecker.getOffShellVertices(massArray)
                if region.checkMassArray(offShellVertices, massArray):
                    setattr(plane, region.name, True)
                    self._extendInfoAttr(region, 'txname',0)
                    region.txname = txName.name + region.topoExtension
                    self._extendInfoAttr(region, 'validated')
                    region.validated = False
                    self._extendInfoAttr(region, 'axes')
                    if not hasattr(region, 'axes'):
                        region.axes = str(plane.origPlot)
                    else:
                        region.axes = region.axes + ';' +\
                        str(plane.origPlot)
        return upperLimits
    
    
    def _extendInfoAttr(self, obj, attr, position = None):
    
        if attr in obj.infoAttr: return
        if position == None:
            obj.infoAttr.append(attr)
            return
        obj.infoAttr.insert(position, attr)
        
        
    def _getLastUpdate(self):
        
        if os.path.isfile(os.getcwd() + self.infoFilePath + 'info.txt'):
            lastUpdate = False
            oldInfo = open(os.getcwd() + self.infoFilePath + 'info.txt')
            lines = oldInfo.readlines()
            oldInfo.close()
            for line in lines:
                if 'lastUpdate' in line:
                    lastUpdate = line.split(': ')[1]
                    break
            if lastUpdate:
                while True:
                    answer = raw_input('overwrite lastUpdate (y/n)?:')
                    if answer == 'y' or answer == 'n': break
                if answer == 'n': return lastUpdate
        today = date.today()
        today = '%s/%s/%s\n' %(today.year, today.month, today.day)
        return today


    def _createSmsRoot(self):
    
        smsRoot = ROOT.TFile(os.getcwd() + self.smsrootPath,'recreate')
        for exclusions in self.exclusions:
            directory = smsRoot.mkdir(exclusions.name, exclusions.name)
            directory.cd()
            for exclusion in exclusions: exclusion.Write()
        smsRoot.Close()
        
    def _createTwikiTxt(self):
        
        twikiTxt = open(os.getcwd() + self.twikitxtPath,'w')
        twikiTxt.write('%s' %self.tWiki)
        twikiTxt.close()
        
    def _createInfoFile(self, name, *objects):
        
        content = ''
        for obj in objects:
            for attr in obj.infoAttr:
                if not hasattr(obj, attr): continue
                content = '%s%s: %s\n' %(content, attr,\
                getattr(obj, attr))
        infoFile = open(os.getcwd() + self.infoFilePath + name + '.txt', 'w')
        infoFile.write(content)
        infoFile.close()
        
databaseCreator = DatabaseCreator()        
        
        
        
             