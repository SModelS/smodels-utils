#!/usr/bin/env python3

""" simple script to create smodels-database.json that will be used
to mark SModelS entries at hepdata """

import os

def merge ( entry1, entry2, anaId ):
    """ merge two entries """
    for k,v in entry2.items():
        if not k in entry1:
            entry1[k]=v
            continue
        if k == "resultType" and v != entry1[k]:
            entry1[k]+=f",{v}"
            continue
        if k == "SRcomb":
            if v in [ None, "None" ]: ## skip
                continue
            entry1[k] = v
            # print ( f"merging {entry1} and {entry2}: {entry1}" )
            continue
        if v != entry1[k]:
            print ( f"[createHepJson] entry {k} differs for {anaId}: '{v}' != '{entry1[k]}'" )
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

def create():
    """ create the json """
    from smodels.experiment.databaseObj import Database
    from smodels_utils.helper.various import getCollaboration
    dbpath = "official"
    dbpath = "../../smodels-database/"
    db = Database ( dbpath )
    expResList = db.getExpResults()
    f=open("smodels-database.json","wt")
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
        entry = { "exp": coll, "anaID": gI.id, "resultType": resultType }
        # signatureType = "prompt"
        if hasattr ( gI, "type" ):
            # signatureType = gI.type
            # entry["signatureType"]=signatureType
            entry["signatureType"]=gI.type
        for ds in dses:
            if hasattr ( ds.dataInfo, "thirdMoment" ):
                SRcomb = "SLv2"
            for txn in ds.txnameList:
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
                    # print ( "tmp", dU, "->", tmp )
                    hepdata = getHepData  ( tmp )
                    inspire = f"https://inspirehep.net/literature/{tmp}"
                    entry["hepdata"]=hepdata
                    entry["inspire"]=inspire
        if SRcomb != None:
            entry["SRcomb"]=SRcomb
        if hasattr ( gI, "arxiv" ):
            ar = gI.arxiv
            p1 = ar.rfind("/")
            entry["arXiv"]=ar[p1+1:]
        if hasattr ( gI, "prettyName" ):
            entry["prettyName"]=gI.prettyName
        if False and hasattr ( gI, "publication" ):
            entry["paper"]=gI.publication
        if hasattr ( gI, "publicationDOI" ):
            doi = gI.publicationDOI
            # doi = doi.replace("http://doi.org/","")
            doi = doi.replace("https://doi.org/","")
            entry["paperDOI"]=doi
        entry["wiki"]=gI.url
        if gI.id in entries:
            merged = merge ( entries[gI.id], entry, gI.id )
            entries[gI.id] = merged
        else:
            entries[gI.id] = entry
    for anaId,entry in entries.items():
        f.write ( str(entry).replace("'",'"')+"\n" )
    f.close()

if __name__ == "__main__":
    create()
