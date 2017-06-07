#!/usr/bin/python

from __future__ import print_function
from smodels.experiment.databaseObj import Database
import urllib
import os, sys

""" write bibtex file of analysis references from the database itself """

def bibtexFromInspire ( url, label=None ):
    """ get the bibtex entry from an inspire record """
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
        if len (ret ) == 1 and label != None:
            ret.append ( '      label          = "%s",\n' % label )
    return "".join ( ret )

def fetchInspireUrl ( l ):
    """ from line in html page, extract the inspire url """
    pos1 = l.find ( "HREF=" )
    pos2 = l.find ( "<B>" )
    if pos1 > 0 and pos2 > pos1:
        return l[pos1+6:pos2-2]
    pos1 = l.find ( "href=" )
    pos2 = l.find ( "inSPIRE" )
    if pos1 > 0 and pos2 > pos1:
        return l[pos1+6:pos2-2]
    return "fetchInspireUrl failed"


def bibtexFromWikiUrl ( url, label=None ):
    """ get the bibtex entry from the atlas wiki """
    print ( " * fetching from wiki", url )
    f=urllib.urlopen ( url )
    lines = f.readlines()
    f.close()
    for l in lines:
        if "nspire" in l:
            inspire = fetchInspireUrl ( l )
            print ( "   `- fetching from inspire", inspire )
            return bibtexFromInspire ( inspire, label )
def test():
    # print ( bibtexFromInspire ( "http://inspirehep.net/record/1469069", "ATLAS-SUSY-2015-02" ) )
    # print ( bibtexFromWikiUrl ( "https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/SUSY-2015-02/","ATLAS-SUSY-2015-02" ) )
    print ( bibtexFromWikiUrl ( "http://cms-results.web.cern.ch/cms-results/public-results/publications/SUS-15-002/index.html", "CMS-SUS-15-002" ) )

def main():
    test()
    sys.exit()
    home = os.environ["HOME"]
    db = Database ( "%s/git/smodels/test/tinydb" % home )
    res = db.getExpResults ()
    for expRes in res:
        print ( expRes.globalInfo.url )

if __name__ == "__main__":
    main()
