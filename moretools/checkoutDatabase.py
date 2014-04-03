#!/usr/bin/env python

"""
.. module:: checkoutDatabase
        :synopsis: Small module to check smodels-database.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""
#import sys
#sys.path.append('../smodels-tools/moretools')
import databaseBrowser
import logging
import prettytable as PT

FORMAT = '%(levelname)s in %(module)s.%(funcName)s(): %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)
log.setLevel(level=logging.DEBUG)

outfile = open('Database.txt', 'w')

databaseBrowser.setLogLevel()

table1 = PT.PrettyTable(['ALL RUNS IN DATABASE'])
table1.align['ALL RUNS IN DATABASE'] = 'l'
table1.add_row([databaseBrowser.getAllRuns()])
print >> outfile, table1

print >> outfile, '\n********************* ANALYSES FOR EACH RUN *********************'
for r in databaseBrowser.getAllRuns():
	print >> outfile, '\n----------------- %s -----------------' %r
	print >> outfile, databaseBrowser.getAllAnalyses(r)

print >> outfile, '\n*************** ANALYSIS INFORMATION FOR EACH RUN ***************'
for r in databaseBrowser.getAllRuns():
	print >> outfile,'\n------------------------ %s ------------------------' %r
	table3extended = PT.PrettyTable(['ANALYSIS', 'PAS', 'INFO.TXT', 'SMS.ROOT', 'SMS.PY', 'CONSTRAINTS', 'AXES', 'PUBLIC', 'PRIVATE', 'ARXIV'])
	table3extended.align['ANALYSIS'] = 'l'
	table3 = PT.PrettyTable(['ANALYSIS', 'PAS', 'INFO.TXT', 'SMS.ROOT', 'SMS.PY'])
	table3.align['ANALYSIS'] = 'l'
	table10 = PT.PrettyTable(['ANALYSIS', 'PAS', 'PUBLICATION?', 'JOURNAL?', 'ARXIV?'])
	table10.align['ANALYSIS'] = 'l'
	table4 = PT.PrettyTable(['ANALYSIS', 'TOPOLOGIES'])
	table4.align['ANALYSIS'] = 'l'
	table8 = PT.PrettyTable(['ANALYSIS', 'AXES'])
	table8.align['ANALYSIS'] = 'l'
	table9 = PT.PrettyTable(['ANALYSIS', 'CHECKED?', 'CHECKED'])
	table9.align['ANALYSIS'] = 'l'
	table5 = PT.PrettyTable(['ANALYSIS', 'PAS', 'PUBLICATION', 'ARXIV', 'JOURNAL'])
	table5.align['ANALYSIS'] = 'l'
	table6 = PT.PrettyTable(['ANALYSIS', 'EXTENDED TOPOLOGIES FOR'])
	table6.align['ANALYSIS'] = 'l'
	table7 = PT.PrettyTable(['TOPOLOGY', 'EXTENDED TOPOLOGIES'])
	table7.align['TOPOLOGY'] = 'l'
	
	for a in databaseBrowser.getAllAnalyses(r):
		pas = 'not available'
		con = 'not available'
		ipu = 'not available'
		pr = 'not available'
		iarx = 'not available'
		jou = 'not available'
		publication = 'not available'
		axes = ['not available']
		Ana = databaseBrowser.Analysis(a, r)
		if Ana:
			pas = Ana.getPAS()
			con = Ana.checkConstraints()
			ax = Ana.checkAxes()
			top = Ana.getTopologyNames()
			extop = Ana.getExtendedTopologyNames()
			ipu = Ana.checkPublic()
			gpu = Ana.getPublic()
			iarx = Ana.checkArxiv()
			ijou = Ana.checkJournal()
			gjou = Ana.getJournal()
			isPublication = Ana.checkPublication()
			getPublication = Ana.getPublication()
			garx = Ana.getArxiv()
			axes = Ana.getAxes()
			check = Ana.getChecked()
			check2 = Ana.checkChecked()
		i, sr, sp = False, False, False
		if databaseBrowser.checkResults(r, a): i = True
		if databaseBrowser.checkResults(r, a, 'sms.root'): sr = True
		if databaseBrowser.checkResults(r, a, 'sms.py'): sp = True
		table3extended.add_row([a, pas, i, sr, sp, con, ax, ipu, pr, iarx])
		table3.add_row([a, pas, i, sr, sp])
		table4.add_row([a, top])
		table9.add_row([a, check2, check])
		table5.add_row([a, pas, gpu, garx, gjou])
		table10.add_row([a, pas, isPublication, ijou, iarx])
		if axes:
			print axes
			for axe in axes:
				table8.add_row([a, axe])
				print a, axe
			table8.add_row(['----------------------', '----------------------'])
		if extop:
			table6.add_row([a, extop.keys()])
			for key in extop:
				table7.add_row([a, extop[key]])
			table7.add_row(['----------------------', '----------------------'])
		else: table6.add_row([a, extop])
		
	#print >> outfile, table3extended
	print >> outfile, table3	
	#print >> outfile, table5
	#print >> outfile, table9
	print >> outfile, table10
	print >> outfile, table8
	print >> outfile, '\n,,,,,,,,,,,,,,,,,,,, INFORMATION ABOUT TOPOLOGIES ,,,,,,,,,,,,,,,,,,,, \n'
	print >> outfile, table4
	#print >> outfile, table6
	print >> outfile, '\n,,,,,,,,,,,,,,,,,,,, INFORMATION ABOUT EXTENDED TOPOLOGIES ,,,,,,,,,,,,,,,,,,,, \n'
	print >> outfile, table7
	print 'File Database.txt has been created'
	
outfile.close()
