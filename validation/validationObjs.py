#!/usr/bin/env python

"""
.. module:: validationObjs
   :synopsis: Main classes and methods for generating a single validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,time

logger = logging.getLogger(__name__)
from smodels.tools.physicsUnits import GeV
from smodels.tools import modelTester
from plottingFuncs import createPlot, getExclusionCurvesFor, createPrettyPlot
import tempfile,tarfile,shutil,copy
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from sympy import var
import pyslha
import string

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
    :ivar limitPoints: limits tested model points to n randomly chosen ones. 
                   If None or negative, take all points.
    :ivar extraInfo: add additional info to plot: agreement factor, time spent,
                      time stamp, hostname
    """

    def __init__(self, ExptRes, TxNameStr, Axes, slhadir=None, databasePath=None,
                 kfactor = 1., limitPoints=None, extraInfo=False, combine=False ):

        self.expRes = copy.deepcopy(ExptRes)
        self.txName = TxNameStr
        self.axes = Axes
        self.niceAxes = self.getNiceAxes(Axes)
        self.slhaDir = None
        self.data = None
        self.officialCurves = self.getOfficialCurve( get_all = True )
        self.kfactor = kfactor
        self.limitPoints = limitPoints
        self.extraInfo = extraInfo
        self.combine = combine

        #Select the desired txname and corresponding datasets in the experimental result:
        for dataset in self.expRes.datasets:
            dataset.txnameList = [tx for tx in dataset.txnameList[:] if tx.txName == self.txName]
        self.expRes.datasets = [dataset for dataset in self.expRes.datasets[:] if len(dataset.txnameList) > 0]

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

        import plottingFuncs ## propagate logging level!
        plottingFuncs.logger.setLevel ( logger.level )

    def __str__(self):

        vstr = "Validation plot for\n"
        vstr += 'id: '+self.expRes.getValuesFor('id')+'\n'
        vstr += 'TxName: '+self.txName+'\n'
        vstr += 'Axes: '+self.niceAxes
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
        curve = self.getOfficialCurve( get_all = False )        
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
        closeWithXAxis=True ## close with x-axis (y=0) or y-axis (x=0)
        if self.txName in [ "T2bbffff" ]: ## T2bbffff tends to close with y-axis
            closeWithXAxis = False

        if closeWithXAxis:
            curve.SetPoint ( curve.GetN(), x, 0. )  ## extend to y=0
            curve.SetPoint ( curve.GetN(), x0, 0. )  ## extend to first point
        else:
            curve.SetPoint ( curve.GetN(), 0., y )  ## extend to x=0
            curve.SetPoint ( curve.GetN(), 0., y0 )  ## extend to first point

        pts= { "total": 0, "excluded_inside": 0, "excluded_outside": 0, "not_excluded_inside": 0,
               "not_excluded_outside": 0, "wrong" : 0 }
        for point in self.data:
            try: ## we seem to have two different ways of writing the x,y values
                x,y=point["axes"]['x'],point["axes"]['y']
            except Exception as e:
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
        Defines the folder or .tar.gz file containing all the slha files to be
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
        If slhadir is a .tar.gz file, returns a temporary folder where the files
        have been extracted to.

        :param slhadir: path to the SLHA folder or the tar ball containing the files (string)
        :return: path to the folder containing the SLHA files
        """

        if os.path.isdir(self.slhaDir):
            return self.slhaDir
        elif os.path.isfile(self.slhaDir):
            try:
                tar = tarfile.open(self.slhaDir,'r:gz')
                tempdir = tempfile.mkdtemp(dir=os.getcwd())
                members=tar.getmembers()
                if self.limitPoints != None and self.limitPoints > 0:
                    import random
                    random.shuffle ( members )
                    members=members[:self.limitPoints]
                tar.extractall(path=tempdir,members=members)
                tar.close()
                logger.debug("SLHA files extracted to %s" %tempdir)
                return tempdir
            except Exception as e:
                logger.error("Could not extract SLHA files from %s: %s" %\
                              ( self.slhaDir, e ) )
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
        tgraphDict = getExclusionCurvesFor(self.expRes,txname=self.txName,
                                           axes=self.axes, get_all = get_all )
        if not tgraphDict: return None
        tgraph = tgraphDict[self.txName]
        if get_all:
            return tgraph
        else:
            return tgraph[0]

    def getParameterFile(self,tempdir=None):
        """
        Creates a temporary parameter file to be passed to runSModelS

        :param tempdir: Temporary folder where the parameter file will be created. Default = current folder.
        """

        #Get the analysis ID, txname and dataset ID:
        expId = self.expRes.globalInfo.id
        txname = self.expRes.getTxNames()[0].txName

        #Get number of cpus:
        if not hasattr(self, 'ncpus') or not self.ncpus:
            self.ncpus  = -1

        if tempdir is None: tempdir = os.getcwd()
        pf, parFile = tempfile.mkstemp(dir=tempdir,prefix='parameter_',suffix='.ini', text=True )
        combine = "False"  
        if self.combine:
            combine = "True"
        with open ( parFile, "w" ) as f:
            f.write("[path]\ndatabasePath = %s\n" %self.databasePath)
            f.write("[options]\ninputType = SLHA\ncheckInput = True\ndoInvisible = True\ndoCompress = True\ncomputeStatistics = True\ntestCoverage = False\ncombineSRs = %s\n" % combine )
            f.write("[parameters]\nsigmacut = 0.000000001\nminmassgap = 2.0\nmaxcond = 1.\nncpus = %i\n" %self.ncpus)
            f.write("[database]\nanalyses = %s\ntxnames = %s\ndataselector = all\n" % (expId,txname))
            f.write("[printer]\noutputType = python\n")
            f.write("[python-printer]\naddElementList = False\n")
            f.close()
        os.close(pf)
        return parFile

    def loadData(self):
        """
        Tries to load an already existing python output.
        """

        validationDir = os.path.join(self.expRes.path,'validation')
        datafile = self.getDataFile(validationDir)
        if not os.path.isfile(datafile):
            logger.error("Validation datafile %s not found" %datafile)
            self.data = None
            return

        #Save data to file
        f = open(datafile,'r')
        self.data = eval(f.read().replace("validationData = ",""))
        f.close()

    def getDataFromPlanes(self):
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
        logger.debug("SLHA files for validation at %s" %slhaDir)

        #Get list of input files to be tested
        try:
            fileList, inDir = modelTester.getAllInputFiles(slhaDir)
        except Exception: ## old version?
            fileList = modelTester.getAllInputFiles(slhaDir)
            inDir = slhaDir
            

        #Set temporary outputdir:
        outputDir = tempfile.mkdtemp(dir=slhaDir,prefix='results_')

        #Get parameter file:
        parameterFile = self.getParameterFile(tempdir=outputDir)
        logger.debug("Parameter file: %s" %parameterFile)

        #Read and check parameter file, exit parameterFile does not exist
        parser = modelTester.getParameters(parameterFile)

        #Select the desired experimental result
        listOfExpRes = [self.expRes]

        t0=time.time()
        """ Test all input points """
        modelTester.testPoints(fileList, inDir, outputDir, parser, 'validation',
                 listOfExpRes, 1000, False, parameterFile)
        dt=(time.time()-t0) / len(fileList) ## for now we just write out avg time

        #Define original plot
        massPlane = MassPlane.fromString(self.txName,self.axes)
        #Now read the output and collect the necessary data
        self.data = []
        slhafiles= os.listdir(slhaDir)
        ct_nooutput=0
        for slhafile in slhafiles:
            if not os.path.isfile(os.path.join(slhaDir,slhafile)):  #Exclude the results folder
                continue
            # print ( "slhafile", slhafile )
            fout = os.path.join(outputDir,slhafile + '.py')
            if not os.path.isfile(fout):
                if ct_nooutput>4:
                    ## suppress subsequently same error messages
                    continue
                logger.error("No SModelS output found for %s (should be %s)" % \
                              ( slhafile, fout ) )
                ct_nooutput+=1
                if ct_nooutput==5:
                    logger.error("did not find SModelS output 5 times subsequently. Will quench error msgs from now on.")
                continue
            ct_nooutput=0
            # print ( "reading %s" % fout )
            ff = open(fout,'r')
            cmd = ff.read().replace('\n','')
            exec( cmd, globals() )
            ff.close()
            if not 'ExptRes' in smodelsOutput:
                logger.debug("No results for %s " %slhafile)
                continue
            res = smodelsOutput['ExptRes']
            expRes = res[0]
            #Double checks (to make sure SModelS ran as expected):
            if len(res) != 1:
                logger.debug("Wait. We have multiple dataset Ids. Lets see if there is a combined result." )
                found_combined=False
                for eR in res:
                    if "combined" in eR["DataSetID"]:
                        logger.debug ( "found a combined result. will use it." )
                        found_combined=True
                        expRes = eR
                if not found_combined:
                    logger.warning("We have multiple dataset ids, but none is a combined one. Dont know what to do." )
                    return False
            if expRes['AnalysisID'] != self.expRes.globalInfo.id:
                logger.error("Something went wrong. Obtained results for the wrong analyses")
                return False
            if self.txName != expRes['TxNames'][0] or len(expRes['TxNames']) != 1:
                logger.error("Something went wrong. Obtained results for the wrong txname")
                return False

            #Replaced rounded masses by original masses
            #(skip rounding to check if mass is in the plane)
            roundmass = expRes['Mass (GeV)']
            mass = [br[:] for br in roundmass]
            slhadata = pyslha.readSLHAFile(os.path.join(slhaDir,slhafile))
            origmasses = list(set(slhadata.blocks['MASS'].values()))
            for i,br in enumerate(mass):
                for im,m in enumerate(br):
                    for omass in origmasses:
                        if round(omass,1) == m:
                            mass[i][im] = omass
                            break
                                  
            varsDict = massPlane.getXYValues(mass)
            if varsDict is None:                
                logger.debug( "dropping %s, doesnt fall into the plane of %s." % \
                               (slhafile, massPlane ) )
                continue            
            Dict = {'slhafile' : slhafile, 'axes' : varsDict, 't': dt,
                    'signal': expRes['theory prediction (fb)'],
                    'UL': expRes['upper limit (fb)'], 'condition': expRes['maxcond'],
                    'dataset': expRes['DataSetID'] }
            if "efficiency" in expRes.keys():
                Dict["efficiency"] = expRes['efficiency']
            if expRes['dataType'] == 'efficiencyMap':
                #Select the correct dataset (best SR):
                dataset = [dset for dset in self.expRes.datasets if dset.dataInfo.dataId == expRes['DataSetID']]
                if len(dataset)==1:
                    dataset = dataset[0]
                else: ## probably the combined case. we take any dataset.
                    dataset = self.expRes.datasets[0]

                txname = [tx for tx in dataset.txnameList if tx.txName == expRes['TxNames'][0]][0]
                massGeV = [[m*GeV for m in mbr] for mbr in mass]
                if not "efficiency" in Dict.keys():
                    Dict['efficiency'] = txname.txnameData.getValueFor(massGeV)

            self.data.append(Dict)

        #Remove temporary folder
        if slhaDir != self.slhaDir: shutil.rmtree(slhaDir)

        if self.data == []:
            logger.error("There is no data for %s/%s/%s.\n Are the SLHA files correct? Are the constraints correct?"
                          %(self.expRes.globalInfo.id,self.txName,self.axes))

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

        self.plot,self.base = createPlot(self,silentMode=silentMode,extraInfo=self.extraInfo)

    def getPrettyPlot(self,silentMode=True):
        """
        Uses the data in self.data and the official exclusion curve
        in self.officialCurves to generate a pretty exclusion plot
        :param silentMode: If True the plot will not be shown on the screen
        """

        self.plot,self.base = createPrettyPlot(self,silentMode=silentMode)

    def savePlot(self,validationDir=None,fformat='pdf'):
        """
        Saves the plot in .pdf format in the validationDir folder.
        If the folder does not exist, it will be created.
        If the folder is not defined the plot will be created in the
        analysis/validation/ folder

        :param validationDir: Folder where the plot will be saved
        :param fformat: File fformat (accepted by ROOT), i.e. pdf, png, jpg...
        """


        if not hasattr(self,'plot') or not self.plot:
            logger.warning("No plot found. Nothing will be saved")
            return False

        if not validationDir:
            vDir = os.path.join(self.expRes.path,'validation')
        else: vDir = validationDir

        if not os.path.isdir(vDir):
            logger.debug("Creating validation folder "+vDir)
            os.mkdir(vDir)

        filename = self.getPlotFile(vDir,fformat)

        if not self.pretty:
            logger.info ( "saving plot in %s" % filename )
            self.plot.Print(filename)
            filename = filename.replace('.'+fformat,'.png')
            try:
                self.plot.Print(filename)
            except Exception as e:
                # if fails because of missing dep, then just proceed
                pass
        else:
            #Print pdf, png and root formats
            filename = filename.replace('.'+fformat,'_pretty.'+fformat)
            logger.info ( "saving plot in %s" % filename )
            self.plot.Print(filename)
            filename = filename.replace('.'+fformat,'.png')
            self.plot.Print(filename)
            filename = filename.replace('.png','.root')
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
            datafile = self.getDataFile(validationDir)
        #Save data to file
        f = open(datafile,'w')
        dataStr = str(self.data)
        dataStr = dataStr.replace('[fb]','*fb').replace('[pb]','*pb')
        dataStr = dataStr.replace('[GeV]','*GeV').replace('[TeV]','*TeV')
        f.write("validationData = "+dataStr)
        f.close()

        return True

    def getDataFile(self,validationDir,fformat='.pdf'):
        """
        Defines the name of the .py file and returns it

        :param validationDir: Folder where the root file will be saved

        :return: name of the .py file
        """

        datafile = self.getPlotFile(validationDir,fformat)
        datafile = datafile.rstrip(fformat)
        return datafile+'.py'

    def getPlotFile(self,validationDir,fformat='.pdf'):
        """
        Defines the name of the plot file and returns it

        :param validationDir: Folder where the root file will be saved

        :return: name of the plot file
        """

        filename = self.expRes.getValuesFor('id')[0] + "_" + self.txName + "_"
        filename += self.niceAxes.replace(",","").replace("(","").replace(")","")
        filename += '.'+fformat

        filename = filename.replace(self.expRes.getValuesFor('id')[0]+"_","")
        filename = os.path.join(validationDir,filename)
        filename = filename.replace("*","").replace(",","").replace("(","").replace(")","")

        return filename

    def getNiceAxes(self,axesStr):
        """
        Convert the axes definition format ('[[x,y],[x,y]]')
        to a nicer format ('Eq(MassA,x)_Eq(MassB,y)_Eq(MassA,x)_Eq(MassB,y)')

        :param axesStr: string defining axes in the old format

        :return: string with a nicer representation of the axes (more suitable for printing)
        """

        x,y,z = var('x y z')
        axes = eval(axesStr,{'x' : x, 'y' : y, 'z': z})

        eqList = []
        for ib,br in enumerate(axes):
            if ib == 0:
                mStr = 'Mass'
            else:
                mStr = 'mass'
            mList = []
            for im,eq in enumerate(br):
                mList.append('Eq(%s,%s)'
                               %(var(mStr+string.ascii_uppercase[im]),eq))
            mStr = "_".join(mList)
            eqList.append(mStr)

        #Simplify symmetric branches:
        if eqList[0].lower() == eqList[1].lower() and len(eqList) == 2:
            eqStr = "2*%s"%eqList[0]
        else:
            eqStr = "__".join(eqList)

        eqStr = eqStr.replace(" ","")

        return eqStr




