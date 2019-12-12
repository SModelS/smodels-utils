#!/usr/bin/env python3

"""
.. module:: createWikiPage.py
   :synopsis: create the wiki page listing the validation plots, like
              https://smodels.github.io/docs/Validation

"""

from __future__ import print_function
#Import basic functions (this file must be run under the installation folder)
import sys,os,glob,time
import tempfile
sys.path.insert(0,"../../smodels")
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import TeV, fb
from smodels.tools.smodelsLogging import setLogLevel, logger
import subprocess
setLogLevel("debug" )

## TGQ12 should be possible
import smodels.experiment.datasetObj
smodels.experiment.datasetObj._complainAboutOverlappingConstraints = False

try:
    import commands as C
except ImportError:
    import subprocess as C

class WikiPageCreator:
    ### starting to write a creator class
    def __init__ ( self, ugly, database, add_version, private, force_upload,
                   comparison_database, ignore_superseded, ignore ):
        self.ugly = ugly ## ugly mode
        self.databasePath = database.replace ( "~", os.path.expanduser("~") )
        self.db = Database( self.databasePath )
        self.comparison_dbPath = comparison_database
        self.ignore_superseded = ignore_superseded
        self.ignore_validated = ignore
        if ugly: ## in ugly mode we always ignore validated, and superseded
            self.ignore_validated = True
            self.ignore_validated = True
        self.comparison_db = None
        if self.comparison_dbPath:
            self.comparison_db = Database ( self.comparison_dbPath )
        self.force_upload = force_upload
        self.dotlessv = ""
        if add_version:
            self.dotlessv = self.db.databaseVersion.replace(".","" )
        self.localdir = "../../smodels.github.io/validation/%s" %self.db.databaseVersion.replace(".","" )
        has_uploaded = False
        if not os.path.exists ( self.localdir ) and self.force_upload:
            print ( "%s does not exist. will try to create it." % self.localdir )
            cmd = "mkdir %s" % self.localdir
            a= C.getoutput ( cmd )
            print ( "%s: %s" % ( cmd, a ) )
        if not os.path.exists ( self.localdir ) and self.force_upload:
            print ( "Creating %s" % self.localdir )
            cmd = "mkdir %s" % self.localdir
            subprocess.getoutput ( cmd )
        if os.path.exists ( self.localdir) and (not "version" in os.listdir( self.localdir )) and self.force_upload:
            print ( "Copying database from %s to %s." % (self.databasePath, self.localdir )  )
            cmd = "rsync -a --prune-empty-dirs --exclude \\*.pdf --exclude \\*.pcl --exclude \\*.root --exclude \\*.py --exclude \\*.txt --exclude \\*.bib --exclude \\*orig\\* --exclude \\*data\\* --exclude \\*.sh --exclude README\\*  -r %s/* %s" % ( self.databasePath, self.localdir )
            a= C.getoutput ( cmd )
            print ( "%s: %s" % ( cmd, a ) )
            has_uploaded = True
        if self.force_upload and not has_uploaded:
            print ( "Copying database from %s to %s." % (self.databasePath, self.localdir )  )
            # cmd = "cp -r %s/* %s" % ( self.databasePath, self.localdir )
            cmd = "rsync -a --prune-empty-dirs --exclude \\*.pdf --exclude \\*.pcl --exclude \\*.root --exclude \\*.py --exclude \\*.txt --exclude \\*.bib --exclude \\*orig\\* --exclude \\*data\\* --exclude \\*.sh --exclude README\\*  -r %s/* %s" % ( self.databasePath, self.localdir )
            a= C.getoutput ( cmd )
            print ( "%s: %s" % ( cmd, a ) )
            has_uploaded = True
        else:
            print ( "Database seems already copied to %s. Good." % self.localdir )
        # self.urldir = self.localdir.replace ( "/var/www", "" )
        self.urldir = self.localdir.replace ( "../../smodels.github.io", "" )
        self.fName = 'Validation%s' % self.dotlessv
        if self.ugly:
            self.fName = 'ValidationUgly%s' % self.dotlessv
        self.file = open ( self.fName, 'w' )
        self.nlines = 0
        print ( )
        #if not has_uploaded:
        #    print ( 'MAKE SURE THE VALIDATION PLOTS IN %s ARE UPDATED\n' % self.localdir  )
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
        self.file.write ( "\nThis page was created %s\n" % time.asctime() )
        self.file.close()
        cmd = "mv %s ../../smodels.github.io/docs/%s.md" % ( self.fName, self.fName )
        print ( cmd )
        C.getoutput ( cmd )

    def writeHeader ( self ):
        print ( 'Creating wiki file (%s)....' % self.fName )
        whatIsIncluded = "Superseded and Fastlim results are included"
        if self.ignore_superseded:
            whatIsIncluded = "Fastlim results are listed; superseded results have been skipped"
        self.file.write( """
# Validation plots for SModelS-v%s 

This page lists validation plots for all analyses and topologies available in
the SMS results database that can be validated against official results.
%s. The list has been created from the
database version %s, including the Fastlim tarball that is shipped separately.
There is also a [list of all analyses](ListOfAnalyses%s), and
a list of [all SMS topologies](SmsDictionary%s).

The validation procedure for upper limit maps used here is explained in [arXiv:1312.4175](http://arxiv.org/abs/1312.4175),  [EPJC May 2014, 74:2868](http://link.springer.com/article/10.1140/epjc/s10052-014-2868-5), section 4. For validating efficiency maps, a very similar procedure is followed. For every input point, the best signal region is chosen. If a covariance matrix has been published, we present the combined limit of all signal regions. The experimental upper limits are compared with the theoretical predictions for that signal region.

""" % ( self.db.databaseVersion, whatIsIncluded, self.db.databaseVersion, 
        self.dotlessv, self.dotlessv ) )
        if self.ugly:
            self.file.write ( "\nTo [official validation plots](Validation%s)\n\n" % self.db.databaseVersion.replace(".","") )

    def writeTableHeader ( self, tpe ):
        fields = [ "Result", "Txname", "L [1/fb]", "Validation plots", "comment" ]
        if self.ugly:
            fields.insert ( 3, "Validated?" )
        ret=""
        lengths = []
        for i in fields:
            #ret=ret +  ( "||<#EEEEEE:> '''%s''' " % i )
            ret=ret +  ( "| **%s** " % i )
            lengths.append ( len(i)+6 )
        ret = ret + ( "|\n" )
        self.true_lines.append ( ret )
        ret=""
        for l in lengths:
            ret=ret+"|"+"-"*l
        ret=ret + ( "|\n" )
        self.true_lines.append ( ret )

    def writeTableList ( self ):
        self.file.write ( "## Individual tables\n" )

        for sqrts in [ 13, 8 ]:
            run=1
            if sqrts == 13: run = 2
            self.file.write ( "\n### Run %d - %d TeV\n" % ( run, sqrts ) )
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
                            if not self.ignore_validated and validated in [ "n/a" ]: 
                                continue
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
                        self.file.write ( " * [%s %s](#%s%s%d): %d analyses, %d results\n" % \
                                      ( exp, tpe, exp, stpe, sqrts, nexpres, nres ) )

    def writeExpRes( self, expRes, tpe ):
        valDir = os.path.join(expRes.path,'validation').replace("\n","")
        if not os.path.isdir(valDir): return
        id = expRes.globalInfo.id
        txnames = expRes.getTxNames()
        ltxn = 0 ## len(txnames)
        txns_discussed=[]
        for txname in txnames:
            validated = txname.getInfo('validated')
            if not self.ignore_validated and validated != True: 
                continue
            # if validated == "n/a": continue
            txn = txname.txName
            if txn in txns_discussed:
                continue
            txns_discussed.append ( txn )
            ltxn += 1
        #line = "||<|%i> [[%s|%s]]" %( ltxn, expRes.getValuesFor('url')[0], id )
        line = "| [%s](%s)" %( id, expRes.getValuesFor('url')[0] )
        hadTxname = False
        txns_discussed=[]
        nfigs = 0
        for txname in txnames:
            txn = txname.txName
            if txn in txns_discussed:
                continue
            txns_discussed.append ( txn )
            validated = txname.getInfo('validated')
            if not self.ignore_validated and validated != True: 
                continue
            #if validated == "n/a": continue
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
            if hadTxname: ## not the first txname for this expres?
                line += "| "
            hadTxname = True
            line += '| [%s](SmsDictionary%s#%s)' % ( txnbrs, self.dotlessv, txn )
            line += "| %.1f" % txname.globalInfo.lumi.asNumber(1/fb)
            if self.ugly:
                line += '| %s ' % ( sval )
                #line += '||<style="color: %s;"> %s ' % ( color, sval )
            line += "|"
            #line += "||"
            hasFig=False
            ## print ( "databasePath=",self.databasePath )
            vDir = valDir.replace ( self.databasePath,"")
            altpath = self.databasePath.replace ( "/home", "/nfsdata" )
            vDir = vDir.replace ( altpath, "" )
            if vDir[0]=="/":
                vDir = vDir[1:]
            dirPath =  os.path.join( self.urldir, vDir )
            files = glob.glob(valDir+"/"+txname.txName+"_*_pretty.png")
            if self.ugly:
                tmp = glob.glob(valDir+"/"+txname.txName+"_*.png")
                files = []
                for i in tmp:
                    if not "pretty" in i:
                        files.append ( i )
            for fig in files:
                pngname = fig.replace(".pdf",".png" )
                figName = pngname.replace(valDir+"/","").replace ( \
                            self.databasePath, "" )
                figPath = dirPath+"/"+figName
                figC = "https://smodels.github.io"+figPath
                line += '<a href="%s"><img src="%s" /></a>' % ( figC, figC )
                line += "<BR>"
                hasFig=True
                nfigs += 1
            if hasFig:
                line = line[:-4] ## remove last BR
            if not "attachment" in line:  #In case there are no plots
                line += "  |"
            else:
                line = line[:line.rfind("<<BR>>")] + "|"

            ## add comments
            if self.isNewAnaID ( id, txname.txName, tpe ):
                line += ' <img src="https://smodels.github.io/pics/new.png" /> in %s! ' % ( self.db.databaseVersion )
            ## from comments file
            cFile = valDir+"/"+txname.txName+".comment"
            if os.path.isfile(cFile):
                commentPath = dirPath+"/"+txname.txName+".comment"
                txtPath = commentPath.replace(".comment", ".txt" )
                githubRepo = "../../smodels.github.io"
                mvCmd = "mv %s/%s %s/%s" % ( githubRepo, commentPath, githubRepo, txtPath )
                subprocess.getoutput ( mvCmd )
                line += "[comment](https://smodels.github.io"+txtPath+\
                        ") |\n"
                #f = open ( cFile, "r" )
                #line += ", ". join ( f.readlines() ).replace("\n","")
                #f.close()
                #line += " |\n" # close it
            else:
                line += " |\n" #In case there are no comments
                #line += " ||\n" #In case there are no comments
        if not hadTxname: return
        if "XXX#778899" in line: self.none_lines.append(line)
        elif "#FF0000" in line: self.false_lines.append(line)
        else: self.true_lines.append(line)
        self.nlines += 1
        logger.debug ( "add %s with %d figs" % ( id, nfigs ) )

    def isNewAnaID ( self, id, txname, tpe ):
        """ is analysis id <id> new? """
        if self.comparison_db == None:
            # no comparison database given. So nothing is new.
            return False
        if not hasattr ( self, "OldAnaIds" ):
            expRs = self.comparison_db.getExpResults( useSuperseded = True, useNonValidated = self.ignore_validated )
            anaIds = [ x.globalInfo.id for x in expRs ]
            self.OldAnaIds = set ( anaIds )
            self.topos = {}
            for r in expRs:
                anaId = r.globalInfo.id
                if not anaId in self.topos.keys():
                    self.topos[anaId]=[]
                topos = r.getTxNames()
                Type = "-ul"
                if len(r.datasets) > 1 or r.datasets[0].dataInfo.dataId != None:
                    Type = "-eff"
                for t in topos:
                    name = t.txName+Type 
                    self.topos[anaId].append ( name )
            ## print ( "the old analysis ids are", self.OldAnaIds )
        if not id in self.OldAnaIds: ## whole ana is new?
            return True
        myType = "-ul"
        if "eff" in tpe:
            myType = "-eff"
        ## FIXME need to check also topo
        txtpe = txname+myType
        if not txtpe in self.topos[id]:
            ## txname is new
            return True
        return False

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
                if not self.ignore_validated and validated != True: 
                    continue
                # if validated in [ "n/a" ]: continue
                if "efficiency" in tpe:
                    dataset = self.getDatasetName ( tn )
                    if dataset == "data": continue
                txnames.append ( name )
                nres += 1
            if len(txnames)>0: nexpRes+=1
        if nres == 0:
                return
        self.true_lines.append ( '\n\n<a name="%s%s%d"></a>\n' % ( exp,stype,sqrts ) )
        self.true_lines.append ( "## %s %s, %d TeV: %d analyses, %d results total\n\n" % (exp,tpe,sqrts, nexpRes, nres ) )
        self.writeTableHeader ( tpe )
        expResList.sort()
        for expRes in expResList:
            # print ( "id=",expRes.globalInfo.id )
            if self.ignore_superseded and hasattr(expRes.globalInfo,'supersededBy'):
                logger.debug ( "skip superseded %s" % expRes.globalInfo.id )
                continue
            self.writeExpRes ( expRes, tpe )


    def getExpList ( self, sqrts, exp, tpe ):
        dsids= [ None ]
        if tpe == "efficiency maps":
            dsids = [ 'all' ]
        T="upperLimit"
        if "efficiency" in tpe: T="efficiencyMap"
        tmpList = self.db.getExpResults( dataTypes=[ T ], 
                         useNonValidated=self.ignore_validated, 
                         useSuperseded=True )
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
                    print ( "Writing %s TeV, %s, %s" % ( sqrts, exp, tpe ) )
                    expResList = self.getExpList ( sqrts, exp, tpe )
                    self.writeExperimentType ( sqrts, exp, tpe, expResList )

        #Copy/update the database plots and generate the wiki table
        for line in self.none_lines + self.true_lines + self.false_lines: 
            self.file.write(line)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser( description= "creates validation wiki pages,"\
                " see e.g. http://smodels.github.io/docs/Validation" )
    ap.add_argument('-u', '--ugly', help='ugly mode (gives more private info,'\
                ' plots everything, uses ugly plots)', action='store_true')
    ap.add_argument('-p', '--private', help='private mode',
                    action='store_true')
    ap.add_argument('-f', '--force_upload', 
                    help='force upload of pics to ../../smodels.github.io.',
                    action='store_true')
    ap.add_argument('-a', '--add_version', help='add version labels in links', 
                    action='store_true')
    ap.add_argument('-s', '--ignore_superseded', help='ignore superseded results', 
                    action='store_true')
    ap.add_argument ( '-i', '--ignore', help='ignore the validation flags of analysis (i.e. also add non-validated results)', action='store_true' )
    ap.add_argument('-v', '--verbose',
            help='specifying the level of verbosity (error, warning, info, debug)'\
                 ' [info]', default = 'info', type = str)
    ap.add_argument('-c', '--comparison_database',
            help='specify database to compare to (to flag "new analyses") [default: ""]',
            default = '', type = str )
    ap.add_argument('-d', '--database',
            help='specify the location of the database [../../smodels-database]',
            default = '../../smodels-database', type = str )
    args = ap.parse_args()
    setLogLevel ( args.verbose )
    creator = WikiPageCreator( args.ugly, args.database, args.add_version, 
                               args.private, args.force_upload,
                               args.comparison_database, args.ignore_superseded,
                               args.ignore )
    creator.run()
