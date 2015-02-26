#!/usr/bin/env python

"""
.. module:: validationObjs
   :synopsis: Main classes and methods for generating a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
from ROOT import TFile,TGraph,TMultiGraph,TCanvas
from smodels.tools.physicsUnits import fb, GeV
from gridSModelS import runSModelSFor

logger.setLevel(level=logging.DEBUG)



class ValidationPlot():
    """
    Encapsulates all the data necessary for creating a single validation plot.
    """
    
    def __init__(self, ExptRes, TxName, Axes, slhadir=None, databasePath=None):
    
        self.expRes = ExptRes
        self.txname = TxName
        self.axes = Axes
        self.slhaDir = None
        self.data = None
        self.officialCurve = self.getOfficialCurve()
        
        if slhadir: self.setSLHAdir(slhadir)
        if databasePath:
            if os.path.isdir(databasePath):
                self.database = databasePath
            else:
                logger.error("Database folder "+databasePath+" does not exist")
                sys.exit()
        #Try to guess the path:
        else:
            anaID = ExptRes.getValuesFor('id')
            self.database = ExptRes.path[:ExptRes.path.find('/'+anaID)]
            self.database = self.database[:self.database.rfind('/')]
            self.database = self.database[:self.database.rfind('/')+1]
            if not os.path.isdir(self.database):
                logger.error("Could not define database folder")
                sys.exit()
        
    def __str__(self):
        
        vstr = "Validation plot for\n"
        vstr += 'id: '+self.expRes.getValuesFor('id')+'\n'
        vstr += 'TxName: '+str(self.txname)+'\n'
        vstr += 'Axes: '+self.axes
        return vstr
    
    def setSLHAdir(self,slhadir):
        """
        Defines the folder which contains all the slha files to be
        used to generate the validation plot
        
        :param slhadir: existing folder containing SLHA files
        """
        
        if not os.path.isdir(slhadir):
            logger.error("Folder containing SLHA files not found for "+str(self))
            sys.exit()
        else:
            self.slhaDir = slhadir
            
    def getOfficialCurve(self):
        """
        Reads the root file associated to the ExpRes and
        obtain the experimental exclusion curve for the corresponding TxName and Axes.
        Saves the exclusion curve in self.officialCurve
        
        :return: a root TGraph object    
        """
        
        rootpath = os.path.join(self.expRes.path,'sms.root')
        if not os.path.isfile(rootpath):
            logger.error("Root file not found for "+str(self)+" in "+rootpath)
            sys.exit()
        
        rootFile = TFile(rootpath)
        tgraph = rootFile.Get(self.txname.getInfo('txname')+'/exclusion_'+self.axes)
        if not isinstance(tgraph,TGraph):
            logger.warning("Exclusion curve found for "+str(self)+" in "+rootpath)
            return None
        else: return tgraph
        
    def getData(self):
        """
        Runs SModelS on the SLHA files listed in slhaDir and
        returns the list of excluded and allowed points.
        """
        
        self.data = runSModelSFor(self)
        
    def generatePlot(self):
        """
        Uses the data in self.data and the official exclusion curve
        in self.officialCurve to generate the exclusion plot
        """
        
        self.plot = createPlot(self)
            
        
        
        
        
    
