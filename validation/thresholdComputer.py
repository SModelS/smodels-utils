#!/usr/bin/env python

"""
.. module:: thresholdComputer
   :synopsis: Derives the thresholds and the bin widths for given topology.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

from __future__ import print_function
import setPath  # # set to python path for smodels
import sys
from smodels_tools.tools.databaseBrowser import Browser
import logging
import os
import types

logger = logging.getLogger(__name__)

class Threshold(object):
    
    def __init__(self, topology, browserObject):
        """Uses the given browser object to retrieve all upper limit histogram 
        dictionaries knowen for this topology. 
        :param topology: topology the slha-files should be preoduced for
        :param browserObject: instance of the class Browser
        
        
        """
        
        if not isinstance(browserObject, Browser):
            logger.error('Parameter browserObject must be type browser, %s given'\
            %type(browserObject))
            sys.exit()            
        self._browser = browserObject
        self.topo = self._browser.expTopology(topology)
        self.thresholds = self._thresholds
        self.motherMasses = self._massList('mother')
        self.lspMasses = self._massList('lsp')
        self.d = self._maxDelta()
    
    
    
    @property    
    def _thresholds(self):
        """Retrieves all the maximal and minimal masses for the mother particle
        and the LSP from upper limit dictionaries for all the experimental 
        results available. Derives the corresponding bin width.
        :returns: {'mother': [thresholdDicts], 'lsp': [thresholdDicts]}
        
        """
        thresh = {}
        thresh['mother'] = []
        thresh['lsp'] = []
        thresh['d'] = []
        #for a in random.sample(set(self.topo.analyses), 4):
        analyses = self.topo.analyses
        logger.info('Computing mass thresholds for topology %s using analyses: \n \
        %s' %(self.topo.name, analyses))
        for a in analyses:
            if self._browser.expAnalysis(a).sqrts != 8.0:
                continue
            ulDict = self._browser.expResult(a, self.topo.name).upperLimitDict()
            if not ulDict: continue
            mM = []
            lspM = []
            for mother in ulDict:
                if not mother: continue
                if not ulDict[mother]: continue
                mM.append(mother)
                
                for lsp in ulDict[mother]:
                    if not lsp in lspM:
                        lspM.append(lsp)
                if not lspM: continue        
            lspM.sort()
            thresholdDictLsp = self._thresholdDict(lspM)
            thresh['lsp'].append(thresholdDictLsp)
            mM.sort()
            thresholdDictMother = self._thresholdDict(mM)
            thresh['mother'].append(thresholdDictMother)
            thresh['d'].append(self._delta(thresholdDictMother['min'],thresholdDictMother['step'],ulDict))
        return thresh
        
    def _delta(self, minMother, step, ulDict):
        """Derives the lsp intercept
        
        """
        
        lspMassMax = -1000.
        for lspMass in ulDict[minMother]:
            if lspMass > lspMassMax: lspMassMax = lspMass
        return lspMassMax-minMother+step
        
    def _thresholdDict(self, masses):
        """Derives the thresholds and the step width for a given list of masses.
        :param masses: list of mass values for either mother particle or LSP
        :returns: {min: lower threshold, max: upper threshold, step: step width}
        
        """
        particleThreshold = {}
        particleThreshold['min'] = min(masses)
        particleThreshold['max'] = max(masses)
        
        steps = []
        for i in range(len(masses)-1):
            step = abs(masses[i] - masses[i+1])
            if step:
                if steps.count(step) == 0:
                    steps.append(step)
        for step in steps:
            step += step
        particleThreshold['step'] = int(float(step) / float(len(steps)))
        return particleThreshold
    
    def _maxMass(self, particle):
        """Derives the maximal mass for given particle.
        :param particle: 'mother' or 'lsp'
        
        """
        maxM = 0.0
        for particleDict in self.thresholds[particle]:
            if int(particleDict['max']) > int(maxM):
                maxM = particleDict['max']
        if particle == 'mother' and self.topo.name == 'TChiWZoff':
            maxM = 250
        if particle == 'lsp' and self.topo.name == 'TChiWZoff':
            maxM = 200
        return maxM
        if particle == 'mother' and self.topo.name == 'TChiWZon':
            maxM = 400
        if particle == 'lsp' and self.topo.name == 'TChiWZon':
            maxM = 300
        return maxMass
        
    def _minMass(self, particle):
        """Derives the minimal mass for given particle.
        :param particle: 'mother' or 'lsp'
        
        """
        minM = 1000000.0
        for particleDict in self.thresholds[particle]:
            if int(particleDict['min']) < int(minM):
                minM = particleDict['min']
        if particle == 'mother' and self.topo.name == 'T1tttt':
            if minM < 400: minM = 400
        if particle == 'mother' and self.topo.name == 'T2':
            if minM < 200: minM = 200#
        if particle == 'mother' and self.topo.name == 'T1':
            if minM < 200: minM = 200
        if particle == 'mother' and self.topo.name == 'T2bb':
            if minM < 100: minM = 100
        return minM
        
    def _stepWidth(self, particle):
        """Derives the minimal bin width for given particle.
        :param particle: 'mother' or 'lsp'
        
        """
        
        minStep = 1000000.0
        for particleDict in self.thresholds[particle]:
            if int(particleDict['step']) < int(minStep):
                minStep = particleDict['step']
        if minStep < 12.5: minStep = 12.5
        if self.topo.name == 'T1tttt': minStep = 25.
        if 'TChiWZ' in self.topo.name: minStep = 10
        return minStep
    
    def _maxDelta(self):
        """Derives the maximal lsp intercept
        
        """
        
        dMax = -1000.
        for d in self.thresholds['d']:
            if d > dMax: dMax = d
        dDefoult = 0
        if self.topo.name == 'T1tttt' or self.topo.name == 'T2tt':
            dDefoult = -200
        if self.topo.name == 'TChiWZon' or self.topo.name == 'TChiWZ':
            dDefoult = -100
        if dMax > dDefoult: dMax = dDefoult  
        return dMax
        
    def _massList(self, particle):    
        """Creates a list of mass values for the given particle.
        :param particle: 'mother' or 'lsp'
        
        """
        massList = []
        maxMass = self._maxMass(particle)
        minMass = self._minMass(particle)
        step = self._stepWidth(particle)
        logger.info('Creating list of %s masses from %s to %s in steps of %s'\
        %(particle, minMass, maxMass, step))
        mass = minMass
        while mass <= maxMass:
            massList.append(mass)
            mass = mass + step
        return massList

def main():
    threshold = Threshold('TChiWZoff',Browser('../../smodels-database'))
    print('motherMasse: %s' %threshold.motherMasses)
    print('lspMasse: %s' %threshold.lspMasses)
    print('minLSB: %s maxLSB %s' %(min(threshold.lspMasses), max(threshold.lspMasses)))
    print('minMother: %s maxMother %s' %(min(threshold.motherMasses), max(threshold.motherMasses)))
    print('d; %s' %threshold.d)

    
if __name__ == '__main__':
    main()
    