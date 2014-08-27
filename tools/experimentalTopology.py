#!/usr/bin/env python

"""
.. module:: experimentalObjects
   :synopsis: Hold the ExpTopology object retrieved from smodels-database\ 
   in order to produce summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""    

import ROOT
import logging, os, types
import setPath
import sys
import databaseBrowser

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

class ExpTopology(object):
    """Contains all topology-specific information (e.g. analyses and runs that 
    contain this topology, category, particles resp. productionmode, ...)
    
    """
    def __init__ (self, topology, topoDict):
        self._name = topology
        self._topoDict = topoDict
        self._runs = [key for key in self._topoDict]
        self._analyses = self._anas
        self._verbosity = 'error'
     
    @property
    def verbosity(self):
        """Tells the level the logger is set to.
        
        """
        return self._verbositya
        
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
        
    @property    
    def _anas(self):
        """Extracts all the analyses given as inner keys of nested topoDict.
        
        """
        anas = []
        for r in self._runs:
            for a in self._topoDict[r]:
                anas.append(a)
        return anas
        
    @property    
    def _category(self):
        """Takes the category for this topology from every info.txt, 
        compairs them and returns the string if they are all the same. 
        Raises an ERROR and returns None if they are not!
        
        """
        
        cats = []
        for run in self._topoDict:
            for ana in self._topoDict[run]:
                try:
                    category = self._topoDict[run][ana][0][self._name]
                    if cats.count(category) == 0:
                        cats.append(category)
                    if cats and cats.count(category) == 0:
                        logger.error('There are different categories for topology %s! \
                        Please check the database entry %s-%s!' %(self._name, run, ana))
                except KeyError:
                    logger.warning('The category for %s is missing! Please \
                    check the database entry %s-%s!' %(self._name, run, ana))
        logger.debug('List of categories: %s.' %cats)
        if len(cats) == 0:
            logger.error('Could not get any category information for %s.' % \
                    self._name )
            return None
        if len(cats) == 1:
            return cats[0]
        
        logger.error('Unable to get consistent category for topology %s: %s' % \
                      (self._name,cats) )
        return None
    
    @property    
    def _constraints(self):
        """Takes the constraints for this topology from every info.txt, 
        returns a list containing all available constraints.
        
        """
        
        const = []
        for run in self._topoDict:
            for ana in self._topoDict[run]:
                try:
                    c = self._topoDict[run][ana][1][self._name]
                    if const.count(c) == 0:
                        const.append(c)
                except KeyError:
                    logger.warning('The constraint for %s is missing! \
                    Please check the database entry %s-%s!' %(self._name, run, ana))
        logger.debug('List of constraints: %s.' %const)
        return const
        
        logger.error('Unable to get category for topology %s!' %self._name)
        return None
        
    @property    
    def name(self):
        return self._name
    
    @property
    def analyses(self):
        return self._analyses
    
    # ### FIX ME doesn't work this way!
    #@property
    #def experimentAnalyses(self):
        #if self.analyses:
            #anas = [ExpAnalysis(a) for a in self.analyses]
        #return anas
    
    @property
    def runs(self):
        return self._runs
        
    @property
    def category(self):
        return self._category
      
    @property
    def constraints(self):
        return self._constraints
        
    #@property
    #def analysesNames(self, run = None):
        #"""Retrieves the names (as strings) of all analyses existing for 
        #this topology. Returns a list of names for one given run, 
        #or a dictionary with runs as keys.
        
        #"""
        #if not run:
            #anas = {}
            #logger.warning('no run was given, therefore trying all available \
            #runs %s and returning dictionary!' %self._runs)
            #for r in self._runs:
                #if getAllAnalyses(run = r, topology = self._name):
                    #anas[r] = [a for a in getAllAnalyses(run = r, \
                    #topology = self._name)]
            #return anas
        #return getAllAnalyses(run = run, topology = self._name)
    
    def _slackExpTopologyName(self):
        """Bypassing case sensitivity
        # ### FIX ME: doesn't know much at the moment.
        """
        if any(c in self._name for c in ['w', 'W', 'z', 'Z']):
            return self._name.replace("W","w").replace("Z","z" )
        return self._name
    
        
    def _searchDecayDict(self):
        """Searches for topology name in descriptions.decay
        :returns: dictionary entry without formating 
        
        """
        if decays.has_key(self._name):
            logger.info('found decay for topology %s' %self._name)
            return decays[self._name]
        if decays.has_key(self._slackExpTopologyName()):
            logger.info('found decay for topology %s with \
            slack name %s' %(self._name, self._slackExpTopologyName()))
            return decays[self._slackExpTopologyName()]
        logger.warning('no decay found for topology %s' %self._name)
        return None        

    @property
    def decay(self):
        """:returns: decay as string, formated for ROOT.TLatex
        
        """
        
        decay = self._searchDecayDict()
        if isinstance(decay,str): return self._latexDecay(decay)
        if isinstance(decay,list):
            i = 1
            lenght = len(decay)
            decayString =''
            for line in decay:
                if i != 1: decayString = decayString + '{'
                if i != lenght:
                    decayString = decayString +  '#splitline{' + self._latexDecay(line) 
                if i == lenght:
                    decayString = decayString + self._latexDecay(line)
                decayString = decayString + '}'
                if i == lenght:
                    decayString = decayString + '}'*(i-2)
                i += 1
            return decayString
            
    def _latexDecay(self, decayString):
        """translate decay description as given in decays dictionary
        to a string readable by ROOT.TLatex object
        
        """
        for key, value in prettySUSYParticle.items():
            decayString = self._latexParticle(decayString,key,value)
        for key, value in prettySMParticle.items():
            decayString = self._latexParticle(decayString,key,value)
        for key, value in highstrings.items():
            decayString = decayString.replace(key,value)
        for key, value in lowstrings.items():
            decayString = decayString.replace(key,value)
        decayString = decayString.replace('-->','#rightarrow')
        return decayString
        
    def _latexParticle(self,decayString,key,value):
        """translate particle description as given in decays dictionary
        to a string readable by ROOT.TLatex object
        
        """
        decayString = decayString.replace('anti' + key + ' ','#bar{' + value + '}')
        decayString = decayString.replace(key + ' ',value)
        decayString = decayString.replace(key + '_',value + '_')
        decayString = decayString.replace(key + '^',value + '^')
        return decayString
        
    @property
    def motherParticle(self):
        """ :returns: motherParticle in simple format as string or None
        
        """
        # ### FIX ME: This is not done yet! 
        decay = self._searchDecayDict()
        if isinstance(decay,list): decay = decay[0]
        motherPart = decay.split('-->')[0]
        motherPart = motherPart.strip()
        if motherPart == 'gluino': return 'g'
        if motherPart == 'squark': return 'q'
        if motherPart == 'stop': return 't'
        if motherPart == 'sbottom': return 'b'
        if motherPart == 'slepton': return 'l'
        if 'chargino' in motherPart and 'neutralino' in motherPart:
            return 'c0cpm'
        if 'chargino' in motherPart and not 'neutralino' in motherPart:
            return 'cpm'
        if not 'chargino' in motherPart and 'neutralino' in motherPart:#
            return 'c0'
        logger.error('could not identify motherParticle for  %s' %self._name)
        return None
        
    @property
    def shortdecay(self):
        """:returns: short version of decay as string
        
        """
        
        decay = self._searchDecayDict()
        if isinstance(decay,list): decay = decay[0]
        decaySteps = decay.split('-->')
        if len(decaySteps) == 2: return self._latexDecay(decay)
        decay = decaySteps[0] + '--> '
        lsp = 'lsp '*(len(decay.split())-1)
        decaySteps = decaySteps[1:]
        for decayStep in decaySteps:
            #decayStep.replace('(','')
            #decayStep.replace(')','')
            #decayStep.replace('|','')
            for particle in prettySMParticle:
                if particle in decayStep: decay = decay + particle + ' '
        decay = decay + lsp
        return self._latexDecay(decay)
        
    @property
    def intermediateParticles(self):
        """:returns: dictionary with intermadieted particles
        
        """
        particles = []
        decays = self._searchDecayDict()
        if isinstance(decays,str): decays = [decays]
        for decay in decays:
            decay = decay.split('-->')
            decay = decay[1:-1]
            if not decay: continue
            for expression in decay:
                expression = expression.replace('(','')
                expression = expression.replace(')','')
                expression = expression.replace('|','')
                expression = expression.replace('lsp','')
                [particles.append(particle.strip()) for particle in expression.split(' ')]
        if not particles: return
        interParticles = []
        for particle in particles:
            for sparticle in prettySUSYParticle:
                if sparticle in particle and not particle in interParticles: 
                    interParticles.append(particle)
        return interParticles
        
                
            
        
        
        
    #def getPrettyName       # particles resp. productionmode
    #def treatMasssplitting
    #def setAnalyses
    #def refreshAnalyses

# dictionary containing all decays for the different topologies.
# special format expected: 
# -supported particle names can be found in the dictionaries prettySMParticels and 
#  prettySUSYParticle
# -supported postfixes can be found in the dictionaries highstrings and lowstrings
# -prefix "anti" for anti-particles supported
# -space is expected to end a particle description (eg: chargino^pm_2 )
# -if there is more then one possible decay for one topology a list with decays is expected
# -neutrino, lepton, neutralion, slepton means fisrt 2 genertions
# -Neutrino, Lepton, Neutralion, sLepton means all 3 genertions

decays = { 
    'T1': 'gluino  --> quark antiquark  lsp ' ,
    'T1bbbb': 'gluino  --> bottom antibottom  lsp ', 
    'T1tttt': 'gluino  --> top antitop  lsp ',
    'T1gg':'gluino  --> quark antiquark (neutralino_2 --> photon lsp )', 
    'T1lg':'gluino  --> quark antiquark (neutralino_2  --> photon lsp |chargino^pm  --> w lsp )', 
    'T1lnu':'gluino  --> quark antiquark (chargino^pm --> lepton^pm neutrino  lsp )', 
    'T1lh':'gluino  --> quark antiquark  neutralino_2 neutralino_2  --> lepton^p lepton^m lsp ', 
    'T2':'squark  --> quark lsp ',
    'T2FVttcc': 'stop  --> charm lsp ',
    'T2llnunubb': 'stop  --> lepton neutrino bottom lsp ',
    'T2bb':'sbottom  --> bottom lsp ', 
    'T2bw':'stop  --> bottom w lsp ',
    'T2ttww': 'sbottom  --> top w lsp ',
    'T2tt': 'stop  --> top lsp ', 
    'T3w': 'gluino --> quark antiquark (chargino^pm_1 --> w lsp | lsp )' ,
    'T3wb':'gluino  --> bottom antibottom (w )lsp ', 
    'T3lh':'gluino  --> quark antiquark (neutralino_2 --> lepton^p lepton^m lsp | lsp )',
    'T3tauh':'gluino  --> quark antiquark (neutralino_2 --> tauon tauon lsp | lsp )', 
    'T5WW':'gluino  --> quark antiquark (chargino^pm_1 --> w lsp )',
    'T5wg':'gluino  --> quark antiquark (neutralino_2 --> photon lsp | chargino^pm_1 --> w lsp )',
    'T5WH':'gluino  --> quark antiquark (neutralino_2 --> higgs lsp | chargino^pm_1 --> w lsp )',
    'T5gg':'gluino  --> quark antiquark (neutralino_2 --> photon lsp )',
    'T5lnu':'gluino  --> quark antiquark (chargino^pm --> lepton^pm neutrino lsp )',
    'T5ZZ':'gluino  --> quark antiquark (neutralino_2 --> z lsp )',
    'T5ZZInc':'neutralino_2 --> z lsp ',
    'T5zzgmsb':'gluino --> quark antiquark (neutralino_2 --> z lsp )', 
    'T5tttt':'gluino  --> top (stop --> top antitop lsp )',
    'T6ttww': 'sbottom  --> top (chargino^pm_1 --> w lsp )',
    'T6ttHH': 'stop  --> top higgs lsp ',
    'T6ttzz': 'stop_2  --> z (stop_1 --> top lsp ) ',
    'T6bbWW':'stop  --> bottom (chargino^p --> w lsp )',
    'T6bbWWoff':'stop  --> bottom (chargino^p --> w lsp )',
    'T6bbZZ':'sbottom  -->  bottom (neutralino_2 --> z lsp )',
    'T7btW':'gluino  --> bottom top w lsp ',
    'T7btbtWW':'gluino  --> bottom (sbottom --> top (chargino^pm --> w lsp ))',
    'TChizz':'neutralino_3 neutralino_2  --> z z lsp lsp ',
    'TChiSlep':'neutralino_2 chargino^pm_1  --> lepton lepton lepton neutrino lsp lsp ',
    'TChiNuSlep':'neutralino_2 chargino^pm_1  --> lepton lepton lepton neutrino lsp lsp ',
    'TChizz':'neutralino_3 neutralino_2  --> z z lsp lsp ',
    'TChiwz':'chargino^pm neutralino_2  --> w z lsp lsp ',
    'TChiWZon':'chargino^pm neutralino_2  --> w z lsp lsp ',
    'TChiWZoff':'chargino^pm neutralino_2  --> w z lsp lsp ',
    'TChiChipmSlepSlep':'neutralino_2 chargino^pm_1  --> lepton (slepton --> lepton lsp ) | neutrino (slepton --> lepton lsp )',
    'TChiChipmStauStau':'neutralino_2 chargino^pm_1  --> tauon (stauon --> tauon lsp ) | neutrino (stauon --> tauon lsp )', 
    'TChiChipmSlepL':[
    'neutralino_2 chargino^pm_1  --> Lepton (sLepton --> Lepton lsp ) | Neutrino (sLepton --> Lepton lsp )' ,
    'neutralino_2 chargino^pm_1  --> Lepton (sLepton --> Lepton lsp ) | Lepton (sNeutrino --> Neutrino lsp )',
    'neutralino_2 chargino^pm_1  --> Neutrino (sNeutrino --> Neutrino lsp ) | Lepton (sNeutrino --> Neutrino lsp )' ,
    'neutralino_2 chargino^pm_1  --> Neutrino (sNeutrino --> Neutrino lsp ) | Neutrino (sLepton --> Lepton lsp )'
    ], 
    'TChiChipmStauL':[
    'neutralino_2 chargino^pm_1  --> tauon (stauon --> tauon lsp ) | neutrino (stauon --> tauon lsp )',
    'neutralino_2 chargino^pm_1  --> tauon (stauon --> tauon lsp ) | tauon (stauon --> neutrino lsp )',
    'neutralino_2 chargino^pm_1  --> neutrino (sneutrino --> neutrino lsp ) | tauon (sneutrino --> neutrino lsp )',
    'neutralino_2 chargino^pm_1  --> neutrino (sneutrino --> neutrino lsp ) | neutrino (stauon -->  lsp )'
    ], 
    'TChiChipmHW':'neutralino_2 chargino^pm_1  --> w lsp higgs lsp ', 
    'TChiChipmSlepStau':'neutralino_2 chargino^pm_1  --> Lepton (slepton --> Lepton lsp ) | neutrino (stauon --> tauon lsp )', 
    'TChiChipmStauStau':'neutralino_2 chargino^pm_1  --> tauon (stauon --> tauon lsp ) | neutrino (stauon --> tauon lsp ) ',
    'TChipChimSlepSnu':[
    'chargino^pm chargino^mp  --> Lepton (sneutrino --> neutrino lsp ) | neutrino (slepton --> Lepton lsp )',
    'chargino^pm chargino^mp  --> Lepton (sneutrino --> neutrino lsp ) | Lepton (sneutrino --> neutrino lsp )',
    'chargino^pm chargino^mp  --> neutralino (slepton --> Lepton lsp ) | neutrino (slepton --> Lepton lsp )'
    ], 
    'TSlepSlep':'slepton  --> lepton lsp '
}

prettySMParticle = {
    'graviton':'#tilde{G}',         #graviton
    'photon': '#gamma',             #photon
    'gluon':'g',                    #gluon
    'w' : 'W',                  #W
    'z' : 'Z',                  #Z
    'higgs' : 'H',                  #higgs
    
    'quark': 'q',           #quark
    'up': 'u',           #up
    'down': 'd',           #down
    'charm': 'c',           #charm
    'strange': 's',           #strange
    'top': 't',           #top
    'bottom': 'b',           #bottom
    
    'lepton' : 'l',             #leptonsupot (first 2 generations)
    'Lepton' : 'l',             #leptonsupot (all 3 generations)
    'electron' : 'e',               #electron
    'muyon' : '#mu',            #myon
    'tauon' : '#tau',  #tauon
    
    'neutrino' : '#nu',                     #neutrino (first 2 generations)
    'Neutrino' : '#nu',                     #neutrino (all 3 generations)
    'elektron-neutrino' : '#nu_{e}',               #elektron-neutrino
    'myon-neutrino' : '#nu_{#mu}',            #myon-neutrino
    'tauon-neutrino' : '#nu_{#tau}',          #tauon-neutrino
}

prettySUSYParticle = {
    'lsp' : '#tilde{#chi}^{0}_{1}',  # lightesd SUSY particle
    'neutralino' : '#chi^{0}',      #neutralino
    'chargino' : '#chi',            #Chargino
    'gravitino':'G',              #gravitino
    'photino':'#tilde{#gamma}',   #photino
    'gluino': '#tilde{g}',        #gluino
    'wino' : '#tilde{W}',       #Wino
    'zino' : '#ti:lde{Z}',       #Zino
    'higgsino' : '#tilde{H}',       #higgsino
    
    'squark': '#tilde{q}',  #squarkfound in
    'sup': '#tilde{u}',  #sup
    'sdown': '#tilde{d}',  #sdown
    'scharm': '#tilde{c}',  #scharm
    'sstrange': '#tilde{s}',  #sstarnge
    'stop': '#tilde{t}',  #stop
    'sbottom': '#tilde{b}',  #sbottom
    
    'slepton' : '#tilde{l}',    #slepton (first 2 generations)
    'sLepton' : '#tilde{l}',    #slepton (all 3 generations)
    'selectron' : '#tilde{e}',      #selectron
    'smyon' : '#tilde{#mu}',   #smyon
    'stauon' : '#tilde{#tau}', #stauon
    
    'sneutrino' : '#tilde{#nu}',            #sneutrino (first 2 generations)
    'sNeutrino' : '#tilde{#nu}',            #sneutrino (all 3 generations)
    'elektron-sneutrino' : '#tilde{#nu}_{e}',      #elektron-sneutrino
    'myon-sneutrino' : '#tilde{#nu}_{#mu}',   #myon-sneutrino
    'tauon-sneutrino' : '#tilde{#nu}_{#tau}', #tauon-sneutrino  
}

highstrings = {
    '^0' : '^{0}',
    '^pm' : '^{#pm}',
    '^mp' : '^{#mp}',
    '^p' : '^{+}',
    '^m' : '^{-}',
}

lowstrings = {
    '_1' : '_{1}',
    '_2' : '_{2}',
    '_3' : '_{3}',
    '_4' : '_{4}',
}
            