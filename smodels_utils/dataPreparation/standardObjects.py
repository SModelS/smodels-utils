#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds objects used by convert.py to create info.txt, sms.root, sms.py and newSms.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   

import sys, logging, os, ROOT
from copy import deepcopy
import inputObjects 
from datetime import date


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

class StandardDataInfo(object):
    """ the dataInfo.txt file content """
    def __init__(self):
        
        self.infoAttr = [ 'datatype', 'dataid' ]
        self._datatype = None
        self.name = 'dataInfo'
        
    @property
    def datatype(self):
        
        """
        :returns: datatype as string
        """
        
        return self._datatype
    
    @datatype.setter
    def datatype(self, datatype):
        
        """
        Checks and sets datatype
        :raise datatypeError: if a datatype diferent
        from the allrady existing one is given
        """
        if not self._datatype:
            self._datatype = datatype
            return
        if self._datatype != datatype:
            Errors().datatype()
        
    def checkMassPlane(self, massPlaneObj):
        
        """
        checks the settings for origLimits and origEfficiencyMap
        for given massplane. 
        sets property datatype
        stes attribute dataid to None (only for upper-limit)
        :param massPlaneObj: inputObjects.MassPlane-objectFormat
        """
        
        limits = False
        for limit in massPlaneObj.origLimits:
            if limit:
                self.datatype = 'upper-limit'
                self.dataid = None
                break
        if massPlaneObj.origEfficiencyMap:
            self.datatype = 'efficiency-map'
        print self.datatype
            

        
class VertexChecker(object):
    
    """
    This class is designed to compute the off-shell
    vertices for a given mass array
    The on-shell constraints of txName are used to define 
    the SM-particles occurring in every vertex.
    The differences of the masses of the SUSY-particles related
    to one vertex are compared with the mass sum of the SM-particles
    in this vertex
    """

    def __init__(self, txNameObj):
        
        """
        :param txNameObj: inputObjects.TxNameInput-object
        """
        
        self.txName = txNameObj.name
        self.kinConstraints = self._getKinConstraints(txNameObj)
        
        
    def getOffShellVertices(self, massArray):
        
        """
        compute the mass-difference between two adjacent
        masses in the mass array. Compare those mass differences
        with the masses held by self.kinConstraint. If the mass 
        difference is smaller then the assigned kinConstraint-mass
        the vertex is added to the list of off-shell vertices
        
        :param massArray: list containing two other lists. Each list contains 
        floats, representing the masses of the particles of each branch in GeV
        :raise decayChainError: if length of mass array not equal length of kinConstraint
        :return: list of off-shell vertices, each vertex is represented by a tuple 
        that contains two integers. The first one of those integers give the branch
        of the vertex and the second one the position of the vertex in the branch
        The count starts with 0. eg: (0,1) --> second vertex in first branch
        """

        offShellVertices = []
        massDeltaArray = [[],[]]
        for i, branch in enumerate(massArray):
            for j, mass in enumerate(branch):
                if j == 0: continue
                massDelta =branch[j-1] - mass
                massDeltaArray[i].append(massDelta)
                
        for kinConstraint in self.kinConstraints:
            for i, branch in enumerate(kinConstraint):
                # print "branch=",branch,"massDeltaArray=",massDeltaArray
                if len(branch) != len(massDeltaArray[i]):
                    Errors().decayChain(self.txName,\
                    len(branch),len(massDeltaArray[i]))
                for j, massDelta in enumerate(branch):
                    if massDeltaArray[i][j] <= massDelta:
                        if not (i,j) in offShellVertices:
                            offShellVertices.append((i,j))
        return offShellVertices
        
    def _getKinConstraints(self, txNameObj):
        
        """
        takes the on-shell constraint of a given txName,
        replace the SM-particles occurring in one Vertex 
        by the sum of their masses. 
        The masses of 'Z', 'W', 't' and 'h' are set 
        to: paricleMass - 2*decaywith
        The masses of all other SM-particles are set to 0
        
        :param txName: inputObjects.TxNameInput-object
        :raise missingOnConstraintError: if TxNameInput-object
        have no-shell constraint
        :raise constraintError: if on-shell constraint can not
        be interpreted as a list in the required format
        :return: list of lists, each list holds the mass-sum
        of the SM-particles for every vertex.
        or None if on-shell constraint set to:'not yet assigned'
        
        """
        
        massDict = {'Z': 86., 'W': 76.,'t': 169.,'h': 118}
        startString = '[[['
        endString = ']]]'
        kinConstraints = []
        if not hasattr(txNameObj.on, 'constraint'):
            Errors().missingOnConstraint(txNameObj.name)
        constraint = txNameObj.on.constraint
        
        if constraint == 'not yet assigned': return None
        if not isinstance(constraint, str):
            Errors().constraint(self.txName, constraint)
        if not endString in constraint or not startString in constraint:
            Errors().constraint(self.txName, constraint)
        for i in range(len(constraint)):
            if constraint[i:i + len(startString)] == startString:
                start = i
            if constraint[i:i + len(endString)] == endString:
                end = i + len(endString)
                kinConstraints.append(constraint[start:end])
        try:
            kinConstraints = \
            [eval(constraint) for constraint in kinConstraints]
        except:
            Errors().constraint(self.txName, constraint)
        for i, constraint in enumerate(kinConstraints):
            for j, branch  in enumerate(constraint):
                for k, vertex in enumerate(branch):
                    massSum = 0.
                    for particle in vertex:
                        particle = particle.replace('+','')
                        particle = particle.replace('-','')
                        if particle in massDict:
                            massSum = massSum + massDict[particle]
                    kinConstraints[i][j][k] = massSum
        return kinConstraints
        
    def __nonzero__(self):
        
        return bool(self.kinConstraints)
        
        
class StandardDataList(list):
    
    """
    list-object, 
    holds lists, each list consists of 2 entrys: [massArry, value]
    The MassArray holds the masses of the SUSY-particles for each branch
    The masses are represented by a string incl. unit of mass
    eg: [['5.0*GeV, '10.0*GeV'],[['5.0*GeV, '10.0*GeV']]
    The value is a string assigned to this  massArray. 
    example for upper limits: '0.578*pb'
    """
    
    def __init__(self, massUnit = '*GeV', valueUnit = '*pb'):
        
        """
        :param massUnit: unit of the mass array
        :param valueUnit; unit of the value
        """
        
        self.massUnit = massUnit
        self.valueUnit = valueUnit
        
    
    def append(self, massArray, value):
        
        """
        append StandardDataList with [massArray, value]
        if there is no entry with the same massArray
        allready in StandardDataList
        
        :raise valueDifferenceWarning: If there are two entries 
        with same massArray but different values
        """
       
        
        self._checkMasses(massArray)
        array = [[],[]]
        for i in range(len(massArray)):
            array[i] = ['%s%s' %(mass, self.massUnit) for mass in massArray[i]]
        inList = False
        for point in self:
            if array ==  point[0]:
                oldvalue = float(point[1][:-3])
                if abs(value-oldvalue) > 0.0001:
                    Errors().valueDifference\
                    (array, point[1], '%s%s' %(value,self.valueUnit))
                inList = True
                break
        value = '%s%s' %(value,self.valueUnit)
        if not inList:
            list.append(self, [array, value])
            
    def _checkMasses(self, massArray):
        
        """
        checks the given mass array
        
        :raise negativMassError: If one of the masses is negative
        :raise massOrderError: if the mass of one particle is bigger
        then the mass of the previous one
        """
        
        for array in massArray:
            for i, mass in enumerate(array):
                if mass < 0.0: Errors().negativMass(massArray)
                if i > 0: 
                    if mass > previousMass: Errors().massOrder(massArray)
                previousMass = mass
                
    
            
    def __str__(self):
        
        """
        :returns: entries of StandardDataList line by line
        formatted as string readable by eval as a list of
        unum-objects
        """
        
        string = '['
        
        for i, entry in enumerate(self):
            if not (i+1) == len(self):
                string = '%s%s,\n' %(string, entry)
                continue
            string = '%s%s]' %(string, entry)
        return string.replace("'","")
        
     
        
class StandardExclusions(list):
    
    """
    list-objects
    holds all exclusion lines for one txName
    as standardized ROOT.TGraph-objects
    """
    
    def __init__(self, name):
        
        """
        initialize a empty StandardExclusions-object
        :param name: name of related txName
        """
        
        self.name = name
        list.__init__(self)
        
    def addMassPlane(self, massPlaneObj):
        
        """
        takes all original exclusion line data from given
        mass plane. Build the standardized ROOT.TGraph and
        saves those TGraphs in self
        
        :param massPlaneObj: inputObjects.MassPlane-object
        """
        
        for exclusion in massPlaneObj.origExclusions:
            if not exclusion: continue
            stGraph = ROOT.TGraph()
            name = '%s_%s' %(exclusion.name, massPlaneObj.origPlot)
            stGraph.SetName(name)
            stGraph.SetTitle(name)
            for i,point in enumerate(exclusion):
                stGraph.SetPoint(i,point[0],point[1])
            stGraph.SetLineColor ( ROOT.kBlack )
            if 'expected' in exclusion.name:
                stGraph.SetLineColor ( ROOT.kRed )
            stGraph.SetLineStyle(1)
            if 'P1' in exclusion.name or 'M1' in exclusion.name:
                stGraph.SetLineStyle(2)
            self.append(stGraph)
            
class StandardTWiki(object):
    
    """
    Holds all information for the creation of
    twiki.txt 
    The string representation of this class can 
    be used to create a new entry for:
    http://smodels.hephy.at/wiki/DataSource
    """
    
    def __init__(self, metaInfo):
        
        """
        Initialize the object with empty lists
        only the entry for the first column in the twiki 
        table is build
        
        :param metaInfo: inputObjects.MetaInfoInput-object
        """
        
        self.id = self.idFormat(metaInfo)      
        self.txNames = []
        self.axes = []
        self.figures = []
        self.limits = []
        self.exclusions = []
        self.efficiencies = []
        
    def __str__(self):
        
        """
        :return: string holding all informations in a format 
        readable by MoinMoin Wiki. The string can be used 
        as a table entry for:
        http://smodels.hephy.at/wiki/DataSource
        """

        string = '||%s||' %(self.id)
        for attr in \
        [self.txNames, self.axes, self.figures, self.limits,\
        self.efficiencies, self.exclusions]:
            string = string + '<<BR>>'.join(attr) + '||'
        return string + '\n'
    
    def addMassPlane(self, txName, plane):
        
        """
        takes all informations needed for the twiki entry
        from given txName and mass plane.
        Builds standardized entries for the columns of
        the twiki table 
        
        :param txName: name of the related TxName-object
        :param plane: inputObjects.MassPlane-object
        """
            
        self.txNames.append(self.link('smsDictionary#%s' %txName, txName))
        self.axes.append(str(plane.origPlot))
        self.figures.append(self.link(plane.figureUrl, plane.figure))
        self.limits.append(self.objectFormat(plane.origLimits))
        self.exclusions.append(self.objectFormat(plane.origExclusions))
        self.efficiencies.append(self.objectFormat([plane.efficiencyMap]))

    def link(self, url, label):
        
        """
        :param url: url of the link as string
        :param label: label of the link as string
        :return: standardized link for the twiki as string
        """
        
        return '[[%s|%s]]' %(url, label)    
      
    def idFormat(self, metaInfo):
        
        """
        :param metaInfo: inputObjects.MetaInfoInput-object
        :return: standardized string for the first column of the tWiki table
        """
        
        ID = self.link(metaInfo.url, metaInfo.id)
        if hasattr(metaInfo, 'superseded_by'):
            ID = '%s<<BR>>ss_by: %s' %(ID, metaInfo.superseded_by)
        return ID
    
    def objectFormat(self, objectList):
        
        """
        Builds standardized entries for the the following
        columns of the twiki entry:
        -upper limits on production cross sections
        -efficiency maps
        -exclusion lines
        
        :param objectList: list of origDataObjects
        :return: standardized entries for the twiki table
        """
        
        string = ''
        for obj in objectList:
            if not obj.dataUrl: continue
            label = 'OBS'
            if 'efficiency' in obj.name: label = 'EFF'
            if 'expected' in obj.name: label = 'EXP'
            if 'M1' in obj.name: label = '-'
            if 'P1' in obj.name: label = '+'
            string = string + self.link(obj.dataUrl, label)
        if not string: string = 'None'
        return string
      
    
class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def constraint(self, txName, constraint):
        
        m = self._starLine
        m = m + 'In VertexChecker: Error while reading the onshell constraint '
        m = m + 'for txName: %s\n' %txName
        m = m + "constraint have to be of form:\n"
        m = m + "\"[[['particle',...],...]][['particle',...],...]]\"\n"
        m = m + 'got: %s' %constraint
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def decayChain(self, txName, constraintLen, massArrayLen):
        
        m = self._starLine
        m = m + 'In StandardLimits: Error while splitting upperlimits'
        m = m + 'for txName: %s\n' %txName
        m = m + "constraints and topology must have the same"
        m = m + "numbers of vertices\n"
        m = m + 'got:\n'
        m = m + 'vertices in constraint: %s\n' %constraintLen
        m = m + 'vertices in topology: %s' %massArrayLen
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def notAssigned(self, txName):
        
        m = self._starLine
        m = m + "can't split limits for txName: %s because " %txName
        m = m + "constraint is set to 'not yet assigned'\n"
        m = m + "please, set all kinematicRegions propertys of txName"
        m = m + "object to 'False' except of one;\n"
        m = m + "or assign constraints"
        m = m + self._starLine
        print(m)
        sys.exit()
        
        
    def valueDifference(self, massArray, oldValue, value):
        
        m = '------------------------\n'
        m = m + "WARNING: massPoint: %s allrady in \n" %massArray
        m = m + "but differ in value: %s v.s. %s" %(oldValue, value)
        m = m + '\n------------------------'
        print(m)
             
    def kinRegionSetter(self, txName, name, value):
    
        m = self._starLine
        m = m + "in txName %s'\n" %txName
        m = m + "setter for propertsy %s must be of bool type or 'auto'\n"\
        %(name)
        m = m + 'got: %s' %value
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def missingOnConstraint(self, txName):
        
        m = self._starLine#
        m = m + "in txName %s: on.constraint not set\n" %txName
        m = m + "onShell constraint have to be set for automated splitting\n"
        m = m + 'please use: %s.on.constraint =' %txName
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def negativMass(self, massArray):
        
        m = self._starLine#
        m = m + "Error in StandardDataList: there is a negativ Mass:\n"
        m = m + "%s\n" %massArray
        m = m + 'please check your mass plane deffintion at convert.py'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def massOrder(self, massArray):
    
        m = self._starLine#
        m = m + "Error in StandardDataList\n"
        m = m + "there is a particle with higher mass then the privous one in:\n"
        m = m + "%s\n" %massArray
        m = m + 'please check your mass plane deffintion at convert.py'
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def datatype(self):
        
        m = self._starLine#
        m = m + "Error datatype, got efficency Map and upper-limits\n"
        m = m + "one publication can either be an efficienciy analyis\n"
        m = m + "or an upper-limit analysis\n" 
        m = m + 'please only use setSource for either obsUpperLimit/expUpperLimits\n' 
        m = m + 'or for efficiencyMap'
        m = m + self._starLine
        print(m)
        sys.exit()
        
        
