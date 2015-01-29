#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds objects used by convert.py to create info.txt, sms.root, sms.py and newSms.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   


import sys
import os
import ROOT
from smodels_utils.dataPreparation.standardObjects import\
OldStandardLimits, StandardExclusions, StandardTWiki, StandardInfo
import logging

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

           
        
class DatabaseCreator(list):
        
    def __init__(self):
        
        self.limits = []
        self.expectedlimits = []
        self.exclusions = []
        self.limitsDictName = 'Dict'
        self.expectedlimitsDictName = 'ExpectedDict'
        self.metaInfo = None
        self.twikitxtPath = '/orig/twiki.txt'
        self.smsrootPath = '/sms.root'
        self.smspyPath = '/sms.py'
        self.infotxtPath = '/info.txt'
        list.__init__(self)
            
    def create(self):
        
        print '\n***strating creation of database entry for %s***\n'\
        %self.metaInfo.id
        
        self.info = StandardInfo(self.metaInfo, self.infotxtPath)
        self.tWiki = StandardTWiki(self.metaInfo)
        for txName in self:
            
            print '\nreading: %s' %txName.name
            
            limits = OldStandardLimits(txName, 'limit',\
            self.limitsDictName)
            expectedlimits = OldStandardLimits(txName, 'expectedlimit', \
            self.expectedlimitsDictName)
            exclusions = StandardExclusions(txName)
            for plane in txName.planes:
                
                print '\nreading mass plane: %s\n' %plane.origPlot
                
                limits.addMassPlane(plane)
                print 'extending upperLimits to %s entrys'\
                %len(limits.limits)
                print 'found topoExtensions: %s' \
                %( limits.topoExtensions)
                
                expectedlimits.addMassPlane(plane)
                
                print 'extending expected upperLimits to %s entrys'\
                %len(expectedlimits.limits)
                print 'found topoExtensions: %s' \
                %(expectedlimits.topoExtensions)
                
                exclusions.addMassPlane(plane)
                
                print 'extend exclusionLines to %s entrys'\
                %len(exclusions)

                self.tWiki.addMassPlane(txName.name,plane)
            if limits: self.limits.append(limits)
            if expectedlimits: self.expectedlimits.append(expectedlimits)
            if exclusions: self.exclusions.append(exclusions)
            #print 'on:%s' %txName.onShell
            #print 'off:%s' %txName.offShell
            self.info.addTxName(txName)
        
        self._createSmsPy()
        self._createSmsRoot()
        self._createTwikiTxt()
        self._createInfoTxt()
        
        
    def _createSmsPy(self):
        
        smsPy = open(os.getcwd() + self.smspyPath,'w')
        if self.limits:
            smsPy.write('%s={}\n' %self.limitsDictName)
            for limits in self.limits: smsPy.write('%s' %limits)
        if self.expectedlimits:
            print self.expectedlimits
            smsPy.write('%s={}\n' %self.expectedlimitsDictName)
            for limits in self.expectedlimits: smsPy.write('%s' %limits)
            
    def _createSmsRoot(self):
    
        smsRoot = ROOT.TFile(os.getcwd() + self.smsrootPath,'recreate')
        for exclusions in self.exclusions:
            directory = smsRoot.mkdir(exclusions.txName, exclusions.txName)
            directory.cd()
            for exclusion in exclusions: exclusion.Write()
        smsRoot.Close()
        
    def _createTwikiTxt(self):
        
        twikiTxt = open(os.getcwd() + self.twikitxtPath,'w')
        twikiTxt.write('%s' %self.tWiki)
        twikiTxt.close()
        
    def _createInfoTxt(self):
        
        infoTxt = open(os.getcwd() + self.infotxtPath, 'w')
        infoTxt.write('%s' %self.info)
        infoTxt.close()
        
databaseCreator = DatabaseCreator()        
        
        
        
             