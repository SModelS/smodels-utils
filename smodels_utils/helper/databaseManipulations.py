#!/usr/bin/env python3

""" module that contains a few methods to manipulate the database """

from smodels.experiment.databaseObj import Database

def combineResults( database, anas_and_SRs : dict, debug=False ):
    """ combine the <anas_and_SRs> results in <database>
        to a single result with a diagonal covariance matrix
    :param anas_and_SRs: dictionary with analysis Ids as keys and lists of signal regions
        as values, e.g.: { "ATLAS-SUSY-2016-07": ['2j_Meff_1200', '2j_Meff_1600'] }
    :returns: a combined ExpResults
    """
    import copy
    anaids = anas_and_SRs.keys()
    expResults = database.getExpResults( analysisIDs = anaids,
                                         dataTypes = [ "efficiencyMap" ] )
    datasets,datasetorder,covariance_matrix = [], [], []
    anaIds = []
    ctdses = 0
    n_datasets = 0
    for i,er in enumerate(expResults):
        anaId = er.globalInfo.id
        anaIds.append ( anaId )
        SRs = anas_and_SRs[anaId]
        for sr in SRs:
            ds = er.getDataset ( sr )
            if ds != None:
                n_datasets+=1

    ctds=0
    for i,er in enumerate(expResults):
        anaId = er.globalInfo.id
        anaIds.append ( anaId )
        SRs = anas_and_SRs[anaId]
        for sr in SRs:
            ds = er.getDataset ( sr )
            if ds != None:
                datasets.append ( ds )
            datasetorder.append ( ds.dataInfo.dataId )
            cov_row = [0.]*n_datasets
            cov_row[ctds]= ds.dataInfo.bgError**2
            ctds += 1
            covariance_matrix.append ( cov_row )
        #er.datasets = er.datasets[:1]

    if debug:
        print ( "[combineResults] cov_matrx", covariance_matrix )
        print ( "[combineResults] datasets", datasets )
        print ( "[combineResults] anaIds", anaIds )
    ## construct a fake result with these <n> datasets and and
    ## an nxn covariance matrix
    er = copy.deepcopy ( expResults[0] )
    er.datasets = datasets
    er.anaIds = anaIds
    er.globalInfo.datasetOrder = datasetorder
    er.globalInfo.covariance = covariance_matrix
    return er

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
    # dbverold = dbverold.replace(".","")
    db.subs[0].expResultList = filtered
    if invert:
        db.subs[0].txt_meta.databaseVersion = "fastlim" + dbverold
    db.subs = [ db.subs[0] ]
    print ( "[databaseManipulations] after removal of fastlim",len(db.expResultList),
            "results" )
    if not invert:
        db.txt_meta.hasFastLim = False
        db.txt_meta.databaseVersion = "fastlim" + dbverold # FIXME why?
        db.subs[0].pcl_meta.hasFastLim = False
    if picklefile not in [ None, "" ]:
        db.createBinaryFile( picklefile )
    return db

def removeNonAggregateFromDB ( db, invert = False, picklefile = "temp.pcl" ):
    """ remove results from database db for which we have an aggregated result
    :param db: database object
    :param invert: if True, then invert the selection, keep *only* nonaggregated
    :param picklefile: picklefile to store trimmed database
    """
    print ( "[databaseManipulations] before removal of nonaggregated",\
            len(db.expResultList), "results" )
    filtered = filterNonAggregatedFromList ( db.expResultList, invert )
    dbverold = db.databaseVersion
    db.subs[0].expResultList = filtered
    if invert:
        db.subs[0].txt_meta.databaseVersion = "nonaggregated" + dbverold
    db.subs = [ db.subs[0] ]
    print ( "[databaseManipulations] after removal of nonaggregated",\
            len(db.expResultList), "results" )
    if not invert:
        db.txt_meta.hasFastLim = False
        db.txt_meta.databaseVersion = dbverold
        db.subs[0].pcl_meta.hasFastLim = False
    if picklefile not in [ None, "" ]:
        db.createBinaryFile( picklefile )
    return db

def filterNonAggregatedFromList ( expResList, invert = False, really = True ):
    """ remove results from list of experimental list for which we have 
        an aggregated result
    :param expResList: list of experiment results
    :param invert: if True, then invert the selection, return *only* fastlim
    :param really: if False, then do not actually filter
    """
    if not really:
        return expResList
    ret = []
    aggs = set()
    maggs = []
    for er in expResList:
        Id =  er.globalInfo.id 
        if "-agg" in Id:
            aggs.add ( Id.replace("-agg","") )
            maggs.append ( er )
    print ( "aggs", aggs )
    endings = [ "-ma5", "-eff", "-adl", "-cm" ]
    for er in expResList:
        Id =  er.globalInfo.id 
        hasEnding = False
        for end in endings:
            if Id.endswith ( end ):
                hasEnding = True
                aId = Id [ :-len(end) ]
                if aId in aggs and invert:
                    ret.append ( er )
                if not aId in aggs and not invert:
                    ret.append ( er )
        if not hasEnding and not invert:
            ret.append ( er )
    if not invert: ## add the aggs
        for a in maggs:
            ret.append ( a )
    return ret

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
                print ( "[databaseManipulations] removing fastlim", gI.id )
            if ctr == 4:
                print ( "                        .... (and a few more) ... " )
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

def removeSupersededFromDB ( db, invert=False, outfile="temp.pcl" ):
    """ remove superseded results from database db
    :param invert: if true, then create superseded-only db
    :returns: database but stores it also in temp.pcl
    """
    print ( "[databaseManipulations] before removal of superseded",len(db.expResultList),\
            "results" )
    filteredList = []
    ctr = 0
    supers, newers = [], []
    olders = db.expResultList
    supers = filterSupersededFromList ( olders, invert )
    db.subs[0].expResultList = supers
    db.subs = [ db.subs[0] ]
    print ( "[databaseManipulations] after removal of superseded",len(db.expResultList),
            "results" )
    if invert:
        db.subs[0].databaseVersion = "superseded" + db.databaseVersion
    db.createBinaryFile( outfile )
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

    ctsuper = 0
    for er in olders:
        gI = er.globalInfo
        if hasattr ( gI, "supersededBy" ): # or gI.id in superseded:
            ctsuper += 1
            if ctsuper < 4:
                print ( "[databaseManipulations]",gI.id, "is superseded" )
            if ctsuper == 4:
                print ( "                        .... (and a few more) ... " )
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

if __name__ == "__main__":
    import os
    def pprint ( l ):
        for i, d in enumerate(l):
            print ( f"{i} {d.globalInfo.id}" )
    db = Database ( os.path.expanduser ( "~/git/smodels-database" )  )
    ers = db.expResultList
    pprint ( ers )
    newers = filterNonAggregatedFromList ( ers )
    print ( f"old {len(ers)} new {len(newers)}" )
    pprint ( newers )
    nonagg = filterNonAggregatedFromList ( ers, invert = True )
    print ( f"old {len(ers)} new {len(nonagg)}" )
    pprint ( nonagg )
