#!/usr/bin/env python

"""
.. module:: createWikiPage.py
   :synopsis: create the wiki page listing the validation plots

"""

#Import basic functions (this file must be run under the installation folder)
import sys,os,glob
import tempfile
sys.path.insert(0,"../../smodels")
from smodels.experiment.databaseObjects import Database



print '\n\nMAKE SURE THE VALIDATION PLOTS IN smodels.hephy.at:/var/www/validationWiki\
 ARE UPDATED\n'

print 'Creating wiki file (wikiFile.txt)....'
wFile = open('wikiFile.txt','w')
#Write header:
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


#Set the address of the database folder
databasePath = os.path.join(os.path.expanduser("~"),"smodels-database/")
database = Database(databasePath)
nlines = 0
#Load list of experimental results (DOES NOT INCLUDE efficiencies for now)
expResList = database.getExpResults(datasetIDs=[None])

#Copy/update the database plots and generate the wiki table
for expRes in expResList:
    valDir = os.path.join(expRes.path,'validation').replace("\n","")
    if not os.path.isdir(valDir): continue
    else:
        txnames = expRes.getTxNames()
        line = "||<|%i> [[%s|%s]]" %(len(txnames),\
                expRes.getValuesFor('url'),expRes.getValuesFor('id'))
        for txname in txnames:
            validated = txname.getInfo('validated')
            if validated is True: color = "#32CD32"
            elif validated is None: color = "#778899"
            elif validated is False: color = "#FF0000"
            line += "|| %s ||<style=\"color: %s;\"> %s ||" %(txname.txname,color,str(validated))
            for fig in glob.glob(valDir+"/"+txname.txname+"_*.pdf"):
                figName = fig.replace(valDir+"/","")                
                dirPath =  os.path.join('/validationWiki/',valDir.replace(databasePath,""))
                figPath = dirPath+"/"+figName
                line += "[[http://smodels.hephy.at"+figPath+\
                        "|"+figName+"]]<<BR>>"            
            if not "attachment" in line:  #In case there are no plots
                line += "  ||"
            else:
                line = line[:line.rfind("<<BR>>")] + "||"
            if os.path.isfile(valDir+"/"+txname.txname+".comment"):
                commentPath = dirPath+"/"+txname.txname+".comment"      
                line += "[[http://smodels.hephy.at"+commentPath+\
                        "|"+txname.txname+".comment"+"]] ||\n"
            else:
                line += "  ||\n" #In case there are no comments
        wFile.write(line)
        nlines += 1
#         if nlines > 2: break
print 'Done.\n --->Copy and paste the content to the SModelS wiki page.'            

wFile.close()