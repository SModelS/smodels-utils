#!/usr/bin/env python

"""
.. module:: copyDatabase
   :synopsis: A simple script that copies the results database to a target directory
   (needs an afs installation on this machine). 
### FIX ME: scp doesn't work yet!

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

import os
import sys
import setPath
from smodels_tools.helper import databaseBrowser
import argparse
import logging
import types

FORMAT = '%(levelname)s in %(module)s.%(funcName)s(): %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

def setLogLevel(level):
    """Sets the level of verbosity.
    
    """
    if level == 'debug':
        logger.setLevel(level=logging.DEBUG)
    if level == 'info':
        logger.setLevel(level=logging.INFO)
    if level == 'warning':
        logger.setLevel(level=logging.WARNING)
    if level == 'error':
        logger.setLevel(level=logging.ERROR)
    
def main():
    """Handles all command line options. Calls all functions.
    
    """
    argparser = argparse.ArgumentParser(description = \
    'Make a cleaned up copy of smodels-database')
    argparser.add_argument ('-t', '--target', nargs = '?', \
    help = 'target folder - default: ./clean-database', \
    type = types.StringType, default = './clean-database/')
    argparser.add_argument ('-rex', '--runExclusions', nargs = '?', \
    help = 'runs that should be totally excluded - default: RPV7', \
    type = types.StringType, default = 'RPV7')
    argparser.add_argument ('-aex', '--analysisExclusions', nargs = '?', \
    help = 'analyses that should be totally excluded \n \
    - default: DileptonicStop8TeV, RazorMono8TeV, SUS11010 and T1ttttCombination8TeV', \
    type = types.StringType, \
    default = 'DileptonicStop8TeV RazorMono8TeV T1ttttCombination8TeV SUS11010')
    #argparser.add_argument ('-scp', '--secureCopy', \
    #help = 'use scp to smodels instead of local copy from afs - default: False',\
    #action = 'store_true')
    argparser.add_argument ('-log', '--loggingLevel', nargs = '?', \
    help = 'set verbosity - default: WARNING', \
    type = types.StringType, default = 'warning')
    argparser.add_argument ('-b', '--Base', \
    help = 'set path to base-directory of smodels-database\n \
    - default: /afs/hephy.at/user/w/walten/public/sms/', \
    type = types.StringType, default = '/afs/hephy.at/user/w/walten/public/sms/')
    argparser.add_argument ('-blog', '--browserVerbosity',\
    help = 'set browser-verbosity - default: ERROR', \
    type = types.StringType, default = 'error')
    args = argparser.parse_args()

    
    targetPath = checkTarget(args.target)
    logger.info('Copying database to %s' %targetPath)
    
    browser = databaseBrowser.Browser(args.Base)
    browser.verbosity = args.browserVerbosity

    setLogLevel(level = args.loggingLevel)
    
    runExclusions = []
    for r in args.runExclusions.split():
        runExclusions.append(r)
    logger.info('Runs that are excluded: %s' %runExclusions)

    analysisExclusions = []
    for a in args.analysisExclusions.split():
        analysisExclusions.append(a)
    logger.info('Analyses that are excluded: %s' %analysisExclusions)

    infoLines = ['sqrts', 'lumi', 'pas', 'publication', 'constraint', \
    'condition', 'fuzzycondition','category', 'axes', 'superseded_by', 'supersedes']
    
    #scp = args.secureCopy
    scp = False
    logger.info('secure copy option is set to: %s' %scp)
    
    database = getDatabase(runExclusions, analysisExclusions, browser)
    goodAnalyses = getGoodAnalyses(browser, database)
    cleanedDatabase = getCleanedDatabase(goodAnalyses, database)
    
    if not scp:
        logger.debug('calling localCopy')
        localCopy(targetPath, cleanedDatabase, infoLines, browser)
    
    #if scp:
        #remoteCopy(targetPath, remove, cleanedDatabase, infoLines)
    

def checkTarget(path):
    """Checks if the target directory already exists.
    If so, the user can decide wether to remove it completely, 
    or to exit the script.
    
    """
    if os.path.exists(path):
        print 'Database %s already exists!' %path
        subdirs = os.listdir(path)
        subdirs = [d for d in subdirs if not '.' in d]
        if not subdirs:
            print 'Target %s already exists but is empty.' %path
            return path
        while True:
            userInput = raw_input('Remove old version of database? [y/n]:  ')
            if userInput == 'n':
                sys.exit()
            if userInput == 'y':
                for subdir in subdirs:
                    os.system('rm -r %s/%s' %(path, subdir))
                return path   
    os.mkdir(path)            
    return path
    
def getDatabase(runExclusions, analysisExclusions, browser):
    """Excludes all runs and analyses, that should not be copied.
    
    """
    
    db = browser.database
    #db = {run: db[run] for run in db if not run in runExclusions}
    database = {}
    keys = [key for key in db if not key in runExclusions]
    logger.debug('Remaining runs: %s' %keys)
    for key in keys:
        database[key] = [a for a in db[key] if not a in analysisExclusions]
        logger.debug('For run %s remaining analyses: %s' %(key, database[key]))
    return database

def getGoodAnalyses(browser, database):
    """Gets all analyses that are sufficient for the official database.
    
    """
    goodAnalyses = []
    for key in database:
        for ana in database[key]:
            expAna = browser.expAnalysis(ana)
            if expAna.isPublished and expAna.pas and expAna.isChecked \
            and expAna.hasPY and not expAna.private and expAna.publishedData:
                goodAnalyses.append(ana)
    return goodAnalyses 

def getGoodTopologies(browser, ana):
    """Gets all topologies for each analysis, which fulfill the requirements 
    for the official datbase.
    
    """
    goodTopologies = []
    badTopologies = []
    for t in browser.getTopologies(ana):
        res = browser.expResultSet(ana, t)
        if t in badTopologies: continue
        if not res: continue
        if not res.hasUpperLimitDicts(): continue
        if not res.condition: continue
        if res.condition.lower() == 'not yet assigned':
            continue
        if not res.constraint: continue
        if res.constraint.lower() == 'not yet assigned':
            continue
        if not res.fuzzyCondition: continue
        if res.fuzzyCondition.lower() == 'not yet assigned':
            continue
        if not res.axes: continue
        goodTopologies.append(t)
    return goodTopologies
        
        
        
    
def getCleanedDatabase(goodAnalyses, database):
    """Excludes all analyses that are insufficient.
    
    """
    for key in database:
        database[key] = [a for a in database[key] if a in goodAnalyses]
    keys = [key for key in database if database[key]]
    clean = {}
    for key in keys:
        clean[key] = database[key]
    logger.info('Cleaned database will contain: %s' %clean) 
    return clean
    
    
def localCopy(targetPath, cleanedDatabase, infoLines, browser):
    """Creates the folder structure for the cleaned version of the database and copies the files.
    
    """
    version = open('%s/version' %targetPath, 'w')
    versionString = 'Halloween2014 (%s-based)' %browser.databaseVersion
    print >> version, versionString
    version.close()
    for key in cleanedDatabase:
        os.mkdir(targetPath + key)
        logger.debug('created folder for run: %s' %key) 
        for a in cleanedDatabase[key]:
            path = '/' + key + '/' + a + '/'
            os.mkdir(targetPath + path)
            logger.debug('created folder for analysis: %s' %a)
            ##---------------------------------------------------------------
            #os.system('cp %s %s' %(browser.base + path + 'sms.py', targetPath + path + 'sms.py'))
            ## ### FIX ME: sms.py should be split into observed and expected dictionary -> only observed should be copied. Also fake entries (e.g. [None,None,None]) should be removed, as well as topologies which don't have valid entries in the info.txt
            #logger.debug('command looks like: cp %s %s' %(browser.base + path + 'sms.py', targetPath + path + 'sms.py'))
            ##---------------------------------------------------------------
            pathToSmsPy = targetPath + path + 'sms.py'
            topos = getGoodTopologies(browser, a)
            createSmsPy(browser, pathToSmsPy, topos, a)
            createInfo(targetPath, key, a, topos, infoLines, browser)
            
def remoteCopy():
    # ### FIX ME: how to? Is there a copy of smodels-database on smodels.hephy.at and can I use it here?
    #target = getTarget()
    pass

def createSmsPy(browser, path, topos, ana):
    """Splits the sms.py and creates a new one, that contains only 
    observed upper limits for "good" topologies.
    
    """
    f = open(path,'w')
    f.write("Dict={}\n")
    for t in topos:
        resSet = browser.expResultSet(ana, t)
        for key in resSet.results:
            extendedTopo = key.split('-')[1].strip()
            upperLimitDict = resSet.results[key].upperLimitDict()
            f.write("Dict['%s']=%s\n" %(extendedTopo, upperLimitDict))
    f.close()
            
            
        
    
    
def createInfo(target, run, ana, topos, infoLines, browser):
    """Creates the info.txt for every run-analysis and copies the requested lines.
    # ### FIX ME: write lines for valid topologies only and split axes accordingly. 
    """
    lines = []
    path = target + '/' + run + '/' + ana
    info = open('%s/info.txt' %path, 'w')
    logger.debug('creating info.txt file %s' %info)
    logger.debug('created info.txt in %s' %path)
    infoObject = databaseBrowser.Infotxt(ana, \
    browser.base + '/' + run + '/' + ana + '/' + 'info.txt')
    for requ in infoLines:
        logger.debug('try to get line for run %s, ana %s and keyword %s' %(run, ana, requ))
        if requ in infoObject.metaInfo:
            line = '%s: %s' %(requ, infoObject.metaInfo[requ])
            lines.append(line)
        else:
            for line in infoObject.info:
                if requ in line and not line in lines:
                    logger.debug('topo from line is %s' %(line.split(':')[1].split('->')[0].strip()))
                    if not line.split(':')[1].split('->')[0].strip() in topos:
                        continue
                    lines.append(line)
                    
    for line in lines:
        logger.debug('line is %s' %line)
        print >> info, line.strip()
    info.close()
        
    

            
    
if __name__ == '__main__':
    main()    
    
##-----------------------------------------------------------------------------------


#if useScp:
  #for Dir in Dirs:
    #Target="%s/%s" % (dest, Dir)
    #if os.path.exists ( Target ):
      #print "Warning:",Target,"exists already."
      #if force:
        #print "Requested removal of",Target
        #os.system ( "rm -rf %s" % Target )
    #cmd="scp -r smodels.hephy.at:%s/%s %s " % (DB, Dir, dest)
    #print cmd
    #os.system ( cmd )
#else:
  #localCopy ( dest, Dirs, force )
