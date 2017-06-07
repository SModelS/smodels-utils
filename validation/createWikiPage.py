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
from smodels.tools.physicsUnits import TeV, fb
from smodels.tools.smodelsLogging import setLogLevel
setLogLevel("debug" )

try:
    import commands as C
except ImportError:
    import subprocess as C

class WikiPageCreator:
    ### starting to write a creator class
    def __init__ ( self, ugly ):
        self.ugly = ugly ## ugly mode
        self.databasePath = os.path.join(os.path.expanduser("~"),\
                "git/smodels-database/")
        self.db = Database( self.databasePath )
        self.localdir = "/var/www/validationWiki"
        self.localdir = "/var/www/validation_v111"
        self.urldir = self.localdir.replace ( "/var/www", "" )
        self.fName = 'wikiFile.txt'
        if self.ugly:
            self.fName = 'uglyFile.txt'
        self.file = open ( self.fName, 'w' )
        self.nlines = 0
        print ( "\n" )
        print ( 'MAKE SURE THE VALIDATION PLOTS IN '
                'smodels.hephy.at:%s ARE UPDATED\n' % self.localdir  )
        self.true_lines = []
        self.false_lines = []
        self.none_lines = []

    def run ( self ):
        self.writeHeader ()
        self.writeTableList ( )
        self.createTables ()
        self.close()

    def getDatasetName ( self, txname ):
        dataset = txname.path [ : txname.path.rfind("/") ]
        dataset = dataset [ dataset.rfind("/")+1 : ]
        dataset = dataset.replace ( "HighPt", "!HighPt" )
        dataset = dataset.replace ( "GtGrid", "!GtGrid" )
        return dataset

    def close ( self ):
        print ( 'Done.\n' )
        print ( '--->Copy and paste the content to the SModelS wiki page.\n')
        print ( '--->(if xsel is installed, you should find the content in your clipboard.)\n' )
        self.file.write ( "\n" )
        self.file.close()
        C.getoutput ( "cat %s | xsel -i" % self.fName )

    def writeHeader ( self ):
        print ( 'Creating wiki file (%s)....' % self.fName )
        if self.ugly:
            self.file.write ( 
"""#acl +DeveloperGroup:read,write,revert -All:write,read Default
<<LockedPage()>>""" )
        self.file.write( """
= Validation plots for all analyses used by SModelS-v1.1.1 =

This page lists validation plots for all analyses and topologies available in the SMS results database of v1.1, including superseded and Fastlim results. The list has been created from the database version 1.1.1 and Fastlim tarball shipped separately.

The validation procedure for upper limit maps used here is explained in [[http://arxiv.org/abs/arXiv:1312.4175|arXiv:1312.4175]][[http://link.springer.com/article/10.1140/epjc/s10052-014-2868-5|EPJC May 2014, 74:2868]], section 4. For validating efficiency maps, a very similar procedure is followed. For every input point, the best signal region is chosen. Experimental upper limit and theoretical prediction are compared for that signal region.
""")
    def writeTableHeader ( self, tpe ):
        fields = [ "Result", "Txname", "L [1/fb]", "Validation plots", "comment" ]
        if self.ugly:
            fields.insert ( 3, "Validated?" )
        ret=""
        for i in fields:
            ret=ret +  ( "||<#EEEEEE:> '''%s''' " % i )
        ret = ret + ( "||\n" )
        self.true_lines.append ( ret )

    def writeTableList ( self ):
        self.file.write ( "== Individual tables ==\n" )
        self.file.write ( "(Results with validated='n/a' are ignored. For efficiency maps, we count the best data set only.)\n\n" )

        for sqrts in [ 13, 8 ]:
            run=1
            if sqrts == 13: run = 2
            self.file.write ( "\n=== Run %d - %d TeV ===\n" % ( run, sqrts ) )
            for exp in [ "ATLAS", "CMS" ]:
                for tpe in [ "upper limits", "efficiency maps" ]:
                    expResList = self.getExpList ( sqrts, exp, tpe )
                    stpe = tpe.replace ( " ", "" )

                    nres = 0
                    nexpres = 0
                    for expRes in expResList:
                        hasTn=False
                        txns = []
                        for tn in expRes.getTxNames():
                            validated = tn.getInfo('validated')
                            tname = tn.txName
                            #if "2015-0" in expRes.globalInfo.id:
                            #    print ( "tname=",tname,"validated=",validated,"path=",tn.path, "tpe=",tpe )
                            #    print ( "   `- info",tn._infoObj.dataType ) 
                            if validated in [ "n/a" ]: continue
                            if "efficiency" in tpe:
                                dataset = self.getDatasetName ( tn )
                                if dataset == "data": continue
                            if tname in txns:
                                continue
                            txns.append ( tname )
                            hasTn=True
                            nres += 1
                        if hasTn: nexpres += 1

                    if nres > 0:
                        self.file.write ( " * [[#%s%s%d|%s %s]]: %d analyses, %d results\n" % \
                                      ( exp, stpe, sqrts, exp, tpe, nexpres, nres ) )

    def writeExpRes( self, expRes, tpe ):
        valDir = os.path.join(expRes.path,'validation').replace("\n","")
        if not os.path.isdir(valDir): return
        id = expRes.getValuesFor('id')[0]
        txnames = expRes.getTxNames()
        ltxn = 0 ## len(txnames)
        txns_discussed=[]
        for txname in txnames:
            validated = txname.getInfo('validated')
            if validated == "n/a": continue
            txn = txname.txName
            if txn in txns_discussed:
                continue
            txns_discussed.append ( txn )
            ltxn += 1
        line = "||<|%i> [[%s|%s]]" %( ltxn, expRes.getValuesFor('url')[0], id )
        hadTxname = False
        txns_discussed=[]
        for txname in txnames:
            txn = txname.txName
            if txn in txns_discussed:
                continue
            txns_discussed.append ( txn )
            validated = txname.getInfo('validated')
            if validated == "n/a": continue
            color=""
            if validated is True: color = "#32CD32"
            elif validated in [ None, "n/a" ]: color = "#778899"
            elif validated in [ False, "tbd" ]: color = "#FF1100"
            txnbrs = txn
            #if txnbrs == "TChiChipmStauL":
            #    txnbrs = "TChi-ChipmStauL"
            sval = str(validated).strip()
            if "efficiency" in tpe:
                dataset = self.getDatasetName ( txname )
                if dataset == "data":
                    continue
                # print ( "txname=", dataset )
                # line += "|| %s " % dataset
            hadTxname = True
            line += '||[[SmsDictionary#%s|%s]]' % ( txn, txnbrs )
            line += "||%.1f" % txname.globalInfo.lumi.asNumber(1/fb)
            if self.ugly:
                line += '||<style="color: %s;"> %s ' % ( color, sval )
            line += "||"
            hasFig=False
            dirPath =  os.path.join( self.urldir, 
                                     valDir.replace( self.databasePath,""))
            files = glob.glob(valDir+"/"+txname.txName+"_*_pretty.pdf")
            if self.ugly:
                tmp = glob.glob(valDir+"/"+txname.txName+"_*.pdf")
                files = []
                for i in tmp:
                    if not "pretty" in i:
                        files.append ( i )
            for fig in files:
                pngname = fig.replace(".pdf",".png" )
                if not os.path.exists ( pngname ):
                    cmd = "convert -trim %s %s" % ( fig, pngname )
                #    C.getoutput ( cmd )
                # figName = fig.replace(valDir+"/","")
                figName = pngname.replace(valDir+"/","").replace ( \
                            self.databasePath, "" )
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
        if not hadTxname: return
        if "XXX#778899" in line: self.none_lines.append(line)
        # if "#778899" in line: self.none_lines.append(line)
        elif "#FF0000" in line: self.false_lines.append(line)
        else: self.true_lines.append(line)
        self.nlines += 1

    def writeExperimentType ( self, sqrts, exp, tpe, expResList ):
        stype=tpe.replace(" ","")
        nres = 0
        nexpRes = 0
        for expRes in expResList:
            txnames=[]
            for tn in expRes.getTxNames():
                name = tn.txName
                if name in txnames:
                    continue
                validated = tn.getInfo('validated')
                if validated in [ "n/a" ]: continue
                if "efficiency" in tpe:
                    dataset = self.getDatasetName ( tn )
                    if dataset == "data": continue
                txnames.append ( name )
                nres += 1
            if len(txnames)>0: nexpRes+=1
        if nres == 0:
                return
        self.true_lines.append ( "== %s %s, %d TeV: %d analyses, %d results total ==\n" % (exp,tpe,sqrts, nexpRes, nres ) )
        self.true_lines.append ( "<<Anchor(%s%s%d)>>\n\n" % ( exp,stype,sqrts ) )
        self.writeTableHeader ( tpe )
        expResList.sort()
        for expRes in expResList:
            # print ( "id=",expRes.globalInfo.id )
            self.writeExpRes ( expRes, tpe )


    def getExpList ( self, sqrts, exp, tpe ):
        dsids= [ None ]
        if tpe == "efficiency maps":
            dsids = [ 'all' ]
        T="upperLimit"
        if "efficiency" in tpe: T="efficiencyMap"
        tmpList = self.db.getExpResults( dataTypes=[ T ], 
                                         useNonValidated=self.ugly )
        expResList = []
        for i in tmpList:
            if not exp in i.globalInfo.id: continue
            xsqrts=int ( i.globalInfo.sqrts.asNumber(TeV) )
            if xsqrts != sqrts: continue
            expResList.append ( i )
        return expResList

    def createTables ( self ):
        for sqrts in [ 13, 8 ]:
            for exp in [ "ATLAS", "CMS" ]:
                for tpe in [ "upper limits", "efficiency maps" ]:
                    expResList = self.getExpList ( sqrts, exp, tpe )
                    self.writeExperimentType ( sqrts, exp, tpe, expResList )

        #Copy/update the database plots and generate the wiki table
        for line in self.none_lines + self.true_lines + self.false_lines: 
            self.file.write(line)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser( description= "creates validation wiki pages." )
    ap.add_argument('-u', '--ugly', help='ugly mode', action='store_true')
    args = ap.parse_args()
    creator = WikiPageCreator( args.ugly )
    creator.run()
