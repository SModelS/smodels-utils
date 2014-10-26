#!/usr/bin/env python


"""
.. module:: slhaCreatorNew
   :synopsis: An iterator object returning slha-files for validation plots

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""
from __future__ import print_function
import setPath 
from smodels_tools.tools.databaseBrowser import Browser
from smodels.tools.physicsUnits import GeV
from smodels.tools.slhaChecks import SlhaStatus
from unum import Unum
import logging
import sys
import os
from massPlaneComputer import MassPlane

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)

        
        
class SlhaFileSet(object):
    
    def __init__(self, browser, topo, extendedTopoName, massParametrization, events = 10, order = 'NLL', \
    unlink = True, sqrts =8.0):
        
        self._browser = browser
        self._massPlane = MassPlane(browser, topo, extendedTopoName, massParametrization)
        self.directory = self._createDirectory(extendedTopoName, events, order, sqrts)
        self._templateFile = self._setTemplateFile(topo)
        self._extendedTopoName = extendedTopoName
        self._order = order
        self._condition = massParametrization[0]
        self._listOfInterPid = self._getPidCodeOfIntermediateParticle(topo)
        self._listOfMotherPid = self._getPidCodeOfMother(topo)
        self._lspPid = '1000022'
    
    def _setTemplateFile(self,topo):
        
        tempPath = '../slha/'
        templateFile = '%s%s.slha' %(tempPath, topo.name)
        if os.path.exists(templateFile):
            return templateFile
        logger.error('no template slha-file for %s' %topo.name)
        return None
        
        
        
    def create(self):
        countAll = 0
        countGOOD = 0
        for lspList in self._massPlane.iterListsWithFixedMotherMasses():
            fileContent  = open(self._templateFile,'r').readlines()
            for i, massPoint in enumerate(lspList):
                    countAll = countAll + 1
                    fileName = '%s_%s_%s_%s.slha' \
                    %(self._extendedTopoName, int(massPoint.xMass), int(massPoint.yMass), self._order)
                    fileName = self.directory + '/' + fileName
                    #print(fileName)
                    pidMassesDict = self._getPidMassesDict(massPoint)
                    #print pidMassesDict
                    fileContent = self._setMasses(fileContent, pidMassesDict)
                    #testDict = self._getPidMassesDict(massPoint)
                    #for l in fileContent:
                    #    rows = l.split()
                    #    if rows:
                    #        if rows[0].strip() in testDict:
                    #            print l
                    slhaFile = open(fileName,'w')
                    slhaFile.writelines(fileContent)
                    slhaFile.close()
                    status = SlhaStatus(fileName,findIllegalDecays=True, findDisplaced=False, \
                    checkXsec=False, checkLSP=False, checkFlightlength=False, findMissingDecays=False)
                    slhastat, warnings = status.status
                    
                    print('*****************start********************')
                    print(fileName)
                    print ('####slhasstatus: %s' %slhastat)
                    print('******************end****************')
                    if slhastat == -1:
                        os.system('rm %s' %fileName)
                        continue
                    countGOOD = countGOOD + 1
                    if i == 0: #### problem wenn 1.file nicht erlaubt!!!!!
                        #### the xsecs have to be calculted at this place
                        fileContent  = open(fileName,'r').readlines()

        print('####all: %s' %countAll)
        print('####good: %s' %countGOOD)
            

            
            #print '*******************************************'
            #for p in l:
            #    print 'motherMass: %s, intMass: %s, lspMass: %s, xMass: %s, yMass: %s' \
            #    %(p.motherMass, p.interMass, p.lspMass, p.xMass, p.yMass)
            
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
        
        picDict = {
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
            if not particle in picDict:
                logger.error('no PIC code for intermediateParticle: %s in picDic' \
                %motherPart)
                return
            for pid in picDict[particle]: listOfInterPid.append(pid)
        return listOfInterPid
     
    def _getPidCodeOfMother(self,topo):
        """Sets the PID codes for mother particles to variable self._listOfMotherPid.
        
        """
        
        picDict = {
            'g' : ['1000021'],
            'q' : ['1000001', '1000002', '1000003', '1000004'],
            #,'2000001', '2000002','2000003','2000004'], only lefthanded squarks
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
        if not motherPart in picDict:
            logger.error('no PIC code for motherParticle: %s in picDic' \
            %motherPart)
            return
        return picDict[motherPart]
    
    
    
    
    
    
    
def main():
    
    browser = Browser('../../smodels-database')
    extendedTopoName = 'T6bWWx125'
    #topo = browser.expTopology('T6bbWW')
    topo = browser.expTopology('T6bbWW')
    parametrizations = topo.massParametrizations
    slhaFileSets = []
    for extendedTopoName,  massParametrization in parametrizations.iteritems():
        fileSet = SlhaFileSet(browser,topo, extendedTopoName,massParametrization)
        slhaFileSets.append(fileSet)
    print (slhaFileSets)
    for fileSet in slhaFileSets:
        userInput = raw_input('press any key')
        if fileSet: 
            fileSet.create()
            print (fileSet._listOfInterPid)
            print (fileSet._listOfMotherPid)
            print (fileSet._lspPid)
            massPlane = fileSet._massPlane
            print('xmin: %s, xmax: %s, xStep: %s' %(massPlane.xMin, massPlane.xMax, massPlane.xStep))
            print('ymin: %s, ymax: %s, yStep: %s' %(massPlane.yMin, massPlane.yMax, massPlane.yStep))
            print (fileSet.directory)
            
            
        
        
if __name__ == '__main__':
    main()
 