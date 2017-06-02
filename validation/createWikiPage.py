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
try:
    import commands as C
except ImportError:
    import subprocess as C


localdir = "/var/www/validationWiki"
localdir = "/var/www/walten/validation/newFormat"
urldir = localdir.replace ( "/var/www", "" )

print ( "\n" )

print ( 'MAKE SURE THE VALIDATION PLOTS IN smodels.hephy.at:%s ARE UPDATED\n' % \
        localdir  )

fName = 'wikiFile.txt'

print ( 'Creating wiki file (%s)....' % fName )
wFile = open( fName,'w')
#Write header:
"""
wFile.write("= Database Validation =\n\
To list the validation plots and the status of validation for each result.\n\
The color coding for the plots is the following:\n\
  * Green: allowed points\n\
  * Red: excluded points\n\
  * Orange: \'\'allowed points if the theoretical prediction is lowered by 20%\'\'\n\
  * Dark Green: \'\'excluded points if the theoretical prediction is increased by 20%\'\'\n\
\n\n\
||<#EEEEEE:> '''Result''' ||<#EEEEEE:> '''Txname''' ||\
<#EEEEEE:> '''Validated?''' ||<#EEEEEE:> '''Validation Plots'''\
 ||<#EEEEEE:> '''comment''' ||\n")
"""
wFile.write( \
"""= Validation plots for all analyses used by SModelS-v1.1.1 =

This page lists validation plots for all analyses and topologies available in the SMS results database of v1.1, including superseded and Fastlim results. The list has been created from the database version 1.1.1 and Fastlim tarball shipped separately.

The validation procedure for upper limit maps used here is explained in [[http://arxiv.org/abs/arXiv:1312.4175|arXiv:1312.4175]][[http://link.springer.com/article/10.1140/epjc/s10052-014-2868-5|EPJC May 2014, 74:2868]], section 4. For validating efficiency maps, a very similar procedure is followed. For every input point, the best signal region is chosen. Experimental upper limit and theoretical prediction is compared for that signal region in order to draw conclusion.

Individual tables: ATLAS upper limits validation, ATLAS efficiency maps validation, CMS upper limits validation, CMS efficiency maps validation.
||<#EEEEEE:> '''Result''' ||<#EEEEEE:> '''Txname''' ||\
<#EEEEEE:> '''Validated?''' ||<#EEEEEE:> '''Validation Plots'''\
 ||<#EEEEEE:> '''comment''' ||
""" )


#Set the address of the database folder
databasePath = os.path.join(os.path.expanduser("~"),"git/smodels-database/")
database = Database(databasePath, progressbar=True )
nlines = 0
#Load list of experimental results (DOES NOT INCLUDE efficiencies for now)
expResList = database.getExpResults(datasetIDs=[None])

#Copy/update the database plots and generate the wiki table
true_lines = []
false_lines = []
none_lines = []

expResList.sort()

for expRes in expResList:
    valDir = os.path.join(expRes.path,'validation').replace("\n","")
    if not os.path.isdir(valDir): continue
    else:
        txnames = expRes.getTxNames()
        line = "||<|%i> [[%s|%s]]" %(len(txnames),\
                expRes.getValuesFor('url')[0],expRes.getValuesFor('id')[0] )
        for txname in txnames:
            validated = txname.getInfo('validated')
            color=""
            if validated is True: color = "#32CD32"
            elif validated is None: color = "#778899"
            elif validated is False: color = "#FF0000"
            txn = txname.txName
            txnbrs = txn
            if txnbrs == "TChiChipmStauL":
                txnbrs = "TChi-ChipmStauL"
            line += "||[[SmsDictionary#%s|%s]]||<style=\"color: %s;\"> %s ||" \
                %(txn,txnbrs,color,str(validated))
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
                line += "{{%s||width=300}}" % figC
                #line += "{{http://smodels.hephy.at"+figPath+\
                #        "||width=300}}"
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
                line += "  ||\n" #In case there are no comments
        if "#778899" in line: none_lines.append(line)
        elif "#FF0000" in line: false_lines.append(line)
        else: true_lines.append(line)
        nlines += 1
#         if nlines > 2: break


for line in none_lines: wFile.write(line)
for line in true_lines: wFile.write(line)
for line in false_lines: wFile.write(line)


print ( 'Done.\n' )
print ( '--->Copy and paste the content to the SModelS wiki page.\n')
print ( '--->(if xsel is installed, you should find the content in your clipboard.)\n' )

C.getoutput ( "cat %s | xsel -i" % fName )

wFile.close()
