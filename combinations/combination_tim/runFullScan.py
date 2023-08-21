#!/usr/bin/env python3

"""
.. module:: Example
   :synopsis: Basic main file example for using SModelS.
   This file must be run under the installation folder.
"""
""" Import basic functions (this file must be executed in the installation folder) """

import sys, os, time, glob, multiprocessing, gc

# smodelsPath = '/home/pascal/SModelS/smodels-2.3.1/'
smodelsPath = '/theo/pascal/SModelS/smodels-2.3.1/'
sys.path.append(smodelsPath)

# protomodelsPath = '/home/pascal/SModelS/protomodels'
protomodelsPath = '/theo/pascal/SModelS/protomodels'
sys.path.append(protomodelsPath)
from tester.combiner import Combiner

# slhaFolder = '/home/pascal/SModelS/EWinoData/2ndFilter_slha_nlo/'
# slhaFolder = '/theo/pascal/2ndFilter_slha_nlo/'
# outputDir = './outputFullScan_nlo_2p3_mmg05'

from smodels.tools import runtime
from smodels.theory import decomposer
from smodels.tools.physicsUnits import fb, GeV
from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner, TheoryPredictionList
from smodels.experiment.databaseObj import Database, ExpResultList
from smodels.tools import coverage, ioObjects, timeOut #, crashReport
# from smodels.tools.smodelsLogging import setLogLevel
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.theory.model import Model
from smodels.theory.exceptions import SModelSTheoryError as SModelSError
from smodels.tools.printer import MPrinter, printScanSummary, PyPrinter, SummaryPrinter
from smodels.tools.smodelsLogging import logger
from imp import reload
from smodels import particlesLoader
try:
    from ConfigParser import NoSectionError, NoOptionError
except ImportError:
    from configparser import NoSectionError, NoOptionError
from collections import OrderedDict

# setLogLevel("info")

timeout = 0

checkInput = True
doInvisible = True
doCompress = True
computeStatistics = False # ??? Ne change rien ?
testCoverage = True
combineSRs = True
reportAllSRs = False # Must be False to combine SRs
experimentalFeatures = False

particles = 'share.models.mssm'
promptWidth = 1e-11*GeV
stableWidth = 1e-25*GeV

sigmacut = 0.001*fb
minmassgap = 5.*GeV
maxcond = 0.2
# ncpus = 45

path = 'official'
force_txt = False
analyses = 'all'
txnames = 'TChi*'
dataselector = 'efficiencyMap'

useSuperseded = False
useNonValidated = False

development = False

def findBestCombination(allPredictions):
    protoCombiner = Combiner()
    combinables = protoCombiner.findCombinations ( allPredictions, strategy='' )
    combinations = protoCombiner.sortOutSubsets ( combinables )

    if len(combinations) == 0:
        return []
    elif len(combinations) == 1:
        return combinables[0]
    else:
        bestCombo,ZCombo,llhdCombo,muhatCombo = protoCombiner.findHighestSignificance(allPredictions,strategy='',expected=True)
    return bestCombo

def loadDatabase(path, db):
    """
    Load database

    :parameter parser: ConfigParser with path to database
    :parameter db: binary database object. If None, then database is loaded,
                   according to databasePath. If True, then database is loaded,
                   and text mode is forced.
    :returns: database object, database version

    """
    try:
        database = db
        # logger.error("database=db: %s" % database)
        if database in [None, True]:
            databasePath = path
            discard_zeroes = True
            force_load = None
            if database is True:
                force_load = "txt"
            if os.path.isfile(databasePath):
                force_load = "pcl"
            database = Database(databasePath, force_load=force_load,
                                discard_zeroes=discard_zeroes)
        databaseVersion = database.databaseVersion
    except DatabaseNotFoundException:
        print("Database not found in ``%s''" %
                     os.path.realpath(databasePath))
        sys.exit()
    return database, databaseVersion

def loadDatabaseResults(analyses,txnames,dataselector,useSuperseded,useNonValidated,database):
    """
    Load database entries specified in parser

    :parameter parser: ConfigParser, containing analysis and txnames selection
    :parameter database: Database object
    :returns: List of experimental results

    """
    """ In case that a list of analyses or txnames are given, retrieve list """
    tmp = analyses.split(",")
    analyses = [x.strip() for x in tmp]
    tmp_tx = txnames.split(",")
    txnames = [x.strip() for x in tmp_tx]
    if dataselector == "efficiencyMap":
        dataTypes = ['efficiencyMap']
        datasetIDs = ['all']
    elif dataselector == "upperLimit":
        dataTypes = ['upperLimit']
        datasetIDs = ['all']
    else:
        dataTypes = ['all']
        tmp_dIDs = dataselector.split(",")
        datasetIDs = [x.strip() for x in tmp_dIDs]

    if useSuperseded:
        print('Including superseded results')
    if useNonValidated:
        print('Including non-validated results')

    """ Load analyses """

    ret = database.getExpResults(analysisIDs=analyses, txnames=txnames,
                                 datasetIDs=datasetIDs, dataTypes=dataTypes,
                                 useSuperseded=useSuperseded, useNonValidated=useNonValidated)
    return ret

def testPoint(inputFile, outputDir, databaseVersion, listOfExpRes):
    """
    Test model point defined in input file (running decomposition, check
    results, test coverage)

    :parameter inputFile: path to input file
    :parameter outputDir: path to directory where output is be stored
    :parameter parser: ConfigParser storing information from parameters file
    :parameter databaseVersion: Database version (printed to output file)
    :parameter listOfExpRes: list of ExpResult objects to be considered

    :return: dictionary with input filename as key and the MasterPrinter object as value
    """

    print("Starting to test point",inputFile)

    """Setup output printers"""
    masterPrinter = MPrinter()
    masterPrinter.Printers['python'] = PyPrinter(output='file')
    masterPrinter.Printers['summary'] = SummaryPrinter(output='file')
    masterPrinter.setOutPutFiles(os.path.join(outputDir, os.path.basename(inputFile)))

    """ Add list of analyses loaded to printer"""
    masterPrinter.addObj(ExpResultList(listOfExpRes))

    """Check input file for errors"""
    inputStatus = ioObjects.FileStatus()
    if checkInput: inputStatus.checkFile(inputFile)

    """Initialize output status and exit if there were errors in the input"""
    printParameters = [('sigmacut', str(sigmacut)), ('minmassgap', str(minmassgap)), ('maxcond', str(maxcond)), ('ncpus', str(ncpus)), ('model', str(particles)), ('promptWidth', str(promptWidth)), ('stableWidth', str(stableWidth)), ('checkInput', str(checkInput)), ('doInvisible', str(doInvisible)), ('doCompress', str(doCompress)), ('computestatistics', str(computeStatistics)), ('testcoverage', str(testCoverage)), ('combineSRs', str(combineSRs)), ('combineanas', ''), ('reportallsrs', str(reportAllSRs)), ('experimentalFeatures', str(experimentalFeatures)), ('useSuperseded', str(useSuperseded)), ('useNonValidated', str(useNonValidated))]

    printParameters = OrderedDict(printParameters)
    outputStatus = ioObjects.OutputStatus(inputStatus.status, inputFile, printParameters, databaseVersion)
    if outputStatus.status < 0:
        masterPrinter.addObj(outputStatus)
        return {os.path.basename(inputFile): masterPrinter}

    """
    Load the input model
    ====================
    """
    try:
        """
        Load the input model and  update it with the information from the input file
        """
        from smodels.particlesLoader import BSMList
        model = Model(BSMparticles=BSMList, SMparticles=SMList)
        model.updateParticles(inputFile=inputFile, promptWidth=promptWidth, stableWidth=stableWidth)
    except SModelSError as e:
        print("Exception %s %s" % (e, type(e)))
        """ Update status to fail, print error message and exit """
        outputStatus.updateStatus(-1)
        return {os.path.basename(inputFile): masterPrinter}

    """
    Decompose input Model
    =====================
    """

    try:
        """ Decompose the input Model, store the output elements in smstoplist """
        smstoplist = decomposer.decompose(model, sigmacut,
                                          doCompress=doCompress,
                                          doInvisible=doInvisible,
                                          minmassgap=minmassgap)
    except SModelSError as e:
        print("Exception %s %s" % (e, type(e)))
        """ Update status to fail, print error message and exit """
        outputStatus.updateStatus(-1)
        return {os.path.basename(inputFile): masterPrinter}

    """ Print Decomposition output.
        If no topologies with sigma > sigmacut are found, update status, write
        output file, stop running """
    if not smstoplist:
        outputStatus.updateStatus(-3)
        return {os.path.basename(inputFile): masterPrinter}

    masterPrinter.addObj(smstoplist)

    """
    Compute theory predictions
    ====================================================
    """

    """ Get theory prediction for each analysis and print basic output """
    allPredictions = []
    combineResults = combineSRs
    useBest = True
    try:
        if reportAllSRs:  # If set print out all SRs and skip combination
            useBest = False
            combineResults = False
    except (NoSectionError, NoOptionError):
        pass
    try:
        expFeatures = experimentalFeatures
        runtime._experimental = expFeatures
    except (NoSectionError, NoOptionError):
        pass

    if not useBest: print(f"\n\n!!!!!!! WILL NOT USE THE BEST SR RESULT, AND THE SR WILL NOT BE COMBINED FOR {inputFile} !!!!!!!!\n\n")

    allPredictions, combinablePredictions = [], []
    for expResult in listOfExpRes:
        theorypredictions = theoryPredictionsFor(expResult, smstoplist, useBestDataset=useBest, combinedResults=combineResults )

        if not theorypredictions:
            continue
        for tpred in theorypredictions._theoryPredictions:
            r_exp = tpred.getRValue(expected = True)
            if r_exp >= 0.1:
                combinablePredictions.append(tpred)
        allPredictions += theorypredictions._theoryPredictions

    """Compute chi-square and likelihood"""
    if computeStatistics:
        for theoPred in allPredictions:
            theoPred.computeStatistics()

    """ Define theory predictions list that collects all theoryPrediction objects which satisfy max condition."""
    theoryPredictions = TheoryPredictionList(allPredictions, maxcond)
    combinablePredictions = TheoryPredictionList(combinablePredictions, maxcond)

    if len(theoryPredictions) != 0:
        outputStatus.updateStatus(1)
        masterPrinter.addObj(theoryPredictions)
    else:
        outputStatus.updateStatus(0)  # no results after enforcing maxcond

    if testCoverage:
        """ Testing coverage of Model point, add results to the output file """
        uncovered = coverage.Uncovered(smstoplist, sigmacut=sigmacut, sqrts=None)
        masterPrinter.addObj(uncovered)

    """ Combine analyses """
    combineAnas = findBestCombination(combinablePredictions)

    if not combineAnas and len(combinablePredictions) == 1: # If only results for 1 analysis that has r_exp >= 0.1, the combination is this analysis.
        combineAnas = combinablePredictions                 # If no analysis with r_exp >= 0.1, but analyses with r_exp <= 0.1, no combination (even when only result for 1 analysis with r_exp <= 0.1)

    if combineAnas:
        combiner = TheoryPredictionsCombiner.selectResultsFrom(combineAnas, [ana.dataset.globalInfo.id for ana in combineAnas])
        # Only compute combination if at least one result was selected
        if combiner is not None and computeStatistics:
            combiner.computeStatistics()
        masterPrinter.addObj(combiner)


    printParameters = [('sigmacut', str(sigmacut)), ('minmassgap', str(minmassgap)), ('maxcond', str(maxcond)), ('ncpus', str(ncpus)), ('model', str(particles)), ('promptWidth', str(promptWidth)), ('stableWidth', str(stableWidth)), ('checkInput', str(checkInput)), ('doInvisible', str(doInvisible)), ('doCompress', str(doCompress)), ('computestatistics', str(computeStatistics)), ('testcoverage', str(testCoverage)), ('combineSRs', str(combineResults)), ('combineanas', ",".join([ana.dataset.globalInfo.id.strip() for ana in combineAnas])), ('reportallsrs', str(not useBest)), ('experimentalFeatures', str(experimentalFeatures)), ('useSuperseded', str(useSuperseded)), ('useNonValidated', str(useNonValidated))]

    printParameters = OrderedDict(printParameters)
    outputStatus.parameters = printParameters
    masterPrinter.addObj(outputStatus)

    return {os.path.basename(inputFile): masterPrinter}

def runSingleFile(inputFile, outputDir, databaseVersion, listOfExpRes, timeout, development):
    """
    Call testPoint on inputFile, write crash report in case of problems

    :parameter inputFile: path to input file
    :parameter outputDir: path to directory where output is be stored
    :parameter parser: ConfigParser storing information from parameter.ini file
    :parameter databaseVersion: Database version (printed to output file)
    :parameter listOfExpRes: list of ExpResult objects to be considered
    :parameter crashReport: if True, write crash report in case of problems
    :param timeout: set a timeout for one model point (0 means no timeout)
    :returns: output of printers
    """

    try:
        with timeOut.Timeout(timeout):
            res = testPoint(inputFile, outputDir, databaseVersion,
                             listOfExpRes)
            for fname,mprinter in res.items():
                res[fname] = mprinter.flush()
            return res
    except Exception as e:
        print("\n\n\n ****** Computation failed for",inputFile," because:",e+'\n\n\n')
        # crashReportFacility = crashReport.CrashReport()
        #
        # if development:
        #     print(crashReport.createStackTrace())
        #     raise e
    return {inputFile: None}

def runSetOfFiles(inputFiles, outputDir, databaseVersion, listOfExpRes, timeout, development):

    output = {}
    for inputFile in inputFiles:
        output.update(runSingleFile(inputFile, outputDir, databaseVersion,
                                    listOfExpRes, timeout, development))
        gc.collect()

    return output

def main(slhaFolder,nb_cpu_to_use,output):
    t0 = time.time()

    global ncpus
    ncpus = nb_cpu_to_use

    global outputDir
    outputDir = output

    if not os.path.isdir(outputDir): os.mkdir(outputDir)

    if reportAllSRs or not combineSRs: print("\n***** RUNNING WITHOUT SR COMBINATION *****\n")
    else: print("\n***** RUNNING WITH SR COMBINATION *****\n")

    alreadyDone = []
    for file in glob.glob(outputDir+'/*.py'):
        alreadyDone.append(os.path.basename(file).replace('.py',''))

    fileList = [file for file in os.listdir(slhaFolder) if file not in alreadyDone]

    fileList = [os.path.join(slhaFolder,file) for file in fileList]

    print(f'\nFound {len(os.listdir(slhaFolder))} files in inputDir {slhaFolder}, {len(alreadyDone)} were already in {outputDir}. The {len(fileList)} remaining files will be computed using {ncpus} CPUs and their output will be printed in {outputDir}.\n')

    runtime.modelFile = particles
    reload(particlesLoader)

    db = None
    if force_txt: db = True
    database, databaseVersion = loadDatabase(path, db)

    listOfExpRes = loadDatabaseResults(analyses,txnames,dataselector,useSuperseded,useNonValidated,database)

    chunkedFiles = [fileList[x::ncpus] for x in range(ncpus)]
    pool = multiprocessing.Pool(processes=ncpus)
    children = []
    for chunkFile in chunkedFiles:
        p = pool.apply_async(runSetOfFiles, args=(chunkFile, outputDir,
                                                  databaseVersion, listOfExpRes, timeout,
                                                  development))
        children.append(p)
    pool.close()

    outputDict = {}
    for p in children:
        outputDict.update(p.get())

    # Collect output to build global summary:
    summaryFile = os.path.join(outputDir, 'summary.txt')
    print("A summary of the results can be found in %s" %
                summaryFile)

    printScanSummary(outputDict, summaryFile)
    print("Done in %3.2f min" % ((time.time()-t0)/60.))

if __name__ == '__main__':
    main('./testDir/',2,'./outputFullScan/')
