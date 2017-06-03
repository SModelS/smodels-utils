#!/usr/bin/env python

"""
.. module:: createWikiPage.py
   :synopsis: create the wiki page listing the validation plots

"""

from __future__ import print_function
#Import basic functions (this file must be run under the installation folder)
import sys,os,glob
import tempfile
sys.path.insert(0,"../../smodels")
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import TeV

try:
    import commands as C
except ImportError:
    import subprocess as C

def writeHeader ( wFile ):
    #Write header:
    wFile.write ( """#acl +DeveloperGroup:read,write,revert -All:write,read Default
<<LockedPage()>>""" )
    wFile.write( """
= Validation plots for all analyses used by SModelS-v1.1.1 =

This page lists validation plots for all analyses and topologies available in the SMS results database of v1.1, including superseded and Fastlim results. The list has been created from the database version 1.1.1 and Fastlim tarball shipped separately.

The validation procedure for upper limit maps used here is explained in [[http://arxiv.org/abs/arXiv:1312.4175|arXiv:1312.4175]][[http://link.springer.com/article/10.1140/epjc/s10052-014-2868-5|EPJC May 2014, 74:2868]], section 4. For validating efficiency maps, a very similar procedure is followed. For every input point, the best signal region is chosen. Experimental upper limit and theoretical prediction is compared for that signal region in order to draw conclusion.
 
Individual tables: [[#ATLASupperlimits13|ATLAS upper limits 13TeV]], [[#ATLASefficiencymaps13|ATLAS efficiency maps 13TeV]], [[#CMSupperlimits8|CMS upper limits 13TeV]], [[#CMSefficiencymaps8|CMS efficiency maps 13TeV]].
[[#ATLASupperlimits8|ATLAS upper limits 8TeV]], [[#ATLASefficiencymaps8|ATLAS efficiency maps 8TeV]], [[#CMSupperlimits8|CMS upper limits 8TeV]], [[#CMSefficiencymaps8|CMS efficiency maps 8TeV]].
""")

def writeTableHeader ( true_lines ):
    fields = [ "Result", "Txname", "Validated?", "Validation plots", "comment" ]
    ret=""
    for i in fields:
        ret=ret +  ( "||<#EEEEEE:> '''%s''' " % i )
    ret = ret + ( "||\n" )
    true_lines.append ( ret )
    # wFile.write ( "||<#EEEEEE:> '''Result''' ||<#EEEEEE:> '''Txname''' ||<#EEEEEE:> '''Validated?''' ||<#EEEEEE:> '''Validation Plots''' ||<#EEEEEE:> '''comment''' ||\n" )

def writeExpRes( expRes, nlines, true_lines, false_lines, databasePath, urldir ):
    valDir = os.path.join(expRes.path,'validation').replace("\n","")
    if not os.path.isdir(valDir): return
    else:
        id = expRes.getValuesFor('id')[0]
        txnames = expRes.getTxNames()
        line = "||<|%i> [[%s|%s]]" %(len(txnames),\
                expRes.getValuesFor('url')[0], id )
        for txname in txnames:
            validated = txname.getInfo('validated')
            color=""
            if validated is True: color = "#32CD32"
            elif validated in [ None, "n/a" ]: color = "#778899"
            elif validated in [ False, "tbd" ]: color = "#FF1100"
            txn = txname.txName
            txnbrs = txn
            #if txnbrs == "TChiChipmStauL":
            #    txnbrs = "TChi-ChipmStauL"
            sval = str(validated).strip()
            line += '||[[SmsDictionary#%s|%s]]||<style="color: %s;"> %s ||' \
                % (txn, txnbrs, color, sval)
            hasFig=False
            for fig in glob.glob(valDir+"/"+txname.txName+"_*_pretty.pdf"):
                pngname = fig.replace(".pdf",".png" )
                if not os.path.exists ( pngname ):
                    cmd = "convert -crop 600x420+250+10 %s %s" % ( fig, pngname )
                    C.getoutput ( cmd )
                # figName = fig.replace(valDir+"/","")
                figName = pngname.replace(valDir+"/","").replace ( databasePath, "" )
                dirPath =  os.path.join( urldir, valDir.replace(databasePath,""))
                figPath = dirPath+"/"+figName
                # print ( "figPath=",figPath, "txname=", txname.txName )
                #line += "[[http://smodels.hephy.at"+figPath+\
                #        "|"+figName+"]]<<BR>>"
                figC = "http://smodels.hephy.at"+figPath
                line += "[[%s|{{%s||width=200}}]]" % ( figC, figC )
                #line += "{{http://smodels.hephy.at"+figPath+\
                #        "||width=300}}"
                line += "<<BR>>"
                hasFig=True
            if hasFig:
                line = line[:-6] ## remove last BR
            if not "attachment" in line:  #In case there are no plots
                line += "  ||"
            else:
                line = line[:line.rfind("<<BR>>")] + "||"
            if os.path.isfile(valDir+"/"+txname.txName+".comment"):
                commentPath = dirPath+"/"+txname.txName+".comment"
                line += "[[http://smodels.hephy.at"+commentPath+\
                        "|comment"+"]] ||\n"
                #        "|"+txname.txName+".comment"+"]] ||\n"
            else:
                line += " ||\n" #In case there are no comments
        if "XXX#778899" in line: none_lines.append(line)
        # if "#778899" in line: none_lines.append(line)
        elif "#FF0000" in line: false_lines.append(line)
        else: true_lines.append(line)
        nlines += 1
#         if nlines > 2: break

def writeExperimentType ( sqrts, exp, tpe, expResList, wFile, nlines, true_lines, false_lines, databasePath, urldir ):
    print ( "\n\nexp",exp )
    stype=tpe.replace(" ","")
    true_lines.append ( "\n<<Anchor(%s%s%d)>>\n" % ( exp,stype,sqrts ) )
    true_lines.append ( "== %s %s, %d TeV: %d results ==\n" % (exp,tpe,sqrts, len(expResList)) )
    writeTableHeader ( true_lines )
    expResList.sort()
    for expRes in expResList:
        # print ( "id=",expRes.globalInfo.id )
        writeExpRes ( expRes, nlines, true_lines, false_lines, databasePath, urldir )


def main():
    localdir = "/var/www/validationWiki"
    localdir = "/var/www/walten/validation/newFormat"
    urldir = localdir.replace ( "/var/www", "" )
    print ( "\n" )
    print ( 'MAKE SURE THE VALIDATION PLOTS IN smodels.hephy.at:%s ARE UPDATED\n' % \
            localdir  )

    true_lines = []
    false_lines = []
    none_lines = []

    fName = 'wikiFile.txt'

    print ( 'Creating wiki file (%s)....' % fName )
    wFile = open( fName,'w')
    writeHeader ( wFile )

    #Set the address of the database folder
    databasePath = os.path.join(os.path.expanduser("~"),"git/smodels-database/")
    database = Database(databasePath, progressbar=True )
    nlines = 0
        
    for sqrts in [ 13, 8 ]:
        for exp in [ "ATLAS", "CMS" ]:
            for tpe in [ "upper limits", "efficiency maps" ]:
                dsids= [ None ]
                if tpe == "efficiency maps":
                    dsids = [ 'all' ]
                tmpList = database.getExpResults(datasetIDs=dsids )
                # tpe = "upper limits"
                #Load list of experimental results (DOES NOT INCLUDE efficiencies for now)
                expResList = []
                for i in tmpList:
                    xsqrts=int ( i.globalInfo.sqrts.asNumber(TeV) )
                    # print ( sqrts )
                    if exp in i.globalInfo.id and xsqrts == sqrts:
                        expResList.append ( i )
                writeExperimentType ( sqrts, exp, tpe, expResList, wFile, nlines, true_lines, false_lines, databasePath, urldir )

    #Copy/update the database plots and generate the wiki table
    for line in none_lines + true_lines + false_lines: wFile.write(line)

    print ( 'Done.\n' )
    print ( '--->Copy and paste the content to the SModelS wiki page.\n')
    print ( '--->(if xsel is installed, you should find the content in your clipboard.)\n' )

    C.getoutput ( "cat %s | xsel -i" % fName )
    wFile.close()

if __name__ == "__main__":
    main()
