#!/usr/bin/env python

"""
.. module:: gridSModelS
   :synopsis: Defines the functionalities required to run SModelS on
   a grid of SLHA files for producing a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import os,sys,logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

sys.path.append('/home/lessa/smodels/')
sys.path.append('/home/lessa/smodels-utils/')
from smodels.theory import slhaDecomposer
from smodels.tools.physicsUnits import fb, GeV
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels_utils.dataPreparation.origPlotObjects import OrigPlot

logger.setLevel(level=logging.DEBUG)

def getSlhaFiles(slhadir):
    """
    Returns a list of valid SLHA files in slhadir
    :param slhadir: path to the SLHA folder (string)
    :return: list of SLHA files (list of strings)
    """            
    
    slhaFiles = []    
    for f in os.listdir(slhadir):
        slhafile = os.path.join(slhadir,f)      
        if not os.path.isfile(slhafile): continue
        f = open(slhafile,'r')
        fdata = f.read()
        f.close()
        #Skip non-SLHA files
        if not 'BLOCK MASS' in fdata: continue
        if not 'XSECTION' in fdata: continue
        slhaFiles.append(slhafile)
    
    return slhaFiles
        
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
    slhaFiles = getSlhaFiles(validationPlot.slhaDir)
    
    #Define basic parameters
    sigmacut = 0.001 * fb
    mingap = 2. * GeV
    #Loop over SLHA files and compute results:
    data = []
    for slhafile in slhaFiles[:10]:
        smstoplist = slhaDecomposer.decompose(slhafile, sigmacut,\
                        doCompress=True,doInvisible=True, minmassgap=mingap)
        predictions = theoryPredictionsFor(validationPlot.expRes, smstoplist)
        if not predictions: continue
        for theoryPrediction in predictions:
            txname = theoryPrediction.txname
            if txname  != validationPlot.txname: continue
            mass = theoryPrediction.mass
            value = theoryPrediction.value
            cond = theoryPrediction.conditions
            upperLimit = theoryPrediction.expResult.getUpperLimitFor(txname,mass)
            if len(value) != 1:
                logger.warning("More than one cross-section found. Using first one")
            value = value[0].value
            x,y = origPlot.getXYValues(mass) 
            print x,y,mass[0]            
            data.append({'slhafile' : slhafile, 'axes': [x,y], \
                         'signal' : value, 'UL' : upperLimit, 'condition': cond})
            
    return data

def getAxes(mass,axes):
    """
    Reads the mass array and the definition of the validation plot axes
    and returns the values of the axes (x and y)
    :param mass: mass array (array of Unum objects)
    :param axes: string describing the mass->axes mapping (e.g. 2*Eq(mother,x)_Eq(lsp,y))
    
    :return: values for x and y
    """
    
    return mass[0]