#!/usr/bin/env python3

""" module that contains a few methods to manipulate the database """

from smodels.experiment.databaseObj import Database

def removeFastLimFromDB ( db, invert = False, picklefile = "temp.pcl" ):
    """ remove fastlim results from database db 
    :param db: database object
    :param invert: if True, then invert the selection, keep *only* fastlim
    :param picklefile: picklefile to store fastlim-free database
    """
    print ( "[databaseManipulations] before removal of fastlim",len(db.expResultList),\
            "results" )
    filtered = filterFastLimFromList ( db.expResultList, invert )
    dbverold = db.databaseVersion
    dbverold = dbverold.replace(".","")
    db.subs[0].expResultList = filtered
    if invert:
        db.subs[0].txt_meta.databaseVersion = "fastlim" + dbverold
    db.subs = [ db.subs[0] ]
    print ( "[databaseManipulations] after removal of fastlim",len(db.expResultList),
            "results" )
    if not invert:
        db.txt_meta.hasFastLim = False
        db.txt_meta.databaseVersion = "fastlim" + dbverold
        db.subs[0].pcl_meta.hasFastLim = False
    if picklefile not in [ None, "" ]:
        db.createBinaryFile( picklefile )
    return db

def filterFastLimFromList ( expResList, invert = False, really = True, update = None ):
    """ remove fastlim results from list of experimental list
    :param expResList: list of experiment results
    :param invert: if True, then invert the selection, return *only* fastlim
    :param really: if False, then do not actually filter
    :param update: consider entries only after this date (yyyy/mm/dd)
    """
    if not really:
        return expResList
    fastlimList,filteredList = [], []
    ctr = 0
    for e in expResList:
        gI = e.globalInfo
        if update not in [ "" , None ]:
            lu = getattr ( e.globalInfo, "lastUpdate" )
            if type(lu) != str:
                print ( "[databaseManipulations] we have lastUpdate that reads %s in %s" % \
                        (lu, e.globalInfo.id ) )
                import sys
                sys.exit(-1)
            from datetime import datetime
            after = datetime.strptime ( update, "%Y/%m/%d" )
            this = datetime.strptime ( lu, "%Y/%m/%d" )
            if this < after:
                continue
        if hasattr ( gI, "contact" ) and "fastlim" in gI.contact.lower():
            ctr+=1
            if ctr < 4:
                print ( "removing", gI.id )
            fastlimList.append ( e )
        else:
            filteredList.append ( e )
    if invert:
        return fastlimList
    return filteredList

def filterSqrtsFromList ( expResultList, sqrts, invert=False ):
    """ filter list of exp results by sqrts
    :param sqrts: sqrts (int) to keep
    :param invert: if True, then invert, discard the given sqrts
    :returns: list of exp results, all at sqrts TeV
    """
    sqrts = int(sqrts)
    ret = []
    for ana in expResultList:
        contact = ""
        ress = int ( ana.globalInfo.sqrts.asNumber(TeV) )
        if invert and sqrts == ress:
            continue
        if not invert and sqrts != ress:
            continue
        ret.append ( ana )
    return ret

def removeSupersededFromDB ( db ):
    """ remove superseded results from database db """
    print ( "[databaseManipulations] before removal of superseded",len(db.expResultList),\
            "results" )
    filteredList = []
    ctr = 0
    superseded, supers, newers = [], [], []
    olders = db.expResultList
    supers = filterSupersededFromList ( olders )
    db.subs[0].expResultList = supers
    db.subs = [ db.subs[0] ]
    print ( "[databaseManipulations] after removal of superseded",len(db.expResultList),
            "results" )
    db.createBinaryFile( "temp.pcl" )
    return db

def filterSupersededFromList ( expRes, invert=False ):
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

def createSupersededPickle ( infile, outfile = "./superseded.pcl", filtered = False ):
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
