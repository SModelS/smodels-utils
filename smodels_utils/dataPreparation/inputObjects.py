#!/usr/bin/env python

"""
.. module:: inputObjects
   :synopsis: Holds objects used by convert.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys
import os
import string
from smodels_utils.helper.txDecays import TxDecay
from smodels_utils.dataPreparation.databaseCreation import databaseCreator,round_list
from smodels_utils.dataPreparation.particles import rEven
from smodels_utils.dataPreparation.dataHandlerObjects import hbar
from smodels_utils.dataPreparation.covarianceHandler import \
         UPROOTCovarianceHandler, CSVCovarianceHandler, PYROOTCovarianceHandler,\
         FakeCovarianceHandler
from smodels_utils.dataPreparation import covarianceHandler
from smodels.tools.physicsUnits import fb, pb, TeV, GeV
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels.theory.element import Element
from smodels.theory.auxiliaryFunctions import elementsInStr
from smodels.installation import version
import copy
import math
import scipy

import logging
from smodels_utils.helper import prettyDescriptions

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.WARNING)
quenchNegativeMasses = False ## set to true, if you wish to
# quench the warning about negative masses

errormsgs = {}

def getSignalRegionsEMBaked ( filename, exclude : list = [] ):
    """ from an emBaked file, retrieve the names of the signal regions
    :param filename: name of embaked file.
                     if list of filenames, get SRs for all and check if equal
    :param exclude: list of SR regions to exclude
    """
    if type ( filename) in [ list, tuple ]:
        rets = {}
        lens = {}
        l0,l,lf = -1,-1,""
        ret=None
        for f in filename:
            rets[f] = getSignalRegionsEMBaked ( f, exclude )
            ret = rets[f]
            l = len(rets[f])
            lens[f] = l
            if l0 > -1 and l != l0:
                print ( "[inputObjects] number of signal regions in embaked files differ: {lf}:{l0}!={f}:{l}" )
            l0,lf = l,f
        return ret


    # ret = set()
    ret = []
    try:
        f=open( filename,"r")
        values=list(eval(f.read()).values())
        f.close()
    except Exception as e:
        logger.error ( f"cannot read {filename}: {e}" )
        sys.exit(-1)
    for v in values:
        for k in v:
            if not k.startswith("__") and not k in exclude:
                if not k in ret:
                    ret.append(k)
                #ret.add(k)
    return ret

def getStatsEMBaked ( ):
    """ retrieve the stats from an emBaked stats file """
    statsfile = "orig/statsEM.py"
    if not os.path.exists ( statsfile ):
        print ( "ERROR: cannot find %s" % statsfile )
        return None
    f=open( statsfile )
    g=eval(f.read())
    f.close()
    from smodels_utils.dataPreparation import databaseCreation
    databaseCreation.DatabaseCreator.tempInputFiles.append ( statsfile )
    return g

class Locker(object):

    """Super-class to 'lock' a class.
    Every child-class of Locker needs 2 class-attributes:
    infoAttr: list of strings
    interAttr: list of strings
    Only attributes with names defined in one of those lists can
    be added to the child
    """


    def __setattr__(self, name, attr):

        """
        set a attripute if defiened in self.allowedAttr
        :param name: name of the attribute
        :param attr: value of the attribute
        :raise attrError: If name is not in self.allowedAttr
        """

        if name in self.allowedAttr:
            object.__setattr__(self, name, attr)
            return
        logger.error("Attribute %s is not allowed for %s" %(name,type(self)))

    @property
    def allowedAttr(self):

        """
        :return: list containing all entries of
        infoAttr and internalAttr
        """

        return self.infoAttr + self.internalAttr + self.requiredAttr


class MetaInfoInput(Locker):
    """Holds all informations related to the publication
    (publication means: physic summary note or conference note)
    """

    infoAttr = [ 'id','sqrts', 'lumi', 'prettyName', 'url', 'arxiv',
    'publication', 'publicationDOI', 'contact', 'supersededBy','supersedes', 'comment',
    'private', 'implementedBy','lastUpdate', 'datasetOrder', 'covariance',
    'combinableWith', 'jsonFiles', 'source', 'Leff_inner', 'Leff_outer', 'type',
    'includeCRs', 'onnxFiles' ]
    internalAttr = ['_sqrts', '_lumi']

    requiredAttr = ['sqrts', 'lumi', 'id', 'lastUpdate']

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

    def createCovarianceMatrix ( self, filename, histoname = None, addOrder=True,
                          max_datasets=None, aggregate = None, datasets = None,
                          histoIsCorrelations=False, aggprefix="ar" ):
        """ create the covariance matrix from file <filename>, histo <histoname>,
        allowing only a maximum of <max_datasets> datasets. If
        aggregate is not None, aggregate the signal regions, given as
        a list of lists of signal region names, e.g.
        [ [ "sr1", "sr2" ], [ "sr3", "sr4" ] ] or as a list of lists of
        signal numbers, e.g.  [ [ 1, 2 ], [ 3, 4 ] ]
        :param addOrder: False, True, or "overwrite". should a datasetOrder field
                         be defined purely from the signal regions (overwrite),
                         only if no datasetOrder is explicitly given (True),
                         or the standard "SRx" names be used (False)
        :param aggregate: aggregate signal regions, given by indices, e.g.
         [[0,1,2],[3,4]] or signal region names, e.g.[["sr0","sr1"],["sr2"]].
        :param datasets: list of datasets, so we can cross-check the covariance
         matrix with the errors given per signal region
        :param histoIsCorrelations: if true, then assume that we histoname
        refers to a correlation matrix, not a covariance matrix, so multiply with
        the SR erros, accordingly
        :param aggprefix: prefix for aggregate signal region names, eg ar0, ar1, etc
        """
        if type(filename)==dict:
            handler = FakeCovarianceHandler ( filename, max_datasets, aggregate,
                    aggprefix )
        elif filename.endswith ( ".csv" ):
            handler = CSVCovarianceHandler ( filename,
                    max_datasets, aggregate, aggprefix )
        else:
            try:
                import uproot
                handler = UPROOTCovarianceHandler ( filename, histoname, max_datasets,
                    aggregate, aggprefix )
            except ModuleNotFoundError as e:
                logger.error ( "could not import uproot, trying pyroot now" )
                handler = PYROOTCovarianceHandler ( filename, histoname, max_datasets,
                    aggregate, aggprefix )

        if not hasattr ( self, "datasetOrder" ) or addOrder == "overwrite":
            if addOrder:
                self.datasetOrder = ", ".join ( [ '"%s"' % x for x in  handler.datasetOrder ] )
            else:
                self.datasetOrder = ", ".join ( [ '"SR%d"' % (x+1) for x in range ( handler.n ) ] )
        self.covariance = handler.covariance
        if True: ## pretty print
            self.covariance = "["
            for rowctr,row in enumerate(handler.covariance):
                self.covariance += "["
                for colctr,x in enumerate(row):
                    if histoIsCorrelations:
                        if datasets == None:
                            logger.error ( "you supplied correlations, now i need datasets" )
                            sys.exit()
                        oldx=x
                        x = x * datasets[colctr].bgError * datasets[rowctr].bgError
                        #if colctr < 2 and rowctr < 2:
                        #    logger.error ( f">>> ctrs={colctr}, {rowctr}, bgerr={datasets[colctr].bgError}, x={oldx}, {x}" )
                    if rowctr==colctr:
                        logger.debug ( "variance(%d,%d)=%f" % ( rowctr+1, colctr+1, x ) )
                        if datasets != None:
                            dsSigma = (datasets[rowctr].bgError)
                            dsVar = (datasets[rowctr].bgError)**2
                            if dsVar > 1.2 * x and not histoIsCorrelations and covarianceHandler.overrideWithConservativeErrors:
                                logger.error ( "variance determined from table (%.2g) is more than 1.2*variance in covariance matrix (%.2g) at (%d). replace variance in covariance matrix with more conservative estimate." % ( dsVar, x, rowctr+1 ) )
                                x = dsVar
                            logger.debug ( "dataset(%d)^2=%f^2=%f" % ( rowctr+1, dsSigma, dsVar ) )
                            off = max ( dsVar,x ) / min ( dsVar,x)
                            logger.debug ( "it is a factor of %.1f off" % off )
                            err = 2.*(dsVar-x ) / (dsVar+x)
                            logger.debug ( "relative error on variance %.1f percent" % (100.*err) )
                    self.covariance += "%.4g, " % x
                self.covariance = self.covariance[:-2] + "], "
            self.covariance = self.covariance[:-2]+"]"

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


class DataSetInput(Locker):
    """
    Holds all informations related to one dataset
    """


    infoAttr = ['dataId','dataType','observedN','expectedBG','bgError', 'comment',
                'upperLimit', 'expectedUpperLimit', 'aggregated', 'jsonfile', 'lumi',
                'originalSRs', 'thirdMoment' ]
    internalAttr = ['_name','_txnameList']

    requiredAttr = ['dataType', 'dataId']

    ntoys = 200000 ## number of toys in computing limits

    def __init__(self,name):

        """initialize the dataset
        :param name: name of dataset (used as folder name)
        """
        if type(name)!=str or len(name)<1: ## or name[0] not in string.ascii_letters:
            logger.error ( "Illegal dataset name: ``%s''. Make sure it starts with a letter." % name )
            sys.exit()

        self._name = name
        self._txnameList = []

        databaseCreator.addDataset(self)

    def __eq__(self,other):
        """
        Check if datasets have the same name
        """

        if type(self) != type(other):
            return False

        return self._name == other._name


    def __str__(self):
        return self._name

    def setInfo(self,**attributes):
        """
        Set the attributes given as input. The only allowed attributes
        are the ones defined in infoAttr:

        :param attributes: Attributes and their values (dataId = xxx,...)
        """

        for key,val in attributes.items():
            if type(val) == type(None):
                continue
            if key in [ "upperLimit", "expectedUpperLimit" ] and type(val) == type(fb):
                val = str(val.asNumber(fb))+"*fb"
            setattr(self,key,val)

    def computeStatistics(self):
        """Compute expected and observed limits and store them """

        if not hasattr(databaseCreator, 'metaInfo'):
            logger.error('MetaInfo must be defined before computing statistics')
            sys.exit()
        elif not hasattr(databaseCreator.metaInfo, 'lumi'):
            logger.error('Luminosity must be defined in MetaInfo')
            sys.exit()
        elif not hasattr(self, 'observedN') or not hasattr(self, 'expectedBG') or not hasattr(self, 'bgError'):
            if hasattr(self,"jsonfile"):
                logger.error ( "pyhf result. for now I wont compute anything. FIXME probably should though." )
                # self.upperLimit = str(ul)+'*fb'
                # self.expectedUpperLimit = str(ulExpected)+'*fb'
                return

            logger.error('observedN, expectedBG and bgError must be defined before computing statistics')
            sys.exit()


        #First check if a luminosity has been defined for the dataset
        if hasattr(self,"lumi"):
            lumi = self.lumi
        else:
            lumi = getattr(databaseCreator.metaInfo,'lumi')
        if isinstance(lumi,str):
            lumi = eval(lumi,{'fb':fb,'pb': pb})
        alpha = .05
        try:
            from smodels.tools.simplifiedLikelihoods import Data, UpperLimitComputer
            comp = UpperLimitComputer ( self.ntoys, 1. - alpha )
            try:
                # new API
                m = Data ( self.observedN, self.expectedBG, self.bgError**2, None, 1.,
                       lumi = lumi )
                ul = comp.getUpperLimitOnSigmaTimesEff ( m, marginalize=True ).asNumber ( fb )
                ulExpected = comp.getUpperLimitOnSigmaTimesEff ( m, marginalize=True, expected=True ).asNumber ( fb )
                if type(ul) == type(None):
                    ul = comp.getUpperLimitOnSigmaTimesEff ( m, marginalize=False ).asNumber ( fb )
                if type(ulExpected) == type(None):
                    ulExpected = comp.getUpperLimitOnSigmaTimesEff ( m, marginalize=True, expected=False ).asNumber ( fb )
            except:
                # old API
                m = Data ( self.observedN, self.expectedBG, self.bgError**2, None, 1. )
                ul = comp.ulSigmaTimesEff ( m, marginalize=True ) # / lumi.asNumber ( 1. / fb )
                ulExpected = comp.ulSigmaTimesEff ( m, marginalize=True, expected=True ) # / lumi.asNumber ( 1. / fb )
                if type(ul) == type(None):
                    ul = comp.ulSigmaTimesEff ( m, marginalize=False )
                if type(ulExpected) == type(None):
                    ulExpected = comp.ulSigmaTimesEff ( m, marginalize=False, expected=True )
                # finally, divide by lumi
                if type(ul) != type(None):
                    ul = ul / lumi.asNumber ( 1. / fb )
                if type(ulExpected) != type(None):
                    ulExpected = ulExpected / lumi.asNumber ( 1. / fb )
        except ModuleNotFoundError as e:
            ## maybe smodels < 1.1.2?
            logger.error ( "cannot import simplifiedLikelihoods module: %s. Maybe upgrade to smodels >= v1.1.3?" % e )
            from smodels.tools import statistics
            ul = statistics.upperLimit(self.observedN, self.expectedBG,
                   self.bgError, lumi, alpha, self.ntoys ).asNumber(fb)
            ulExpected = statistics.upperLimit(self.expectedBG, self.expectedBG,
                   self.bgError, lumi, alpha, self.ntoys ).asNumber(fb)

        #Round numbers:
        ul = round_list(ul, 3)
        ulExpected = round_list(ulExpected, 3)
        self.upperLimit = str(ul)+'*fb'
        self.expectedUpperLimit = str(ulExpected)+'*fb'

    def addTxName(self,txname):
        """
        Adds txname to dataset. Checks if txname already exists and
        raise an error if it does.

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

    def checkConsistency(self):
        """
        Some consistency checks which the dataset must satisfy
        """

        #Check if it contains txnames:
        if not self._txnameList:
            logger.error("Dataset %s does not contain txnames" %self)
            return False

        #Check txname data type
        for tx in self._txnameList:
            txDataTypes = set()
            for plane in tx._planes:
                if hasattr(plane,'upperLimits'):
                    txDataTypes.add('upperLimits')
                elif hasattr(plane,'efficiencyMap'):
                    txDataTypes.add('efficiencyMap')
            txDataTypes = list(txDataTypes)
            if not txDataTypes:
                logger.error("Txname %s has no upperLimits or efficiencyMap data?" %\
                              tx.txName)
                return False
            if len(txDataTypes) > 1:
                logger.error("Txname %s has mixed data types" %tx.txName)
                return False
            elif not self.dataType in txDataTypes[0]:
                logger.error("Txname %s data type (%s) does not match dataset type (%s)"
                             %(tx.txName,txDataTypes[0],self.dataType))
                return False


        if self.dataType != 'efficiencyMap':
            return True

        #Check constraints (only for EM results):
        datasetElements = []
        for tx in self._txnameList:
            for el in elementsInStr(tx.constraint):
                newEl = None
                fs = tx.finalState
                midState = tx.intermediateState
                try:
                    newEl = Element(el,finalState=fs,intermediateState=midState,model=tx._particles)
                except Exception as e:
                    logger.error(str(e))
                    logger.error("Error building elements. Are the versions of smodels-utils and smodels compatible?")
                    sys.exit()

                datasetElements.append(newEl)
        for iel,elA in enumerate(datasetElements):
            for jel,elB in enumerate(datasetElements):
                if jel <= iel:
                    continue

                if hasattr ( elA, "particlesMatch" ) and elA.particlesMatch(elB):
                        logger.error("Constraints (%s <-> %s) appearing in dataset %s overlap (may result in double counting)" %(elA,elB,self))
                        return False
                if elA == elB:
                    logger.error("Constraints (%s <-> %s) appearing in dataset %s overlap (may result in double counting)" %(elA,elB,self))
                    return False

        return True

class TxNameInput(Locker):

    """
    Holds all informations related to one txName
    """


    infoAttr = ['txName','constraint', 'condition','conditionDescription',
                'susyProcess','checked','figureUrl','dataUrl','source',
                'comment', 'validated','axes','upperLimits', 'validationTarball',
                'efficiencyMap','expectedUpperLimits','xrange', 'yrange' ]
    internalAttr = ['_name', 'name', '_txDecay','_planes','_goodPlanes',
                    '_branchcondition', 'onShell', 'offShell', 'constraint',
                    'condition', 'conditionDescription','massConstraint',
                    'upperLimits','efficiencyMap','expectedUpperLimits',
                    'massConstraints', '_dataLabels', 'round_to',
                    '_databaseParticles', '_smallerThanError', '_particles' ]

    requiredAttr = [ 'constraint','condition','txName','axes','dataUrl',
                     'source' ]
    infoAttr.append ( 'finalState' )
    infoAttr.append ( 'intermediateState' )
    requiredAttr.append ( 'finalState' )
    __hasWarned__ = { "omitted": 0 }
    round_to = 7 ## number of digits to round to

    def addValidationTarballsFromPlanes ( self ):
        """ if a mass plane has a validation tarball defined,
        add it to to this TxnameInput object, together with axis name """
        for p in self._planes:
            if hasattr ( p, "validationTarball" ):
                line = str(p).replace(" ","")+":"+p.validationTarball
                if not hasattr ( self, "validationTarball" ) or self.validationTarball in [ "", None ]:
                    self.validationTarball = line
                else:
                    self.validationTarball += ";" + line

    def addXYRangesFromPlanes ( self ):
        """ if a mass plane has xrange or yrange defined, add it to this
            TxnameInput object, together with the axis name """
        for p in self._planes:
           if hasattr ( p, "xrange" ):
                line = str(p).replace(" ","")+":"+p.xrange
                if not hasattr ( self, "xrange" ) or self.xrange in [ "", None ]:
                    self.xrange = line
                else:
                    self.xrange += ";" + line
           if hasattr ( p, "yrange" ):
                line = str(p).replace(" ","")+":"+p.yrange
                if not hasattr ( self, "yrange" ) or self.yrange in [ "", None ]:
                    self.yrange = line
                else:
                    self.yrange += ";" + line

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
        self._smallerThanError = 0
        self.txName = txName
        self.finalState = ['MET','MET']
        self.intermediateState = None
        self.susyProcess = prettyDescriptions.prettyTxname(txName,outputtype="text")
        self._txDecay = TxDecay(self._name)
        if not self._txDecay:
            logger.error("Unknown txname %s" %self._name)
            sys.exit()
        self._planes = []
        self._goodPlanes = []
        self._dataLabels = []
        self.setDefaultParticles()


    def __str__(self):

        return self._name

    def setDefaultParticles(self):
        """
        Load the default particles contained in the smodels/experiment/defaultFinalStates.py.
        """

        from smodels.experiment.defaultFinalStates import finalStates
        self._particles = finalStates


    def setParticlesFromFile(self,particlesFile):
        """
        Load the particles contained in the particlesFile. These are stored in self._particles
        and used to build the txname elements.
        """

        pFile = os.path.abspath(particlesFile)
        if not os.path.isfile(pFile):
            logger.error("Could not find file %s" %pFile)
            sys.exit()

        from importlib import import_module
        sys.path.append(os.path.dirname(pFile))
        pF = os.path.basename(os.path.splitext(pFile)[0])
        logger.debug("Loading database particles from: %s" %pFile)
        modelFile = import_module(pF, package='smodels')
        if not hasattr(modelFile,'finalStates'):
            logger.error("Model definition (finalStates) not found in" % pFile)
        else:
            #set model name to file location:
            modelFile.finalStates.label = os.path.basename(pFile)
            self._particles = modelFile.finalStates

    def addMassPlane(self, plane):

        """
        add a MassPlane object with given axes to self.planes.
        Add new attributes to the MassPlane.
        :param txDecay: object of type TxDecay
        :param plane: A MassPlane object or the full mass array containing
                      equations which relate the physical masses and the plane
                      coordinates, using the pre-defined 'x','y',.. symbols.
        (e.g. [[x,y],[x,y]]).
        :raise missingMassError: if one mass entry is missing
        :raise onlyOnePlaneError: if a second mass plane is given and the related mass space
        have only 2 dimensions
        :raise interMediateParticleError: if a interMasses are given and the related
                                          mass space
        have only 2 dimensions
        :return: MassPlane-object
        """

        if isinstance(plane,MassPlane):
            self._planes.append(plane)
            return plane
        elif isinstance(plane,list):
            massArray = plane
        else:
            logger.error("Input must be a MassPlane object or a mass array")
            sys.exit()
        try:
            element = Element(elementsInStr(self.constraint,removeQuotes=False)[0],
                            intermediateState=self.intermediateState,
                            finalState=self.finalState,
                            model = self._particles)
        except Exception as e:
            logger.error(str(e))
            logger.error("Error building elements. Are the versions of smodels-utils and smodels compatible?")
            sys.exit()


        #Checks for new input
        if len(massArray) != len(element.branches):
            logger.error("Mass array definition %s is not consistent with the txname constraint %s"
                         %(str(massArray),str(element)))
            sys.exit()
        for ibr,br in enumerate(element.branches):
            if str(br) == '[*]':  #Ignore wildcard branches
                continue
            if len(massArray[ibr]) != br.vertnumb+1:
                logger.error("Mass array definition (%d-dim) is not consistent with the txname constraint (%d-dim) in %s [%s]" % ( len(massArray[ibr]), br.vertnumb+1, self._txDecay, plane ))
                sys.exit()
        #Create mass plane for new input
        massPlane = MassPlane(self._txDecay,massArray)
        self._planes.append(massPlane)
        return massPlane

    def getDataFromPlanes(self,dataType):
        """
        Loop over the defined planes and collects the data.
        Reads the source file and stores the data.
        Stores which planes have data for this txname in _goodPlanes.

        :param dataType: Type of data (efficiencyMap or upperLimit)
        """


        for plane in self._planes:
            logger.info('Reading mass plane: %s, %s' % (self, plane))

            if dataType == 'upperLimit':
                if not hasattr(plane,'upperLimits'):
                    logger.error('%s source not defined for plane %s' %(dataType,plane))
                    sys.exit()
                else:
                    if self.addDataFrom(plane,'upperLimits'):
                        self._dataLabels.append('upperLimits')
                        #Avoid adding the same plane twice
                        if not plane in self._goodPlanes:
                            self._goodPlanes.append(plane)
            elif dataType == 'efficiencyMap':
                if not hasattr(plane,'efficiencyMap'):
                    logger.warning('%s source not defined for plane %s' %(dataType,plane))
                    if not plane in self._goodPlanes:
                        self._goodPlanes.append(plane)
                    # sys.exit()
                else:
                    if self.addDataFrom(plane,'efficiencyMap'):
                        self._dataLabels.append('efficiencyMap')
                        #Avoid adding the same plane twice
                        if not plane in self._goodPlanes:
                            self._goodPlanes.append(plane)
            else:
                logger.error('Unknown data type %s' %dataType)
                sys.exit()

            #Add expected upper limits, if it exists:
            if hasattr(plane,'expectedUpperLimits'):
                if self.addDataFrom(plane,'expectedUpperLimits'):
                    self._dataLabels.append('expectedUpperLimits')
                    #Avoid adding the same plane twice
                    if not plane in self._goodPlanes:
                        self._goodPlanes.append(plane)

    def getMetaData(self):
        """
        Collects all the info attributes from its mass planes
        (only for the planes which generated data and are stored
        in _goodPlanes) and stores it in self.
        Also defines additional information.
        """

        for infoAttr in self.infoAttr:
            infoList = [""]*len(self._goodPlanes)
            planeHasInfo = False
            for i,plane in enumerate(self._goodPlanes):
                if not infoAttr in plane.infoAttr:
                    continue
                if hasattr(plane,infoAttr):
                    planeHasInfo = True
                    infoList[i] = str(getattr(plane, infoAttr))
            if planeHasInfo:
                # infoStr = " ".join(infoList) ## new version
                myInfoList = []
                hasNone = False
                ## remove Nones, but only if there are other values.
                for i in infoList:
                    if i not in [ None, "None" ]:
                        myInfoList.append ( i )
                    else:
                        hasNone = True
                if hasNone and len(myInfoList)==0:
                    myInfoList = [ "None" ]
                # myInfoList.sort()
                infoStr = ";".join(myInfoList) ## old version
                # infoStr = ";".join(set(myInfoList)) ## old version
                setattr(self,infoAttr,infoStr)

        if not hasattr(self,'validated'):
            self.validated = 'TBD'


    def widthsInNs ( self, units ):
        """ find out if widths are meant to be given in ns """
        if type(units) != tuple:
            return False
        if len(units)<2:
            return False
        return units[1]=="ns"

    def getValueUnit ( self, unit ):
        """ get the unit of the 'value' field, so eff or UL
        :param nmasses: number of o
        """
        if type(unit)==str:
            return unit
        if unit[-1].startswith ( "/1" ):
            return unit[-1]
        if unit[-1] in [ "%", "" ]:
            return unit[-1]
        if unit[-1] in [ "GeV", "ns", "GeV" ]:
            return ""
        if unit[-1] in [ "fb", "pb" ]:
            return unit[-1]
        logger.error ( f"cannot determine the unit of the values from {unit}" )
        return ""

    def addDataFrom(self, plane, dataLabel):

        """
        extend the given data list by the values related to this type of list
        examples for data lists are: upperLimits, efficiencyMaps, ....
        The values held by the given mass plane are extended to the data list.
        If self does not contain the dataLabel, set this attribute.

        :param plane: MassPlane-object
        :param dataLabel: label of the given data (efficiencyMap, upperLimits,..)

        """

        #Get dimension of the plot:
        nvars = len(plane.xvars)
        if nvars < 1 or nvars > 4:
            logger.error('Can not deal with %i variables' %nvars)
            sys.exit()

        #Check if plane has a dataLabel object holder:
        if not hasattr(plane,dataLabel):
            logger.error("Plane %s does not contain data holder for dataLabel %s" %(plane,dataLabel))
            sys.exit()

        dataHandler = getattr(plane,dataLabel)

        #Check if acceptances have been defined and reweight efficiencies by acceptance data:
        if dataLabel == 'efficiencyMap':
            if hasattr(plane, 'acceptanceMap'):
                acceptanceData = getattr(plane,'acceptanceMap')
                dataHandler.reweightBy(acceptanceData)

        dataList = []
        for ptDict in dataHandler:

            if len(ptDict) != nvars+1:
                logger.error( f"Number of free parameters in data ({ptDict}) and in axes ({plane.xvars}) do not match")
                sys.exit()

            #ptDic is of the form: {x : float, y : float, value-key : float}
            #where value-key is any key identifying the (upper limit,efficiency,..) value
            #Restrict the pt dictionary to only the variable values:
            xDict = dict([[str(xv),v] for xv,v in ptDict.items() if xv in plane.xvars])
            #Get the (upper limit, efficiency,..) value:
            value = [v for xv,v in ptDict.items() if  not xv in plane.xvars][0]
            massArray = plane.getParticleMasses(**xDict)
            skipMass = False
            #Check if the massArray is positive and value is positive:
            for br in massArray:
                if br == None:
                    skipMass = True
                    continue
                for M in br:
                    if (type(M) == float and M<0.) or type(M) == tuple and M[0]<0.:
                        skipMass = True
                        if not quenchNegativeMasses:
                            logger.warning("Negative mass value found for %s. Point %s will be ignored." %(self,massArray))
                        continue
                    if type(M) == tuple and M[1]<0.:
                        skipMass = True
                        logger.warning("Negative lifetime found for %s. Point %s will be ignored." %(self,massArray))
                        continue
            if value < 0.:
                skipMass = True
                logger.warning("Negative value for %s found. Point %s will be ignored." %(self,str(massArray)))
            if skipMass:
                continue
            #Check if mass array is consistent with the mass constraints given by the
            #txname constraint. If not, skip this mass.
            if not self.checkMassConstraints(massArray):
                continue
            #Add units
            if hasattr(dataHandler, 'unit') and dataHandler.unit:
                unit = self.getValueUnit ( dataHandler.unit )
                if unit == "%":
                    value = value / 100.
                elif unit == "/10000":
                    value = value / 10000.
                elif self.widthsInNs(dataHandler.unit):
                    pass #
                elif type(unit) == str and unit.startswith ( "/" ):
                    factor = unit[1:]
                    try:
                        factor = float ( factor )
                    except ValueError as e:
                        logger.error ( f"unit starting with / is meant as a factor. cannot cast {dataHandler.unit[1:]} to a float!" )
                    value = value / factor
                elif type(unit) == str and unit.startswith ( "*" ):
                    factor = unit[1:]
                    try:
                        factor = float ( factor )
                    except ValueError as e:
                        logger.error ( f"unit starting with * is meant as a factor. cannot cast {dataHandler.unit[1:]} to a float!" )
                    value = value * factor
                else:
                    value = value*eval(unit, {'fb':fb,'pb': pb,'GeV': GeV,'TeV': TeV})
            if hasattr(dataHandler, 'massUnit') and dataHandler.massUnit:
                for i,br in enumerate(massArray):
                    if isinstance(br,str):  #Allow for string identifiers in the mass array
                        continue
                    for j,M in enumerate(br):
                        if isinstance(M,tuple):
                            m0 = M[0]*eval(dataHandler.massUnit,{'GeV': GeV,'TeV': TeV})
                            if self.widthsInNs(dataHandler.unit):
                                m1 = hbar / M[1] * GeV
                            else:
                                m1 = M[1] * GeV ## width in GeV
                            M = ( m0, m1 )
                        if isinstance(M,(float,int)):
                            M = M*eval(dataHandler.massUnit,{'GeV': GeV,'TeV': TeV})
                        massArray[i][j] = M
            dataList.append([massArray, value])


        if not dataList:
            logger.warning('Could not retrieve data for %s (plane %s)' %(self,plane))
            return False
        #Add data to txname. If dataLabel already exists, extend it
        if hasattr(self,dataLabel) and isinstance(getattr(self,dataLabel),list):
            txData = getattr(self,dataLabel)
            txData += dataList
        else:
            setattr(self,dataLabel,dataList)
        return True

    def hasData(self, dataType):

        """
        Check if txname has data of the type dataLabel.
        Returns True/False

        :param dataType: Type of data (efficiencyMap or upperLimit)
        """

        if dataType == 'upperLimit':
            if not hasattr(self,'upperLimits') or not getattr(self,'upperLimits'):
                return False
        elif dataType == 'efficiencyMap':
            if not hasattr(self,'efficiencyMap') or not getattr(self,'efficiencyMap'):
                return False
        else:
            logger.error("DataType %s unknown" %dataType)
            sys.exit()

        return True



    def _setMassConstraints(self):
        """
        Define the mass constraints for the txname, based
        on its constraint. The constraints on the mass differences of the BSM
        particles are given as a nested array (according to the constraint format)
        containing string inequalities to be satisfied by the BSM masses.
        (e.g. for the constraint [[[t,t]],[[t,t]] we have the
        mass constraint [['m > 169.+169.'],['m > 169.+169.']].
        """


        #Replace particles appearing in the vertices by their mass
        self.massConstraints = []
        for el in elementsInStr(self.constraint,removeQuotes=False):
            try:
                element = Element(el,
                                intermediateState=self.intermediateState,
                                finalState=self.finalState,
                                model = self._particles)
            except Exception as e:
                logger.error(str(e))
                logger.error("Error building elements. Are the versions of smodels-utils and smodels compatible?")
                sys.exit()
            #Get even particles from vertices:
            particles = element.evenParticles
            #Compute minimum mass difference (sum over SM final state masses)
            elConstraint = []
            for branch in particles:
                branchConstraint = []
                for vertex in branch:
                    vertexMasses = []
                    for ptc in vertex:
                        if not hasattr(ptc,'mass'):
                            continue
                        elif isinstance(ptc.mass,list):
                            vertexMasses.append(max(ptc.mass).asNumber(GeV))
                        else:
                            vertexMasses.append(ptc.mass.asNumber(GeV))
                    vertexConstraint = "dm >= %s" %str(sum(vertexMasses))
                    branchConstraint.append(vertexConstraint)
                elConstraint.append(branchConstraint)
            self.massConstraints.append(elConstraint)

    def warn ( self, *txt ):
        t=str(*txt)
        if not t in self.__hasWarned__:
            self.__hasWarned__[t] = 0
        self.__hasWarned__[t]+=1
        if self.__hasWarned__[t]<2:
            logger.warn ( t )
        if self.__hasWarned__[t]==2:
            self.__hasWarned__["omitted"]+=1
            if self.__hasWarned__["omitted"]<2:
                logger.warn ( "(omitted more such msgs)" )

    def error ( self, line ):
        if not line in self.__hasWarned__:
            self.__hasWarned__[line]=0
        self.__hasWarned__[line]+=1
        if self.__hasWarned__[line]<2:
            logger.error ( line )

    def checkMassConstraints(self,massArray):
        """
        Check if massArray satisfies the mass constraints defined in massConstraints

        If the txname constraint contains several elements, require that massArray
        satisfies the constaint for at least one of the elements.

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
        if len(massArray)==0:
            line = f"empty mass array {massArray} for constraint {self.massConstraints}??"
            if not line in errormsgs:
                logger.error ( line )
                errormsgs[line]=0
            errormsgs[line]+=1
            return True

        for elMass in self.massConstraints:
            goodMasses = True
            for ib,br in enumerate(elMass):
                if len(massArray)<=ib:
                    if not massArray == [[], []]:
                        self.error ( f"something is wrong with the mass array {massArray}, ib={ib}" )
                    return False
                for iv,vertex in enumerate(br):
                    if len(massArray[ib])<=iv:
                        if not massArray == [[], []]:
                            self.error ( f"something is wrong with the mass array {massArray}, ib={ib}, iv={iv}" )
                        return False
                    m1 = massArray[ib][iv]
                    if type(m1) == tuple:
                        m1 = m1[0]
                    m2 = massArray[ib][iv+1]
                    if type(m2) == tuple:
                        m2 = m2[0]
                    if type(m1)==str:
                        self.warn ( f"expected masses/floats, got string: ''{m1}''. skip it." )
                        continue
                    if type(m2)==str:
                        self.warn ( f"expected masses/floats, got string: ''{m2}''. skip it." )
                        continue
                    massDiff = m1-m2
                    if massDiff < 0.:
                        self._smallerThanError += 1
                        if not quenchNegativeMasses:
                            if self._smallerThanError < 4:
                                logger.error("Parent mass (%.1f) is smaller than daughter mass (%.1f) for %s" % (m1,m2,str(self)))
                            if self._smallerThanError == 4:
                                logger.error("(I quenched a few more error msgs as the one above)" )
                        return False
                    #Evaluate the inequality replacing m by the mass difference:
                    check = eval(vertex,{'dm' : massDiff})
                    if check == False:
                        goodMasses = False
                        break
                    if not check in [ False, True ]:
                        logger.error("Something went wrong evaluating the mass constraint %s. Check was %s(%s), massDiff was %s" % ( vertex, check, type(check), massDiff ) )
                        return False
            if goodMasses:
                return True

        return False
