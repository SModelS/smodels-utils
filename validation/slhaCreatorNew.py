#!/usr/bin/env python


"""
.. module:: slhaCreatorNew
   :synopsis: An iterator object returning slha-files for validation plots

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""
from __future__ import print_function
import setPath 
from smodels_utils.tools.databaseBrowser import Browser
from smodels.tools.physicsUnits import GeV
from smodels.tools.physicsUnits import TeV
from smodels.tools.slhaChecks import SlhaStatus
from smodels.tools import xsecComputer
from unum import Unum
import logging
import sys
import os
from massPlaneComputer import MassPlane
import argparse
import types

FORMAT = '%(levelname)s in %(module)s.%(funcNbrowser, topo, extendedTopoName, massParametrization)ame)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)

        
        
class SlhaFileSet(object):
    
    def __init__(self, browser, topo, extendedTopoName, massParametrization, events = 10000, order = None, \
    unlink = True, sqrts =8.0):
        
        self._browser = browser
        self._massPlane = MassPlane(browser, topo, extendedTopoName, massParametrization)
        self._order = self._getOrder(topo,order)
        self.directory = self._createDirectory(extendedTopoName, events, self._order, sqrts)
        self._templateFile = self._setTemplateFile(topo)
        self._extendedTopoName = extendedTopoName
        self._condition = massParametrization[0]
        self._listOfInterPid = self._getPidCodeOfIntermediateParticle(topo)
        self._listOfMotherPid = self._getPidCodeOfMother(topo)
        self._lspPid = '1000022'
        self._events = events
        self._unlink = unlink
        self._sqrts = sqrts
        self._NLLfastMin, self._NLLfastMax = self._getNLLfastMinMax(topo) #min/max mass for NLLfast 
    
    def _setTemplateFile(self,topo):
        
        tempPath = '../slha/'
        templateFile = '%s%s.slha' %(tempPath, topo.name)
        if os.path.exists(templateFile):
            return templateFile
        logger.error('no template slha-file for %s' %topo.name)
        return None
        
    def _getOrder(self, topo, order):
        
        motherParticle = topo.motherParticle
        if not order and motherParticle in ['g','q','gq','b','t']:
            return 'NLL'
        if not order and motherParte in ['l','c0cpm','c0','cpm']:
            return 'LO'
        if order and order in ['LO','NLL','NLO']:
            return order
        logger.error('order must be LO, NLO, or NLL; got %s' %order)
        sys.exit()
        
    def _getNLLfastMinMax(self, topo):
        """return the min lsp mass for which NLLfast is able to 
        compute xsecs
        
        """
        if topo.motherParticle in ['g','gq','q'] and not topo.intermediateParticles:
            return [200.,2000.]
        if topo.motherParticle in ['b','t'] and not topo.intermediateParticles:
            return [100.,1000.]
        if topo.motherParticle in ['b'] and topo.intermediateParticles:
            return [400.,1000.]
        return [0.,2000.]
        
        
    def create(self):
        countAll = 0
        countGOOD = 0

        for lspList in self._massPlane.iterListsWithFixedMotherMasses():
            if lspList[0].motherMass < self._NLLfastMin: continue 
            if lspList[0].motherMass > self._NLLfastMax: continue 
            fileContent  = open(self._templateFile,'r').readlines()
            computeXsecs = True
            for massPoint in lspList:
                    countAll = countAll + 1
                    fileName = '%s_%s_%s_%s.slha' \
                    %(self._extendedTopoName, int(massPoint.xMass), int(massPoint.yMass), self._order)
                    fileName = self.directory + '/' + fileName
                    logger.info('next file:  %s' %fileName.split('/')[-1])
                    pidMassesDict = self._getPidMassesDict(massPoint)
                    fileContent = self._setMasses(fileContent, pidMassesDict)
                    slhaFile = open(fileName,'w')
                    slhaFile.writelines(fileContent)
                    slhaFile.close()
                    status = SlhaStatus(fileName,findIllegalDecays=True, findDisplaced=False, \
                    checkXsec=False, checkLSP=False, checkFlightlength=False, findMissingDecays=False)
                    slhastat, warnings = status.status
                    if slhastat == -1:
                        os.system('rm %s' %fileName)
                        logger.info('illegalDecay: drop %s' %fileName.split('/')[-1])
                        continue
                    countGOOD = countGOOD + 1
                    if computeXsecs: 
                        self._addXsecsToFile(fileName)
                        fileContent  = open(fileName,'r').readlines()
                        computeXsecs = False
        os.system(' tar -cf %s.tar %s' %(self.directory, self.directory))
        print('\n*****slha creation for %s, %sTeV done**************' %(self._extendedTopoName, self._sqrts))
        print('xmin: %s, xmax: %s, xStep: %s' %(self._massPlane.xMin, self._massPlane.xMax, self._massPlane.xStep))
        print('ymin: %s, ymax: %s, yStep: %s' %(self._massPlane.yMin, self._massPlane.yMax, self._massPlane.yStep))
        print('got %s mass points, chreated %s slha-files' %(countAll, countGOOD))
        print('************************************************')
            

    def _addXsecsToFile(self,fileName):
        """Adds the xsecs to the slha file. First LO then NLO and finally NLL 
        are computed.
        # ### FIX ME: order NLO? does this make sens? We get NLO by adding a factor 1.2 to LO, right?
        
        """
        
        comment = "Nevts: " + str(self._events)
        sqrts = self._sqrts*TeV
        xsecs = xsecComputer.computeXSec(sqrts, 0, self._events, \
        fileName,unlink = self._unlink)
        xsecComputer.addXSecToFile(xsecs, fileName, comment)
        logger.info('added new LO order xsecs to %s' %fileName)
        if self._order == 'NLO':
            xsecs = xsecComputer.computeXSec(sqrts, 1, self._events,\
            fileName,loFromSlha=True,unlink = self._unlink)
            xsecComputer.addXSecToFile(xsecs, fileName, comment)
            logger.info('added new NLO order xsecs to %s' %fileName)
        if self._order == 'NLL':
            xsecs = xsecComputer.computeXSec(sqrts, 2, self._events, \
            fileName, loFromSlha=True,unlink = self._unlink)
            xsecComputer.addXSecToFile(xsecs, fileName, comment)
            logger.info('added new NLL order xsecs to %s' %fileName)
    
            
    def _getPidMassesDict(self, massPoint):
        
        pidMassesDict = {}
        pidMassesDict[self._lspPid] = massPoint.lspMass
        if self._listOfInterPid:
            for pid in self._listOfInterPid:
                pidMassesDict[pid] = massPoint.interMass
        for pid in self._listOfMotherPid:
            pidMassesDict[pid] = massPoint.motherMass
        return pidMassesDict
        
        
        
        
    def _setMasses(self, fileContent, pidMassesDict):

        massBlock = False
        for i in range(0,len(fileContent)-1):
            if fileContent[i] == '#\n' and massBlock ==True: break
            if fileContent[i] == '\n' and massBlock ==True: break
            if massBlock == True: 
                rows = fileContent[i].split()
                if rows[0].strip() in pidMassesDict:
                    rows[1] = pidMassesDict[rows[0].strip()]
                    del pidMassesDict[rows[0].strip()]
                    fileContent[i] = self._formatMassEntry(rows)
            if 'BLOCK MASS' in fileContent[i]: massBlock = True

        if not massBlock: 
            logger.error('No Mass block found in slha file')
            sys.exit()
        if pidMassesDict:
            logger.error('PID Codes: %s not found in Mass block of slha file' \
            %pidMassesDict)
            sys.exit()
        return fileContent

        
        
    def _formatMassEntry(self,rows):
        """Builds a correct formated mass entry for slha file out of a given list.
        :param listOfline: list containing PID-Code as string in [0], 
        mass as float in [1], ('#' in [2] and particle name in [3] also supported)
        
        """
        
        rows[1] = str(rows[1])
        rows[0] = " "*(10-len(rows[0])) + rows[0]
        return '    '.join(rows) + '\n'
        

    def _createDirectory(self, extendedTopoName, events, order, sqrts):
        
        directory = '../slha/%s_%s_%s_%sTeV_slhas' \
        %(extendedTopoName, events, order, int(sqrts))
        if os.path.exists(directory):
            print('Folder %s already exists!' %directory)
            while True:
                userInput = raw_input('Remove old files? [y/n]:  ')
                if userInput == 'n': return None
                if userInput == 'y': break
            os.system('rm -r %s' %directory)
        if os.path.exists(directory +'.tar'):
            print('tarball %s already exists!' %(directory + '.tar'))
            while True:
                userInput = raw_input('Remove tarball? [y/n]:  ')
                if userInput == 'n': return None
                if userInput == 'y': break
            os.system('rm %s' %(directory + '.tar'))
        os.makedirs(directory)
        logger.info('Created new folder %s.' %directory)
        return directory
        
    def __nonzero__(self):
        
        if not self._listOfMotherPid: return False
        if not self._templateFile: return False
        if not self._massPlane: return False
        if not self.directory: return False
        if not self._listOfInterPid and self._condition:
            return False
        return True
        
        
    def _getPidCodeOfIntermediateParticle(self,topo):
        """":returns: List of PID codes for intermediate particles 
        
        """
        
        pidDict = {
            'chargino^pm_1' : ['1000024'],
            'chargino^p' : ['1000024'],
            'slepton' : ['1000013','1000011'],
            'sLepton' : ['1000013','1000011','1000015'],
            'sneutrino' : ['1000012','1000014'],
            'sNeutrino' : ['1000012','1000014', '1000016'],
            'stauon' : ['1000015']}
            
        interPart = topo.intermediateParticles
        if not interPart: 
            return None
        if not interPart and self._condition: 
            logger.error('no intermediate particle for %s, please check experimentalTopology.py in smodels-tools/tools'  \
            %topo.name)
            return
        listOfInterPid = []
        for particle in interPart:
            if not particle in pidDict:
                logger.error('no PIC code for intermediateParticle: %s in pidDic' \
                %motherPart)
                return
            for pid in pidDict[particle]: listOfInterPid.append(pid)
        return listOfInterPid
     
    def _getPidCodeOfMother(self,topo):
        """Sets the PID codes for mother particles to variable self._listOfMotherPid.
        
        """
        
        pidDict = {
            'g' : ['1000021'],
            'q' : ['1000001', '1000002', '1000003', '1000004',
            '2000001', '2000002','2000003','2000004'], #all squarks
            'gq' : ['1000021', '1000001', '1000002', '1000003', '1000004'],
            'b' : ['1000005'], #'2000005'], no b2
            't' : ['1000006'], #'2000006'], no t2
            'l' : ['1000011','1000013','2000011','2000013'],
            'c0cpm':['1000024','1000023'],
            'c0':['100023'],
            'cpm':['1000024']}
            
        motherPart = topo.motherParticle
        if not motherPart:
            logger.error('no mother particle for %s, please check experimentalTopology.py in smodels-tools/tools'  \
            %topo.name)
            return
        if not motherPart in pidDict:
            logger.error('no PIC code for motherParticle: %s in pidDic' \
            %motherPart)
            return
        return pidDict[motherPart]
    
    
    
    
    
    
    
def main():
    
    argparser = argparse.ArgumentParser(description = \
    'Produces the slha files for smodels validation plots')
    argparser.add_argument ('-b', '--Base', \
    help = 'set path to base-directory of smodels-database\n \
    - default: /afs/hephy.at/user/w/walten/public/sms/', \
    type = types.StringType, default = '/afs/hephy.at/user/w/walten/public/sms/')
    
    
    argparser.add_argument ('-t', '--topology', \
    help = 'topology that slha-files should be produced for - default: T1',\
    type = types.StringType, default = 'T1')
    
    argparser.add_argument ('-n', '--events',\
    help = 'set number of events - default: 10000', \
    type = types.IntType, default = 10000)
    
    
    argparser.add_argument ('-o', '--order', \
    help = 'perturbation order (LO or NLL) - default: LO for ew-production, NLL else', \
    type = types.StringType, default = 'None')
    
    argparser.add_argument ('-l', '--link', \
    help = 'Do not clean up temp directory after running pythia', \
    action = 'store_false')
   
    argparser.add_argument ('-sqrts', '--sqrts',\
    help = 'set sqrts in TeV - default: greate slha for 8 and 7TeV', \
    type = types.FloatType, default = 0.0)
    args = argparser.parse_args()
    
    browser = Browser(args.Base)
    topoName = args.topology       
    events = args.events
    if args.order != 'None':
        order = args.order
    else:
        order = None
    if args.sqrts != 0.0:
        sqrts = [args.sqrts]
    else:
        sqrts = [7.0, 8.0]
    unlink = args.link
    

    #topo = browser.expTopology('T6bbWW')
    topo = browser.expTopology(topoName)
    parametrizations = topo.massParametrizations
    slhaFileSets = []
    for extendedTopoName,  massParametrization in parametrizations.iteritems():
        for sqrt in sqrts:
            fileSet = SlhaFileSet(browser,topo, extendedTopoName,massParametrization, \
            events = events , order = order, unlink = unlink, sqrts =sqrt)
            slhaFileSets.append(fileSet)

            
    for fileSet in slhaFileSets:
        if fileSet: 
            fileSet.create()
            massPlane = fileSet._massPlane

            
            
        
        
if __name__ == '__main__':
    main()
 
