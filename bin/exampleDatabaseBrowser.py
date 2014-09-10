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
  print 'Analysis-object: ', analysis
  # use this object
  print '\nAnalysis is: ', analysis.name
  print 'PAS: ', analysis.pas
  print 'luminosity: ', analysis.lumi
  print 'Experiment: ', analysis.experiment
  print 'comment: ', analysis.comment
  print 'axes: ', analysis.axes
  print
  print

  # to get specified Topology-object
  topology = browser.expTopology('TChiChipmSlepStau')
  print 'Topology-object: ', topology
  print 'name: ', topology.name
  print 'analyses: ', topology.analyses
  print 'runs: ', topology.runs
  print 'category: ', topology.category
  print 'constraint: ', topology.constraints
  print 'decay: ', topology.decay
  print 'short decay: ', topology.shortdecay
  print 'third masses: ', topology.thirdMasses
  print 'intermediate particles:', topology.intermediateParticles
  print 'mother particle:', topology.motherParticle
  print
  print
  
  ## to get a specified set of Result-objects
  resultSet = browser.expResultSet("SUS13008","T6ttWW" )
  print 'Set of results is: ', resultSet
  print "members of this set:", resultSet.members
  print "results encapsulated in this set:", resultSet.results
  print "which observed upper limits:", resultSet.hasUpperLimitDicts()
  print "which expected upper limits:", resultSet.hasUpperLimitDicts(expected = True)
  print 'Result is checked: ', resultSet.checked
  
  # to get one selected exclusion line:
  
  line = resultSet.exclusionLine(condition = 'M2/M0', value = 2.0)
  print 'One selected exclusion line: ', line
  print 'Default line: ', resultSet.exclusionLine()
  

  
  
if __name__ == '__main__':
  main()  
