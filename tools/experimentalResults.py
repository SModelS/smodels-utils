 #!/usr/bin/env python

"""
.. module:: experimentalResults
   :synopsis: Holds the experimental result object retrieved from smodels-database\ 
   in order to produce summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""    

import ROOT
import logging, os, types
import prettyDescriptions
import setPath
import sys
import databaseBrowser

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

class ExpResult (object):
    """Contains all result-specific information and objects (e.g. 
    exclusion lines, histograms, ...). Uses the extended result objects to 
    handle different mass assumptions for given topology and analysis.
    """
    
    def __init__ (self, run, expAnalysis, expTopology, smsroot, smspy):
        """Sets all private variables, especially self._extendedResults 
        as list containing all available extended results as objects.
    
        """
        self._expTopo = expTopology
        self._expAna = expAnalysis
        self._smsroot = smsroot
        self._smspy = smspy
        self._topo = expTopology.name
        self._ana = expAnalysis.name
        self._run = run
        logger.info('Creating experimental result object for %s-%s-%s!' \
        %(self._run, self._ana, self._topo))
        self.extendedTopos = self._expAna.extendedTopologies[self._topo]
        self._extendedResults = self._getExtendedResults
        self._extResDefault = self._getExtendedResultsDefault
        self._verbosity = 'error'
    
    @property
    def verbosity(self):
        """Tells the level the logger is set to.
        
        """
        return self._verbosity
        
    @verbosity.setter
    def verbosity(self, level):
        """Set the logger to specified level.
        
        """
        level = self._validateLevel(level)
        self._verbosity = level
        self._setLogLevel(level)
        
    def _validateLevel(self, level):
        """Validates given level for pythons logger module.
        
        """
        if not level.lower() in ['debug', 'info', 'warning', 'error']:
            logger.error('No valid level for verbosity: %s! \n \
            Browser will use default setting!' %level)
            return 'error'
        return level.lower()
            
    def _setLogLevel(self, level = 'error'):
        if level == 'debug':
            logger.setLevel(level=logging.DEBUG)
        if level == 'info':
            logger.setLevel(level=logging.INFO)
        if level == 'warning':
            logger.setLevel(level=logging.WARNING)
        if level == 'error':
            pass
    
    @property
    def name(self):
        return self._ana + '_' + self._topo
    
    @property
    def _getExtendedResults(self):
        """Retrieves a list of all extended results we have for this 
        analysis topology pair.
        
        """
        exRes = [ExtendedResult(extop, self._expAna, self._smsroot, self._smspy)\
        for extop in self.extendedTopos]
        return exRes
        
    @property    
    def _getExtendedResultsDefault(self):
        """Defines the default mass assumptions for this result. 
        If there is just a single result, this will be the default, 
        else the one with mass splitting = 050.
    
        """
        # ### FIX ME: rework default settings and docstring 
        exRes = self._extendedResults
        if len(exRes) == 1:
            logger.debug('There is only one extended Result for %s-%s!' \
            %(self._ana, self._topo))
            return exRes[0]
        logger.debug('There are %s extended results for %s-%s!' \
        %(len(exRes), self._ana, self._topo))
        exRes = [er for er in exRes if er.topoName == self._topo + '050']
        if not exRes:
            logger.warning('FIX ME: there is no default for: %s' %self.extendedTopos)
            return None
        return exRes[0]
    
    @property    
    def expAnalysis(self):
        """Returns the analysis-object linked to this result-object.
        
        """
        return self._expAna
    
    @property    
    def expTopology(self):
        """Returns the topology-object linked to this result-object.
        
        """
        return self._expTopo
    
    @property    
    def extendedTopologyNames(self):
        """Returns the topology-object linked to this result-object.
        
        """
        return self.extendedTopos
    
    @property    
    def hasupperLimitDict(self):
        """Checks if there is any upper limit dictionary for this result.
        
        """
        if self.upperLimitDicts:
            return True
        return False
        
    @property
    def upperLimitDicts(self):
        """Retrieves all the upper limit dictionaries available for this result.
        
        """ 
        ulDicts = {}
        for exTopo in self.extendedTopos:
            ulDicts[exTopo] = [exRes.upperLimitDict for exRes in self._extendedResults]
        return ulDicts
        
    def upperLimitDict(self, extendedTopoName = 'default'):
        """Retrieves the upper limit dictionary (out of all upper limit 
        dictionaries available for this topology). If no extended topology name is 
        given, the default mass assumptions will be used.
        
        """
        
        if extendedTopoName == 'default':
            logger.debug('Using default for mass proportions!')
            extRes = self._extResDefault
            if not extRes:
                logger.error('Could not retrieve upper limit dictionary!\n \
                Check if there is a proper default for %s!' %self.extendedTopos)
                return None
            return extRes.upperLimitDict
        if not extendedTopoName in self.extendedTopologies:
            logger.error('No valid extended topology %s! Possibilities are %s: '\
            %(extendedTopoName, self.extendedTopologies))
            return None
        extendedResults = [exRes for exRes in self._extendedResults if \
        extendedTopoName == exRes.topoName]
        return extendedResults[0].upperLimitDict
        
    @property    
    def isChecked(self):
        """Is this result checked?
        
        """
        if self.checked: return True
        return False
    
    @property    
    def checked(self):
        """Retrieves checked_by entry from info.txt.
        
        """
        infoLine = self._expAna.checked
        logger.debug('Got infoLine from Analysis-object: %s.' %infoLine)
        if not infoLine: return None
        # ### FIX ME: the IF below will be obsolet when 
        #the checked flag is fixed in every info.txt
        if len(infoLine.split()) == 1: 
            logger.warning('There is no information about single topologies.')
            return infoLine[0]
        
        infoLine = infoLine.split(',')
        logger.debug('First preprocessed infoLine: %s.' %infoLine)
        infoLine = [c.split(':')[1].strip() for c in infoLine if \
        c.split(':')[0].strip() == self._topo]
        logger.debug('Second preprocessed infoLine: %s.' %infoLine)
        if not infoLine:
            logger.warning('This Result is not checked!')
            return None
        logger.debug('Return value of infoLine: %s.' %infoLine[0])
        return infoLine[0].strip()
    
    @property
    def condition(self):
        """Retrieves the condition for this result.
        
        """
        cond = []
        if not self._expAna.hasConditions:
            logger.warning('No conditions available for analysis %s.' \
            %self._ana)
            return None
        cond = [c.split('->')[1].strip() for c in self._expAna.conditions \
        if c.split('->')[0].strip() == self._topo]
        if not cond:
            logger.warning('No condition available for result %s.' \
            %self.name)
            return cond
        return cond[0]
     
    @property
    def constraint(self):
        """Retrieves the constraint for this result.
        
        """
        cons = []
        if not self._expAna.hasConstraints:
            logger.warning('No constraints available for analysis %s.' \
            %self._ana)
            return None
        cons = [c.split('->')[1].strip() for c in self._expAna.constraints \
        if c.split('->')[0].strip() == self._topo]
        if not cons:
            logger.warning('No constraints available for result %s.' \
            %self.name)
            return cond
        return cons[0]
        
    @property
    def axes(self):
        """Retrieves the axes information for this result.
        :return: {extended topology: 
        {'mx': mass on x-axis, 'my': mass on y-axes, 
        'mz': condition for intermediate mass}}
        
        """
        axdict = {}
        if not self._expAna.hasAxes:
            logger.warning('No axes information available for analysis %s.' \
            %self._ana)
            return None
        ax = [ a.strip() for a in self._expAna.axes if self._topo in a]
        ax = ax[0].replace('%s:' %self._topo, '')
        logger.debug('1) Axes information: %s.' %ax)
        if len(self.extendedTopos) == 1:
            axdict[self._topo] = {}
            logger.debug('2) Axes information: %s.' %ax.split())
            axdict[self._topo]['mx'] = ax.split()[0].strip()
            axdict[self._topo]['my'] = ax.split()[1].strip()
            try:
                axdict[self._topo]['mz'] = ax.split()[2].strip()
            except IndexError:
                logger.info('No intermediate mass mz.')
                axdict[self._topo]['mz'] = None
            try:
                logger.warning('There is a second condition for the masses: %s!'\
                %ax.split()[3].strip())
            except IndexError: pass
        else:
            logger.warning('There are %s extended topologies!'\
            %len(self.extendedTopos))
            ax = ax.split('-')
            logger.debug('3) Axes information: %s.' %ax)
            for et in self.extendedTopos:
                axdict[et] = {}
                extention = et.replace(self._topo, '')
                if not 'D' in extention:
                    for a in ax:
                        logger.debug('4) Axes information: %s.' %a)
                        if a.split()[2].strip() == extention:
                            axdict[et]['mx'] = a.split()[0].strip()
                            axdict[et]['my'] = a.split()[1].strip()
                            axdict[et]['mz'] = a.split()[2].strip()
                else:
                    for a in ax:
                        logger.debug('4) Axes information: %s.' %a)
                        if extention.strip('D') == a.split()[2].split('=')[-1].strip():
                            axdict[et]['mx'] = a.split()[0].strip()
                            axdict[et]['my'] = a.split()[1].strip()
                            axdict[et]['mz'] = a.split()[2].strip()
               
        return axdict
        
    @property
    def extendedResults(self):
        """Returns a list containing all available extended 
        results as objects.
        
        """
        return self._extendedResults
     
    # ### FIX ME: rework exclusions and exclusionLines to not get one type for all mass splittings but all types for one mass splitting!!! 
    
    @property
    def exclusionLines(self):
        """Returns all exclusion lines available for this result 
        as ROOT TGraphs. 
        
        """
        contours = {}
        for exRes in self._extendedResults:
            contours[exRes.name] = exRes.exclusionLines
        return contours
    
    @property
    def exclusions(self):
        """Returns all exclusion values available for this result.
        
        """
        values = {}
        for exRes in self._extendedResults:
            values[exRes.name] = exRes.exclusions
        return values
        
    def typeOfExclusionLines(self,expected = False, sigma = 0):
        """Returns a list containing the exclusion lines for all mass 
        assumptions available for this result as ROOT TGraphs. 
        If expected is set to False, the observed exclusion lines will 
        be returned, else the expected ones. 
        Possible values for keyword argument "sigma" are: -1,0,1.
        
        """
        return [exRes.exclusionLine(expected, sigma) for exRes in \
        self._extendedResults]
        
    def typeOfExclusions(self,expected = False, typ = 'xmax'):
        """Returns a list containing all exclusion values for all mass 
        assumptions available for this result. If expected is set to False, 
        the observed values will be returned, else the expected ones. 
        Possible values for keyword argument "typ" are: "minx", "xmin", "xmax".
        
        """
        return [exRes.exclusion(expected, typ) for exRes in \
        self._extendedResults]
        
    def exclusionLine(self, extendedTopoName = 'default', expected = False, \
    sigma = 0):
        """Retrieves one specified exclusion line (out of all exclusion lines  
        available for this topology) as ROOT TGraph. If no extended 
        topology name is given, the default mass assumptions will be used. 
        If expected is set to False, the observed exclusion line will be 
        returned, else the expected one. Possible values for keyword argument 
        "sigma" are: -1, 0, 1.
        
        """
        
        return self._getSingleAttribute(extendedTopoName, expected, \
        sigma, 'exclusionLine')
        
    def exclusion(self, extendedTopoName = 'default', expected = False, typ = 'xmax'):
        """Retrieves one specified exclusion value (out of all exclusion   
        values available for this topology). If no extended topology name is 
        given, the default mass assumptions will be used. 
        If expected is set to False, the observed exclusion value will be 
        returned, else the expected one. Possible values for keyword argument 
        "typ" are: "limit", "min", "max".
        
        """
        
        return self._getSingleAttribute(extendedTopoName, expected, typ, \
        'exclusion')
        
    def _getSingleAttribute(self, extendedTopoName, expected, argument, \
    attribute):
        """Private method used by the methods 'exclusionLine' and 'exclusion'.
        Retrieves either an exclusion line or an exclusion value.
        
        """
        if extendedTopoName == 'default':
            logger.debug('Using default for mass proportions!')
            extRes = self._extResDefault
            if not extRes:
                logger.error('Could not retrieve exclusion line! \n \
                Check if there is a proper default for %s!' %self.extendedTopos)
                return None
            return getattr(extRes, attribute)(expected, argument)
        if not extendedTopoName in self.extendedTopologies:
            logger.error('No valid extended topology %s! Possibilities are %s: '\
            %(extendedTopoName, self.extendedTopologies))
            return None
        extendedResults = [exRes for exRes in self._extendedResults if \
        extendedTopoName == exRes.topoName]
        return getattr(extendedResults[0], attribute)(expected, argument)
    
    
        
    def selectExclusionLine(self, expected = False, sigma = 0, \
    condition = 'xvalue', value = '050'):
        """Selects one type of exclusion line (out of all exclusion lines 
        for this topology) corresponding to a specified case of mass proportions.
        :param expected: switch between the observed (False) or the 
        expected (True) exclusion lines
        :param sigma: Takes -1, 0 or 1 corresponding to minus one sigma, 
        no sigma or plus one sigma exclusion lines
        :param condition: Takes the condition for the masses as string
        (e.g. 'xvalue', 'LSP', 'D(M1/M2)=', ...)
        :param value: Takes the value for the mass condition as string
        (e.g. '050', '100', ...)
        
        """
        
        if condition == 'xvalue':
            exTopName = self._topoName + value
        elif condition in ['LSP' ,'x' ,'C' ,'M'] or 'D' in condition:
            exTopName = self._topoName + condition + value
        else:
            logger.error('Unknown condition %s!' %condition)
            
        return self.exclusionLine(extendedTopoName = exTopName, \
        expected = expected, sigma = sigma)

class ExtendedResult(object):
    """Contains all specific informations linked to one extended result,
    where an extended result denotes a pair of analysis and topology
    when a specified case of mass proportions is assumed (e.g. x-value = 050, 
    mass of LSP = 50 GeV, ...).
    
    """
    
    def __init__(self, extendedTopologyName, expAnalysis, smsroot, smspy):
        """Sets all private variables and initiates the dictionaries for 
        exclusion lines and exclusions.
        
        """
        self._topoName = extendedTopologyName
        self._expAna = expAnalysis
        self._ana = expAnalysis.name
        self._run = expAnalysis.run
        self._smsroot = smsroot
        self._smspy = smspy
        
    @property
    def name(self):
        """Returns the name of this experimental result as concatenated string.
        
        """
        return self._ana + '-' + self._topoName
     
    @property
    def topoName(self):
        """Returns the name of the extended topology e.g.: 'TChiChipmSlepL050'.

        """
        return self._topoName

    def exclusionLine(self, expected = False, sigma = 0):
        """Retrieves one specified exclusion line (out of all exclusion lines  
        available for this topology) as ROOT TGraph. If expected is set 
        to False, the observed exclusion line will be returned, else the 
        expected one. Possible values for keyword argument "sigma" are: -1, 0, 1.
        
        """
        
        sigmaDict = self.exclusionLines['observed']
        if expected: sigmaDict = self.exclusionLines['expected']
        return sigmaDict[sigma]
        
    def exclusion(self, expected = False, typ = 'xmax'):
        """Retrieves one specified exclusion value (out of all exclusion   
        values available for this topology). If expected is set to False, the 
        observed value will be returned, else the expected one. 
        Possible values for keyword argument "typ" are: "minx", "xmin", "xmax".
        
        """

        typDict = self.exclusions['observed']
        if expected: typDict = self.exclusions['expected']
        if typ in typDict:
            return typDict[typ]
        logger.warning('There is no exclusion of type %s (expected = %s).'\
        %(typ, expected))
        return None
        
    @property    
    def exclusionLines(self):
        """Retrieves the exclusion lines from the sms.root file linked to the 
        corresponding analysis and builds a nested dictionary including all 
        the exclusion lines: 
        {'observed': {1: TGraph, 0: TGraph, -1: TGraph}, 
        'expected': {1: TGraph, 0: TGraph, -1: TGraph}}
        
        """

        rootFile = ROOT.TFile(self._smsroot)
        exclusionLines = {'observed': 'exclusion', 'expected':\
        'expectedexclusion'}
        for key, value in exclusionLines.items(): 
            sigmaDict = {1: 'p1', 0: '', -1: 'm1'}
            for sigmaKey, sigmaValue in sigmaDict.items():
                sigmaDict[sigmaKey] = rootFile.Get(value + sigmaValue + '_' + \
                self._topoName)
            exclusionLines[key] = sigmaDict
        logger.debug('Built dictionary for exclusion lines for %s-%s-%s: %s.'\
        %(self._run, self._ana, self._topoName, exclusionLines))     
        return exclusionLines
        
    @property
    def exclusions(self):
        """Retrieves the exclusion values for this result from the experimental  
        analysis object and builds a nested dictionary including all the 
        exclusion values of form:
        {'observed': {'minx': value, 'xmin':value, 'xmax': value}, 
        'expected': {'minx': value, 'xmin': value, 'xmax': value}}
        
        """
        
        excl = self._expAna.exclusions
        excl = [e for e in excl if self._topoName in e]
        logger.debug('Found exclusions for %s-%s-%s: %s.'\
        %(self._run, self._ana, self._topoName, excl))
        exclDict = {'observed': 'exclusions', 'expected': 'expectedexclusions'}
        typDict = {}
        for key, value in exclDict.items():
            for line in excl:
                if value in line:
                    line = line.split()
                    try:
                        typDict = {'minx': line[2].strip(), \
                        'xmin': line[3].strip(), 'xmax': line[4].strip()}
                    except IndexError:
                        logger.warning('Incorrect number (%s) of exclusion \n \
                        values for %s-%s-%s-%s!' %(len(line), self._run, self._ana, \
                        self._topoName, value))
                        typDict = {'xmin': line[2].strip(), \
                        'xmax': line[3].strip()}
            exclDict[key] = typDict
        logger.debug('Built dictionary for exclusion values for %s-%s-%s: %s.'\
        %(self._run, self._ana, self._topoName, exclDict))    
        return exclDict
        
    @property
    def upperLimitDict(self):
        localSms = {}
        if self._smspy:
            execfile(self._smspy, localSms)
        if 'Dict' in localSms and self._topoName in localSms['Dict']:
            return localSms['Dict'][self._topoName]
        logger.warning('No upper limit dictionary was found for extended \n \
        result %s!' %self.name)