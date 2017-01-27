#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds objects used by convert.py to create globalInfo.txt,
              sms.root, sms.py and newSms.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   

import sys, logging
import ROOT
from math import floor, log10
from smodels.tools.physicsUnits import pb, IncompatibleUnitsError, GeV


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)
    
#round_to_n = lambda x, n: round(x, -int(floor(log10(x))) + (n - 1))
def round_to_n ( x, n ):
    if x==0.: return x
    return round(x, -int(floor(log10(x))) + (n - 1))

            
class StandardTWiki(object):
    
    """
    Holds all information for the creation of
    twiki.txt 
    The string representation of this class can 
    be used to create a new entry for:
    http://smodels.hephy.at/wiki/DataSource
    """
    
    def __init__(self, metaInfo):
        
        """
        Initialize the object with empty lists
        only the entry for the first column in the twiki 
        table is build
        
        :param metaInfo: inputObjects.MetaInfoInput-object
        """
        
        self.id = self.idFormat(metaInfo)      
        self.txNames = []
        self.axes = []
        self.figures = []
        self.limits = []
        self.exclusions = []
        self.efficiencies = []
        
    def __str__(self):
        
        """
        :return: string holding all informations in a format 
        readable by MoinMoin Wiki. The string can be used 
        as a table entry for:
        http://smodels.hephy.at/wiki/DataSource
        """

        string = '||%s||' %(self.id)
        for attr in \
        [self.txNames, self.axes, self.figures, self.limits,\
        self.efficiencies, self.exclusions]:
            string = string + '<<BR>>'.join(attr) + '||'
        return string + '\n'
    
    def addMassPlane(self, txName, plane):
        
        """
        takes all informations needed for the twiki entry
        from given txName and mass plane.
        Builds standardized entries for the columns of
        the twiki table 
        
        :param txName: name of the related TxName-object
        :param plane: inputObjects.MassPlane-object
        """
            
        self.txNames.append(self.link('SmsDictionary#%s' %txName, txName))
        #print "[standardObjects] appending",str(plane.origPlot),"to",\
        #    txName
        self.axes.append(str(plane.origPlot))
        self.figures.append(self.link(plane.figureUrl, plane.figure))
        self.limits.append(self.objectFormat(plane.origLimits))
        self.exclusions.append(self.objectFormat(plane.origExclusions))
        self.efficiencies.append(self.objectFormat([plane.efficiencyMap]))

    def link(self, url, label):
        
        """
        :param url: url of the link as string
        :param label: label of the link as string
        :return: standardized link for the twiki as string
        """
        
        return '[[%s|%s]]' %(url, label)    
      
    def idFormat(self, metaInfo):
        
        """
        :param metaInfo: inputObjects.MetaInfoInput-object
        :return: standardized string for the first column of the tWiki table
        """
        
        ID = self.link(metaInfo.url, metaInfo.id)
        if hasattr(metaInfo, 'supersededBy'):
            ID = '%s<<BR>>ss_by: %s' %(ID, metaInfo.supersededBy)
        return ID
    
    def objectFormat(self, objectList):
        
        """
        Builds standardized entries for the the following
        columns of the twiki entry:
        -upper limits on production cross sections
        -efficiency maps
        -exclusion lines
        
        :param objectList: list of origDataObjects
        :return: standardized entries for the twiki table
        """
        
        string = ''
        for obj in objectList:
            if not obj.dataUrl: continue
            label = 'OBS'
            if 'efficiency' in obj.name: label = 'EFF'
            if 'expected' in obj.name: label = 'EXP'
            if 'M1' in obj.name: label = '-'
            if 'P1' in obj.name: label = '+'
            string = string + self.link(obj.dataUrl, label)
        if not string: string = 'None'
        return string
      

        
