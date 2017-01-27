#!/usr/bin/env python

"""
.. module:: inputObjects
   :synopsis: Holds objects used by convert.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   

import sys
from smodels_utils.helper.txDecays import TxDecay
from smodels_utils.dataPreparationNew.origDataObjects import\
OrigLimit, OrigExclusion, OrigEfficiencyMap
from smodels_utils.dataPreparationNew.origPlotObjects import OrigPlot
from smodels_utils.dataPreparationNew.databaseCreation import databaseCreator
from smodels_utils.dataPreparationNew.preparationHelper import Locker
from smodels.tools.physicsUnits import fb, pb
from smodels.theory.particleNames import elementsInStr
from smodels.particles import rEven, ptcDic

import logging
from smodels_utils.helper import prettyDescriptions

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)



class MetaInfoInput(Locker):
    """Holds all informations related to the publication 
    (publication means: physic summary note or conference note)
    """
    
    infoAttr = [ 'sqrts', 'lumi', 'id', 'prettyName', 'url', 'arxiv', 'signalRegion',
    'publication', 'contact', 'supersededBy','supersedes', 'comment',
    'private', 'implementedBy','lastUpdate']
    internalAttr = ['_sqrts', '_lumi']
    
    requiredAttr = ['sqrts', 'lumi', 'id', 'contact', 'lastUpdate']
    
    def __new__(cls, ID):
        
        """
        checks if databaseCreator already contains
        a MetaInfoInput object, writes this object to
        databaseCreation if not
        :param ID: name of the publication as string
        :returns: instance of MetaInfoInput
        :raise Error: if there is already a MetaInfoInput instance
        """
        
        if databaseCreator.metaInfo:
            logger.error('MetaInfo object for this publication already defined')
            sys.exit()
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
            logger.error("Sqrts value not correclty defined")
            sys.exit()
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
            logger.error("lumi value not correclty defined")
            sys.exit()
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
    
    
    infoAttr = ['conditionDescription', 'condition', 'constraint','checked',\
                'figureUrl', 'dataUrl', 'finalState' ]
    internalAttr = ['name', 'functions', 'topoExtension', 'region']
    
    requiredAttr = ['condition','constraint']
    
    def __init__(self,name,topoExtension, *conditionFunctions):
        """
        :param name: name as string
        :param topoExtension: string to be added to the txName in order
        to define the membership to this kinematic region
        :param *conditionFunctions: functions describing the conditions for the
        kinematic region. The parameter of this functions have to be a list of 
        tuples. The return value has to be a bool type
        """
        self.name = name
        self.functions = conditionFunctions
        self.topoExtension = topoExtension
        self.region = 'auto'

    def __str__(self):
        ret="KinematicRegion: %s, %s" % ( self.name, self.region )
        # ret+=" [%s]" % ( self.topoExtension )
        return ret

    def checkoffShellVertices(self,offShellVertices):
        """
        checks if offShellVertices meet the conditions
        given by self.functions (= conditionFunctions)
        :param offShellVertices: list of tuples describing
        the vertices with off-shell SM-particles
        :returns: True or False
        """
        for function in self.functions:
            if not function(offShellVertices): 
                return False
        return True
        
    def __nonzero__(self):
        return self.regionExist
             
class MassPlane(Locker):
    """
    Holds all information related to one mass plane
    a mass plane is defined by their axes
    """
    
    infoAttr = ['figureUrl','dataUrl','axes']
    internalAttr = ['_txDecay', 'origPlot', 'origLimits','_exclusionCurves',
            'origEfficiencyMap', 'figure', 'figureUrl', 'dataUrl', 'histoDataUrl', 
            'exclusionDataUrl', '_planeDimensions', 'upperLimits','expectedUpperLimits','efficiencyMap',
            'obsExclusion','obsExclusionP1','obsExclusionM1',
            'expExclusion','expExclusionP1','expExclusionM1']
    requiredAttr = []
    
    def __init__(self,txDecay, massArray):
        """
        sets the branches to the given axes and initialize the mass plane related
        values an objects
        :param txDecay: object of type TxDecay
        :param massArray: the full mass array containing equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [[x,y],[x,y]])        
        :param lspMass: mass of lightest SUSY-particle as sympy.core.symbol.Symbol,
        containing only the variables 'x', 'y' and numbers as float
        :param **interMasses: masses of the intermediated particles as 
                              sympy.core.symbol.Symbol, containing only the
                              variables 'x', 'y' and numbers as float
        """
        self._txDecay = txDecay
        self.origPlot = OrigPlot()
        for i,brMasses in enumerate(massArray):
            if not isinstance(brMasses,list):
                logger.error("Mass array must be in the format [[m1,m2,..],[m3,m4,..]]")
                sys.exit()
            self.setBranch(branchNumber=i,branchMasses=brMasses)
        
        #Count mass plane dimensions:
        xvars = []
        for br in self.origPlot.branches:
            for xvar in br._xvars:
                if not xvar in xvars:
                    xvars.append(xvar)
        self._planeDimensions = len(xvars)
            

        #Define all possible data types:        
        self.efficiencyMap = OrigEfficiencyMap('efficiencyMap')
        self.upperLimits = OrigLimit('limit')
        self.expectedUpperLimits = OrigLimit('expectedlimit')
        
        self.obsExclusion = OrigExclusion('exclusion')
        self.obsExclusionP1 =  OrigExclusion('exclusionP1')
        self.obsExclusionM1 =  OrigExclusion('exclusionM1')
        self.expExclusion =  OrigExclusion('expectedExclusion')
        self.expExclusionP1 =  OrigExclusion('expectedExclusionP1')
        self.expExclusionM1 =  OrigExclusion('expectedExclusionM1')
        self._exclusionCurves = [self.obsExclusion,self.obsExclusionP1,self.obsExclusionM1,
                                 self.expExclusion,self.expExclusionP1,self.expExclusionM1]
                
        self.figure = None
        self.figureUrl = None

    def __str__(self):
        return "%s" % ( self.origPlot )

        
    def setBranch(self,branchNumber, branchMasses):
        
        """
        Set masses for branch branchNumber.
        :param branchNumber: index of the branch        
        :param branchMasses: list containing the equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [x,y])        
        """

        self.origPlot.setBranch(branchNumber,branchMasses)
        
         
    
    @property
    def dataUrl(self):
        
        """ not yet in use, but is needed in order to define
        a setter 
        """
        
        pass
    
    @dataUrl.setter
    def dataUrl(self, url):
        
        """set url for efficiencyMap, opsUpperlimits, expUpperLimit 
        and all exclusionlines
        :param: html-link as string
        """
        
        self.efficiencyMap.dataUrl = url
        self.exclusionDataUrl = url
        self.histoDataUrl = url
    
    @property
    def histoDataUrl(self):
        
        """ not yet in use, but is needed in order to define
        a setter 
        """
        
        pass
    
    @histoDataUrl.setter
    def histoDataUrl(self, url):
        
        """set url for opsUpperlimits and expUpperLimit
        :param: html-link as string
        """
        
        for histo in self.origLimits:
            histo.dataUrl = url
            
    @property
    def exclusionDataUrl(self):
        
        """ not yet in use, but is needed in order to define
        a setter 
        """
        
        pass
    
    @exclusionDataUrl.setter
    def exclusionDataUrl(self, url):
        
        """set url for all exclusion lines
        :param: html-link as string
        """
        
        for exclusion in self.origExclusions:
            exclusion.dataUrl = url
  
class DataSetInput(Locker):
    """
    Holds all informations related to one dataset
    """
    
    
    infoAttr = ['dataType', 'dataId', 'observedN','expectedBG','bgError', 
                'upperLimit', 'expectedUpperLimit']
    internalAttr = ['_name','_txnameList']
    
    requiredAttr = ['dataType', 'dataId']
    
    def __new__(cls,name):
        
        """
        Checks if databaseCreator already contains
        a dataset object with the same id, writes this object to
        databaseCreation if not
        :param name: name of dataset (used as folder name)
        :returns: instance of DataSetInput
        :raise Error: if there is already a dataset instance with same name
        """
        
        for dataSet in databaseCreator:
            if dataSet._name == name: 
                logger.error("Dataset %s has already been defined" %name)
                sys.exit()
        datasetObject = object.__new__(cls)
        databaseCreator.append(datasetObject)
        return datasetObject 
    

    def __init__(self,name):
        
        """initialize the dataset
        :param name: name of dataset (used as folder name)
        """
        
        self._name = name
        self._txnameList = []

    def __str__(self):
        return self._name
    
    def setInfo(self,**attributes):
        """
        Set the attributes given as input. The only allowed attributes
        are the ones defined in infoAttr:
        
        :param attributes: Attributes and their values (dataId = xxx,...)
        """
        
        for key,val in attributes.items():
            setattr(self,key,val)
       
    def computeStatistics(self):
        """Compute expected and observed limits and store them """
        
        from math import floor, log10
        from smodels.tools import statistics
        
        if not hasattr(databaseCreator, 'metaInfo'):
            logger.error('MetaInfo must be defined before computing statistics')
            sys.exit()
        elif not hasattr(databaseCreator.metaInfo, 'lumi'):
            logger.error('Luminosity must be defined in MetaInfo')
            sys.exit()
        elif not hasattr(self, 'observedN') or not hasattr(self, 'expectedBG') or not hasattr(self, 'bgError'):
            logger.error('observedN, expectedBG and bgError must be defined before computing statistics')
            sys.exit()

        
        lumi = databaseCreator.metaInfo.lumi
        ul = statistics.upperLimit(self.observedN, self.expectedBG, self.bgError, lumi, .05, 200000).asNumber(fb)
        ulExpected = statistics.upperLimit(self.expectedBG, self.expectedBG, self.bgError, lumi, .05, 200000).asNumber(fb)
        self.upperLimit = ul
        self.expectedUpperLimit = ulExpected
        
    def addTxName(self,txname):
        """
        Adds txname to dataset. Checks if txname already exists and
        raise a error if it does.
        
        :param txname: txname (string)
        
        :return: TxNameInput object
        """
        
        for txobj in self._txnameList:
            if txobj._name == txname:
                logger.error("Txname %s already exists in dataset" %txname)
                sys.exit()
                
        txobj = TxNameInput(txname)
        self._txnameList.append(txobj)
        
        return txobj
        

class TxNameInput(Locker):
    
    """
    Holds all informations related to one txName
    """
    
    
    infoAttr = ['condition', 'conditionDescription', 'upperLimits',
                'efficiencyMap','expectedUpperLimits','txName','figureUrl','dataUrl','validated','axes',
                'publishedData','prettyTxName','checked','finalState']
    internalAttr = ['_name', 'name', '_txDecay', '_kinematicRegions','_planes',\
    '_branchcondition', 'onShell', 'offShell', 'constraint',\
    'condition', 'conditionDescription', '_newMassInput', '_ignoreKinematics',\
    'upperLimits','efficiencyMap','expectedUpperLimits']
    
    requiredAttr = ['constraint','condition','txName']
    
    
    def __init__(self,txName, ignoreKinematics=False):
        
        """initialize the txName related values an objects
        checks if the given txName string is valid
        :param txName: name as string
        :param ignoreKinematics: If True the data points will not be checked against
                                 the kinematic restrictiins defined by the contraint and
                                 all the data points will be included.
        :raise unknownTxNameError: if txName string is not known by module 
        helper.txDecays
        :raise doubleDecayError: if helper.txDecays holds 2 txNames with 
        the same decay chain
        """
        
        
        self._name = txName
        self.txName = txName
        self.prettyTxName = prettyDescriptions.prettyTxname(txName)
        self._txDecay = TxDecay(self._name)    
        if not self._txDecay:
            logger.error("Unknown txname %s" %self._name)
            sys.exit()
        self._ignoreKinematics = ignoreKinematics
        self._planes = []

    def __str__(self):

        return self._name
        
    
    def addMassPlane(self, massArray):
        
        """
        add a MassPlane object with given axes to self.planes.
        Add new attributes to the MassPlane. For every KinematicRegion-object
        in self.kinematicRegions an attribute named after the name of the 
        KinematicRegion-object is added and set to the value of 
        KinematicRegion.region
        :param txDecay: object of type TxDecay
        :param massArray: the full mass array containing equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [[x,y],[x,y]])        
        :raise missingMassError: if one mass entry is missing
        :raise onlyOnePlaneError: if a second mass plane is given and the related mass space 
        have only 2 dimensions
        :raise interMediateParticleError: if a interMasses are given and the related mass space 
        have only 2 dimensions
        :return: MassPlane-object
        """
        # print("[inputObjects] add mass plane %s %s" % ( motherMass,interMasses) )
        
        #Standard input
        if not isinstance(massArray,list):
            logger.error('Input must be a mass array')
            sys.exit()
            

        #Checks for new input
        for ibr,br in enumerate(eval(self.constraint)):
            nmasses = len(br)+1
            if len(massArray[ibr]) != nmasses:
                logger.error("Mass array definition is not consistent with the txname constraint")
                sys.exit()
        #Create mass plane for new input
        massPlane = MassPlane(self._txDecay,massArray)
        self._planes.append(massPlane)
        return massPlane                    
                  

            

    def getData(self,dataType):
        """
        Reads the source file and stores the data.
        :param dataType: Type of data (efficiencyMap or upperLimit)
        """
        

        for plane in self._planes:
            self.timeStamp('Reading mass plane: %s, %s' % (self, plane.origPlot))
            
            if dataType == 'efficiencyMap':
                if not plane.efficiencyMap:
                    logger.error('Efficiency map source not defined for plane %s' %plane.origPlot)
                    sys.exit()
                self.addData(plane,dataType='efficiencyMap')
                
            elif dataType == 'upperLimits':
                if not plane.upperLimits:
                    logger.error('Upper limit map source not defined for plane %s' %plane.origPlot)
                    sys.exit()
                self.addData(plane,dataType='upperLimits')
                self.publishedData = hasattr(plane,'upperLimits.dataUrl')

            if plane.expectedUpperLimits:
                self.addData(plane,dataType='expectedUpperLimits')
                
    def getInfo(self):
        """
        Collects all the info from its mass planes and stores it
        in self. Also defines additional information.
        """
        
        for infoAttr in self.infoAttr:
            infoList = [""]*len(self._planes)            
            planeHasInfo = False
            for i,plane in enumerate(self._planes):
                if hasattr(plane,infoAttr):
                    planeHasInfo = True
                    infoList[i] = str(getattr(plane, infoAttr))
            if planeHasInfo:
                infoStr = ";".join(infoList)
                setattr(self,infoAttr,infoStr)
        
        self.publishedData = hasattr(self,'efficiencyMap.dataUrl')
        self.validated = 'Not done yet'


    def addData(self, plane, dataType):

        """
        extend the given data list by the values related to this type of list
        examples for data lists are ; upperLimits, efficiencyMaps, ....
        The values held by the given mass plane are extended to the data list.
        If self does not contain the dataType, set this attribute.

        :param plane: MassPlane-object
        :param dataType: type of the given data (efficiencyMap, obsUpperLimit, expUpperLimit,..)
        
        """
        
        #Get dimension of the plot:
        nvars = plane._planeDimensions
        if nvars < 1 or nvars > 3:
            logger.error('Can not deal with %i variables' %nvars)
            sys.exit()
        
        #Check if plane is has a dataType object holder:
        if not hasattr(plane,dataType):
            logger.error("Plane %s does not contain data holder for dataType %s" %(plane,dataType))
            sys.exit()
            
        origData = getattr(plane,dataType)
        
        dataList = []
        for value in origData:
            if len(value) != nvars+1:
                logger.error("Number of free parameters in data and in axes do not match")
                sys.exit()
            xvals = value[:nvars]
            value = value[-1]
            massArray = plane.origPlot.getParticleMasses(*xvals)
            #Check if mass array is consistent with the kinematical constraints given by the 
            #txname constraint. If not, skip this mass.
            if not self._ignoreKinematics:
                if not self.checkKinematicConstrain(massArray):
                    continue
            dataList.append([massArray, value])
        
        #Add data to txname. If dataType already exists, extend it
        if hasattr(self,dataType):
            txData = getattr(self,dataType)
            txData += dataList
        else:
            setattr(self,dataType,dataList)
            
    def _setKinematicConstraint(self):
        """
        Define the kinematical constraint for the txname, based
        on its constraint.
        """
        
        #Build mass dictionary for all particles
        massDict = {'Z': 86., 'W+': 76.,'W-' : 76.,'t': 169.,
                    't-': 169.,'h': 118., 'higgs': 118., 'ta+' : 1.7, 'ta-' : 1.7}
        #(if they do not appear in masssDict, replace by zero)
        for key in rEven.values():
            if not key in massDict:
                massDict[key] = 0.
        #Set masses for inclusive labels (use lowest mass)
        for key,ptclist in ptcDic.items():
            minMass = [massDict[ptc] for ptc in ptclist if ptc in massDict]
            if not minMass:
                minMass = 0.
            else:
                minMass = min(minMass)
            massDict[key] = minMass
        
        #Replace particles appearing in the vertices by their mass        
        self._kinematicConstraints = []
        for el in elementsInStr(self.constraint):
            self._kinematicConstraints.append(eval(el,massDict)) #Replace particles in element by their masses
            
    def checkKinematicConstrain(self,massArray):
        """
        Check if massArray satisfies the kinematical constraints.
        
        If the txname constraint contains several elements, require that massArray
        satisfied the constaint for at least one of the elements.
        
        :param massArray: array with masses to be checked. It must be consistend with the
                          topology of the txname constraint.
        """
        
        if not hasattr(self, '_kinematicConstraints'):
            self._setKinematicConstraint()
        
        for elMass in self._kinematicConstraints:
            goodMasses = True
            for ib,br in enumerate(elMass):
                for iv,vertex in enumerate(br):
                    if sum(vertex) > massArray[ib][iv]-massArray[ib][iv+1]:
                        goodMasses = False
                        break
            if goodMasses:
                return True
        
        return False                 
            