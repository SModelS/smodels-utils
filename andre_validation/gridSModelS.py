#!/usr/bin/env python

"""
.. module:: gridSModelS
   :synopsis: Defines the functionalities required to run SModelS on
   a grid of SLHA files for producing a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import os,sys,logging,shutil
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

sys.path.append('../')
from smodels_utils import SModelSUtils
import tempfile,tarfile
from smodels.theory import slhaDecomposer
from smodels.tools.physicsUnits import fb, GeV
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot

logger.setLevel(level=logging.DEBUG)

def getSlhaFiles(slhadir):
    """
    Returns a list of valid SLHA files in slhadir
    :param slhadir: path to the SLHA folder or the tar ball containing the files (string)
    :return: list of SLHA files (list of strings)
    """            
    
    slhaFiles = []    
    if os.path.isdir(slhadir):
        slhaD = slhadir
    elif os.path.isfile(slhadir):
        try:
            tar = tarfile.open(slhadir)
            tempdir = tempfile.mkdtemp(dir=os.getcwd())
            tar.extractall(path=tempdir)
            slhaD = tempdir
        except:
            logger.error("Could not extract SLHA files from %s" %slhadir)
            sys.exit()
    else:
        logger.error("%s is not a file nor a folder" %slhadir)
        sys.exit()
    
    for root, dirs, files in os.walk(slhaD):
        for slhafile in files:
            slhafile = os.path.join(root,slhafile)
            f = open(slhafile,'r')
            fdata = f.read()
            f.close()
            #Skip non-SLHA files
            if not 'BLOCK MASS' in fdata: continue
            if not 'XSECTION' in fdata: continue
            slhaFiles.append(slhafile)

    return slhaFiles,slhaD
        
def runSModelSFor(validationPlot):
    """
    Uses the information in the ValidationPlot object
    to produce a parameter file to be used with runSModelS.
    Selects the analysis and topology corresponding to the validationPlot
    
    :param validationPlot: a ValidationPlot object
    :return: path to the temporary parameter file
    """  
    
    #Define original plot
    origPlot = OrigPlot.fromString(validationPlot.axes)
    
    #Get list of SLHA files:
    if not validationPlot.slhaDir:
        logger.warning("SLHA folder not defined")
        return False
    slhaFiles,slhaD = getSlhaFiles(validationPlot.slhaDir)
    
    expRes = validationPlot.expRes
    #Define basic parameters
    sigmacut = 0.001 * fb
    mingap = 2. * GeV
    #Loop over SLHA files and compute results:
    data = []
    for slhafile in slhaFiles:
        smstoplist = slhaDecomposer.decompose(slhafile, sigmacut,\
                        doCompress=True,doInvisible=True, minmassgap=mingap)
        predictions = theoryPredictionsFor(expRes, smstoplist)
        if not predictions: continue
        dataset = predictions.dataset
        datasetID = dataset.getValuesFor('dataid')
        for theoryPrediction in predictions:
            txname = theoryPrediction.txname
            if txname and txname.txname  != validationPlot.txname: continue                      
            mass = theoryPrediction.mass
            if not mass and len(smstoplist.getElements()) == 1:
                mass = smstoplist.getElements()[0].getMasses()
            elif not mass:
                logger.error("Could not define mass for prediction.")
                sys.exit()            
            value = theoryPrediction.value
            cond = theoryPrediction.conditions
            if expRes.getValuesFor('datatype') == 'upper-limit':
                upperLimit = expRes.getUpperLimitFor(txname=txname,mass=mass)
            elif expRes.getValuesFor('datatype') == 'efficiency-map':
                upperLimit = expRes.getUpperLimitFor(dataID=datasetID)

            if len(value) != 1:
                logger.warning("More than one cross-section found. Using first one")
            value = value[0].value
            mass_unitless = [[(m/GeV).asNumber() for m in mm] for mm in mass]            
            x,y = origPlot.getXYValues(mass_unitless)
            data.append({'slhafile' : slhafile, 'axes': [x,y], \
                         'signal' : value, 'UL' : upperLimit, 'condition': cond,
                         'dataset': predictions.dataset.getValuesFor("dataid")})

    #Remove temporary folder
    if slhaD != validationPlot.slhaDir: shutil.rmtree(slhaD)

    return data
