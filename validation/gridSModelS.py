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

logger.setLevel(level=logging.INFO )

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

    import copy
    expRes = copy.deepcopy ( validationPlot.expRes )
    #Limit the experimental result to the respective Txname (relevant for EM results)
    for dataset in expRes.datasets:
        dataset.txnameList = [tx for tx in dataset.txnameList[:] if tx.txName == validationPlot.txName]
    #Define basic parameters
    sigmacut = 0.0 * fb
    mingap = 2. * GeV
    #Loop over SLHA files and compute results:
    data = []
    for slhafile in slhaFiles:
        #print "[gridSModelS] now run on",slhafile
        smstoplist = slhaDecomposer.decompose(slhafile, sigmacut,\
                        doCompress=True,doInvisible=True, minmassgap=mingap)

        predictions = theoryPredictionsFor(expRes, smstoplist)
        s_eR = str ( expRes )
        if len(s_eR) > 44:
            s_eR = s_eR[:20]+"..."+s_eR[-20:]
        if not predictions:
            logger.info ( "no theory predictions for %s in %s" % ( s_eR, slhafile) )
            continue
        logger.info("I have theory predictions for %s in %s" % ( s_eR, slhafile) )

        for theoryPrediction in predictions:
            dataset = theoryPrediction.dataset
            datasetID = dataset.dataInfo.dataId
            txnames = theoryPrediction.txnames
            if len(txnames) != 1:
                logger.warning( "Multiple Txnames entering the theory prediction. "
                                "Something may be wrong.")
            is_in=False
            for txname in txnames:
                if txname.txName == validationPlot.txName:
                    is_in=True
            if not is_in:
                logger.error ( "cannot find %s" % validationPlot.txName )
                continue
            mass = theoryPrediction.mass
            if not mass:
                logger.error("Could not define mass ``%s'' for prediction." % mass )
            value = theoryPrediction.value
            cond = theoryPrediction.conditions
            upperLimit=None
            efficiency=None
            CLs=None
            if expRes.datasets[0].dataInfo.dataType == 'upperLimit':
                upperLimit = expRes.getUpperLimitFor(txname=txname,mass=mass)
            elif expRes.datasets[0].dataInfo.dataType == 'efficiencyMap':
                upperLimit = expRes.getUpperLimitFor(dataID=datasetID)                
                eff=dataset.txnameList[0].txnameData.getValueFor(mass)
                expectedBG=dataset.dataInfo.expectedBG
                observedN=dataset.dataInfo.observedN
                bgError=dataset.dataInfo.bgError
                lumi=expRes.globalInfo.lumi
                from smodels.tools import statistics
                CLs=statistics.CLs ( observedN, expectedBG, bgError, 
                                     value[0].value * lumi, 10000 )
                efficiency=eff
            else:
                logger.error ( "dont know dataType of %s" % 
                               expRes.getValuesFor('dataType')[0] )

            if len(value) != 1:
                logger.warning("More than one cross-section found. Using first one")
            value = value[0].value
            mass_unitless = [[(m/GeV).asNumber() for m in mm] for mm in mass]
            v=origPlot.getXYValues(mass_unitless)
            if v == None:
                logger.info ( "dropping %s, doesnt fall into the plane of %s." % 
                              ( slhafile, origPlot.string ) )
                continue
            x,y = v
            Dict= {'slhafile' : slhafile, 'axes': [x,y], 'signal' : value, 
                   'UL' : upperLimit, 'condition': cond, 'dataset': datasetID } 
            ## , 'efficiency' : eff}
            # print "[gridSModelS] run on ",Dict
            if efficiency:
                Dict['efficiency']=efficiency
                Dict['CLs']=CLs
            data.append( Dict )

    #Remove temporary folder
    if slhaD != validationPlot.slhaDir: shutil.rmtree(slhaD)

    if data == []:
        logger.error ( "There are no data for a validation plot."
                       " Are the SLHA files correct? Are the constraints correct?" )

    return data
