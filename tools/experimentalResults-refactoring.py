 #!/usr/bin/env python

"""
.. module:: experimentalResults
   :synopsis: Holds the experimental result object retrieved from smodels-database 
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

# ### FIX ME:

# various names for same variables!
# ordering of functions is confusing
# code duplicates


class ExpResultSet (object):
    """Contains all result-specific information and objects (e.g. 
    exclusion lines, histograms, ...). Encapsules the result objects to 
    handle different mass assumptions for given topology and analysis.
    
    """
    
    def __init__ (self, run, expAnalysis, expTopology, smsroot, smspy):
        """Sets all private variables, especially self._results 
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
        self._results = self._getResults
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
        
    def __str__(self):
        ret = "%s" %self.name
        return ret
        
    @property
    def name(self):
        return self._ana + '_' + self._topo
        
        
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
    def topologySet(self):
        """Returns all the extended topologies linked to this result set.
        
        """
        return self.extendedTopos
        
    @property
    def results(self):
        """Returns a list containing all available result objects.
        
        """
        return self._results    

    @property
    def _getResults(self):
        """Retrieves a list of all extended results we have for this 
        analysis topology pair.
        
        """
        res = [Results(extop, self._expAna, self._smsroot, self._smspy)\
        for extop in self.extendedTopos]
        return res
        
  
    def _getExtendedTopology(self, condition = condition, value = value):
        """Creates the name of the extended topology (e.g. 'T6ttWWLSP050')
        :param condition: condition for the third mass as string (e.g. 'xvalue')
        :param value: value for the condition as string (e.g. '025')
        
        """
        if not condition or not value:
            return self._getDefaultExtendedTopology(condition = condition, value = value)
        elif condition == 'xvalue':
            extTopo = self._topo + value
        elif condition in ['LSP' ,'x' ,'C' ,'M'] or 'D' in condition:
            extTopo = self._topo + condition + value
        else:
            logger.error('Unknown condition %s!' %condition)
            return None
        return extTopo
    
    def _getDefaultExtendedTopology(self, condition = condition, value = value)
    """Retrieves the default settings for this set of results.
    
    """
    # ### FIX ME: do this! xvalue -> 050, LSP -> ? etc.
    
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
    
    def hasUpperLimitDict(self, expected = False):
        """Checks if there is any observed/expected upper limit dictionary 
        for this result set.
        
        """
        if not expected:
            if self.upperLimitDicts():
                return True
            return False
        if expected:
            if self.upperLimitDicts(expected = True):
                return True
            return False
        
    def upperLimitDicts(self, expected = False):
        """Retrieves all the observed/expected upper limit dictionaries 
        available for this result set.
        
        """ 
        ulDicts = {}
        for extTopo in self.extendedTopos:
            ulDicts[extTopo] = [res.upperLimitDict(expected) \
            for res in self._results]
        return ulDicts
        
    def upperLimitDict(self, expected = False, condition = None, value = None):
        """Retrieves one observed/expected upper limit dictionary (out of all 
        upper limit dictionaries available for this topology). 
        If condition and value are None, the default mass assumptions will be used.
        
        """
        
        extTopo = self._getExtendedTopologyName(condition = condition, value = value)
        if expected:
            if not extTopo in self.expectedUpperLimitDicts(expected = expected):
                logger.error('No expected upper limit dictionary could be found\
                for %s!' %extTopo)
                return None
            logger.error('No upper limit dictionary could be found for %s!' \
            %extTopo)
            return None
        return self.upperLimitDicts(expected = expected)[extTopo]
        
    def exclusionLines(self, expected = False):
        """Returns all observed/expected exclusion lines available for this 
        result set as ROOT TGraphs. 
        
        """
        contours = {}
        for res in self._results:
            contours[res.name] = res.exclusionLines(expected)
        return contours
        
    
    def exclusionLine(self, expected = False, sigma = 0, \
    condition = None, value = None):
        """Retrieves one observed/expected exclusion line (out of all 
        exclusion lines available for this topology). 
        If condition and value are None, the default mass assumptions 
        will be used.
         :param expected: False/True gives observed/expected
        :param sigma: -1, 0, 1.
        
        """
        extTopo = self._getExtendedTopologyName(condition = condition, value = value)
        if not extTopo in self.exclusionLines(expected = expected)\
        or not sigma in self.exclusionLines(expected = expected)[extTopo]: 
            if expected:
                logger.error('No expected exclusion lines could be found for %s!' \
                %extTopo)
                return None
            logger.error('No exclusion lines could be found for %s!' \
            %extTopo)
            return None
        return self.exclusionLines(expected = expected)[extTopo][sigma]
    

    def exclusions(self, expected = False):
        """Returns all observed/expected exclusion values available for this result.
        
        """
        
        exclusions = {}
        for res in self._results:
            exclusions[res.name] = res.exclusions(expected)
        return exclusions
        
    def exclusion(self, expected = False, typ = 'xmax', condition = None, value = None):
        """Retrieves one observed/expected exclusion line (out of all 
        exclusion lines available for this topology). 
        If condition and value are None, the default mass assumptions 
        will be used.
         :param expected: False/True gives observed/expected
        :param typ: "limit", "min", "max"
        
        """
        
        extTopo = self._getExtendedTopologyName(condition = condition, value = value)
        if not extTopo in self.exclusionLines(expected = expected)\
        or not typ in self.exclusionLines(expected = expected)[extTopo]:
            if expected:
                logger.error('No expected exclusions could be found for %s!' \
                %extTopo)
                return None
            logger.error('No exclusions could be found for %s!' \
            %extTopo)
            return None
        return self.exclusions(expected = expected)[extTopo][typ]
        


class Results(object):
    """Contains all specific informations linked to one result,
    where a result denotes a pair of analysis and topology with a specific
    assumption for the third mass (e.g. x-value = 050, mass of LSP = 50 GeV, ...).
    
    """
    
    def __init__(self, extendedTopology, expAnalysis, expTopology, smsroot, smspy):
        """Sets all private variables and initiates the dictionaries for 
        exclusion lines and exclusions.
        
        """
        self._extTopo = extendedTopology
        self._expAna = expAnalysis
        self._expTopo = expTopology
        self._ana = expAnalysis.name
        self._run = expAnalysis.run
        self._smsroot = smsroot
        self._smspy = smspy
    
    def __str__(self):
        ret = "%s" %self.name
        return ret
        
    @property
    def name(self):
        """Returns the name of this experimental result as concatenated string.
        
        """
        return self._ana + '-' + self._extTopo
    @property
    def experimentalAnalysis(self):
        """Retrieves the experimental analysis object.
        """
        return self._expAna
    
    @property
    def experimentalTopology(self):
        """Retrieves the experimental topology object.
        """
        return self._expTopo
        
    @property    
    def allExclusionLines(self):
        """Retrieves the exclusion lines from the sms.root file linked to the 
        corresponding analysis and builds a nested dictionary including all 
        the exclusion lines. 
        :return: {'observed': {1: TGraph, 0: TGraph, -1: TGraph}, 
        'expected': {1: TGraph, 0: TGraph, -1: TGraph}}
        
        """

        rootFile = ROOT.TFile(self._smsroot)
        exclusionLines = {'observed': 'exclusion', 'expected':\
        'expectedexclusion'}
        for key, value in exclusionLines.items(): 
            sigmaDict = {1: 'p1', 0: '', -1: 'm1'}
            for sigmaKey, sigmaValue in sigmaDict.items():
                sigmaDict[sigmaKey] = rootFile.Get(value + sigmaValue + '_' + \
                self._extTopo)
                ###FIX ME: work around to handel exclusionlines of the topology TChiWZon: 
                if not sigmaDict[sigmaKey]:
                    if self.topoName[-2:] == 'on':
                        sigmaDict[sigmaKey] = rootFile.Get(value + sigmaValue + '_' + \
                        self._extTopo[:-2])
                    if self.topoName[-3:] == 'off':
                        sigmaDict[sigmaKey] = rootFile.Get(value + sigmaValue + '_' + \
                        self._extTopo[:-3])
                ###---------------------------------------------------------------------
            exclusionLines[key] = sigmaDict
        logger.debug('Built dictionary for exclusion lines for %s-%s-%s: %s.'\
        %(self._run, self._ana, self._extTopo, exclusionLines))     
        return exclusionLines
     
    def exclusionLines(self expected = False):
        """Retrieves the observed/expected exclusion lines for this result 
        as a dictionary.
        :return: {1: TGraph, 0: TGraph, -1: TGraph}
        
        """
        if not expected:
            if self.allExclusionLines['observed']:
                return self.allExclusionLines['observed']
            logger.warning('No observed exclusion lines were found for \n \
            extended result %s!' %self.name)
            return None
        if expected:
            if self.allExclusionLines['expected']:
                return self.allExclusionLines['expected']
            logger.warning('No expected exclusion lines were found for \n \
            extended result %s!' %self.name)
            return None 
    
    def exclusionLines(self, expected = False, sigma = 0):
        """Retrieves one observed/expected exclusion line for this result 
        specified by sigma.
        :param sigm: 1,0,-1
        :return: {1: TGraph, 0: TGraph, -1: TGraph}
        
        """
        if not expected:
            if self.exclusionLines() and sigma in self.exclusionLines():
                return self.exclusionLines[sigma]
            logger.warning('No observed exclusion line with %s was found for \n \
            result %s!' %(sigma, self.name))
            return None
        if expected:
            if self.exclusionLines(expected = True) and sigma \
            in self.exclusionLines(expected = True):
                return self.exclusionLines(expected = True)[sigma]
            logger.warning('No expected exclusion line with %s was found for \n \
            result %s!' %(sigma, self.name))
            return None 
    
    @property
    def allExclusions(self):
        """Retrieves the exclusion values for this result from the experimental  
        analysis object and builds a nested dictionary including all the 
        exclusion values.
        :return: {'observed': {'minx': value, 'xmin':value, 'xmax': value}, 
        'expected': {'minx': value, 'xmin': value, 'xmax': value}}
        
        """
        
        excl = self._expAna.exclusions
        excl = [e for e in excl if self._extTopo in e]
        logger.debug('Found exclusions for %s-%s-%s: %s.'\
        %(self._run, self._ana, self._extTopo, excl))
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
                        self._extTopo, value))
                        typDict = {'xmin': line[2].strip(), \
                        'xmax': line[3].strip()}
            exclDict[key] = typDict
        logger.debug('Built dictionary for exclusion values for %s-%s-%s: %s.'\
        %(self._run, self._ana, self._extTopo, exclDict))    
        return exclDict
        
    def exclusions(self, expected = False):
        """Retrieves the observed/expected exclusion values for this result 
        as a dictionary.
        :return: {'minx': value, 'xmin':value, 'xmax': value}
        
        """
        if not expected:
            if self.allExclusions['observed']:
                return self.allExclusions['observed']
            logger.warning('No observed exclusion values were found for \n \
            result %s!' %self.name)
            return None
        if expected:
            if self.allExclusions['expected']:
                return self.allExclusions['expected']
            logger.warning('No expected exclusion values were found for \n \
            result %s!' %self.name)
            return None
        
    def exclusion(self, expected = False, typ = 'xmax'):
        """Retrieves the observed/expected exclusion value for this result 
        specified by typ.
        :param typ: 'minx', 'xmin', 'xmax'
        :return: {'minx': value, 'xmin':value, 'xmax': value}
        
        """
        if not expected:
            if self.exclusions() and typ in sel.exclusions():
                return self.exclusions()[typ]
            logger.warning('No observed exclusion value with %s was found for \n \
            result %s!' %(typ,self.name))
            return None
        if expected:
            if self.exclusions(expected = True) and typ \
            in self.exclusions(expected = True):
                return self.exclusions(expected = True)[typ]
            logger.warning('No expected exclusion value with %s was found for \n \
            result %s!' %(typ, self.name))
            return None
            
    def upperLimitDict(self, expected = False):
        """Retrieves the observed/expected cross section upper limit dictionary for this 
        result from the sms.py file located in the database.
        
        """
        localSms = {}
        fakeDicts = [[None], [None, None], [None, None, None]]
        if self._smspy:
            execfile(self._smspy, localSms)
        else:
            return None
        if not expected:
            if 'Dict' in localSms and self._extTopo in localSms['Dict']:
                if localSms['Dict'][self._extTopo] in fakeDicts:
                    logger.warning('No useful upper limit dictionary was found \n \
                    for extended result %s!' %self.name)
                    return None
                return localSms['Dict'][self._extTopo]
            logger.warning('No upper limit dictionary was found for extended \n \
            result %s!' %self.name)
            return None
        if expected:
            if 'ExpectedDict' in localSms and self._extTopo in \
            localSms['ExpectedDict']:
                if localSms['ExpectedDict'][self._extTopo] in fakeDicts:
                    logger.warning('No useful expected upper limit dictionary  \n \
                    was found for extended result %s!' %self.name)
                    return None
                return localSms['ExpectedDict'][self._extTopo]    
            logger.warning('No expected upper limit dictionary was found  \n \
            for extended result %s!' %self.name)  
            return None
 