#!/usr/bin/env python

"""
.. module:: databaseBrowser
   :synopsis: Centralized facility to access smodels-database.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Wolfgang Magerl <wolfgang.magerl@gmail.com>

"""

import ROOT
import logging, os, types
import setPath
import sys
import experimentalTopology
import experimentalAnalysis
import experimentalResults
from smodels.tools.physicsUnits import GeV, addunit, rmvunit


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

class Browser(object):
    
    """Browses the database, exits if given path does not point to a valid 
    smodels-database. Browser can be restricted to specified run or experiment. 
    Verbosity can be set to specified level.
    
    """
    def __init__(self, base = '/afs/hephy.at/user/w/walten/public/sms/'):
        self._allruns = ["8TeV", "ATLAS8TeV", "RPV8", "2012", "RPV7", "2011"]
        #self._allruns = ["8TeV", "ATLAS8TeV", "2012", "RPV7"]
        self._artifacts = ['old', 'bad', 'missing', 'TODO', 'readme', 'SUCHI_RL_TEST']
        self._base = self._validateBase(base)
        self._experimentRestriction = None
        self._verbosity = 'error'
        self._databaseVersion = self._getDatabaseVersion
        self.database = self._getDatabase()
        self._runRestriction = None
        self._infos = {}
        self._analyses = {}
        self._topologies = {}
        self._results = {}
        self._resultSets = {}

    @property
    def databaseVersion(self):
        """The version of the database, read from the 'version'
           file.

        """
        return self._databaseVersion
        
    @property
    def base(self):
        """This is the path to the base directory where to find the database.
        
        """
        return self._base
        
    def _validateBase(self, path):
        """Validates the base directory to locate the database. 
        Exits the script if something is wrong with the path.
    
        """
        logger.debug('Try to set the path for the database to: %s' %path)
        path = os.path.realpath(path) + '/'
        if not os.path.exists(path):
            logger.error('%s is no valid path!' %path)
            sys.exit()
        if not [run for run in os.listdir(path) if run in self._allruns]:
            logger.error('There is no valid database at %s' %path)
            sys.exit()
        return path
     
    @property
    def _getDatabaseVersion(self):
        """Retrieves the version of the database using the version file.
        
        """
        try:
            versionFile = open(self._base + '/version')
            content = versionFile.readlines()
            versionFile.close()
            logger.debug('Found version file %s with content %s' \
            %(self._base + '/version', content))
            return content[0].strip()
            
        except IOError:
            logger.error('There is no version file %s' \
            %self._base + '/version')
            return 'unknown version'
        
    @property
    def experimentRestriction(self):
        """Tells if the browser is restricted to either CMS or ATLAS. 
        Gives None if both are allowed.
        
        """
        if self._experimentRestriction:
            return self._experimentRestriction
        return 'Browser will use CMS and ATLAS'
        
    @experimentRestriction.setter
    def experimentRestriction(self, detector):
        """Restricts the browser to either CMS or ATLAS.
        
        """
        self._experimentRestriction = self._validateExperiment(detector)
        if self._experimentRestriction == 'ATLAS':
            self.database = {key: self.database[key] for key in \
            self.database if 'ATLAS' in key}
        if self._experimentRestriction == 'CMS':
            self.database = {key: self.database[key] for key in \
            self.database if not 'ATLAS' in key}
        
    @experimentRestriction.deleter
    def experimentRestriction(self):
        """Removes the experimental restriction.
        
        """
        self._experimentRestriction = None
        self.database = self._getDatabase()
    
    def _validateExperiment(self, detector):
        """Validates the given experiment. Exits the script if the given 
        experiment is unknown.
        ### FIX ME: maybe better not exit the script, but set experiment to default?
        
        """
        if not detector in ['CMS', 'ATLAS']:
            logger.error('%s is no valid experiment!' %detector)
            sys.exit()
        logger.info('Focusing on experiment %s.' %detector)
        return detector
        
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
            logger.error('No valid level for verbosity: %s! Browser will \n \
            use default setting!' %level)
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
    def experimentalObejctsDictionaries(self):
        """Retrieves all the dictionaries containing the experimental objects.
        Use the deleter to reset these.
        """
        return [self._analyses, self._topologies, self._resultSets, self._infos]
        
    @experimentalObejctsDictionaries.deleter
    def experimentalObejctsDictionaries(self):
        """Resets all the dictionaries containing the experimental objects in
        order to get all the logger messages from the building process again.
        """
        [self._analyses, self._topologies, self._resultSets, self._infos] \
        = [{}, {}, {}, {}]

    def _getDatabase(self):
        """Creates a dictionary containing all runs as keys and all 
        subdirectories resp. analyses as entries.
    
        """
        data = {}
        if os.path.exists('%s/version' % self._base ):
            # set the database version
            f=open('%s/version' % self._base )
            self._databaseVersion=f.readline()[:-1]
            f.close()
        for r in self._allruns:
            if not os.path.exists('%s/%s' % (self._base, r)):
                logger.info('Using an incomplete version of the \n\
                database! Run %s is missing' %r)
                continue
            data[r] = os.listdir('%s/%s' % (self._base, r))
            data[r] = [directory for directory in data[r] if not '.' in \
            directory]
            # exclude all files (e.g. create.sh) from list of directories 
            data[r] = [directory for directory in data[r] if not directory in \
            self._artifacts]
            # exclude every file and directory specified by list of artifacts
        return data
        
    # ### FIX ME: Do we really want to restrict the run?   
    @property
    def runRestriction(self):
        """Tells if the browser is restricted to a specified run. 
        
        """
        if not self._runRestriction:
            return 'All runs are allowed.'
        return self._runRestriction
        
    @runRestriction.setter
    def runRestriction(self, run):
        """Restricts the browser to one specified run. Don't use this lightly
        it may cause serious changes in functionality.
        
        """
        self._runRestriction = self._validateRun(run)
        if not self._runRestriction:
            logger.error('Failed to restrict browser to run: %s is not \n\
            valid!' %run)
            sys.exit()
        logger.warning('Browser restricted to run %s.' %run)
        self.database = {key: self.database[key] for key in self.database if \
        key == self._runRestriction}
    
    @runRestriction.deleter
    def runRestriction(self):
        """Deletes the restriction to one run.
        
        """
        self._runRestriction = None
        self.database = self._getDatabase()
        
    def _validateRun(self, run):
        """Validates the given run. Returns None if the given run is unknown.
        
        """
        if not run: return None
        if not run in self.database:
            logger.error('%s is no valid run!' %run)
            return None

        return run
        
    def _validateAnalysis(self, analysis):
        """Validates the given analysis. Returns None if the given analysis 
        is unknown.
        
        """
        if not analysis: return None    
        runs = [key for key in self.database if analysis in self.database[key]]
        if not runs:
            logger.error('%s is no valid analysis!' %analysis)
            return None
        
        return analysis
        
        
    def _validateTopology(self, topology):
        """Validates the given topology. Returns valid topologies and None if 
        the given topology is unknown.
        
        """
        
        if not topology in self.getTopologies():
            logger.error('%s is no valid topology!' %topology)
            return None
            
        return topology
    
    def getRuns(self, analysis = None, topology = None):
        """Retrieves all runs a given analysis or topology or analysis-topology 
        pair is available for. Returns a list containing all runs or just a 
        string when analysis is given. 
        
        """
    # ### FIX ME: think about the ambiguities: rais an error?, stop the script?,
    #try to pass this problem?
    # ### FIX ME: maybe return only list?
        if not analysis and not topology:
            logger.warning('No analysis was given. Returnvalue will be list\n \
            containing all available runs!')
            return self.database.keys()
    
        if self._runRestriction:
            logger.warning('Cannot get all runs because browser is restricted \n\
            to %s!' %self._runRestriction)
            #return self._runRestriction
    
        if self._experimentRestriction:
            logger.warning('Browser is restricted to experiment %s!' \
            %self._experimentRestriction)
        
        analysis = self._validateAnalysis(analysis)
        if analysis and not topology:
            runs = [key for key in self.database if analysis in \
            self.database[key]]
            if len(runs) == 1:
                return runs[0]
            logger.warning('%s appears in %s runs! Returnvalue will be first\n \
            hit! Please check the database for ambiguities!' \
            %(analysis, len(runs)))
            return runs[0]
        
        topology = self._validateTopology(topology)    
        if not analysis and topology:
            runs = [key for key in self.database if \
            self.getTopologies(run = key) and topology in \
            self.getTopologies(run = key)]
            if not runs:
                return None
            logger.warning('No analysis was given. There are %s runs for given\n \
            topology %s. Returnvalue will be list!' %(len(runs), topology))
            return runs
        
        if analysis and topology:
            runs = [key for key in self.database if analysis in \
            self.database[key] and self.getTopologies(run = key) and topology \
            in self.getTopologies(run = key)]
            if not runs:
                logger.warning('Could not find run for %s-%s!' \
                %(analysis, topology))
                return None
            if len(runs) == 1:
                return runs[0]
            logger.error('%s appears in %s runs! Returnvalue will be first hit!\n \
            Please check the database for ambiguities!' %(analysis, len(runs)))
            return runs[0]

    def getAnalyses(self, run = None, topology = None):
        """Retrieves all analyses or all analyses existing for given run or 
        run-topology-pair.
    
        """
    
        analyses = []
        topologies = []
    
        if self._runRestriction:
            logger.warning('Browser is restricted to run %s!' \
            %self._runRestriction)
        
        if not run:
            analyses = [self.database[key] for key in self.getRuns()]
            analyses = [ana for anas in analyses for ana in anas]  
            # flattens out the nested list to plain list
            
        if not topology and not run:
            return analyses
            
        if not topology and run:
            logger.debug('Found %s analyses for %s.' \
            %(len(self.database[run]), run))
            return self.database[run]

        topology = self._validateTopology(topology)
        if topology and run:
            for a in self.database[run]:
                if self.getTopologies(analysis = a) and topology in \
                self.getTopologies(analysis = a):
                    logger.debug('Found %s in %s-%s.' %(topology, run, a))
                    analyses.append(a)
            
        if topology and not run:
            analyses = [ana for ana in analyses if \
            self.getTopologies(analysis = ana) and topology in \
            self.getTopologies(analysis = ana)]
        
        
        if not analyses:
            logger.warning('There is no valid topology %s for given run %s!' \
            %(topology, run))
            return None
        
        return analyses
    
    def getTopologies(self, run = None, analysis = None):
        """Retrieves all topologies existing for given run or analysis-run-pair.
    
        """
        topos = []
        runs = []
        analyses = []
        analysis = self._validateAnalysis(analysis)
        run = self._validateRun(run)
    
        if analysis and not run:
            analyses.append(analysis)
            runs.append(self.getRuns(analysis))

        if run and not analysis:
            runs.append(run)
            analyses = self.getAnalyses(run)
            
        if run and analysis:
            runs.append(run)
            analyses.append(analysis)
        
        if not run and not analysis:
            runs = self.getRuns()
            analyses = self.getAnalyses()
                    
        logger.debug('Searching topologies for runs %s and analyses %s.' \
        %(runs,analyses))
    
        for r in runs:
            for a in analyses:
                if a in self._infos:
                    content = self._infos[a]
                else:
                    content = Infotxt(a, self._checkResults(a))
                    self._infos[a] = content
                for t in content.topologies:
                    if topos.count(t) == 0:
                        topos.append(t)
        if not topos:
            logger.info('For runs %s and analyses %s no topology could be found!' \
            %(runs, analyses))
            return None
        
        return topos
    
    def _checkResults(self, analysis, requested = 'info.txt'):
        """Checks if results for given analysis are available in form of 
        info.txt, sms.root and sms.py, returns path to these files.
    
        """
        if not self._validateAnalysis(analysis):
            return None
            
        run = self.getRuns(analysis)
        path = self._base + run + '/' + analysis + '/' + requested
        logger.debug('Check path: %s.' %path)
        if not os.path.exists(path):
            logger.warning('For run %s and analysis %s no %s was found!' \
            %(run, analysis, requested))
            return None
        
        return path
    
    def expAnalysis(self, analysis):
        """This is the factory for the experimental analysis object. 
        Returns None if it's not possible to build the experimental 
        analysis object. 
        
        """
        
        #if isinstance(analysis, object):
            #return analysis
        if analysis in self._analyses:
            return self._analyses[analysis]
        if not self._checkResults(analysis):
            logger.info('Skipped building of ExpAnalysis-object for %s! \n \
            There is not enough information.' %analysis)
            return None
        if not analysis in self._infos:
            logger.debug('Browser has no info.txt-object for %s!' %analysis)
            self._infos[analysis] = Infotxt(analysis, \
            self._checkResults(analysis))
            logger.debug('Created and stored info.txt-object!')
        logger.debug('Try to create experimental Analysis: %s - %s - %s' \
        %(analysis, self._infos[analysis], self.getRuns(analysis)))    
        self._analyses[analysis] = experimentalAnalysis.ExpAnalysis(analysis, \
        self._infos[analysis], self.getRuns(analysis), \
        self._checkResults(analysis, requested = 'sms.root'), \
        self._checkResults(analysis, requested = 'sms.py'))
        return self._analyses[analysis]
        
    def expTopology(self, topology):
        """This is the factory for the experimental topology object.
        
        """        
        #if isinstance(topology, object):
            #return topology
        if topology in self._topologies:
            return self._topologies[topology]
        topology = self._validateTopology(topology)
        topoDict = self._topoDict(topology)        
        self._topologies[topology] = experimentalTopology.ExpTopology(topology, \
        topoDict)
        return self._topologies[topology]
        
    def _topoDict(self, topology):
        """Creates a nested dictionary that holds all the info.txt objects
        for each topology.
        :return: {'topology': {'analysis': Infotxt(analysis)}}
        
        """
        topoDict = {}
        for r in self.getRuns(topology = topology):
            topoDict[r] = {}
            for a in self.getAnalyses(run = r, topology = topology):
                if not a in self._infos:
                    logger.debug('Browser has no info.txt-object for %s!' %a)
                    self._infos[a] = Infotxt(a, self._checkResults(a))
                    logger.debug('Created and stored info.txt-object!')
                topoDict[r][a] = self._infos[a]
        return topoDict
                
        
    def expResultSet(self, analysis, topology):
        """This is the factory for the experimental result set object.
        :param analysis: name of analysis as string or expAnalysis.name
        :param topology: name of topology as string or expTopology.name
        
        """
        resultSet = analysis + '-' + topology
        logger.debug('Try to get experimental result %s for %s-%s.' \
        %(resultSet, analysis, topology))
        if resultSet in self._resultSets:
            logger.debug('Found experimental result for %s in dictionary.' \
            %resultSet)
            return self._resultSets[resultSet]
        analysis = self._validateAnalysis(analysis)
        expAna = self.expAnalysis(analysis)
        run = expAna.run
        if not topology in expAna.topologies:
            logger.error('There is no experimental result set for \n\
            run-analysis-topology: %s-%s-%s!' %(run, analysis, topology))
            return None
        self._resultSets[resultSet] = experimentalResults.ExpResultSet(run, \
        expAna, self.expTopology(topology), \
        self._checkResults(analysis, requested = 'sms.root'), \
        self._checkResults(analysis, requested = 'sms.py'))
        logger.debug('Built experimental result for %s-%s: %s' \
        %(analysis, topology, self._resultSets[resultSet]))
        return self._resultSets[resultSet]
    
    def expResult(self, analysis, topology):
        """This is the factory for the experimental result object.
        :param analysis: name of analysis as string or expAnalysis.name
        :param topology: name of extended topology as string 
        (e.g. 'T6ttWWLSP050')
        
        """
        result = analysis + '-' + topology
        logger.debug('Try to get experimental result %s for %s-%s.' \
        %(result, analysis, topology))
        expAna = self.expAnalysis(analysis)
        run = expAna.run
        for topo in expAna.extendedTopologies:
            if topology in expAna.extendedTopologies[topo]:
                return self.expResultSet(analysis, topo).results[result]
            else:
                continue
        logger.error('There is no experimental result for \n\
        run-analysis-topology: %s-%s-%s!' %(run, analysis, topology))
        return None
            
    
class Infotxt(object):
    """Holds all the lines, stored in the info.txt file. 
    Provides the required information about topologies, results and all the 
    meta-information needed for the experimental objects.

    """
    
    def __init__(self, analysis, path):
        self._analysis = analysis
        logger.debug('Got analysis %s.' %analysis)
        self._path = path
        self._run = self._path.split('/')[-3]
        logger.debug('Got run %s.' % self._run)
        logger.debug('Creating object based on info.txt: %s' %self._path)
        self._exceptions = ['constraint', 'condition', 'fuzzycondition', \
        'unconstraint', 'exclusions', 'expectedexclusions', 'exclusionsp1', \
        'expectedexclusionsp1','exclusionsm1', 'expectedexclusionsm1', \
        'category']
    
    @property
    def _readInfo(self):
        """Reads the whole info.txt file, returns a tuple containing a 
        dictionary holding the meta-information (e.g. PAS, lumi, comment, ...) 
        and a list holding all the lines with keywords that show up several 
        times (e.g. 'constraint', 'condition', 'exclusions', ...).
    
        """
        info = []
        infoFile = open(self._path)
        content = infoFile.readlines()
        infoFile.close()
        
        #logger.debug('Found info.txt for %s.' %self._path)
        metaInfo = {line.split(':', 1)[0].strip(): line.split(':', 1)[1].strip() \
        for line in content if not line.split(':')[0].strip() in self._exceptions}
        #logger.debug('Meta info is %s' %metaInfo)
        for key in self._exceptions:
            for line in content:
                if key in line:
                    info.append(line.strip())
        #logger.debug('Info is %s' %info)    
        return [metaInfo, info]
    
    @property
    def metaInfo(self):
        """Returns the meta info dictionary (contains the axes line too).
        
        """
        return self._readInfo[0]
        
    @property
    def info(self):
        """Returns the list of lines connected with the topologies.
        
        """
        return self._readInfo[1]
    
    def _topoInfo(self, requested):
        """Creates a dictionary for topology related information.
        :return: {'topology': 'line of info.txt'}
        
        """
        dic = {}
        logger.debug('Look for requested keyword %s.' %requested)
        content = self.info
        content = [string.strip() for string in content if requested in string]
        content = [string.split(':')[1] for string in content] 
        for c in content:
            dic[c.split('->')[0].strip()] = c.split('->')[1].strip()
        return dic
        
    @property
    def category(self):
        cat = self._topoInfo('category')
        return cat
    
    @property
    def constraints(self):
        const = self._topoInfo('constraint')
        return const
    
    @property
    def topologies(self):
        topos = []
        content = self.info
        content = [string.strip() for string in content if 'constraint' \
        in string or 'unconstraint' in string]
        for c in content:
            if topos.count(c.split(' ')[1]) == 0:
                topos.append(c.split(' ')[1])                
        return topos

    @property    
    def exclusions(self):
        """Retrieves all the exclusions for every extended topology stored in 
        the info.txt and returns them as simple list.
        
        """
        infList = self.info
        exList = []
        keys = ['exclusions', 'expectedexclusions', 'exclusionsp1', \
        'expectedexclusionsp1','exclusionsm1', 'expectedexclusionsm1']
        infList = [l for l in infList for k in keys if k in l]
        for l in infList:
            if exList.count(l) == 0:
                exList.append(l)
        logger.debug('List of exclusions for %s-%s: %s.' \
        %(self._run, self._analysis, exList))
        return exList
        
    @property    
    def _preprocessAxesLine(self):
        """Handles the information stored in the axes-labeled line of info.txt, 
        therefor this line has to be preprocessed.
    
        """
        infoLine = self.metaInfo['axes'].split(',')
        infoLine = [ax.strip() for ax in infoLine]
        logger.debug('axes- information: %s' %infoLine)
        return infoLine
        
    def _axesDict(self, axesLines):
        """Splits the axes line and retrieves all the topologies to form
        a dictionary.
        :return: {'topology': ['axes entry', 'axes entry', ...]}
    
        """
        axDic = {}
        for axesLine in axesLines:
            topo = axesLine.split(' ')[0].replace(':', '').strip()
            axDic[topo] = axesLine.replace(topo + ':', '').split('-')
            axDic[topo] = [c.strip() for c in axDic[topo]]
            logger.debug('For %s there are %s masses.' \
            %(topo, len(axDic[topo])))
            logger.debug('For %s the axes dictionary is: %s.' %(topo, axDic[topo]))
        return axDic
        
    
    def _massDict(self, axesEntry):
        """Retrieves the axes information for given entry as dictionary.
        :param axesEntry: one axes entry for one topology
        :return:  {'mx': mass on x-axis, 'my': mass on y-axes, 
        'mz': condition for intermediate mass} or 
        {'mx': mass on x-axis, 'my': mass on y-axes, 
        'm3': condition for first intermediate mass,
        'm4': condition for second intermediate mass}
        
        """
        
        axDict = {}
        
        logger.debug('Axes entry: %s.' %axesEntry.split())
        axDict['mx'] = axesEntry.split()[0].strip()
        axDict['my'] = axesEntry.split()[1].strip()
        try:
            axesEntry.split()[3]
            logger.info('There are more then three masses!\n\
            Keys will be mx, my, m3 and m4!')
            axDict['m3'] = axesEntry.split()[2].strip()
            axDict['m4'] = axesEntry.split()[3].strip()
            axDict['extension'] = '%s%s' %(axDict['m3'], axDict['m4'])
        except IndexError:
            try:
                axDict['mz'] = axesEntry.split()[2].strip()
                axDict['extension'] = axesEntry.split()[2].strip()
            except IndexError:
                logger.debug('No intermediate mass mz.')
                axDict['mz'] = None
                axDict['extension'] = None
        return axDict
        
    def _massCondition(self, mz):
        """Takes the axes entry for the third mass and splits it into
        condition for this mass and its value with units added if not unitless:
        -) fixed LSP, Chargino or other mass in GeV
        -) mass splitting (as well 'xvalue'): M2=x*M1+(1-x)*M0
        -) difference between masses (e.g. M1-M0) in GeV
        -) ratio between masses (e.g. M2/M0) in percent
        :param mz: third item of an axes-entry for one topology
        :return: ('massCondition', value)
        
        """
        
        try:
            value = float(mz) / (10. ** (len(mz)-1))
            condition = 'massSplitting'
        except TypeError:
            logger.debug('Got no mz!')
            return None
        except ValueError:
            if 'D' in mz:
                value = addunit(int(mz.split('=')[-1].strip()), 'GeV')
                if mz.split('=')[0].strip() == 'D':
                    logger.error('There is something wrong with the "D-entry"!\n \
                    Check database for %s!' %self.name)
                    condition = 'unknownDifference' 
                else:
                    condition = mz.split('=')[0].strip().replace('D(', '')
                    condition = condition.replace(')', '')
                    condition = condition.split('/')
                    condition = '%s-%s' %(condition[0], condition[1])
            elif 'LSP' in mz:
                value = addunit(int(mz.replace('LSP', '')), 'GeV')
                condition = 'fixedLSP'
            elif 'M' in mz:
                value = addunit(int(mz[2:]), 'GeV')
                condition = 'fixed%s' %mz[:2]
            elif 'C' in mz:
                value = addunit(int(mz.replace('C', '')), 'GeV')
                condition = 'fixedM2'
            elif 'x' in mz:
                value = (float(mz.replace('x', ''))/100.)
                condition = 'M2/M0'
            else:
                logger.error('Unknown third mass entry %s!' %mz)
                value = None
                condition = None
        return (condition, value)
                        
    @property
    def axes(self):
        """Runs all the preprocessing methods and retrieves the wrought axes 
        information.
        :return: {'topology': [{'mx': 'mass on x-axis', 'my': 'mass on y-axis',
        'mz': ('condition for third mass', int(value for this condition)), 
        'extension': 'extension glued to topology name'}]}
        # ### FIX ME: if there are two conditions for intermediate masses this routine yields the wrong format. -> Fixed, right? 
        # ### FIX ME: These entries should be totally removed?
        """
        
        axLines = self._preprocessAxesLine
        axDict = self._axesDict(axLines)
        # Just to cross check these two fields of the info.txt,
        # print some warnings.
        for t in self.topologies:
            if not t in axDict:
                logger.warning('There is no axes entry for %s-%s! Check database!' %(self._analysis, t))
        for t in axDict:
            if not t in self.topologies:
                logger.error('There is an axes entry for %s-%s, \n \
                but this is no known topology! Check database!' %(self._analysis, t))
        axDict = {t: axDict[t] for t in axDict if t in self.topologies}
        for t in axDict:
            entries = []
            for entry in axDict[t]:
                entries.append(self._massDict(entry))

            #entries = [e for e in entries if e]
            for entry in entries:
                for key in ['mz', 'm3', 'm4']:
                    if key in entry:
                        entry[key] = self._massCondition(entry[key])
                    
            axDict[t] = entries    
            logger.debug('Axes information for %s is: %s' \
            %(t, axDict[t]))
        return axDict
    
    @property
    def extensions(self):
        """Retrieves a dictionary with the topologies as keys and the 
        extensions for these topologies to find exclusion lines etc.
        :return: {'topology': ['extension']}
        
        """
        extDic = {}
        for t in self.topologies:
            extDic[t] = []
            try:
                axes = self.axes[t]
            except KeyError:
                continue
            for ax in axes:
                if ax['extension']:
                    if 'D' in ax['extension']:
                        extDic[t].append('D' + ax['extension'].split('=')[-1].strip())
                    else:    
                        extDic[t].append(ax['extension'])
                        
        return extDic
            