#!/usr/bin/env python3

""" simple script to create smodels-database.json that will be used
to mark SModelS entries at hepdata """

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
    for er in expResList:
        gI = er.globalInfo
        # print ( gI.id )
        coll = getCollaboration ( gI.id )
        dses = er.datasets
        resultType = "EM"
        SRcomb = "None"
        if hasattr ( gI, "covariance" ):
            SRcomb = "SLv1"
        if hasattr ( gI, "jsonFiles" ):
            SRcomb = "pyhf"
        if len(dses) == 1 and dses[0].dataInfo.dataId == None:
            resultType = "UL"
        signatureType = "prompt"
        if hasattr ( gI, "type" ):
            signatureType = gI.type
        entry = { "exp": coll, "anaID": gI.id, "resultType": resultType }
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
                    entry["inspire"]=tmp
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
