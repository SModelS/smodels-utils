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
  
  #set the path to the database (default - "/afs/hephy.at/user/w/walten/public/sms/") if the path does not exist or if there is no valid sms-database, databaseBrowser will be stoped
  # databaseBrowser.base = '../../smodels-database/'
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
  print 
  print

  # to get specified Topology-object
  topology = browser.expTopology('T1')
  print 'Topology-object: ', topology
  print 'name: ', topology.name
  print 'analyses: ', topology.analyses
  print 'runs: ', topology.runs
  print 'category: ', topology.category
  print 'constraint: ', topology.constraints
  print 'decay: ', topology.decay
  print 
  print 
  
  ## to get a specified Result-object
  result = browser.expResult("SUS13006","TChiWZ" )
  print 'Result is: ', result
  ## use this object
  #print '\nResult is checked: ', result.checkedBy
  #print '\nGet all the exclusionlines: ', result.getExclusionLines()
  #print '\nSelect a specified exclusionline: ', \
  #result.selectExclusionLine(expected = True, sigma = 1)
  
  ## get Analysis belonging to this Pair:
  #analysis = result.analysis
  #print '\nNow we have an Analysis-object: ', analysis
  #print '\nFor this Pair the PAS is: ', analysis.pas
  #print ''
  
  
if __name__ == '__main__':
  main()  
