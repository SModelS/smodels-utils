#!/usr/bin/env python

"""
.. module:: inputObjects
   :synopsis: Holds objects used by convert.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""

import sys
import string
from smodels_utils.helper.txDecays import TxDecay
from smodels_utils.dataPreparation.databaseCreation import databaseCreator,round_list
from smodels_utils.dataPreparation.particleNames import elementsInStr, ptcDic
from smodels_utils.dataPreparation.particles import rEven
from smodels.tools.physicsUnits import fb, pb, TeV, GeV
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels.theory.element import Element
from smodels.installation import version
import copy

import logging
from smodels_utils.helper import prettyDescriptions

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.WARNING)

hscp=False ## central switch for smodels v1.1 versus smodels v1.2
if version()[:3]=="1.2":
    hscp=True
## smodels v1.2 has final states for hscp patch

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

class CovarianceHandler:
    def __init__ ( self, filename, histoname, max_datasets=None,
                   aggregate = None ):
        import ROOT
        f=ROOT.TFile ( filename )
        h=self.getHistogram ( f, histoname )
        xaxis = h.GetXaxis()
        self.n=h.GetNbinsX()+1
        if max_datasets:
            self.n=min(max_datasets+1,self.n)
        self.datasetOrder = []
        self.covariance = []
        self.blinded_regions = []
        for i in range ( 1, self.n ):
            if i in self.blinded_regions:
                continue
            self.datasetOrder.append ( xaxis.GetBinLabel(i) )
            row = []
            for j in range ( 1, self.n ):
                if j in self.blinded_regions:
                    continue
                el = h.GetBinContent ( i, j )
                if i==j and el < 1e-4:
                   logger.error ( "variance in the covariance matrix at position %d has a very small (%g) value" % (i,el) )
                   logger.error ( "will set it to 1e-4" )
                   el = 1e-4
                row.append ( el )
            self.covariance.append ( row )

        if aggregate != None:
            ## aggregate the stuff
            self.aggregateThis ( aggregate )

        self.checkCovarianceMatrix()

    def computeAggCov ( self, agg1, agg2 ):
        """ compute the covariance between agg1 and agg2 """
        C=0.
        for i in agg1:
            for j in agg2:
                C+=self.covariance[i-1][j-1]
        return C

    def checkCovarianceMatrix( self ):
        """ a quick check if the covariance matrix is invertible. """
        from smodels.tools.simplifiedLikelihoods import Data
        n=len(self.covariance)
        m=Data( [0.]*n, [0.]*n, self.covariance )
        logger.info ( "Check %d-dim covariance matrix for positive definiteness." % n )
        try:
            I=(m.covariance)**(-1)
        except Exception as e:
            logger.error ( "Inversion failed. %s" % e )
            sys.exit()
        try:
            from scipy import stats
            l=stats.multivariate_normal.logpdf([0.]*n,mean=[0.]*n,cov=m.covariance)
        except Exception as e:
            import numpy
            logger.error ( "computation of logpdf failed: %s" % e )
            logger.error ( "the diagonal reads: %s " % ( numpy.diag ( m.covariance ) ) )
            sys.exit()


    def aggregateThis ( self, aggregate ):
        newDSOrder=[]
        nNew = len(aggregate)
        row = [0.]*nNew
        newCov = []
        oldcov = copy.deepcopy ( self.covariance )
        for i in range(nNew):
            newCov.append ( copy.deepcopy(row) )
        #logger.error ( "aggregating cov matrix from %d to %d dims." % ( self.n,nNew) )
        for ctr,agg in enumerate ( aggregate ):
            newDSOrder.append ( "ar%d" % ctr )
            V=0.
            for i in agg:
                for j in agg:
                    V+=self.covariance[i-1][j-1]
            newCov[ctr][ctr]=V
            for ctr2,agg2 in enumerate ( aggregate ):
                if ctr == ctr2: continue
                cov = self.computeAggCov ( agg, agg2 )
                newCov[ctr][ctr2]=cov

            #for i,a in enumerate(agg):
            #    newCov[ctr][ctr]+=self.covariance[a][a]
        self.covariance=newCov
        self.datasetOrder=newDSOrder
        #logger.error("datasetOrder %s" % self.datasetOrder )

    def getHistogram ( self, f, histoname ):
        """ simple method to retrieve histogram
        :param f: filehandle
        """
        h=f.Get ( histoname )
        if h: return h
        if not "/" in histoname:
            logger.error ( "cannot find %s in %s" % (histoname, f.GetName()))
            sys.exit()
        tokens = histoname.split("/")
        if not len(tokens)==2:
            logger.error ( "cannot interpret histoname %s in %s" % \
                            ( histoname, f.name ) )
            sys.exit()
        c= f.Get ( tokens[0] )
        if not c:
            logger.error ( "cannot retrieve %s from %s" % \
                            ( histoname, f.name ) )
            sys.exit()
        if c.ClassName() == "TCanvas":
            h=c.GetPrimitive ( tokens[1] )
            if h: return h
            logger.error ( "cannot retrieve %s from %s" % \
                            ( histoname, f.name ) )
            sys.exit()
        logger.error ( "cannot interpret %s in %s" % \
                        ( histoname, f.name ) )
        sys.exit()



class MetaInfoInput(Locker):
    """Holds all informations related to the publication
    (publication means: physic summary note or conference note)
    """

    infoAttr = ['id','sqrts', 'lumi', 'prettyName', 'url', 'arxiv',
    'publication', 'contact', 'supersededBy','supersedes', 'comment',
    'private', 'implementedBy','lastUpdate', 'datasetOrder', 'covariance',
    'combinableWith' ]
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

    def createCovarianceMatrix ( self, filename, histoname, addOrder=True,
                          max_datasets=None, aggregate = None, datasets = None ):
        """ create the covariance matrix from file <filename>, histo <histoname>,
        allowing only a maximum of <max_datasets> datasets. If
        aggregate is not None, aggregate the signal regions, given as
        a list of lists of signal region names, e.g.
        [ [ "sr1", "sr2" ], [ "sr3", "sr4" ] ] or as a list of lists of
        signal numbers, e.g.  [ [ 1, 2 ], [ 3, 4 ] ]
        :param aggregate: aggregate signal regions, given by indices, e.g.
         [[0,1,2],[3,4]] or signal region names, e.g.[["sr0","sr1"],["sr2"]].
        :param datasets: list of datasets, so we can cross-check the covariance
         matrix with the errors given per signal region
        """

        handler = CovarianceHandler ( filename, histoname, max_datasets, aggregate )
        if addOrder:
            self.datasetOrder = ", ".join ( [ '"%s"' % x for x in  handler.datasetOrder ] )
        else:
            self.datasetOrder = ", ".join ( [ '"sr%d"' % (x) for x in range ( handler.n-1 ) ] )
        # print ( "the handlers cov=",len(handler.covariance) )
        self.covariance = handler.covariance
        if True: ## pretty print
            self.covariance = "["
            for rowctr,row in enumerate(handler.covariance):
                self.covariance += "["
                for colctr,x in enumerate(row):
                    if rowctr==colctr:
                        logger.debug ( "variance(%d,%d)=%f" % ( rowctr+1, colctr+1, x ) )
                        if datasets != None:
                            dsSigma = (datasets[rowctr].bgError)
                            dsVar = (datasets[rowctr].bgError)**2
                            if dsVar > 1.2 * x:
                                logger.error ( "variance determined from table (%.2g) is more than 1.2*variance in covariance matrix (%.2g) var #(%d,%d). replace variance in covariance matrix with more conservative estimate." % ( dsVar, x, rowctr+1, colctr+1 ) )
                                x = dsVar
                            logger.debug ( "dataset(%d)^2=%f^2=%f" % ( rowctr+1, dsSigma, dsVar ) )
                            off = max ( dsVar,x ) / min ( dsVar,x)
                            logger.debug ( "it is a factor of %.1f off" % off )
                            err = 2.*(dsVar-x ) / (dsVar+x)
                            logger.debug ( "relative error on variance %.1f percent" % (100.*err) )
                    self.covariance += "%.4g, " % x
                self.covariance = self.covariance[:-2] + "], "
            self.covariance = self.covariance[:-2]+"]"
        # sys.exit()

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


    infoAttr = ['dataId','dataType','observedN','expectedBG','bgError',
                'upperLimit', 'expectedUpperLimit', 'aggregated' ]
    internalAttr = ['_name','_txnameList']

    requiredAttr = ['dataType', 'dataId']

    ntoys = 200000 ## number of toys in computing limits

    def __init__(self,name):

        """initialize the dataset
        :param name: name of dataset (used as folder name)
        """
        if type(name)!=str or len(name)<1 or name[0] not in string.ascii_letters:
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
            logger.error('observedN, expectedBG and bgError must be defined before computing statistics')
            sys.exit()


        lumi = getattr(databaseCreator.metaInfo,'lumi')
        if isinstance(lumi,str):
            lumi = eval(lumi,{'fb':fb,'pb': pb})
        alpha = .05
        try:
            from smodels.tools.simplifiedLikelihoods import Data, UpperLimitComputer
            comp = UpperLimitComputer ( self.ntoys, 1. - alpha )
            m = Data ( self.observedN, self.expectedBG, self.bgError**2, None, 1. )
            ul = comp.ulSigma ( m, marginalize=True ) / lumi.asNumber ( 1. / fb )
            ulExpected = comp.ulSigma ( m, marginalize=True, expected=True ) / lumi.asNumber ( 1. / fb )
        except ModuleNotFoundError as e:
            ## maybe smodels < 1.1.2?
            logger.error ( "cannot import simplifiedLikelihoods module: %s. Maybe upgrade to smodels v1.1.3?" % e )
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
                if hasattr(tx, 'finalState'):
                    fs = tx.finalState
                else:
                    fs = ['MET','MET']
                if not hscp:
                    newEl = Element(el)
                else:
                    newEl = Element(el,fs)
                datasetElements.append(newEl)
        for iel,elA in enumerate(datasetElements):
            for jel,elB in enumerate(datasetElements):
                if jel <= iel:
                    continue

                if elA.particlesMatch(elB):
                    logger.error("Constraints (%s <-> %s) appearing in dataset %s overlap (may result in double counting)" %(elA,elB,self))
                    return False

        return True

class TxNameInput(Locker):

    """
    Holds all informations related to one txName
    """


    infoAttr = ['txName','constraint', 'condition','conditionDescription',
                'susyProcess','checked','figureUrl','dataUrl','source',
                'validated','axes','upperLimits',
                'efficiencyMap','expectedUpperLimits']
    internalAttr = ['_name', 'name', '_txDecay','_planes','_goodPlanes',
                    '_branchcondition', 'onShell', 'offShell', 'constraint',
                    'condition', 'conditionDescription','massConstraint',
                    'upperLimits','efficiencyMap','expectedUpperLimits',
                    'massConstraints', '_dataLabels', 'round_to',
                    '_smallerThanError' ]

    requiredAttr = [ 'constraint','condition','txName','axes','dataUrl',
                     'source' ]
    if hscp:
        infoAttr.append ( 'finalState' )
        requiredAttr.append ( 'finalState' )


    def __init__(self,txName):

        """initialize the txName related values an objects
        checks if the given txName string is valid
        :param txName: name as string
        :raise unknownTxNameError: if txName string is not known by module
        helper.txDecays
        :raise doubleDecayError: if helper.txDecays holds 2 txNames with
        the same decay chain
        """

        self.round_to = 5 ## number of digits to round to
        self._name = txName
        self._smallerThanError = 0
        self.txName = txName
        if hscp:
            self.finalState = ['MET','MET']
        self.susyProcess = prettyDescriptions.prettyTxname(txName,outputtype="text")
        self._txDecay = TxDecay(self._name)
        if not self._txDecay:
            logger.error("Unknown txname %s" %self._name)
            sys.exit()
        self._planes = []
        self._goodPlanes = []
        self._dataLabels = []

    def __str__(self):

        return self._name


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

        #Get element constraint structure/topology:
        element = Element(elementsInStr(self.constraint,removeQuotes=False)[0])
        #Checks for new input
        if len(massArray) != len(element.branches):
            logger.error("Mass array definition %s is not consistent with the txname constraint %s"
                         %(str(massArray),str(element)))
            sys.exit()
        for ibr,br in enumerate(element.branches):
            if str(br) == '[*]':  #Ignore wildcard branches
                continue
            if len(massArray[ibr]) != br.vertnumb+1:
                logger.error("Mass array definition (%d-dim) is not consistent with the txname constraint (%d-dim)" % ( len(massArray[ibr]), br.vertnumb+1 ))
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
                    logger.error('%s source not defined for plane %s' %(dataType,plane))
                    sys.exit()
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
                for i in infoList:
                    if i not in [ None, "None" ]:
                        myInfoList.append ( i )
                        continue
                    if not hasNone: ## only one None
                        myInfoList.append ( i )
                        hasNone=True
                infoStr = ";".join(myInfoList) ## old version
                setattr(self,infoAttr,infoStr)

        if not hasattr(self,'validated'):
            self.validated = 'TBD'

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
        if nvars < 1 or nvars > 3:
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
                logger.error("Number of free parameters in data and in axes do not match")
                sys.exit()

            #ptDic is of the form: {x : float, y : float, value-key : float}
            #where value-key is any key identifying the (upper limit,efficiency,..) value
            #Restrict the pt dictionary to only the variable values:
            xDict = dict([[str(xv),v] for xv,v in ptDict.items() if xv in plane.xvars])
            #Get the (upper limit, efficiency,..) value:
            value = [v for xv,v in ptDict.items() if  not xv in plane.xvars][0]
            massArray = plane.getParticleMasses(**xDict)

            for br in massArray:
                for m in br:
            #Check if the massArray is positive and value is positive:
                    if (type(m) == float and m<0.) or type(m) == tuple and m[0]<0.:
                        logger.warning("Negative mass value found for %s. Point %s will be ignored." %(self,massArray))
                        continue
                    if type(m) == tuple and m[1]<0.:
                        logger.warning("Negative lifetime found for %s. Point %s will be ignored." %(self,massArray))
                        continue
            if value < 0.:
                logger.warning("Negative value for %s found. Point %s will be ignored." %(self,str(massArray)))
                continue
            #Check if mass array is consistent with the mass constraints given by the
            #txname constraint. If not, skip this mass.
            if not self.checkMassConstraints(massArray):
                continue
            #Add units
            if hasattr(dataHandler, 'unit') and dataHandler.unit:
                value = value*eval(dataHandler.unit,
                                   {'fb':fb,'pb': pb,'GeV': GeV,'TeV': TeV})
            if hasattr(dataHandler, 'massUnit') and dataHandler.massUnit:
                for i,br in enumerate(massArray):
                    if isinstance(br,str):  #Allow for string identifiers in the mass array
                        continue
                    for j,m in enumerate(br):
                        if isinstance(m,tuple):
                            m0 = m[0]*eval(dataHandler.massUnit,{'GeV': GeV,'TeV': TeV})
                            logger.error ( "FIXME whats the units we are using for lifetime?" )
                            m1 = m[1]*eval(dataHandler.massUnit,{'GeV': GeV,'TeV': TeV})
                            m = ( m0, m1 )
                        if isinstance(m,(float,int)):
                            m = m*eval(dataHandler.massUnit,{'GeV': GeV,'TeV': TeV})
                        massArray[i][j] = m
            dataList.append([massArray, value])

        if not dataList:
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

        #Build mass dictionary for all particles
        massDict = {'Z': 86., 'W+': 76.,'W-' : 76.,'t': 169.,
                    't-': 169.,'h': 118., 'higgs': 118., 'ta+' : 1.7, 'ta-' : 1.7}
        #(if they do not appear in masssDict, replace by zero)
        for key in rEven.values():
            if not key in massDict:
                massDict[key] = 0.
        #Set masses for inclusive labels (use lowest mass)
        for key,ptclist in ptcDic.items():
            if key in massDict:
                continue
            minMass = [massDict[ptc] for ptc in ptclist if ptc in massDict]
            if not minMass:
                minMass = 0.
            else:
                minMass = min(minMass)
            massDict[key] = minMass

        #Replace particles appearing in the vertices by their mass
        self.massConstraints = []
        for el in elementsInStr(self.constraint,removeQuotes=False):
            if isinstance(el,str):
                #use dummy labels to evaluate elements without strings
                dummyLabels = dict([[label,label] for label in rEven.values()])
                dummyLabels.update(dict([[label,label] for label in ptcDic]))
                newDummyLabels = copy.deepcopy ( dummyLabels )
                for key,val in dummyLabels.items():
                    newkey = key.replace('+','_p').replace('-','_m')
                    newDummyLabels[ newkey ] = val
                    massDict[newkey ] = massDict [ key ]
                dummyLabels = copy.deepcopy ( newDummyLabels )
                el = el.replace('+','_p').replace('-','_m')
                el = eval(el,newDummyLabels)
            #Replace particles in element by their masses
            massConstraint = []
            for ibr,br in enumerate(el):
                massConstraint.append([])
                for vertex in br:
                    #print ( "ibr=",ibr, "vertex=",vertex )
                    #print ( "massDict=",massDict )
                    massConstraint[ibr].append([massDict[ptc] for ptc in vertex])
            self.massConstraints.append(massConstraint)

        #Now convert the constraints to inequality expressions:
        for el in self.massConstraints:
            for branch in el:
                for iv,vertex in enumerate(branch):
                    eqStr = "dm >= "
                    massValue = sum(vertex)
                    eqStr += str(massValue)
                    branch[iv] = eqStr

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

        for elMass in self.massConstraints:
            goodMasses = True
            for ib,br in enumerate(elMass):
                for iv,vertex in enumerate(br):
                    m1 = massArray[ib][iv]
                    if type(m1) == tuple:
                        m1 = m1[0]
                    m2 = massArray[ib][iv+1]
                    if type(m2) == tuple:
                        m2 = m2[0]
                    massDiff = m1-m2
                    if massDiff < 0.:
                        self._smallerThanError += 1
                        if self._smallerThanError < 4:
                            logger.error("Parent mass (%.1f) is smaller than daughter mass (%.1f) for %s" % (m1,m2,str(self)))
                        if self._smallerThanError == 4:
                            logger.error("(I quenched a few more error msgs as the one above)" )
                        return False
                    #Evaluate the inequality replacing m by the mass difference:
                    check = eval(vertex,{'dm' : massDiff})
                    if check is False:
                        goodMasses = False
                        break
                    elif not check is True:
                        logger.error("Something went wrong evaluating the mass constraint %s" %vertex)
                        return False
            if goodMasses:
                return True

        return False

