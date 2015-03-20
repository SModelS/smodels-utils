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
StandardDataList, StandardExclusions, StandardTWiki, StandardDataInfo
from smodels_utils.dataPreparation.vertexChecking import VertexChecker
from preparationHelper import ObjectList
import logging
from datetime import date

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

         
        
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
    -info.txt
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

        self.exclusions = []
        self.metaInfo = None
        self.base = os.getcwd() + '/'
        self.origPath = './orig/'
        self.twikitxtPath = self.origPath + 'twiki.txt'
        self.validationPath = './validation/'
        self.smsrootFile = "./sms.root"
        self.infoFileDirectory = './data/'
        self.infoFileExtension = '.txt'
        self.metaInfoFileDirectory = './'
        self.metaInfoFileName = 'info'
        self.assignmentOperator = ': '
        self.txNameField = 'txname'
        list.__init__(self)
            
    def create(self):
        
        """
        main method of the class
        This method calls all other methods of the class
        
        The following working steps are performed:
        --date of last update is evaluated
        --old database files are deleted 
        --write info.txt 
        --a empty StandardDataInfo-object is built
        --a empty StandardTWiki-object is built
        --a validation folder is created and a validate.py script is added
        --loop over all txNames:
        ----VertexChecker-object is build
        ----empty StandardDataList objects are build for:
            upperLimits, expectedUpperLimits and efficiencyMaps 
        ----self.exclusions is appended with an empty StandardExclusions-object
        ----loop over all mass planes:
        ------extending upperLimits, expectedUpperLimits and efficiencyMaps
              and setting all kinematic region to True if the exist
        ------checking published data
        ------setting all kin region to False if the are not True until now
        ------extending StandardExclusions
        ------pass massplane to dataInfo
        ------extending StandardTWiki
        ----extend TxNames with some attributes, to be written to txName.txt
        ----checking if constraint, condition and fuzzycondition are set for 
            every existing kin. region
        ----write txName.txt
        --write sms.root
        --write twiki.txt
        --write datainfo.txt
        
        :raise requiredError: If a region exist, but no constraint, condition 
        or fuzzycondition is set for this region
        """
        
        print '\n***starting creation of database entry for %s***\n'\
        %self.metaInfo.id
        
        self._extendInfoAttr(self.metaInfo, 'lastUpdate')
        self._setLastUpdate()
        self._delete()
        self._createInfoFile(self.metaInfoFileName, self.metaInfo)
        self._createValidationFolder ()

        self.tWiki = StandardTWiki(self.metaInfo)
        
        publishedData = True

        hasUpperLimits = False
        for txName in self:
            
            print '\nreading: %s' %txName.name
            
            if not hasattr(txName.on, 'constraint'): 
                Errors().missingOnConstraint(txName.name)
            vertexChecker = VertexChecker(txName.name, txName.on.constraint )
            upperLimits = StandardDataList()
            print "upperLimits=",upperLimits
            expectedUpperLimits = StandardDataList()
            efficiencyMap = StandardDataList(valueUnit ='')
            
            dataInfo = StandardDataInfo()
            
            exclusions = ObjectList('name')
            for region in txName.kinematicRegions:
                exclusions.append\
                (StandardExclusions(txName.name + region.topoExtension))
            
            for plane in txName.planes:
                
                print '\nreading mass plane: %s\n' %plane.origPlot
                
                efficiencyMap = self.extendDataList\
                (efficiencyMap, plane, vertexChecker, txName)
                upperLimits = self.extendDataList\
                (upperLimits, plane, vertexChecker, txName, 'limit')
                expectedUpperLimits = self.extendDataList(expectedUpperLimits,\
                plane, vertexChecker, txName, 'expectedlimit')
                
                print 'extending upperLimits to %s entrys'\
                %len(upperLimits)
                print 'extending expectedUpperLimits to %s entrys'\
                %len(expectedUpperLimits)
                print 'extending efficiencyMap to %s entrys'\
                %len(efficiencyMap)
                
                if plane.obsUpperLimit or plane.efficiencyMap:
                    if not plane.obsUpperLimit.dataUrl and \
                    not plane.efficiencyMap.dataUrl: 
                        publishedData = False
                    
                for region in txName.kinematicRegions:      
                    if getattr(plane, region.name) == 'auto' \
                    or getattr(plane, region.name) == False:
                        setattr(plane, region.name, False)
                    else:
                        exclusions[getattr(region, self.txNameField)]\
                        .addMassPlane(plane)
                        print 'Found region: %s' %region.name
                        
                for excl in exclusions:
                    print 'extend exclusionLines for %s to %s entrys'\
                    %(excl.name, len(excl))
                    
                dataInfo.checkMassPlane(plane)
                self.tWiki.addMassPlane(txName.name,plane)

            for excl in exclusions: 
                if excl: self.exclusions.append(excl)
            self._extendInfoAttr(txName, 'publishedData')
            self._extendInfoAttr(txName, 'upperLimits')
            self._extendInfoAttr(txName, 'expectedUpperLimits')
            self._extendInfoAttr(txName, 'efficiencyMap')
            if upperLimits: txName.upperLimits = upperLimits
            if expectedUpperLimits: txName.expectedUpperLimits =\
            expectedUpperLimits
            if efficiencyMap: txName.efficiencyMap = efficiencyMap
            txName.publishedData = publishedData

            for region in txName.kinematicRegions:
                if getattr(txName, region.name):
                    if not hasattr(region, 'constraint'):
                        Errors().required(txName.name, region, 'constraint')
                    if not hasattr(region, 'condition'):
                        Errors().required(txName.name, region, 'condition')
                    if not hasattr(region, 'fuzzycondition'):
                        Errors().required(txName.name, region, 'fuzzycondition')
                    self._createInfoFile(getattr(region, self.txNameField), region, txName)
        self._createInfoFile( dataInfo.name, dataInfo)

   
        
        self._createSmsRoot()
        self._createTwikiTxt()
   
        
    def extendDataList(self, dataList, plane, vertexChecker, txName, limitType = None):
        
        """
        extend the given data list by the values related to this type of list
        examples for data lists are ; upperLimits, efficiencyMaps, ....
        The values held by the given mass plane are extended to the data list
        
        calls self._computeKinRegions to check the kin, regions
        
        :param dataList: standardObjects.StandardDataList-object
        :param plane: inputObjects.MetaInfoInput-object
        :param vertexChecker: standardObjects.VertexChecker-object
        :param txName: inputObjects.TxNameInput-object
        :param limitType: type of the given data list, None for
        efficiency maps, else: name of the related origData-object
        :return: data list, extended by the values given by plane
        """
        
        
        if limitType:
            origData = plane.origLimits[limitType] 
        else:
            origData = plane.origEfficiencyMap
        if not origData: return dataList
               
        for i,value in enumerate(origData):
            x = value[0] 
            y = value[1]
            value = value[2]
            massArray = plane.origPlot.getParticleMasses(x,y)
            #massArray = [massPoints,massPoints]
            dataList.append(massArray, value)
            self._computeKinRegions(massArray, i, plane, vertexChecker, txName, limitType )
        return dataList
        
    def _computeKinRegions(self, massArray, i, plane, vertexChecker, txName, limitType ):
        
        """
        checks to which kin reagion a mass array belongs 
        A mass array belongs not only to a kin. region, but also to 
        a mass plane. If a single mass array of a mass plane belongs
        to a specific kin region, the whole mass plane belongs to that 
        region and the -region-exist' attr. is set to True 
        
        Only if the region-exist' attr. is set to 'auto' this automated scan of 
        region is performed, else the predefined settings (True/False)
        of this attr. is used to determine if the mass plane belongs
        to the region
        
        If the region exist (means at least on mass Array belongs to it)
        self._setRegionAttr is called to set the attributes
        which belong to the region
        
        :param massArray: list containing two other lists. Each list contains 
        floats, representing the masses of the particles of each branch in GeV
        :param i: loop-index of outer loop
        :param plane: inputObjects.MetaInfoInput-objects
        :param vertexChecker: standardObjects.VertexChecker-object
        :param txName: inputObjects.TxNameInput-object
        :param limitType: type off limit (limit, expectedlimit, or None for efficiencyMap)
        :raise kinRegionSetterError: if the 'region-exist' is not True, False or 'auto'
        """
        
        kinRegions = txName.kinematicRegions  
        for region in kinRegions:
            regionExist = getattr(plane, region.name)
            if not regionExist == 'auto':
                if not isinstance(regionExist , bool):
                    Errors().kinRegionSetter(txName.name, region.name, \
                    regionPreSet)
                if regionExist == True and i == 0 and limitType != "expectedlimit":
                    self._setRegionAttr(txName, region, plane)
                continue
            if not vertexChecker: 
                Errors().notAssigned(txName.name)
            offShellVertices = \
            vertexChecker.getOffShellVertices(massArray)
            if region.checkoffShellVertices(offShellVertices) and limitType != "expectedlimit":
                setattr(plane, region.name, True)
                self._setRegionAttr(txName, region, plane)
    
        kinRegions = txName.kinematicRegions
        
        
    def _setRegionAttr(self, txName, region, plane):
        
        """
        The list infoAttr of inputObjects.KinematicRegion-class
        is extended by some attributes which will be written
        to txname.txt

        :param plane: inputObjects.MetaInfoInput-object
        :param txName: inputObjects.TxNameInput-object
        :param region: inputObjects.KinematicRegion-object
        """ 
        
        self._extendInfoAttr(region, self.txNameField,0)
        setattr(region, self.txNameField, txName.name + region.topoExtension)
        self._extendInfoAttr(region, 'validated')
        region.validated = None
        self._extendInfoAttr(region, 'axes')
        if not hasattr(region, 'axes'):
            region.axes = str(plane.origPlot)
        else:
            region.axes = region.axes + ';' +\
            str(plane.origPlot)
        if not hasattr(region, 'figureUrl'):
            region.figureUrl=plane.figureUrl
        else:
            region.figureUrl += ";" + plane.figureUrl
    
    
    def _extendInfoAttr(self, obj, attr, position = None):
        
        """
        checks if an attribute is in the list  'infoAttr' 
        of the given object
        If not: writes the attribute to the list.
        
        :param obj: any instance of a child-class of preparationHelper.Locker
        :param attr: name of the attribute as string
        :position: position were do add the attribute, if None:
        add the attr. to the end of the list
        """
  
    
        if attr in obj.infoAttr: return
        if position == None:
            obj.infoAttr.append(attr)
            return
        obj.infoAttr.insert(position, attr)
        
        
    def _setLastUpdate(self):
        
        """
        checks if there is already a info,txt file. If there is, the lastUpdate
        field and the implemented_by field is read.
        If there is no old info.txt, lastUpdate for the info.txt is set to current date.
        If there is an old file, the user is asked if the last update should be
        overwritten with current date
        When last update is overwritten, self._setImplementedBy is called
        """
        
        if os.path.isfile(self.base + self.infoFilePath(self.metaInfoFileName)):
            lastUpdate = False
            implemented_by = False
            oldInfo = open(self.base + self.infoFilePath(self.metaInfoFileName))
            lines = oldInfo.readlines()
            oldInfo.close()
            for line in lines:
                if 'lastUpdate' in line:
                    lastUpdate = line.split(self.assignmentOperator)[1]
                    lastUpdate = lastUpdate.replace('\n','')
                if 'implemented_by' in line:
                    implemented_by = line.split(self.assignmentOperator)[1]
                    implemented_by = implemented_by.replace('\n','')
            if lastUpdate:
                while True:
                    m = 'if one of the following data are changed, '
                    m = m + 'lastUpdate should be overwritten:\n'
                    m = m + 'number or name of txNames, arXiv, publication,'
                    m = m + ' upperLimits\n'
                    m = m + 'overwrite lastUpdate (y/n)?:'
                    answer = raw_input(m)
                    if answer == 'y' or answer == 'n': break
                if answer == 'n': 
                    self.metaInfo.lastUpdate = lastUpdate
                    if not implemented_by: self._setImplementedBy()
                    else: self.metaInfo.implemented_by = implemented_by
                    return
        today = date.today()
        today = '%s/%s/%s\n' %(today.year, today.month, today.day)
        self.metaInfo.lastUpdate = today
        self._setImplementedBy()
        
    def _setImplementedBy(self):
        
        """
        set implemented_by attribute of self.metaInfo
        from comand line
        """
        
        while True:
            answer = raw_input('enter your name or initials: ')
            if answer: break
        self.metaInfo.implemented_by = answer
        
        
    def _delete(self):
        
        """
        deletes all old info.txt, txName.txt, sms.root and twiki.txt files
        """
        
        predefinedPaths = [
            self.base + self.smsrootFile,
            self.base + self.twikitxtPath,
            self.base + self.infoFilePath(self.metaInfoFileName)
            ]
        for path in predefinedPaths:
            if os.path.exists(path): os.remove(path)
        
        try:
            for entry in os.listdir(self.base + self.infoFileDirectory):
                if not entry[-len(self.infoFileExtension):] == self.infoFileExtension:
                    continue
                compareLine = '%s%s%s\n' %(self.txNameField,\
                self.assignmentOperator, entry[:-len(self.infoFileExtension):])
                f = open( self.base + self.infoFileDirectory + entry,'r')
                lines = f.readlines()
                f.close()
                if not compareLine in lines: continue
                os.remove( self.base + self.infoFileDirectory + entry)
        except OSError,e:
            pass

    def _createValidationFolder(self):
        """ create the validation folder and populate it with validate.py """
        if not os.path.exists ( self.validationPath ):
            os.mkdir ( self.validationPath )
        import inspect, commands
        path = inspect.getfile ( self._createValidationFolder )
        path=path.replace( "smodels_utils/dataPreparation/databaseCreation.py", "validation/scripts" )
        scripts = [ "validate.py", "validateTx.py", "plotValidation.py" ]
        for i in scripts:
            if not os.path.exists ( "%s/%s" % ( self.validationPath, i ) ):
                cmd = "cp %s/%s %s" % ( path, i, self.validationPath ) 
                print cmd
                print commands.getoutput ( "cp %s/%s %s" % ( path, i, self.validationPath ) )
        ### fixme add a few more, txname specific, only the plotting, etc ###


    def _createSmsRoot(self):
        
        """
        creates the sms.root file
        """

        #if not os.path.exists ( self.validationPath ):
        #    os.mkdir ( self.validationPath )
    
        smsRoot = ROOT.TFile(self.base + self.smsrootFile,'recreate')
        for exclusions in self.exclusions:
            directory = smsRoot.mkdir(exclusions.name, exclusions.name)
            directory.cd()
            for exclusion in exclusions: exclusion.Write()
        smsRoot.Close()
        
    def _createTwikiTxt(self):
        
        """
        creates the twiki.txt file
        """
        if not os.path.exists ( self.base + self.origPath ):
            os.mkdir ( self.base + self.origPath )

        
        twikiTxt = open(self.base + self.twikitxtPath,'w')
        twikiTxt.write('%s' %self.tWiki)
        twikiTxt.close()
        
    def _createInfoFile(self, name, *objects):
        
        """
        creates a file of type .txt
        all attributes defined in the list called 'infoAttr'
        of the given objects are written to this txt file
        :param name: name of the file (without extension)
        :param *objects: objects containing attributes which will be
        written to the file. The object must have a list called
        'infoAttr' to define what attributes should be written  
        """
        
        content = ''
        for obj in objects:
            for attr in obj.infoAttr:
                if not hasattr(obj, attr) and \
                not hasattr(obj.__class__, attr) : continue
                content = '%s%s%s%s\n' %(content, attr,\
                self.assignmentOperator, getattr(obj, attr))
        infoFile = open(self.base + self.infoFilePath(name), 'w')
        infoFile.write(content)
        infoFile.close()
        
    def infoFilePath(self, infoFileName):
        """
        :param infoFileName: name of requested file without extension
        :return: path of info-file with given name
        """

        directory = self.infoFileDirectory
        if infoFileName=="info":
            directory = self.metaInfoFileDirectory

        if not os.path.exists ( directory ):
            os.mkdir ( directory )
        
        path = '%s%s%s' %(directory, infoFileName, self.infoFileExtension)
        return path
        
databaseCreator = DatabaseCreator()   

class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'

    def required(self, txName, kinObj, attr):
        
        m = self._starLine
        m = m + "there is an %s-region for %s " %(kinObj.name, txName) 
        m = m + "but no %s for this region\n" %attr
        m = m + "use txName.%s.%s " %(kinObj.topoExtension, attr)
        m = m + "to set %s" %attr
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def kinRegionSetter(self, txName, name, value):
    
        m = self._starLine
        m = m + "in txName %s'\n" %txName
        m = m + "setter for propertsy %s must be of bool type or 'auto'\n"\
        %(name)
        m = m + 'got: %s' %value
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def missingOnConstraint(self, txName):
        
        m = self._starLine#
        m = m + "in txName %s: on.constraint not set\n" %txName
        m = m + "onShell constraint have to be set for automated splitting\n"
        m = m + 'please use: %s.on.constraint =' %txName
        m = m + self._starLine
        print(m)
        sys.exit()
        
        
        
             
