#!/usr/bin/python

from __future__ import print_function
from smodels.experiment.databaseObj import Database
import urllib
import os, sys
import bibtexparser
try:
    import commands
except ImportError:
    import subprocess as commands

""" write bibtex file of analysis references from the database itself """

class BibtexWriter:
    def __init__ ( self ):
        self.f=open ( "refs.bib", "w" )
        self.g=open ( "log.txt", "w" )
        self.h=open ( "failed.txt", "w" )
        self.i=open ( "database.bib", "w" )
        self.npublications = 0
        self.nfailed = 0
        self.nsuperseded = 0
        self.not_found = 0
        self.success = 0
        self.nomatch = 0
        self.fastlim = 0
        self.specialcases = { 
            "CMS-PAS-SUS-13-018": "https://cds.cern.ch/record/1693164",
            "CMS-PAS-SUS-13-023": "http://cds.cern.ch/record/2044441",
            "ATLAS-CONF-2013-007": "http://cds.cern.ch/record/1522430",
            "ATLAS-CONF-2013-061": "http://cds.cern.ch/record/1557778",
            "ATLAS-CONF-2013-089": "http://cds.cern.ch/record/1595272",
        }

    def header ( self ):
        self.i.write ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n" )
        self.i.write ( "% References for the analyses included in this version of the database %\n" )
        self.i.write ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n" )
        self.i.write ( "\n" )

    def close ( self ):
        self.log ( "%d results in container." % len(self.res) )
        self.log ( "Summary: %d / %d successful." % \
                ( self.success, self.npublications ) )
        self.log ( "failed: %d" % self.nfailed )
        self.log ( " ... of which: %d superseded results" % self.nsuperseded )
        self.log ( "               %d not found" % self.not_found )
        self.log ( "               %d fastlim" % self.fastlim )
        self.log ( "               %d no match" % self.nomatch )
        self.g.close()
        self.h.close()

    def bibtexFromCDS ( self, url, label=None ):
        """ get the bibtex entry from cds """
        self.log ( " * fetching from CDS: %s" % url )
        fullurl =  url+"/export/hx" 
        f=urllib.urlopen (fullurl)
        lines = f.readlines()
        f.close()
        ret = []
        hasBegin = False
        inAuthorList = False
        for line in lines:
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
        return "".join ( ret )

    def bibtexFromInspire ( self, url, label=None ):
        """ get the bibtex entry from an inspire record """
        self.log ( " * fetching from Inspire: %s" % url )
        fullurl =  url+"/export/hx" 
        # return fullurl
        f=urllib.urlopen (fullurl)
        lines = f.readlines()
        f.close()
        ret = []
        hasBegin = False
        for line in lines:
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
        return "".join ( ret )

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
        self.log ( " * CDSUrl: %s" % ret )
        return ret

    def bibtexFromWikiUrl ( self, url, label=None ):
        """ get the bibtex entry from the atlas wiki """
        self.log ( " * fetching from wiki: %s" % url )
        f=urllib.urlopen ( url )
        lines = f.readlines()
        f.close()
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
        #    print ( l )
            if "nspire" in l:
                inspire = self.fetchInspireUrl ( l, label )
                # self.log ( "   `- fetching from inspire: %s" % inspire )
                if not "failed" in inspire:
                    return self.bibtexFromInspire ( inspire, label )
            if 'CDS record' in l:
                cds = self.fetchCDSUrl ( l, label )
                if not "failed" in cds:
                    return self.bibtexFromCDS ( cds, label )
            if 'target="_blank">' in l:
            # if 'target="_blank">Link to ' in l:
                pas = self.fetchPasUrl ( l )
                if not "failed" in pas:
                    return self.bibtexFromCDS ( pas, label )

    def log ( self, line ):
        print ( line )
        self.g.write ( line + "\n" )

    def test( self ):
        # print ( self.bibtexFromInspire ( "http://inspirehep.net/record/1469069", "ATLAS-SUSY-2015-02" ) )
        # print ( self.bibtexFromWikiUrl ( "https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/SUSY-2015-02/","ATLAS-SUSY-2015-02" ) )
        # print ( self.bibtexFromWikiUrl ( "http://cms-results.web.cern.ch/cms-results/public-results/publications/SUS-15-002/index.html", "CMS-SUS-15-002" ) )
        print ( self.bibtexFromWikiUrl ( "http://cms-results.web.cern.ch/cms-results/public-results/publications/SUS-15-002/index.html", "CMS-SUS-15-002" ) )
        sys.exit()

    def searchOnCMSWiki ( self, Id ):
        """ search for the publication on the summary wiki page """
        return None



    def processExpRes ( self, expRes ):
        self.npublications += 1
        Id = expRes.globalInfo.id
        self.log ( "\n\n\nNow processing %s" % Id )
        self.log ( "==================================" )
        url = expRes.globalInfo.url
        if Id in self.specialcases.keys():
            self.log ( "Marked as special case!" )
            bib = self.bibtexFromCDS ( self.specialcases[Id] )
            if bib:
                self.success += 1
                self.log ( "Success!" )
                self.f.write ( bib )
                self.f.write ( "\n" )
                return
            else:
                self.log ( "Special treatment failed." )
            
        contact = expRes.globalInfo.getInfo ( "contact" ) ## globalInfo.contact
        if contact and "fastlim" in contact:
            self.fastlim += 1
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
        self.log ( " * Id, Url: %s, %s" % ( Id, url ) )
        bib = self.bibtexFromWikiUrl ( url, Id )
        if bib:
            self.success += 1
            self.log ( "Success!" )
            self.f.write ( bib )
            self.f.write ( "\n" )
            return
        if "bin/view/CMSPublic" in url:
            oldurl = url
            url = "http://cms-results.web.cern.ch/cms-results/public-results/publications/%s/index.html" % ( Id.replace ( "CMS-", "" ) )
            self.log ( " * rewriting %s -> %s\n" % ( oldurl, url ) )
            # self.log ( " * Id, Url: %s, %s" % ( Id, url ) )
            bib = self.bibtexFromWikiUrl ( url, Id )
            if bib:
                self.success += 1
                self.log ( "Success! (with url rewrite)" )
                # self.log ( "Bib: %s" % bib[-100:] )
                self.f.write ( bib )
                self.f.write ( "\n" )
                return
        self.nfailed += 1
        self.nomatch += 1
        self.log ( "Failed!" )
        self.h.write ( "%s failed (no match).\n" % Id )
        self.h.write ( "    `---- %s\n" % url )

    def run( self ):
        home = os.environ["HOME"]
        # db = Database ( "%s/git/smodels/test/tinydb" % home )
        self.db = Database ( "%s/git/smodels-database" % home )
        self.res = self.db.getExpResults ()
        ids = []
        for expRes in self.res:
            if expRes.globalInfo.id in ids:
                continue
            ids.append ( expRes.globalInfo.id )
#            if not "CMS-PAS-SUS-16-033" in str(expRes):
#                continue
            self.processExpRes ( expRes )
        self.f.close()
        self.addSummaries()

    def findCollaboration ( self, entry ):
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

    def createSummaryCitation ( self, entries, experiment ):
        filtered = []
        for entry in entries:
            collaboration = self.findCollaboration ( entry )
            if not experiment == collaboration:
                continue
            filtered.append ( entry )
        ret = "% Use this LaTeX code to cite all " + str(len(filtered)) + " non-superseded "+experiment+" results:\n"
        ret+= "% \cite{"
        for entry in filtered:
            ID = entry["ID"]
            ret += "%s, " % ID
        ret = ret[:-2]+"}"
        return ret

    def addSummaries ( self ):
        f=open("refs.bib")
        self.log ( "adding summaries to database.bib." )
        self.header()
        bibtex=bibtexparser.load ( f )
        f.close()
        self.i.write ( "\n" )
        self.i.write ( self.createSummaryCitation ( bibtex.entries, "CMS" ) )
        self.i.write ( "\n" )
        self.i.write ( self.createSummaryCitation ( bibtex.entries, "ATLAS" ) )
        self.i.write ( "\n" )
        self.i.close()
        commands.getoutput ( "cat refs.bib >> database.bib" )


if __name__ == "__main__":
    writer = BibtexWriter()
    writer.run()
    writer.close()
