#!/usr/bin/env python

"""
.. module:: gridDataCreator
   :synopsis: Will produce the grid data for the validation plots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

from __future__ import print_function
import setPath  # # set to python path for smodels
from smodels.theory import slhaDecomposer
from smodels.tools.physicsUnits import fb, GeV, addunit, rmvunit
from smodels.experiment import smsAnalysisFactory, smsHelpers
from smodels.theory.theoryPrediction import theoryPredictionFor
from smodels_tools.tools.databaseBrowser import Browser
import logging
import argparse
import os
import types
import ROOT
import sys

logger = logging.getLogger(__name__)


class GridData(object):
    
    def __init__(self, topology, analysis, slha):
        self.slha = slha
        self.topoName = topology
        self.anaName = analysis
        self.ana = self._analysesList[0]
        self.predictions = self._predictions   
        self._removeUnits = True
        if self.predictionInfo > 1:
            logger.error('There are more then one theoretical predictions!')
            sys.exit()
     
    @property
    def removeUnits(self):
        """Tells if all the units will be removed or not.
        
        """
        return self._removeUnits
        
    @removeUnits.setter
    def removeUnits(self, boolean):
        """Switch for removal of units.
        
        """
        if not bool(boolean):
            logger.warning('Units will NOT be removed!')
        self._removeUnits = bool(boolean)
    
    @property
    def _smsTopoList(self):
        sigmacut = 0.000001 * fb
        smsTopoList = slhaDecomposer.decompose(self.slha, sigmacut, \
        doCompress = False, doInvisible = False)
        #smsTopoList.printout()
        return smsTopoList
        
    @property
    def _analysesList(self):
        return smsAnalysisFactory.load(analyses = self.anaName, topologies = self.topoName)
        
    @property
    def analysisInfo(self):
        """Gives all the information about the analysis.
        This is meant for debugging.
        
        """
        analysis = self.ana
        print ("========================================================")
        print ("Analysis Name:", analysis.label.split(":")[0])
        print ("Analysis Topology:", analysis.label.split(":")[1])
        print ("Analysis Sqrts:", analysis.sqrts)
        print ("Analysis conditions:", analysis.conditions)
        print ("Analysis constraint:", analysis.constraint)
        print ("========================================================")
    
    @property
    def topologyInfo(self):
        """Gives all the information about the topology.
        This is meant for debugging.
        
        """
        for (i, topo) in enumerate(self._smsTopoList):
            print ("=========================================================")
            for j, el in enumerate(topo.elementList):
                print('Element: ', el)
            print ("=========================================================")    
    
    @property
    def _predictions(self):
        theoryPredictions = theoryPredictionFor(self.ana, self._smsTopoList)
        if theoryPredictions:
            theoryPredictions.printout()
        else:
            logger.error('There are no theoretical predictions!')
        return theoryPredictions   
        
    @property
    def predictionInfo(self):
        """Gives all the information about the theoretical predictions.
        This is meant for debugging.
        
        """
        count = 0
        if not self.predictions:
            return None
        for prediction in self.predictions:
            logger.debug('Analysis: %s' %prediction.analysis.label.split(":")[0])
            logger.debug('Topology: %s' %prediction.analysis.label.split(":")[1])
            logger.debug('Energy: %s' %prediction.analysis.sqrts)
            logger.debug ('Values: %s'%prediction.value[0].value)
            logger.debug('Conditions: %s' %prediction.conditions)
            logger.debug('Maximum conditions: %s' %prediction.getmaxCondition())
            logger.debug('Masses: %s' %prediction.mass)
            logger.debug('UpperLimit: %s' %prediction.analysis.getUpperLimitFor(prediction.mass))
            count += 1
        logger.debug('Total number of predictions: %s' %count)
        return count
        
    @property
    def massMother(self):
        """Mass of the mother particle.
        
        """
        if not self.predictions:
            return None
        for prediction in self.predictions:
            mass = prediction.mass[0][0]
        if not self.removeUnits:
            return mass
        return rmvunit(mass, 'GeV')
            
    @property
    def massLSP(self):
        """Mass of the lightest SUSY particle.
        
        """
        if not self.predictions:
            return None
        for prediction in self.predictions:
            mass = prediction.mass[0][-1]
        if not self.removeUnits:
            return mass
        return rmvunit(mass, 'GeV')
            
    @property
    def experimentalCondition(self):
        """Analysis condition, that has to be fulfilled.
        
        """
        if not self.predictions:
            return None
        for prediction in self.predictions:
            for key in prediction.conditions:
                return prediction.conditions[key]
                
    @property
    def theoreticalCondition(self):
        """Maximum condition, that should always be 0.0 for simplified models.
        
        """
        if not self.predictions:
            return None
        for prediction in self.predictions:
            return prediction.getmaxCondition()
                
    @property
    def experimentalUpperLimit(self):
        """Experimental upper limit for the cross section.
        
        """
        if not self.predictions:
            return None
        for prediction in self.predictions:
            eul = prediction.analysis.getUpperLimitFor(prediction.mass)
        if not self.removeUnits:
            return eul
        return rmvunit(eul, 'fb')
            
    @property
    def theoreticalUpperLimit(self):
        """Theoretical upper limit for the cross section.
        
        """
        if not self.predictions:
            return None
        for prediction in self.predictions:
            tul = prediction.value[0].value
        if not self.removeUnits:
            return tul
        return rmvunit(tul, 'fb')
        
def main():
    """Handles all command line options, as:
    topology, analysis, directory, base, loglevel, ...
    Produces the grid data file and adds some meta data.
    
    """
    argparser = argparse.ArgumentParser(description = \
    'Produces the grid data for smodels validation plots')
    argparser.add_argument ('-b', '--Base', \
    help = 'set path to base-directory of smodels-database \n \
    - default: /afs/hephy.at/user/w/walten/public/sms/', \
    type = types.StringType, default = '/afs/hephy.at/user/w/walten/public/sms/')
    argparser.add_argument ('-a', '--analysis', \
    help = 'analysis that should be validated - default: SUS12028',\
    type = types.StringType, default = 'SUS12028')
    argparser.add_argument ('-t', '--topology', \
    help = 'topology that should be validated - default: T1',\
    type = types.StringType, default = 'T1')
    argparser.add_argument ('-o', '--order', \
    help = 'perturbation order (LO, NLO, NLL) - default: NLL', \
    type = types.StringType, default = 'NLL')
    argparser.add_argument ('-d', '--directory', \
    help = 'directory the data file should be stored in - default: ./gridData', \
    type = types.StringType, default = './gridData')
    argparser.add_argument ('-blog', '--browserVerbosity',\
    help = 'set browser-verbosity - default: ERROR', \
    type = types.StringType, default = 'error')
    argparser.add_argument ('-n', '--events',\
    help = 'set number of events - default: 10000', \
    type = types.IntType, default = 10000)
    args = argparser.parse_args()

    smsHelpers.base = args.Base
    browser = Browser(args.Base)
    browser.verbosity = args.browserVerbosity
    topology = args.topology
    analysis = args.analysis
    targetPath = getTarget(args.directory)
    events = args.events
    order = args.order
    expRes = browser.expResult(analysis, topology)
    expAna = expRes.expAnalysis
    expTopo = expRes.expTopology
    print ("========================================================")
    print('Producing the grid data file')
    print('Topology: ', topology)
    print('Analysis: ', analysis)
    print('Using database: ', args.Base)
    print('Store file in: ', targetPath)
    print ("========================================================")
    
    fileName = '%s-%s-%s-%s.dat' %(topology, analysis, events, order)
    f = checkFile(targetPath + '/' + fileName)
    outFile = open(f, 'w')
    count = 0
    slhaPath = '../slha/%s_%s_%s_slhas' %(topology, events, order)
    if not os.path.exists(slhaPath):
        logger.error('There are no slha-files for %s with %s events and order %s! \n \
        Run slhaCreator.py first: ./slhaCreator.py -h!' %(topology, events, order))
        sys.exit()
    fileList =  os.listdir(slhaPath)
    slhaList = sorted(fileList, key = lambda slha: int(slha.split('_')[1]))
    for slha in slhaList:
        data = GridData(topology, analysis, slhaPath + '/' + slha)
        massMother = data.massMother
        massLSP = data.massLSP
        tUL = data.theoreticalUpperLimit
        eUL = data.experimentalUpperLimit
        cond = data.theoreticalCondition
        if not massMother:
            massMother = slha.split('_')[1].strip()
            massLSP = slha.split('_')[2].strip()
        if bool(data.theoreticalCondition):
            logger.warning('Condition %s not satisfied! degree of violation: %s' \
            %(data.experimentalCondition, data.theoreticalCondition))
        print('%s  %s  %s  %s %s' \
        %(massMother, massLSP, tUL, eUL, cond), file = outFile)
        count += 1
    print('#END', file = outFile)
    metaData = writeMetaData(expRes, args.order, fileName)
    for key in metaData:
        print(key, metaData[key], file = outFile)
    print ('Worte %s lines of grid data to file %s!' %(count, fileName))
    outFile.close()    

def writeMetaData(expRes, order, fileName):
    """Writes all the meta data (e.g. root tag, name of output-file, ...)
    :returns: dictionary
    
    """
    expAna = expRes.expAnalysis
    expTopo = expRes.expTopology
    metaData = {}
    decay = ''
    prettyName = ''
    sqrts = ''
    if expTopo.decay: decay = expTopo.decay
    if expAna.prettyName: prettyName = expAna.prettyName.replace('\\', '#')
    if expAna.sqrts: sqrts = '%s TeV' %expAna.sqrts
    if expAna.pas: pas = expAna.pas
    metaData['decay:'] = '%s' %decay
    metaData['analysis:'] = '%s, %s, %s, %s' %(pas, prettyName, sqrts, order)
    metaData['outFile:'] = fileName.replace('.dat', '.png') 
    exclName = ''
    official = ''
    if expRes.exclusionLine():
        exclName = expRes.exclusionLine().GetName()
    if expAna.publishedData or expAna.isPublished:
        official = 'official exclusion line'
    metaData['rootTag:'] = '%s: %s' %(exclName, official)
    return metaData
   

    
    
def getTarget(path):
    """Checks if the target directory already exists and creates it if not.
    
    """
    
    if os.path.exists(path):
        logger.info('Target %s already exists.' %path)
        return path
    
    os.mkdir(path)
    logger.info('Created new directory: %s' %path) 
    return path

def checkFile(path):
    """Checks if the data file already exists.
    If the file already exists, the user can decide wether to remove it, 
    or to exit the script.
    
    """
    if os.path.exists(path):
        print('File %s already exists!' %path)
        while True:
            userInput = raw_input('Replace old file? [y/n]:  ')
            if userInput == 'n':
                sys.exit()
            if userInput == 'y':
                os.remove(path)
                return path
    return path
    
if __name__ == '__main__':
    main()  