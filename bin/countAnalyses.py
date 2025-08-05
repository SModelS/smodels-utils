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

from typing import Union
# setLogLevel("debug")

def discussExperiment ( anas : list, experiment : str, title : str, verbose : bool ):
    print ( f"{GREEN}{title}{experiment}:{RESET}" )
    ianas = set()
    ianas_MET = set()
    ul,em=set(),set()
    n_maps = 0
    n_maps_ul = 0
    n_maps_em = 0
    n_maps_em_MET = 0
    n_datasets = 0
    n_datasets_sronly = 0
    em_MET=set()
    n_datasets_MET = 0
    for expRes in anas:
        Id = removeAnaIdSuffices ( expRes.globalInfo.id )
        ianas.add ( Id )
        ulType = False
        if expRes.datasets[0].dataInfo.dataType=="upperLimit":
            ul.add ( Id )
            ulType = True
        else:
            em.add ( Id )
        for dataset in expRes.datasets:
            topos = set()
            topos_MET = set()
            hasMET = False
            for i in dataset.txnameList:
                if hasattr ( i, "finalState" ) and i.finalState is not None:
                    for fs in i.finalState:
                        if fs == "MET":
                            hasMET = True
                if "PV" in i.constraint and "MET" in i.constraint:
                    hasMET = True
                if i.validated in [ True, "N/A", "n/a" ]:
                    topos.add ( i.txName )
                    if hasMET:
                        topos_MET.add ( i.txName )
                else:
                    print ( f"[discussExperiment] {expRes.globalInfo.id}:{dataset.dataInfo.dataId}:{i} validated {i.validated}" )
            if hasMET:
                ianas_MET.add ( Id )
            if not ulType and hasMET:
                em_MET.add ( Id )
            if len(topos)>0 and ulType == False:
                n_datasets += 1
                if not dataset.dataInfo.dataId.startswith ( "CR_" ):
                    n_datasets_sronly += 1
                if hasMET:
                    n_datasets_MET += 1
                if verbose:
                    print ( f"[countAnalyses] adding #{n_datasets} {Id}:{dataset.dataInfo.dataId}" )
            if dataset.dataInfo.dataType=="upperLimit":
                n_maps_ul += len ( topos )
            else:
                n_maps_em += len ( topos )
                n_maps_em_MET += len ( topos_MET )
            n_maps += len ( topos )

    print ( f"{len(ianas)} analyses." )
    if verbose:
        print ( f"   `- {', '.join(ianas)}" )
    print ( f"{len(ianas_MET)} analyses with MET." )
    print ( f"{n_maps} maps total" )
    print ( f"{len(ul)} upper limits analyses" )
    print ( f"{len(em)} efficiency map analyses" )
    print ( f"{len(em_MET)} efficiency map analyses with MET" )
    print ( f"{n_maps_ul} upper limit maps" )
    print ( f"{n_maps_em} efficiency maps" )
    print ( f"{n_maps_em_MET} efficiency maps with MET" )
    print ( f"{n_datasets_sronly} signal regions" )
    print ( f"{n_datasets_MET} signal regions with MET in fs" )
    print ( f"{n_datasets} signal and control regions" )

    print ()

def discuss ( db, sqrts : Union[str,int,float], 
              verbose : bool, lumi : Union[None,float] ):
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
    print ( "---------------" )
    discussExperiment ( atlas, "ATLAS", title, verbose )
    print ( "---------------" )
    discussExperiment ( anas, "both", title, verbose )

def countTopos ( superseded, filter_fastlim, db, update : str, verbose : bool = True ):
    """ count the topologies
    :param update: consider entries only after this date (yyyy/mm/dd)
    """
    e = db.getExpResults( useSuperseded = superseded )
    anas = manips.filterFastlimFromList ( e, False, filter_fastlim, update )
    topos = set()
    topos_roff = set()
    for i in anas:
        for t in i.getTxNames():
            topos.add ( t.txName )
            topos_roff.add ( t.txName.replace("off","") )
    print ( f"{len(topos)} topologies ({len(topos_roff)}, not counting off-shell separately)" )
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
    discuss ( db, sqrts, args.verbose, args.lumi )
    if args.topologies:
        countTopos ( db, args.update, args.verbose )
if __name__ == '__main__':
    main()
