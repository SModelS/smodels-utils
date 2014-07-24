#!/usr/bin/python

"""
.. module:: cleanCopyDatabase
   :synopsis: a simple script that downloads the results database to a target directory, either locally via 'cp' (needs an afs installation on this machine), or via scp to smodels 
### FIX ME: scp doesn't work jet!

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""
import os
#import sys
#sys.path.append('../smodels-tools/tools')
import setPath
from smodels_tools.tools import databaseBrowser
import argparse
import logging
import types

FORMAT = '%(levelname)s in %(module)s.%(funcName)s(): %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)

log.setLevel(level=logging.ERROR)
databaseBrowser.setLogLevel()

def setLogLevel(level):
	"""Sets the level of verbosity.
	
	"""
	if level == 'debug':
		log.setLevel(level=logging.DEBUG)
	if level == 'info':
		log.setLevel(level=logging.INFO)
	if level == 'warning':
		log.setLevel(level=logging.WARNING)
	if level == 'error':
		log.setLevel(level=logging.ERROR)
	
def main():
	"""Handles all command line options. Calls all functions.
	
	"""
	argparser = argparse.ArgumentParser(description = 'Make a cleaned up copy of smodels-database')
	argparser.add_argument ('-t', '--target', nargs = '?', help = 'target folder - default: ./clean-database', type = types.StringType, default = './clean-database/')
	argparser.add_argument ('-rex', '--runExclusions', nargs = '?', help = 'runs that should be totally excluded - default: RPV7', type = types.StringType, default = 'RPV7')
	argparser.add_argument ('-aex', '--analysisExclusions', nargs = '?', help = 'analyses that should be totally excluded - default: DileptonicStop8TeV, RazorMono8TeV and T1ttttCombination8TeV', type = types.StringType, default = 'DileptonicStop8TeV RazorMono8TeV T1ttttCombination8TeV')
	argparser.add_argument ('-rm', '--remove', help = 'remove old local copy, if exists - default: False', action = 'store_true')
	argparser.add_argument ('-scp', '--secureCopy', help = 'use scp to smodels instead of local copy from afs - default: False', action = 'store_true')
	argparser.add_argument ('-log', '--loggingLevel', nargs = '?', help = 'set verbosity - default: WARNING', type = types.StringType, default = 'warning')
	args = argparser.parse_args()

	
	targetPath = args.target
	log.info('copying database to %s' %targetPath)
	
	requestedLines = ['pas', 'checked']	# ### FIX ME: maybe make this switchable
	setLogLevel(level = args.loggingLevel)
	
	runExclusions = []
	for r in args.runExclusions.split():
		runExclusions.append(r)
	log.info('runs that are excluded: %s' %runExclusions)

	analysisExclusions = []
	for a in args.analysisExclusions.split():
		analysisExclusions.append(a)
	log.info('analyses that are excluded: %s' %analysisExclusions)

	infoLines = ['sqrts', 'lumi', 'pas', 'publication', 'constraint', 'condition', 'axes', 'superseded_by']
	remove = args.remove
	log.info('removal is set to: %s' %remove)
	scp = args.secureCopy
	log.info('secure copy option is set to: %s' %scp)
	
	cleanedDatabase = getCleanedDatabase(runExclusions, analysisExclusions, requestedLines)
	
	if scp == False and getTarget(targetPath, remove):
		log.debug('calling localCopy')
		localCopy(targetPath, remove, cleanedDatabase, infoLines)
	
	if scp == True and getTarget(targetPath, remove):
		remoteCopy(targetPath, remove, cleanedDatabase, infoLines)
	
def getTarget(path, rmv):
	"""Checks if the target directory already exists, if its empty or not and removes every old content if requested.
	
	"""
	
	if os.path.exists(path):
		subdirs = os.listdir(path)
		subdirs = [d for d in subdirs if not '.' in d]
		if subdirs == []:
			log.info('Target %s already exists but is empty.' %path)
			return path
		if subdirs != [] and rmv == False:
			log.warning('Target %s contents old version! To replace it use option -rm' %path)
			log.info('Target contents %s: ' %subdirs) 
			return None
		if subdirs != [] and rmv == True:
			for d in subdirs:
				os.system('rm -rf %s' %path+d)
			log.warning('Requested removal of old version in %s!' %path)
			return path
	else:
		os.mkdir(target)
		log.debug('created folder for cleaned database: %s' %target) 
		return path

def getCleanedDatabase(runExclusions, analysisExclusions, requestedLines):
	"""Excludes all runs and analyses, that should not be copied.
	
	"""
	db = databaseBrowser.getDatabase()
	database = {}
	keys = [key for key in db if not key in runExclusions]
	for key in keys:
		database[key] = [a for a in db[key] if not a in analysisExclusions]
		for requ in requestedLines:
			database[key] = [a for a in database[key] if databaseBrowser.getInfo(key, a, requ)]
	keys = [key for key in keys if not database[key] == []]
	clean = {}
	for key in keys:
		clean[key] = database[key]
	log.info('cleaned database will contain: %s' %clean) 
	return clean
	
	
def localCopy(targetPath, rmv, cleanedDatabase, infoLines):
	"""Creates the folder structure for the cleaned version of the database and copies the files.
	
	"""
	Base = databaseBrowser.Base
	target = getTarget(targetPath, rmv)
	
	for key in cleanedDatabase:
		os.mkdir(target + key)
		log.debug('created folder for run: %s' %key) 
		for a in cleanedDatabase[key]:
			path = '/' + key + '/' + a + '/'
			os.mkdir(target + path)
			log.debug('created folder for analysis: %s' %a)
			for f in ['sms.root', 'sms.py']:
				if databaseBrowser.checkResults(key, a, f):
					log.debug('copying file %s from %s to %s' %(f, Base + path, target + path))
					os.system('cp %s %s' %(Base + path + f, target + path + f))
					log.debug( 'command looks like: cp %s %s' %(Base + path + f, target + path + f))
			createInfo(target, key, a, infoLines)
			
def remoteCopy():
	# ### FIX ME: how to? Is there a copy of smodels-database on smodels.hephy.at and can I use it here?
	#target = getTarget()
	pass
	
def createInfo(target, run, ana, infoLines):
	"""Creates the info.txt for every run-analysis and copies the requested lines.
	
	"""
	path = target + '/' + run + '/' + ana
	info = open('%s/info.txt' %path, 'w')
	log.debug('creating info.txt file %s' %info)
	log.debug('created info.txt in %s' %path)
	for requ in infoLines:
		log.debug('try to get line for run %s, ana %s and keyword %s' %(run, ana, requ))
		line = databaseBrowser.getInfo(run, ana, requ)
		log.debug('line is %s' %line)
		if line:
			for i in line:
				print >> info, i.strip()
	

			
	
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
