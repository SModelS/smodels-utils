#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds objects used by convert.py to create globalInfo.txt,
              sms.root, sms.py and newSms.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""

import sys
import os
import ROOT
from smodels_utils.dataPreparation.standardObjects import StandardDataList, \
     StandardExclusions, StandardTWiki, StandardDataInfo, round_to_n
from smodels_utils.dataPreparation.vertexChecking import VertexChecker
from preparationHelper import ObjectList
import logging
from datetime import date
from smodels.tools.physicsUnits import fb, pb
import time

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

limitCache={}

def computeLimit ( observed, expected, error, lumi ):
    """ compute limits and cache them """
    from math import floor, log10
    from smodels.tools import statistics
    def r4 ( x ): ## round to four digits
        if x==0.: return x
        return round(x, -int(floor(log10(x))) + (4 - 1))
    ## r4 = lambda x: round(x, -int(floor(log10(x))) + (4 - 1))
    key = "%f %f %f %f" % ( r4(observed), r4(expected), r4(error), r4(lumi.asNumber(1/fb)) )
    if key in limitCache:
        return limitCache[key]
    ul = statistics.upperLimit ( observed, expected, error, lumi, .05, 10000 ).asNumber ( fb )
    ret=str(ul)+"*fb"
    limitCache[key]=ret
    return ret

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
        self.infoFileDirectory = './data/'
        self.infoFileExtension = '.txt'
        self.metaInfoFileDirectory = './'
        self.metaInfoFileName = 'globalInfo'
        self.assignmentOperator = ': '
        self.txNameField = 'txName'
        self.add_axes= {}
        self.addToSmsRootFile = set()
        self.useColors = True
        list.__init__(self)

    def timeStamp ( self, txt, c="green" ):
        color, reset = '\x1b[32m', '\x1b[39m'
        colors = { "yellow": '\x1b[33m', "red": '\x1b[31m', "blue": '\x1b[34m', \
                   "white": '\x1b[37m' }
        if c in colors: color = colors[c]
        if not self.useColors:
            color, reset = "", ""

        dt = time.time() - self.t0
        print "%s[databaseCreation:%.1fs] %s%s" % ( color, dt, txt, reset )

    def describeMap ( self, Map ):
        """ simple method to describe quickly method in a string """
        ret=""
        if len(Map)==0:
            return ret
        m=str(Map[0]).replace("'","")
        ret = ">>> %s ... " % m
        return ret

    def create(self, createAdditional=False, ask_for_name=True, create_dataInfo=True ):

        """
        main method of the class
        This method calls all other methods of the class

        The following working steps are performed:
        --date of last update is evaluated
        --old database files are deleted
        --write globalInfo.txt
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
        ----checking if constraint, condition and conditionDescription are set for
            every existing kin. region
        ----write txName.txt
        --write sms.root
        --write twiki.txt
        --write dataInfo.txt

        :param createAdditional: if true, we dont delete, nor do we create sms.root
        :param ask_for_name: if false, we assume 'ww' to be the author. Use with
        great care!
        :param createDataInfo: if false, we dont create dataInfo.txt

        :raise requiredError: If a region exist, but no constraint, condition
        or conditionDescription is set for this region
        """
        self.ask_for_name = ask_for_name

        self.timeStamp ( 'create next database entry for %s' % self.metaInfo.id, "red" )

        if not createAdditional:
            self._extendInfoAttr(self.metaInfo, 'lastUpdate')
            self._setLastUpdate()
            self._delete()
            self._createInfoFile(self.metaInfoFileName, None, None, self.metaInfo)
            self._createValidationFolder ()

        self.tWiki = StandardTWiki(self.metaInfo)

        publishedData = True

        dataInfo = StandardDataInfo()

        hasUpperLimits = False

        # self.timeStamp ( "before going through txnames" )
        for txName in self:
            self.timeStamp ( "reading %s" % txName )
            dataset=None

            if not hasattr(txName.on, 'constraint'):
                Errors().missingOnConstraint(txName.name)
            self.vertexChecker = VertexChecker(txName.name, txName.on.constraint )
            upperLimits = StandardDataList()
            ## print "upperLimits=",upperLimits
            expectedUpperLimits = StandardDataList()
            efficiencyMap = StandardDataList(valueUnit ='')
            efficiencyMap3D = StandardDataList(valueUnit ='')

            exclusions = ObjectList('name')
            for region in txName.kinematicRegions:
                exclusions.append\
                (StandardExclusions(txName.name + region.topoExtension))

            datasets = []

            for plane in txName.planes:
                if len(datasets)>0 and datasets[0] != plane.origEfficiencyMap.dataset:
                    self.timeStamp ( "wrong dataset of plane!! %s" % plane.origEfficiencyMap.dataset )
                    continue
                datasets.append ( plane.origEfficiencyMap.dataset )
                # print ( "what datasets do we have here? %s" % datasets  )

                if plane.origEfficiencyMap and hasattr ( plane.origEfficiencyMap, "observedN" ):
                    dataInfo.dataset = plane.origEfficiencyMap.dataset
                    dataInfo.observedN = plane.origEfficiencyMap.observedN
                    dataInfo.expectedBG = plane.origEfficiencyMap.expectedBG
                    dataInfo.bgError = plane.origEfficiencyMap.bgError
                    lumi=eval(self.metaInfo.lumi)
                    if create_dataInfo:
                        self.timeStamp ( "computing upper limit for %d/%.1f/%.1f" % ( dataInfo.observedN, dataInfo.expectedBG, dataInfo.bgError ) )
                        dataInfo.upperLimit = computeLimit ( dataInfo.observedN, dataInfo.expectedBG, dataInfo.bgError, lumi )
                        dataInfo.expectedUpperLimit = computeLimit ( dataInfo.expectedBG, dataInfo.expectedBG, dataInfo.bgError, lumi )
                        self.timeStamp ( "done computing upper limit.", "white" )

                self.timeStamp ( 'Reading mass plane: %s, %s [%s][%s]' % (txName, plane.origPlot, str(plane.obsExclusion.path)[-30:], plane.origEfficiencyMap.dataset ) )

                efficiencyMap = self.extendDataList (efficiencyMap, plane, txName)
                if len ( efficiencyMap) > 0:
                    self.timeStamp ( 'extended efficiencyMap of %s to %s entries %s'\
                                    % ( plane.origEfficiencyMap.dataset, len(efficiencyMap), 
                                     self.describeMap ( efficiencyMap ) ), "yellow" )
                efficiencyMap3D = self.extendDataList\
                (efficiencyMap3D, plane, txName)
                self.timeStamp ( 'extended efficiencyMap3D of %s to %s entries %s'\
                    % ( plane.origEfficiencyMap.dataset, len(efficiencyMap3D), 
                        self.describeMap ( efficiencyMap3D ) ), "yellow" )
                upperLimits = self.extendDataList\
                (upperLimits, plane, txName, 'limit')
                if len(upperLimits)>0:
                    self.timeStamp ( 'extended upperLimits to %s entries %s'\
                                   % ( len(upperLimits), self.describeMap ( upperLimits ) ),
                                "yellow" )
                if len(expectedUpperLimits)>0:
                    expectedUpperLimits = self.extendDataList(expectedUpperLimits,\
                                                              plane, txName, 'expectedlimit')
                if len(expectedUpperLimits)>0:
                    self.timeStamp ( 'extended expectedUpperLimits to %s entries %s'\
                                    % ( len(expectedUpperLimits), 
                                        self.describeMap ( expectedUpperLimits ) ) )
                if plane.obsUpperLimit or plane.efficiencyMap or plane.efficiencyMap3D:
                    if not plane.obsUpperLimit.dataUrl and \
                    not plane.efficiencyMap.dataUrl and \
                    not plane.efficiencyMap3D.dataUrl:
                        publishedData = False

                for region in txName.kinematicRegions:
                    #if getattr(plane, region.name) == 'auto' \
                    #or getattr(plane, region.name) == False:
                    if getattr(plane, region.name) == False:
                        setattr(plane, region.name, False)
                    else:
                        exclusions[getattr(region, self.txNameField)]\
                        .addMassPlane(plane)
                        #self.timeStamp ( 'Found region: %s' % ( region.name ) )

                for excl in exclusions:
                    self.timeStamp ( 'extend exclusionLines for %s to %s entries'\
                        %(excl.name, len(excl)) )

                self.timeStamp ( 'Now checking mass plane %s' % plane )
                dataInfo.checkMassPlane(plane)
                self.tWiki.addMassPlane(txName.name,plane)

            for excl in exclusions:
                if excl: self.exclusions.append(excl)
            self._extendInfoAttr(txName, 'publishedData')
            self._extendInfoAttr(txName, 'upperLimits')
            self._extendInfoAttr(txName, 'expectedUpperLimits')
            self._extendInfoAttr(txName, 'efficiencyMap')
            self._extendInfoAttr(txName, 'efficiencyMap3D')
            if upperLimits: txName.upperLimits = upperLimits
            if expectedUpperLimits: txName.expectedUpperLimits =\
            expectedUpperLimits
            if efficiencyMap: txName.efficiencyMap = efficiencyMap
            if efficiencyMap3D: txName.efficiencyMap3D = efficiencyMap3D
            txName.publishedData = publishedData

            self.timeStamp ( "we have %d kin regions" % 
                             len (txName.kinematicRegions ) )
            for region in txName.kinematicRegions:
                if getattr(txName, region.name):
                    if not hasattr(region, 'constraint'):
                        Errors().required(txName.name, region, 'constraint')
                    if not hasattr(region, 'condition'):
                        Errors().required(txName.name, region, 'condition')
                    if not hasattr(region, 'conditionDescription'):
                        Errors().required(txName.name, region, 'conditionDescription')
                    # print "dataInfo.dataId",dataInfo.dataId
                    self._createInfoFile(getattr(region, self.txNameField), region.name, dataInfo.dataId, region, txName )
                    region.figureUrl=""
                    region.dataUrl=""
                    region.axes=""
        # self.timeStamp ( "after going through txnames" )
        if create_dataInfo:
            self._createInfoFile( dataInfo.name, None, dataInfo.dataId, dataInfo)
        self._createSmsRoot( createAdditional )

        if not createAdditional:
            self._createTwikiTxt()
        self.timeStamp ( "done", "white" )


    def extendDataList(self, dataList, plane, txName, limitType = None):

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

        effMap3d=False

        if limitType:
            origData = plane.origLimits[limitType]
        else:
            origData = plane.origEfficiencyMap
            if len(plane.origEfficiencyMap)>0 and len(plane.origEfficiencyMap3D)>0:
               Errors().has2DAnd3DMap(plane)
            if len(plane.origEfficiencyMap)>0:
                origData = plane.origEfficiencyMap
            if len(plane.origEfficiencyMap3D)>0:
                origData = plane.origEfficiencyMap3D
                effMap3d=True

        if not origData: return dataList

        if effMap3d:
            for i,value in enumerate(origData):
                x = value[0]
                y = value[1]
                z = value[2]
                value = value[3]
                massArray = plane.origPlot.getParticleMasses(x,y,z)
                #massArray = [massPoints,massPoints]
                dataList.append(massArray, value)
                self._computeKinRegions(massArray, i, plane, txName, limitType )
            return dataList

        for i,value in enumerate(origData):
            x = value[0]
            y = value[1]
            value = value[2]
            massArray = plane.origPlot.getParticleMasses(x,y)
            #massArray = [massPoints,massPoints]
            # print ( "[databaseCreation] appending %s %s" % ( massArray, value ) )
            dataList.append(massArray, value)
            self._computeKinRegions(massArray, i, plane, txName, limitType )
        return dataList

    def _computeKinRegions(self, massArray, i, plane, txName, limitType ):
        """
        checks to which kin region a mass array belongs
        A mass array belongs not only to a kin. region, but also to
        a mass plane. If a single mass array of a mass plane belongs
        to a specific kin region, the whole mass plane belongs to that
        region and the regionExist attr. is set to True

        Only if the regionExist attr. is set to 'auto' this automated scan of
        region is performed, else the predefined settings (True/False)
        If the region exist (means at least one mass array belongs to it)
        self._setRegionAttr is called to set the attributes
        which belong to the region

        :param massArray: list containing two other lists. Each list contains
        floats, representing the masses of the particles of each branch in GeV
        :param i: loop-index of outer loop
        :param plane: inputObjects.MetaInfoInput-objects
        :param vertexChecker: standardObjects.VertexChecker-object
        :param txName: inputObjects.TxNameInput-object
        :param limitType: type of limit (limit, expectedlimit, 
                          or None for efficiencyMap)
        :raise kinRegionSetterError: raised if the 'regionExist' is not 
                                     True, False or 'auto'
        """

        kinRegions = txName.kinematicRegions
        for region in kinRegions:
            offShellVertices = self.vertexChecker.getOffShellVertices(massArray)
            #add_axes = True
            #if len(offShellVertices)==0 and region.name == "offShell":
            #    add_axes = False
            #if len(offShellVertices)>0 and region.name == "onShell":
            #    add_axes = False
            tn = str(txName)+region.name+str(plane)
            if not tn in self.add_axes:
                self.add_axes[tn]=False
            if len(offShellVertices)>0 and region.name == "offShell":
                self.add_axes[tn] = True
            if len(offShellVertices)==0 and region.name == "onShell":
                self.add_axes[tn] = True
            """
            print "[debug]"
            print "[debug] region.name=",region.name
            print "[debug] plane=",plane
            print "[debug] tn=",tn
            print "[debug] plane.onShell=",plane.onShell
            print "[debug] plane.offShell=",plane.onShell
            print "[debug] offShellVertices=",offShellVertices
            print "[debug] txname=",txName,"region.name=",region.name,"offShell=",\
                    len(offShellVertices)
            print "[debug] add_axes=",self.add_axes[tn]
            """
            if self.add_axes[tn]:
                # print "[_computeKinRegions] add_axes for ",txName.name,plane
                off="off" if region.name == "offShell" else ""
                adde = "%s%s/exclusion_%s" % (txName.name, off, plane)
                self.addToSmsRootFile.add ( adde )
            regionExist = getattr(plane, region.name)
            if not regionExist == 'auto':
                if not isinstance(regionExist , bool):
                    Errors().kinRegionSetter(txName.name, region.name, \
                    regionPreSet)
                if regionExist == True and i == 0 and limitType != "expectedlimit":
                    self._setRegionAttr(txName, region, plane, self.add_axes[tn] )
                continue
            if regionExist == 'auto':
                self._setRegionAttr(txName, region, plane, self.add_axes[tn] )

            if not self.vertexChecker:
                Errors().notAssigned(txName.name)
            if region.checkoffShellVertices(offShellVertices) and \
                       limitType != "expectedlimit":
                setattr(plane, region.name, True )
                ## setattr(plane, region.name, 'auto' )
                self._setRegionAttr(txName, region, plane, self.add_axes[tn] )

        kinRegions = txName.kinematicRegions


    def _setRegionAttr(self, txName, region, plane, add_axes ):

        """
        The list infoAttr of inputObjects.KinematicRegion-class
        is extended by some attributes which will be written
        to txname.txt

        :param plane: inputObjects.MetaInfoInput-object
        :param txName: inputObjects.TxNameInput-object
        :param region: inputObjects.KinematicRegion-object
        """
        #self.timeStamp ( "_setRegionAttr %s add_axes=%d" % ( region, add_axes ) )

        self._extendInfoAttr(region, self.txNameField,0)
        setattr(region, self.txNameField, txName.name + region.topoExtension)
        self._extendInfoAttr(region, 'validated')
        region.validated = None
        if add_axes:
            self._extendRegionAttr(region, 'axes', str(plane.origPlot))
            self._extendRegionAttr(region, 'figureUrl', plane.figureUrl)
            if plane.obsUpperLimit.dataUrl:
                self._extendRegionAttr(region, 'dataUrl', plane.obsUpperLimit.dataUrl)
            if plane.efficiencyMap.dataUrl:
                self._extendRegionAttr(region, 'dataUrl', plane.efficiencyMap.dataUrl)
            if plane.efficiencyMap3D.dataUrl:
                self._extendRegionAttr(region, 'dataUrl', plane.efficiencyMap3D.dataUrl)

    def _extendRegionAttr(self, region, name, value):
        if value in [ None, "" ]: ## we dont add None or empty strings
            return
        if hasattr(region, name):
            previous =getattr (region, name )
            if previous in [ "", None ]:
                self._extendInfoAttr(region, name)
            else:
                if value in previous:
                    value = previous
                else:
                    # dont duplicate entries
                    value = previous + ";" + value
        else:
            self._extendInfoAttr(region, name)
        setattr(region, name, value)


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
                        print "SMODELS_NOUPDATE is set!"
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
        today = '%s/%s/%s\n' %(today.year, today.month, today.day)
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

        self.timeStamp ( "cleaned up in %s " % self.base )

    def _createValidationFolder(self):
        """ create the validation folder and populate it with validate.py """
        if not os.path.exists ( self.validationPath ):
            os.mkdir ( self.validationPath )
        import inspect, commands
        path = inspect.getfile ( self._createValidationFolder )
        self.timeStamp ( "creating validation folder %s" % path )
        path=path.replace( "smodels_utils/dataPreparation/databaseCreation.py", "validation/scripts" )
        # scripts = [ "validate.py", "validateSinglePlot.py"]#, "plotValidation.py" ]
        scripts = [] # for now, no scripts
        for i in scripts:
            if not os.path.exists ( "%s/%s" % ( self.validationPath, i ) ):
                cmd = "cp %s/%s %s" % ( path, i, self.validationPath )
                print cmd
                print commands.getoutput ( "cp %s/%s %s" % ( path, i, self.validationPath ) )
        ### fixme add a few more, txname specific, only the plotting, etc ###


    def _createSmsRoot(self,update=False):

        """
        creates the sms.root file
        """
        mode="recreate"
        if update:
            mode="update"

        smsRoot = ROOT.TFile(self.base + self.smsrootFile,mode)
        for exclusions in self.exclusions:
            dirname = exclusions.name
            if smsRoot.Get( dirname )==None:
                directory = smsRoot.mkdir( dirname, dirname )
            smsRoot.cd ( dirname )
            for exclusion in exclusions: 
                fullname = "%s/%s" % ( dirname, exclusion.GetName() )
                if fullname in self.addToSmsRootFile:
                    if smsRoot.Get( fullname ) == None:
                        self.timeStamp ( "add %s to sms.root" % fullname, "info" )
                        exclusion.Write()
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

    def _createInfoFile(self, name, kinregname, dataid, *objects):

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
        path=self.infoFilePath(name, dataid)
        # self.timeStamp ( "we write to %s for %s" % (path, kinregname) )
        for obj in objects: 
            # in the case of Txname.txt, obj is a Kinematic region
            # self.timeStamp ( "we write %s" % obj )
            add_axes=False
            for attr in obj.infoAttr:
                if not attr in [ "upperLimits", "expectedUpperLimits", \
                                 "efficiencyMap" ]:
                    continue
                add_axes=True

            for attr in obj.infoAttr:
                ## self.timeStamp ( "attr is %s" % attr )
                if attr in [ "efficiencyMap3D" ]: continue
                if not hasattr(obj, attr) and \
                not hasattr(obj.__class__, attr) : continue
                value=getattr(obj,attr)
                if value=="":
                    continue
                if attr in [ "upperLimits", "expectedUpperLimits", "efficiencyMap" ]:
                    ## the next line splits onshell from offshell data points
                    value = self.vertexChecker.filterData( value, kinregname )
                content = '%s%s%s%s\n' % ( content, attr,\
                                           self.assignmentOperator, value )

                if attr == "dataId":
                    path = self.infoFilePath ( name, getattr ( obj, attr ) )
        infoFile = open(self.base + path, 'w')
        self.timeStamp ( "writing %s" % path )
        infoFile.write(content)
        infoFile.close()

    def infoFilePath(self, infoFileName, dataid=None ):
        """
        :param infoFileName: name of requested file without extension
        :return: path of info-file with given name
        """

        directory = self.infoFileDirectory
        if dataid: ## if dataid is given, we name the directory according to the dataid
            directory = dataid + "/"
        if infoFileName=="globalInfo":
            directory = self.metaInfoFileDirectory

        if not os.path.exists ( directory ):
            os.mkdir ( directory )

        path = '%s%s%s' %(directory, infoFileName, self.infoFileExtension)
        # print "[infoFilePath]",path
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

    def has2DAnd3DMap(self, plane):
        m= self._starLine
        m = m + '%s has 2d and 3d plane' % ( plane )
        print(m)
        sys.exit()

    def missingOnConstraint(self, txName):
        m = self._starLine#
        m = m + "in txName %s: on.constraint not set\n" %txName
        m = m + "onShell constraint has to be set for automated splitting\n"
        m = m + 'please use: %s.on.constraint =' %txName
        m = m + self._starLine
        print(m)
        sys.exit()
