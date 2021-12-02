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

def getTheoryPredsCombiner_ ( slhafile, expRes ):
    model = Model(BSMparticles=BSMList, SMparticles=SMList )
    model.updateParticles(inputFile=slhafile )
    smstopos = decompose ( model )
    tpreds = theoryPredictionsFor ( expRes, smstopos,
           combinedResults=False, useBestDataset=False, marginalize=False )
    combiner = TheoryPredictionsCombiner ( tpreds )
    return combiner

class ValidationPlot( validationObjs.ValidationPlot ):

            
    def addError ( self, slhafile, axes, msg ):
        """ add an error entry """
        Dict = {'slhafile' : slhafile, 'error': msg, 'axes' : axes }
        self.data.append ( Dict )

    def hello ( self ):
        blue, reset = "", ""
        try:
            import colorama
            blue = colorama.Fore.BLUE
            reset = colorama.Fore.RESET
        except Exception as e:
            pass
        logger.info ( f"--- {blue}using theoryPredictionsCombiner{reset}" )
        
    def getDataFromPlanes(self):
        """
        Runs SModelS on the SLHA files from self.slhaDir and store
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


        #Set temporary outputdir:
        outputDir = tempfile.mkdtemp(dir=slhaDir,prefix='results_')
        for f in fileList:
            axes = self.getXYFromSLHAFileName ( f, asDict=True )
            fullpath = os.path.join ( inDir, f )
            t0 = time.time()
            combiner = getTheoryPredsCombiner_ ( fullpath, self.expRes )
            if combiner.theoryPredictions == None:
                self.addError ( f, axes, "no theorypreds" )
                continue
            dt = time.time() - t0
            xsec =float(combiner.totalXsection().asNumber(fb))
            ul, eul = 1e15, 1e15
            r = combiner.getRValue ( expected=False )
            rexp = combiner.getRValue ( expected=True )
            if r > 0.:
                ul = xsec / r
            if rexp > 0.:
                eul = xsec / rexp
            cond = combiner.getmaxCondition()
            Dict = {'slhafile' : f, 'UL': ul, 'axes' : axes, 't': dt,
                    'kfactor': self.kfactor, 'condition': cond, 'eUL': eul }
            Dict["signal"]=xsec
#            'signal': expRes['theory prediction (fb)'],
#            'UL': expRes['upper limit (fb)'], 'condition': expRes['maxcond'],
#            'dataset': expRes['DataSetID'] }
            self.data.append ( Dict )
