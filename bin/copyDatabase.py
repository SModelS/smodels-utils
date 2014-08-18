#!/usr/bin/env python

"""
.. module:: copyDatabase
   :synopsis: A simple script that copies the results database to a target directory
   (needs an afs installation on this machine). 
### FIX ME: scp doesn't work jet!

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

import os
import sys
#sys.path.append('../smodels-tools/tools')
import setPath
from smodels_tools.tools import databaseBrowser
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
    help = 'runs that should be totally excluded - default: RPV7, RPV8, 2011', \
    type = types.StringType, default = 'RPV7, RPV8, 2011')
    argparser.add_argument ('-aex', '--analysisExclusions', nargs = '?', \
    help = 'analyses that should be totally excluded \n \
    - default: DileptonicStop8TeV, RazorMono8TeV and T1ttttCombination8TeV', \
    type = types.StringType, \
    default = 'DileptonicStop8TeV RazorMono8TeV T1ttttCombination8TeV')
    argparser.add_argument ('-scp', '--secureCopy', \
    help = 'use scp to smodels instead of local copy from afs - default: False',\
    action = 'store_true')
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
    
    browser = Browser(args.Base)
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
    'condition', 'fuzzycondition','category', 'axes', 'superseded_by', 'superseds']
    
    scp = args.secureCopy
    logger.info('secure copy option is set to: %s' %scp)
    
    database = getDatabase(runExclusions, analysisExclusions, browser)
    goodAnalyses = getGoodAnalyses(browser, database)
    cleanDatabase = getCleanedDatabase(goodAnalyses, database)
    
    if not scp:
        logger.debug('calling localCopy')
        localCopy(targetPath, cleanDatabase, infoLines)
    
    #if scp:
        #remoteCopy(targetPath, remove, cleanedDatabase, infoLines)
    

def checkTarget(path):
    """Checks if the target directory already exists.
    If so, the user can decide wether to remove it completely, 
    or to exit the script.
    
    """
    if os.path.exists(path):
        print 'Folder %s already exists!' %path
        subdirs = os.listdir(path)
        subdirs = [d for d in subdirs if not '.' in d]
        if not subdirs:
            print 'Target %s already exists but is empty.' %path
            return path
        while True:
            userInput = raw_input('Remove old files? [y/n]:  ')
            if userInput == 'n':
                sys.exit()
            if userInput == 'y':
                os.system('rm -r %s' %path)
                return path
    os.mkdir(path)            
    return path
    
def getDatabase(runExclusions, analysisExclusions, browser):
    """Excludes all runs and analyses, that should not be copied.
    
    """
    
    db = browser.database
    database = {}
    keys = [key for key in db if not key in runExclusions]
    for key in keys:
        database[key] = [a for a in db[key] if not a in analysisExclusions]
    return database

def getGoodAnalyses(browser, database):
    """Gets all analyses that are sufficient for the official database.
    
    """
    goodAnalyses = []
    for key in database:
        for ana in database[key]:
            expAna = browser.expAnalysis(a)
            if expAna.isPublished and expAna.pas and expAna.isChecked \
            and expAna.hasPY and not expAna.private:
                goodAnalyses.append(a)
    return goodAnalyses 
    
def getCleanedDatabase(goodAnalyses, database):
    """Excludes all analyses that are insufficient.
    
    """
    database[key] = [a for a in database[key] if a in goodAnalyses]
    keys = [key for key in keys if database[key]]
    clean = {}
    for key in keys:
        clean[key] = database[key]
    logger.info('Cleaned database will contain: %s' %clean) 
    return clean
    
    
def localCopy(targetPath, cleanDatabase, infoLines):
    """Creates the folder structure for the cleaned version of the database and copies the files.
    
    """
    
    for key in cleanDatabase:
        os.mkdir(targetPath + key)
        logger.debug('created folder for run: %s' %key) 
        for a in cleanedDatabase[key]:
            path = '/' + key + '/' + a + '/'
            os.mkdir(targetPath + path)
            logger.debug('created folder for analysis: %s' %a)
            os.system('cp %s %s' %(Base + path + 'sms.py', target + path + 'sms.py'))
                    logger.debug( 'command looks like: cp %s %s' %(Base + path + 'sms.py', target + path + 'sms.py'))
            createInfo(target, key, a, infoLines)
            
def remoteCopy():
    # ### FIX ME: how to? Is there a copy of smodels-database on smodels.hephy.at and can I use it here?
    #target = getTarget()
    pass
    
def createInfo(target, run, ana, infoLines, browser):
    """Creates the info.txt for every run-analysis and copies the requested lines.
    
    """
    path = target + '/' + run + '/' + ana
    info = open('%s/info.txt' %path, 'w')
    logger.debug('creating info.txt file %s' %info)
    logger.debug('created info.txt in %s' %path)
    infoObject = databaseBrowser.Infotxt(ana, \
    browser.base + '/' + run + '/' + ana + '/' + 'info.txt')
    for requ in infoLines:
        logger.debug('try to get line for run %s, ana %s and keyword %s' %(run, ana, requ))
        if requ in infoObject.metaInfo:
            line = '%s: %s' %(requ, info.metaInfo[requ])
            logger.debug('line is %s' %line)
            print >> info, line.strip()
        else:
            for line in infoObject.info:
                if requ in line:
                logger.debug('line is %s' %line)
                print >> info, line.strip()   
        
    

            
    
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
