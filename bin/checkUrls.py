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
    log.write ( f"{line}\n" )

def checkUrl ( url, id ):
    if url in [ "Not defined", None, "None" ]:
        return
    Print ( f"Now checking {id}: {url}" )
    f=urlopen ( url )
    lines=f.readlines()
    f.close()
    Print ( f" done. {len(lines)} lines." )
    Print ( f"first line: {lines[0][:30]}" )

def checkUrls ( urls, id ):
    if urls == None:
        return
    ret = urls
    if type ( urls ) == str:
        ret = urls.split ( ";" )
#        ret = re.findall ( r"[^,;]+", urls )
    for url in ret:
        checkUrl ( url, id )

e = db.getExpResults( useNonValidated=True, useSuperseded=True )
for expRes in e:
    id = expRes.globalInfo.id
    resume=False
    resume = True ## makes it possible to resume at later stage,
    ## if set to False
    if not resume and not "ATLAS-SUSY-2013-09" in id:
        continue
    resume = True
    if hasattr ( expRes.globalInfo, "publication" ):
        checkUrls ( expRes.globalInfo.publication, id )
    if hasattr ( expRes.globalInfo, "arxiv" ):
        checkUrls ( expRes.globalInfo.arxiv, id )
    txnames = expRes.getTxNames()
    for t in txnames:
        if hasattr ( t, "figureUrl" ):
            Print ( f"\n\nfigureUrl={t.figureUrl}" )
            checkUrls ( t.figureUrl, id )
        if hasattr ( t, "dataUrl" ):
            Print ( f"\n\ndataUrl={t.dataUrl}" )
            checkUrls ( t.dataUrl, id )

log.close()
