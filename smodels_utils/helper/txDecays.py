#!/usr/bin/env python

"""
.. module:: txNames
   :synopsis: Holds a dictionary with decays for every txName and a
              small object to read them.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""

from __future__ import print_function

import logging
from smodels_utils.helper.prettyDescriptions import decayDict as decays
from smodels_utils.helper.prettyDescriptions import highstrings,lowstrings,prettySMParticle,prettySUSYParticle,getIntermediates


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)


class TxDecay(object):
    def __init__(self,txName):
        self._name = txName

    def __str__(self):
        return self._name

    def __nonzero__(self):
        return self._name in decays

    @property
    def doubledDecays(self):
        compareDict = {key: value for (key, value) in decays.iteritems()\
        if not self.name == key}
        doubled = []
        for compTxName, compDecay in compareDict.items():
        #for compTxName, compDecay in compareDict.iteritems():
            if decays[self.name] == compDecay:
                doubled.append(compTxName)
        return doubled

    @property
    def name(self):
        return self._name

    @property
    def shortdecay(self):
        return self._shortdecay

    @property
    def decay(self):
        return self._decay

    @property
    def motherParticle(self):
        return self._motherParticle

    @property
    def intermediateParticles(self):
        return self._intermediateParticles


    def _slackExpTopologyName(self):
        """Bypassing case sensitivity
        # ### FIX ME: doesn't know much at the moment. Is this still needed?
        """
        if any(c in self._name for c in ['w', 'W', 'z', 'Z']):
            return self._name.replace("W","w").replace("Z","z" )
        return self._name

    def _searchDecayDict(self):
        """Searches for topology name in descriptions.decay
        :returns: dictionary entry without formatting

        """
        if self._name in decays.keys():
            logger.info(f'found decay for topology {self._name}')
            return decays[self._name]
        if self._slackExpTopologyName() in decays.keys():
            logger.info('found decay for topology %s with \
            slack name %s' %(self._name, self._slackExpTopologyName()))
            return decays[self._slackExpTopologyName()]
        logger.warning(f'no decay found for topology {self._name}')
        return None

    @property
    def _decay(self):
        """:returns: decay as string, formatted for ROOT.TLatex

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
        """Translates decay description as given in decays dictionary
        to a string readable by ROOT.TLatex object.

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
        """Translates particle description as given in decays dictionary
        to a string readable by ROOT.TLatex object.

        """
        decayString = decayString.replace('anti' + key + ' ','#bar{' + value + '}')
        decayString = decayString.replace('anti' + key + '* ','#bar{' + value + '}*')
        decayString = decayString.replace(key + ' ',value)
        decayString = decayString.replace(key + '_',value + '_')
        decayString = decayString.replace(key + '^',value + '^')
        decayString = decayString.replace(key + '* ',value + '*')
        return decayString

    @property
    def _motherParticle(self):
        """ :returns: mother particle in simple format as string or None

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
        if motherPart == 'stau': return 'tau'
        if motherPart == 'stop_2': return 't2'
        if 'gluino' in motherPart and 'squark' in motherPart:
            return 'gq'
        if 'chargino' in motherPart and 'neutralino' in motherPart:
            return 'c0cpm'
        if 'chargino' in motherPart and not 'neutralino' in motherPart:
            return 'cpm'
        if not 'chargino' in motherPart and 'neutralino' in motherPart \
        and not 'neutralino_2' in motherPart and not 'neutralino_3' in motherPart:
            return 'c0'
        if  'neutralino_2' in motherPart and 'neutralino_3' in motherPart:#
            return 'c02c03'
        logger.error(f'could not identify mother particle for  {self._name}')
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
    def _intermediateParticles(self):
        """:returns: dictionary with intermediate particles

        """

        return getIntermediates(self._name)
