#!/usr/bin/env python

"""
.. module:: countAnalyses
         :synopsis: Small script to produce a database statistics

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
import sys
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
setLogLevel("debug")

def discussExperiment ( anas, experiment ):
    print ( experiment )
    ianas = []
    ul,em=0,0
    n_results = 0
    n_results_ul = 0
    n_results_em = 0
    for expRes in anas:
        Id = expRes.globalInfo.id
        contact = ""
        if hasattr ( expRes.globalInfo, "contact" ):
            contact = expRes.globalInfo.contact
        #if not "SModelS" in contact:
        #    continue
        if not Id in ianas:
            ianas.append ( Id )
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
    print ( "%d results total" % n_results )
    print ( "%d upper limits analyses" % ul )
    print ( "%d efficiency map analyses" % em )
    print ( "%d upper limits results" % n_results_ul )
    print ( "%d efficiency map results" % n_results_em )

    print ()

def filter ( anas, really=True, update="" ):
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

def discuss ( superseded, filter_fastlim, db, update ):
    print ()
    print ( "---------------" )
    if superseded:
        print ( "Including superseded results" )
    else:
        print ( "Excluding superseded results" )
    if filter_fastlim:
        print ( "Without FastLim" )
    else:
        print ( "With FastLim" )
    anas = db.getExpResults( useSuperseded=superseded )
    anas = filter ( anas, filter_fastlim, update )
    cms,atlas=[],[]
    for expRes in anas:
        Id=expRes.globalInfo.id
        if "CMS" in Id: cms.append ( expRes )
        if "ATLAS" in Id: atlas.append ( expRes )
    discussExperiment ( cms, "CMS" )
    discussExperiment ( atlas, "ATLAS" )

def countTopos ( superseded, filter_fastlim, db, update ):
    e = db.getExpResults( useSuperseded = superseded )
    anas = filter ( e, filter_fastlim, update )
    topos = set()
    topos_roff = set()
    for i in anas:
        for t in i.getTxNames():
            topos.add ( t.txName )
            topos_roff.add ( t.txName.replace("off","") )
    print ( "%d topologies (%d, not counting off-shell separately)" % \
            ( len(topos), len(topos_roff) ) )

def main():
    import argparse
    argparser = argparse.ArgumentParser( description=
                                         'Count analyses in different ways' )
    argparser.add_argument ( '-s', '--superseded', help='show superseded results (yes/no/both)',
              type=str, default="both" )
    argparser.add_argument ( '-u', '--update', help='consider entries only after this date (yyyy/mm/dd)',
              type=str, default="" )
    argparser.add_argument ( '-f', '--fastlim', help='show fastlim results (yes/no/both)',
              type=str, default="both" )
    argparser.add_argument ( '-d', '--database', help='path to database',
              type=str,default='http://smodels.hephy.at/database/official112' )
    args = argparser.parse_args()
    db = Database ( args.database )
    ss = [ True, False ]
    fl = [ True, False ]
    if args.superseded.lower() in [ "yes", "true" ]: ss = [ True ]
    if args.superseded.lower() in [ "no", "false" ]: ss = [ False ]
    if args.fastlim.lower() in [ "yes", "true" ]: fl = [ False ]
    if args.fastlim.lower() in [ "no", "false" ]: fl = [ True ]
    for filter_fastlim in fl:
        for superseded in ss:
            discuss ( superseded, filter_fastlim, db, args.update )
            countTopos ( superseded, filter_fastlim, db, args.update )
if __name__ == '__main__':
    main()
