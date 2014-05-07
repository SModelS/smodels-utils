#!/usr/bin/python

""" This is a simple tool that I (WW) need to work out with the CMS susy group
what digitized results are not yet published """

import setPath
from smodels.experiment import smsResults, smsHelpers
from smodels.tools.physicsUnits import rmvunit
  
Fields= [ "analysis", "sqrts", "lumi", "topologies", "constraints" ]
NiceName= { "nick name": "nick name", "analysis": "analysis", "sqrts":"$\sqrt{s}$", "topologies": "topologies", "constraints":"constraints", "lumi": "lumi" }


def isATLAS ( analysis ):
  if analysis.find("ATLAS")==0: return True
  return False

def begintable ( File ):
  File.write ( "\\begin{table}\n" )
  flds="{"
  for i in range(len(Fields)):
    flds+="l|"
  flds=flds[:-1]
  flds+="}"
  File.write ( "\\begin{tabular}%s\n" % flds )
  for (ct,F) in enumerate(Fields):
    File.write ( "{\\bf %s} " % NiceName[F] )
    if ct<len(Fields)-1: File.write ( "&" )

  File.write ( "\\\\ \\hline \n" )


def header ( File ):
  File.write ( "\\documentclass[8pt]{article}\n" )
  File.write ( "\\usepackage{multirow}\n" )
  File.write ( "\\begin{document}\n" )
  File.write ( "\\thispagestyle{empty}\n" )
  begintable ( File )

def endtable ( File ):
  File.write ( "\\end{tabular}\n" )
  File.write ( "\\end{table}\n" )

def footer ( File ):
  endtable ( File )
  File.write ( "\\end{document}" )

def line ( File ):
  # going from ATLAS to CMS
  endtable ( File )
  File.write ( "\\newpage\n \\thispagestyle{empty}\n" )
  begintable ( File )

def compileTex ( Filename="database.tex" ):
  import os
  os.system ( "pdflatex database.tex" )
  os.system ( "convert database.pdf database.png" )

def pprint ( constr ):
  constr=constr.replace("'","")
  if len(constr)>40:
    constr=constr[:37]+"..."
  return constr

def printFirstTopo ( File, analysis, topo ):
  sqrts=int(rmvunit(smsResults.getSqrts ( analysis ),"TeV"))
  lumi=smsResults.getLumi ( analysis ).asNumber()
  constr=pprint ( smsResults.getConstraints ( analysis, topo ) )
  pas=smsResults.getPAS ( analysis )
  File.write ( "%s & %s & %s & %s & %s \\\\ \n" % ( pas, sqrts, lumi, topo, constr ) ) 

def printNextTopo ( File, analysis, topo ):
  constr=pprint ( smsResults.getConstraints ( analysis, topo ) )
  File.write ( " & & & %s & %s \\\\ \n" % ( topo, constr ) ) 

def printAnalysis ( File, analysis, topos ):
  first=True
  for topo in topos:
    constr=smsResults.getConstraints ( analysis, topo )
    if not constr or constr=="Not yet assigned": continue
    if first:
      printFirstTopo ( File, analysis, topo )
      first=False
    else:
      printNextTopo ( File, analysis, topo )

def run( ):
  results={}
  All=smsResults.getAllResults()
  for analysis in All:
    for topo in All[analysis]:
      # if not smsResults.isPublic ( analysis ): continue
      constr=smsResults.getConstraints ( analysis, topo )
      if not constr: continue
      sqrts=smsResults.getSqrts ( analysis )
      run=smsResults.getRun ( analysis )
      if not results.has_key ( analysis ): results[analysis]=[]
      results[analysis].append ( topo )

  keys=results.keys()
  keys.sort()
  print keys
  wasATLAS=True
  File=open("database.tex","w")
  header ( File )
  for analysis in keys:
    topos=results[analysis]
    if wasATLAS and not isATLAS ( analysis ):
      line( File )
      wasATLAS=False
    printAnalysis ( File, analysis, topos )
  footer ( File )
  File.close()
  compileTex()

run()
