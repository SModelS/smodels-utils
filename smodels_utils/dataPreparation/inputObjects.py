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


class MetaInfoInput(Locker):
    
    """
    Holds all informations related to the publication 
    (publication means: physic summary note or conference note)
    """
    
    infoAttr = [ 'sqrts', 'lumi', 'id', 'prettyname', 'url', 'arxiv', 'signalRegion',
    'publication', 'contact', 'superseded_by','supersedes', 'comment',
    'private', 'implemented_by', 'observedN', 'expectedBG', 'bgError' ]
    internalAttr = ['_sqrts', '_lumi']
    
    def __new__(cls, ID):
        
        """
        checks if databaseCreator already contains
        a MetaInfoInput object, writes this object to
        databaseCreation if not
        :param ID: name of the publication as string
        :returns: instance of MetaInfoInput
        :raise Error: if there is alrady a MetaInfoInput instance
        """
        
        if databaseCreator.metaInfo:
            Errors().metaInfo()
        metaInfo = object.__new__(cls)
        databaseCreator.metaInfo = metaInfo
        return metaInfo
    
    def __init__(self, ID):
        
        """
        :param ID: name of the publication as string
        """
        
        self.id = ID
       
    @property
    def sqrts(self):
        
        """
        :returns: center-of-mass energy in TeV as String
        """
        
        return self._sqrts
        
    @sqrts.setter
    def sqrts(self, value):
        
        """
        sets center-of-mass energy
        :param value: center-of-mass energy as float, integer or string
        """
        
        
        value = self.unitValue(value,'*','TeV')
        if not value:
            Errors().sqrts(value)
        self._sqrts = value
        
    @property
    def lumi(self):
        
        """
        :returns: integrated luminosity in fb-1 as string
        """
        
        return self._lumi
        
    @lumi.setter
    def lumi(self, value):
        
        """
        sets integrated luminosity in fb-1 as string
        :param value: integrated luminosity as float, integer or string
        """
        
        value = self.unitValue(value,'/','fb')
        if not value:
            Errors().limi(value)
        self._lumi = value
    
    def unitValue(self, value, operation,unit):
        
        """
        checks if input conditions are met by value
        formats value 
        :param value: float, integer or a number as string
        :param operation: '/' or '*'
        :param unit: unit of value as string
        """

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
            
class KinematicRegion(Locker):
    
    """
    Holds all informations related to one kinematic region
    in this context a kinematic region is defined by their
    off-shell vertices 
    """
    
    
    infoAttr = ['condition', 'fuzzycondition', 'constraint','checked']
    internalAttr = ['name', 'functions', 'topoExtension',\
    'region']
    
    def __init__(self,name,topoExtension, *conditionFunctions):
        
        """
        :param name: name as string
        :param topoExtension: string to be added to the txName in order
        to define the membership to this kinematic region
        :param *conditionFunctions: functions describing the conditions for the
        kinematic region. The parameter of this functions have to be a list of 
        tuples. The return value have to be a bool type
        """
        
        self.name = name
        self.functions = conditionFunctions
        self.topoExtension = topoExtension
        self.region = 'auto'

    def checkoffShellVertices(self,offShellVertices):
        
        """
        checks if the massArray offShellVertices met the conditions
        given by self.functions (= conditionFunctions)
        :returns: True or False
        """

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
  


class TxNameInput(Locker):
    
    
    infoAttr = []
    internalAttr = ['_name', 'name', '_txDecay', '_kinematicRegions','_planes',\
    '_branchcondition', 'onShell', 'offShell', 'constraint',\
    'condition', 'fuzzycondition'] 
    
    def __new__(cls,txName):
        
        for txObjects in databaseCreator:
            if txObjects.name == txName: 
                Errors().doublelTxName(txName)
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
        self._kinematicRegions = self._getKinRegions()
        self._planes = []


    def _getKinRegions(self):
        
        kinRegions = ObjectList('name')
        onShellFunc = lambda offVertices: True if not offVertices else False
        onShellObj = KinematicRegion('onShell','', onShellFunc)
        kinRegions.append(onShellObj)
        offShellFunc = lambda offVertices: True if offVertices else False
        offShellObj = KinematicRegion('offShell','off', offShellFunc)
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
        for kinRegion in self.kinematicRegions:
            if not kinRegion.name in MassPlane.internalAttr:
                MassPlane.internalAttr.append(kinRegion.name)
            setattr(massPlane, kinRegion.name, kinRegion.region)
        self._planes.append(massPlane)
        return massPlane
        
    @property
    def name(self):
        return self._name
        
    @property
    def planes(self):
        
        return self._planes

            
    @property
    def kinematicRegions(self):
        
        return self._kinematicRegions
        
    @property
    def onShell(self):
        
        return self._kinematicRegionGetter('onShell')
        
    @onShell.setter
    def onShell(self,value):

        self._kinematicRegionSetter('onShell', value)
        
    @property
    def off(self):
        
        return self.kinematicRegions['offShell']
        
    @property
    def on(self):
        
        return self.kinematicRegions['onShell']
        
    @property
    def offShell(self):
        
        return self._kinematicRegionGetter('offShell')
        
            
    @offShell.setter
    def offShell(self,value):
        
        self._kinematicRegionSetter('offShell', value)
        
    def _kinematicRegionGetter(self, name):

        for plane in self.planes:
            if getattr(plane, name) == True: return True
        return False
        
    def _kinematicRegionSetter(self, name, value):

        setattr(self.kinematicRegions[name], 'region', value)
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
    
    def doublelTxName(self, txName):
        
        m = self._starLine
        m = m + '%s already defined !!\n' %txName
        m = m + 'every txName can only appear once in one publication'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def missingMass(self, massName, txName):
        
        m = self._starLine
        m = m + '%s for mass plane of\n' %massName
        m = m + 'txName %s not defined' %txName
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
        m = m + 'metaInfo object for this publication already defined\n'
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
        

        
