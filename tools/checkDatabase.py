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

FORMAT = '%(levelname)s in %(module)s.%(funcName)s(): %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

outfile = open('Database.txt', 'w')

databaseBrowser.setLogLevel()

# ### FIX ME manipulate with argparser:
flags = True
#flags = False
level = 'fully'
#level = 'extended'
#level = 'standard'
analysisInfoList = ['ARXIV', 'CONSTRAINTS', 'CHECKED', 'PUBLICATION', 'JOURNAL', 'AXES', 'INFO.TXT', 'SMS.ROOT', 'SMS.PY', 'PUBLIC', 'PAS', 'PRETTYNAME', 'TOPOLOGIES']
flagList = ['ANALYSIS', 'INFO.TXT', 'SMS.ROOT', 'SMS.PY', 'CONSTRAINTS', 'AXES', 'PUBLIC', 'JOURNAL', 'PUBLICATION', 'ARXIV', 'CHECKED']
detailed = True
detailedList = ['ANALYSIS', 'CONSTRAINTS', 'AXES', 'CHECKED']

table1 = prettytable.PrettyTable(['ALL RUNS IN DATABASE'])
table1.align['ALL RUNS IN DATABASE'] = 'l'
table1.add_row([databaseBrowser.getAllRuns()])
print >> outfile, table1

print >> outfile, '\n************************************* ANALYSES FOR EACH RUN *************************************'
for run in databaseBrowser.getAllRuns():
	print >> outfile, '\n~~~~~~~~~~~~~~~~~~~~~~~~ %s ~~~~~~~~~~~~~~~~~~~~~~~~' %run
	print >> outfile, databaseBrowser.getAllAnalyses(run)

print >> outfile, '\n************************************* ANALYSIS INFORMATION FOR EACH RUN *************************************'
for run in databaseBrowser.getAllRuns():
	print >> outfile,'\n~~~~~~~~~~~~~~~~~~~~~~~~ %s ~~~~~~~~~~~~~~~~~~~~~~~~' %run
	if flags:
		print >> outfile,'\n-------------------------- AVAILABLE --------------------------'
		if level == 'fully':
			tableFlag = prettytable.PrettyTable(flagList)
			tableFlag.align['ANALYSIS'] = 'l'
			
	if detailed:
		tableDetailed = prettytable.PrettyTable(detailedList)
		tableDetailed.align['ANALYSIS'] = 'l'
		#table5 = prettytable.PrettyTable(['ANALYSIS', 'PAS', 'PUBLICATION', 'JOURNAL', 'ARXIV'])
	#table10.align['ANALYSIS'] = 'l'
	#table4 = prettytable.PrettyTable(['ANALYSIS', 'TOPOLOGIES'])
	#table4.align['ANALYSIS'] = 'l'
	#table8 = prettytable.PrettyTable(['ANALYSIS', 'AXES'])
	#table8.align['ANALYSIS'] = 'l'
	#table9 = prettytable.PrettyTable(['ANALYSIS', 'CHECKED?', 'CHECKED'])
	#table9.align['ANALYSIS'] = 'l'
	#table5 = prettytable.PrettyTable(['ANALYSIS', 'PAS', 'PUBLICATION', 'ARXIV', 'JOURNAL'])
	#table5.align['ANALYSIS'] = 'l'
	#table6 = prettytable.PrettyTable(['ANALYSIS', 'EXTENDED TOPOLOGIES FOR'])
	#table6.align['ANALYSIS'] = 'l'
	#table7 = prettytable.PrettyTable(['TOPOLOGY', 'EXTENDED TOPOLOGIES'])
	#table7.align['TOPOLOGY'] = 'l'
	
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
		detailedDictionary = {'ANALYSIS':analysis, 'ARXIV':arxiv, 'CONSTRAINTS':constraints, 'CHECKED':checked, 'PUBLICATION': publication, 'JOURNAL':journal, 'AXES':axes, 'PAS':pas, 'PRETTYNAME':prettyName, 'TOPOLOGIES':topologyNames}
		if flags:
			#for key in infoFlag:
			tableFlag.add_row([analysis, infoFlag, rootFlag, pyFlag, constraintsFlag, axesFlag, publicFLag, journalFlag, publicationFlag, arxivFlag, checkedFlag])
		if detailed:
			tableList = []
			for key in detailedList:
				tableList.append(detailedDictionary[key])
			tableDetailed.add_row(tableList) 
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
		
	print >> outfile, tableFlag
	#print >> outfile, table3	
	#print >> outfile, table5
	#print >> outfile, table9
	print >> outfile, tableDetailed
	#print >> outfile, table8
	print >> outfile, '\n,,,,,,,,,,,,,,,,,,,, INFORMATION ABOUT TOPOLOGIES ,,,,,,,,,,,,,,,,,,,, \n'
	#print >> outfile, table4
	#print >> outfile, table6
	print >> outfile, '\n,,,,,,,,,,,,,,,,,,,, INFORMATION ABOUT EXTENDED TOPOLOGIES ,,,,,,,,,,,,,,,,,,,, \n'
	#print >> outfile, table7
	print 'File Database.txt has been created'
	
outfile.close()
