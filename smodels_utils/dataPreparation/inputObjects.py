#!/usr/bin/env python

"""
.. module:: inputObjects
   :synopsis: Holds objects used by convert.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   

import sys
import os
import ROOT
from copy import deepcopy
from smodels_utils.helper.txDecays import TxDecay
from smodels_utils.dataPreparation.origDataObjects import\
OrigLimit, OrigExclusion, OrigEfficiencyMap
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot
from smodels_utils.dataPreparation.databaseCreation import databaseCreator
from smodels_utils.dataPreparation.preparationHelper import Locker, ObjectList

import logging

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)


class MetaInfo(Locker):
    
    infoAttr = [ 'sqrts', 'lumi', 'id', 'prettyname', 'url', 'arxiv', 'signalRegion',
    'publication', 'contact', 'superseded_by','supersedes', 'comment',
    'private', 'implemented_by', 'observedN', 'expectedBG', 'bgError' ]
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
    
    infoAttr = ['condition', 'fuzzycondition', 'constraint','checked']
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
    internalAttr = ['_txDecay', 'origPlot', 'origLimits', 'origExclusions',
    'origEfficiencyMap', 'figure', 'figureUrl', 'dataUrl', 'histoDataUrl', 
    'exclusionDataUrl']
    
    def __init__(self,txDecay, motherMass = None,\
    lspMass = None, **interMasses ):
        self._txDecay = txDecay
        self.origPlot = OrigPlot()
        self.setBranch_1 \
        ( motherMass = motherMass, lspMass = lspMass, **interMasses)
        self.setBranch_2 \
        ( motherMass = motherMass, lspMass = lspMass, **interMasses)
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
        self.origEfficiencyMap = OrigEfficiencyMap('EfficiencyMap')
        self.figure =None
        self.figureUrl = None
        
    def setBranch_1(self, motherMass = None, lspMass = None, **interMasses):

        self.origPlot.setBranch_1 \
        ( motherMass = motherMass, lspMass = lspMass, **interMasses)
        
    def setBranch_2(self, motherMass = None, lspMass = None, **interMasses):

        self.origPlot.setBranch_2 \
        ( motherMass = motherMass, lspMass = lspMass, **interMasses)
        
    @property
    def efficiencyMap(self):
        return self.origEfficiencyMap
        
    @property
    def obsUpperLimit(self):
        return self.origLimits['limit']
        
    @property
    def expUpperLimit(self):
        return self.origLimits['expectedlimit']
        
    @property
    def obsExclusion(self):
        return self.origExclusions['exclusion']
        
    @property
    def obsExclusionP1(self):
        return self.origExclusions['exclusionP1']
        
    @property
    def obsExclusionM1(self):
        return self.origExclusions['exclusionM1']

    @property
    def expExclusion(self):
        return self.origExclusions['expectedExclusion']
        
    @property
    def expExclusionP1(self):
        return self.origExclusions['expectedExclusionP1']
        
    @property
    def expExclusionM1(self):
        return self.origExclusions['expectedExclusionM1'] 
    
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
  


class TxName(Locker):
    
    infoAttr = ['branchcondition']
    internalAttr = ['_name', 'name', '_txDecay', '_kinematikRegions','_planes',\
    '_branchcondition', 'onShell', 'offShell', 'constraint',\
    'condition', 'fuzzycondition','branchingRatio'] 
    
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
        self._kinematikRegions = self._getKinRegions()
        self._planes = []
        self.branchingRatio = None

    def _getKinRegions(self):
        
        kinRegions = ObjectList('name')
        onShellFunc = lambda offVertices: True if not offVertices else False
        onShellObj = KineamtikRegion('onShell','', onShellFunc)
        kinRegions.append(onShellObj)
        offShellFunc = lambda offVertices: True if offVertices else False
        offShellObj = KineamtikRegion('offShell','off', offShellFunc)
        kinRegions.append(offShellObj)
        return kinRegions
        
    
    def addMassPlane(self, motherMass = None, lspMass = None, **interMasses):

        if not motherMass:
            Errors().missingMass('motherMass',self.name)
        if not lspMass:
            Errors().missingMass('lspMass',self.name)
        if not self._txDecay.intermediateParticles:
            if self._planes: Errors().onlyOnePlane(self.name)
            if interMasses: Errors().interMediateParticle(self.name)
        else:
            if not interMasses:
                Errors().missingMass('interMass',self.name)
            
        massPlane = MassPlane(self._txDecay,\
        motherMass = motherMass, lspMass = lspMass, **interMasses)
        for kinRegion in self.kinematikRegions:
            if not kinRegion.name in MassPlane.internalAttr:
                MassPlane.internalAttr.append(kinRegion.name)
            setattr(massPlane, kinRegion.name, kinRegion.region)
        self._planes.append(massPlane)
        return massPlane
        
    @property
    def branchcondition(self):
        
        for plane in self.planes:
            branch_1 = plane.origPlot.branch_1
            branch_2 = plane.origPlot.branch_2
            if branch_1 != branch_2:
                if not self.branchingRatio: Errors().branchingRatio()
                if not isinstance(self.branchingRatio, float):
                    Errors().branchingRatioType(type(self.branchingRatio))
                if self.branchingRatio < 0. or self.branchingRatio > 1.:
                    Errors().branchingRatioValue(self.branchingRatio)
                return 'asymetric branches BR = %s' %self.branchingRatio
        return 'equal branches'
        
    @property
    def name(self):
        return self._name
        
    @property
    def planes(self):
        
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
    def on(self):
        
        return self.kinematikRegions['onShell']
        
    @property
    def offShell(self):
        
        return self._kinematikRegionGetter('offShell')
        
            
    @offShell.setter
    def offShell(self,value):
        
        self._kinematikRegionSetter('offShell', value)
        
    def _kinematikRegionGetter(self, name):

        for plane in self.planes:
            if getattr(plane, name) == True: return True
        return False
        
    def _kinematikRegionSetter(self, name, value):

        setattr(self.kinematikRegions[name], 'region', value)
        for plane in self.planes:
            setattr(plane, name, value)
    

class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def unknownTxName(self, txName):
        
        m = self._starLine
        m = m + '%s is no known txName !!\n'  %txName
        m = m + 'make sure there are no typos in the txName\n'
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
        m = m + '%s for mass plane of\n' %massName
        m = m + 'txName %s not deffiend' %txName
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def onlyOnePlane(self, txName):
        
        m = self._starLine
        m = m + 'can not add more then one massplane to tx: %s !!\n' %txName
        m = m + '%s has only one decay, ' %txName
        m = m + 'therefore onlyone massplane\n'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def interMediateParticle(self, txName):
        
        m = self._starLine
        m = m + 'txName: %s have no interMediateParticle!!\n' %txName
        m = m + 'please check your addMassPlane call at convert.py, ' %txName
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
        
    def branchingRatio(self):
        
        m = self._starLine
        m = m + 'Error there are asymetric branches\n'
        m = m + 'but brunchingRatio not set\n'
        m = m + 'please use .brunchingRatio ='
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def branchingRatioType(self, typ):
    
        m = self._starLine
        m = m + 'Error branchingRatio must be of type float\n'
        m = m + 'get: %s' %typ
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def branchingRatioValue(self, branchingRatio):
    
        m = self._starLine
        m = m + 'Error branchingRatio must be between 0 and 1\n'
        m = m + 'get: %s' %branchingRatio
        m = m + self._starLine
        print(m)
        sys.exit()
        

        
