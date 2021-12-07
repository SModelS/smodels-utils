#!/usr/bin/env python3

"""
.. module:: useTheoPredCombiner
   :synopsis: contains the code that replaces validationObjs:getDataFromPlanes,
              runs theoryPredictionsCombiner over it. To use it, overwrite
              ValidationPlot.getDataFromPlanes with the method below.

"""

import logging, tempfile, time, os
logger = logging.getLogger(__name__)
import validationObjs
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory.decomposer import decompose
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
from smodels.theory import model 
model.logger.setLevel ( logging.WARNING )
from smodels.tools.physicsUnits import GeV, fb
from smodels.theory import decomposer
from smodels.tools.theoryPredictionsCombiner import TheoryPredictionsCombiner
import multiprocessing

def getCombinedTheoryPreds_ ( slhafile : str, inDir : str, expRes : list, rdicts ):
    """ the theory combiner, written for parallelization.
    :param slhafile: slha file name, basename only
    :param inDir: directory where slha file resides
    :param expRes: list of experiment results
    :param rdicts: a dictionary for the return values
    """
    with open ( "useTheoPredCombiner.stats", "at" ) as f:
        f.write ( f"{time.asctime()}: started {slhafile}.\n" )
        f.close()
    t0 = time.time()
    fullpath = os.path.join ( inDir, slhafile )
    model = Model(BSMparticles=BSMList, SMparticles=SMList )
    model.updateParticles(inputFile=fullpath )
    smstopos = decompose ( model )
    tpreds = theoryPredictionsFor ( expRes, smstopos,
           combinedResults=False, useBestDataset=False, marginalize=False )
    rdicts[slhafile]["success"] = False
    rdicts[slhafile]["reason"] = "unknown"
    if tpreds == None:
        rdicts[slhafile]["reason"]="no tpreds"
        return
    combiner = TheoryPredictionsCombiner ( tpreds, slhafile )
    combiner.computeStatistics()
    r = combiner.getRValue ( expected=False )
    rexp = combiner.getRValue ( expected=True )
    maxcond = combiner.getmaxCondition()
    xsec =float(combiner.totalXsection().asNumber(fb))
    chi2 = combiner.chi2()
    ul, eul = 1e15, 1e15
    if r > 0.:
        ul = xsec / r
    if rexp > 0.:
        eul = xsec / rexp
    rdicts[slhafile]["r"]=r
    rdicts[slhafile]["UL"]=ul
    rdicts[slhafile]["eUL"]=eul
    rdicts[slhafile]["rexp"]=rexp
    rdicts[slhafile]["signal"]=xsec
    rdicts[slhafile]["condition"]=maxcond
    rdicts[slhafile]["chi2"]=chi2
    dt = time.time() - t0
    rdicts[slhafile]["t"]=dt
    # lastly, we toggle the success flag
    rdicts[slhafile]["success"]=True
    with open ( "useTheoPredCombiner.stats", "at" ) as f:
        f.write ( f"{time.asctime()}: finished {slhafile} in {dt:.1f}s: UL={ul:.2f}.\n" )
        f.close()
    return rdicts

def getCombinedTheoryPredsForBatch_ ( slhafiles : str, inDir : str, 
                                      expRes : list, rdicts ):
    """ the theory combiner, written for parallelization, for a batch of
        slhafiles
    :param slhafiles: slha file names, basenames only
    :param inDir: directory where slha file resides
    :param expRes: list of experiment results
    :param rdicts: a dictionary for the return values
    """
    for slhafile in slhafiles:
        getCombinedTheoryPreds_ ( slhafile, inDir, expRes, rdicts )

class ValidationPlot( validationObjs.ValidationPlot ):

    def addError ( self, slhafile, axes, msg ):
        """ add an error entry """
        Dict = {'slhafile' : slhafile, 'error': msg, 'axes' : axes }
        self.data.append ( Dict )

    def resetStatusFile ( self ):
        with open ( "useTheoPredCombiner.stats", "wt" ) as f:
            f.write ( f"Started new run at {time.asctime()}.\n" )
            f.close()

    def specialInits ( self ):
        """ inits for the subclass """
        self.validationType = "tpredcomb"

    def hello ( self ):
        blue, reset = "", ""
        try:
            import colorama
            blue = colorama.Fore.BLUE
            reset = colorama.Fore.RESET
        except Exception as e:
            pass
        logger.info ( f"--- {blue}using theoPredsCombiner on {self.options['ncpus']} CPUs {reset}" )
        self.resetStatusFile()

    def getDataFromPlanes(self):
        """
        Runs SModelS on the SLHA files fr m self.slhaDir and store
        the relevant data in self.data.
        Uses runSModelS.main.
        """
        self.hello()
        self.data = []

        #Get list of SLHA files:
        if not self.slhaDir:
            logger.warning("SLHA folder not defined")
            return False
        slhaDir = self.getSLHAdir()  #Path to the folder containing the SLHA files
        logger.debug("SLHA files for validation at %s" %slhaDir)

        from smodels.tools import modelTester
        #Get list of input files to be tested
        try:
            fileList, inDir = modelTester.getAllInputFiles(slhaDir)
        except Exception: ## old version?
            fileList = modelTester.getAllInputFiles(slhaDir)
            inDir = slhaDir

        ncpus = self.options["ncpus"]
        manager = multiprocessing.Manager()
        rdicts = manager.dict()
        for f in fileList:
            if "recipe" in f:
                continue
            rdicts[f] = manager.dict()
        if ncpus == 1:
            getCombinedTheoryPredsForBatch_ ( fileList, inDir, self.expRes, rdicts )
        else:
            logger.debug ( f"starting computations on {ncpus} CPUs" )
            chunks = [ fileList[i::ncpus] for i in range(ncpus) ]
            jobs = []
            for c in chunks:
                p = multiprocessing.Process(target=getCombinedTheoryPredsForBatch_, 
                        args=(c, inDir, self.expRes, rdicts ))
                jobs.append ( p )
                p.start()
            for j in jobs:
                j.join()

        for f in fileList:
            if "recipe" in f:
                continue
            thisd = rdicts[f]
            axes = self.getXYFromSLHAFileName ( f, asDict=True )
            if thisd["success"]==False:
                self.addError ( f, axes, thisd["reason"] )
                continue
            Dict = {'slhafile' : f, 'axes' : axes, 'kfactor': self.kfactor }
            if not "UL" in thisd:
                print ( f"what is wrong with thisd: {thisd}" )
            Dict["UL"]=thisd["UL"]
            Dict["eUL"]=thisd["eUL"]
            Dict["condition"]=thisd["condition"]
            Dict["signal"]=thisd["signal"]
            Dict["chi2"]=thisd["chi2"]
            Dict["t"]=thisd["t"]
            self.data.append ( Dict )

    def getPlotFile(self,validationDir,fformat='pdf'):
        """
        Defines the name of the plot file and returns it. Override 
        for "_tpredcomb" postfix to name

        :param validationDir: Folder where the root file will be saved

        :return: name of the plot file
        """

        if fformat.startswith("."):
            fformat = fformat[1:]

        filename = self.expRes.globalInfo.id + "_" + self.txName + "_"
        filename += self.niceAxes.replace(",","").replace("(","").replace(")","").\
                    replace("/","d")
        filename += '_tpredcomb.'+fformat

        filename = filename.replace(self.expRes.globalInfo.id+"_","")
        filename = os.path.join(validationDir,filename)
        filename = filename.replace("*","").replace(",","").replace("(","").replace(")","")

        return filename
