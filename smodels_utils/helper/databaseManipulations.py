#!/usr/bin/env python3

""" module that contains a few methods to manipulate the database """

from smodels.experiment.databaseObj import Database

def filterSuperseded ( expRes, invert=False ):
    """ filter out superseded results,
    :returns: list of non-superseded results if invert is False, else return
              list of superseded results
    """ 
    ret, ss = [], []
    for er in expRes:
        if hasattr ( er.globalInfo, "supersededBy" ):
            ss.append ( er )
        else:
            ret.append ( er )
    if invert:
        return ss
    return ret

def createSuperseded ( infile, outfile = "./superseded.pcl", filtered = False ):
    """ create the superseded pickle file from a database path
    :param filtered: if true, then remove superseded entries instead of the other way round
    :param outfile: write to outfile. If None or "", then to write out.
    :returns: list of exp results
    """
    db = Database ( infile )
    olders = db.expResultList
    newers, supers, fastlims = [], [], []
    superseded = []
    for er in olders:
        gI = er.globalInfo
        if hasattr ( gI, "supersedes" ):
            superseded.append ( gI.supersedes )

    for er in olders:
        gI = er.globalInfo
        if hasattr ( gI, "supersededBy" ): # or gI.id in superseded:
            print ( "[databaseManipulations]",gI.id, "is superseded" )
            newers.append ( er )
        elif hasattr ( gI, "contact" ) and "fastlim" in gI.contact.lower():
                fastlims.append ( er )
        else:
            supers.append ( er )
            # print ( "[databaseManipulations] keep", gI.id )
    if filtered:
        db.subs[0].expResultList = supers
    else:
        db.subs[0].expResultList = newers
    db.subs = [ db.subs[0] ]
    print ( "[databaseManipulations] storing", len(db.expResultList), "superseded results" )
    sstring = "superseded"
    if filtered:
        sstring = "" # "nosuperseded"
    db.subs[0].txt_meta.databaseVersion = db.databaseVersion + sstring
    print ( "[databaseManipulations] writing to", outfile )
    if outfile not in  [ "", None ]:
        db.createBinaryFile ( outfile )

    return db.expResultList
