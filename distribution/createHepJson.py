#!/usr/bin/env python3

""" simple script to create smodels-database.json that will be used
to mark SModelS entries at hepdata """

import os, sys, time
from typing import Union

def merge ( entry1, entry2, anaId ):
    """ merge two entries """
    for k,v in entry2.items():
        if not k in entry1:
            entry1[k]=v
            continue
        if k == "resultType" and v != entry1[k]:
            if v in entry1[k]: ## already in!
                continue
            entry1[k]+=f",{v}"
            continue
        if k == "path" and v != entry1[k]:
            if v in entry1[k]: ## already in!
                continue
            entry1[k]+=f",{v}"
            continue
        if k == "SRcomb":
            if v in [ None, "None" ]: ## skip
                continue
            entry1[k] = v
            # print ( f"merging {entry1} and {entry2}: {entry1}" )
            continue
        if k == "prettyName":
            # take the shorter!
            if v in entry1[k]:
                entry1[k]=v
        if v != entry1[k]:
            print ( f"[createHepJson] entry {k} differs for {anaId}: '{v}' != '{entry1[k]}'" )
            print ( f"[createHepJson] will use {entry1[k]}" )
    return entry1

def getHepData ( nr ):
    hepdata = f"https://www.hepdata.net/record/ins{nr}"
    if not os.path.exists ( "cache" ):
        os.mkdir ( "cache" )
    cachefile = f"cache/{nr}"
    if os.path.exists ( cachefile ):
        try:
            with open ( cachefile, "rt" )  as f:
                content = f.read()
                f.close()
                return content
        except Exception as e:
            print ( f"cannot read cachefile {cachefile}: {e}" )
    import requests
    req = requests.request ( url=hepdata, method="GET" )
    try:
        content = eval(req.content)
        ret = content["@id"]
        with open ( cachefile, "wt" ) as f:
            f.write ( ret )
            f.close()
        return ret
    except SyntaxError as e:
        print ( f"cannot read content for {nr}: {e}" )
        return hepdata

def header(f, db ):
    """ header of the json file """
    import smodels
    f.write ( "{\n" )
    f.write ( '    "tool": "SModelS",\n' )
    # ver = smodels.installation.version()
    ver = db.databaseVersion
    f.write (f'    "version": "{ver}",\n' )
    f.write (f'    "created": "{time.asctime()}",\n' )
    f.write ( '    "link_types": [ "implementation", "validation", "publication", "arXiv" ],\n' )
    f.write ( '    "url_templates": {\n' )
    f.write ( '        "implementation": "https://github.com/SModelS/smodels-database-release/tree/main/%s",\n' )
    f.write ( '        "validation": "https://smodels.github.io/docs/Validation#%s",\n' )
    f.write ( '        "publication": "https://doi.org/%s",\n' )
    f.write ( '        "arXiv": "https://arxiv.org/abs/%s"\n' )
    f.write ( '    },\n' )
    f.write ( '    "analyses" : {\n' )

def footer(f):
    """ footer of the json file """
    f.write ( '    }\n' )
    f.write ( '}\n' )

def getInspireFromWebPage ( gI ) -> Union[None,int]:
    """ try to get the inspire number from the wiki page """
    if not hasattr ( gI, "url" ):
        return None
    import requests
    r = requests.get ( gI.url )
    txt = r.text
    ## first search for inspirehep.net/record links
    p1 = txt.find("://inspirehep.net/record/")
    while p1 > 0 and len(txt)>0:
        p1 = txt.find("://inspirehep.net/record/")
        txt = txt[p1+25:]
        p2 = txt.find('"')
        tmp = txt[:p2]
        try:
            tmp = int(tmp)
            return tmp
        except ValueError as e:
            pass
    txt = r.text
    ## now try  hepdata.net/record links
    p1 = txt.find("://www.hepdata.net/record/ins")
    while p1 > 0 and len(txt)>0:
        p1 = txt.find("://www.hepdata.net/record/ins")
        txt = txt[p1+29:]
        p2 = txt.find('"')
        tmp = txt[:p2]
        try:
            tmp = int(tmp)
            return tmp
        except ValueError as e:
            pass
            # print ( e )
    return None

def collectEntries( expResList ) -> dict:
    from smodels_utils.helper.various import getCollaboration
    entries = {}
    for i,er in enumerate(expResList):
        gI = er.globalInfo
        print ( f"[createHepJson] {i+1}/{len(expResList)}: {gI.id}" )
        coll = getCollaboration ( gI.id )
        dses = er.datasets
        resultType = "EM"
        SRcomb = None
        if hasattr ( gI, "covariance" ):
            SRcomb = "SLv1"
        if hasattr ( gI, "jsonFiles" ):
            SRcomb = "pyhf"
        if len(dses) == 1 and dses[0].dataInfo.dataId == None:
            resultType = "UL"
        Id = gI.id
        for ext in [ "-ma5", "-ewk", "-strong", "-agg", "-hino", "-multibin", "-exclusive" ]:
           Id = Id.replace(ext,"")
        entry = { "exp": coll, "anaID": Id, "resultType": resultType }
        path = gI.path.replace("/globalInfo.txt","")
        p1 = path.rfind("/")
        entry["path"]=path[p1+1:]
        # signatureType = "prompt"
        if hasattr ( gI, "type" ):
            # signatureType = gI.type
            # entry["signatureType"]=signatureType
            entry["signatureType"]=gI.type
        for ds in dses:
            if hasattr ( ds.dataInfo, "thirdMoment" ):
                SRcomb = "SLv2"
            for txn in ds.txnameList:
                if not hasattr ( txn, "dataUrl" ):
                    continue
                dU = txn.dataUrl
                if dU != None and "/ins" in dU:
                    p1 = dU.find("/ins")
                    tmp = dU[p1+4:]
                    p2 = tmp.find("/")
                    if p2 > -1 :
                        tmp = tmp[:p2]
                    p2 = tmp.find("?")
                    if p2 > -1 :
                        tmp = tmp[:p2]
                    p2 = tmp.find("_")
                    if p2 > -1 :
                        tmp = tmp[:p2]
                    # print ( "tmp", dU, "->", tmp )
                    inspire = tmp
                    hepdata = getHepData  ( inspire )
                    # inspire = f"https://inspirehep.net/literature/{tmp}"
                    entry["hepdata"]=hepdata
                    entry["inspire"]=inspire
                    break
        if SRcomb != None:
            entry["SRcomb"]=SRcomb
        if hasattr ( gI, "arxiv" ):
            ar = gI.arxiv
            p1 = ar.rfind("/")
            entry["arXiv"]=ar[p1+1:]
        if hasattr ( gI, "prettyName" ):
            entry["prettyName"]=gI.prettyName
        if True and hasattr ( gI, "publication" ):
            entry["paper"]=gI.publication
        if hasattr ( gI, "publicationDOI" ):
            doi = gI.publicationDOI
            # doi = doi.replace("http://doi.org/","")
            doi = doi.replace("https://doi.org/","")
            entry["publication"]=doi
        wiki = gI.url
        if ";" in wiki:
            wiki = wiki.find(";")
        entry["wiki"]=wiki
        if not "inspire" in entry:
            inspire = getInspireFromWebPage ( gI )
            if inspire != None:
                entry["inspire"]=inspire
                hepdata = getHepData  ( inspire )
                entry["hepdata"]= hepdata
        if Id in entries:
            merged = merge ( entries[Id], entry, Id )
            entries[Id] = merged
        else:
            entries[Id] = entry
        print ( f"[createHepJson] {entry}" )
    return entries

def body(f,expResList):
    entries = collectEntries ( expResList )
    from smodels_utils.helper.various import getSqrts
    first = True

    for anaId,entry in entries.items():
        if not "inspire" in entry:
            continue
        if not first:
            f.write ( ',\n' )
        first = False
        inspire = entry["inspire"]
        f.write ( f'        "{inspire}": {{\n' )
        sqrts = getSqrts ( anaId )
        exp = entry["exp"]
        resultTypes = entry["resultType"].lower().split(",")
        implementations = []
        for path in entry["path"].split(","):
            implementation = f'"{sqrts}TeV/{exp}/{path}/"'
            implementations.append ( implementation )
        simplementations = ", ".join ( implementations )
        f.write ( f'            "implementation": [{simplementations}],\n' )
        validations = []
        for resultType in resultTypes:
            validations.append ( f'"{anaId}_{resultType}"' )
        svalidations = ", ".join(validations)
        f.write ( f'            "validation": [{svalidations}]' )
        #for label in [ "publication", "anaID" ]:
        #    if label in entry:
        #        f.write ( ',\n' )
        #        l = entry[label]
        #        f.write ( f'            "{label}": ["{l}"]' )
        for label in [ "publication", "anaID", "arXiv", "SRcomb", "signatureType", "prettyName", "wiki" ]:
            if label in entry:
                f.write ( ',\n' )
                l = entry[label]
                f.write ( f'            "{label}": "{l}"' )
        f.write ( '\n        }' )
    f.write('\n' )

    #  [ "exp", "anaID", "arXiv", "inspire", "paper", "publication", "hepdata", "resultType", "SRcomb", "signatureType", "prettyName", "wiki"]

def create( dbpath : os.PathLike, outputfile : os.PathLike ):
    """ create smodels-analyses.json """
    from smodels.experiment.databaseObj import Database
    if not os.path.exists ( dbpath ) and not dbpath in [ "official", "superseded",
            "fastlim", "full_llhds", "nonaggregated", "backup", "latest",
            "backupunittest", "unittest", "debug", ]:
        print ( f"[createHepJson] {dbpath} not found" )
        sys.exit()
    db = Database ( dbpath )
    expResList = db.getExpResults()
    f=open(outputfile,"wt")
    header(f, db )
    body(f,expResList)
    footer(f)
    f.close()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="simple script to create the smodels-analyses.json files" )
    ap.add_argument('-d', '--dbpath',
            help='path to database [../../smodels-database/]', 
            default='../../smodels-database/')
    ap.add_argument('-o', '--outputfile',
            help='path to database [smodels-analyses.json]', 
            default='smodels-analyses.json')
    args = ap.parse_args()
    # args.dbpath = "official"
    create( args.dbpath, args.outputfile )
