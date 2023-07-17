#!/usr/bin/env python3

""" This is a simple tool that I (WW)need to work out with the CMS susy group
what digitized results are not yet published """

from __future__ import print_function

import sys
sys.path.append("../../smodels/")
from operator import attrgetter
from smodels.experiment.databaseObj import Database
from smodels.base.physicsUnits import TeV
  
Fields= [ "expResult", "sqrts", "lumi","type", "topologies", "constraints" ]
nextLineFields = ["", "", "", "", "topologies", "constraints"]
NiceName= { "nick name": "nick name", "expResult": "Experimental Result", "sqrts":"$\sqrt{s}$", "topologies": "topologies", "constraints":"constraints", "lumi": "lumi", "type" : "data type"}

Fields= [ "expResult", "sqrts", "lumi","type"]
nextLineFields = []
removeFastlim = True



def isATLAS(expResult):
    if expResult.find("ATLAS")==0: return True
    return False

def begintable(File):
    flds="{"
    for i in range(len(Fields)):
        flds+="c|"
    flds=flds[:-1]
    flds+="}"
    File.write("\\begin{longtable}%s\n" % flds)
    for (ct,F)in enumerate(Fields):
        File.write("{\\bf %s} " % NiceName[F])
        if ct<len(Fields)-1: File.write("&")

    File.write("\\\\ \\hline \n")


def header(File):
    File.write( "\\documentclass[8pt]{article}\n")
    File.write( "\\usepackage{multirow}\n")
    File.write( "\\usepackage{longtable}\n")
    File.write( "\\begin{document}\n")
    File.write( "\\thispagestyle{empty}\n")
    begintable( File)

def endtable( File):
    File.write( "\\end{longtable}\n")

def footer( File):
    endtable( File)
    File.write( "\\end{document}")

def line(File):
    # going from ATLAS to CMS
    endtable(File)
    File.write("\\newpage\n \\thispagestyle{empty}\n")
    begintable(File)

def compileTex(Filename="database.tex"):
    import os
    os.system("pdflatex database.tex")
    os.system("convert database.pdf database.png")

def pprint(constr):
    constr=constr.replace("'","")
    if len(constr)>40:
        constr=constr[:37]+"..."
    return constr

def printFirstTopo(File, expResult, txname):
    sqrts = int(expResult.globalInfo.sqrts.asNumber(TeV))
    lumi = expResult.globalInfo.lumi.asNumber()
    constr = pprint(txname.constraint)
    expId = expResult.globalInfo.id
    dataType = expResult.datasets[0].dataInfo.dataType
    infofields = {"expResult" : expId, "sqrts" : sqrts, "lumi" : lumi,"type" : dataType, 
			"topologies" : txname.txName, "constraints" : constr}
    writeStr = ""
    for i,f in enumerate(Fields):
        if f:
            writeStr += str(infofields[f])
        if i < len(Fields) - 1:
            writeStr += " &"
        else:
            writeStr += " \\\\ \n"
    File.write(writeStr)

def printNextTopo(File, expResult, txname):
    sqrts = int(expResult.globalInfo.sqrts.asNumber(TeV))
    lumi = expResult.globalInfo.lumi.asNumber()
    constr = pprint(txname.constraint)
    expId = expResult.globalInfo.id
    dataType = expResult.datasets[0].dataInfo.dataType
    infofields = {"expResult" : expId, "sqrts" : sqrts, "lumi" : lumi,"type" : dataType, 
			"topologies" : txname.txName, "constraints" : constr}
    writeStr = ""
    for i,f in enumerate(nextLineFields):
        if f:
            writeStr += str(infofields[f])
        if i < len(Fields) - 1:
            writeStr += " &"
        else:
            writeStr += " \\\\ \n"
    File.write(writeStr)

def printAnalysis(File,expResult,txnames):
    first=True
    printedTxnames = []
    for tx in sorted(txnames, key=lambda tx: tx.txName):
        if tx.txName in printedTxnames: continue
        constr = tx.constraint
        if not constr or constr=="Not yet assigned": continue
        if first:
            printFirstTopo(File,expResult,tx)
            first=False
            printedTxnames.append(tx.txName)
        else:
            printNextTopo(File, expResult,tx)
            printedTxnames.append(tx.txName)

def run():
    database = Database('../../smodels-database/')
    allResults = database.getExpResults(useSuperseded=True, useNonValidated=True)
    for expResult in allResults:
        expResult.dataType = expResult.datasets[0].dataInfo.dataType
    allResults = sorted(allResults, key = attrgetter('globalInfo.id','globalInfo.sqrts','dataType'))
    wasATLAS=True
    File=open("database.tex","w")
    header(File)
    for expResult in allResults:
        expId = expResult.globalInfo.id
        txnames = expResult.getTxNames()
        if hasattr(expResult.globalInfo,'contact'):
            if 'fastlim' in expResult.globalInfo.contact  and removeFastlim:
                print ( 'skipping fastlim result:',expId )
                continue

        if wasATLAS and not isATLAS(expId):
            line(File)
            wasATLAS=False
        printAnalysis(File,expResult,txnames)
    footer(File)
    File.close()
    compileTex()

run()
