#!/usr/bin/env python

"""
.. module:: databaseCreation
   :synopsis: Holds objects used by convert.py to create globalInfo.txt,
              sms.root, sms.py and newSms.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys
import os
import shutil
import ROOT
import logging
from datetime import date
from smodels.tools.physicsUnits import fb, pb,IncompatibleUnitsError,GeV,TeV
from math import floor, log10
from unum import Unum  
import time

Unum.VALUE_FORMAT = "%.4E"

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

limitCache={}


class DatabaseCreator(list):

    """
    list-object
    main class of smodels_utils.dataPreparation
    Holds all TxNameInput-objects and the MetaInfo-object
    The classes defined in the module standardObjects are used
    to create the database entry for one publication
    The following files are created by this class:
    -sms.root
    -twiki.txt
    -globalInfo.txt
    -txName.txt (one for every txName and every kin. region,
    if the kin. region exist)
    """

    def __init__(self):

        """
        initialize the object
        names and paths of the files to be created
        are defined, as well as some other strings
        used in those files
        """

        self.t0 = time.time()
        self.exclusions = []
        self.metaInfo = None
        self.base = os.getcwd() + '/'
        self.origPath = './orig/'
        self.twikitxtPath = self.origPath + 'twiki.txt'
        self.validationPath = './validation/'
        self.smsrootFile = "./sms.root"
        self.infoFileExtension = '.txt'
        self.metaInfoFileDirectory = './'
        self.metaInfoFileName = 'globalInfo'
        self.assignmentOperator = ': '
        # colorScheme: light for dark background, dark for light background
        #              None for monochrome
        self.colorScheme = "light" ## "dark", None
        list.__init__(self)

    def timeStamp ( self, txt, c="info" ):
        color, reset = '\x1b[32m', '\x1b[39m'
        if self.colorScheme in [ None, "None", "mono" ]:
            color, reset = "", ""
        else:
            #colors = { "yellow": '\x1b[33m', "red": '\x1b[31m', "blue": '\x1b[34m', \
            #           "white": '\x1b[37m' }
            colors = {}
            if self.colorScheme == "light":
                colors = { "info": '\x1b[33m', "error": '\x1b[31m', 
                           "warn": '\x1b[34m', "debug": '\x1b[37m' }
            if self.colorScheme == "dark":
                colors = { "info": '\x1b[33m', "error": '\x1b[31m', 
                           "warn": '\x1b[34m', "debug": '\x1b[30m' }
            if c in colors: 
                color = colors[c]
            else:
                self.timeStamp ( "do not know message level %s" % c, "error" )

        dt = time.time() - self.t0
        name=""
        # name="databaseCreation:"
        print ( "[%s%.1fs] %s%s%s" % ( name, dt, color, txt, reset ) )

    def describeMap ( self, Map ):
        """ simple method to describe quickly method in a string """
        ret=""
        if len(Map)==0:
            return ret
        m=str(Map[0]).replace("'","")
        ret = ">>> %s ... " % m
        return ret

    def create(self, createAdditional=False, ask_for_name=True):

        """
        main method of the class
        This method calls all other methods of the class

        The following working steps are performed:
        --date of last update is evaluated
        --old database files are deleted
        --write globalInfo.txt
        --loop over datasets
        ----write dataInfo.txt
        ----loop over all txNames:
        ------load data from mass planes
        ------define info for txname
        ------write txname.txt
        --write sms.root
        --write twiki.txt

        :param createAdditional: if true, we dont delete, nor do we create sms.root
        :param ask_for_name: if false, we assume 'ww' to be the author. Use with
        great care!

        :raise requiredError: If a region exist, but no constraint, condition
        or conditionDescription is set for this region
        """
        self.ask_for_name = ask_for_name

        self.timeStamp ( 'create next database entry for %s' % self.metaInfo.id, "error" )

        if not createAdditional:
            self._setLastUpdate()
            self._delete()
            self._createInfoFile(self.metaInfoFileName, self.metaInfo)
            self._createValidationFolder()

        #Loop over datasets:
        for dataset in self:
            #Set current dataset folder (for writing all files below)
            self.dataInfoDirectory = './'+dataset._name
            self.timeStamp ( "reading %s" % dataset, "debug" )            
            #Create dataInfo.txt file:
            if dataset.dataType == 'efficiencyMap':
                if not hasattr(dataset,'upperLimit') or not hasattr(dataset,'expectedUpperLimit'):
                    self.timeStamp("computing upper limits for %s" %str(dataset))
                    dataset.computeStatistics()
            #Write down dataInfo.txt
            self._createInfoFile('dataInfo', dataset)

            #Loop over txnames in datasets:
            for txName in dataset._txnameList:
                if not hasattr(txName, 'constraint'):
                    logger.error('Missing constraint for txname %s' %str(txName))
                    sys.exit()

                #Write down txname.txt                
                txName.getInfo()  #Set txname info attributes
                txName.getData(dataType = dataset.dataType)  #Read source files and load data
                self._createTxnameFile(str(txName), txName)
                
                
                
        
        #Get all exclusion curves and write to sms.root:
        self.exclusions = self.getExclusionCurves()
        self._createSmsRoot(createAdditional)


    def getExclusionCurves(self):
        """
        Get all exclusion curves defined. If there are multiple datasets,
        does not include duplicated exclusion curves.
        
        :return: list with exclusion curves (TGraph objects)
        """
                
        curves = {}
        allCurves = []
        #Loop over datasets
        for dataset in self:
            curves[dataset.dataId] = {}
            datasetCurves = curves[dataset.dataId]
            #Loop over txnames
            for txname in dataset._txnameList:                 
                datasetCurves[txname.txName] = {}
                txnameCurves = datasetCurves[txname.txName]
                for plane in txname._planes:
                    txnameCurves[str(plane)] = {}
                    planeCurves = txnameCurves[str(plane)]
                    for exclusion in plane._exclusionCurves:
                        if not exclusion:
                            continue  #Exclusion source has not been defined                        
                        name = '%s_%s' %(exclusion.name, plane.axes)
                        if name in planeCurves: #Curve already appears in dict
                            continue
                        stGraph = ROOT.TGraph()
                        stGraph.SetName(name)
                        stGraph.SetTitle(name)
                        stGraph.name = exclusion.name
                        stGraph.txname = txname.txName
                        for i,point in enumerate(exclusion):
                            stGraph.SetPoint(i,point[0],point[1])
                        stGraph.SetLineColor ( ROOT.kBlack )
                        if 'expected' in exclusion.name:
                            stGraph.SetLineColor(ROOT.kRed)
                        stGraph.SetLineStyle(1)
                        if 'P1' in exclusion.name or 'M1' in exclusion.name:
                            stGraph.SetLineStyle(2)
                        planeCurves[name] = stGraph
                        allCurves.append(stGraph)
                        
                        
        return allCurves

    def _setLastUpdate(self):

        """
        checks if there is already a globalInfo,txt file. If there is, the lastUpdate
        field and the implementedBy field is read.
        If there is no old globalInfo.txt, lastUpdate for the globalInfo.txt is set to current date.
        If there is an old file, the user is asked if the last update should be
        overwritten with current date
        When last update is overwritten, self._setImplementedBy is called
        """

        if os.path.isfile(self.base + self.infoFilePath(self.metaInfoFileName)):
            lastUpdate = False
            implementedBy = False
            oldInfo = open(self.base + self.infoFilePath(self.metaInfoFileName))
            lines = oldInfo.readlines()
            oldInfo.close()
            for line in lines:
                if 'lastUpdate' in line:
                    lastUpdate = line.split(self.assignmentOperator)[1]
                    lastUpdate = lastUpdate.replace('\n','')
                if 'implementedBy' in line:
                    implementedBy = line.split(self.assignmentOperator)[1]
                    implementedBy = implementedBy.replace('\n','')
            if lastUpdate:
                while True:
                    m = 'if one of the following data are changed, '
                    m = m + 'lastUpdate should be overwritten:\n'
                    m = m + 'number or name of txNames, arXiv, publication,'
                    m = m + ' upperLimits\n'
                    m = m + '(You can turn this off via the environment variable SMODELS_NOUPDATE)\n'
                    m = m + 'overwrite lastUpdate (y/n)?:'
                    answer = 'n'
                    if "SMODELS_NOUPDATE" in os.environ.keys():
                        self.timeStamp ( "SMODELS_NOUPDATE is set!", "error" )
                        break
                    if self.ask_for_name:
                        answer = raw_input(m)
                    if answer == 'y' or answer == 'n': break
                if answer == 'n':
                    self.metaInfo.lastUpdate = lastUpdate
                    if not implementedBy: self._setImplementedBy()
                    else: self.metaInfo.implementedBy = implementedBy
                    return
        today = date.today()
        today = '%s/%s/%s' %(today.year, today.month, today.day)
        self.metaInfo.lastUpdate = today
        self._setImplementedBy()

    def _setImplementedBy(self):

        """
        set implementedBy attribute of self.metaInfo
        from comand line
        """

        while True:
            answer = 'ww'
            if self.ask_for_name:
                answer = raw_input('enter your name or initials: ')
            if answer: break
        initialDict= { "ww": "Wolfgang Waltenberger",
            "WW": "Wolfgang Waltenberger",
            "AL": "Andre Lessa",
            "al": "Andre Lessa",
            "suk": "Suchita Kulkarni",
            "SuK": "Suchita Kulkarni",
            "SUK": "Suchita Kulkarni",
            "fa" : "Federico Ambrogi",
            "ul" : "Ursula Laa",
            "UL" : "Ursula Laa",
            "FA" : "Federico Ambrogi" }
        if answer in initialDict.keys():
            answer=initialDict[answer]

        self.metaInfo.implementedBy = answer

    def _delete(self):

        """
        deletes all old globalInfo.txt, txName.txt, sms.root and twiki.txt files
        """

        #Remove files
        predefinedPaths = [
            self.base + self.smsrootFile,
            self.base + self.twikitxtPath,
            self.base + self.infoFilePath(self.metaInfoFileName)
            ]
        #Remove dataset folders
        datasetFolders = [ os.path.join(self.base,dataset._name) for dataset in self]
        for path in predefinedPaths:
            if os.path.exists(path): os.remove(path)
        for path in datasetFolders:
            if os.path.isdir(path):
                shutil.rmtree(path)


        self.timeStamp ( "cleaned up in %s " % self.base )

    def _createValidationFolder(self):
        """
        Create empty validation folder
        """
        
        if not os.path.exists(self.validationPath):
            os.mkdir(self.validationPath)

    def _createSmsRoot(self,update=False):

        """
        creates the sms.root file
        """
        mode="recreate"
        if update:
            mode="update"

        smsRoot = ROOT.TFile(self.base + self.smsrootFile,mode)
        for exclusion in self.exclusions:
            dirname = exclusion.txname
            if smsRoot.Get(dirname)==None:
                directory = smsRoot.mkdir(dirname, dirname)
            smsRoot.cd(dirname)
            fullname = "%s/%s" % (dirname, exclusion.GetName())
            if smsRoot.Get(fullname) == None:
                self.timeStamp("add %s to sms.root" % fullname, "info")
                exclusion.Write()
        smsRoot.Close()

    def _createInfoFile(self, name, obj):

        """
        creates a file of type .txt
        all attributes defined in the list called 'infoAttr'
        of the given objects are written to this txt file
        :param name: name of the file (without extension)
        :param obj: object containing attributes which will be
        written to the file. The object must have a list called
        'infoAttr' to define what attributes should be written
        """

        content = ''
        
        path = self.infoFilePath(name)

        #Check if all required attributes have been defined:
        for attr in obj.requiredAttr:
            if not hasattr(obj,attr):
                logger.error("Attribute %s must be defined for object type %s" %(attr,type(obj)))
                sys.exit()

        for attr in obj.infoAttr:
            if not hasattr(obj, attr) and \
            not hasattr(obj.__class__, attr) : continue
            value = getattr(obj,attr)
            if value=="":
                continue
            content = '%s%s%s%s\n' % (content, attr,\
                                       self.assignmentOperator, value)

        infoFile = open(self.base + path, 'w')
        self.timeStamp ( "writing %s" % path )
        infoFile.write(content)
        infoFile.close()
        
    def _createTxnameFile(self, name, obj):

        """
        creates a file of type txname.txt
        all attributes defined in the list called 'infoAttr'
        of the given txname obj are written to this txt file.
        The txname data is formatted before being written to the file.
        :param name: name of the file (without extension)
        :param obj: a TxNameInput object containing attributes which will be
        written to the file. The object must have a list called
        'infoAttr' to define what attributes should be written
        """
    
        if not hasattr(obj,'_dataLabels'):
            logger.error('Input obj must be a TxNameInput object')
    
        #Get the dataLabels stored in the txname 
        #(e.g. efficiencyMap, upperLimits, expectedUpperLimits)
        dataLabels = obj._dataLabels
        content = ''
        
        path = self.infoFilePath(name)

        #Check if all required attributes have been defined:
        for attr in obj.requiredAttr:
            if not hasattr(obj,attr):
                logger.error("Attribute %s must be defined for object type %s" %(attr,type(obj)))
                sys.exit()

        for attr in obj.infoAttr:
            if not hasattr(obj,attr) and not hasattr(obj.__class__,attr):
                continue
            value = getattr(obj,attr)
            if value=="":
                continue
            #Leave data for last
            if attr in dataLabels:
                continue
                value = self._formatData(value)            
            
            content = '%s%s%s%s\n' % (content, attr,\
                                       self.assignmentOperator, value)
        for attr in obj.infoAttr:
            if not attr in dataLabels:
                continue
            if not hasattr(obj,attr) and not hasattr(obj.__class__,attr):
                continue
            value = getattr(obj,attr)
            if value=="":
                continue
            
            value = self._formatData(value)
            content = '%s%s%s%s\n' % (content, attr,\
                                       self.assignmentOperator, value)


        infoFile = open(self.base + path, 'w')
        self.timeStamp ( "writing %s" % path )
        infoFile.write(content)
        infoFile.close()
        

    def infoFilePath(self, infoFileName):
        """
        :param infoFileName: name of requested file without extension
        :return: path of info-file with given name
        """
        
        #Define where the file will be written to:
        if infoFileName == "globalInfo":
            directory = self.metaInfoFileDirectory
        else:  #Except for globalInfo, all other files are written to the current dataset folder
            directory = self.dataInfoDirectory            

        if not os.path.exists(directory):
            os.mkdir(directory)

        path = os.path.join(directory, infoFileName.strip()+self.infoFileExtension.strip())
        return path

    def _formatData(self,value):
        """
        Formats the data grid for nice printing in the txname.txt file
        
        :param value: value for the data (in list format)
        """
        
        if not isinstance(value,list):
            logger.error("Data for TxNameInput must be in list format")
            sys.exit()
        
        #First round numbers:
        value = round_list(value)
        #Convert to string:
        vStr = str(value)
        #Replace units:
        vStr = vStr.replace('[GeV]','*GeV').replace('[TeV]','*TeV')
        vStr = vStr.replace('[fb]','*fb').replace('[pb]','*pb')        
        #Break lines:
        vStr = vStr.replace(" ","")
        vStr = vStr.replace('],[[','],\n[[')

        return vStr


def round_list(x, n=5):
    """
    Rounds all values in x down to n digits.
    :param x: value (float) or nested list of floats
    
    :return: x, with all floats rounded to n digits
    """
    
    if isinstance(x,list):
        for i,pt in enumerate(x):
            x[i] = round_list(pt)
        return x
    else:
        if type(x) is type(fb):
            if not x.asNumber():
                return x            
            unit = x/x.asNumber()
            x = x.asNumber()
        else:
            if not x:
                return x
            unit = 1.
        
        return round(x,-int(floor(log10(x))) + (n - 1))*unit

databaseCreator = DatabaseCreator()


