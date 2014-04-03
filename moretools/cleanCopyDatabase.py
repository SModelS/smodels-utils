#!/usr/bin/python

""" a simple script that downloads the results database to a target directory, either locally via 'cp' (needs an afs installation on this machine), or via scp to smodels 
### FIX ME: scp doesn't work jet!
"""
import os
#import sys
#sys.path.append('../smodels-tools/moretools')
import databaseBrowser
import argparse
import logging
import types

FORMAT = '%(levelname)s in %(module)s.%(funcName)s(): %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)

log.setLevel(level=logging.DEBUG)
databaseBrowser.setLogLevel()

argparser = argparse.ArgumentParser(description = 'Make a cleaned up copy of smodels-database')
#argparser.add_argument ('-h', '--help', nargs = '?', help = 'target folder', type = types.StringType, default = '../clean-database/')
#argparser.add_argument('-d', '--default', help = 'use default settings') 
argparser.add_argument ('-t', '--target', nargs = '?', help = 'target folder - default: ./clean-database', type = types.StringType, default = './clean-database/')
argparser.add_argument ('-rex', '--runExclusions', nargs = '?', help = 'runs that should be totally excluded - default: RPV7 and RPV8', type = types.StringType, default = 'RPV7 RPV8')
argparser.add_argument ('-aex', '--analysisExclusions', nargs = '?', help = 'analyses that should be totally excluded - default: DileptonicStop8TeV, RazorMono8TeV and T1ttttCombination8TeV', type = types.StringType, default = 'DileptonicStop8TeV RazorMono8TeV T1ttttCombination8TeV')
argparser.add_argument ('-rm', '--remove', help = 'remove old local copy, if exists - default: False', action = 'store_true')
argparser.add_argument ('-scp', '--secureCopy', help = 'use scp to smodels instead of local copy from afs - default: False', action = 'store_true')
args = argparser.parse_args()

targetPath = args.target
log.debug('copying database to %s' %targetPath)

runExclusions = []
for r in args.runExclusions.split():
	runExclusions.append(r)
log.debug('runs that are excluded: %s' %runExclusions)

analysisExclusions = []
for a in args.analysisExclusions.split():
	analysisExclusions.append(a)
log.debug('analyses that are excluded: %s' %analysisExclusions)

infoLines = ['sqrts', 'lumi', 'pas', 'journal', 'constraint', 'condition', 'axes', 'superseded_by']
remove = args.remove
log.debug('removal is set to: %s' %remove)
scp = args.secureCopy
log.debug('secure copy option is set to: %s' %scp)

def getTarget(path = targetPath, rmv = remove):
	if os.path.exists(path):
		if rmv == False:
			log.warning('Target %s already exists! To replace it use option -rm' %path)
			return None
		else:
			os.system('rm -rf %s' %path)
			log.warning('Requested removal of %s!' %path)
			return path
	else: return path

def getCleanedDatabase(runExclusions = runExclusions, analysisExclusions = analysisExclusions):
	db = databaseBrowser.getDatabase()
	database = {}
	keys = [key for key in db if not key in runExclusions]
	for key in keys:
		database[key] = [a for a in db[key] if not a in analysisExclusions]
	log.debug('cleaned database: %s' %database) 
	return database
	
	
def localCopy():
	Base = databaseBrowser.Base
	target = getTarget()
	cleanedDatabase = getCleanedDatabase()
	os.mkdir(target)
	log.debug('created folder for cleaned database: %s' %target) 
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
					print 'cp %s %s' %(Base + path + f, target + path + f)
			createInfo(target, key, a)
			
def remoteCopy():
	# ### FIX ME: how to? Is there a copy of smodels-database on smodels.hephy.at and can I use it here?
	target = getTarget()
	
def createInfo(target, run, ana, infoLines = infoLines):
	path = target + '/' + run + '/' + ana
	info = open('%s/info.txt' %path, 'w')
	print info
	log.debug('created info.txt in %s' %path)
	for requ in infoLines:
		log.debug('try to get line for run %s, ana %s and keyword %s' %(run, ana, requ))
		line = databaseBrowser.getInfo(run, ana, requ)
		log.debug('line is %s' %line)
		if line:
			for i in line:
				print >> info, i.strip()
	
if scp == False and getTarget():
	log.debug('calling localCopy')
	localCopy()
	
if scp == True and getTarget():
	remoteCopy()
			
	
	
	
##-----------------------------------------------------------------------------------
#import os, sys

#def usage():
  #print "Usage:",sys.argv[0]," [-h] [-r] [-scp] <destination_directory>"
  #print "        -scp: use scp to smodels instead of local cp (from afs)"
  #print "        -h: show this help"
  #print "        -r: remove old local database, if exists"
  #sys.exit(0)

#def localCopy ( dest, Dirs, force ):
  #cmd="cp -r"
  #for Dir in Dirs:
    #Target="%s/%s" % (dest, Dir)
    #print "Dir",Target
    #if os.path.exists ( Target ):
      #print "Warning:",Target,"exists already."
      #if force:
        #print "Requested removal of",Target
        #os.system ( "rm -rf %s" % Target )
  ##  if not os.path.exists ( Target ):
  ##    os.mkdir ( Target )
    #cmd+=" %s/%s " % ( DB, Dir )
  #cmd+= dest
  #print cmd
  #os.system ( cmd )
  #stripDatabase ( dest, Dirs )

#def stripAnalysis ( path ):
  #Files=os.listdir ( path )
  #print "stripping",path,Files
  #for F in Files:
    #if not F in [ "sms.py", "sms.root", "info.txt" ]:
    ### if F in [ "orig", "old", "convert.py", "draw.py", "Standardizer.py", "convert.py~", "#Standardizer.py#", "info.txt_", "info.old", "Standardizer.pyc", "#convert.py#", "results" ]:
      #cmd="rm -rf %s/%s" % ( path, F )
      #print cmd
      #os.system ( cmd )

#def stripDatabase ( dest, Dirs ):
  #for Dir in Dirs:
    #path=dest + "/" + Dir
    #anas= os.listdir ( path )
    #for ana in anas:
      #if ana.lower() in ['old', 'bad', 'missing', 'todo', 'readme']: continue
      #if ana[0]==".": continue
      #if ana[-3:] in [ ".py", ".sh" ]: continue
      #stripAnalysis ( path+"/"+ana )

#if len(sys.argv)<2:
  #usage()

#useScp=False
#force=False

#for i in sys.argv[1:]:
  #if i=="-scp": useScp=True
  #if i=="-h": usage()
  #if i=="-r": force=True

#dest=sys.argv[-1]
#print "Installing the database to %s:" % dest

#if not os.path.exists ( dest ):
  #os.mkdir ( dest )

#DB="/afs/hephy.at/user/w/walten/public/sms"

#Dirs=[ "2011", "2012", "RPV7", "RPV8", "ATLAS8TeV","8TeV" ]

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
