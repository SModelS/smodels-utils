#!/usr/bin/env python3

"""
.. module:: countAnalyses
         :synopsis: Small script to produce a database statistics

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
import sys
from smodels.experiment.databaseObj import Database
from smodels.base.physicsUnits import TeV
from smodels.base.smodelsLogging import setLogLevel
from smodels_utils.helper import databaseManipulations as manips
from smodels_utils.helper.various import removeAnaIdSuffices
from smodels_utils.helper.terminalcolors import *
setLogLevel("debug")

def discussExperiment ( anas, experiment, title, verbose ):
    print ( f"{GREEN}{title}{experiment}:{RESET}" )
    ianas = set()
    ul,em=0,0
    n_results = 0
    n_results_ul = 0
    n_results_em = 0
    for expRes in anas:
        Id = removeAnaIdSuffices ( expRes.globalInfo.id )
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

    print ( f"{len(ianas)} analyses." )
    if verbose:
        print ( f"   `- {', '.join(ianas)}" )
    print ( f"{int(n_results)} results total" )
    print ( f"{int(ul)} upper limits analyses" )
    print ( f"{int(em)} efficiency map analyses" )
    print ( f"{int(n_results_ul)} upper limits results" )
    print ( f"{int(n_results_em)} efficiency map results" )

    print ()

def discuss ( db, update, sqrts, verbose, lumi ):
    print ()
    print ( "---------------" )
    title = ""
    if lumi != None:
        title += f"lumi>{lumi}/fb, "
    anas = db.getExpResults( )
    if sqrts == "all":
        title += "all runs, "
    else:
        title += f"{sqrts} TeV only, "
    if sqrts not in [ "all", "both" ]:
        anas = manips.filterSqrtsFromList ( anas, sqrts )
    anas = manips.filterByLumi  ( anas, lumi, invert=False )
    cms,atlas=[],[]
    for expRes in anas:
        Id=expRes.globalInfo.id
        if "CMS" in Id: cms.append ( expRes )
        if "ATLAS" in Id: atlas.append ( expRes )
    discussExperiment ( cms, "CMS", title, verbose )
    discussExperiment ( atlas, "ATLAS", title, verbose )

def countTopos ( superseded, filter_fastlim, db, update, verbose=True ):
    e = db.getExpResults( useSuperseded = superseded )
    anas = manips.filterFastlimFromList ( e, False, filter_fastlim, update )
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
    argparser.add_argument ( '-u', '--update', help='consider entries only after this date (yyyy/mm/dd)',
              type=str, default="" )
    argparser.add_argument ( '-S', '--sqrts', help='select sqrts (8/13/all) [all]',
              type=str, default="all" )
    argparser.add_argument ( '-L', '--lumi', help='require a minimum lumi, in 1/fb [None]',
              type=float, default=None )
    argparser.add_argument ( '-v', '--verbose', help='be verbose', action='store_true' )
    argparser.add_argument ( '-t', '--topologies', help='list topologies, also', action='store_true' )
    argparser.add_argument ( '-d', '--database', help='path to (or name of) database [official]',
              type=str,default='official' )
    args = argparser.parse_args()
    db = Database ( args.database )
    ss = [ True, False ]
    fl = [ True, False ]
    sqrts = args.sqrts.lower()
    if sqrts in [ "*" ]:
        sqrts = "all"
    discuss ( db, args.update, sqrts, args.verbose, args.lumi )
    if args.topologies:
        countTopos ( db, args.update, args.verbose )
if __name__ == '__main__':
    main()
