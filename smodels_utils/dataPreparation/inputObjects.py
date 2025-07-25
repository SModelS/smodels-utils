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
from smodels.base.physicsUnits import fb, pb, TeV, GeV
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.dataPreparation.graphMassPlaneObjects import GraphMassPlane
from smodels.experiment.expSMS import ExpSMS
from smodels.experiment.expAuxiliaryFuncs import smsInStr
from smodels.installation import version
import copy
import math
import scipy
from typing import Dict, Union

import logging
from smodels_utils.helper import prettyDescriptions
from smodels_utils.helper.terminalcolors import *

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.WARNING)
quenchNegativeMasses = False ## set to true, if you wish to
# quench the warning about negative masses
errormsgs = {}
# if on, will check for overlapping constraints
_complainAboutOverlappingConstraints = False

complainAbout = { "sympy obj": 0, "x in datamap": 0, "axesMap": 0 }

def elementsInStr(instring : str,removeQuotes : bool = True) -> list: ## from V2
    """
    Parse instring and return a list of elements appearing in instring.
    instring can also be a list of strings.

    :param instring: string containing elements (e.g. "[[['e+']],[['e-']]]+[[['mu+']],[['mu-']]]")
    :param removeQuotes: If True, it will remove the quotes from the particle labels.
                         Set to False, if one wants to run eval on the output.

    :returns: list of elements appearing in instring in string format

    """
    outstr = ""
    if isinstance(instring,str):
        outstr = instring
    elif isinstance(instring,list):
        for st in instring:
            if not isinstance(st,str):
                logger.error("Input must be a string or a list of strings")
                raise SModelSError()
            # Combine list of strings in a single string
            outstr += st
    else:
        raise SModelSError(f"syntax error in constraint/condition: ``{instring}''."\
              "Check your constraints and conditions in your database." )

    elements = []
    outstr = outstr.replace(" ", "")
    if removeQuotes:
        outstr = outstr.replace("'", "")
    elStr = ""
    nc = 0
    # Parse the string and looks for matching ['s and ]'s, when the matching is
    # complete, store element
    for c in outstr:
        delta = 0
        if c == '[':
            delta = -1
        elif c == ']':
            delta = 1
        nc += delta
        if nc != 0:
            elStr += c
        if nc == 0 and delta != 0:
            elements.append(elStr + c)
            elStr = ""
            # Syntax checks
            ptclist = elements[-1].replace(']', ',').replace('[', ',').\
                    split(',')
            for ptc in ptclist:
                ptc = ptc.replace("'","")
                if not ptc:
                    continue

    # Check if there are not unmatched ['s and/or ]'s in the string
    if nc != 0:
        raise SModelSError("Wrong input (incomplete elements?) " + instring)

    return elements

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

def getStatsEMBaked ( statsfile : os.PathLike = "orig/statsEM.py" ) -> Dict:
    """ retrieve the stats from an emBaked stats file """
    if not os.path.exists ( statsfile ):
        print ( f"ERROR: cannot find {statsfile}" )
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
        logger.error( f"Attribute {name} is not allowed for {type(self)}" )

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
    'publication', 'publicationDOI', 'contact', 'supersededBy','supersedes', 'comment', 'modelFile', 'datasetOrderForModel',
    'private', 'implementedBy','lastUpdate', 'datasetOrder', 'covariance',
    'combinableWith', 'jsonFiles', 'jsonFiles_FullLikelihood', 'source',
    'Leff_inner', 'Leff_outer', 'type',
    'includeCRs', 'onnxFiles', 'resultType', 'signalUncertainty' ]
    internalAttr = ['_sqrts', '_lumi']

    requiredAttr = ['sqrts', 'lumi', 'id', 'lastUpdate']

    def __new__( cls, ID : str ):
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

    def createCovarianceMatrix ( self, filename : str,
            histoname : Union[str,None] = None, addOrder : bool =True,
            max_datasets : Union[int,None] = None,
            aggregate : Union[list,None] = None,
            datasets : Union[list,None] = None,
            matrixIsCorrelations : bool = False,
            aggprefix : str ="ar", zeroIndexed : bool = False,
            scaleCov : float = 1.0, blinded_regions : list = [] ):
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
        :param max_datasets: if not None, restrict the number of datasets
        :param aggregate: aggregate signal regions, given by indices, e.g.
         [[0,1,2],[3,4]] or signal region names, e.g.[["sr0","sr1"],["sr2"]].
        :param datasets: list of datasets, so we can cross-check the covariance
         matrix with the errors given per signal region
        :param matrixIsCorrelations: if true, then assume that we histoname
        refers to a correlation matrix, not a covariance matrix, so multiply with
        the SR erros, accordingly
        :param aggprefix: prefix for aggregate signal region names, eg ar0, ar1, etc
        :param zeroIndexed: are indices given one-indexed or zero-indexed
        :param scaleCov: allows to downscale the offdiagonal elements, so that
        the determinant stays firmly positive
        :param blinded_regions: list of regions we omit
        """
        if type(filename)==dict:
            if zeroIndexed:
                logger.error ( "zeroIndex not implemented for FakeCovarianceHandler" )
            if abs ( scaleCov - 1. ) > 1e-20:
                logger.error ( "scaleCov not implemented for FakeCovarianceHandler" )
            handler = FakeCovarianceHandler ( filename, max_datasets, aggregate,
                    aggprefix )
        elif filename.endswith ( ".csv" ):
            if zeroIndexed:
                logger.error ( "zeroIndex not implemented for CSVCovarianceHandler" )
            if abs ( scaleCov - 1. ) > 1e-20:
                logger.error ( "scaleCov not implemented for CSVCovarianceHandler" )
            handler = CSVCovarianceHandler ( filename,
                    max_datasets, aggregate, aggprefix )
        else:
            """
            try:
                import ROOT
                handler = PYROOTCovarianceHandler ( filename, histoname, max_datasets,
                    aggregate, aggprefix )
            except ModuleNotFoundError as e:
                logger.error ( "could not import pyroot, trying uproot now" )
                handler = UPROOTCovarianceHandler ( filename, histoname, max_datasets,
                    aggregate, aggprefix )
            """
            try:
                import uproot
                handler = UPROOTCovarianceHandler ( filename, histoname,
                    max_datasets, aggregate, aggprefix, zeroIndexed,
                    scaleCov = scaleCov, blinded_regions = blinded_regions,
                    datasets = datasets )
            except ModuleNotFoundError as e:
                logger.error ( "could not import uproot, trying pyroot now" )
                if zeroIndexed:
                    logger.error ( "zeroIndex not implemented for PYROOTCovarianceHandler" )
                    sys.exit()
                if abs ( scaleCov - 1. ) > 1e-20:
                    logger.error ( "scaleCov not implemented for PYROOTCovarianceHandler" )
                    sys.exit()
                if len ( blinded_regions ) > 0:
                    logger.error ( "blinded_regions not implemented for PYROOTCovarianceHandler" )
                    sys.exit()

                handler = PYROOTCovarianceHandler ( filename, histoname, max_datasets,
                    aggregate, aggprefix )

        if not hasattr ( self, "datasetOrder" ) or addOrder == "overwrite":
            if addOrder:
                self.datasetOrder = ", ".join ( [ f'"{x}"' for x in  handler.datasetOrder ] )
            else:
                self.datasetOrder = ", ".join ( [ f'"SR{x+1}"' for x in range ( handler.n ) ] )
        self.covariance = handler.covariance
        if True: ## pretty print
            self.covariance = "["
            for rowctr,row in enumerate(handler.covariance):
                self.covariance += "["
                for colctr,x in enumerate(row):
                    if matrixIsCorrelations:
                        if datasets == None:
                            logger.error ( "you supplied correlations, now i need datasets" )
                            sys.exit()
                        oldx=x
                        x = x * datasets[colctr].bgError * datasets[rowctr].bgError
                        #if colctr < 2 and rowctr < 2:
                        #    logger.error ( f">>> ctrs={colctr}, {rowctr}, bgerr={datasets[colctr].bgError}, x={oldx}, {x}" )
                    if rowctr==colctr:
                        logger.debug ( f"variance({rowctr+1},{colctr+1})={x}" )
                        if datasets != None:
                            dsSigma = (datasets[rowctr].bgError)
                            dsVar = (datasets[rowctr].bgError)**2
                            if dsVar > 1.5 * x and not matrixIsCorrelations and covarianceHandler.overrideWithConservativeErrors:
                                logger.error ( f"variance determined from table ({dsVar:.2g}) is more than 1.5*variance in covariance matrix ({x:.2g}) at #({rowctr+1}). replace variance in covariance matrix with more conservative estimate." )
                                x = dsVar
                            logger.debug ( f"dataset({rowctr+1})^2={dsSigma}^2={dsVar}" )
                            off = max ( dsVar,x ) / min ( dsVar,x)
                            logger.debug ( f"it is a factor of {off:.1f} off" )
                            err = 2.*(dsVar-x ) / (dsVar+x)
                            logger.debug ( f"relative error on variance {100*err:.1f} percent" )
                    self.covariance += f"{x:.4g}, "
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
            if len(check) == 1: return f'{value}{operation}{unit}'
            if len(check) == 2: return value
            return False
        try:
            check = float(value)
            return f'{value}{operation}{unit}'
        except:
            return False


class DataSetInput(Locker):
    """
    Holds all informations related to one dataset
    """


    infoAttr = ['dataId','dataType','observedN','expectedBG','bgError', 'comment',
                'upperLimit', 'expectedUpperLimit', 'aggregated', 'jsonfile', 'lumi',
                'originalSRs', 'thirdMoment', 'regionType' ]
    internalAttr = ['_name','_txnameList']

    requiredAttr = ['dataType', 'dataId']

    ntoys = 200000 ## number of toys in computing limits

    def __init__(self,name):

        """initialize the dataset
        :param name: name of dataset (used as folder name)
        """
        if name == None:
            name = "data"
        if type(name)!=str or len(name)<1: ## or name[0] not in string.ascii_letters:
            logger.error ( f"Illegal dataset name: ``{name}''. Make sure it starts with a letter." )
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

    def computeULs ( self ):
        #First check if a luminosity has been defined for the dataset
        if hasattr(self,"lumi"):
            lumi = self.lumi
        else:
            lumi = getattr(databaseCreator.metaInfo,'lumi')
        if isinstance(lumi,str):
            lumi = eval(lumi,{'fb':fb,'pb': pb})
        # lumi = lumi.asNumber(1./fb)
        if False: ## the spey stuff
            try:
                import spey
            except ImportError as e:
                print ( f"[inputObjects] seems like you dont have spey. install it!" )
                sys.exit()
            from smodels.tools.speyTools import SpeyComputer, SimpleSpeyDataSet
            dataset = SimpleSpeyDataSet ( float(self.observedN),
                        float(self.expectedBG), float(self.bgError), lumi )
            computer = SpeyComputer ( dataset, 1. )
            try:
                ulspey = computer.poi_upper_limit ( expected = False, limit_on_xsec = True )
                ulspeyE = computer.poi_upper_limit ( expected = True, limit_on_xsec = True )
            except Exception as e:
                ulspey = computer.poi_upper_limit ( evaluationType = observed, limit_on_xsec = True )
                ulspeyE = computer.poi_upper_limit ( evaluationType = apriori, limit_on_xsec = True )
            #Round numbers:
            ulspey, ulspeyE = round_list(( ulspey.asNumber(fb),ulspeyE.asNumber(fb)), 4)
            return ulspey, ulspeyE
        alpha = .05
        try:
            try:
                # v3.1.0
                # new API
                from smodels.statistics.simplifiedLikelihoods import Data, UpperLimitComputer, LikelihoodComputer
                from smodels.statistics.basicStats import aposteriori
                m = Data ( self.observedN, self.expectedBG, self.bgError**2, None, 1.,
                           lumi = lumi )
                llhdComp = LikelihoodComputer  ( m )
                comp = UpperLimitComputer ( llhdComp, 1. - alpha )
                ul = comp.getUpperLimitOnSigmaTimesEff ( ).asNumber ( fb )
                try:
                    ulExpected = comp.getUpperLimitOnSigmaTimesEff ( expected=aposteriori ).asNumber ( fb )
                except Exception as e:
                    ulExpected = comp.getUpperLimitOnSigmaTimesEff ( evaluationType=aposteriori ).asNumber ( fb )
                if type(ul) == type(None):
                    ul = comp.getUpperLimitOnSigmaTimesEff ( m, )
                ul, ulExpected = round_list(( ul, ulExpected ), 4)
                return ul, ulExpected

            except Exception as e:
                print ( f"[inputObjects] Exception {e}, will try with older version" )
            try:
                # v3.0.0
                from smodels.statistics.simplifiedLikelihoods import Data, UpperLimitComputer
                # new API
                m = Data ( self.observedN, self.expectedBG, self.bgError**2, None, 1.,
                           lumi = lumi )
                comp = UpperLimitComputer ( 1. - alpha )
                ul = comp.getUpperLimitOnSigmaTimesEff ( m ).asNumber ( fb )
                ulExpected = comp.getUpperLimitOnSigmaTimesEff ( m, expected="posteriori" ).asNumber ( fb )
                if type(ul) == type(None):
                    ul = comp.getUpperLimitOnSigmaTimesEff ( m, )
                ul, ulExpected = round_list(( ul, ulExpected ), 4)
                print ( f"[inputObjects] older version worked!" )
                return ul, ulExpected

            except Exception as e:
                print ( "Exception", e  )
        except Exception as e:
            print ( f"[inputObjects] Exception {e}" )
        # print ( "@>>>>>", "obs", m.observed, "bg", m.backgrounds, "+-", m.covariance )
        # print ( "SModelS ul", ul, "ule", ulExpected )
        # print ( "spey ul", ulspey, ulspeyE )
        return None, None

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

        ul, ulExpected = self.computeULs ( )
        self.upperLimit = str(ul)+'*fb'
        self.expectedUpperLimit = str(ulExpected)+'*fb'

    def addTxName( self,txname : str ):
        """
        Adds txname to dataset. Checks if txname already exists and
        raise an error if it does.

        :param txname: txname (string)

        :return: TxNameInput object
        """

        for txobj in self._txnameList:
            if txobj._name == txname:
                logger.error( f"Txname {txname} already exists in dataset" )
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
            logger.error( f"Dataset {self} does not contain txnames" )
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
                logger.info( f"{self}:{tx.txName} has neither upperLimits nor efficiencyMap data. skip it!" )
                # return False
            if len(txDataTypes) > 1:
                logger.error( f"Txname {tx.txName} has mixed data types" )
                return False
            if len(txDataTypes) > 0 and not self.dataType in txDataTypes[0]:
                logger.error( f"Txname {tx.txName} data type ({txDataTypes[0]}) does not match dataset type ({self.dataType})" )
                return False


        if self.dataType != 'efficiencyMap':
            return True

        #Check constraints (only for EM results):
        datasetElements = []
        for tx in self._txnameList:
            for el in smsInStr(tx.constraint):
                newEl = None
                fs = tx.finalState
                midState = tx.intermediateState
                try:
                    newEl = ExpSMS.from_string(el,finalState=fs,intermediateState=midState,model=tx._particles)
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
                    logger.error( f"Constraints ({elA} <-> {elB}) appearing in dataset {self} overlap (may result in double counting)" )
                    if not _complainAboutOverlappingConstraints: return True
                    return False
                if elA == elB:
                    logger.error( f"Constraints ({elA} <-> {elB}) appearing in dataset {self} overlap (may result in double counting)" )
                    if not _complainAboutOverlappingConstraints: return True
                    return False

        return True

class TxNameInput(Locker):

    """
    Holds all informations related to one txName
    """


    infoAttr = ['txName','constraint', 'condition','conditionDescription',
                'susyProcess','checked','figureUrl','dataUrl','source',
                'comment', 'validated','axes','upperLimits', 'validationTarball',
                'efficiencyMap','expectedUpperLimits','xrange', 'yrange',
                'axesMap', 'dataMap', 'bsmProcess' ]
    internalAttr = ['_name', 'name', '_txDecay','_planes','_goodPlanes',
                    '_branchcondition', 'onShell', 'offShell', 'constraint',
                    'condition', 'conditionDescription','massConstraint',
                    'upperLimits','efficiencyMap','expectedUpperLimits',
                    'massConstraints', '_dataLabels', 'round_to',
                    '_databaseParticles', '_smallerThanError', '_particles' ]

    requiredAttr = [ 'constraint','condition','txName','dataUrl', 'source' ]
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
                if p.validationTarball == None:
                    # p.validationTarball = "skip"
                    continue
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
               if type(p.xrange) == list:
                   p.xrange=str(p.xrange)
               line = str(p).replace(" ","")+":"+p.xrange
               if not hasattr ( self, "xrange" ) or self.xrange in [ "", None ]:
                   self.xrange = line
               else:
                   self.xrange += ";" + line
           if hasattr ( p, "yrange" ):
               if type(p.yrange) == list:
                   p.yrange=str(p.yrange)
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
        self.bsmProcess = prettyDescriptions.prettyTxname(txName,outputtype="text")
        self._txDecay = TxDecay(self._name)
        if not self._txDecay:
            logger.error( f"Unknown txname {self._name}" )
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
            logger.error( f"Could not find file {pFile}" )
            sys.exit()

        from importlib import import_module
        sys.path.append(os.path.dirname(pFile))
        pF = os.path.basename(os.path.splitext(pFile)[0])
        logger.debug( f"Loading database particles from: {pFile}" )
        modelFile = import_module(pF, package='smodels')
        if not hasattr(modelFile,'finalStates'):
            logger.error( f"Model definition (finalStates) not found in {pFile}" )
        else:
            #set model name to file location:
            modelFile.finalStates.label = os.path.basename(pFile)
            self._particles = modelFile.finalStates

    def addMassPlaneV2(self, plane):
        """
        add a MassPlane object with given axes to self.planes, for axes v2 format
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
            element = ExpSMS.from_string(smsInStr(self.constraint)[0],
                            intermediateState=self.intermediateState,
                            finalState=self.finalState,
                            model = self._particles)
        except Exception as e:
            logger.error(str(e))
            logger.error("Error building elements. Are the versions of smodels-utils and smodels compatible?")
            sys.exit()

        for ibr,br in enumerate(element.branches):
            if str(br) == '[*]':  #Ignore wildcard branches
                continue
            if len(massArray[ibr]) != br.vertnumb+1:
                logger.error( f"Mass array definition ({len(massArray[ibr])}-dim) is not consistent with the txname constraint ({br.vertnumb+1}-dim) in {self._txDecay} [{plane}]" )
                sys.exit()
        #Create mass plane for new input
        massPlane = MassPlane(self._txDecay,massArray)
        self._planes.append(massPlane)
        return massPlane

    def addAxesMap ( self, plane ):
        """ add an axesMap entry. """
        if "z" in str(plane):
            return ## dont add 3d axes. we dont validate them.
        if not hasattr ( self, "axesMap" ):
            self.axesMap = []
        if isinstance(plane,MassPlane):
            import sympy
            x,y,z,w=sympy.var("x y z w")
            s = eval(str(plane))
            if not s in self.axesMap:
                self.axesMap.append ( s )
        elif isinstance(plane,(list,dict)):
            if not plane in self.axesMap:
                self.axesMap.append ( plane )
        elif isinstance(plane,str):
            massArray = eval(plane)
            if not massArray in self.axesMap:
                self.axesMap.append ( massArray )

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
        if type(plane)==list:
            complainAbout["axesMap"]+=1
            if complainAbout["axesMap"]<3:
               logger.error ( f"skipping adding axesMap, hope it is ok, else fix in inputObjects!" )
            if complainAbout["axesMap"]==3:
               logger.error ( f"... " )

        else:
            self.addAxesMap ( plane )
        if isinstance(plane,MassPlane):
            self._planes.append(plane)
            return plane
        elif isinstance(plane,(list,dict)):
            massArray = plane
        elif isinstance(plane,str):
            massArray = eval(plane)
        else:
            logger.error("Input must be a MassPlane object or a mass array")
            sys.exit()
        try:
            element = ExpSMS.from_string(smsInStr(self.constraint)[0],
                            intermediateState=self.intermediateState,
                            finalState=self.finalState,
                            model = self._particles)
        except Exception as e:
            logger.error(str(e))
            logger.error("Error building elements. Are the versions of smodels-utils and smodels compatible?")
            sys.exit()

        #Create mass plane for new input
        if type(massArray)==dict:
            massPlane = GraphMassPlane(self._txDecay,massArray)
        else:
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
            logger.info( f'Reading mass plane: {self}, {plane}' )

            if dataType == 'upperLimit':
                if not hasattr(plane,'upperLimits'):
                    logger.error( f'{dataType} source not defined for plane {plane}' )
                    sys.exit()
                else:
                    if self.addDataFrom(plane,'upperLimits'):
                        self._dataLabels.append('upperLimits')
                        #Avoid adding the same plane twice
                        if not plane in self._goodPlanes:
                            self._goodPlanes.append(plane)
            elif dataType == 'efficiencyMap':
                if not hasattr(plane,'efficiencyMap'):
                    logger.info( f'{dataType} source not defined for plane {plane}' )
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
                logger.error( f'Unknown data type {dataType}' )
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
                doValidateIt=True
                if infoAttr in [ "axes", "validationTarball", "xrange", "yrange" ]:
                    # plane.noValidation = True turns off this plane
                    # as a validation target
                    if hasattr(plane,"noValidation") and plane.noValidation:
                        doValidateIt=False
                if hasattr(plane,infoAttr) and doValidateIt:
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

    def addDataFromV2(self, plane, dataLabel : str ):
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
            logger.error( f'Cannot deal with {nvars} variables' )
            sys.exit()

        #Check if plane has a dataLabel object holder:
        if not hasattr(plane,dataLabel):
            logger.error( f"Plane {plane} does not contain data holder for dataLabel {dataLabel}" )
            sys.exit()

        dataHandler = getattr(plane,dataLabel)

        #Check if acceptances have been defined and reweight efficiencies by acceptance data:
        if dataLabel == 'efficiencyMap':
            if hasattr(plane, 'acceptanceMap'):
                acceptanceData = getattr(plane,'acceptanceMap')
                dataHandler.reweightBy(acceptanceData)

        dataList = []
        for ptDict in dataHandler:
            nPtDict = 0
            for k,v in ptDict.items():
                if k not in [ "constraint", "value" ]:
                    nPtDict += 1

            if nPtDict != nvars:
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
                            logger.warning( f"Negative mass value found for {self}. Point {massArray} will be ignored." )
                        continue
                    if type(M) == tuple and M[1]<0.:
                        skipMass = True
                        logger.warning( f"Negative lifetime found for {self}. Point {massArray} will be ignored." )
                        continue
            if value < 0.:
                skipMass = True
                logger.warning( f"Negative value for {self} found. Point {massArray} will be ignored." )
            if skipMass:
                continue
            #Check if mass array is consistent with the mass constraints given by the
            #txname constraint. If not, skip this mass.
            if not self.checkMassConstraints(massArray,value):
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
            logger.warning( f'Could not retrieve data for {self} (plane {plane})')
            return False
        #Add data to txname. If dataLabel already exists, extend it
        if hasattr(self,dataLabel) and isinstance(getattr(self,dataLabel),list):
            txData = getattr(self,dataLabel)
            txData += dataList
        else:
            setattr(self,dataLabel,dataList)
        return True


    def addDataFrom(self, plane, dataLabel):
        """
        extend the given data list by the values related to this type of list
        examples for data lists are: upperLimits, efficiencyMaps, ....
        The values held by the given mass plane are extended to the data list.
        If self does not contain the dataLabel, set this attribute.

        :param plane: MassPlane-object
        :param dataLabel: label of the given data (efficiencyMap, upperLimits,..)
        """
        if type(plane)==MassPlane:
            return self.addDataFromV2 ( plane, dataLabel )

        #Get dimension of the plot:
        # nvars = len(plane.xvars)
        hasVariables = set() # count
        for ax in plane.xvars:
            for i in [ "x", "y", "z" ]:
                if i in str(ax):
                    hasVariables.add ( i )
        nvars = len ( hasVariables )
        if nvars < 1 or nvars > 4:
            logger.error(f'Can not deal with {nvars} variables' )
            sys.exit()

        #Check if plane has a dataLabel object holder:
        if not hasattr(plane,dataLabel):
            logger.error( f"Plane {plane} does not contain data holder for dataLabel {dataLabel}" )
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
                #sys.exit()

            #ptDic is of the form: {x : float, y : float, value-key : float}
            #where value-key is any key identifying the (upper limit,efficiency,..) value
            #Restrict the pt dictionary to only the variable values:
            xDict = dict([[str(xv),v] for xv,v in ptDict.items() if xv in plane.xvars])
            #Get the (upper limit, efficiency,..) value:
            value = [v for xv,v in ptDict.items() if  not xv in plane.xvars][0]
            massArray = plane.getParticleMasses(**xDict)
            skipMass = False
            #Check if the massArray is positive and value is positive:
            for M in massArray:
                if (type(M) == float and M<0.) or type(M) == tuple and M[0]<0.:
                    skipMass = True
                    if not quenchNegativeMasses:
                        logger.warning( f"Negative mass value found for {self}. Point {massArray} will be ignored." )
                    continue
                if type(M) == tuple and M[1]<0.:
                    skipMass = True
                    logger.warning( f"Negative lifetime found for {self}. Point {massArray} will be ignored." )
                    continue
            if value < 0.:
                skipMass = True
                logger.warning( f"Negative value for {self} found. Point {massArray} will be ignored." )
            if skipMass:
                continue
            #Check if mass array is consistent with the mass constraints given by the
            #txname constraint. If not, skip this mass.
            if not self.checkMassConstraints(massArray,value):
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
            dataList.append([massArray, value])

        if not dataList:
            logger.warning( f'Could not retrieve data for {self} (plane {plane})' )
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
            logger.error( f"DataType {dataType} unknown" )
            sys.exit()

        return True

    def _setMassConstraintsV2(self):
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
        masses = { "higgs": 125.0, "t": 173.1, "Z": 91., "W": 80., "jet": 1.28,
                   "ta": 1.777, "e": 0.0005, "mu": 0.106, "b": 4.7, "c": 1.28 }
        for el in elementsInStr(self.constraint,removeQuotes=False):
            for m in masses.keys():
                for ext in  [ "+", "-", "" ]:
                    el = el.replace( f"[{m}{ext}",f"['{m}{ext}'" )
                    el = el.replace( f",{m}{ext}",f",'{m}{ext}'" )
            try:
                particles = eval(el)
            except SyntaxError as e:
                print ( f"[inputObjects] syntax error {e} for {self.constraint}" )
                import sys; sys.exit(-1)
            #Compute minimum mass difference (sum over SM final state masses)
            elConstraint = []
            for branch in particles:
                branchConstraint = []
                for vertex in branch:
                    vertexMasses = []
                    for ptc in vertex:
                        if ptc in masses:
                            vertexMasses.append(masses[ptc])
                    vertexConstraint = f"dm >= {sum(vertexMasses)}"
                    branchConstraint.append(vertexConstraint)
                elConstraint.append(branchConstraint)
            if elConstraint not in [ [], None ]:
                self.massConstraints.append(elConstraint)

    def _setMassConstraints(self):
        """
        Define the mass constraints for the txname, based
        on its constraint. The constraints on the mass differences of the BSM
        particles are given as a nested array (according to the constraint format)
        containing string inequalities to be satisfied by the BSM masses.
        (e.g. for the constraint [[[t,t]],[[t,t]] we have the
        mass constraint [['m > 169.+169.'],['m > 169.+169.']].
        """

        # Replace particles appearing in the vertices by their mass
        self.massConstraints = []
        if not "PV" in self.constraint:
            return self._setMassConstraintsV2 ()
        # print ( f"{RED}[inputObjects._setMassConstraints] FIXME need to implement this! the mass gaps have been determined, see below. now lets apply them{RESET}" )
        massGaps = {}
        #masses = { "W": 80, "higgs": 125., "top": 173.1, "Z": 91, "b": 4.7,
        #           "c": 1.28, "mu": 0.106, "tau": 1.777, "e": 0.0005, "pi": 0.14 }
        for el in smsInStr(self.constraint):
            try:
                element = ExpSMS.from_string(el,
                                intermediateState=self.intermediateState,
                                finalState=self.finalState,
                                model = self._particles)
                n_nodes = element.number_of_nodes()
                for nodenr in range(1,n_nodes):
                    daughterIndices = element.daughterIndices(nodenr)
                    daughtersP = element.daughters(nodenr)
                    totalmass = 0.
                    bsmDaughter=None
                    for d in daughterIndices:
                        particle = element.nodes[d]
                        # particlename = str(particle).replace("+","").replace("-","")
                        if str(particle) in [ "anyBSM", "MET" ]:
                            bsmDaughter = d
                        #if particlename in masses:
                        #    totalmass += masses[particlename]
                        if hasattr ( particle, "mass" ):
                            mass = particle.mass
                            if isinstance(mass,list):
                                mass = max(mass).asNumber(GeV)
                            else:
                                mass = mass.asNumber(GeV)
                            totalmass += mass
                    if bsmDaughter != None:
                        massGaps[(nodenr,bsmDaughter)]=totalmass
                # import IPython ; IPython.embed ( colors="neutral" )
            except Exception as e:
                logger.error(str(e))
                logger.error("Error building elements. Are the versions of smodels-utils and smodels compatible?")
                sys.exit()
        self.massConstraints.append ( massGaps )

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


    def checkMassConstraintsV2(self,massArray, value = None ):
        #If massConstraints was pre-defined as None or empty list, return always True
        # print ( f"@@0 checkMassConstraintsV2 {self.massConstraints}" )
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
            if elMass == None:
                continue
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
                    if massDiff < 0. and ( value is None or value > 0. ):
                        self._smallerThanError += 1
                        if not quenchNegativeMasses:
                            if self._smallerThanError < 3:
                                logger.error( f"Parent mass ({m1:.1f}) is smaller than daughter mass ({m2:.1f}) for {self} value is {value}" )
                            if self._smallerThanError == 3:
                                logger.error("(I quenched a few more error msgs as the one above)" )
                        return False
                    #Evaluate the inequality replacing m by the mass difference:
                    check = eval(vertex,{'dm' : massDiff})
                    if check == False:
                        goodMasses = False
                        break
                    if not check in [ False, True ]:
                        logger.error( f"Something went wrong evaluating the mass constraint {vertex}. Check was {check}({type(check)}), massDiff was {massDiff}" )
                        return False
            if goodMasses:
                return True

        return False

    def checkMassConstraints(self,massArray, value = None ):
        """
        Check if massArray satisfies the mass constraints defined in massConstraints

        If the txname constraint contains several elements, require that massArray
        satisfies the constaint for at least one of the elements.

        :param massArray: array with masses to be checked. It must be consistend with the
                          topology of the txname constraint.
        :param value: the actual value. if this is zero, then we do not need to complain. if None, we dont take it into account
        """
        if hasattr(self,'massConstraint') and self.massConstraint!=None:
            ## FIXME obsolete?
            self.massConstraints = [self.massConstraint]
        if not hasattr(self,'massConstraints'):
            self._setMassConstraints()
        if len(self.massConstraints)==0: ## no constraints
            return True
        if type(self.massConstraints[0])!=dict:
            return self.checkMassConstraintsV2(massArray, value)
        if not hasattr ( self, "dataMap" ): # dont check
            return True
        #If massConstraints was pre-defined as None or empty list, return always True
        if len(massArray)==0:
            line = f"empty mass array {massArray} for constraint {self.massConstraints}??"
            if not line in errormsgs:
                logger.error ( line )
                errormsgs[line]=0
            errormsgs[line]+=1
            return True
        # print ( f"[inputObjects] checkMassConstraints {self.massConstraints} :: {massArray}" )
        for constraint in self.massConstraints:
            # {(1, 3): 80.0, (2, 4): 125.0}
            for parindices, massGap in constraint.items():
                # now we need to translate from parameterindices to nodeindices
                nodeindices = parindices[0]-1,parindices[1]-1 # wrong
                invertedMap = {}
                for k,v in self.dataMap.items():
                    invertedMap[v[0]]=k
                for x in parindices:
                    if not x in invertedMap:
                        complainAbout["x in datamap"]+=1
                        if complainAbout["x in datamap"]<3:
                            logger.error ( f"could not find {x} in datamap {self.dataMap}" )
                        sys.exit()
                nodeindices = [ invertedMap[x] for x in parindices ]

                dm = massArray[nodeindices[0]]-massArray[nodeindices[1]]
                if type(dm)!=float:
                    complainAbout["sympy obj"]+=1
                    if complainAbout["sympy obj"]<3:
                        print ( f"[inputObjects] FIXME dont know what to do with this sympy expr: {dm} < = {massGap}" )
                    if complainAbout["sympy obj"]==4:
                        print ( f"[inputObjects] (quenched more of the above errors)" )
                if type(dm)==float:
                    if dm <= massGap:
                        # print ( f"skipping {massArray}: does not meet mass constraint: {constraint}" )
                        return False
        return True
        #import IPython ; IPython.embed ( colors="neutral" )
        #sys.exit(-1)
