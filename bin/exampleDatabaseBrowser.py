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
	
	print '\n===========================\n'
	# get a specified Analysis-object 
	analysis = databaseBrowser.Analysis('SUS13002')
	print 'Analysis-object: ', analysis
	# use this object
	print '\nAnalysis is: ', analysis.getName()
	print 'PAS: ', analysis.getPAS()
	print 'Luminosity: ', analysis.getLumi()
	print 'Experiment: ', analysis.getExperiment()
	print 'Comment: ', analysis.getComment()
	print 'Is analysis published?  ', analysis.checkPublic()
	print ''

	print '\n===========================\n'
	# to get specified Topology-object
	topology = databaseBrowser.Topology('T1')
	print 'Name of this topology: ', topology.getName()
	print 'Topology-object: ', topology
	# use this object
	print 'Analyses that contain this topology: ', topology.getAnalysisNames(run = '8TeV')
	print ''
	
	print '\n===========================\n'
	# to get a specified Pair-object
	pair = databaseBrowser.Pair(['8TeV','SUS13002', 'T1tttt'])
	print 'Pair-object is: ', pair
	# use this object
	print '\nResult is checked: ', pair.checkedBy()
	print '\nGet all the exclusionlines: ', pair.getExclusionLines()
	print '\nSelect a specified exclusionline: ', pair.selectExclusionLine(expected = True, sigma = 1)
	
	# get Analysis belonging to this Pair:
	analysis = pair.getAnalysis()
	print '\nNow we have an Analysis-object: ', analysis
	print '\nFor this Pair the PAS is: ', analysis.getPAS()
	print ''
	
	
if __name__ == '__main__':
    main()	