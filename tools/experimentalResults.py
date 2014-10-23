 #!/usr/bin/env python

"""
.. module:: experimentalResults
   :synopsis: Holds the experimental result object retrieved from smodels-database 
   in order to produce summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""    

import logging, os, types
import setPath
import sys
import databaseBrowser
from smodels.tools.physicsUnits import GeV

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)


# ### FIX ME: When there is no intermediate particle in a given topology and one provides "condition" and "value" currently it throws an error in line 782: 
    #if self._expTopo.name + ax['extension'] != self._topo:
    #TypeError: cannot concatenate 'str' and 'NoneType' objects
# this should be turned into a more human readable exception (e.g. MassParametrizationError), a warning should be given and the "extensionless" topology should be used to get e.g. upper limits or exclusion lines!

# ### TO DO: clean up all the logger strings containing line brakes



# add upperlimithistos as root.TH2!


class ExpResultSet (object):
    """Contains all result-specific information and objects (e.g. 
    exclusion lines, histograms, ...). Encapsules the result objects to 
    handle different mass assumptions for given topology and analysis.
    
    """
    
    def __init__ (self, run, expAnalysis, expTopology, smsroot, smspy):
        """Sets all private variables, especially self._results 
        as list containing all available results as objects.
    
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
        self._extTopos = self._expAna.extendedTopologies[self._topo]
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
    
    def __str__(self):
        ret = "Analysis: %s \nTopology: %s" %(str(self._expAna).split('<')[0], self._expTopo)
        return ret
        
    @property
    def name(self):
        return self._ana + '-' + self._topo
        
        
    @property    
    def expAnalysis(self):
        """Returns the analysis object linked to this set of results.
        
        """
        return self._expAna
    
    @property    
    def expTopology(self):
        """Returns the topology object linked to this set of results.
        
        """
        return self._expTopo
        
    @property    
    def isChecked(self):
        """Is this set of results checked?
        
        """
        if self.checked: return True
        return False
    
    @property    
    def checked(self):
        """Retrieves checked_by entry from info.txt.
        
        """
        return self._checked
    
    @property    
    def topologySet(self):
        """Returns all the extended topologies linked to this result set.
        
        """
        return self._extTopos
        
    @property
    def results(self):
        """Returns a dictionary containing all available result objects.
        
        """
        return self._resultDict    
    
    @property
    def resultNames(self):
        """Returns a list containing all available result object names.
        
        """
        return self._resultNames    
    
    
    @property    
    def condition(self):
        """Retrieves the condition for this set of results.
        
        """
        return self._condition
        
    @property    
    def constraint(self):
        """Retrieves constraint for this set of results.
        
        """
        return self._constraint
    
    @property
    def axes(self):
        """Retrieves the axes for this set of results.
        
        """
        return self._axes
        
    @property
    def members(self):
        """Retrieves the members of this set of results.
        :return: {'extended topology': ('condition', value)}
        """
        return self._members
        
    def hasUpperLimitDicts(self, expected = False):
        """Checks which observed/expected upper limit dictionaries there are  
        for this result set.
        
        """
        if self.upperLimitDicts(expected):
            return [key for key in self.upperLimitDicts(expected)]
        return None
        
    def upperLimitDicts(self, expected = False):
        """Retrieves all the observed/expected upper limit dictionaries 
        available for this result set.
        # ### FIX ME: yields list -> for every extTopo 0> compare to exclusions to fix!
        """ 
        ulDicts = {}
        for res in self._results:
            ulDicts[res.name] = res.upperLimitDict(expected)
        return ulDicts
        
    def upperLimitDict(self, expected = False, condition = None, value = None):
        """Retrieves one observed/expected upper limit dictionary (out of all 
        upper limit dictionaries available for this topology). 
        If condition and value are None, the default mass assumptions will be used.
        Condition and value as a tuple specify the result (out of this set) to be taken, e.g. ('fixedLSP', 50), ('massSplitting', 0.25), ...
        :param condition: condition for the third mass 
        :param value: value of the condition as either float or integer
        """
        
        extTopo = self._getExtendedTopology(condition = condition, value = value)
        resultName = self.name.replace(self._topo, extTopo)
        if not resultName in self.upperLimitDicts(expected = expected):
            if expected:
                logger.error('No expected upper limit dictionary could be found\
                for %s!' %extTopo)
                return None
            logger.error('No upper limit dictionary could be found for %s!' \
            %extTopo)
            return None
        return self.upperLimitDicts(expected = expected)[resultName]
    
    @property
    def allExclusionLines(self):
        """Returns all exclusion lines available for this 
        result set as ROOT TGraphs. 
        
        """
        contours = {}
        for res in self._results:
            contours[res.name] = res.allExclusionLines
        return contours
    
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
        Condition and value as a tuple specify the result (out of this set) to be taken, e.g. ('fixedLSP', 50), ('massSplitting', 0.25), ...
        :param condition: condition for the third mass 
        :param value: value of the condition as either float or integer
        :param expected: False/True gives observed/expected
        :param sigma: -1, 0, 1.
        
        """
        extTopo = self._getExtendedTopology(condition = condition, value = value)
        resultName = self.name.replace(self._topo, extTopo)
        if not resultName in self.exclusionLines(expected = expected)\
        or not sigma in self.exclusionLines(expected = expected)[resultName]: 
            if expected:
                logger.error('No expected exclusion lines could be found for %s!' \
                %extTopo)
                return None
            logger.error('No exclusion lines could be found for %s!' \
            %extTopo)
            return None
        return self.exclusionLines(expected = expected)[resultName][sigma]
    
    @property
    def allExclusions(self):
        """Returns all exclusions available for this 
        result set as values. 
        
        """
        values = {}
        for res in self._results:
            values[res.name] = res.allExclusions
        return values
        
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
        Condition and value as a tuple specify the result (out of this set) to be taken, e.g. ('fixedLSP', 50), ('massSplitting', 0.25), ...
        :param condition: condition for the third mass 
        :param value: value of the condition as either float or integer
        :param expected: False/True gives observed/expected
        :param typ: "limit", "min", "max"
        
        """
        
        extTopo = self._getExtendedTopology(condition = condition, value = value)
        resultName = self.name.replace(self._topo, extTopo)
        if not resultName in self.exclusionLines(expected = expected)\
        or not typ in self.exclusionLines(expected = expected)[resultName]:
            if expected:
                logger.error('No expected exclusions could be found for %s!' \
                %extTopo)
                return None
            logger.error('No exclusions could be found for %s!' \
            %extTopo)
            return None
        return self.exclusions(expected = expected)[resultName][typ]
        
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
    def _checked(self):
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
    def _condition(self):
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
    def _constraint(self):
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
    def _getResults(self):
        """Retrieves a list of all extended results we have for this 
        analysis topology pair.
        
        """
        res = [ExpResult(extop, self._expAna, self._expTopo, self._smsroot, \
        self._smspy) for extop in self._extTopos]
        return res
        
    @property
    def _resultDict(self):
        return {r.name: r for r in self._results}
    
    @property
    def _resultNames(self):
        return [r.name for r in self._results]
    
    
    def _getExtendedTopology(self, condition = None, value = None):
        """Creates the name of the extended topology (e.g. 'T6ttWWLSP050')
        :param condition: condition for the third mass as string (e.g. 'massSplitting')
        :param value: value for the condition as string (e.g. 0.25)
        :return: 'extended topology'
        # ### FIX ME whats with the units when matching with given values? give values with units? Add units?
        """
        #print '*****************', condition, value
        if not condition or not value:
            return self._getDefaultExtendedTopology
        else:
            if type(value) == int:
                #value = addunit(value, 'GeV')
                #print '*****************', value
                value = value * GeV
                
            for res in self._results:
                if res.axes['mz'] == (condition, value):
                    return res._topo
                else: continue 
            logger.warning('Unknown condition for third mass %s = %s!' \
            %(condition, value))
            return self._getDefaultExtendedTopology
    
    @property
    def _getDefaultExtendedTopology(self):
        """Retrieves the default topology settings for this set of results.
        :return: 'extended topology'
    
        """
        first = self._expAna._infotxt.axes[self._topo][0]
        if first['extension']:
            return self._topo + first['extension']
        else:
            return self._topo
        
    
    @property
    def _axes(self):
        """Retrieves the axes information for this result.
        :return: {extended topology: 
        {'mx': mass on x-axis, 'my': mass on y-axes, 
        'mz': condition for intermediate mass}}
        
        """
        if not self._expAna.hasAxes:
            logger.warning('No axes information available for analysis %s.' \
            %self._ana)
            return None
        try:
            return self._expAna.axes[self._topo]
        except KeyError:
            logger.warning('No axes information available for set of results \
            %s.' %self.name)
            return None
    
    @property
    def _members(self):
        """Retrieves (condition, value) tuples for all the results in this set.
        # ### FIX ME: if there is no information about mz this results in {'Tx': None}
        this is not very nice?
        """
        axes = self._expAna._infotxt.axes[self._topo]
        mems ={}
        for ax in axes:
            if ax['extension']:
                mems[self._topo + ax['extension']] = ax['mz']
            else:
                mems[self._topo] = ax['mz']
        return mems        

class ExpResult(object):
    """Contains all specific informations linked to one result,
    where a result denotes a pair of analysis and topology with a specific
    assumption for the third mass (e.g. x-value = 050, mass of LSP = 50 GeV, ...).
    
    """
    
    def __init__(self, topology, expAnalysis, expTopology, smsroot, smspy):
        """Sets all private variables and initiates the dictionaries for 
        exclusion lines and exclusions.
        
        """
        self._topo = topology
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
        return self._ana + '-' + self._topo
        
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
    def siblings(self):
        """Retrieves the names of all the related results.
        
        """
        return self._siblings
    
    @property
    def axes(self):
        """Retrieves the x- and y- axis of the upper limit histogram
        end the additional condition for the third mass, if there is any.
        """
        return self._axes
        
    
    @property
    def allExclusionLines(self):
        """Retrieves the exclusion lines from the sms.root file linked to the 
        corresponding analysis and builds a nested dictionary including all 
        the exclusion lines. 
        :return: {'observed': {1: TGraph, 0: TGraph, -1: TGraph}, 
        'expected': {1: TGraph, 0: TGraph, -1: TGraph}}
        
        """
        
        return self._allExclusionLines

    def exclusionLines(self, expected = False):
        """Retrieves the observed/expected exclusion lines for this result 
        as a dictionary.
        :return: {1: TGraph, 0: TGraph, -1: TGraph}
        
        """
        return self._exclusionLines(expected)
    
    def exclusionLine(self, expected = False, sigma = 0):
        """Retrieves one observed/expected exclusion line for this result 
        specified by sigma.
        :param sigm: 1,0,-1
        :return: {1: TGraph, 0: TGraph, -1: TGraph}
        
        """

        return self._exclusionLine(expected, sigma)
    
    @property
    def allExclusions(self):
        """Retrieves the exclusion values for this result from the experimental  
        analysis object and builds a nested dictionary including all the 
        exclusion values.
        :return: {'observed': {'minx': value, 'xmin':value, 'xmax': value}, 
        'expected': {'minx': value, 'xmin': value, 'xmax': value}}
        
        """
        return self._allExclusions
    
    def exclusions(self, expected = False):
        """Retrieves the observed/expected exclusion values for this result 
        as a dictionary.
        :return: {'minx': value, 'xmin':value, 'xmax': value}
        
        """
        return _exclusions(expected)
    
    def exclusion(self, expected = False, typ = 'xmax'):
        """Retrieves the observed/expected exclusion value for this result 
        specified by typ.
        :param typ: 'minx', 'xmin', 'xmax'
        :return: {'minx': value, 'xmin':value, 'xmax': value}
        
        """
        return self._exclusion(expected, typ)
    
    def upperLimitDict(self, expected = False):
        """Retrieves the observed/expected cross section upper limit dictionary for this 
        result from the sms.py file located in the database.
        
        """
        return self._upperLimitDict(expected)
    
    @property
    def _siblings(self):
        sibs = []
        for t in self._expAna.extendedTopologies[self._expTopo.name]:
            sibs.append(self._ana + '-' + t)
        return sibs
    
    @property    
    def _allExclusionLines(self):
        """Retrieves the exclusion lines from the sms.root file linked to the 
        corresponding analysis and builds a nested dictionary including all 
        the exclusion lines. 
        :return: {'observed': {1: TGraph, 0: TGraph, -1: TGraph}, 
        'expected': {1: TGraph, 0: TGraph, -1: TGraph}}
        
        """
        if not self._smsroot:
            return None
        from ROOT import TFile
        rootFile = TFile(self._smsroot)
        exclusionLines = {'observed': 'exclusion', 'expected':\
        'expectedexclusion'}
        for key, value in exclusionLines.items(): 
            sigmaDict = {1: 'p1', 0: '', -1: 'm1'}
            for sigmaKey, sigmaValue in sigmaDict.items():
                sigmaDict[sigmaKey] = rootFile.Get(value + sigmaValue + '_' + \
                self._topo)
                ###FIX ME: work around to handel exclusionlines of the topology TChiWZon: 
                if not sigmaDict[sigmaKey]:
                    if self._topo[-2:] == 'on':
                        sigmaDict[sigmaKey] = rootFile.Get(value + sigmaValue + '_' + \
                        self._topo[:-2])
                    if self._topo[-3:] == 'off':
                        sigmaDict[sigmaKey] = rootFile.Get(value + sigmaValue + '_' + \
                        self._topo[:-3])
                ###---------------------------------------------------------------------
            exclusionLines[key] = sigmaDict
        logger.debug('Built dictionary for exclusion lines for %s-%s-%s: %s.'\
        %(self._run, self._ana, self._topo, exclusionLines))     
        return exclusionLines
     
    def _exclusionLines(self, expected):
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
    
    def _exclusionLine(self, expected, sigma):
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
    def _allExclusions(self):
        """Retrieves the exclusion values for this result from the experimental  
        analysis object and builds a nested dictionary including all the 
        exclusion values.
        :return: {'observed': {'minx': value, 'xmin':value, 'xmax': value}, 
        'expected': {'minx': value, 'xmin': value, 'xmax': value}}
        
        """
        
        excl = self._expAna.exclusions
        excl = [e for e in excl if self._topo in e]
        logger.debug('Found exclusions for %s-%s-%s: %s.'\
        %(self._run, self._ana, self._topo, excl))
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
                        self._topo, value))
                        typDict = {'xmin': line[2].strip(), \
                        'xmax': line[3].strip()}
            exclDict[key] = typDict
        logger.debug('Built dictionary for exclusion values for %s-%s-%s: %s.'\
        %(self._run, self._ana, self._topo, exclDict))    
        return exclDict
        
    def _exclusions(self, expected):
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
        
    def _exclusion(self, expected, typ):
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
            
    def _upperLimitDict(self, expected):
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
            if 'Dict' in localSms and self._topo in localSms['Dict']:
                if localSms['Dict'][self._topo] in fakeDicts:
                    logger.warning('No useful upper limit dictionary was found \n \
                    for extended result %s!' %self.name)
                    return None
                return localSms['Dict'][self._topo]
            logger.warning('No upper limit dictionary was found for extended \n \
            result %s!' %self.name)
            return None
        if expected:
            if 'ExpectedDict' in localSms and self._topo in \
            localSms['ExpectedDict']:
                if localSms['ExpectedDict'][self._topo] in fakeDicts:
                    logger.warning('No useful expected upper limit dictionary  \n \
                    was found for extended result %s!' %self.name)
                    return None
                return localSms['ExpectedDict'][self._topo]    
            logger.warning('No expected upper limit dictionary was found  \n \
            for extended result %s!' %self.name)  
            return None
            
    @property
    def _axes(self):
        if self._expTopo.name == self._topo:
            ax = self._expAna._infotxt.axes[self._expTopo.name][0]
            a = {key: ax[key] for key in ax if key != 'extension'}
            return a
        for ax in self._expAna._infotxt.axes[self._expTopo.name]:
            if self._expTopo.name + ax['extension'] != self._topo:
                continue
            a = {key: ax[key] for key in ax if key != 'extension'}
            return a
