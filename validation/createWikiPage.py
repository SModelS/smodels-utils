#!/usr/bin/env python3

"""
.. module:: createWikiPage.py
   :synopsis: create the wiki page listing the validation plots, like
              https://smodels.github.io/docs/Validation

"""

from __future__ import print_function
#Import basic functions (this file must be run under the installation folder)
import sys,os,glob,time,copy
import tempfile
sys.path.insert(0,"../../smodels")
from smodels.experiment.databaseObj import Database
from smodels.base.physicsUnits import TeV, fb
from smodels.base.smodelsLogging import setLogLevel, logger
from smodels_utils.helper.databaseManipulations import filterSupersededFromList
import subprocess
setLogLevel("debug" )

## TGQ12 should be possible
import smodels.experiment.datasetObj
smodels.experiment.datasetObj._complainAboutOverlappingConstraints = False

try:
    import commands as C
except ImportError:
    import subprocess as C

def sortingFunc ( x : str ) -> str:
    x = str(x).replace("SUSY","")
    x = x.replace("EXOT","")
    x = x.replace("EXO","")
    x = x.replace("SUS","")
    x = x.replace("PAS","")
    x = x.replace("CONF","")
    return x

class WikiPageCreator:
    ### starting to write a creator class
    def __init__ ( self, ugly, database, add_version, private, force_upload,
                   comparison_database, ignore_superseded, ignore, moveFile,
                   include_fastlim, add_old ):
        """
        :param ugly: ugly mode, produces the ValidationUgly pages with more info
        :param include_fastlim: include fastlim results
        :param ignore_superseded: if True, then filter out superseded results
        :param ignore: if true, then add also validated results
               (i.e. ignore the validation field)
        pparam add_old: if plots exist in validation/old/ folder, add them.
        """
        self.ugly = ugly ## ugly mode
        self.databasePath = database.replace ( "~", os.path.expanduser("~") )
        self.db = Database( self.databasePath )
        self.comparison_dbPath = comparison_database.replace ( "~", os.path.expanduser("~") )
        self.ignore_superseded = ignore_superseded
        self.include_fastlim = include_fastlim
        self.ignore_validated = ignore
        self.moveFile = moveFile
        self.add_old = add_old
        if ugly: ## in ugly mode we always ignore validated, and superseded
            self.ignore_validated = True
            self.ignore_superseded = False
        self.comparison_db = None
        if self.comparison_dbPath:
            self.comparison_db = Database ( self.comparison_dbPath )
        self.force_upload = force_upload
        self.dotlessv = ""
        if add_version:
            self.dotlessv = self.db.databaseVersion.replace(".","" )
        self.localdir = f"../../smodels.github.io/validation/{self.db.databaseVersion.replace('.','' )}"
        has_uploaded = False
        if not os.path.exists ( self.localdir ) and self.force_upload:
            print ( f"{self.localdir} does not exist. will try to create it." )
            cmd = f"mkdir {self.localdir}"
            a= C.getoutput ( cmd )
            print ( f"{cmd}: {a}" )
        if not os.path.exists ( self.localdir ) and self.force_upload:
            print ( f"Creating {self.localdir}" )
            cmd = f"mkdir {self.localdir}"
            subprocess.getoutput ( cmd )
        cmd = f"rsync -a --prune-empty-dirs --exclude \\*.tgz --exclude \\*/__pycache__ --exclude \\*.pdf --exclude \\*.pcl --exclude \\*.root --exclude \\*.py --exclude \\*.txt --exclude \\*.bib --exclude \\*\/orig\/\\* --exclude \\*data\\* --exclude \\*.sh --exclude README\\*  -r {self.databasePath}/* {self.localdir}"
        if os.path.exists ( self.localdir) and (not "version" in os.listdir( self.localdir )) and self.force_upload:
            print ( f"[createWikiPage] Copying database from {self.databasePath} to {self.localdir}." )
            a= C.getoutput ( cmd )
            print ( f"[createWikiPage] {cmd}: {a}" )
            has_uploaded = True
        if self.force_upload and not has_uploaded:
            print ( f"[createWikiPage] Copying database from {self.databasePath} to {self.localdir}." )
            a= C.getoutput ( cmd )
            print ( f"[createWikiPage] {cmd}: {a}" )
            has_uploaded = True
        else:
            print ( f"Database seems already copied to {self.localdir}. Good." )
        # self.urldir = self.localdir.replace ( "/var/www", "" )
        self.urldir = self.localdir.replace ( "../../smodels.github.io", "" )
        self.fName = f'Validation{self.dotlessv}'
        if self.ugly:
            self.fName = f'ValidationUgly{self.dotlessv}'
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
        self.file.write ( f"\nThis page was created {time.asctime()}\n" )
        self.file.close()
        if self.moveFile:
            cmd = f"mv {self.fName} ../../smodels.github.io/docs/{self.fName}.md" )
            print ( "[createWikiPage]",cmd )
            C.getoutput ( cmd )

    def writeHeader ( self ):
        print ( f'[createWikiPage] Creating wiki file ({self.fName})....' )
        whatIsIncluded = "Superseded and Fastlim results are included"
        if not self.include_fastlim:
            whatIsIncluded = "Superseded results are listed; fastlim results are not"
        if self.ignore_superseded:
            whatIsIncluded = "Fastlim results are listed; superseded results have been skipped"
            if not self.include_fastlim:
                whatIsIncluded = "Neither superseded nor fastlim results are listed in this table"
        self.file.write( """
# Validation plots for SModelS-v%s

This page lists validation plots for all analyses and topologies available in
the SMS results database that can be validated against official results.
%s. The list has been created from the
database version %s, including the Fastlim tarball that is shipped separately.
There is also a [list of all analyses](ListOfAnalyses%s), and
a list of [all SMS topologies](SmsDictionary%s).

The validation procedure for upper limit maps used here is explained in [arXiv:1312.4175](http://arxiv.org/abs/1312.4175),  [EPJC May 2014, 74:2868](http://link.springer.com/article/10.1140/epjc/s10052-014-2868-5), section 4. For validating efficiency maps, a very similar procedure is followed. For every input point, the best signal region is chosen. If a covariance matrix has been published, we present the combined limit of all signal regions. The experimental upper limits are compared with the theoretical predictions for that signal region.

Note that the SModelS validation plots show on- and off-shell regions
separately (e.g., T2tt and T2ttoff) while the exclusion lines given by ATLAS or
CMS are for on- and off-shell at once.

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
            ret=ret +  ( f"| **{i}** " )
            lengths.append ( len(i)+6 )
        ret = ret + ( "|\n" )
        self.true_lines.append ( ret )
        ret=""
        for l in lengths:
            ret=ret+"|"+"-"*l
        ret=ret + ( "|\n" )
        self.true_lines.append ( ret )

    def getNumber ( self, nr ):
        """ just format an integral number nicely """
        if nr == 0:
            return "no"
        return "%d" % nr

    def writeTableList ( self ):
        self.file.write ( "## Individual tables\n" )

        for sqrts in [ 13, 8 ]:
            run=1
            if sqrts == 13: run = 2
            self.file.write ( "\n### Run %d - %d TeV\n" % ( run, sqrts ) )
            nResults = { "ATLAS": set(), "CMS": set() }
            for exp in [ "ATLAS", "CMS" ]:
                #for tpe in [ "upper limits", "efficiency maps" ]:
                for tpe in [ "efficiency maps", "upper limits" ]:
                    expResList = self.getExpList ( sqrts, exp, tpe )
                    for expRes in expResList:
                        Id = expRes.globalInfo.id
                        Id = Id.replace("-agg","")
                        Id = Id.replace("-eff","")
                        nResults[exp].add(Id)
            print ( "[createWikiPage] results at %d TeV: %d CMS, %d ATLAS" % ( sqrts, len(nResults["CMS"]), len(nResults["ATLAS"]) ))
            for exp in [ "ATLAS", "CMS" ]:
                # for tpe in [ "upper limits", "efficiency maps" ]:
                for tpe in [ "efficiency maps", "upper limits" ]:
                    print ( f"[createWikiPage] now {exp} {tpe}" )
                    expResList = self.getExpList ( sqrts, exp, tpe )
                    stpe = tpe.replace ( " ", "" )

                    nres, nnewres, nexpres, nnewexpres = set(), set(), set(), set()
                    for expRes in expResList:
                        hasTn,hasNewTn=False,False
                        txns, newtxns = [], []
                        for tn in expRes.getTxNames():
                            validated = tn.validated
                            tname = tn.txName
                            if not self.ignore_validated and validated in [ "n/a" ]:
                                continue
                            Id = expRes.globalInfo.id
                            Idnoagg = Id.replace("-agg","")
                            isNew = self.isNewAnaID ( Id, tn.txName, tpe,
                                                      validated )
                            hasChanged = self.anaHasChanged ( expRes.globalInfo.id, tn.txName, tpe )
                            if "efficiency" in tpe:
                                dataset = self.getDatasetName ( tn )
                                if dataset == "data": continue
                            if tname in txns:
                                continue
                            txns.append ( tname )
                            hasTn=True
                            nres.add ( Idnoagg )
                            if isNew or hasChanged:
                                hasNewTn = True
                                nnewres.add ( Idnoagg )
                                newtxns.append ( tname )
                        if hasTn: nexpres.add ( Idnoagg )
                        if hasNewTn: nnewexpres.add ( Idnoagg )

                    if len(nres) > 0:
                        sanalyses = "%d analyses (%s new)" % \
                                     ( len(nexpres), self.getNumber(len(nnewexpres)) )
                        sresults = "%d results (%s new)" % \
                                     ( len(nres), self.getNumber(len(nnewres)) )
                        self.file.write ( " * [%s %s](#%s%s%d): %s, %s\n" % \
                                      ( exp, tpe, exp, stpe, sqrts, sanalyses, sresults ) )

    def isOneDimensional( self, txname ):
        """ simple method that tells us if its a 1d map. In this case, we dont
            do "pretty", we use ugly plots for pretty. """
        # import IPython; IPython.embed ( colors = "neutral" ); sys.exit()
        if hasattr ( txname, "axes" ):
            r = not ( "y" in str(txname.axes) )
            return r
        if not hasattr ( txname, "axesMap" ):
            logger.error ( "we have neither an axes field nor an axesMap field?" )
            sys.exit(-1)
        maps = str ( txname.axesMap )
        if "y" in maps:
            return False
        return True


    def writeExpRes( self, expRes, tpe ):
        """ write the experimental result expRes
        :param tpe: data type (ul or em)
        """
        valDir = os.path.join(expRes.path,'validation').replace("\n","")
        if not os.path.isdir(valDir): return
        id = expRes.globalInfo.id
        # print ( "[createWikiPage] `- adding %s" % id, flush=True, end=" " )
        txnames = expRes.getTxNames()
        ltxn = 0 ## len(txnames)
        if id in [ "ATLAS-SUSY-2016-07" ]:
            for txn in txnames:
                if False: # txn.txName == "TGQ":
                    txn2 = copy.deepcopy ( txn )
                    txn2.txName = "TGQ12"
                    txnames.append ( txn2 )
                #print ( id, txn.txName )
        if id in [ "ATLAS-SUSY-2016-24" ]:
            for txn in txnames:
                if txn.txName == "TSelSel":
                    txn2 = copy.deepcopy ( txn )
                    txn2.txName = "TSlepSlep"
                    txnames.append ( txn2 )
                #print ( id, txn.txName )
        txnames.sort()
        txns_discussed=set()
        for txname in txnames:
            validated = txname.validated
            if not self.ignore_validated and validated != True:
                continue
            # if validated == "n/a": continue
            txn = txname.txName
            if txn in txns_discussed:
                continue
            txns_discussed.add ( txn )
            ltxn += 1
        # line = "| [%s](%s)" %( id, expRes.getValuesFor('url')[0] )
        line = ""
        hadTxname = False
        nfigs = 0
        # url = expRes.getValuesFor('url')[0]
        url = expRes.globalInfo.url
        if ";" in url:
            url = url.split(";")[0]
        # print ( "%d txnames: " % len(txns_discussed), flush=True, end="" )
        txns_discussed=set()
        for txname in txnames:
            txn = txname.txName
            if txn in txns_discussed:
                continue
            #if hadTxname:
            #    print ( ",", end="" )
            # print ( txn, flush=True, end= "" )
            txns_discussed.add ( txn )
            validated = txname.validated
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
            #if hadTxname: ## not the first txname for this expres?
            #    line += "| "
            line += "| [%s](%s) " %( id, url )

            hadTxname = True
            line += '| [%s](SmsDictionary%s#%s)' % ( txnbrs, self.dotlessv, txn )
            line += "| %.1f" % txname.globalInfo.lumi.asNumber(1/fb)
            if self.ugly:
                line += '| %s ' % ( sval )
                #line += '||<style="color: %s;"> %s ' % ( color, sval )
            line += "|"
            #line += "||"
            hasFig=False
            vDir = valDir.replace ( self.databasePath,"")
            altpath = self.databasePath.replace ( "/home", "/nfsdata" )
            vDir = vDir.replace ( altpath, "" )
            if "smodels-database" in vDir:
                vDir = vDir [ vDir.find("smodels-database")+17: ]
            if vDir[0]=="/":
                vDir = vDir[1:]
            dirPath =  os.path.join( self.urldir, vDir )
            files = glob.glob(valDir+"/"+txname.txName+"_*_pretty.png")
            # print ( "@@@", txname, " ugly?", self.ugly, "files", files, "is1d", self.isOneDimensional ( txname ) )
            if self.add_old:
                files += glob.glob(valDir+"/old/"+txname.txName+"_*_pretty.png")
            if self.ugly or self.isOneDimensional ( txname ):
                tmp = glob.glob(valDir+"/"+txname.txName+"_*.png")
                if self.add_old:
                    tmp += glob.glob(valDir+"/old/"+txname.txName+"_*.png")
                files = []
                for i in tmp:
                    if not "pretty" in i:
                        files.append ( i )
            files.sort( key = lambda x: str(x.replace("old/","") ) )
            t0=time.time()-159000000
            valDir = valDir.replace("/media/linux/walten/git/smodels-database","" )
            for fig in files:
                pngname = fig.replace(".pdf",".png" )
                figName = pngname.replace(valDir+"/","").replace ( \
                            self.databasePath, "" )
                figPath = dirPath+"/"+figName
                figC = "https://smodels.github.io"+figPath
                line += f'<a href="{figC}"><img src="{figC}?{t0}" /></a>'
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
            if self.isNewAnaID ( id, txname.txName, tpe, validated ):
                line += f' <img src="https://smodels.github.io/pics/new.png" /> in {self.db.databaseVersion}! '
            else:
                hasChanged = self.anaHasChanged ( id, txname.txName, tpe )
                if hasChanged == "cov":
                    line += f' <img src="https://smodels.github.io/pics/updated.png" /> added covariances in {self.db.databaseVersion}! '
                if hasChanged == "eUL":
                    line += f' <img src="https://smodels.github.io/pics/updated.png" /> added expected UL in {self.db.databaseVersion}! '
            line += f"<br><font color='grey'>source: {self.describeSource ( txname )}</font><br>"
            if txname.validated not in [ "True", True ]:
                font, endfont = "", ""
                if txname.validated in [ "False", False ]:
                    font, endfont = "<font color='red'>", "</font>"
                line += "%svalidated: %s%s<br>" % (font, txname.validated, endfont )
            ## from comments file
            cFile = valDir+"/"+txname.txName+".comment"
            if os.path.isfile(cFile):
                commentPath = dirPath+"/"+txname.txName+".comment"
                txtPath = commentPath.replace(".comment", ".txt" )
                githubRepo = "../../smodels.github.io"
                mvCmd = "cp %s/%s %s/%s" % ( githubRepo, commentPath, githubRepo, txtPath )
                subprocess.getoutput ( mvCmd )
                line += "[comment](https://smodels.github.io"+txtPath+ ")"
            srplot = valDir + "/bestSR_%s.png" % ( txname.txName )
            if os.path.isfile( srplot ) and self.ugly:
                srPath = dirPath+"/bestSR_"+txname.txName+".png"
                githubRepo = "../../smodels.github.io"
                mvCmd = "cp %s/%s %s/%s" % ( githubRepo, srPath, githubRepo, srPath )
                subprocess.getoutput ( mvCmd )
                addl = " <br>[SR plot](https://smodels.github.io"+srPath+ ")"
                line += addl
            line += " |\n" # End the line
        # print ( )
        if not hadTxname: return
        if "XXX#778899" in line: self.none_lines.append(line)
        elif "#FF0000" in line: self.false_lines.append(line)
        else: self.true_lines.append(line)
        self.nlines += 1
        logger.debug ( "add %s with %d figs" % ( id, nfigs ) )

    def describeSource ( self, txname ):
        """ describe the source of the data
        :param txname: txname object
        """
        if not hasattr ( txname, "source" ):
            return "unknown"
        source = txname.source.lower()
        if "cms" in source:
            return "CMS"
        if "atlas" in source:
            return "ATLAS"
        if "smodels" in source:
            return "SModelS"
        if "ma5" in source:
            return "MA5"
        if "recast" in source:
            return txname.source
        print ( f"[createWikiPage] there is an unknown2 in {source}" )
        return "unknown2"

    def anaHasChanged ( self, id, txname, tpe ):
        """ has analysis id <id> changed?
        :param id: analysis id, e.g. ATLAS-SUSY-2013-02  (str)
        :param txname: topology name, e.g. T1 (str)
        :param tpe: type of result, e.g. "upper limits" (str)
        """
        if self.comparison_db == None:
            # no comparison database given. So nothing is new.
            return False
        dataTypes = []
        if tpe in [ "upper limits" ]:
            dataTypes.append ( "upperLimit" )
        if tpe in [ "efficiency maps" ]:
            dataTypes.append ( "efficiencyMap" )
        newR = self.db.getExpResults( analysisIDs = [ id ],
                    txnames = [ txname ], dataTypes = dataTypes,
                    useNonValidated = self.ignore_validated )
        if self.ignore_superseded:
            newR = filterSupersededFromList ( newR )
        oldR = self.comparison_db.getExpResults( analysisIDs = [ id ],
                    txnames = [ txname ], dataTypes = dataTypes,
                    useNonValidated = self.ignore_validated )
        if len(newR) == 0 or len(oldR) == 0:
            return False
        oldDS = oldR[0].datasets
        newDS = newR[0].datasets
        if newR[0].hasCovarianceMatrix() and not oldR[0].hasCovarianceMatrix():
            return "cov"
        for od,nd in zip ( oldDS, newDS ):
            for otxn,ntxn in zip ( od.txnameList, nd.txnameList ):
                if otxn.hasLikelihood() != ntxn.hasLikelihood():
                    return "eUL"
        return False

    def compileOldAnaIds ( self ):
        """ compile the list of analysis ids in the comparison database,
        i.e. create self.OldAnaIds, and self.topos
        """
        expRs = self.comparison_db.getExpResults( useNonValidated = self.ignore_validated )
        anaIds = [ x.globalInfo.id for x in expRs ]
        self.OldAnaIds = set ( anaIds )
        self.topos = {}
        for r in expRs:
            anaId = r.globalInfo.id
            if not anaId in self.topos.keys():
                self.topos[anaId]=[]
            topos = r.getTxNames()
            topos.sort()
            Type = "-ul"
            if len(r.datasets) > 1 or r.datasets[0].dataInfo.dataId != None:
                Type = "-eff"
            for t in topos:
                name = t.txName+Type
                self.topos[anaId].append ( name )
        # print ( "the old analysis ids are", self.OldAnaIds )
        if self.comparison_db.databaseVersion == "1.2.3":
            print ( "[createWikiPage] adding ATLAS-SUSY-2016-24:TSlepSlep-eff" )
            self.topos["ATLAS-SUSY-2016-24"].append ( 'TSlepSlep-eff' )


    def isNewAnaID ( self, id, txname, tpe, validated ):
        """ is analysis id <id> new?
        :param id: analysis id, e.g. ATLAS-SUSY-2013-02 (str)
        :param txname: topology name, e.g. T1 (str)
        :param tpe: type of result, e.g. "upper limits" (str)
        :param validated: is it validated? for if it is not, it won't
                          be marked as new
        """
        if validated == False:
            return False
        if self.comparison_db == None:
            # no comparison database given. So nothing is new.
            return False
        if not hasattr ( self, "OldAnaIds" ):
            self.compileOldAnaIds()
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
        """ write the table for a specific sqrts, experiment, data Type
        """
        stype=tpe.replace(" ","")
        nres = 0
        nexpRes = 0
        expResList.sort( key = sortingFunc, reverse = True ) # start with most recent!
        for expRes in expResList:
            txnames=[]
            tnamess = expRes.getTxNames()
            tnamess.sort()
            for tn in tnamess:
                name = tn.txName
                if name in txnames:
                    continue
                validated = tn.validated
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
        self.true_lines.append ( f'\n\n<a name="{exp}{stype}{sqrts}"></a>\n' )
        self.true_lines.append ( f"## {exp} {tpe}, {sqrts} TeV: {nexpRes} analyses, {nres} results total\n\n" )
        expResList.sort( key = sortingFunc, reverse=True ) # start with most recent
        self.writeTableHeader ( tpe )
        for expRes in expResList:
            # print ( "id=",expRes.globalInfo.id )
            if self.ignore_superseded and hasattr(expRes.globalInfo,'supersededBy'):
                logger.debug ( f"skip superseded {expRes.globalInfo.id}" )
                continue
            self.writeExpRes ( expRes, tpe )

    def getExpList ( self, sqrts, exp, tpe ):
        """ get the list of experimental results for given sqrts and
            data type and experiment
        :param exp: experiment, i.e. "CMS" or "ATLAS"
        """
        dsids= [ None ]
        if tpe == "efficiency maps":
            dsids = [ 'all' ]
        T="upperLimit"
        if "efficiency" in tpe: T="efficiencyMap"
        tmpList = self.db.getExpResults( dataTypes=[ T ],
                         useNonValidated=self.ignore_validated )
        if self.ignore_superseded:
            tmpList = filterSupersededFromList ( tmpList )
        expResList = []
        for i in tmpList:
            if not exp in i.globalInfo.id: continue
            xsqrts=int ( i.globalInfo.sqrts.asNumber(TeV) )
            if xsqrts != sqrts: continue
            if not self.include_fastlim and hasattr ( i.globalInfo, "contact" ) and \
                "fastlim" in i.globalInfo.contact.lower():
                    # we do not include fastlim, the result has a contact field,
                    # and "fastlim" is mentioned there: skip it
                    continue
            expResList.append ( i )
        return expResList

    def createTables ( self ):
        print ( "[createWikiPage] create tables" )
        for sqrts in [ 13, 8 ]:
            for exp in [ "ATLAS", "CMS" ]:
                for tpe in [ "efficiency maps", "upper limits" ]:
                # for tpe in [ "upper limits", "efficiency maps" ]:
                    expResList = self.getExpList ( sqrts, exp, tpe )
                    if self.ignore_superseded:
                        expResList = filterSupersededFromList ( expResList )
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
    ap.add_argument('-M', '--dontmove', help='dont move file at the end',
                    action='store_true')
    ap.add_argument('-f', '--force_upload',
                    help='force upload of pics to ../../smodels.github.io.',
                    action='store_true')
    ap.add_argument('-F', '--include_fastlim', help='include fastlim results',
                    action='store_true')
    ap.add_argument('-a', '--add_version', help='add version labels in links',
                    action='store_true')
    ap.add_argument('-o', '--add_old', help='add old plots if they exist',
                    action='store_true')
    ap.add_argument('-s', '--ignore_superseded', help='ignore superseded results',
                    action='store_true')
    ap.add_argument ( '-i', '--ignore', help='ignore the validation flags of analysis (i.e. also add non-validated results)', action='store_true' )
    ap.add_argument('-v', '--verbose',
            help='specifying the level of verbosity (error, warning, info, debug)'\
                 ' [info]', default = 'info', type = str)
    ap.add_argument('-c', '--comparison_database',
            help='specify database to compare to (to flag "new analyses") [default: "~/git/smodels-database-release"]',
            default = '~/git/smodels-database-release', type = str )
    ap.add_argument('-d', '--database',
            help='specify the location of the database [~/git/smodels-database]',
            default = '~/git/smodels-database', type = str )
    args = ap.parse_args()
    if not os.path.exists(os.path.expanduser(args.database)):
        print ( f"[createWikiPage] cannot find {args.database}" )
        sys.exit()
    if not os.path.exists(os.path.expanduser(args.comparison_database)):
        print ( f"[createWikiPage] couldnt find comparison database {args.comparison_database}, set to ''" )
        args.comparison_database = ""
    setLogLevel ( args.verbose )
    creator = WikiPageCreator( args.ugly, args.database, args.add_version,
                               args.private, args.force_upload,
                               args.comparison_database, args.ignore_superseded,
                               args.ignore, not args.dontmove, args.include_fastlim, 
                               args.add_old )
    creator.run()
