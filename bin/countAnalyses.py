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

def filter ( anas, really=True ):
    if not really:
        return anas
    ret = []
    for ana in anas:
        contact = ""
        if hasattr ( ana.globalInfo, "contact" ):
            contact = getattr ( ana.globalInfo, "contact" )
        if "fastlim" in contact:
            continue
        ret.append ( ana )
    return ret

def discuss ( superseded, filter_fastlim, db ):
    print ()
    print ( "---------------" )
    if superseded:
        print ( "Including superseded results" )
    else:
        print ( "Excluding superseded results" )
    if filter_fastlim:
        print ( "Filtering out FastLim" )
    else:
        print ( "Leaving in FastLim" )
    anas = db.getExpResults( useSuperseded=superseded )
    anas = filter ( anas, filter_fastlim )
    cms,atlas=[],[]
    for expRes in anas:
        Id=expRes.globalInfo.id
        if "CMS" in Id: cms.append ( expRes )
        if "ATLAS" in Id: atlas.append ( expRes )
    discussExperiment ( cms, "CMS" )
    discussExperiment ( atlas, "ATLAS" )

def countTopos ( superseded, filter_fastlim, db ):
    e = db.getExpResults( useSuperseded = superseded )
    anas = filter ( e, filter_fastlim )
    topos = set()
    for i in anas:
        for t in i.getTxNames():
            topos.add ( t.txName )
    print ( "%d topologies" % len(topos) )

def main():
    db = Database ( '../../smodels-database/' )
    for filter_fastlim in [ False, True ]:
        for superseded in [ True, False ]:
            discuss ( superseded, filter_fastlim, db )
            countTopos ( superseded, filter_fastlim, db )
if __name__ == '__main__':
    main()
