#!/usr/bin/env python

"""
.. module:: exampleDatabaseBrowser
     :synopsis: Small script to show how the databaseBrowser module can be used to access smodels-database. 

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


"""

import ROOT
import setPath
from smodels_tools.tools import databaseBrowser

def main():
  # set the level of the logger (default: error ; possible: debug, info, warning, error) 
  # databaseBrowser.setLogLevel('warning')
  
  #set the path to the database (default - "/afs/hephy.at/user/w/walten/public/sms/") if the path does not exist or if there is no valid sms-database, databaseBrowser will be stopped

  browser = databaseBrowser.Browser ( '../../smodels-database/' )

  # to get the structure of the database:
  database = browser.database
  print ''
  print '\nStructure of database: ',database
  print ''
  
  # get a specified Analysis-object 
  analysis = browser.expAnalysis('SUS13002')
  print '\nAnalysis is: ', analysis.name
  print 'Analysis-object: ', analysis
  print 'PAS: ', analysis.pas
  print 'luminosity: ', analysis.lumi
  print 'Experiment: ', analysis.experiment
  print 'comment: ', analysis.comment
  print 'axes: ', analysis.axes
  print 'parametrizations of third mass: ', analysis.massParametrizations
  print
  print

  # to get specified Topology-object
  topology = browser.expTopology('TChiChipmSlepStau')
  print 'topology is: ', topology.name
  print 'Print out this topology:'
  print str(topology)
  print 'analyses: ', topology.analyses
  print 'runs: ', topology.runs
  print 'category: ', topology.category
  print 'constraint: ', topology.constraints
  print 'decay: ', topology.decay
  print 'short decay: ', topology.shortdecay
  print 'parametrizations of third mass: ', topology.massParametrizations
  print 'intermediate particles:', topology.intermediateParticles
  print 'mother particle:', topology.motherParticle
  print
  print
  
  ## to get a specified set of Result-objects
  resultSet = browser.expResultSet("SUS13008","T6ttWW" )
  print 'Print out this result set:'
  print str(resultSet)
  print "members of this set:", resultSet.members
  print "results encapsulated in this set:", resultSet.results
  print "observed upper limits:", resultSet.hasUpperLimitDicts()
  print "expected upper limits:", resultSet.hasUpperLimitDicts(expected = True)
  print 'Result is checked: ', resultSet.checked
  
  # to get one selected exclusion line:
  
  line = resultSet.exclusionLine(condition = 'M2/M0', value = 2.0)
  print 'One selected exclusion line: ', line
  print 'Default line: ', resultSet.exclusionLine()
  

  
  
if __name__ == '__main__':
  main()  
