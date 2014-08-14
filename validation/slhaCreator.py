#!/usr/bin/env python


"""
.. module:: slhaCreator
   :synopsis: An iterator object returning slha-files for validation plots

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

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
    """Uses upper limit dictionaries for a given topology and analysis to 
    create slha-files and returns them via an __iter__ method.
    ### no intermediated mass supported
    ### no mass splitting for topology supported
    

    """
    
    def __init__(self, topology, browserObject, thresholdMotherMasses, \
    thresholdLSPMasses, d, events = 1000, order = 'LO',unlink = True):
        """Uses the given browser object to retrieve all upper limit histogram 
        dictionaries knowen for this topology. Creates a directory ./'topology'_slhas
        and stores the slha-file for this topology for every point in the mass-plane.
        :param topology: topology the slha-files should be preoduced for
        :param browserObject: instance of the class Browser
        :param events: number of events for pythia simulation 
        :param order: order of pertubation theory as string
        'LO', 'NLO', and 'NLL' are possible
        
        """
        self._tempSlhaName = 'temp.slah'
        self.folder = '../slha/%s_%s_%s_slhas' %(topology, events, order)
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            logger.info('Created new folder %s!' %self.folder)
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
        
    def __iter__(self):
        """Creates a slha-file named 'topology_motherMass_lspMass_order.slha and
        adds the masses. If the mother mass changes the cross sections will be
        computed and also added to the slha-file.
        
        """
        logger.info('There are approximately %s points in the mass plane!' \
        %(int(len(self.motherMasses) * len(self.lspMasses) / 2.)))
        for motherMass in self.motherMasses:
            firstLoop = True
            for lspMass in self.lspMasses:
                if lspMass > motherMass + self.d: continue
                fileName = self.topo.name + '_' + str(int(motherMass)) + \
                '_' + str(int(lspMass)) + '_' + self._order + '.slha'
                slhaLines = self._setMass(motherMass, lspMass)
                if firstLoop:
                    self._delXsecFromFile()
                    self._addXsecsToFile()
                    firstLoop = False
                path = self.folder + '/' + fileName)
                
                os.system('cp ./%s %s' %(self._tempSlhaName, path))
                yield path
                
                    
    def _addXsecsToFile(self):
        """add the xsecs to the slha file. first LO then NLO and finaly 
        are computed
        
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
        lines = slhaFile.readlines()
        for i in range(0, len(lines) - 1):
            if 'XSECTION' in lines[i]: break
        lines = lines[:i+1]
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
        ### FIX ME: EW-Production not included yet
        
        """
        
        picDict = {
            'g' : ['1000021'],
            'q' : ['1000001', '1000002', '1000003', '1000004', 
            '2000001', '2000002','2000003','2000004'],
            'b' : ['1000005', '2000005'],
            't' : ['1000006', '2000006'],
            'l' : ['1000011','1000012','1000013','1000014',
            '1000015','1000016'],
            'c0cpm':['1000024','1000023'],
            'c0':['100023'],
            'cpm':['1000024']}
            
        motherPart = self.topo.motherParticle
        if not motherPart in picDict:
            logger.error('no PIC code for motherParticle: %s in picDic' \
            %motherPart)
            sys.exit()
        return picDict[motherPart]
        
    def _setMass(self, motherMass, lspMass):
        """Search for mass block in self._tempSlhaName and write the given 
        motherMass to all particles in ListOfPidCode and the LSPMass to LSP.
        :param motherMass: one mass for all particles in ListOfPidCode as float
        :param lspMass: mass of the LSP as float
        :returns: list containing lines of slha file
        ### FIX ME no intermediated mass implemented yet
        
        """
        pidOfLsp = '1000022'
        slhaFile = open(self._tempSlhaName,'r')
        lines = slhaFile.readlines()
        listOfPidCode = self._getPidCodeOfMother()
        
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
            if 'BLOCK MASS' in lines[i]: massBlock = True
        if not massBlock: 
            logger.error('No Mass block found in slha file')
            sys.exit()
        if listOfPidCode:
            logger.error('PID Codes: %s not found in Mass block of slha file' \
            %listOfPidCode)
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
    """Handles all command line options, as:
    topology, base, loglevel, ...
    Produces the slha-files for given topology.
    
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
    help = 'perturbation order (LO, NLO, NLL) - default: NLL', \
    type = types.StringType, default = 'NLL')
    argparser.add_argument ('-l', '--link', \
    help = 'Do not clean up temp directory after running pythia', \
    action = 'store_false')
    args = argparser.parse_args()

    browser = Browser(args.Base)
    browser.verbosity = args.browserVerbosity
    topology = args.topology
    events = args.events
    order = args.order
    unlink = args.link
    threshold = Threshold(topology, browser)
    folder = checkFolder('../slha/%s_%s_%s_slhas' \
    %(topology, events, order))
    count = 0
    for f in SlhaFiles(topology, browser, threshold.motherMasses, \
    threshold.lspMasses, threshold.d, events, order, unlink):
        count += 1
    print('Wrote %s slha-files to ../slha/%s_%s_%s_slhas' \
    %(count, topology, events, order))
    print('unlink %s' %unlink)

def checkFolder(path):
    """Checks if the slha folder already exists.
    If the folder already exists, the user can decide wether to remove 
    all slha files, or to exit the script.
    
    """
    if os.path.exists(path):
        print('Folder %s already exists!' %path)
        while True:
            userInput = raw_input('Remove old files? [y/n]:  ')
            if userInput == 'n':
                sys.exit()
            if userInput == 'y':
                import shutil
                shutil.rmtree(path)
    return path
    
if __name__ == '__main__':
    main()
                    

    
    