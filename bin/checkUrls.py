#!/usr/bin/python

""" simple python script to check all urls in the database, to make sure
    the webpages exist """

from __future__ import print_function
try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

from smodels.experiment.databaseObj import Database
import re

db=Database ( "/home/walten/git/smodels-database" )

log=open("urls.log", "w" )

def Print ( line ):
    print ( line )
    log.write ( line + "\n" )

def checkUrl ( url, id ):
    if url == "Not defined":
        return
    Print ( "Now checking %s: %s" % (id, url ) )
    f=urlopen ( url )
    lines=f.readlines()
    f.close()
    Print ( " done. %d lines." % ( len(lines) ) )
    Print ( "first line: %s" % lines[0][:30] )

def checkUrls ( urls, id ):
    ret = urls
    if type ( urls ) == str:
        ret = urls.split ( ";" )
#        ret = re.findall ( r"[^,;]+", urls )
    for url in ret:
        checkUrl ( url, id )

e = db.getExpResults( useNonValidated=True, useSuperseded=True )
for expRes in e:
    id = expRes.globalInfo.id
    if hasattr ( expRes.globalInfo, "publication" ):
        checkUrls ( expRes.globalInfo.publication, id )
    if hasattr ( expRes.globalInfo, "arxiv" ):
        checkUrls ( expRes.globalInfo.arxiv, id )
    txnames = expRes.getTxNames()
    for t in txnames:
        if hasattr ( t, "figureUrl" ):
            Print ( "\n\nfigureUrl=%s" % t.figureUrl )
            checkUrls ( t.figureUrl, id )
        if hasattr ( t, "dataUrl" ):
            Print ( "\n\ndataUrl=%s" % t.dataUrl )
            checkUrls ( t.dataUrl, id )

log.close()
