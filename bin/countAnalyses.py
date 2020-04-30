#!/usr/bin/env python3

"""
.. module:: countAnalyses
         :synopsis: Small script to produce a database statistics

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
import sys, colorama
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import TeV
from smodels.tools.smodelsLogging import setLogLevel
setLogLevel("debug")

def discussExperiment ( anas, experiment, title, verbose ):
    print ( colorama.Fore.GREEN + title + experiment + ":" + colorama.Fore.RESET )
    ianas = set()
    ul,em=0,0
    n_results = 0
    n_results_ul = 0
    n_results_em = 0
    for expRes in anas:
        Id = expRes.globalInfo.id
        Id = Id.replace("-agg","")
        contact = ""
        if hasattr ( expRes.globalInfo, "contact" ):
            contact = expRes.globalInfo.contact
        # print ( "id", Id )
        ianas.add ( Id )
        topos = set()
        for dataset in expRes.datasets:
            for i in dataset.txnameList:
                # print ( "validated=",i.validated )
                if i.validated not in [ True, "N/A", "n/a" ]:
                    continue
                topos.add ( i.txName )
        if expRes.datasets[0].dataInfo.dataType=="upperLimit":
            ul+=1
            n_results_ul += len ( topos )
        else:
            em+=1
            n_results_em += len ( topos )
        n_results += len ( topos )

    print ( "%d analyses." % len(ianas) )
    if verbose:
        print ( "   `- %s" % ( ", ".join(ianas) ) )
    print ( "%d results total" % n_results )
    print ( "%d upper limits analyses" % ul )
    print ( "%d efficiency map analyses" % em )
    print ( "%d upper limits results" % n_results_ul )
    print ( "%d efficiency map results" % n_results_em )

    print ()

def filterSqrts ( anas, sqrts ):
    sqrts = int ( sqrts)
    ret = []
    for ana in anas:
        contact = ""
        anaS = int ( ana.globalInfo.sqrts.asNumber(TeV) )
        if sqrts != anaS:
            continue
        ret.append ( ana )
    return ret

def filterFastlim ( anas, really=True, update="" ):
    if not really:
        return anas
    ret = []
    for ana in anas:
        contact = ""
        if hasattr ( ana.globalInfo, "contact" ):
            contact = getattr ( ana.globalInfo, "contact" )
        if update != "":
            lu = getattr ( ana.globalInfo, "lastUpdate" )
            from datetime import datetime
            after = datetime.strptime ( update, "%Y/%m/%d" )
            this = datetime.strptime ( lu, "%Y/%m/%d" )
            if this < after:
                continue
        if "fastlim" in contact:
            continue
        ret.append ( ana )
    return ret

def discuss ( superseded, filter_fastlim, db, update, sqrts, verbose ):
    print ()
    print ( "---------------" )
    title = "Excluding superseded results, "
    if superseded:
        title = "Including superseded results, "
    if sqrts != "13":
        if filter_fastlim:
                title += "without FastLim, " 
        else:
            title += "with FastLim, "
    anas = db.getExpResults( useSuperseded=superseded )
    if sqrts == "all":
        title += "all runs, "
    else:
        title += "%s TeV only, " % sqrts
    if sqrts != "all":
        anas = filterSqrts ( anas, sqrts )
    anas = filterFastlim ( anas, filter_fastlim, update )
    cms,atlas=[],[]
    for expRes in anas:
        Id=expRes.globalInfo.id
        if "CMS" in Id: cms.append ( expRes )
        if "ATLAS" in Id: atlas.append ( expRes )
    discussExperiment ( cms, "CMS", title, verbose )
    discussExperiment ( atlas, "ATLAS", title, verbose )

def countTopos ( superseded, filter_fastlim, db, update, verbose=True ):
    e = db.getExpResults( useSuperseded = superseded )
    anas = filterFastlim ( e, filter_fastlim, update )
    topos = set()
    topos_roff = set()
    for i in anas:
        for t in i.getTxNames():
            topos.add ( t.txName )
            topos_roff.add ( t.txName.replace("off","") )
    print ( "%d topologies (%d, not counting off-shell separately)" % \
            ( len(topos), len(topos_roff) ) )
    if verbose:
        print ( ", ".join ( sorted ( topos ) ) )

def main():
    import argparse
    argparser = argparse.ArgumentParser( description=
                                         'Count analyses in different ways' )
    argparser.add_argument ( '-s', '--superseded', help='show superseded results (yes/no/both) [both]',
              type=str, default="both" )
    argparser.add_argument ( '-u', '--update', help='consider entries only after this date (yyyy/mm/dd)',
              type=str, default="" )
    argparser.add_argument ( '-f', '--fastlim', help='show fastlim results (yes/no/both) [both]',
              type=str, default="both" )
    argparser.add_argument ( '-S', '--sqrts', help='select sqrts (8/13/all) [all]',
              type=str, default="both" )
    argparser.add_argument ( '-v', '--verbose', help='be verbose', action='store_true' )
    argparser.add_argument ( '-t', '--topologies', help='list topologies, also', action='store_true' )
    argparser.add_argument ( '-d', '--database', help='path to (or name of) database [official_fastlim]',
              type=str,default='official_fastlim' )
    args = argparser.parse_args()
    db = Database ( args.database )
    ss = [ True, False ]
    fl = [ True, False ]
    sqrts = args.sqrts.lower()
    if sqrts in [ "*" ]:
        sqrts = "all"
    if args.superseded.lower() in [ "yes", "true" ]: ss = [ True ]
    if args.superseded.lower() in [ "no", "false" ]: ss = [ False ]
    if args.fastlim.lower() in [ "yes", "true" ]: fl = [ False ]
    if args.fastlim.lower() in [ "no", "false" ]: fl = [ True ]
    for filter_fastlim in fl:
        for superseded in ss:
            discuss ( superseded, filter_fastlim, db, args.update, sqrts, args.verbose )
            if args.topologies:
                countTopos ( superseded, filter_fastlim, db, args.update, args.verbose )
if __name__ == '__main__':
    main()
