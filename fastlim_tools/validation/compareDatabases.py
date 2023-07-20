#!/usr/bin/env python

"""
.. module:: compareDatabases
   :synopsis: Collects simple information about Fastlim database and compares to the SModelS database

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import sys,os,glob
import logging
sys.path.append('../runTools')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
sys.path.append(os.path.join(home,'smodels-database'))
from smodels.tools import databaseBrowser
from smodels.base.physicsUnits import GeV, fb, TeV


class simpleSR(object):
    """
    Holds very basic information about a Fastlim Signal Region (SR)
    """
    
    def __init__(self,line):
        data = line.split()
        self.lumi = eval(data[1])/fb
        self.observedN = eval(data[2])
        self.expectedBG = eval(data[3])
        self.BGerror = eval(data[4])
        self.upperLimit = eval(data[7])*fb
        self.id = data[9]        
        self.name = ""
        for sn in data[10:]: self.name += " "+sn
        self.name = self.name.lstrip()
        
    def __str__(self):
        return self.id
        


fastlimPath = "../fastlim-1.0/analyses_info/8TeV"
databasePath = os.path.join(home,'smodels-database')

fastExpRes = {}
for expID in os.listdir(fastlimPath):    
    srInfo = open(os.path.join(fastlimPath,expID,'SR_info.txt'),'r')
    srData = srInfo.readlines()
    srInfo.close()
    expID = expID.replace("_","-")
    fastExpRes[expID] = []    
    for line in srData[1:]:
        if not line.split(): continue
        fastExpRes[expID].append(simpleSR(line))
        
browser = databaseBrowser.Browser(databasePath)
browser.selectExpResultsWith(contact = ['fastlim'])

for expRes in browser:
    expID = expRes.getValuesFor('id')[0]
    print expID,len(fastExpRes[expID]),len(expRes.datasets)
    if len(fastExpRes[expID]) != len(expRes.datasets):
        print expID,'differ (smodels/fastlim):',len(expRes.datasets),len(fastExpRes[expID])
        print 'SMODELS:',expRes.getValuesFor('dataId')
        print 'FASTLIM:',[sr.id for sr in fastExpRes[expID]]

