#!/usr/bin/env python

"""
.. module:: databaseBrowser
   :synopsis: Centralized facility to access smodels-database 
   in order to produce summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Wolfgang Magerl <wolfgang.magerl@gmail.com>

"""

import ROOT
import logging, os, types
import setPath
import sys
import experimentalObjects


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

class Browser(object):
    
    """Browses the database, exits if given path does not point to a valid smodels-database. Browser can be restricted to specified run or experiment. Verbosity can be set to specified level.
    
    """
    def __init__(self, base = '/afs/hephy.at/user/w/walten/public/sms/'):
        self._allruns = ["8TeV", "ATLAS8TeV", "RPV8", "2012", "RPV7", "2011"]
        #self._allruns = ["8TeV", "ATLAS8TeV", "2012", "RPV7"]
        self._artifacts = ['old', 'bad', 'missing', 'TODO', 'readme']
        self._base = self._validateBase(base)
        self._experimentRestriction = None
        self._verbosity = 'error'
        self.database = self._getDatabase()
        self._runRestriction = None
        self._infos = {}
        self._analyses = {}
        self._topologies = {}
        self._results = {}
        
    @property
    def base(self):
        """This is the path to the base directory where to find the database.
        
        """
        return self._base
        
    def _validateBase(self, path):
        """Validates the base directory to locate the database. Exits the script if something is wrong with the path.
    
        """
        logger.debug('Try to set the path for the database to: %s' %path)
        if not os.path.exists(path):
            logger.error('%s is no valid path!' %path)
            sys.exit()
        if not [run for run in os.listdir(path) if run in self._allruns]:
            logger.error('There is no valid database at %s' %path)
            sys.exit()
        return path
        
    @property
    def experimentRestriction(self):
        """Tells if the browser is restricted to either CMS or ATLAS. Gives None if both are allowed.
        
        """
        return self._experimentRestriction
        
    @experimentRestriction.setter
    def experimentRestriction(self, detector):
        """Restricts the browser to either CMS or ATLAS.
        
        """
        self._experimentRestriction = self._validateExperiment(detector)
        if self._experimentRestriction == 'ATLAS':
            self.database = {key: self.database[key] for key in self.database if 'ATLAS' in key}
        if self._experimentRestriction == 'CMS':
            self.database = {key: self.database[key] for key in self.database if not 'ATLAS' in key}
        
    @experimentRestriction.deleter
    def experimentRestriction(self):
        """Removes the experimental restriction.
        
        """
        self._experimentRestriction = None
        self.database = self._getDatabase()
    
    def _validateExperiment(self, detector):
        """Validates the given experiment. Exits the script if the given experiment is unknown.
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
        self._verbosity = level
        self._setLogLevel(level)
        
    def _setLogLevel(self, level = 'error'):
        if level == 'debug':
            logger.setLevel(level=logging.DEBUG)
        if level == 'info':
            logger.setLevel(level=logging.INFO)
        if level == 'warning':
            logger.setLevel(level=logging.WARNING)
        if level == 'error':
            pass

    def _getDatabase(self):
        """Creates a dictionary containing all runs as keys and all subdirectories resp. analyses as entries.
    
        """
        data = {}
        for r in self._allruns:
            if not os.path.exists('%s/%s' % (self._base, r)):
                logger.info('Using an incomplete version of the database! Run %s is missing' %r)
                continue
            data[r] = os.listdir('%s/%s' % (self._base, r))
            data[r] = [directory for directory in data[r] if not '.' in directory]
            # exclude all files (e.g. create.sh) from list of directories 
            data[r] = [directory for directory in data[r] if not directory in self._artifacts]
            # exclude every file and directory specified by list of artifacts
        return data
     # ### FIX ME: Do we really want to restrict the run?   
    @property
    def runRestriction(self):
        """Tells if the browser is restricted to a specified run. Gives None if all runs are allowed.
        
        """
        return self._runRestriction
        
    @runRestriction.setter
    def runRestriction(self, run):
        """Restricts the Browser to one specified run.
        
        """
        self._runRestriction = self._validateRun(run)
        if self._runRestriction == None:
            logger.error('Failed to restrict browser to run: %s is not valid!' %run)
            sys.exit()
        logger.info('Browser restricted to run %s.' %run)
        self.database = {key: self.database[key] for key in self.database if key == self._runRestriction}
    
    @runRestriction.deleter
    def runRestriction(self):
        self._runRestriction = None
        self.database = self._getDatabase()
        
    def _validateRun(self, run):
        """Validates the given run. Returns None if the given run is unknown.
        
        """
        if not run: return None
        if not run in self.database.keys():
            logger.warning('%s is no valid run!' %run)
            return None

        return run
        
    def _validateAnalysis(self, analysis):
        """Validates the given analysis. Returns None if the given analysis is unknown.
        
        """
        if not analysis: return None    
        runs = [key for key in self.database if analysis in self.database[key]]
        if not runs:
            logger.warning('%s is no valid analysis!' %analysis)
            return None
        
        return analysis
        
        
    def _validateTopology(self, topology):
        """Validates the given topology. Returns valid topologies and None if the given topology is unknown.
        
        """
        
        if not topology in self.allTopologies():
            logger.warning('%s is no valid topology!' %topology)
            return None
            
        return topology
    
    def allRuns(self, analysis = None, topology = None):
        """Retrieves all runs a given analysis or topology or analysis-topology pair is available for. Returns a list containing all runs or just a string when analysis is given. 
    
        """
    # ### FIX ME: think about the ambiguities: rais an error?, stop the script?, try to pass this problem?
    # ### FIX ME: maybe return only list?
        if not analysis and not topology:
            logger.warning('No analysis was given. Returnvalue will be list containing all available runs!')
            return self.database.keys()
    
        if self._runRestriction:
            logger.warning('Cannot get all runs because browser is restricted to %s!' %self._runRestriction)
            return self._runRestriction
    
        if self._experimentRestriction:
            logger.warning('Browser is restricted to experiment %s' %self._experimentRestriction)
        
        analysis = self._validateAnalysis(analysis)
        if analysis and not topology:
            runs = [key for key in self.database if analysis in self.database[key]]
            if len(runs) == 1:
                return runs[0]
            logger.error('%s appears in %s runs! Returnvalue will be first hit! Please check the database for ambiguities!' %(analysis, len(runs)))
            return runs[0]
        
        topology = self._validateTopology(topology)    
        if not analysis and topology:
            runs = [key for key in self.database if self.allTopologies(run = key) and topology in self.allTopologies(run = key)]
            if not runs:
                return None
            logger.warning('No analysis was given. There are %s runs for given topology %s. Returnvalue will be list!' %(len(runs), topology))
            return runs
        
        if analysis and topology:
            runs = [key for key in self.database if analysis in self.database[key] and self.allTopologies(run = key) and topology in self.allTopologies(run = key)]
            if len(runs) == 1:
                return runs[0]
            logger.error('%s appears in %s runs! Returnvalue will be first hit! Please check the database for ambiguities!' %(analysis, len(runs)))
            return runs[0]

    def allAnalyses(self, run = None, topology = None):
        """Retrieves all analyses or all analyses existing for given run or run-topology-pair.
    
        """
    
        analyses = []
        topologies = []
    
        if self._runRestriction:
            logger.warnig('Browser is restricted to run %s!' %self._runRestriction)
        
        if not run:
            analyses = [self.database[key] for key in self.allRuns()]
            analyses = [ana for anas in analyses for ana in anas]  # flattens out the nested list to plain list
            
        if not topology and not run:
            return analyses
            
        if not topology and run:
            logger.debug('Found %s analyses for %s.' %(len(self.database[run]), run))
            return self.database[run]

        topology = self._validateTopology(topology)
        if topology and run:
            for a in self.database[run]:
                if self.allTopologies(analysis = a) and topology in self.allTopologies(analysis = a):
                    logger.debug('Found %s in %s-%s.' %(topology, run, a))
                    analyses.append(a)
            
        if topology and not run:
            analyses = [ana for ana in analyses if self.allTopologies(analysis = ana) and topology in self.allTopologies(analysis = ana)]
        
        
        if not analyses:
            logger.warning('There is no valid topology %s for given run %s!' %(topology, run))
            return None
        
        return analyses
    
    def allTopologies(self, run = None, analysis = None):
        """Retrieves all topologies existing for given run or analysis-run-pair
    
        """
        topos = []
        runs = []
        analyses = []
        analysis = self._validateAnalysis(analysis)
        run = self._validateRun(run)
    
        if analysis and not run:
            analyses.append(analysis)
            runs.append(self.allRuns(analysis))

        if run and not analysis:
            runs.append(run)
            analyses = self.allAnalyses(run)
            
        if run and analysis:
            runs.append(run)
            analyses.append(analysis)
        
        if not run and not analysis:
            runs = self.allRuns()
            analyses = self.allAnalyses()
                    
        logger.debug('Searching topologies for runs %s and analyses %s' %(runs,analyses))
    
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
            logger.info('for runs %s and analyses %s no topology could be found' %(runs, analyses))
            return None
        
        return topos
    
    def _checkResults(self, analysis, requested = 'info.txt'):
        """Checks if results for given analysis are available in form of info.txt, sms.root and sms.py, returns path to these files.
    
        """
    
        analysis = self._validateAnalysis(analysis)
        run = self.allRuns(analysis)
        
        path = self._base + run + '/' + analysis + '/' + requested
        logger.debug('Check path: %s.' %path)
        if not os.path.exists(path):
            logger.warning('For run %s and analysis %s no %s was found!' %(run, analysis, requested))
            return None
        
        return path
    
    def expAnalysis(self, analysis):
        """This is the factory for the experimental Analysis object. 
        Returns None if it's not possible to build the experimental analysis object. 
        
        """
        
        #if isinstance(analysis, object):
            #return analysis
        if analysis in self._analyses:
            return self._analyses[analysis]
        if not self._checkResults(analysis):
            logger.info('Skipped building of ExpAnalysis-object for %s!' %analysis)
            return None
        if not analysis in self._infos:
            logger.debug('Browser has no info.txt-object for %s!' %analysis)
            self._infos[analysis] = Infotxt(analysis, self._checkResults(analysis))
            logger.debug('Created and stored info.txt-object!')
        logger.debug('Try to creat experimental Analysis: %s - %s - %s' %(analysis, self._infos[analysis], self.allRuns(analysis)))    
        self._analyses[analysis] = experimentalObjects.ExpAnalysis(analysis, self._infos[analysis], self.allRuns(analysis))
        return self._analyses[analysis]
        
    def expTopology(self, topology):
        """This is the factory for the experimental Topology object.
        
        """        
        #if isinstance(topology, object):
            #return topology
        if topology in self._topologies:
            return self._topologies[topology]
        topology = self._validateTopology(topology)
        topoDict = self._topoDict(topology)        
        self._topologies[topology] = experimentalObjects.ExpTopology(topology, topoDict)
        return self._topologies[topology]
        
    def _topoDict(self, topology):
        topoDict = {}
        for r in self.allRuns(topology = topology):
            topoDict[r] = {}
            for a in self.allAnalyses(run = r, topology = topology):
                if not a in self._infos:
                    logger.debug('Browser has no info.txt-object for %s!' %a)
                    self._infos[a] = Infotxt(a, self._checkResults(a))
                    logger.debug('Created and stored info.txt-object!')
                topoDict[r][a] = self._infos[a].category
        print '####################', topoDict
        return topoDict
                
        
    def expResult(self, analysis, topology, run = None):
        """This is the factory for the experimental Result object.
        
        """
        _result = analysis + '-' + topology
        if _result in self._results:
            return self._results[_result]
        analysis = self._validateAnalysis(analysis)
        topology = self._validateTopology(topology)
        if run:
            run = self._validateRun(run)
        if not run:
            run = self.allRuns(analysis, topology)
            
        if not analysis or not topology or not topology in self.alltopologies(run, analysis):
            logger.warning('There is no experimental result for run-analysis-topology: %s-%s-%s!' %(run, analysis, topology))
            return None
        self._results[_result] = experimentalObjects.ExpResult(run, self.expAnalysis(analysis), self.expTopology(topology))
        return experimentalObjects.ExpResult(run, self.expAnalysis(analysis), self.expTopology(topology))
        
class Infotxt(object):
    """Holds all the lines, stored in the info.txt file. Provides the required information about topologies, results and all the meta-information needed for the experimental objects.
    # ### FIX ME:add category-method
    """
    
    def __init__(self, analysis, path):
        self._analysis = analysis
        logger.debug('Got analysis %s.' %analysis)
        self._path = path
        self._run = self._path.split('/')[-3]
        logger.debug('Got run %s.' % self._run)
        logger.debug('Creating object based on info.txt: %s' %self._path)
        self._exceptions = ['constraint', 'condition', 'fuzzycondition', 'unconstraint', 'exclusions', 'expectedexclusions', 'exclusionsp1', 'expectedexclusionsp1','exclusionsm1', 'expectedexclusionsm1', 'category']
        
    def _readInfo(self):
        """Reads the whole info.txt file, returns a tuple containing a dictionary holding the meta-information (e.g. PAS, lumi, comment, ...) and a list holding all the lines with keywords that show up several times (e.g. 'constraint', 'condition', 'exclusions', ...).
    
        """
        info = []
        infoFile = open(self._path)
        content = infoFile.readlines()
        infoFile.close()
        
        logger.debug('Found info.txt for %s.' %self._path)
        metaInfo = {line.split(':', 1)[0].strip(): line.split(':', 1)[1].strip() for line in content if not line.split(':')[0].strip() in self._exceptions}
        #logger.debug('Meta info is %s' %metaInfo)
        for key in self._exceptions:
            for line in content:
                if key in line:
                    info.append(line.strip())
        #logger.debug('Info is %s' %info)    
        return [metaInfo, info]
    
    @property
    def metaInfo(self):
        """Returns the meta info dictionary.
        
        """
        return self._readInfo()[0]
        
    @property
    def info(self):
        """Returns the list of lines connected with the topologies.
        
        """
        return self._readInfo()[1]
     
    @property
    def category(self):
        cat = {}
        content = self.info
        content = [string.strip() for string in content if 'category' in string]
        content = [string.split(':')[1] for string in content] 
        for c in content:
            cat[c.split('->')[0].strip()] = c.split('->')[1].strip()
        return cat
        
    @property
    def topologies(self):
        topos = []
        content = self.info
        content = [string.strip() for string in content if 'constraint' in string or 'unconstraint' in string]
        for c in content:
            if topos.count(c.split(' ')[1]) == 0:
                topos.append(c.split(' ')[1])                
        return topos
        
    @property    
    def _preprocessAxes(self):
        """Handles the information stored in the axes-labeled line of info.txt, therefor this line has to be preprocessed.
    
        """
        infoLine = self.metaInfo['axes'].split(',')
        infoLine = [ax.strip() for ax in infoLine]
        logger.debug('axes- information: %s' %infoLine)
        return infoLine


        
    def extendedTopologies(self, topology = None):
        """Checks if the topologies in this info.txt are tainted with any kind of mass requirements and returns dictionary with extended topologies. Can be reduced to given topology (returns list).
    
        """
        topos = {}
        logger.debug('Got analysis %s and run %s!' %(self._analysis, self._run))
        if not 'axes' in self.metaInfo:
            logger.info('No additional information about axes was found for %s-%s!' %(self._run, self._analysis))
            if not self.topologies: return None
            for t in self.topologies:
                topos[t]=[t]
            if not topology: return topos
            if topos.has_key(topology): return topos[topology]
            logger.warning('For %s-%s there is no topology %s' %(self._run, self._analysis, topology))
            return None
    
        axes = self._preprocessAxes
        logger.info('For %s-%s there is additional mass information!' %(self._run, self._analysis)) 
        
        for ax in axes:
            logger.debug('Axesline is: %s' %ax)
            massdic = self._massProportions(ax)
            topo = massdic.keys()[0]
            topos[topo] = []

            for case in massdic[topo]:
                if len(case) == 2: topos[topo].append(topo)
                if len(case) == 3:
                    try:
                        x = int(case[2])
                        topos[topo].append(topo + case[2])
                    except ValueError:
                        if 'D' in case[2]:
                            D = case[2].split('=')[-1].strip()
                            topos[topo].append(topo + 'D' + D)
                        elif 'LSP' or 'x' or 'C' or 'M' in case[2]: topos[topo].append(topo + case[2])
                if len(case) > 3:
                    logger.warning('Topology is: %s => more then one additional condition is too much at the moment.' %topo)
                    continue
        
        if topos == {'':[]}:
            logger.warning('Something is wrong with the axes line in the info.txt for %s-%s!' %(self._run, self._analysis))
            return None
        if not topology: return topos
        if topos.has_key(topology): return topos[topology]
        logger.warning('For %s-%s there is no topology %s.' %(self._run, self._analysis, topology))
        return None

    def _massProportions(self, axesLine):
        """Reads out all the conditions for intermediate masses (e.g. masssplitting-xvalues 025, 050, 075) implicitly stored in axes-lines of info.txt and returns the information as dictionary.
    
        """
        massdic = {}
        topo = axesLine.split(' ')[0].replace(':', '').strip()
        massdic[topo] = axesLine.replace(topo + ':', '').split('-')
        massdic[topo] = [c.strip() for c in massdic[topo]]
        logger.info('For %s there are %s different cases of mass proportions.' %(topo, len(massdic[topo])))
        massdic[topo]=[c.split(' ') for c in massdic[topo]]
        logger.debug('For %s the massdictionary is: %s.' %(topo, massdic[topo]))
        return massdic
