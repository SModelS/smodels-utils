#!/usr/bin/env python3

def create():
    from smodels.experiment.databaseObj import Database
    from smodels_utils.helper.various import getCollaboration
    db = Database ( "official" )
    expResList = db.getExpResults()
    f=open("smodels-database.json","wt")
    for er in expResList:
        print ( er )
        gI = er.globalInfo
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
        for ds in dses:
            if hasattr ( ds.dataInfo, "thirdMoment" ):
                SRcomb = "SLv2"
            for txn in ds.txnameList:
                if hasattr ( txn, "finalState" ):
                    fS = str(txn.finalState)
                    if "HSCP" in fS:
                        signatureType = "longlived"
                    if "RHadron" in fS:
                        signatureType = "longlived"
                dU = txn.dataUrl
                if dU != None and "/ins" in dU:
                    p1 = dU.find("/ins")
                    tmp = dU[p1+4:]
                    p2 = tmp.find("/")
        entry = { "exp": coll, "anaID": gI.id, "resultType": resultType,
                  "SRcomb": SRcomb }
        if hasattr ( gI, "arxiv" ):
            ar = gI.arxiv
            p1 = ar.rfind("/")
            entry["arXiv"]=ar[p1+1:]
        if hasattr ( gI, "prettyName" ):
            entry["prettyName"]=gI.prettyName
        if hasattr ( gI, "publicationDOI" ):
            doi = gI.publicationDOI
            doi = doi.replace("http://doi.org/","")
            entry["paper"]=doi
        entry["wiki"]=gI.url
        if hasattr ( gI, "publication" ):
            entry["publication"]=gI.publication
        f.write ( str(entry).replace("'",'"')+"\n" )
    f.close()
        

create()
