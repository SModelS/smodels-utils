#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds objects used by convert.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   

import sys
import os
import ROOT
from copy import deepcopy
from smodels_utils.helper.txDecays import TxDecay
from smodels_utils.dataPreparation.origDataObjects import\
OrigLimit, OrigExclusion
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot
from smodels_utils.dataPreparation.databaseCreation import databaseCreator
from smodels_utils.dataPreparation.helper import Locker, ObjectList

import logging

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)


class MetaInfo(Locker):
    
    infoAttr = [ 'sqrts', 'lumi', 'id', 'prettyname', 'url', 'arxiv',\
    'publication', 'superseded_by','supersedes', 'comment', 'private',\
    'implemented_by']
    internalAttr = ['_sqrts', '_lumi']
    
    def __new__(cls, ID):
        
        if databaseCreator.metaInfo:
            Errors().metaInfo()
        metaInfo = object.__new__(cls)
        databaseCreator.metaInfo = metaInfo
        return metaInfo
    
    def __init__(self, ID):
        
        self.id = ID
       
    @property
    def sqrts(self):
        
        return self._sqrts
        
    @sqrts.setter
    def sqrts(self, value):
        
        value = self.unitValue(value,'*','TeV')
        if not value:
            Errors().sqrts(value)
        self._sqrts = value
        
    @property
    def lumi(self):
        
        return self._lumi
        
    @lumi.setter
    def lumi(self, value):
        
        value = self.unitValue(value,'/','fb')
        if not value:
            Errors().limi(value)
        self._lumi = value
    
    def unitValue(self, value, operation,unit):

        if isinstance(value, str):
            check = value.split(operation)
            if len(check) == 2:
                if not check[1].strip() == unit: return False
            try:
                check[0] = float(check[0])
            except:
                return False
            if len(check) == 1: return '%s%s%s' %(value,operation,unit)
            if len(check) == 2: return value
            return False
        try: 
            check = float(value)
            return '%s%s%s' %(value,operation,unit)
        except:
            return False
            
class KineamtikRegion(Locker):
    
    infoAttr = ['condition', 'fuzzycondition', 'constraint']
    internalAttr = ['name', 'functions', 'topoExtension',\
    'region']
    
    def __init__(self,name,topoExtension, *conditionFunctions):
        
        self.name = name
        self.functions = conditionFunctions
        self.topoExtension = topoExtension
        self.region = 'auto'

    def checkMassArray(self,offShellVertices, massArray):
        

        for function in self.functions:
            if not function(offShellVertices): 
                return False
        return True
        
    def __nonzero__(self):
        
        return self.regionExist
             
class MassPlane(Locker):
    
    infoAttr = []
    internalAttr = ['_txDecay', 'origPlot', 'origLimits', 'origExclusions',\
    'figure', 'figureUrl', 'dataUrl', 'histoDataUrl', 'exclusionDataUrl']
    
    def __init__(self,txDecay):
        self._txDecay = txDecay
        self.origPlot = None
        self.origLimits = ObjectList('name',[
            OrigLimit('limit'),
            OrigLimit('expectedlimit')
            ])
        self.origExclusions = ObjectList('name',[
            OrigExclusion('exclusion'),
            OrigExclusion('exclusionP1'),
            OrigExclusion('exclusionM1'),
            OrigExclusion('expectedExclusion'),
            OrigExclusion('expectedExclusionP1'),
            OrigExclusion('expectedExclusionM1'),
            ])
        self.figure =None
        self.figureUrl = None

    @property
    def limit(self):
        return self.origLimits['limit']
        
    @property
    def expectedlimit(self):
        return self.origLimits['expectedlimit']
        
    @property
    def exclusion(self):
        return self.origExclusions['exclusion']
        
    @property
    def exclusionP1(self):
        return self.origExclusions['exclusionP1']
        
    @property
    def exclusionM1(self):
        return self.origExclusions['exclusionM1']

    @property
    def expectedExclusion(self):
        return self.origExclusions['expectedExclusion']
        
    @property
    def expectedExclusionP1(self):
        return self.origExclusions['expectedExclusionP1']
        
    @property
    def expectedExclusionM1(self):
        return self.origExclusions['expectedExclusionM1']
        
    @classmethod
    def additional(cls, txDecay, motherMass = None, interMass = None, lspMass = None):
        
        if not motherMass:
            Errors().missingMass('motherMass',txDecay.name)
        if not interMass:
            Errors().missingMass('interMass',txDecay.name)
        if not lspMass:
            Errors().missingMass('lspMass',txDecay.name)
        if not txDecay.intermediateParticles:
            Errors().noInterParticle(txDecay.name)
            
        massPlane = cls(txDecay)
        massPlane.origPlot = OrigPlot.fromConvert( \
        motherMass = motherMass, interMass = interMass, lspMass = lspMass)
        return massPlane
        
    def setMassPlane(self, motherMass = None, lspMass = None):
        
        if not motherMass:
            Errors().missingMass('motherMass',self._txDecay.name)
        if not lspMass:
            Errors().missingMass('lspMass',self._txDecay.name)
            
        self.origPlot = OrigPlot.fromConvert(motherMass = motherMass, lspMass = lspMass)  
    
    @property
    def dataUrl(self):
        pass
    
    @dataUrl.setter
    def dataUrl(self, url):
        
        self.exclusionDataUrl = url
        self.histoDataUrl = url
    
    @property
    def histoDataUrl(self):
        pass
    
    @histoDataUrl.setter
    def histoDataUrl(self, url):
        
        for histo in self.origLimits:
            histo.dataUrl = url
            
    @property
    def exclusionDataUrl(self):
        pass
    
    @exclusionDataUrl.setter
    def exclusionDataUrl(self, url):
        
        for exclusion in self.origExclusions:
            exclusion.dataUrl = url
  


class TxName(MassPlane):
    
    infoAttr = ['branchcondition', 'checked'] + MassPlane.infoAttr
    internalAttr = ['_name', 'name', '_txDecay', '_kinematikRegions','_planes',\
    '_branchcondition', 'onShell', 'offShell', 'constraint',\
    'condition', 'fuzzycondition'] + MassPlane.internalAttr
    
    def __new__(cls,txName):
        
        for txObjects in databaseCreator:
            if txObjects.name == txName: 
                Errors().doppelTxName(txName)
        txObject = object.__new__(cls)
        databaseCreator.append(txObject)
        return txObject
    
    def __init__(self,txName):
        
        self._name = txName
        self._txDecay = TxDecay(self._name)
        if not self._txDecay:
            Errors().unknownTxName(self._name)
        if self._txDecay.doubledDecays:
            Errors().doubledDecay(self._name, self._txDecay.doubledDecays)
            
        if not self._txDecay.intermediateParticles:
            MassPlane.__init__(self,self._txDecay)
            
        self._kinematikRegions = self._getKinRegions()
        self._planes = []
        self._branchcondition = 'equal branches'

    def _getKinRegions(self):
        
        kinRegions = ObjectList('name')
        onShellFunc = lambda offVertices: True if not offVertices else False
        onShellObj = KineamtikRegion('onShell','', onShellFunc)
        kinRegions.append(onShellObj)
        offShellFunc = lambda offVertices: True if offVertices else False
        offShellObj = KineamtikRegion('offShell','off', offShellFunc)
        kinRegions.append(offShellObj)
        return kinRegions
        
    
    def addMassPlane(self, motherMass = None, interMass = None, \
    lspMass = None):

        massPlane = MassPlane.additional(self._txDecay,\
        motherMass = motherMass, interMass = interMass, lspMass = lspMass)
        for kinRegion in self.kinematikRegions:
            if not kinRegion.name in MassPlane.internalAttr:
                MassPlane.internalAttr.append(kinRegion.name)
            setattr(massPlane, kinRegion.name, kinRegion.region)
        self._planes.append(massPlane)
        return massPlane
    
    @property
    def branchcondition(self):
        
        return self._branchcondition
        
    @branchcondition.setter
    def branchcondition(self, value):
        
        if not value == 'equal branches':
            Errors().branchcondition(self.name, value)
        self._branchcondition = value
            
    @property
    def constraint(self):
        
        return self.kinematikRegions['onShell'].constraint
        
    @constraint.setter
    def constraint(self, value):

        self.kinematikRegions['onShell'].constraint  = value
        
    @property
    def condition(self):
        
        return self.kinematikRegions['onShell'].condition
        
    @condition.setter
    def condition(self, value):
        
        self.kinematikRegions['onShell'].condition  = value
        
    @property
    def fuzzycondition(self):
        
        return self.kinematikRegions['onShell'].fuzzycondition
        
    @fuzzycondition.setter
    def fuzzycondition(self, value):
        
        self.kinematikRegions['onShell'].fuzzycondition  = value
    
    @property
    def name(self):
        return self._name
        
    @property
    def planes(self):
        
        if not self._txDecay.intermediateParticles:
            return [self]
        return self._planes

            
    @property
    def kinematikRegions(self):
        
        return self._kinematikRegions
        
    @property
    def onShell(self):
        
        return self._kinematikRegionGetter('onShell')
        
    @onShell.setter
    def onShell(self,value):

        self._kinematikRegionSetter('onShell', value)
        
    @property
    def off(self):
        
        return self.kinematikRegions['offShell']
        
    @property
    def offShell(self):
        
        return self._kinematikRegionGetter('offShell')
        
            
    @offShell.setter
    def offShell(self,value):
        
        self._kinematikRegionSetter('offShell', value)
        
    def _kinematikRegionGetter(self, name):

        if not self._txDecay.intermediateParticles:
            return self.kinematikRegions[name].region
        for plane in self.planes:
            if plane == self: continue
            if getattr(plane, name) == True: return True
        return False
        
    def _kinematikRegionSetter(self, name, value):

        self.kinematikRegions[name].region = value
        for plane in self.planes:
            if plane == self: continue
            setattr(plane, name, value)
    

class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def unknownTxName(self, txName):
        
        m = self._starLine
        m = m + '%s is no known txName !!\n'  %txName
        m = m + 'make shure there are no typos in the txName\n'
        m = m + 'or add the txName to the decay Dict at helper/txDecays.py'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def doubledDecay(self, txName, doubledTxNames):
    
        m = self._starLine
        m = m + 'decay for %s ambiguous !!\n' %txName
        m = m + 'there are the following txNames with equal decays '
        m = m + 'in decay Dict at helper/txDecays.py:\n'
        m = m + '%s\n' %doubledTxNames
        m = m + 'for every decay only one TxName alowed, please check'
        m = m + self._starLine
        print(m)
        sys.exit()
    
    def doppelTxName(self, txName):
        
        m = self._starLine
        m = m + '%s allraedy deffiend !!\n' %txName
        m = m + 'every txName can only appear one time in one publication'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def missingMass(self, massName, txName):
        
        m = self._starLine
        m = m + '%s for mass plane off\n' %massName
        m = m + 'txName %s not deffiend' %txName
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def noInterParticle(self, txName):
        
        m = self._starLine
        m = m + 'can not add massplane to tx: %s !!\n' %txName
        m = m + '%s has only one decay, ' %txName
        m = m + 'therefore onlyone massplane\n'
        m = m + 'use methode setMassplane to define this one massplane'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def shellFlag(self, txName, value):
        
        m = self._starLine
        m = m + 'in txName: %s \n' %txName
        m = m + 'values for propertys offshell and onshell\n'
        m = m + 'must be of bool type, got %s' %value
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def metaInfo(self):
        
        m = self._starLine
        m = m + 'metaInfo object for this publication allrady defiend\n'
        m = m + 'There can only be one metaInfo Object for every publication\n'
        m = m + 'please check your convert file'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def sqrts(self, value):
        
        m = self._starLine#
        m = m + "sqrts must be value, interpretable as float'\n"
        m = m + 'or a string of form: value*TeV, got: %s' %value
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def lumi(self, value):
        
        m = self._starLine#
        m = m + "lumi must be value, interpretable as float'\n"
        m = m + 'or a string of form: value/fb, got: %s' %value
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def branchcondition(self, txName, value):
        
        m = self._starLine#
        m = m + "Current implimentation only works for 'equal Branches'\n"
        m = m + 'got: %s for txName: %s' %(value, txName)
        m = m + self._starLine
        print(m)
        sys.exit()
        

        
