#!/usr/bin/env python3

"""
.. module:: bibtexTools
        :synopsis: Collection of methods for bibtex.
                   Currently contains only a dictionary for getting the
                   bibtex names of analyses

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function

from smodels.tools.smodelsLogging import setLogLevel
import bibtexparser
import urllib, colorama, subprocess
import os, sys
from smodels.experiment.databaseObj import Database

if sys.version[0]=="2":
    reload(sys)
    sys.setdefaultencoding('utf8')

try:
    import commands
except ImportError:
    import subprocess as commands
try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

class BibtexWriter:
    cachedir = "../bibtexs/"
    unuseddir = f"{cachedir}unused/"

    def __init__ ( self, databasepath="./", verbose="info" ):
        self.verbose = verbose.lower()
        setLogLevel ( self.verbose )
        self.databasepath = databasepath
        self.npublications = 0
        self.nfailed = 0
        self.nsuperseded = 0
        self.not_found = 0
        self.success = 0
        self.nomatch = 0
        self.fastlim = 0
        self.stats = { "CMS":{}, "ATLAS":{} } ## stats
        self.specialcases = {
            "CMS-PAS-SUS-13-018": "https://cds.cern.ch/record/1693164",
            "CMS-PAS-SUS-13-023": "http://cds.cern.ch/record/2044441",
            "CMS-SUS-16-050": "http://cds.cern.ch/record/2291344",
            "ATLAS-CONF-2013-007": "http://cds.cern.ch/record/1522430",
            "ATLAS-CONF-2013-061": "http://cds.cern.ch/record/1557778",
            "ATLAS-CONF-2013-089": "http://cds.cern.ch/record/1595272",
        }
        self.g=open ( "log.txt", "w" )
        self.mkdirs()

    def mkdirs ( self ):
        """ make the directories """
        if not os.path.exists ( self.cachedir ):
            os.mkdir( self.cachedir  )
        if not os.path.exists ( self.unuseddir ):
            os.mkdir( self.unuseddir )

    def openHandles ( self ):
        """ open all file handles. """
        self.f=open ( "refs.bib", "w" )
        self.h=open ( "failed.txt", "w" )
        self.i=open ( "database.bib", "w" )

    def header ( self ):
        self.i.write ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n" )
        self.i.write ( "% References for the analyses included in this version of the database %\n" )
        self.i.write ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n" )
        self.i.write ( "\n" )

    def copy ( self ):
        """ copy the files to the database path. """
        if os.path.isdir ( self.databasepath ) and os.path.exists ( "database.bib" ) and os.path.exists ( "refs.bib" ) and os.stat ( "database.bib" ).st_size > 0 and os.stat ( "refs.bib" ).st_size > 0:
            self.log ( "Copying database.bib to %s" % self.databasepath )
            cmd = "cp ./database.bib %s" % self.databasepath
            o = commands.getoutput ( cmd )
            if len(o) != 0:
                self.log ( "cp: %s" % o )
            else:
                self.log ( "Success!" )
        else:
            if not os.path.isdir ( self.databasepath ):
                print ( "Databasepath %s is not a directory. Wont copy." % self.databasepath )
            else:
                self.log ( "Did not copy ./database.bib and ./refs.bib. Something seems wrong. Maybe you did not generate them?" )


    def close ( self ):
        self.log ( "%d results in container." % len(self.res) )
        self.log ( "Summary: %d / %d successful." % \
                ( self.success, self.npublications ) )
        self.log ( " ... of which: %d superseded results" % self.nsuperseded )
        self.log ( "               %d not found" % self.not_found )
        self.log ( "               %d fastlim" % self.fastlim )
        self.log ( "               %d no match" % self.nomatch )
        self.log ( "failed: %d" % self.nfailed )
        self.g.close()
        self.h.close()
        self.createStatsFile()

    def bibtexFromCDS ( self, url, label=None ):
        """ get the bibtex entry from cds """
        fullurl =  url+"/export/hx"
        fullurl = fullurl.replace ( "?ln=en", "" )
        fullurl = fullurl.replace ( "?ln=de", "" )
        self.log ( " * fetching from CDS: %s" % fullurl )
        f=urlopen (fullurl)
        lines = f.readlines()
        f.close()
        ret = []
        hasBegin = False
        inAuthorList = False
        for line in lines:
            line=line.decode()
            if "=" in line:
                inAuthorList = False
            if "@techreport" in line or "@article" in line:
                hasBegin=True
            if not hasBegin or inAuthorList:
                continue
            if "</pre>" in line:
                hasBegin=False
                continue
            if "author" in line and "Sirunyan" in line:
                inAuthorList = True
                line = '      author        = "{CMS collaboration}",\n'
                ret.append ( line )
                continue
            ret.append ( line )
            if "@article" in line and label != None:
                ret.append ( '      label          = "%s",\n' % label )
            if "@techreport" in line and label != None:
                ret.append ( '      label          = "%s",\n' % label )
        return self.replaceUnicodes ( "".join ( ret ) )

    def replaceUnicodes ( self, source ):
        repls = { 8211:"--", 160:" ", 8722:"-", 8201:" ", 226:"-", 128:" ", 147:"-",
                  137: " " }
        for k,v in repls.items():
            try:
                source = source.replace ( chr(k), v )
            except: ## python2
                source = source.replace ( unichr(k), v )
        for ctr,letter in enumerate(source):
            o=ord(letter)
            if o>127:
                print ( "foreign letter %d: %s" % ( o, letter) )
                print ( "The context was: >>%s#%s<<" % ( source[ctr-20:ctr], source[ctr+1:ctr+20] ) )
                sys.exit()
        if self.verbose in [ "debug", "info" ]:
            print ( source )
        source=source.replace( "8TeV", "8 TeV" ).replace("Tev","TeV" )
        source=source.replace ( "fb-1", "fb$^{-1}$" )
        source=source.replace ( "AlphaT", "$\\alpha_{T}$" )
        return source

    def bibtexFromInspire ( self, url, label=None ):
        """ get the bibtex entry from an inspire record """
        self.log ( " * fetching from Inspire: %s" % url )
        ## hack for now, this solution wont work in the future
        self.warn ( "for now we are using the old.inspirehep.net hack. This wont work in the long run!" )
        url =  url.replace( "inspirehep.net", "old.inspirehep.net" )
        fullurl =  url+"/export/hx"
        # return fullurl
        f=urlopen (fullurl)
        lines = f.readlines()
        f.close()
        ret = []
        hasBegin = False
        for line in lines:
            line=line.decode()
            if "pagebodystripemiddle" in line:
                hasBegin=True
                continue
            if not hasBegin:
                continue
            if "</pre>" in line:
                hasBegin=False
                continue
            ret.append ( line )
            if "@article" in line and label != None:
                ret.append ( '      label          = "%s",\n' % label )
            if "@techreport" in line and label != None:
                ret.append ( '      label          = "%s",\n' % label )
        r =  str(self.replaceUnicodes ( "".join ( ret )  ))
        return r

    def fetchInspireUrl ( self, l, label ):
        """ from line in html page, extract the inspire url """
        self.log ( " * fetching Inspire url: %s" % label )
        pos1 = l.find ( "HREF=" )
        pos2 = l.find ( "<B>" )
        if pos1 > 0 and pos2 > pos1:
            return l[pos1+6:pos2-2]
        pos1 = l.find ( "href=" )
        pos2 = l.find ( "inSPIRE" )
        if pos1 > 0 and pos2 > pos1 and not "INSPIRE_ID" in l:
            ret=l[pos1+6:pos2-2]
            return ret
        return "fetchInspireUrl failed"

    def fetchPasUrl ( self, line ):
        pos1 = line.find( 'href="' )
        pos2 = line.find( ' target=' )
        if pos1 < 1 or pos2 < pos1:
            return "failed to find pas url"
        ret = line[pos1+6:pos2-1]
        self.log ( " * PasUrl: %s" % ret )
        return ret

    def fetchCDSUrl ( self, line, label ):
        self.log ( " * fetching CDS url: %s" % label )
        pos1 = line.find( 'href="' )
        pos2 = line.find( '">CDS' )
        if pos1 < 1 or pos2 < pos1:
            return "failed to find pas url"
        ret = line[pos1+6:pos2]
        self.log ( " * CDS url: %s" % ret )
        return ret

    def bibtexFromWikiUrl ( self, url, label=None ):
        """ get the bibtex entry from the atlas wiki """
        self.log ( " * fetching from wiki: %s" % url )
        try:
            f=urlopen ( url )
        except urllib.error.HTTPError as e:
            self.log( "   `- error %s, not fetching from wiki" % e )
            return None
        lines = f.readlines()
        f.close()
        lines = list ( map ( str, lines ) )

        ## first pass, aim for inspire
        for l in lines:
            if "nspire" in l:
                inspire = self.fetchInspireUrl ( l, label )
                # self.log ( "   `- fetching from inspire: %s" % inspire )
                if not "failed" in inspire:
                    return self.bibtexFromInspire ( inspire, label )

        ## second pass, try CDS and everything else
        for l in lines:
            if "preliminary results are superseded by the following paper" in l:
                self.log ( "    %s: superseded !!!!! " % label )
                self.h.write ( "%s is superseded." % label )
                self.nsuperseded += 1
                return None
            if "404 - Not found" in l:
                self.log ( "    %s is not found!" % label )
                #self.h.write ( "%s is not found!" % label )
                #self.not_found += 1
                return None
            if 'CDS record' in l:
                cds = self.fetchCDSUrl ( l, label )
                if not "failed" in cds:
                    try:
                        return self.bibtexFromCDS ( cds, label )
                    except Exception as e:
                        print ( "HTTPEerror when fetching %s/%s from CDS: %s" % \
                                ( cds, label, e ) )
            if 'target="_blank">' in l:
            # if 'target="_blank">Link to ' in l:
                pas = self.fetchPasUrl ( l )
                if not "failed" in pas:
                    return self.bibtexFromCDS ( pas, label )
            return None

    def log ( self, line ):
        if self.verbose in [ "debug", "info" ]:
            print ( line )
        self.g.write ( line + "\n" )

    def warn ( self, line ):
        print ( "%sWARN %s%s" % ( colorama.Fore.RED, line, colorama.Fore.RESET ) )
        self.g.write ( line + "\n" )

    def test( self ):
        print ( self.bibtexFromWikiUrl ( "http://cms-results.web.cern.ch/cms-results/public-results/publications/SUS-15-002/index.html", "CMS-SUS-15-002" ) )
        sys.exit()

    def searchOnCMSWiki ( self, Id ):
        """ search for the publication on the summary wiki page """
        return None

    def tryFetchFromCache ( self, Id ):
        """ there is a local file with the entry?
        convenient! we use it! """
        fname = "%s/%s.tex" % ( self.cachedir, Id )
        if not os.path.exists ( fname ):
            return False
        self.log ( "A backup file exists. We use it." )
        f=open( fname, "r" )
        txt=f.read()
        f.close()
        sqrts = self.getSqrts ( Id )
        coll = self.findCollaboration ( Id )
        self.stats[coll][Id] = { "cached": 1 }
        return txt

    def writeCache ( self, Id, bib ):
        """ write the cache entry for analysis id <Id>, bibtex text is <bib> """
        self.log ( "Now write cache file %s/%s.tex" % ( self.cachedir, Id ) )
        cachef = open ( "%s/%s.tex" % ( self.cachedir, Id ) , "w" )
        cachef.write ( str(bib) )
        cachef.write ( "\n" )
        cachef.close()

    def getSqrts ( self, Id ):
        """ given analysis id <Id>, determine sqrts """
        year = Id.replace("ATLAS-","").replace("CMS-","").replace("SUSY-","")
        year = year.replace("EXO-","").replace("SUS-","").replace("PAS-","")
        year = year.replace("CONF-","")
        p1 = year.find("-")
        year = year[:p1]
        if year.startswith("20"):
            year = year[2:]
        year = int ( year )
        if year < 15:
            return 8
        return 13

    def writeBibEntry ( self, bib, Id ):
        self.success += 1
        self.log ( "Success!" )
        sqrts = self.getSqrts ( Id )
        coll = self.findCollaboration ( Id )
        self.stats[coll][Id]={"cached":0 }
        self.f.write ( bib )
        self.f.write ( "\n" )
        if self.write_cache:
            self.writeCache ( Id, bib )
        return

    def processExpRes ( self, expRes, write_cache ):
        self.npublications += 1
        Id = expRes.globalInfo.id
        self.log ( "\n\n\nNow processing %s" % Id )
        self.log ( "==================================" )

        backup = self.tryFetchFromCache( Id )
        if backup != False:
            self.success += 1
            self.log ( "Success!" )
            self.f.write ( backup )
            self.f.write ( "\n" )
            return

        url = expRes.globalInfo.url
        if Id in self.specialcases.keys():
            self.log ( "Marked as special case!" )
            bib = self.bibtexFromCDS ( self.specialcases[Id] )
            if bib:
                self.writeBibEntry ( bib, Id )
                return
            else:
                self.log ( "Special treatment failed." )

        contact = expRes.globalInfo.getInfo ( "contact" ) ## globalInfo.contact
        sqrts = self.getSqrts ( Id )
        coll = self.findCollaboration ( Id )
        if contact and "fastlim" in contact:
            # self.stats[coll][Id]={ "fastlim": 1 }
            self.fastlim += 1
            self.success += 1
            self.log ( "Fastlim. Skipping.\n" )
            return
        if "superseded" in url:
            self.log ( "superseded appears in URL (%s)" % Id )
            self.log ( "   `-- %s" % url )
            self.log ( "Failed!" )
            self.h.write ( "%s failed. (superseded).\n" % Id )
            self.h.write ( "    `---- %s\n" % url )
            self.nfailed += 1
            self.nsuperseded += 1
            return
        self.log ( " * Id, url: %s, %s" % ( Id, url ) )
        bib = self.bibtexFromWikiUrl ( url, Id )
        if bib:
            self.writeBibEntry ( bib, Id )
            return
        if "bin/view/CMSPublic" in url:
            oldurl = url
            url = "http://cms-results.web.cern.ch/cms-results/public-results/publications/%s/index.html" % ( Id.replace ( "CMS-", "" ) )
            self.log ( " * rewriting %s -> %s\n" % ( oldurl, url ) )
            # self.log ( " * Id, Url: %s, %s" % ( Id, url ) )
            bib = self.bibtexFromWikiUrl ( url, Id )
            if bib:
                self.writeBibEntry ( bib, Id )
                return
        self.nfailed += 1
        self.nomatch += 1
        self.log ( "Failed!" )
        self.h.write ( "%s failed (no match).\n" % Id )
        self.h.write ( "    `---- %s\n" % url )

    def run( self, write_cache ):
        self.write_cache = write_cache
        self.openHandles()
        home = os.environ["HOME"]
        # self.db = Database ( "%s/git/smodels-database" % home )
        self.db = Database ( self.databasepath )
        self.res = self.db.getExpResults ()
        ids = set()
        for expRes in self.res:
            ID = expRes.globalInfo.id.replace("-eff","").replace("-agg","")
            if ID in ids:
                continue
            ids.add ( expRes.globalInfo.id )
            if not "ATLAS-SUSY-2015-01" in str(expRes):
                pass
                # continue
            self.processExpRes ( expRes, write_cache )
        self.f.close()
        self.addSummaries()

    def findCollaboration ( self, entry ):
        if type(entry) == str:
            if "ATLAS" in entry:
                return "ATLAS"
            if "CMS" in entry:
                return "CMS"
            return "???"
        collaboration=""
        ID = entry["ID"]
        if "collaboration" in entry.keys():
            t = entry["collaboration"]
            if "ATLAS" in t:
                collaboration = "ATLAS"
            if "CMS" in t:
                collaboration = "CMS"
        else:
            if "ATLAS" in ID:
                collaboration = "ATLAS"
            if "CMS" in ID:
                collaboration = "CMS"
        return collaboration

    def createTestTex ( self, bibtex ):
        """ create the test.tex file, to check """
        print ( "Writing test.tex." )
        f = open ( "test.tex", "wt" )
        f.write ( "\documentclass[a4paper,11pt]{article}\n" )
        f.write ( "\\usepackage{amssymb}\n" )
        f.write ( "\\usepackage{amsmath}\n" )
        f.write ( "\\usepackage{hyperref}\n" )
        f.write ( "\\begin{document}\n" )
        for i in [ "CMS", "ATLAS" ]:
            r = self.createSummaryCitation ( bibtex, i, False )
            f.write ( r + "\\newline\n\n" )
        f.write (
"""\\bibliographystyle{elsarticle-num}
\\bibliography{database}
\end{document}
""" )
        f.close()
        f = open ( "latex.sh", "wt" )
        f.write ( "#!/bin/bash\n" )
        cmds = [ "pdflatex -interaction nonstopmode test.tex", "pdflatex -interaction nonstopmode test.tex", "bibtex test.aux", "pdflatex -interaction nonstopmode test.tex" ]
        cmds = [ "latexmk -pvs -ps test" ]
        cmds = []
        for cmd in cmds:
            f.write ( cmd + "\n" )
        f.close()
        os.chmod ( "latex.sh", 0o755 )
        print ( "Execute latex.sh if you want a test document" )
        # subprocess.getoutput ( "./latex.sh" )
        # os.system ( "./latex.sh" )

    def createSummaryCitation ( self, bibtex, experiment, commentOut=True ):
        """ create summary citation 
        :param commentOut: if true, prepend with %
        """
        entries = bibtex.entries
        filtered = []
        for entry in entries:
            collaboration = self.findCollaboration ( entry )
            if not experiment == collaboration:
                continue
            filtered.append ( entry )
        ret = ""
        if commentOut:
            ret += "% "
        ret += "Use this LaTeX code to cite all " + str(len(filtered)) + " non-superseded "+experiment+" results:\n"
        if commentOut:
            ret += "% "
        ret+= "\cite{"
        labels = self.getLabels ( bibtex )
        for entry in filtered:
            ID = entry["ID"]
            label = labels [ ID ]
            sqrts = self.getSqrts ( label )
            coll = self.findCollaboration ( label )
            if label in self.stats[coll]:
                self.stats[coll][label]["bibtex"]=ID
            ret += "%s, " % ID
        ret = str(ret[:-2]+"}")
        return ret

    def getLabels ( self, bibtex ):
        """ given a bibtex object, extract a dictionary of the labels,
            both ways, so anaid <-> bibtex name.
        """
        biblabels = bibtex.entries_dict.keys()
        labels = {}
        for label,entry in bibtex.entries_dict.items():
            for i in [ "label", "reportnumber", "number" ]:
                if i in entry:
                    name = entry[i].split(",")[0]
                    name = name.split(".")[0]
                    if not label in labels:
                        labels[label]=name
                    if not name in labels:
                        labels[ name ] = label
                    break
        names = { "ATLAS-SUSY-2016-07": "Aaboud:2017vwy",
                  "ATLAS-SUSY-2016-16": "Aaboud:2017aeu",
                  "CMS-SUS-16-050": "Sirunyan:2291344",
                  "ATLAS-CONF-2013-047": "ATLAS-CONF-2013-047",
                  "CMS-SUS-13-012": "Chatrchyan:2014lfa",
                  "ATLAS-SUSY-2013-02": "Aad:2014wea",
                  "CMS-SUS-19-006": "Sirunyan:2686457",
        }
        labels.update ( names )
        reverse = {}
        for k,v in labels.items():
            reverse[v]=k
        labels.update ( reverse )
        return labels

    def query ( self, anaid: str ):
        """ get the bibtex name of anaid
        :param anaid: eg CMS-SUS-16-050
        :returns: bibtex label, eg Aaboud:2017vwy
        """
        path = os.path.dirname ( __file__ )
        refsfile = f"{path}/refs.bib"
        if os.path.exists ( refsfile ):
            f=open( refsfile )
            bibtex=bibtexparser.load ( f )
            f.close()
            biblabels = bibtex.entries_dict.keys()
            labels = self.getLabels ( bibtex )
            if anaid in labels:
                return labels[anaid]
        return "FIXME"

    def interactive ( self ):
        """ start an interactive session """
        import IPython
        IPython.embed( using = False )

    def addSummaries ( self ):
        f=open("refs.bib")
        self.log ( "adding summaries to database.bib." )
        self.header()
        bibtex=bibtexparser.load ( f )
        f.close()
        self.i.write ( "\n" )
        self.i.write ( self.createSummaryCitation ( bibtex, "CMS" ) )
        self.i.write ( "\n" )
        self.i.write ( self.createSummaryCitation ( bibtex, "ATLAS" ) )
        self.i.write ( "\n" )
        self.i.close()
        self.createTestTex ( bibtex )
        commands.getoutput ( "cat refs.bib >> database.bib" )

    def createStatsFile ( self ):
        """ create a file that contains the stats of this process """
        statsfile = "bib.py"
        print ( f"Writing {statsfile}." )
        f = open ( statsfile,"wt" )
        sqrtses = list ( self.stats.keys() )
        sqrtses.sort()
        f.write ( "D={ 'CMS':{}, 'ATLAS':{} }\n" )
        f.write ( "I={}\n" )
        for coll,anas in self.stats.items():
            for ana,values in anas.items():
                f.write ( "D['%s']['%s'] = %s\n" % ( coll, ana, str(values) ) )
                bibtex = values["bibtex"]
                ivalues = values
                ivalues.pop ( "bibtex" )
                ivalues["anaid"]=ana
                f.write ( "I['%s'] = %s\n" % ( bibtex, str(ivalues) ) )
        f.close()

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='write bibtex files for database, and other bibtex related tools' )
    argparser.add_argument ( '-d', '--database',
            help='path to database [../../../smodels-database]',
            type=str, default='../../../smodels-database' )
    argparser.add_argument ( '-v', '--verbose',
            help='specifying the level of verbosity (error, warning, info, debug) [info]',
            default = 'info', type = str )
    argparser.add_argument ( "-q", "--query",
            help="query the database for bibtex label of <anaId>",
            default = None, type = str )
    argparser.add_argument ( "-c", "--copy",
            help="copy bibtex files to database folder (does not generate the files, however)",
            action="store_true" )
    argparser.add_argument ( "-w", "--write_cache",
            help=f"cache the retrieved results in {BibtexWriter.cachedir}",
            action="store_true" )
    args = argparser.parse_args()
    writer = BibtexWriter( args.database, args.verbose )
    if args.query != None:
        ret = writer.query( args.query )
        print ( "query for %s resulted in %s" % ( args.query, ret ) )
        sys.exit()
    if args.copy:
        writer.copy()
    else:
        writer.run( args.write_cache )
        writer.close()
