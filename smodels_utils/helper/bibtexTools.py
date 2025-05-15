#!/usr/bin/env python3

"""
.. module:: bibtexTools
        :synopsis: Collection of methods for bibtex. The module is also
        an executable that can be used to create a database.bib file for a 
        given database.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

__all__ = [ "BibtexWriter", "removeDoubleEntries" ]

from smodels.base.smodelsLogging import setLogLevel
import bibtexparser
import urllib, subprocess
import os, sys, time
from smodels.experiment.databaseObj import Database
from smodels_utils import SModelSUtils 
from smodels_utils.helper.databaseManipulations import filterFastLimFromList, \
         filterSupersededFromList
from smodels_utils.helper.various import getSqrts, getCollaboration
from typing import Union, Text
from smodels_utils.helper.terminalcolors import *

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

def removeDoubleEntries ( anaids : dict ) -> dict:
    """ given two lists of analysis ids, remove all ids that appear in both 
    :param anaids: should be a dictionary of two collections of anaids, e.g. \
                   { "smodels230": {ana1, ana2}, "smodels220": {ana2, ana3} }
    :returns: a dictionary that shows the ids of anaX that are not in anaY
    """
    new1, new2 = [], []
    def pprint ( *args ):
        return
        print ( " ".join ( map(str,args) ) )
    lists = list ( anaids.items() )
    name1, list1 = lists[0]
    name2, list2 = lists[1]
    for l1 in list1:
        if not l1 in list2:
            new1.append ( l1 )
        else:
            pprint ( "removing", l1, "from list1" )
    for l2 in list2:
        if not l2 in list1:
            new2.append ( l2 )
        else:
            pprint ( "removing", l2, "from list2" )
    ret = { name1: new1, name2: new2 }
        
    return ret

class BibtexWriter:
    # cachedir = "../bibtexs/"
    cachedir = f"{SModelSUtils.installDirectory()}/smodels_utils/bibtexs/"
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
        self.nomatch = []
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

    def cleanAnaId ( self, anaid : str ):
        """ clean analysis id from some extensions """
        from smodels_utils.helper import various
        return various.removeAnaIdSuffices ( anaid )

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
        self.i.write ( f"% This file was created at {time.asctime()} for db v{self.db.databaseVersion}         "[:71]+"%\n" )
        self.i.write ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n" )
        self.i.write ( "\n" )

    def copy ( self ):
        """ copy the files to the database path. """
        if os.path.isdir ( self.databasepath ) and os.path.exists ( "database.bib" ) and os.path.exists ( "refs.bib" ) and os.stat ( "database.bib" ).st_size > 0 and os.stat ( "refs.bib" ).st_size > 0:
            self.log ( f"Copying database.bib to {self.databasepath}" )
            cmd = f"cp ./database.bib {self.databasepath}"
            o = commands.getoutput ( cmd )
            if len(o) != 0:
                self.log ( f"cp: {o}" )
            else:
                self.log ( f"{GREEN}Success!{RESET}" )
        else:
            if not os.path.isdir ( self.databasepath ):
                print ( f"Databasepath {self.databasepath} is not a directory. Wont copy." )
            else:
                self.log ( "Did not copy ./database.bib and ./refs.bib. Something seems wrong. Maybe you did not generate them?" )


    def close ( self ):
        self.log ( f"{len(self.res)} results in container." )
        self.log ( f"Summary: {self.success} / {self.npublications} successful." )
        self.log ( " ... of which: %d superseded results" % self.nsuperseded )
        self.log ( f"               {self.not_found} not found" )
        self.log ( f"               {self.fastlim} fastlim" )
        self.log ( f"               {len(self.nomatch)} no match" )
        self.log ( f"               {','.join( self.nomatch )}" )
        self.log ( "failed: %d" % self.nfailed )
        self.g.close()
        self.h.close()
        self.createStatsFile()

    def bibtexFromCDS ( self, url, label=None ):
        """ get the bibtex entry from cds """
        fullurl =  url+"/export/hx"
        fullurl = fullurl.replace ( "?ln=en", "" )
        fullurl = fullurl.replace ( "?ln=de", "" )
        self.log ( f" * fetching from CDS: {fullurl}" )
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
                ret.append ( f'      label          = "{label}",\n' )
            if "@techreport" in line and label != None:
                ret.append ( f'      label          = "{label}",\n' )
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
                print ( f"foreign letter {o}: {letter}" )
                print ( f"The context was: >>{source[ctr-20:ctr]}#{source[ctr+1:ctr+20]}<<" )
                sys.exit()
        if self.verbose in [ "debug", "info" ]:
            print ( source )
        source=source.replace( "8TeV", "8 TeV" ).replace("Tev","TeV" )
        source=source.replace ( "fb-1", "fb$^{-1}$" )
        source=source.replace ( "AlphaT", "$\\alpha_{T}$" )
        return source

    def bibtexFromInspire ( self, url : str, label : Union[None,str] = None ):
        """ get the bibtex entry from an inspire record """
        url = url.replace("record","api/literature" )
        self.log ( f" * fetching from Inspire: {url}" )
        ## hack for now, this solution wont work in the future
        # self.warn ( "for now we are using the old.inspirehep.net hack. This wont work in the long run!" )
        # url =  url.replace( "inspirehep.net", "old.inspirehep.net" )
        fullurl =  url +"?format=bibtex"
        # return fullurl
        try:
            f=urlopen (fullurl)
            txt = f.read()
            f.close()
            txt = txt.decode("utf-8")
            if label != None:
                p1 = txt.rfind("}")
                txt = txt[:p1-1] + f',\n    label = "{label}"\n}}\n'
            return txt
        except urllib.error.HTTPError as e:
            print ( f"[bibtexTools] Caught: {e}" )
            sys.exit(-1)
        except Exception as e:
            print ( f"[bibtexTools] Caught: {e}" )
            sys.exit(-1)

    def fetchInspireUrl ( self, line : str, label : Union[None,str] ):
        """ from line in html page, extract the inspire url """
        # line = line.lower()
        self.log ( f" * fetching Inspire url: {label}" )
        line = line.replace ( "net/literature", "net/api/literature" )
        line = line.replace(' id="inspire_link"','')
        pos1 = line.find ( "href=" )
        if pos1 < 0:
            pos1 = line.find ( "HREF=" )
        pos2 = line.find( "<b>" )
        if pos2 < 0:
            pos2 = line.find( "<B>" )
        if pos1 > 0 and pos2 > pos1:
            ret = line[pos1+6:pos2-2]
            return ret
        pos1 = line.find ( "href=" )
        pos2 = line.find ( "inSPIRE" )
        if pos1 > 0 and (pos2 > pos1 or pos2<0) and not "INSPIRE_ID" in line:
            ret=line[pos1+6:pos2-2]
            return ret
        self.log ( f"    * fetching attempt failed!" ) 
        return "fetchInspireUrl failed"

    def fetchPasUrl ( self, line ):
        pos1 = line.find( 'href="' )
        pos2 = line.find( ' target=' )
        if pos1 < 1 or pos2 < pos1:
            return "failed to find pas url"
        ret = line[pos1+6:pos2-1]
        self.log ( f" * PasUrl: {ret}" )
        return ret

    def fetchCDSUrl ( self, line, label ):
        self.log ( f" * fetching CDS url: {label}" )
        pos1 = line.find( 'href="' )
        pos2 = line.find( '">CDS' )
        if pos1 < 1 or pos2 < pos1:
            return "failed to find pas url"
        ret = line[pos1+6:pos2]
        self.log ( f" * CDS url: {ret}" )
        return ret

    def bibtexFromWikiUrl ( self, url : str, label : Union[None,str]=None ):
        """ get the bibtex entry from the atlas wiki """
        self.log ( f" * fetching from wiki: {url}" )
        try:
            f=urlopen ( url )
        except urllib.error.HTTPError as e:
            self.log( f"   `- error {e}, not fetching from wiki" )
            return None
        lines = f.readlines()
        f.close()
        lines = list ( map ( str, lines ) )

        ## first pass, aim for inspire
        for l in lines:
            if "nspire" in l and "href" in l.lower():
                inspire = self.fetchInspireUrl ( l, label )
                self.log ( f"   `- fetching from inspire: {inspire}" )
                if not "failed" in inspire:
                    return self.bibtexFromInspire ( inspire, label )

        ## second pass, try CDS and everything else
        for l in lines:
            if "preliminary results are superseded by the following paper" in l:
                self.log ( f"    {label}: superseded !!!!! " )
                self.h.write ( f"{label} is superseded." )
                self.nsuperseded += 1
                return None
            if "404 - Not found" in l:
                self.log ( f"    {label} is not found!" )
                #self.h.write ( f"{label} is not found!" )
                #self.not_found += 1
                return None
            if 'CDS record' in l:
                cds = self.fetchCDSUrl ( l, label )
                if not "failed" in cds:
                    try:
                        return self.bibtexFromCDS ( cds, label )
                    except Exception as e:
                        print ( f"HTTPEerror when fetching {cds}/{label} from CDS: {e}" )
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
        print ( f"{RED}WARN {line}{RESET}" )
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
        fname = f"{self.cachedir}/{Id}.tex"
        if not os.path.exists ( fname ):
            return False
        self.log ( "A backup file exists. We use it." )
        f=open( fname, "r" )
        txt=f.read()
        f.close()
        sqrts = getSqrts ( Id )
        coll = getCollaboration ( Id )
        self.stats[coll][Id] = { "cached": 1 }
        return txt

    def writeCache ( self, Id, bib ):
        """ write the cache entry for analysis id <Id>, bibtex text is <bib> """
        self.log ( f"Now write cache file {self.cachedir}/{Id}.tex" )
        cachef = open ( f"{self.cachedir}/{Id}.tex", "w" )
        cachef.write ( str(bib) )
        cachef.write ( "\n" )
        cachef.close()

    def writeBibEntry ( self, bib : str , Id : str ):
        self.success += 1
        self.log ( f"{GREEN}Success!{RESET}" )
        sqrts = getSqrts ( Id )
        coll = getCollaboration ( Id )
        self.stats[coll][Id]={"cached":0 }
        bib=bib.strip()
        if not "label" in bib:
            bib = bib[:-1]+",\n    label={"+Id+"}}"
        if bib.endswith("}"):
            bib = bib[:-1]+"\n}\n"

        self.f.write ( bib )
        self.f.write ( "\n" )
        if False and "10.1103/PhysRevD.103.112006" in bib:
            print ( f"XXX {Id}:\n\n {bib}" )
        if self.write_cache:
            self.writeCache ( Id, bib )
        return

    def processExpRes ( self, expRes, write_cache ):
        """ process the given experimental result """
        self.npublications += 1
        Id = self.cleanAnaId ( expRes.globalInfo.id )
        self.log ( f"\nNow processing {YELLOW}{Id}{RESET}" )
        self.log ( "==================================" )

        backup = self.tryFetchFromCache( Id )
        if backup != False:
            self.success += 1
            self.log ( f"{GREEN}Success!{RESET}" )
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

        contact = None
        if hasattr ( expRes.globalInfo, "contact" ):
            contact = expRes.globalInfo.contact ## globalInfo.contact
        sqrts = getSqrts ( Id )
        coll = getCollaboration ( Id )
        if contact and "fastlim" in contact:
            # self.stats[coll][Id]={ "fastlim": 1 }
            self.fastlim += 1
            self.success += 1
            self.log ( "Fastlim. Skipping.\n" )
            return
        if "superseded" in url:
            self.log ( f"superseded appears in URL ({Id})" )
            self.log ( f"   `-- {url}" )
            self.log ( f"{RED}Failed!{RESET}" )
            self.h.write ( f"{Id} failed. (superseded).\n" )
            self.h.write ( f"    `---- {url}\n" )
            self.nfailed += 1
            self.nsuperseded += 1
            return
        self.log ( f" * Id, url: {Id}, {url}" )
        bib = self.bibtexFromWikiUrl ( url, Id )
        if bib:
            self.writeBibEntry ( bib, Id )
            return
        if "bin/view/CMSPublic" in url:
            oldurl = url
            shortId = Id.replace ( "CMS-", "" )
            url = f"http://cms-results.web.cern.ch/cms-results/public-results/publications/{shortId}/index.html"
            self.log ( f" * rewriting {oldurl} -> {url}\n" )
            bib = self.bibtexFromWikiUrl ( url, Id )
            if bib is not None and bib[0]:
                self.writeBibEntry ( bib[1], Id )
                return
        ## try with doi2bib
        if hasattr ( expRes.globalInfo, "publicationDOI" ):
            from doi2bib.crossref import get_bib_from_doi
            bib = get_bib_from_doi ( expRes.globalInfo.publicationDOI )
            if bib[0]:
                text = bib[1]
                p1 = text.find("author={")
                p2 = text.find("}",p1 )
                if p2 - p1 > 10000: 
                    ## replace author list with collaboration name
                    text = text[:p1] + "author={" + coll + " collaboration}" + bib[1][p2+1:]
                text = text.replace( '\n<mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="inline"><mml:mi>p</mml:mi><mml:mi>p</mml:mi></mml:math>\n', r"$pp$" )
                text = text.replace( '<mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="inline"><mml:mi>p</mml:mi><mml:mi>p</mml:mi></mml:math>', r"$pp$" )
                text = text.replace( '\n<mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="inline"><mml:msqrt><mml:mi>s</mml:mi></mml:msqrt><mml:mo>=</mml:mo><mml:mn>13</mml:mn><mml:mtext> </mml:mtext><mml:mtext> </mml:mtext><mml:mi>TeV</mml:mi></mml:math>\n', r"$\sqrt{s} =$ 13 TeV" )
                text = text.replace( '<mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="inline"><mml:msqrt><mml:mi>s</mml:mi></mml:msqrt><mml:mo>=</mml:mo><mml:mn>13</mml:mn><mml:mtext> </mml:mtext><mml:mtext> </mml:mtext><mml:mi>TeV</mml:mi></mml:math>', r"$\sqrt{s} =$ 13 TeV" )

                text = text.replace(", ",", \n    ")
                self.writeBibEntry ( text, Id )
                return
        self.nfailed += 1
        self.nomatch.append ( Id )
        self.log ( f"{RED}Failed!{RESET}" )
        self.h.write ( f"{Id} failed (no match).\n" )
        self.h.write ( f"    `---- {url}\n" )

    def run( self, write_cache, do_filter : bool, outfile : os.PathLike ):
        """ 
        :param outfile: name of output file, default: database.bib
        """
        self.write_cache = write_cache
        self.openHandles()
        home = os.environ["HOME"]
        self.db = Database ( self.databasepath )
        self.res = self.db.getExpResults ()
        if do_filter:
            self.res = filterSupersededFromList ( filterFastLimFromList(self.res) )
        ids = set()
        for expRes in self.res:
            ID = self.cleanAnaId ( expRes.globalInfo.id )
            if ID in ids:
                continue
            ids.add ( ID )
            if not "ATLAS-SUSY-2015-01" in str(expRes):
                pass
                # continue
            self.processExpRes ( expRes, write_cache )
        self.f.close()
        self.addSummaries( outfile )

    def createTestTex ( self, bibtex ):
        """ create the test.tex file, to check """
        print ( "Writing test.tex." )
        f = open ( "test.tex", "wt" )
        f.write ( r"\documentclass[a4paper,11pt]{article}" )
        f.write ( "\n" )
        f.write ( "\\usepackage{amssymb}\n" )
        f.write ( "\\usepackage{amsmath}\n" )
        f.write ( "\\usepackage{hyperref}\n" )
        f.write ( "\\begin{document}\n" )
        for i in [ "CMS", "ATLAS" ]:
            r = self.createSummaryCitation ( bibtex, i, False )
            f.write ( r + "\\newline\n\n" )
        f.write (
"""\\bibliographystyle{plain}
\\bibliography{database}
\\end{document}
""" )
        f.close()
        f = open ( "latex.sh", "wt" )
        f.write ( "#!/bin/bash\n" )
        cmds = [ "pdflatex -interaction nonstopmode test.tex", "pdflatex -interaction nonstopmode test.tex", "bibtex test.aux", "pdflatex -interaction nonstopmode test.tex", "bibtex test.aux", "pdflatex -interaction nonstopmode test.tex" ]
        #cmds = [ "latexmk -pvs -ps test" ]
        #cmds = []
        for cmd in cmds:
            f.write ( cmd + "\n" )
        f.close()
        os.chmod ( "latex.sh", 0o755 )
        print ( "Execute latex.sh if you want a test document" )

    def createSummaryCitation ( self, bibtex, experiment, commentOut=True ):
        """ create summary citation 
        :param commentOut: if true, prepend with %
        """
        entries = bibtex.entries
        filtered = []
        for entry in entries:
            label = "???"
            if "label" in entry:
                label = entry["label"]
            else:
                if "reportNumber" in entry:
                    label = entry["reportNumber"].split(",")[0].strip()
                elif "reportnumber" in entry:
                    label = entry["reportnumber"].split(",")[0].strip()
                else:
                    self.warn ( f"label not defined in {entry}" )
                    import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()
            collaboration = getCollaboration ( label )
            if not experiment == collaboration:
                continue
            filtered.append ( entry ) # label )
        ret = ""
        if commentOut:
            ret += "% "
        ret += "Use this LaTeX code to cite all " + str(len(filtered)) + " non-superseded "+experiment+" results:\n"
        if commentOut:
            ret += "% "
        ret+= r"\cite{"
        labels = self.getLabels ( bibtex )
        for entry in filtered:
            ID = entry["ID"]
            label = labels [ ID ]
            sqrts = getSqrts ( label )
            coll = getCollaboration ( label )
            if coll in self.stats and label in self.stats[coll]:
                self.stats[coll][label]["bibtex"]=ID
            ret += f"{ID}, "
        ret = str(ret[:-2]+"}")
        return ret

    def getLabels ( self, bibtex ):
        """ given a bibtex object, extract a dictionary of the labels,
            both ways, so anaid <-> bibtex name.
        """
        biblabels = bibtex.entries_dict.keys()
        labels = {}
        for label,entry in bibtex.entries_dict.items():
            for i in [ "label", "reportnumber", "reportNumber" ]:
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

    def query ( self, anaid: str, search : bool = False ) -> str:
        """ get the bibtex name of anaid
        :param anaid: eg CMS-SUS-16-050
        :param search: if true, then search for it if not available
        :returns: bibtex label, eg Aaboud:2017vwy
        """
        # path = os.path.dirname ( __file__ )
        path = os.getcwd()
        refsfile = f"{path}/database.bib"
        if not os.path.exists ( refsfile ):
            db_bib = f"{self.databasepath}/database.bib"
            if os.path.exists ( db_bib ):
                print ( f"[bibtexTools] symlinking {db_bib} -> {refsfile}" )
                os.symlink ( db_bib, refsfile )
        if os.path.exists ( refsfile ):
            bibtex=self.getBibtex ( refsfile )
            biblabels = bibtex.entries_dict.keys()
            labels = self.getLabels ( bibtex )
            # import sys, IPython; IPython.embed( colors = "neutral" ); sys.exit()
            if anaid in labels:
                return labels[anaid]
        if search:
            self.pprint ( f"not in cache: lets search for this!" )
            self.db = Database ( self.databasepath )
            expRes = self.db.getExpResults ( analysisIDs = [ anaid ] )
            if len(expRes)>0:
                self.write_cache = False
                self.processExpRes ( expRes[0], write_cache=False )
        return f"no entry for {anaid} in {refsfile} found"

    def pprint ( self, *args ):
        print ( f"[bibtexTools] {' '.join(map(str,args))}" )

    def interactive ( self ):
        """ start an interactive session """
        import IPython
        IPython.embed( colors="neutral" )

    def getBibtex ( self, bibtexfile : str ):
        """ get the bibtex content from file, hopefully working with
        bibtexparser v1 and v2 alike """
        # v1
        if not hasattr ( bibtexparser, "parse_file" ):
            with open( bibtexfile ) as handle:
                bibtex = bibtexparser.load(handle)
                handle.close()
                return bibtex
        # v2
        return bibtexparser.parse_file ( bibtexfile )

    def addSummaries ( self, outfile : os.PathLike ):
        f=open("refs.bib")
        self.log ( f"adding summaries to {outfile}." )
        self.header()
        bibtex = self.getBibtex ( "refs.bib" )
        f.close()
        self.i.write ( "\n" )
        self.i.write ( self.createSummaryCitation ( bibtex, "CMS" ) )
        self.i.write ( "\n" )
        self.i.write ( self.createSummaryCitation ( bibtex, "ATLAS" ) )
        self.i.write ( "\n" )
        self.i.write ( "\n" )
        self.i.close()
        self.createTestTex ( bibtex )
        commands.getoutput ( f"cat refs.bib >> {outfile}" )

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
                f.write ( f"D['{coll}']['{ana}'] = {str(values)}\n" )
                if not "bibtex" in values:
                    print ( f"cannot find bibtex in {values} for {ana}" )
                    continue
                bibtex = values["bibtex"]
                ivalues = values
                ivalues.pop ( "bibtex" )
                ivalues["anaid"]=ana
                f.write ( f"I['{bibtex}'] = {str(ivalues)}\n" )
        f.close()
    def createPdf ( self ):
        """ create the pdf file, i.e. execute latex.sh """
        o = subprocess.getoutput ( "./latex.sh" )
        self.pprint ( "test.pdf created." )
        # os.system ( "./latex.sh" )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='write bibtex files for database, and other bibtex related tools' )
    argparser.add_argument ( '-d', '--database',
            help='path to database [../../../smodels-database]',
            type=str, default='../../../smodels-database' )
    argparser.add_argument ( '-o', '--outfile',
            help='output file name [database.bib]',
            type=str, default='database.bib' )
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
    argparser.add_argument ( "-n", "--dont_filter",
            help=f"dont filter anything out",
            action="store_true" )
    argparser.add_argument ( "-p", "--pdf",
            help=f"create pdf summary document",
            action="store_true" )
    args = argparser.parse_args()
    writer = BibtexWriter( args.database, args.verbose )
    if args.query != None:
        ret = writer.query( args.query, search = False )
        print ( f"query for {args.query} resulted in: {ret}" )
        sys.exit()
    if args.copy:
        writer.copy()
    else:
        writer.run( args.write_cache, not args.dont_filter, args.outfile )
        writer.close()
    if args.pdf:
        writer.createPdf()
