#!/usr/bin/env python

"""
.. module:: checkDatabase
        :synopsis: Small module to check smodels-database.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""
#import sys
#sys.path.append('../smodels-tools/tools')
#from smodels_tools.tools import databaseBrowser
import databaseBrowser
import logging
import prettytable
import argparse
import types

FORMAT = '%(levelname)s in %(module)s.%(funcName)s(): %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

databaseBrowser.setLogLevel()

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
	argparser = argparse.ArgumentParser(description = 'Summarizes the content of smodels-database')
	argparser.add_argument ('-f', '--flags', help = 'enables checks of existence - default: False', action = 'store_true')
	argparser.add_argument ('-e', '--extended', help = 'enables detailed information - default: True', action = 'store_false')
	argparser.add_argument ('-fl', '--flagList', nargs = '?', help = 'list of requested information (gives only True or False) - default: INFO.TXT SMS.ROOT SMS.PY', type = types.StringType, default = 'INFO.TXT SMS.ROOT SMS.PY')
	argparser.add_argument ('-el', '--extendedList', nargs = '?', help = 'list of requested extended information - default: "PAS TOPOLOGIES"', type = types.StringType, default = 'PAS TOPOLOGIES')
	argparser.add_argument ('-fle', '--flagLevel', nargs = '?', help = 'set information level for checks only (0 - manual, 1 - reduced, 2 - standard, 3 - fully) - default: standard', type = types.StringType, default = '2')
	argparser.add_argument ('-ele', '--extendedLevel', nargs = '?', help = 'set information level for extended requests (0 - manual, 1 - reduced, 2 - standard, 3 - fully)- default: reduced', type = types.StringType, default = '1')
	argparser.add_argument ('-log', '--loggingLevel', nargs = '?', help = 'set verbosity - default: WARNING', type = types.StringType, default = 'warning')
	argparser.add_argument ('-af', '--addFlagList', nargs = '?', help = 'list of requested information added to preset list (gives only True or False) - no default', type = types.StringType, default = '')
	argparser.add_argument ('-ae', '--addExtendedList', nargs = '?', help = 'list of requested extended information added to preset list- no default', type = types.StringType, default = '')
	argparser.add_argument ('-at', '--axesTable', help = 'enables separated table for the axes lines - default: False', action = 'store_true')
	argparser.add_argument ('-ett', '--extendedTopologyTable', help = 'enables separated table for all topologies - default: False', action = 'store_true')
	
	args = argparser.parse_args()
	setLogLevel(level = args.loggingLevel)
	
	flagLevel = setInfoLevel(args.flagLevel)
	if args.flags:
		logger.info('set flag level to %s' %flagLevel)
	
	extendedLevel = setInfoLevel(args.extendedLevel)
	logger.info('set extended level to %s' %extendedLevel)
	
	
	extendedList = builtInfoList(extendedLevel, args.addExtendedList.split())
	flagList = builtInfoList(flagLevel, args.addFlagList.split(), args.flags)
	
	if extendedLevel == 'manual':
		if args.extendedList:
			extendedList = [el.strip() for el in args.extendedList.split()] 
			extendedList.insert(0, 'ANALYSIS')
			logger.info('Manually set list of queries: %s' %extendedList)
		else:
			logger.error('Set list of queries or choose different information level to get preset list!')
			
	if flagLevel == 'manual':
		if args.flagList:
			flagList = [el.strip() for el in args.flagList.split()] 
			flagList.insert(0, 'ANALYSIS')
			logger.info('Manually set List of queries: %s' %flagList)
		else:
			logger.error('Set list of queries or choose different information level to get preset list!')
	
	table1 = prettytable.PrettyTable(['ALL RUNS IN DATABASE'])
	table1.align['ALL RUNS IN DATABASE'] = 'l'
	table1.add_row([databaseBrowser.getAllRuns()])
	print >> outfile, table1
	
	print >> outfile, '\n************************************* ANALYSES FOR EACH RUN *************************************'
	for run in databaseBrowser.getAllRuns():
		print >> outfile,'\n~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ %s ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~' %run
		print >> outfile, databaseBrowser.getAllAnalyses(run)

	print >> outfile, '\n************************************* ANALYSIS INFORMATION FOR EACH RUN *************************************'
	if args.flags:
		print >> outfile,'\n=========================================== AVAILABLE INFORMATION ==========================================='
		createTable(flagList, flag = True)
		
	if args.extended:
		print >> outfile,'\n=========================================== DETAILED INFORMATION ==========================================='
		createTable(extendedList, axesT = args.axesTable, topologiesT = args.extendedTopologyTable)

def setInfoLevel(level):
	"""Makes the level of information requested more readable.
	
	"""
	
	if level == '0':
		level = 'manual'
	if level == '1':
		level = 'reduced'
	if level == '2':
		level = 'standard'
	if level == '3':
		level = 'fully'
	return level
	
def builtInfoList(level, add, flag = False):
	"""Builds a list containing all the requested keywords due to level of information and if flag or extended.
	
	"""
	
	allExtendedInfos = ['ANALYSIS', 'ARXIV', 'CONSTRAINTS', 'CHECKED', 'PUBLICATION', 'JOURNAL', 'AXES', 'PAS', 'PRETTYNAME', 'TOPOLOGIES', 'EXTENDEDTOPOLOGIES']
	allFlagInfos = ['ANALYSIS', 'INFO.TXT', 'SMS.ROOT', 'SMS.PY', 'CONSTRAINTS', 'AXES', 'PUBLIC', 'JOURNAL', 'PUBLICATION', 'ARXIV', 'CHECKED']
	
	if level == 'reduced':
		extendedList = ['ANALYSIS', 'CHECKED']
		flagList = ['ANALYSIS', 'INFO.TXT', 'SMS.ROOT', 'SMS.PY']
	if level == 'standard':
		extendedList = ['ANALYSIS', 'CHECKED', 'TOPOLOGIES']
		flagList = ['ANALYSIS', 'INFO.TXT', 'SMS.ROOT', 'SMS.PY', 'JOURNAL', 'PUBLICATION', 'ARXIV', 'CHECKED']
	if level == 'fully':
		extendedList = ['ANALYSIS', 'PAS','CHECKED', 'TOPOLOGIES', 'EXTENDEDTOPOLOGIES', 'AXES', 'ARXIV']
		flagList = allFlagInfos
	if level == 'manual':
		extendedList = []
		flagList = []
		
	if add and not flag:
		logger.debug('Additional extended queries: %s' %add)
		for el in add:
			if not el in extendedList:
				extendedList.append(el.strip())
		logger.debug('Enhanced extended: %s' %extendedList)

	if add and flag:
		logger.debug('Additional flag queries: %s' %add)
		for el in add:
			if not el in flagList:
				flagList.append(el.strip())
		logger.debug('Enhanced flag: %s' %flagList)
	
		
	if flag:
		return flagList
	return extendedList

def createTable(infoList, flag = False, axesT = False, topologiesT = False):
	
	for run in databaseBrowser.getAllRuns():
		print >> outfile,'\n~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ %s ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~' %run
		table = prettytable.PrettyTable(infoList)
		table.align['ANALYSIS'] = 'l'
		
		if axesT:
				axesTable = prettytable.PrettyTable(['ANALYSIS', 'AXES'])
				axesTable.align['ANALYSIS'] = 'l'
		if topologiesT:
				topologiesTable = prettytable.PrettyTable(['ANALYSIS', 'TOPOLOGY', 'EXTENDEDTOPOLOGIES'])
				topologiesTable.align['ANALYSIS'] = 'l'
				
		for analysis in databaseBrowser.getAllAnalyses(run):
			pas = 'not available'
			constraints = 'not available'
			public = 'not available'
			prettyName = 'not available'
			arxiv = 'not available'
			journal = 'not available'
			publication = 'not available'
			axes = ['not available']
			infoFlag, rootFlag, pyFlag = False, False, False
			Analysis = databaseBrowser.Analysis(analysis, run)
			if Analysis:
				pas = Analysis.getPAS()
				constraintsFlag = Analysis.checkConstraints()
				axesFlag = Analysis.checkAxes()
				axes = Analysis.getAxes()
				topologyNames = Analysis.getTopologyNames()
				extendedTopologyNames = Analysis.getExtendedTopologyNames()
				publicFLag = Analysis.checkPublic()
				public = Analysis.getPublic()
				arxivFlag = Analysis.checkArxiv()
				arxiv = Analysis.getArxiv()
				journalFlag = Analysis.checkJournal()
				journal = Analysis.getJournal()
				publicationFlag = Analysis.checkPublication()
				publication = Analysis.getPublication()
				checked = Analysis.getChecked()
				checkedFlag = Analysis.checkChecked()
				prettyName = Analysis.getPrettyName()
			if databaseBrowser.checkResults(run, analysis): infoFlag = True
			if databaseBrowser.checkResults(run, analysis, 'sms.root'): rootFlag = True
			if databaseBrowser.checkResults(run, analysis, 'sms.py'): pyFlag = True
		
			infoDict = {'ANALYSIS':analysis, 'ARXIV':arxiv, 'CHECKED':checked, 'PUBLICATION': publication, 'JOURNAL':journal, 'AXES':axes, 'PAS':pas, 'PRETTYNAME':prettyName, 'TOPOLOGIES':topologyNames, 'EXTENDEDTOPOLOGIES':extendedTopologyNames}
			if flag:
				infoDict = {'ANALYSIS': analysis, 'INFO.TXT': infoFlag, 'SMS.ROOT': rootFlag, 'SMS.PY': pyFlag, 'CONSTRAINTS': constraintsFlag, 'AXES': axesFlag, 'PUBLIC': public, 'JOURNAL':journalFlag, 'PUBLICATION': publicationFlag, 'ARXIV': arxivFlag,'CHECKED': checkedFlag}
			tableList = [infoDict[key] for key in infoList]
			logger.debug('Feeding into table: %s' %tableList)
			table.add_row(tableList)
			if axesT:
				if not axes:
					axesTable.add_row([analysis, 'not available'])
					axesTable.add_row(['----------------------', '----------------------'])
					continue
				for ax in axes:
					axesTable.add_row([analysis, ax])
				axesTable.add_row(['----------------------', '----------------------'])
				
			if topologiesT:
				if not extendedTopologyNames:
					topologiesTable.add_row([analysis, '', 'not available'])
					topologiesTable.add_row(['----------------------', '----------------------', '----------------------'])

					continue
				for key in extendedTopologyNames:
					topologiesTable.add_row([analysis, key, extendedTopologyNames[key]])
				topologiesTable.add_row(['----------------------', '----------------------', '----------------------'])

		print >> outfile, table		
		if axesT:
			print >> outfile, axesTable
		if topologiesT:
			print >> outfile, topologiesTable
			
		#table3.add_row([a, pas, i, sr, sp])
		#table4.add_row([a, top])
		#table9.add_row([a, check2, check])
		#table5.add_row([a, pas, gpu, garx, gjou])
		#table10.add_row([a, pas, isPublication, ijou, iarx])
		#if axes:
			#print axes
			#for axe in axes:
				#table8.add_row([a, axe])
				#print a, axe
			#table8.add_row(['----------------------', '----------------------'])
		#if extop:
			#table6.add_row([a, extop.keys()])
			#for key in extop:
				#table7.add_row([a, extop[key]])
			#table7.add_row(['----------------------', '----------------------'])
		#else: table6.add_row([a, extop])
		
	#print >> outfile, tableFlag
	##print >> outfile, table3	
	##print >> outfile, table5
	##print >> outfile, table9
	#print >> outfile, tableDetailed
	##print >> outfile, table8
	#print >> outfile, '\n,,,,,,,,,,,,,,,,,,,, INFORMATION ABOUT TOPOLOGIES ,,,,,,,,,,,,,,,,,,,, \n'
	##print >> outfile, table4
	##print >> outfile, table6
	#print >> outfile, '\n,,,,,,,,,,,,,,,,,,,, INFORMATION ABOUT EXTENDED TOPOLOGIES ,,,,,,,,,,,,,,,,,,,, \n'
	##print >> outfile, table7

	
outfile = open('Database.txt', 'w')
if __name__ == '__main__':
    main()	
    
print 'File Database.txt has been created'
outfile.close()