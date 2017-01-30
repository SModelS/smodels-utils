#!/usr/bin/env python

"""
.. module:: inputObjects
   :synopsis: Holds objects used by convert.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   

import sys
import copy
from smodels_utils.helper.txDecays import TxDecay
from smodels_utils.dataPreparation.origDataObjects import Orig
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot
from smodels_utils.dataPreparation.databaseCreation import databaseCreator
from smodels_utils.dataPreparation.preparationHelper import Locker
from smodels.tools.physicsUnits import fb, pb, TeV, GeV
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
    
    infoAttr = ['id','sqrts', 'lumi', 'prettyName', 'url', 'arxiv',
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

             
class MassPlane(Locker):
    """
    Holds all information related to one mass plane
    a mass plane is defined by their axes
    """
    
    infoAttr = ['figureUrl','dataUrl','axes']
    internalAttr = ['_txDecay', 'origPlot', 'origLimits','_exclusionCurves',
            'origEfficiencyMap', 'figure', 'figureUrl', 'dataUrl', 'histoDataUrl', 
            'exclusionDataUrl', 'dimensions', 'upperLimits','expectedUpperLimits','efficiencyMap',
            'obsExclusion','obsExclusionP1','obsExclusionM1',
            'expExclusion','expExclusionP1','expExclusionM1','axesLabels']
    requiredAttr = []
    allowedDataLabels = ['efficiencyMap','upperLimits','expectedUpperLimits',
                        'obsExclusion','obsExclusionP1','obsExclusionM1',
                        'expExclusion','expExclusionP1','expExclusionM1']
    
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
        dimensions = len(xvars)
        self.dimensions = dimensions
        self._exclusionCurves = []
        #Define the default labels for the input axes variables
        #(relevant for computing the masses from x,y,z...)
        self.axesLabels = ['x','y','z'][:dimensions]
         
        self.axes = massArray       
        self.figure = None
        self.figureUrl = None

    def __str__(self):
        return "%s" % ( self.axes )
        
    def setBranch(self,branchNumber, branchMasses):
        
        """
        Set masses for branch branchNumber.
        :param branchNumber: index of the branch        
        :param branchMasses: list containing the equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [x,y])        
        """

        self.origPlot.setBranch(branchNumber,branchMasses)
        
    def setSources(self,dataLabels,dataFiles,dataFormats,objectNames=None,indices=None,units=None):
        """
        Defines the data sources for the plane.
        
        :param dataLabels: Single string with the data label or list of strings with the dataLabels
                          possible data laels are defined in allowedDataLabels
                          (e.g. efficiencyMap, upperLimits, expectedUpperLimits,...)
        :param datafiles: Single string with the file path or list of strings with the file paths
                          to the data files.
        :param dataFormats: Single string with the file format or list of strings with the file formats
                          for the data files.
        
        :param objectName: name of object stored in root-file or cMacro or list of object names                         
        :param indices: index of object in listOfPrimitives of ROOT.TCanvas or lis of indices
        :param units: Unit string for objects (e.g. 'fb',None,'pb',...)
        """

        #Make sure input is consistent:
        if isinstance(dataFiles,list):
            if indices is None:
                indices = [None]*len(dataFiles)
            if objectNames is None:
                objectNames = [None]*len(dataFiles)
            if units is None:
                units = [None]*len(dataFiles)                
            if not isinstance(dataLabels,list) or len(dataLabels) != len(dataFiles):
                logger.error("dataLabels and dataFiles are not consistent:\n %s \n %s" %(dataLabels,dataFiles))
                sys.exit()
            if not isinstance(dataFormats,list) or len(dataFormats) != len(dataFiles):
                logger.error("dataFormats and dataFiles are not consistent:\n %s \n %s" %(dataFormats,dataFiles))
                sys.exit()                
            if not isinstance(indices,list) or len(indices) != len(dataFiles):
                logger.error("indices and dataFiles are not consistent:\n %s \n %s" %(indices,dataFiles))
                sys.exit()
            if not isinstance(objectNames,list) or len(objectNames) != len(dataFiles):
                logger.error("objectNames and dataFiles are not consistent:\n %s \n %s" %(objectNames,dataFiles))
                sys.exit()
                                
        elif not isinstance(dataFiles,str):
            logger.error('dataFiles must be a list or a single string')
        else:
            if not isinstance(dataLabels,str):
                logger.error("dataLabels and dataFiles are not consistent")
                sys.exit()
            if not isinstance(dataFormats,str):
                logger.error("dataFormats and dataFiles are not consistent")
                sys.exit()      
            dataFiles = [dataFiles]
            dataLabels = [dataLabels]
            indices = [indices]
            objectNames = [objectNames]
            
            
        for i,dataFile in enumerate(dataFiles):
            dataLabel = dataLabels[i]
            dataFormat = dataFormats[i]
            index = indices[i]
            objectName = objectNames[i]
            unit = units[i]
            if not dataLabel in self.allowedDataLabels:
                logger.warning("Data label %s is not allowed and will be ignored" %dataLabel)
                continue
            
            if 'exclusion' in dataLabel.lower():
                dimensions = 2
            else:
                dimensions = self.dimensions
            #Get the origData object for the corresponding dataLabel
            origObject = Orig.getObjectFor(dataLabel,dimensions)
            #Set source of object
            origObject.setSource(dataFile, dataFormat, objectName, index)
            origObject.unit = unit
            #Store it as a mass plane attribute:            
            setattr(self,dataLabel,origObject)
            if 'exclusion' in dataLabel.lower():
                self._exclusionCurves.append(origObject)
    

class DataSetInput(Locker):
    """
    Holds all informations related to one dataset
    """
    
    
    infoAttr = ['dataId','dataType','observedN','expectedBG','bgError', 
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
        if isinstance(lumi,str):
            lumi = eval(lumi)
        ul = statistics.upperLimit(self.observedN, self.expectedBG, self.bgError, lumi, .05, 200000).asNumber(fb)
        ulExpected = statistics.upperLimit(self.expectedBG, self.expectedBG, self.bgError, lumi, .05, 200000).asNumber(fb)
        self.upperLimit = str(ul)+'*fb'
        self.expectedUpperLimit = str(ulExpected)+'*fb'
        
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
    
    
    infoAttr = ['txName','constraint','condition','conditionDescription','finalState',
                'susyProcess','checked','figureUrl','dataUrl','publishedData',
                'validated','axes','upperLimits',
                'efficiencyMap','expectedUpperLimits']
    internalAttr = ['_name', 'name', '_txDecay','_planes',
    '_branchcondition', 'onShell', 'offShell', 'constraint',
    'condition', 'conditionDescription','massConstraint',
    'upperLimits','efficiencyMap','expectedUpperLimits','massConstraints','_dataLabels']
    
    requiredAttr = ['constraint','condition','txName']
    
    
    def __init__(self,txName):
        
        """initialize the txName related values an objects
        checks if the given txName string is valid
        :param txName: name as string
        :raise unknownTxNameError: if txName string is not known by module 
        helper.txDecays
        :raise doubleDecayError: if helper.txDecays holds 2 txNames with 
        the same decay chain
        """
        
        
        self._name = txName
        self.txName = txName
        self.susyProcess = prettyDescriptions.prettyTxname(txName,latex=False)
        self._txDecay = TxDecay(self._name)    
        if not self._txDecay:
            logger.error("Unknown txname %s" %self._name)
            sys.exit()
        self._planes = []
        self._dataLabels = []

    def __str__(self):

        return self._name
        
    
    def addMassPlane(self, plane):
        
        """
        add a MassPlane object with given axes to self.planes.
        Add new attributes to the MassPlane.
        :param txDecay: object of type TxDecay
        :param plane: A MassPlane object or the full mass array containing equations which relate the
        physical masses and the plane coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [[x,y],[x,y]]).
        :raise missingMassError: if one mass entry is missing
        :raise onlyOnePlaneError: if a second mass plane is given and the related mass space 
        have only 2 dimensions
        :raise interMediateParticleError: if a interMasses are given and the related mass space 
        have only 2 dimensions
        :return: MassPlane-object
        """
        # print("[inputObjects] add mass plane %s %s" % ( motherMass,interMasses) )
        
        if isinstance(plane,MassPlane):
            newplane = copy.deepcopy(plane)
            self._planes.append(newplane)
            return newplane            
        elif isinstance(plane,list):
            massArray = plane
        else:
            logger.error("Input must be a MassPlane object or a mass array")
            sys.exit()
        
        #Standard input
        if not isinstance(massArray,list):
            logger.error('Input must be a mass array')
            sys.exit()
            

        #Get element constraint structure/topology:
        element = eval(elementsInStr(self.constraint,removeQuotes=False)[0])
        #Checks for new input
        if len(massArray) != len(element):
            logger.error("Mass array definition %s is not consistent with the txname constraint %s"
                         %(str(massArray),str(element)))
            sys.exit()
        for ibr,br in enumerate(element):
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
        Loop over the defined the planes and collects the data.
        Reads the source file and stores the data.
        :param dataType: Type of data (efficiencyMap or upperLimit)
        """
        

        for plane in self._planes:
            logger.info('Reading mass plane: %s, %s' % (self, plane.origPlot))
            
            if dataType == 'upperLimit':
                if not hasattr(plane,'upperLimits'):
                    logger.error('%s source not defined for plane %s' %(dataType,plane.origPlot))
                    sys.exit()
                else:
                    self.addData(plane,'upperLimits')
                    self._dataLabels.append('upperLimits')
            elif dataType == 'efficiencyMap':
                if not hasattr(plane,'efficiencyMap'):
                    logger.error('%s source not defined for plane %s' %(dataType,plane.origPlot))
                    sys.exit()
                else:
                    self.addData(plane,'efficiencyMap')
                    self._dataLabels.append('efficiencyMap')
            else:
                logger.error('Unknown data type %s' %dataType)
                sys.exit()         
                                
            #Add expected upper limits, if it exists:
            if hasattr(plane,'expectedUpperLimits'):
                self.addData(plane,'expectedUpperLimits')
                self._dataLabels.append('expectedUpperLimits')
                
    def getInfo(self):
        """
        Collects all the info attributes from its mass planes and stores it
        in self. Also defines additional information.
        """
        
        for infoAttr in self.infoAttr:
            infoList = [""]*len(self._planes)            
            planeHasInfo = False
            for i,plane in enumerate(self._planes):
                if not infoAttr in plane.infoAttr:
                    continue
                if hasattr(plane,infoAttr):
                    planeHasInfo = True
                    infoList[i] = str(getattr(plane, infoAttr))
            if planeHasInfo:
                infoStr = ";".join(infoList)
                setattr(self,infoAttr,infoStr)
        
        self.publishedData = hasattr(self,'dataUrl')
        self.validated = 'Not done yet'

    def addData(self, plane, dataLabel):

        """
        extend the given data list by the values related to this type of list
        examples for data lists are ; upperLimits, efficiencyMaps, ....
        The values held by the given mass plane are extended to the data list.
        If self does not contain the dataLabel, set this attribute.

        :param plane: MassPlane-object
        :param dataLabel: label of the given data (efficiencyMap, upperLimits,..)
        
        """
        
        #Get dimension of the plot:
        nvars = plane.dimensions
        if nvars < 1 or nvars > 3:
            logger.error('Can not deal with %i variables' %nvars)
            sys.exit()
        
        #Check if plane is has a dataLabel object holder:
        if not hasattr(plane,dataLabel):
            logger.error("Plane %s does not contain data holder for dataLabel %s" %(plane,dataLabel))
            sys.exit()
            
        origData = getattr(plane,dataLabel)
        
        dataList = []        
        for value in origData:
            if len(value) != nvars+1:
                logger.error("Number of free parameters in data and in axes do not match")
                sys.exit()
            xvals = value[:nvars]
            value = value[-1]
            xdict = dict([[plane.axesLabels[i],xv] for i,xv in enumerate(xvals)])
            massArray = plane.origPlot.getParticleMasses(**xdict)
            #Check if mass array is consistent with the mass constraints given by the 
            #txname constraint. If not, skip this mass.
            if not self.checkMassConstraints(massArray):
                continue
            #Add units
            if hasattr(origData, 'unit') and origData.unit:
                value = value*eval(origData.unit)
            if hasattr(origData, 'massUnit') and origData.massUnit:
                massArray = [[m*eval(origData.massUnit) for m in br ] for br in massArray]
            dataList.append([massArray, value])
        
        #Add data to txname. If dataLabel already exists, extend it
        if hasattr(self,dataLabel) and isinstance(getattr(self,dataLabel),list):
            txData = getattr(self,dataLabel)
            txData += dataList
        else:
            setattr(self,dataLabel,dataList)
            
    def _setMassConstraints(self):
        """
        Define the mass constraints for the txname, based
        on its constraint. The constraints on the mass differences of the BSM
        particles are given as a nested array (according to the constraint format)
        containing string inequalities to be satisfied by the BSM masses.
        (e.g. for the constraint [[[t,t]],[[t,t]] we have the
        mass constraint [['m > 169.+169.'],['m > 169.+169.']].
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
        self.massConstraints = []
        for el in elementsInStr(self.constraint,removeQuotes=False):
            el = eval(el)
            #Replace particles in element by their masses
            massConstraint = [[[massDict[ptc] for ptc in v] for v in br] for br in el]      
            self.massConstraints.append(massConstraint) 
            
        #Now convert the constraints to inequality expressions:
        for el in self.massConstraints:
            for branch in el:
                for iv,vertex in enumerate(branch):
                    eqStr = "m >= "
                    massValue = sum(vertex)
                    eqStr += str(massValue)
                    branch[iv] = eqStr
                        
    def checkMassConstraints(self,massArray):
        """
        Check if massArray satisfies the mass constraints defined in massConstraints
        
        If the txname constraint contains several elements, require that massArray
        satisfied the constaint for at least one of the elements.
        
        :param massArray: array with masses to be checked. It must be consistend with the
                          topology of the txname constraint.
        """
        
        if hasattr(self,'massConstraint'):
            if not self.massConstraint:
                return True
            self.massConstraints = [self.massConstraint]
        if not hasattr(self, 'massConstraints'):
            self._setMassConstraints()
        
        #If massConstraints was pre-defined as None or empty list, return always True
        if not self.massConstraints:  
            return True
        
        for elMass in self.massConstraints:            
            goodMasses = True
            for ib,br in enumerate(elMass):
                for iv,vertex in enumerate(br):
                    massDiff = massArray[ib][iv]-massArray[ib][iv+1]
                    if massDiff < 0.:
                        logger.error("Parent mass is smaller than daughter mass for %s" %str(self))
                        sys.exit()
                    #Evaluate the inequality replacing m by the mass difference:
                    check = eval(vertex,{'m' : massDiff}) 
                    if check is False:
                        goodMasses = False
                        break
                    elif not check is True:
                        logger.error("Something went wrong evaluating the mass constraint %s" %vertex)
                        sys.exit()
            if goodMasses:
                return True
        
        return False                 
            
