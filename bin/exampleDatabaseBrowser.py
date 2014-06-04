#!/usr/bin/env python

"""
.. module:: exampleDatabaseBrowser
   :synopsis: Small script to show how the databaseBrowser module can be used to access smodels-database. 

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


"""

import ROOT
import setPath
from tools import databaseBrowser

def main():
	# set the level of the logger (default: error ; possible: debug, info, warning, error) 
	databaseBrowser.setLogLevel('warning')
	
	#set the path to the database (default - "/afs/hephy.at/user/w/walten/public/sms/") if the path does not exist or if there is no valid sms-database, databaseBrowser will be stoped
	databaseBrowser.base = '../../smodels-database/'

	# to get the structure of the database:
	database = databaseBrowser.getDatabase()
	print ''
	print '\nStructure of database: ',database
	print ''
	
	# get a specified Analysis-object 
	Analysis = databaseBrowser.Analysis('SUS13002')
	print 'Analysis-object: ', Analysis
	# use this object
	print '\nAnalysis is: ', Analysis.getName()
	print 'PAS: ', Analysis.getPAS()
	print 'luminosity: ', Analysis.getLumi()
	print 'Experiment: ', Analysis.getExperiment()
	print 'comment: ', Analysis.getComment()
	print ''

	# to get specified Topology-object
	Topology = databaseBrowser.Topology('T1')
	print 'Topology-object: ', Topology
	# use this object
	print 'Analyses that contain this topology: ', Topology.getAnalysisNames(run = '8TeV')
	print ''
	
	# to get a specified Pair-object
	Pair = databaseBrowser.Pair(['8TeV','SUS13002', 'T1tttt'])
	print 'Pair-object is: ', Pair
	# use this object
	print '\nResult is checked: ', Pair.checkedBy()
	print '\nGet all the exclusionlines: ', Pair.getExclusionLines()
	print '\nSelect a specified exclusionline: ', Pair.selectExclusionLine(expected = True, sigma = 1)
	
	# get Analysis belonging to this Pair:
	Analysis = Pair.getAnalysis()
	print '\nNow we have an Analysis-object: ', Analysis
	print '\nFor this Pair the PAS is: ', Analysis.getPAS()
	print ''
	
	
if __name__ == '__main__':
    main()	