#!/usr/bin/env python

#Given a SLHA file for a proto-model, runs all available CheckMATE analyses over it.
#The signal strength multipliers are automatically taken into account and only the
#processes listed in the XSECTION blocks of the SLHA file are generated.
#The main options are set using a parameter card.

#First tell the system where to find the modules:
import sys,os,shutil
import pyslha
import logging
import subprocess
import time,datetime
import multiprocessing
import tempfile
from MG5converter import convert_to_mg5card
sys.path.append('../')
from ptools import sparticleNames
try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError as e:
    from configparser import ConfigParser


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s at %(asctime)s'
logging.basicConfig(format=FORMAT,datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)


def getCheckMateCard(parserDict):
    """
    Create a process card using the input SLHA file.

    :param parserDict: Dictionary containing all the ConfigParser parameters.

    :return: The path to the process card
    """

    #Create a temporary checkmate card
    cardFile = tempfile.mkstemp(suffix='.dat', prefix='checkmateCard_',
                                   dir=os.getcwd())
    os.close(cardFile[0])
    cardFile = os.path.abspath(cardFile[1])

    #Get the required information from the SLHA file:
    slhafile = os.path.abspath(parserDict["options"]["SLHAfile"])
    if not os.path.isfile(slhafile):
        logger.error("SLHA file %s not found" %slhafile)
        return False
    try:
        slhaData = pyslha.readSLHAFile(slhafile)
    except:
        logger.error("Could not read SLHA file %s" %slhafile)
        return False

    #Convert SLHA file to the SLHA2 format accepted by MG5
    slha2file = convert_to_mg5card(slhafile,slhafile.replace('.slha','.slha2'))
    slha2file = os.path.abspath(slha2file)

    #Get cross-sections from SLHA file:
    xsections = slhaData.xsections

    pNames = sparticleNames.SParticleNames()

    logger.debug("Creating CheckMATE card file")
    #Generate CheckMate card file:
    #Set basic parameters:
    cardF = open(cardFile,'w')
    cardF.write("\n[Parameters]\n")
    cardF.write("SLHAFile: %s\n" %slha2file)
    cardF.write("Name: %s\n" %os.path.splitext(os.path.basename(slha2file))[0])
    cardF.write("OutputExists: overwrite\n")
    checkmatePars = parserDict["CheckMateParameters"]
    for key,val in checkmatePars.items():
        if '__' in key: continue
        cardF.write("%s: %s\n" %(key,val))

    processPars = parserDict["ProcessParameters"]

    if parserDict["CheckMateParameters"]["Analyses"].strip() == "13TeV":
        sqrts = 13000.
    elif parserDict["CheckMateParameters"]["Analyses"].strip() == "8TeV":
        sqrts = 8000.
    else:
        logger.error("Please set [CheckMateParameters][Analyses] to either 13TeV or 8TeV")
        return False

    #Add processes to checkmate card:
    for process in xsections.keys():
        procPIDs = process[2:]
        procName = "_".join([pNames.name(pid).replace('~','s').replace('^*','bar').replace('_','')
                             for pid in procPIDs])
        cardF.write("\n[%s]\n" %procName)
        MGcommand = "import model MSSM_SLHA2\n define p = g u c d s u~ c~ d~ s~ b b~\n generate p p > " + " ".join([str(pid) for pid in procPIDs])
        cardF.write("MGcommand: %s\n" %MGcommand)
        cardF.write("MGparam: %s\n" %slha2file)
        #Get cross-section:
        xs = max([xsec.value for xsec in xsections[process].xsecs
                  if xsec.sqrts == sqrts])
        cardF.write("XSect: %1.3e PB\n" %xs)
        #Write additional parameters defined in the input card:
        for key,val in processPars.items():
            if '__' in key: continue
            cardF.write("%s: %s\n" %(key,val))
    cardF.close()

    return cardFile

def RunCheckMate(parserDict):
    """
    Runs CheckMATE using the parameters given in parser.

    :param parserDict: Dictionary containing all the ConfigParser parameters.
    """


    pars = parserDict["options"]
    outputFolder = os.path.abspath(parserDict["CheckMateParameters"]["OutputDirectory"])
    if not "SLHAfile" in pars:
        logger.error("An SLHA file must be defined in options")
        return False
    slhaTag = pars["SLHAfile"]
    slhaTag =  os.path.splitext(os.path.basename(slhaTag))[0]
    resultFolder = os.path.join(outputFolder,slhaTag)
    if  not eval(parserDict["options"]['overwrite']) and os.path.isdir(resultFolder):
        logger.info("Results folder %s found. Skipping." %resultFolder)
        return "---- %s skipped" %resultFolder
    cardFile = getCheckMateCard(parserDict)
    if not cardFile or not os.path.isfile(cardFile):
        logger.error("Error creating CheckMATE steering file.")
        return False

    logger.debug('Steering card %s created' %cardFile)

    #Create output dirs, if do not exist:
    try:
        os.makedirs(outputFolder)
    except:
        pass

    #Run CheckMate
    checkmateFolder = pars['checkmateFolder']
    if not os.path.isdir(checkmateFolder):
        logger.error("CheckMATE folder %s not found. Try running the install_checkMate.sh script." %checkmateFolder)
        return False
    elif not os.path.isfile(os.path.join(checkmateFolder,'bin/CheckMATE')):
        logger.error("CheckMATE executable (%s/bin/CheckMATE) not found. Try running the install_checkMate.sh script." %checkmateFolder)
        return False


    logger.info('Running checkmate with steering card: %s ' %cardFile)
    run = subprocess.Popen('./%s/bin/CheckMATE %s' %(pars['checkmateFolder'],cardFile)
                       ,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errorMsg= run.communicate()
    logger.debug('CheckMATE error:\n %s \n' %errorMsg)
    logger.debug('CheckMATE output:\n %s \n' %output)

    os.remove(cardFile)

    convertCheckMateOutput(resultFolder)

    if not eval(parserDict["options"]['keepResultsFolder']):
        shutil.rmtree(resultFolder)


    logger.info("Done in %3.2f min" %((time.time()-t0)/60.))
    now = datetime.datetime.now()


    return "Finished running CheckMATE at %s" %(now.strftime("%Y-%m-%d %H:%M"))


def convertCheckMateOutput(outputFolder):
    """
    Reads the information in the CheckMATE output folder and convert it.

    :param outputFolder: CheckMATE output folder containing the results.
    """

    if not os.path.isdir(outputFolder):
        logger.error("CheckMATE output folder %s not found." %outputFolder)
        return False
    if not os.path.isfile(os.path.join(outputFolder,'result.txt')):
        logger.error("CheckMATE result.txt file not found in folder %s." %outputFolder)
        return False

    with open(os.path.join(outputFolder,'result.txt'),'r') as f:
        print('=======\nCheckMATE Result:\n=======')
        print(f.read())

    return True


def main(parfile,verbose):


    level = verbose.lower()
    levels = { "debug": logging.DEBUG, "info": logging.INFO,
               "warn": logging.WARNING,
               "warning": logging.WARNING, "error": logging.ERROR }
    if not level in levels:
        logger.error ( "Unknown log level ``%s'' supplied!" % level )
        sys.exit()
    logger.setLevel(level = levels[level])

    parser = ConfigParser()
    parser.optionxform=str
    ret = parser.read(parfile)
    if ret == []:
        logger.error( "No such file or directory: '%s'" % args.parfile)
        sys.exit()

    if not parser.has_option('options', 'SLHAfile'):
        logger.error("An input file SLHAfile must be defined.")
        return False

    parserList = [parser]
    ncpus = 1
    pool = multiprocessing.Pool(processes=ncpus)
    children = []
    #Loop over parsers and submit jobs
    logger.info("Submitting %i jobs over %i cores" %(len(parserList),ncpus))
    for newParser in parserList:
        parserDict = newParser._sections #Must convert to dictionary for pickling
        p = pool.apply_async(RunCheckMate, args=(parserDict,))
        children.append(p)
        time.sleep(1)

    #Wait for jobs to finish:
    output = [p.get() for p in children]
    for out in output:
        print(out)


if __name__ == "__main__":

    import argparse
    ap = argparse.ArgumentParser( description=
            "Run CheckMATE for a given protoModel SLHA file." )
    ap.add_argument('-p', '--parfile', default='checkmate_parameters.ini',
            help='path to the parameters file. Default is checkmate_parameters.ini')
    ap.add_argument('-v', '--verbose', default='error',
            help='verbose level (debug, info, warning or error). Default is error')


    t0 = time.time()

    args = ap.parse_args()

    t0 = time.time()

    args = ap.parse_args()
    output = main(args.parfile,args.verbose)

    print("\n\nDone in %3.2f min" %((time.time()-t0)/60.))
