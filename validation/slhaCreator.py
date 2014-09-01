#!/usr/bin/env python


"""
.. module:: slhaCreator
   :synopsis: An iterator object returning slha-files for validation plots

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

from __future__ import print_function
import setPath
import logging
import sys
import os
from smodels.tools import xsecComputer
from smodels_tools.tools.databaseBrowser import Browser
from smodels_tools.tools.experimentalResults import ExpResult
from smodels.tools.physicsUnits import rmvunit, addunit
import random
from thresholdComputer import Threshold
import argparse
import types

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)


class SlhaFiles(object):
    """Creates slha-files and stores them via an __iter__ method.
    ### no intermediated mass supported
    ### no mass splitting for topology supported

    """
    
    def __init__(self, topology, browserObject, thresholdMotherMasses, \
    thresholdLSPMasses, d, condition, value, events = 1000, order = 'LO',unlink = True):
        """Creates a directory ./'topology'_slhas and stores all the slha-files
        for every point in the mass-plane.
        :param topology: topology the slha-files should be preoduced for
        :param browserObject: instance of the class Browser
        :param events: number of events for pythia simulation 'LO' or 'NLL' 
        :param order: order of perturbation theory as string
        :param condition: condition for mass of the intermediate particle as string 
        (only xvalue supported) 
        :param value: value for the condition as string
        
        
        """
        self._tempSlhaName = 'temp.slha'
        if not isinstance(browserObject, Browser):
            logger.error('Parameter browserObject must be type browser, %s given'\
            %type(browserObject))
            sys.exit()            
        self._browser = browserObject
        self.topo = self._browser.expTopology(topology)
        self._templateSlhaFile(topology)
        self._events = events
        self._sqrts = 8.0
        if not order in ['LO','NLO','NLL']:
            logger.error('%s is not a possible pertubation order' %(order))
            sys.exit()            
        self._order = order
        self.motherMasses = thresholdMotherMasses
        self.lspMasses = thresholdLSPMasses
        self.d = d
        self._unlink = unlink
        self._listOfInterPid = self._getPidCodeOfIntermediateParticle()
        self._listOfMotherPid = self._getPidCodeOfMother()
        if not condition in ['xvalue','x']:
            logger.error('Condition %s not supported' %condition)
            sys.exit()  
        if condition == 'xvalue':
            cond = ''
        else:
            cond = condition
        if value == '050':
            val = ''
        else:
            val = value
        self._extension = cond + val
        self.folder = '../slha/%s_%s_%s_slhas' %(topology + self._extension, events, order)
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            logger.info('Created new folder %s!' %self.folder)
        self._condition = condition
        self._interValue = self._setInterValue(value)
        
    def __del__(self):
        """remove temp.slha
        
        """
        
        os.system('rm ./%s' %self._tempSlhaName)

        
        
    def _setInterValue(self,value):
        """
        
        """
        try:
            float(value)
        except ValueError:
            logger.error('value for contion %s must be a number. Got: %s' %(self._condition,interValue))
            sys.exit() 
        if self._condition == 'xvalue':
            if value[:1] != '0':
                logger.error('value %s not allowed for contion %s' %(value,self._condition))
                sys.exit()  
            div = float('1' + (len(value)-1)*'0')
            interValue = float(value[1:])/div
            interValue = round(interValue,2)
            if not interValue >= 0. or not interValue <= 1.:
                logger.error('value for contion %s must be between 1 and 0. Got: %s' %(self._condition,interValue))
                sys.exit() 
            return interValue
        if self._condition == 'x':
            interValue == float(value)/100.
            interValue == interValue = round(interValue,2)
            return interValue
        return
        
    def __iter__(self):
        """Creates a slha-file named 'topology_motherMass_lspMass_order.slha and
        adds the masses. If the mother mass changes the cross sections are
        computed and also added to the slha-file.
        
        """
        logger.info('There are approximately %s points in the mass plane!' \
        %(int(len(self.motherMasses) * len(self.lspMasses) / 2.)))
        for motherMass in self.motherMasses:
            firstLoop = True
            for lspMass in self.lspMasses:
                if lspMass > motherMass + self.d: continue
                if self.topo.name == 'TChiWZoff':
                    if lspMass - motherMass < -80: continue
                fileName = self.topo.name + self._extension + '_' + \
                str(int(motherMass)) + '_' + str(int(lspMass)) + '_' + \
                self._order + '.slha'
                logger.info('mother mass: %s, lsp mass: %s' %(motherMass, lspMass)) 
                if self._condition == 'xvalue':
                    interMass = self._interValue * motherMass + (1 - self._interValue) * lspMass
                if self._condition == 'x':
                    interMass = self._interValue * lspMass
                slhaLines = self._setMass(motherMass, lspMass, interMass)
                if firstLoop:
                    self._delXsecFromFile()
                    self._addXsecsToFile()
                    firstLoop = False
                path = self.folder + '/' + fileName
                
                os.system('cp ./%s %s' %(self._tempSlhaName, path))
                yield path
                
                    
    def _addXsecsToFile(self):
        """Adds the xsecs to the slha file. First LO then NLO and finally NLL 
        are computed.
        # ### FIX ME: order NLO? does this make sens? We get NLO by adding a factor 1.2 to LO, right?
        
        """
        
        comment = "Nevts: " + str(self._events)
        xsecs = xsecComputer.computeXSec(self._sqrts, 0, self._events, \
        self._tempSlhaName,unlink = self._unlink)
        xsecComputer.addXSecToFile(xsecs, self._tempSlhaName, comment)
        logger.info('added new LO order xsecs to temp.slha')
        if self._order == 'NLO':
            xsecs = xsecComputer.computeXSec(self._sqrts, 1, self._events,\
            self._tempSlhaName,loFromSlha=True,unlink = self._unlink)
            xsecComputer.addXSecToFile(xsecs, self._tempSlhaName, comment)
            logger.info('added new NLO order xsecs to temp.slha')
        if self._order == 'NLL':
            xsecs = xsecComputer.computeXSec(self._sqrts, 2, self._events, \
            self._tempSlhaName, loFromSlha=True,unlink = self._unlink)
            xsecComputer.addXSecToFile(xsecs, self._tempSlhaName, comment)
            logger.info('added new NLL order xsecs to temp.slha')
    
    def _delXsecFromFile(self):
        
        slhaFile = open(self._tempSlhaName,'r')
        xsecBlock = False
        lines = slhaFile.readlines()
        for i in range(0, len(lines) - 1):
            if 'XSECTION' in lines[i]:
                xsecBlock = True
                break
        if xsecBlock: lines = lines[:i+1]
        slhaFile.close()
        
        slhaFile = open(self._tempSlhaName,'w')
        slhaFile.writelines(lines)
        slhaFile.close()

        
    def _templateSlhaFile(self, topo):
        """Checks if there is a template slha-file for given topology
        in smodels-tools/slha. If there is, the file is copied to self._tempSlhaName.
        :param topo: topology name as string
        
        """
        
        tempPath = '../slha/'
        if not os.path.exists('%s%s.slha' %(tempPath, topo)):
            logger.error('no template slha-file for %s' %topo)
            sys.exit()
        os.system('cp %s%s.slha ./%s' %(tempPath, topo, self._tempSlhaName))
        
    def _getPidCodeOfMother(self):
        """Sets the PID codes for mother particles to variable self._listOfMotherPid.
        
        """
        
        picDict = {
            'g' : ['1000021'],
            'q' : ['1000001', '1000002', '1000003', '1000004', 
            '2000001', '2000002','2000003','2000004'], 
            'b' : ['1000005'], #'2000005'], no right handed particles
            't' : ['1000006'], #'2000006'], no right handed particles
            'l' : ['1000011','1000013','2000011','2000013'],
            'c0cpm':['1000024','1000023'],
            'c0':['100023'],
            'cpm':['1000024']}
            
        motherPart = self.topo.motherParticle
        if not motherPart in picDict:
            logger.error('no PIC code for motherParticle: %s in picDic' \
            %motherPart)
            sys.exit()
        return picDict[motherPart]
    
    def _getPidCodeOfIntermediateParticle(self):
        """":returns: List of PID codes for intermediate particles 
        
        """
        
        picDict = {
            'chargino^pm_1' : ['1000024'],
            'chargino^p' : ['1000024'],
            'slepton' : ['1000013','1000011'],
            'sLepton' : ['1000013','1000011','1000015'],
            'sneutrino' : ['1000012','1000014'],
            'sNeutrino' : ['1000012','1000014', '1000016'],
            'stauon' : ['1000015']}
            
        interPart = self.topo.intermediateParticles
        if not interPart: return
        listOfInterPid = []
        for particle in interPart:
            if not particle in picDict:
                logger.error('no PIC code for intermediateParticle: %s in picDic' \
                %motherPart)
                sys.exit()
            for pid in picDict[particle]: listOfInterPid.append(pid)
        return listOfInterPid
        
        
            
    def _setMass(self, motherMass, lspMass, interMass = None):
        """Search for mass block in self._tempSlhaName and write the given 
        motherMass to all particles in ListOfPidCode and the LSPMass to LSP.
        :param motherMass: one mass for all particles in ListOfPidCode as float
        :param lspMass: mass of the LSP as float
        :param interMass: mass of intermediate particle
        :returns: list containing lines of slha file
        ### FIX ME no intermediated mass implemented yet
        
        """
        pidOfLsp = '1000022'
        slhaFile = open(self._tempSlhaName,'r')
        lines = slhaFile.readlines()
        listOfPidCode = [pid for pid in self._listOfMotherPid]
        listOfInterPid = [pid for pid in self._listOfInterPid]
        
        massBlock = False
        for i in range(0,len(lines)-1):
            if lines[i] == '#\n' and massBlock ==True: break
            if massBlock == True: 
                listOfLine = lines[i].split()
                if listOfLine[0] in listOfPidCode:
                    listOfPidCode.remove(listOfLine[0])
                    listOfLine[1] = motherMass
                    lines[i] = self._formatMassEntry(listOfLine)
                if listOfLine[0] == pidOfLsp:
                    pidOfLsp = None
                    listOfLine[1] = lspMass
                    lines[i] = self._formatMassEntry(listOfLine)
                if listOfInterPid and interMass:
                    if listOfLine[0] in listOfInterPid:
                        listOfInterPid.remove(listOfLine[0])
                        listOfLine[1] = interMass
                        lines[i] = self._formatMassEntry(listOfLine)
                        
            if 'BLOCK MASS' in lines[i]: massBlock = True
        if not massBlock: 
            logger.error('No Mass block found in slha file')
            sys.exit()
        if listOfPidCode:
            logger.error('PID Codes: %s not found in Mass block of slha file' \
            %listOfPidCode)
            sys.exit()
        if listOfInterPid:
            logger.error('PID Codes: %s not found in Mass block of slha file' \
            %listOfInterPid)
            sys.exit()            
        if pidOfLsp:
            logger.error('PID Code of LSP  not found in Mass block of slha file')
            sys.exit()
        slhaFile.close()
        
        
        #for line in lines:
        #   print line
        
        slhaFile = open(self._tempSlhaName,'w')
        slhaFile.writelines(lines)
        slhaFile.close()
        logger.debug('temp.slha file changed to mother mass: %s and LSP mass: \
        %s' %(motherMass, lspMass))
        
    def _formatMassEntry(self,listOfLine):
        """Builds a correct formated mass entry for slha file out of a given list.
        :param listOfline: list containing PID-Code as string in [0], 
        mass as float in [1], ('#' in [2] and particle name in [3] also supported)
        
        """
        
        listOfLine[1] = str(listOfLine[1])
        listOfLine[0] = " "*(10-len(listOfLine[0])) + listOfLine[0]
        return '    '.join(listOfLine) + '\n'
            

def main():
    """Handles all command line options.
    Produces the slha-files for given topology.
    :param Base: sets the path to the smodels-database
    :param topology: topology the slha-files should be preoduced for
    :param events: number of events for pythia simulation 
    :param order: order of perturbation theory as string ('LO' or 'NLL')
    :param link: unlinks the pythia log file, when set to False
    :param intermediate: comma separated condition and value (e.g. LSP,300); condition for mass of intermediate particle (e.g xvalue), value for the mass condition (e.g. 025)
    
    """
    argparser = argparse.ArgumentParser(description = \
    'Produces the slha files for smodels validation plots')
    argparser.add_argument ('-b', '--Base', \
    help = 'set path to base-directory of smodels-database\n \
    - default: /afs/hephy.at/user/w/walten/public/sms/', \
    type = types.StringType, default = '/afs/hephy.at/user/w/walten/public/sms/')
    argparser.add_argument ('-t', '--topology', \
    help = 'topology that slha-files should be produced for - default: T1',\
    type = types.StringType, default = 'T1')
    argparser.add_argument ('-blog', '--browserVerbosity',\
    help = 'set browser-verbosity - default: ERROR', \
    type = types.StringType, default = 'error')
    argparser.add_argument ('-n', '--events',\
    help = 'set number of events - default: 10000', \
    type = types.IntType, default = 10000)
    argparser.add_argument ('-o', '--order', \
    help = 'perturbation order (LO or NLL) - default: NLL', \
    type = types.StringType, default = 'NLL')
    argparser.add_argument ('-l', '--link', \
    help = 'Do not clean up temp directory after running pythia', \
    action = 'store_false')
    argparser.add_argument ('-i', '--intermediate', \
    help = 'condition and value for intermediate particle - default: xvalue,050', \
    type = types.StringType, default = 'xvalue,050')
    args = argparser.parse_args()

    browser = Browser(args.Base)
    browser.verbosity = args.browserVerbosity
    topology = args.topology
    intermediate = args.intermediate.split(',')
    intermediate = [i.strip() for i in intermediate]
    if len(intermediate) != 2:
        logger.error('Could not handle argument intermediate: %s! \n \
        Expected: condition,value!' %intermediate)
        sys.exit()
    if intermediate[0] == 'xvalue':
        condition = ''
    else:
        condition = intermediate[0]
    if intermediate[1] == '050':
        value = ''
    else:
        value = intermediate[1]
    extendedTopology = topology + condition + value
    logger.info('Creating slha for extended topology %s.' %extendedTopology)
    events = args.events
    order = args.order
    unlink = args.link
    threshold = Threshold(topology, browser, intermediate[0], intermediate[1])
    folder = checkFolder('../slha/%s_%s_%s_slhas' \
    %(extendedTopology, events, order))
    count = 0
    slhaFiles = SlhaFiles(topology, browser, threshold.motherMasses, \
    threshold.lspMasses, threshold.d, intermediate[0], intermediate[1], events, order, unlink)
    for f in slhaFiles:
        count += 1
        print('Progress ...... ', count)
    print('Wrote %s slha-files to %s' %(count, folder))
    print('unlink %s' %unlink)
    #del slhaFiles

def checkFolder(path):
    """Checks if the slha folder already exists.
    If the folder already exists, the user can decide whether to remove 
    all slha files, or to exit the script.
    
    """
    if os.path.exists(path):
        print('Folder %s already exists!' %path)
        while True:
            userInput = raw_input('Remove old files? [y/n]:  ')
            if userInput == 'n':
                sys.exit()
            if userInput == 'y':
                os.system('rm -r %s' %path)
                return path
    return path
    
if __name__ == '__main__':
    main()
                    

    
    