#!/usr/bin/env python

"""
.. module:: validationObjs
   :synopsis: Main classes and methods for generating a single validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
#from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment import databaseObj
from smodels.tools.physicsUnits import GeV
from smodels.tools import statistics, modelTester 
from plottingFuncs import createPlot, getExclusionCurvesFor, createSpecialPlot, createTempPlot
import tempfile,tarfile,shutil,copy
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot

logger.setLevel(level=logging.ERROR)



class ValidationPlot():
    """
    Encapsulates all the data necessary for creating a single validation plot.
    
    :ivar ExptRes: ExpResult object containing the experimental result for validation
    :ivar TxNameStr: String describing the txname (e.g. T2tt)
    :ivar Axes: String describing the axes (e.g. 2*Eq(mother,x)_Eq(lsp,y))
    :ivar slhadir: path to the SLHA folder or the tar ball containing the files (string)
    :ivar databasePath: path to the database folder. If not defined, the path from ExptRes.path will be
                        used to extract the database path.
    :ivar kfactor: Common kfactor to be applied to all theory cross-sections (float)
    """

    def __init__(self, ExptRes, TxNameStr, Axes, slhadir=None, databasePath=None,
                 kfactor = 1.):

        self.expRes = copy.deepcopy(ExptRes)
        self.txName = TxNameStr
        self.axes = Axes
        self.slhaDir = None
        self.data = None
        self.officialCurves = self.getOfficialCurve( get_all = True )
        self.kfactor = kfactor

        if slhadir: self.setSLHAdir(slhadir)
        if databasePath:
            if os.path.isdir(databasePath):
                self.databasePath = databasePath
            else:
                logger.error("Database folder "+databasePath+" does not exist")
                sys.exit()
        #Try to guess the path:
        else:
            anaID = ExptRes.getValuesFor('id')[0]
            self.databasePath = ExptRes.path[:ExptRes.path.find('/'+anaID)]
            self.databasePath = self.databasePath[:self.databasePath.rfind('/')]
            self.databasePath = self.databasePath[:self.databasePath.rfind('/')+1]
            if not os.path.isdir(self.databasePath):
                logger.error("Could not define databasePath folder")
                sys.exit()

    def __str__(self):

        vstr = "Validation plot for\n"
        vstr += 'id: '+self.expRes.getValuesFor('id')+'\n'
        vstr += 'TxName: '+self.txName+'\n'
        vstr += 'Axes: '+self.axes
        return vstr

    def computeAgreementFactor ( self, looseness=1.2, signal_factor=1.0 ):
        """ computes how much the plot agrees with the official exclusion curve
            by counting the points that are inside/outside the official
            exclusion curve, and comparing against the points' r values
            ( upper limit / predict theory cross section )
            :param looseness: how much do we loosen the criterion? I.e. by what factor do we
            change the cross sections in favor of getting the right assignment?
            :param signal_factor: an additional factor that is multiplied with the signal cross section,
        """
        import ROOT
        curve = self.getOfficialCurve()        
        if not curve:
            logger.error( "could not get official tgraph curve for %s %s %s" % ( self.expRes,self.txName,self.axes  ) )
            return 1.0
        elif isinstance(curve,list):
            for c in curve:                
                objName = c.GetName()
                if 'exclusion_' in objName:
                    curve = c
                    break
        x0=ROOT.Double()
        y0=ROOT.Double()
        x=ROOT.Double()
        y=ROOT.Double()
        curve.GetPoint ( 0, x0, y0 ) ## get the last point
        curve.GetPoint ( curve.GetN()-1, x, y ) ## get the last point
        curve.SetPoint ( curve.GetN(), x, 0. )  ## extend to y=0
        curve.SetPoint ( curve.GetN(), x0, 0. )  ## extend to first point

        pts= { "total": 0, "excluded_inside": 0, "excluded_outside": 0, "not_excluded_inside": 0,
               "not_excluded_outside": 0, "wrong" : 0 }
        for point in self.data:
            x,y=point["axes"][0],point["axes"][1]
            if y==0: y=1.5 ## to avoid points sitting on the line
            excluded = point["UL"] < point["signal"]
            really_excluded = looseness * point["UL"] < point["signal"] * signal_factor
            really_not_excluded = point["UL"] > looseness * point["signal"] * signal_factor
            inside = curve.IsInside ( x,y )
            pts["total"]+=1
            s=""
            if excluded:
                s="excluded"
            else:
                s="not_excluded"
            if inside:
                s+="_inside"
            else:
                s+="_outside"
            pts[s]+=1
            if really_excluded and not inside:
                pts["wrong"]+=1
            if really_not_excluded and inside:
                pts["wrong"]+=1
        #logger.debug ( "points in categories %s" % str(pts) )
        #print ( "[validationObjs] points in categories %s" % str(pts) )
        if pts["total"]==0:
            return float("nan")
        return 1.0 - float(pts["wrong"]) / float(pts["total"])

    def setSLHAdir(self,slhadir):
        """
        Defines the folder or tar file containing all the slha files to be
        used to generate the validation plot

        :param slhadir: existing folder containing SLHA files
        """

        if not os.path.isdir(slhadir) and not os.path.isfile(slhadir):
            logger.error("SLHA files not found in %s for %s" %(slhadir,str(self)))
            sys.exit()
        else:
            self.slhaDir = slhadir
            
    def getSLHAdir(self):
        """
        Returns path to the folders containing the SLHA files.
        If slhadir is a .tar file, returns a temporary folder where the files
        have been extracted to.
        
        :param slhadir: path to the SLHA folder or the tar ball containing the files (string)
        :return: path to the folder containing the SLHA files
        """
    
        if os.path.isdir(self.slhaDir):
            return self.slhaDir
        elif os.path.isfile(self.slhaDir):
            try:
                tar = tarfile.open(self.slhaDir)
                tempdir = tempfile.mkdtemp(dir=os.getcwd())
                tar.extractall(path=tempdir)
                logger.info("SLHA files extracted to %s" %tempdir)
                return tempdir
            except:
                logger.error("Could not extract SLHA files from %s" %self.slhaDir)
                sys.exit()
        else:
            logger.error("%s is not a file nor a folder" %self.slhaDir)
            sys.exit()            
    
    
    def getOfficialCurve(self, get_all=True ):
        """
        Reads the root file associated to the ExpRes and
        obtain the experimental exclusion curve for the corresponding TxName and Axes.
        
        :param get_all: get also the +- 1 sigma curves

        :return: a root TGraph object
        """
        tgraphDict = getExclusionCurvesFor(self.expRes,txname=self.txName,axes=self.axes, get_all = get_all )
        if not tgraphDict: return None
        tgraph = tgraphDict[self.txName]
        #print "[validationObjs.py] get_all=",get_all
        #for t in tgraph:
        #    print "[validationObjs.py] t=",t
        #    print "[validationObjs.py] name=",t.GetName()
        if get_all:
            return tgraph
        else:
        #if len(tgraph) > 1:
        #    logger.warning("More than one exclusion curve found. Using the first one.")
            return tgraph[0]

    
    def getParameterFile(self,tempdir=None):
        """
        Creates a temporary parameter file to be passed to runSModelS
        
        :param tempdir: Temporary folder where the parameter file will be created. Default = current folder.
        """
        
        #Get the analysis ID, txname and dataset ID:
        expId = self.expRes.globalInfo.id
        txname = self.expRes.getTxNames()[0].txName
        
        if tempdir is None: tempdir = os.getcwd()
        pf, parFile = tempfile.mkstemp(dir=tempdir,prefix='parameter_',suffix='.ini')
        
        os.write(pf,"[path]\ndatabasePath = %s\n" %self.databasePath)
        os.write(pf,"[options]\ninputType = SLHA\ncheckInput = True\ndoInvisible = True\ndoCompress = True\ntestCoverage = False\n")
        os.write(pf,"[parameters]\nsigmacut = 0.000000001\nminmassgap = 2.0\nmaxcond = 1.\nncpus = -1\n")
        os.write(pf,"[database]\nanalyses = %s\ntxnames = %s\ndataselector = all\n" % (expId,txname))
        os.write(pf,"[stdout]\nprintDecomp = False\naddElmentInfo = False\nprintAnalyses = False\naddAnaInfo = False\noutputType = python\n")
        os.write(pf,"[file]\nexpandedSummary = True\naddConstraintInfo = True\n")
        
        os.close(pf)
        return parFile
    
    def getData(self):
        """
        Runs SModelS on the SLHA files from self.slhaDir and store
        the relevant data in self.data.
        Uses runSModelS.main.
        """

        #Get list of SLHA files:
        if not self.slhaDir:
            logger.warning("SLHA folder not defined")
            return False
        slhaDir = self.getSLHAdir()  #Path to the folder containing the SLHA files
        logger.info("SLHA files for validation at %s" %slhaDir)
        
        #Set temporary outputdir:
        outputDir = tempfile.mkdtemp(dir=slhaDir,prefix='results_')
        
        #Get parameter file:
        parameterFile = self.getParameterFile(tempdir=outputDir)
        logger.info("Parameter file: %s" %parameterFile)
        
        #Read and check parameter file, exit parameterFile does not exist
        parser = modelTester.getParameters(parameterFile)

        #Get list of input files to be tested
        fileList = modelTester.getAllInputFiles(slhaDir)

        #Select the desired txnames and experimental result:
        for dataset in self.expRes.datasets:
            dataset.txnameList = [tx for tx in dataset.txnameList[:] if tx.txName == self.txName]
        listOfExpRes = [self.expRes]

        """ Test all input points """
        modelTester.testPoints(fileList, slhaDir, outputDir, parser, 'validation', 
                 listOfExpRes, 1000, False, parameterFile) 

        #Define original plot
        origPlot = OrigPlot.fromString(self.axes)        
        #Now read the output and collect the necessary data
        self.data = []
        for slhafile in os.listdir(slhaDir):
            if not os.path.isfile(os.path.join(slhaDir,slhafile)):  #Exclude the results folder
                continue
            fout = os.path.join(outputDir,slhafile + '.py')            
            if not os.path.isfile(fout):
                logger.error("No SModelS output found for %s \n" %slhafile)
                continue            
            f = open(fout,'r')
            exec(f.read().replace('\n',''))
            f.close()
            if not 'ExptRes' in smodelsOutput:
                logger.info("No results for %s \n" %slhafile)
                continue 
            res = smodelsOutput['ExptRes']
            if len(res) != 1:
                logger.warning("More than one result found for %s \n" %slhafile)
            for expRes in res:
                if expRes['AnalysisID'] != self.expRes.globalInfo.id:
                    continue
                txnames = [tx.txName for tx in self.expRes.getTxNames()] 
                if txnames != expRes['TxNames']:
                    continue
                mass = expRes['Mass (GeV)']                
                v = origPlot.getXYValues(mass)
                if v == None:
                    logger.info("dropping %s, doesnt fall into the plane of %s." % (slhafile, origPlot.string ) )
                    continue
                x,y = v
                Dict = {'slhafile' : slhafile, 'axes': [x,y], 'signal' : expRes['theory prediction (fb)'],
                         'UL' : expRes['upper limit (fb)'], 'condition': expRes['maxcond'],
                         'dataset': expRes['DataSetID']}                
                if expRes['dataType'] == 'efficiencyMap':
                    dataset = self.expRes.datasets[0]
                    massGeV = [[m*GeV for m in mbr] for mbr in mass]
                    Dict['efficiency'] = dataset.txnameList[0].txnameData.getValueFor(massGeV)
                    expectedBG = dataset.dataInfo.expectedBG
                    observedN = dataset.dataInfo.observedN
                    bgError = dataset.dataInfo.bgError
                    lumi = expRes.globalInfo.lumi
                    CLs = statistics.CLs(observedN, expectedBG, bgError, Dict['signal']*lumi, 10000)                    
                    Dict['CLs'] =CLs
                self.data.append(Dict)
    
        #Remove temporary folder
        if slhaDir != self.slhaDir: shutil.rmtree(slhaDir)
            
        if self.data == []:
            logger.error ( "There are no data for a validation plot. Are the SLHA files correct? Are the constraints correct?" )
        
        #Apply k-factors to theory prediction (default is 1)
        for ipt,pt in enumerate(self.data):
            pt['signal'] *= self.kfactor 
            self.data[ipt] = pt
            self.data[ipt]['kfactor'] = self.kfactor

    def getPlot(self,silentMode=True):
        """
        Uses the data in self.data and the official exclusion curve
        in self.officialCurves to generate the exclusion plot
        :param silentMode: If True the plot will not be shown on the screen
        """

        self.plot,self.base = createPlot(self,silentMode)


    def getSpecialPlot(self,silentMode=True,what = "bestregion", nthpoint = 1,signal_factor = 1.0 ):
        """ get one of the special plots.
            :param what: which special plot
                         bestregion = best analysis/cut pair 
                         upperlimits = upper limits on prod xsec (pb) 
                         crosssections = theory prediction, in pb
                         efficiencies = efficiency (=1 for UL results)
            :param nthpoint: plot only every nth point
            :param signal_factor: an additional factor that is multiplied with the signal cross section,
        """
        self.plot = createSpecialPlot( self, silentMode, 1.2, what, nthpoint, signal_factor )
        
    def getTempPlot(self,silentMode=True,what = "R", nthpoint = 1,signal_factor = 1.0 ):
        """ get one of the special plots.
            :param what: which special plot
                         R = theory prediction/upper limit 
                         upperlimits = upper limits on prod xsec (pb) 
                         crosssections = theory prediction, in pb
            :param nthpoint: plot only every nth point
            :param signal_factor: an additional factor that is multiplied with the signal cross section,
        """
        self.plot = createTempPlot(self, silentMode, what, nthpoint, signal_factor)
        

    def savePlot(self,validationDir=None,format='pdf'):
        """
        Saves the plot in .pdf format in the validationDir folder.
        If the folder does not exist, it will be created.
        If the folder is not defined the plot will be created in the
        analysis/validation/ folder

        :param validationDir: Folder where the plot will be saved
        :param format: File format (accepted by ROOT), i.e. pdf, png, jpg...
        """


        if not hasattr(self,'plot') or not self.plot:
            logger.warning("No plot found. Nothing will be saved")
            return False

        if not validationDir:
            vDir = os.path.join(self.expRes.path,'validation')
        else: vDir = validationDir

        if not os.path.isdir(vDir):
            logger.info("Creating validation folder "+vDir)
            os.mkdir(vDir)

        filename = self.plot.GetTitle()+'.'+format
        filename = filename.replace(self.expRes.getValuesFor('id')[0]+"_","")
        filename = os.path.join(vDir,filename)
        filename = filename.replace("*","").replace(",","").replace("(","").replace(")","")
        self.plot.Print(filename)
        return True

    def saveData(self,validationDir=None,datafile=None):
        """
        Saves the data and plot in a text file in the validationDir folder.
        If the folder does not exist, it will be created.
        If the folder is not defined the plot will be created in the
        analysis/validation/ folder
        If datafile is not define, uses the default naming (Txname_axes.py)

        :param validationDir: Folder where the root file will be saved
        :param datafile: Name of the data file
        """

        if not hasattr(self,'plot') or not self.plot:
            logger.warning("No plot found. Nothing will be saved")
            return False
        if not hasattr(self,'data') or not self.data:
            logger.warning("No data found. Nothing will be saved")
            return False

        if not validationDir:
            validationDir = os.path.join(self.expRes.path,'validation')

        if not os.path.isdir(validationDir):
            logger.info("Creating validation folder "+validationDir)
            os.mkdir(validationDir)

        if not datafile:
            datafile = self.plot.GetTitle()+'.py'
            datafile = datafile.replace(self.expRes.getValuesFor('id')[0]+"_","")
            datafile = os.path.join(validationDir,datafile)
            datafile = datafile.replace("*","").replace(",","").replace("(","").replace(")","")


        #Save data to file
        f = open(datafile,'w')
        dataStr = str(self.data)
        dataStr = dataStr.replace('[fb]','*fb').replace('[pb]','*pb')
        dataStr = dataStr.replace('[GeV]','*GeV').replace('[TeV]','*TeV')
        f.write("validationData = "+dataStr)
        f.close()

        return True






