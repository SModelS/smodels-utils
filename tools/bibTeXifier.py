#!/usr/bin/env python

"""
.. module:: bibTeXification
        :synopsis: module intended to obtain the optimal bibtex description for a given analysis.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import urllib
import setPath
from smodels_tools.tools import databaseBrowser

class BibTeXifier:
    def __init__ ( self, analysis, run=None, database=None ):
        """
            create a bibtexifier for one analysis
        """
        self.ananame=analysis
        self.run=run
        self.database=database
        self.browser=databaseBrowser.Browser ()
        if database!=None:
            self.browser=databaseBrowser.Browser ( database )
        self.analysis=self.browser.expAnalysis ( analysis )
        self.createBibTeX()

    def createBibTeX(self):
        """ create bibtex entry """
        self.noBibTeX()
        self.fromPAS ()


    def noBibTeX ( self ):
        """ set the default to 'no bibtex found' """
        self.bibtex="No bibtex entry found for {}".format(analysis)
        if self.run:
            self.bibtex+=" run {}".format(run)
        if self.database:
            self.bibtex+=" database at {}".format(self.browser.base)

    def bibprint ( self ):
        """ print the entry on stdout """
        print(self.bibtex)

    def write ( self, filename ):
        """ write into file called 'filename' """
        import os
        mode="a"
        f=open(filename,mode)
        f.write ( self.bibtex + "\n" )
        f.close()

    def fromPAS ( self ):
        """ obtain bibtex entry from a CMS PAS number (e.g. SUS-13-002 or SUS13002) """
        if not self.analysis:
            return 
        url="http://inspirehep.net/search?ln=en&ln=en&p=find+r+%s&of=hx&action_search=Search&sf=earliestdate&so=d&rm=&rg=25&sc=0" % \
             self.analysis.pas
        f=urllib.urlopen ( url )
        # self.bibtex="fromPAS {}".format ( self.analysis.pas )
        lines=f.readlines()
        f.close()
        self.bibtex=""
        write=False
        hasJournalLine=False ## if we find an entry with a journal line, we take it
        for line in lines:
            if line.find ( "</pre>" ) > -1 :
                write=False
                if hasJournalLine:
                    ## we have a journal line, so we quit
                    return
            if write:
                if line.find("@article")>-1:
                    ## we replace the label with the ana name
                    line="@article{%s,\n" % self.analysis.pas
                self.bibtex+=line
                if line.find("journal")>-1:
                    hasJournalLine=True
            if line.find ( "<pre>" ) > -1:
                if not hasJournalLine:
                    ## no journal line yet, so we delete the last one
                    self.bibtex=""
                write=True

    def fromArXiv ( self, arxiv ):
        """ obtain bibtex entry from an arxiv name """
        ret="?"
        return ret
        
    def fromJournalPublication ( self, publication ):
        """ obtain bibtex entry from a journal publication """
        ret="?"
        return ret


if __name__ == '__main__':
    import argparse, types
    argparser = argparse.ArgumentParser(description='tool that is meant to return optimal bibtex entry for a given analysis')
    argparser.add_argument ( '-r', '--run', nargs='?', help='name of the run', type=types.StringType, default=None )
    argparser.add_argument ( '-d', '--database', nargs='?', help='path to database', type=types.StringType, default=None )
    argparser.add_argument ( '-f', '--filename', nargs='?', help='write to <filename>, if None, print to stdout', \
                             type=types.StringType, default=None )
    argparser.add_argument ( 'analyses', nargs='+', help='name of the analyses', type=types.StringType, default=None )
    args=argparser.parse_args()

    for analysis in args.analyses:
        texifier=BibTeXifier ( analysis, args.run, args.database )
        if args.filename:
            texifier.write ( args.filename )
        else:
            texifier.bibprint()
